"""Player accounts for Magitech RPG multiplayer (roadmap P6 #41).

An **account** groups one or more characters under a single login so that, in
multiplayer, a player identifies themselves once and then picks which of *their*
characters to bring online. This module is the pure, dependency-free core of
that feature.

Design goals (mirroring the rest of the P6 multiplayer layer):

* **Purely additive / single-player untouched.** Nothing in the single-player
  import path references this module. Single-player still discovers characters
  by scanning ``Characters/`` (see ``CharacterManager.get_character_list``); it
  neither needs nor creates an account. Accounts live in their own ``Accounts/``
  directory and only the (opt-in) multiplayer path uses them.
* **No game/GUI imports.** Standard library only, so it imports and unit-tests
  headlessly — no pygame, no arcade, no display.
* **Deterministic + testable.** All state is plain JSON on disk under a base
  directory you pass in; every method is a pure function of that directory plus
  its arguments.

Security note: passwords are **never** stored in plaintext. Each account stores
a random per-account salt and a PBKDF2-HMAC-SHA256 hash of the password. This is
a lightweight local-account scheme suitable for a hobby game's LAN/self-hosted
server, not a substitute for a real identity provider.

Account file schema (``Accounts/<username>.json``)::

    {
        "Account_Version": 1,
        "username": "joe",
        "password_salt": "<hex>",
        "password_hash": "<hex>",
        "password_iterations": 200000,
        "created_at": 1700000000.0,
        "characters": ["Aria", "Borin"]
    }

The ``characters`` list holds character *names* that also correspond to saves in
``Characters/`` — accounts index existing single-player saves, they do not
duplicate character data.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Schema revision for account files, bumped if the on-disk shape changes.
ACCOUNT_SCHEMA_VERSION = 1

#: Default directory (relative to CWD) that holds one JSON file per account.
DEFAULT_ACCOUNTS_DIR = "Accounts"

#: PBKDF2 iteration count. High enough to be a real speed bump on a local box,
#: low enough not to stall account creation. Stored per-account so it can be
#: raised later without invalidating existing accounts.
PBKDF2_ITERATIONS = 200_000

#: Username rules: 3-24 chars, letters/digits/_/-/. only. Kept filesystem-safe
#: so ``<username>.json`` never needs escaping and can't traverse directories.
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,24}$")

#: Minimum password length. Modest by design — this guards casual local misuse.
MIN_PASSWORD_LENGTH = 4

#: Maximum characters an account may hold. Sanity cap, not a gameplay limit.
MAX_CHARACTERS_PER_ACCOUNT = 32


class AccountError(Exception):
    """Raised for invalid account operations (bad input, duplicates, auth)."""


# ---------------------------------------------------------------------------
# Validation + hashing helpers (pure)
# ---------------------------------------------------------------------------

def normalize_username(username: str) -> str:
    """Return the canonical form of ``username`` (trimmed, lower-cased).

    Usernames are compared case-insensitively so ``Joe`` and ``joe`` are the
    same account; the normalized form is also the on-disk filename stem.
    """
    return (username or "").strip().lower()


def validate_username(username: str) -> str:
    """Validate and return the normalized username, or raise ``AccountError``."""
    norm = normalize_username(username)
    if not _USERNAME_RE.match(norm):
        raise AccountError(
            "username must be 3-24 chars using letters, digits, '_', '-', or '.'"
        )
    return norm


def validate_password(password: str) -> None:
    """Raise ``AccountError`` if ``password`` is too short/empty."""
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise AccountError(
            f"password must be at least {MIN_PASSWORD_LENGTH} characters"
        )


def hash_password(
    password: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS
) -> str:
    """Return the hex PBKDF2-HMAC-SHA256 digest of ``password`` with ``salt``."""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return dk.hex()


def verify_password(password: str, account: Dict[str, Any]) -> bool:
    """Constant-time check that ``password`` matches a stored account record."""
    try:
        salt = bytes.fromhex(account["password_salt"])
        iterations = int(account.get("password_iterations", PBKDF2_ITERATIONS))
        expected = account["password_hash"]
    except (KeyError, ValueError, TypeError):
        return False
    candidate = hash_password(password, salt, iterations)
    return hmac.compare_digest(candidate, expected)


# ---------------------------------------------------------------------------
# AccountManager
# ---------------------------------------------------------------------------

class AccountManager:
    """CRUD over player accounts stored as JSON under a base directory.

    Every method is a pure function of the on-disk state plus its arguments, so
    two managers pointed at the same directory always agree. Nothing here has a
    GUI/game dependency, so it is safe to construct and drive headlessly.
    """

    def __init__(self, accounts_dir: str = DEFAULT_ACCOUNTS_DIR) -> None:
        self.accounts_dir = accounts_dir

    # -- paths -------------------------------------------------------------
    def _path_for(self, username: str) -> str:
        """Filesystem path for ``username``'s account file (validated)."""
        norm = validate_username(username)
        return os.path.join(self.accounts_dir, f"{norm}.json")

    def _ensure_dir(self) -> None:
        os.makedirs(self.accounts_dir, exist_ok=True)

    # -- existence / listing ----------------------------------------------
    def account_exists(self, username: str) -> bool:
        """True if an account file exists for ``username``."""
        try:
            return os.path.exists(self._path_for(username))
        except AccountError:
            return False

    def list_accounts(self) -> List[str]:
        """Sorted list of existing account usernames (by file stem)."""
        if not os.path.isdir(self.accounts_dir):
            return []
        names = [
            f[:-5]
            for f in os.listdir(self.accounts_dir)
            if f.endswith(".json")
        ]
        return sorted(names)

    # -- load / save (raw) -------------------------------------------------
    def _load(self, username: str) -> Dict[str, Any]:
        path = self._path_for(username)
        if not os.path.exists(path):
            raise AccountError(f"no such account: {normalize_username(username)!r}")
        with open(path, "r") as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            raise AccountError(f"corrupt account file: {path}")
        return data

    def _write(self, data: Dict[str, Any]) -> None:
        self._ensure_dir()
        path = self._path_for(data["username"])
        with open(path, "w") as fh:
            json.dump(data, fh, indent=4)

    # -- create / authenticate --------------------------------------------
    def create_account(self, username: str, password: str) -> Dict[str, Any]:
        """Create a new account and return its (public) record.

        Raises ``AccountError`` on invalid input or if the account already
        exists. The returned record is safe to hand around: it omits the
        password hash/salt via :func:`public_view`.
        """
        norm = validate_username(username)
        validate_password(password)
        if self.account_exists(norm):
            raise AccountError(f"account already exists: {norm!r}")
        salt = os.urandom(16)
        record = {
            "Account_Version": ACCOUNT_SCHEMA_VERSION,
            "username": norm,
            "password_salt": salt.hex(),
            "password_hash": hash_password(password, salt),
            "password_iterations": PBKDF2_ITERATIONS,
            "created_at": time.time(),
            "characters": [],
        }
        self._write(record)
        return public_view(record)

    def authenticate(self, username: str, password: str) -> bool:
        """Return True iff ``username`` exists and ``password`` matches."""
        try:
            record = self._load(username)
        except AccountError:
            return False
        return verify_password(password, record)

    # -- character membership ---------------------------------------------
    def list_characters(self, username: str) -> List[str]:
        """Return the character names registered under ``username``."""
        record = self._load(username)
        chars = record.get("characters", [])
        return list(chars) if isinstance(chars, list) else []

    def add_character(self, username: str, character_name: str) -> List[str]:
        """Register ``character_name`` under ``username``; return the new list.

        Idempotent (adding an already-linked character is a no-op) and
        case-insensitive on the character name to match save-file behaviour.
        Raises ``AccountError`` past :data:`MAX_CHARACTERS_PER_ACCOUNT`.
        """
        name = (character_name or "").strip()
        if not name:
            raise AccountError("character name must be non-empty")
        record = self._load(username)
        chars = record.get("characters", [])
        if not isinstance(chars, list):
            chars = []
        if any(c.lower() == name.lower() for c in chars):
            return list(chars)  # already linked
        if len(chars) >= MAX_CHARACTERS_PER_ACCOUNT:
            raise AccountError(
                f"account holds the max {MAX_CHARACTERS_PER_ACCOUNT} characters"
            )
        chars.append(name)
        record["characters"] = chars
        self._write(record)
        return list(chars)

    def remove_character(self, username: str, character_name: str) -> List[str]:
        """Unlink ``character_name`` from ``username``; return the new list.

        Only removes the account's *reference* to the character — it never
        deletes the underlying ``Characters/*.json`` save. Case-insensitive.
        """
        name = (character_name or "").strip().lower()
        record = self._load(username)
        chars = record.get("characters", [])
        if not isinstance(chars, list):
            chars = []
        new_chars = [c for c in chars if c.lower() != name]
        if len(new_chars) != len(chars):
            record["characters"] = new_chars
            self._write(record)
        return new_chars

    def get_account(self, username: str) -> Dict[str, Any]:
        """Return the public (secret-free) view of an existing account."""
        return public_view(self._load(username))


def public_view(record: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of ``record`` without the password secrets.

    Use this whenever an account is surfaced to the game/UI or the network so a
    salt/hash never leaves the storage layer.
    """
    return {
        "Account_Version": record.get("Account_Version", ACCOUNT_SCHEMA_VERSION),
        "username": record.get("username", ""),
        "created_at": record.get("created_at"),
        "characters": list(record.get("characters", []) or []),
    }


def authenticate_or_create(
    manager: AccountManager, username: str, password: str
) -> Dict[str, Any]:
    """Log in if the account exists, otherwise create it — a convenience for a
    single "Account" prompt on the multiplayer join screen.

    Returns the public account view. Raises ``AccountError`` if the account
    exists but the password is wrong, or on invalid new-account input.
    """
    norm = validate_username(username)
    if manager.account_exists(norm):
        if not manager.authenticate(norm, password):
            raise AccountError("incorrect password")
        return manager.get_account(norm)
    return manager.create_account(norm, password)
