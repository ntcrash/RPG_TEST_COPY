"""Tests for player accounts (roadmap P6 #41).

Covers the pure account layer (`Code/account_system.py`) — validation, password
hashing/verification, account CRUD, and character membership — plus its opt-in
wiring into the multiplayer session (`Code/multiplayer.py`). Everything is
standard-library only and headless (no pygame/arcade/display), and every test
writes to a throwaway temp directory so it never touches a real ``Accounts/``.
"""

import os
import tempfile
import unittest

from Code.account_system import (
    ACCOUNT_SCHEMA_VERSION,
    MAX_CHARACTERS_PER_ACCOUNT,
    MIN_PASSWORD_LENGTH,
    AccountError,
    AccountManager,
    authenticate_or_create,
    hash_password,
    normalize_username,
    public_view,
    validate_password,
    validate_username,
    verify_password,
)
from Code.multiplayer import account_from_env, session_from_env


class ValidationTests(unittest.TestCase):
    def test_normalize_lowers_and_trims(self):
        self.assertEqual(normalize_username("  Joe  "), "joe")

    def test_valid_usernames(self):
        for name in ("joe", "Aria-1", "b.o_r", "PlayerOne"):
            self.assertEqual(validate_username(name), name.lower())

    def test_invalid_usernames_rejected(self):
        for bad in ("", "ab", "x" * 25, "has space", "bad/slash", "emoji😀x"):
            with self.assertRaises(AccountError):
                validate_username(bad)

    def test_password_min_length_enforced(self):
        with self.assertRaises(AccountError):
            validate_password("a" * (MIN_PASSWORD_LENGTH - 1))
        # exactly the minimum is fine (no raise)
        validate_password("a" * MIN_PASSWORD_LENGTH)

    def test_non_string_password_rejected(self):
        with self.assertRaises(AccountError):
            validate_password(None)  # type: ignore[arg-type]


class HashingTests(unittest.TestCase):
    def test_hash_is_deterministic_for_same_salt(self):
        salt = b"\x01" * 16
        self.assertEqual(hash_password("secret", salt), hash_password("secret", salt))

    def test_hash_differs_by_salt(self):
        self.assertNotEqual(
            hash_password("secret", b"\x01" * 16),
            hash_password("secret", b"\x02" * 16),
        )

    def test_hash_is_not_plaintext(self):
        self.assertNotIn("secret", hash_password("secret", b"\x00" * 16))

    def test_verify_password_roundtrip(self):
        salt = os.urandom(16)
        record = {
            "password_salt": salt.hex(),
            "password_hash": hash_password("hunter2", salt),
            "password_iterations": 200_000,
        }
        self.assertTrue(verify_password("hunter2", record))
        self.assertFalse(verify_password("wrong", record))

    def test_verify_password_handles_corrupt_record(self):
        self.assertFalse(verify_password("x", {}))
        self.assertFalse(verify_password("x", {"password_salt": "zz"}))


class AccountManagerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = os.path.join(self._tmp.name, "Accounts")
        self.mgr = AccountManager(self.dir)

    def tearDown(self):
        self._tmp.cleanup()

    def test_create_account_persists_and_hides_secrets(self):
        view = self.mgr.create_account("Joe", "hunter2")
        self.assertEqual(view["username"], "joe")
        self.assertEqual(view["Account_Version"], ACCOUNT_SCHEMA_VERSION)
        self.assertEqual(view["characters"], [])
        # public view must not leak secrets
        self.assertNotIn("password_hash", view)
        self.assertNotIn("password_salt", view)
        # file exists on disk
        self.assertTrue(os.path.exists(os.path.join(self.dir, "joe.json")))

    def test_duplicate_account_rejected_case_insensitively(self):
        self.mgr.create_account("Joe", "hunter2")
        with self.assertRaises(AccountError):
            self.mgr.create_account("JOE", "other")

    def test_create_account_validates_input(self):
        with self.assertRaises(AccountError):
            self.mgr.create_account("ab", "hunter2")  # bad username
        with self.assertRaises(AccountError):
            self.mgr.create_account("valid", "x")  # bad password

    def test_authenticate(self):
        self.mgr.create_account("joe", "hunter2")
        self.assertTrue(self.mgr.authenticate("joe", "hunter2"))
        self.assertTrue(self.mgr.authenticate("JOE", "hunter2"))  # case-insensitive
        self.assertFalse(self.mgr.authenticate("joe", "nope"))
        self.assertFalse(self.mgr.authenticate("ghost", "hunter2"))  # no account

    def test_account_exists_and_listing(self):
        self.assertFalse(self.mgr.account_exists("joe"))
        self.assertEqual(self.mgr.list_accounts(), [])
        self.mgr.create_account("joe", "hunter2")
        self.mgr.create_account("aria", "hunter2")
        self.assertTrue(self.mgr.account_exists("JOE"))
        self.assertEqual(self.mgr.list_accounts(), ["aria", "joe"])

    def test_list_accounts_missing_dir(self):
        self.assertEqual(AccountManager("/no/such/dir/xyz").list_accounts(), [])


class CharacterMembershipTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mgr = AccountManager(os.path.join(self._tmp.name, "Accounts"))
        self.mgr.create_account("joe", "hunter2")

    def tearDown(self):
        self._tmp.cleanup()

    def test_add_and_list_characters(self):
        self.assertEqual(self.mgr.add_character("joe", "Aria"), ["Aria"])
        self.assertEqual(self.mgr.add_character("joe", "Borin"), ["Aria", "Borin"])
        self.assertEqual(self.mgr.list_characters("joe"), ["Aria", "Borin"])

    def test_add_character_is_idempotent_case_insensitive(self):
        self.mgr.add_character("joe", "Aria")
        self.assertEqual(self.mgr.add_character("joe", "aria"), ["Aria"])
        self.assertEqual(self.mgr.list_characters("joe"), ["Aria"])

    def test_add_empty_character_rejected(self):
        with self.assertRaises(AccountError):
            self.mgr.add_character("joe", "   ")

    def test_remove_character_does_not_touch_others(self):
        self.mgr.add_character("joe", "Aria")
        self.mgr.add_character("joe", "Borin")
        self.assertEqual(self.mgr.remove_character("joe", "aria"), ["Borin"])
        self.assertEqual(self.mgr.list_characters("joe"), ["Borin"])

    def test_remove_missing_character_is_noop(self):
        self.mgr.add_character("joe", "Aria")
        self.assertEqual(self.mgr.remove_character("joe", "ghost"), ["Aria"])

    def test_membership_persists_across_managers(self):
        self.mgr.add_character("joe", "Aria")
        other = AccountManager(self.mgr.accounts_dir)
        self.assertEqual(other.list_characters("joe"), ["Aria"])

    def test_max_characters_enforced(self):
        for i in range(MAX_CHARACTERS_PER_ACCOUNT):
            self.mgr.add_character("joe", f"Char{i}")
        with self.assertRaises(AccountError):
            self.mgr.add_character("joe", "OneTooMany")

    def test_operations_on_missing_account_raise(self):
        with self.assertRaises(AccountError):
            self.mgr.list_characters("ghost")
        with self.assertRaises(AccountError):
            self.mgr.add_character("ghost", "Aria")

    def test_get_account_returns_public_view(self):
        self.mgr.add_character("joe", "Aria")
        view = self.mgr.get_account("joe")
        self.assertEqual(view["characters"], ["Aria"])
        self.assertNotIn("password_hash", view)


class PublicViewTests(unittest.TestCase):
    def test_public_view_strips_secrets_and_copies_list(self):
        chars = ["Aria"]
        record = {
            "Account_Version": 1,
            "username": "joe",
            "password_salt": "aa",
            "password_hash": "bb",
            "created_at": 123.0,
            "characters": chars,
        }
        view = public_view(record)
        self.assertEqual(
            set(view), {"Account_Version", "username", "created_at", "characters"}
        )
        # returned list is a copy, not the original reference
        view["characters"].append("Mutated")
        self.assertEqual(chars, ["Aria"])


class AuthenticateOrCreateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mgr = AccountManager(os.path.join(self._tmp.name, "Accounts"))

    def tearDown(self):
        self._tmp.cleanup()

    def test_creates_on_first_use(self):
        view = authenticate_or_create(self.mgr, "joe", "hunter2")
        self.assertEqual(view["username"], "joe")
        self.assertTrue(self.mgr.account_exists("joe"))

    def test_logs_in_existing(self):
        self.mgr.create_account("joe", "hunter2")
        self.mgr.add_character("joe", "Aria")
        view = authenticate_or_create(self.mgr, "JOE", "hunter2")
        self.assertEqual(view["characters"], ["Aria"])

    def test_wrong_password_raises(self):
        self.mgr.create_account("joe", "hunter2")
        with self.assertRaises(AccountError):
            authenticate_or_create(self.mgr, "joe", "wrong")


class MultiplayerAccountEnvTests(unittest.TestCase):
    """The account layer's opt-in wiring into the multiplayer session."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.accounts_dir = os.path.join(self._tmp.name, "Accounts")

    def tearDown(self):
        self._tmp.cleanup()

    def test_account_from_env_disabled_without_creds(self):
        self.assertIsNone(account_from_env({}))
        self.assertIsNone(account_from_env({"MEGITECH_ACCOUNT": "joe"}))  # no pw

    def test_account_from_env_creates_then_logs_in(self):
        env = {
            "MEGITECH_ACCOUNT": "Joe",
            "MEGITECH_ACCOUNT_PASSWORD": "hunter2",
            "MEGITECH_ACCOUNTS_DIR": self.accounts_dir,
        }
        view = account_from_env(env)
        self.assertIsNotNone(view)
        self.assertEqual(view["username"], "joe")
        # second call logs into the same account, not a new one
        again = account_from_env(env)
        self.assertEqual(again["username"], "joe")
        self.assertEqual(AccountManager(self.accounts_dir).list_accounts(), ["joe"])

    def test_account_from_env_wrong_password_degrades_to_none(self):
        AccountManager(self.accounts_dir).create_account("joe", "hunter2")
        env = {
            "MEGITECH_ACCOUNT": "joe",
            "MEGITECH_ACCOUNT_PASSWORD": "wrong",
            "MEGITECH_ACCOUNTS_DIR": self.accounts_dir,
        }
        self.assertIsNone(account_from_env(env))

    def test_session_from_env_attaches_account_and_defaults_name(self):
        env = {
            "MEGITECH_MULTIPLAYER": "1",
            "MEGITECH_ACCOUNT": "Joe",
            "MEGITECH_ACCOUNT_PASSWORD": "hunter2",
            "MEGITECH_ACCOUNTS_DIR": self.accounts_dir,
        }
        session = session_from_env(env)
        self.assertIsNotNone(session)
        self.assertIsNotNone(session.account)
        self.assertEqual(session.account["username"], "joe")
        # name defaults to the account username when no explicit name given
        self.assertEqual(session.name, "joe")

    def test_explicit_player_name_overrides_account_username(self):
        env = {
            "MEGITECH_MULTIPLAYER": "1",
            "MEGITECH_PLAYER_NAME": "Ariadne",
            "MEGITECH_ACCOUNT": "joe",
            "MEGITECH_ACCOUNT_PASSWORD": "hunter2",
            "MEGITECH_ACCOUNTS_DIR": self.accounts_dir,
        }
        session = session_from_env(env)
        self.assertEqual(session.name, "Ariadne")
        self.assertEqual(session.account["username"], "joe")

    def test_session_without_account_stays_guest(self):
        session = session_from_env({"MEGITECH_MULTIPLAYER": "1"})
        self.assertIsNotNone(session)
        self.assertIsNone(session.account)
        self.assertEqual(session.name, "Adventurer")


if __name__ == "__main__":
    unittest.main()
