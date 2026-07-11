"""Tests for the expanded spell library (roadmap P5 #33).

Covers the two new spell tiers per aspect (master @ level 8, ultimate @ level
12) and the data-driven, level-gated `SpellManager.get_spells_for_aspect`:
unlock thresholds, list growth with level, the unknown-aspect fallback, balance
sanity of the new spells, and parity between the two SpellManager copies
(`Code.combat_system` and `Code.enhanced_combat_system`). Also pins the adaptive
spell-menu layout math so a full 5-spell list never overlaps the combat log.

Pure/deterministic; runs headlessly on the `Code.gfx` shim (no GPU/audio).
"""

import unittest

from Code.enhanced_combat_system import (
    SpellManager as EnhancedSpellManager,
    SPELL_UNLOCK_LEVELS,
)
from Code.combat_system import SpellManager as LegacySpellManager

ASPECTS = ("fire", "water", "dream", "earth", "life", "void")


class SpellLibraryTests(unittest.TestCase):
    def setUp(self):
        self.mgr = EnhancedSpellManager()

    def test_unlock_levels_constant(self):
        self.assertEqual(SPELL_UNLOCK_LEVELS, (1, 3, 5, 8, 12))

    def test_every_aspect_has_five_tiers(self):
        for aspect in ASPECTS:
            self.assertEqual(
                len(self.mgr.spell_library[aspect]), 5,
                f"{aspect} should define 5 spell tiers",
            )

    def test_new_master_and_ultimate_spells_present(self):
        names = {s.name for s in self.mgr.spell_library["fire"]}
        self.assertIn("Meteor", names)      # master (lvl 8)
        self.assertIn("Supernova", names)   # ultimate (lvl 12)

    def test_spell_attributes_valid(self):
        for aspect in ASPECTS:
            for spell in self.mgr.spell_library[aspect]:
                self.assertGreater(spell.mana_cost, 0, spell.name)
                self.assertLessEqual(spell.damage_min, spell.damage_max, spell.name)
                self.assertIn(
                    spell.spell_type, ("damage", "heal", "drain"), spell.name
                )

    def test_new_tiers_cost_more_than_existing(self):
        # The two new tiers (master idx 3, ultimate idx 4) should be pricier than
        # every pre-existing tier, and the ultimate the priciest of all. (The
        # original 3-tier "life" list is intentionally non-monotonic — Holy Light
        # is a cheap utility spell — so we only guard the newly added content.)
        for aspect in ASPECTS:
            costs = [s.mana_cost for s in self.mgr.spell_library[aspect]]
            base_max = max(costs[:3])
            master, ultimate = costs[3], costs[4]
            self.assertGreater(master, base_max, f"{aspect} master should cost most")
            self.assertGreater(ultimate, master, f"{aspect} ultimate should top master")


class LevelGatingTests(unittest.TestCase):
    def setUp(self):
        self.mgr = EnhancedSpellManager()

    def _count(self, level):
        return len(self.mgr.get_spells_for_aspect("fire_level_1", level))

    def test_gating_thresholds(self):
        expected = {
            1: 1, 2: 1,          # only basic
            3: 2, 4: 2,          # + intermediate
            5: 3, 6: 3, 7: 3,    # + advanced
            8: 4, 9: 4, 11: 4,   # + master
            12: 5, 20: 5,        # + ultimate
        }
        for level, count in expected.items():
            self.assertEqual(self._count(level), count, f"level {level}")

    def test_never_empty_even_below_level_one(self):
        # Defensive: a level-0 (or negative) character still gets the basic spell.
        spells = self.mgr.get_spells_for_aspect("fire_level_1", 0)
        self.assertEqual(len(spells), 1)
        self.assertEqual(spells[0].name, "Flame Bolt")

    def test_order_is_lowest_tier_first(self):
        spells = self.mgr.get_spells_for_aspect("fire_level_1", 20)
        self.assertEqual(
            [s.name for s in spells],
            ["Flame Bolt", "Fireball", "Inferno", "Meteor", "Supernova"],
        )

    def test_unknown_aspect_falls_back_to_fire(self):
        spells = self.mgr.get_spells_for_aspect("nonsense_aspect", 12)
        self.assertEqual(spells[0].name, "Flame Bolt")
        self.assertEqual(len(spells), 5)

    def test_all_aspects_reach_five_at_high_level(self):
        for aspect in ASPECTS:
            spells = self.mgr.get_spells_for_aspect(f"{aspect}_level_1", 15)
            self.assertEqual(len(spells), 5, aspect)


class ManagerParityTests(unittest.TestCase):
    """The legacy and enhanced SpellManagers must stay in lock-step."""

    def test_libraries_match(self):
        legacy = LegacySpellManager().spell_library
        enhanced = EnhancedSpellManager().spell_library
        self.assertEqual(set(legacy), set(enhanced))
        for aspect in enhanced:
            leg = [(s.name, s.mana_cost, s.damage_min, s.damage_max)
                   for s in legacy[aspect]]
            enh = [(s.name, s.mana_cost, s.damage_min, s.damage_max)
                   for s in enhanced[aspect]]
            self.assertEqual(leg, enh, aspect)

    def test_gating_matches(self):
        legacy = LegacySpellManager()
        enhanced = EnhancedSpellManager()
        for level in (1, 3, 5, 8, 12, 20):
            self.assertEqual(
                [s.name for s in legacy.get_spells_for_aspect("void_level_1", level)],
                [s.name for s in enhanced.get_spells_for_aspect("void_level_1", level)],
                f"level {level}",
            )


class MenuLayoutTests(unittest.TestCase):
    """Mirror of the adaptive row-pitch math in the spell-menu draw code.

    Ensures a full 5-spell list still fits above the combat log (top y=455).
    """

    LOG_TOP = 455
    MENU_Y = 190

    def _layout(self, n):
        row_pitch = 45
        rows_top = self.MENU_Y + 40
        row_budget = 448 - rows_top - 35
        if n * row_pitch > row_budget:
            row_pitch = max(34, row_budget // n)
        spell_y = self.MENU_Y + 40  # menu_y + 10 (title) + 30
        instruction_y = spell_y + n * row_pitch + 10
        instruction_bottom = instruction_y + 25
        return row_pitch, instruction_bottom

    def test_three_spells_use_comfortable_pitch(self):
        row_pitch, bottom = self._layout(3)
        self.assertEqual(row_pitch, 45)
        self.assertLess(bottom, self.LOG_TOP)

    def test_five_spells_fit_above_log(self):
        row_pitch, bottom = self._layout(5)
        self.assertGreaterEqual(row_pitch, 34)
        self.assertLess(bottom, self.LOG_TOP)

    def test_pitch_never_below_floor(self):
        for n in range(1, 8):
            row_pitch, _ = self._layout(n)
            self.assertGreaterEqual(row_pitch, 34)


if __name__ == "__main__":
    unittest.main()
