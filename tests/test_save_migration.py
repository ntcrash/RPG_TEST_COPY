"""Unit tests for Code/save_migration.py (roadmap P4 #14).

Covers the versioned save schema and the migration/validation pass that heals
older/partial character saves so newer code that reads fields by direct index
does not KeyError. Also exercises the CharacterManager.load_character
integration: an out-of-date save on disk is migrated and re-written on load.
"""

import json
import os
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MEGITECH_BACKEND", "arcade")

from Code.save_migration import (  # noqa: E402
    FIELD_DEFAULTS,
    INT_FIELDS,
    SAVE_SCHEMA_VERSION,
    STAT_KEYS,
    migrate_character,
    validate_character,
)


class MigrateCharacterTests(unittest.TestCase):
    def _minimal_legacy_save(self):
        # A plausible pre-schema save: has a name/level but is missing several
        # fields newer combat/inventory code reads by direct index.
        return {"Name": "Old Hero", "Level": 5, "Experience_Points": 700}

    def test_backfills_all_required_fields(self):
        data, changed, _ = migrate_character(self._minimal_legacy_save())
        self.assertTrue(changed)
        for field in FIELD_DEFAULTS:
            self.assertIn(field, data)
        for stat in STAT_KEYS:
            self.assertIn(stat, data)
        self.assertIn("Inventory", data)
        self.assertIsInstance(data["Inventory"], dict)

    def test_preserves_existing_values(self):
        data, _, _ = migrate_character(self._minimal_legacy_save())
        self.assertEqual(data["Name"], "Old Hero")
        self.assertEqual(data["Level"], 5)
        self.assertEqual(data["Experience_Points"], 700)

    def test_stamps_schema_version(self):
        data, _, _ = migrate_character(self._minimal_legacy_save())
        self.assertEqual(data["Save_Version"], SAVE_SCHEMA_VERSION)

    def test_coerces_numeric_strings_and_floats(self):
        data, changed, _ = migrate_character(
            {"Credits": "1500", "Hit_Points": 87.6, "Aspect1_Mana": "40"}
        )
        self.assertTrue(changed)
        self.assertEqual(data["Credits"], 1500)
        self.assertEqual(data["Hit_Points"], 87)
        self.assertEqual(data["Aspect1_Mana"], 40)
        for field in INT_FIELDS:
            self.assertIsInstance(data[field], int)

    def test_clamps_negative_non_negative_fields(self):
        data, _, _ = migrate_character({"Credits": -50, "Hit_Points": -10})
        self.assertEqual(data["Credits"], 0)
        self.assertEqual(data["Hit_Points"], 0)

    def test_resets_non_dict_inventory(self):
        data, changed, _ = migrate_character({"Inventory": ["Health Potion"]})
        self.assertTrue(changed)
        self.assertEqual(data["Inventory"], {})

    def test_non_dict_input_replaced_with_defaults(self):
        data, changed, notes = migrate_character(None)
        self.assertTrue(changed)
        self.assertEqual(data["Save_Version"], SAVE_SCHEMA_VERSION)
        self.assertEqual(data["Name"], FIELD_DEFAULTS["Name"])
        self.assertTrue(any("replaced" in n for n in notes))

    def test_idempotent_second_pass_makes_no_changes(self):
        once, _, _ = migrate_character(self._minimal_legacy_save())
        twice, changed, notes = migrate_character(dict(once))
        self.assertFalse(changed)
        self.assertEqual(notes, [])

    def test_already_current_save_unchanged(self):
        current = dict(FIELD_DEFAULTS)
        current["Inventory"] = {}
        current["Pets"] = []  # container field (roadmap P5 #32), like Inventory
        for stat in STAT_KEYS:
            current[stat] = 10
        current["Save_Version"] = SAVE_SCHEMA_VERSION
        _, changed, _ = migrate_character(current)
        self.assertFalse(changed)


class ValidateCharacterTests(unittest.TestCase):
    def test_clean_on_migrated_save(self):
        data, _, _ = migrate_character({"Name": "X"})
        self.assertEqual(validate_character(data), [])

    def test_flags_missing_and_stale(self):
        issues = validate_character({"Name": "X"})
        self.assertTrue(any("Inventory" in i for i in issues))
        self.assertTrue(any("schema out of date" in i for i in issues))

    def test_rejects_non_object(self):
        self.assertEqual(len(validate_character(42)), 1)


class LoadCharacterMigrationTests(unittest.TestCase):
    """Integration: an old save on disk is healed and re-written on load."""

    def setUp(self):
        from Code.game_data import CharacterManager

        self.mgr = CharacterManager()
        self._tmp = tempfile.mkdtemp(prefix="megitech_saves_")
        self.path = os.path.join(self._tmp, "legacy.json")

    def test_loads_and_rewrites_legacy_save(self):
        with open(self.path, "w") as f:
            json.dump({"Name": "Legacy", "Level": 3}, f)

        self.assertTrue(self.mgr.load_character(self.path))
        # In-memory data is complete.
        self.assertEqual(self.mgr.character_data["Save_Version"], SAVE_SCHEMA_VERSION)
        self.assertIn("Aspect1_Mana", self.mgr.character_data)
        self.assertEqual(self.mgr.character_data["Name"], "Legacy")

        # The healed save was persisted back to disk.
        with open(self.path) as f:
            on_disk = json.load(f)
        self.assertEqual(on_disk["Save_Version"], SAVE_SCHEMA_VERSION)
        self.assertEqual(validate_character(on_disk), [])

    def test_current_save_not_rewritten_needlessly(self):
        data, _, _ = migrate_character({"Name": "Fresh"})
        with open(self.path, "w") as f:
            json.dump(data, f)
        before = os.path.getmtime(self.path)
        self.assertTrue(self.mgr.load_character(self.path))
        # No structural change -> load_character should not have re-saved.
        self.assertEqual(os.path.getmtime(self.path), before)


if __name__ == "__main__":
    unittest.main()
