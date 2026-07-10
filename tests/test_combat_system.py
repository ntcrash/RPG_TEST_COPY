"""Unit tests for Code/combat_system.py damage / hit-chance logic (roadmap P2 #8).

These cover the pure calculation methods flagged in the roadmap
(`calculate_spell_damage`, `calculate_hit_chance`, and `calculate_damage`) plus
spell-availability gating. Randomness is pinned via ``mock.patch`` on the
module's ``random.randint`` so each expected value is exact.
"""

import os
import unittest
from unittest import mock

# Headless SDL must be configured before pygame is imported (mirrors tests/__init__).
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MEGITECH_BACKEND", "arcade")

from Code.backend import pygame  # noqa: E402  (default: Code.gfx shim)

pygame.init()

from Code.combat_system import CombatManager, Spell, SpellManager  # noqa: E402

RANDINT = "Code.combat_system.random.randint"


class PhysicalDamageTests(unittest.TestCase):
    def setUp(self):
        self.cm = CombatManager(character_manager=None)

    def test_strength_bonus_added_no_crit(self):
        # strength 20 -> +5 bonus; dexterity 10 -> crit_chance 5%.
        attacker = {"strength": 20, "dexterity": 10}
        with mock.patch(RANDINT, side_effect=[12, 100]):  # base roll 12, crit roll misses
            dmg, crit = self.cm.calculate_damage(10, 15, attacker)
        self.assertEqual(dmg, 17)  # 12 + 5
        self.assertFalse(crit)

    def test_critical_multiplies_by_1_5(self):
        attacker = {"strength": 20, "dexterity": 10}
        with mock.patch(RANDINT, side_effect=[12, 1]):  # crit roll 1 <= 5% crit chance
            dmg, crit = self.cm.calculate_damage(10, 15, attacker)
        self.assertEqual(dmg, 25)  # int((12 + 5) * 1.5)
        self.assertTrue(crit)

    def test_low_strength_never_negative_bonus(self):
        attacker = {"strength": 4, "dexterity": 10}  # (4-10)//2 = -3 -> clamped to 0
        with mock.patch(RANDINT, side_effect=[10, 100]):
            dmg, crit = self.cm.calculate_damage(10, 10, attacker)
        self.assertEqual(dmg, 10)
        self.assertFalse(crit)


class SpellDamageTests(unittest.TestCase):
    def setUp(self):
        self.cm = CombatManager(character_manager=None)

    def test_heal_uses_wisdom_and_level(self):
        spell = Spell("Heal", 0, 10, 10, "heal")
        # wisdom 20 -> +5; level 5 -> (5-1)//2 = +2
        dmg, crit = self.cm.calculate_spell_damage(spell, {"wisdom": 20, "intelligence": 10}, 5)
        self.assertEqual(dmg, 17)  # 10 + 5 + 2
        self.assertFalse(crit)

    def test_drain_uses_intelligence_and_level(self):
        spell = Spell("Drain", 0, 10, 10, "drain")
        # intelligence 20 -> +5; level 3 -> +1
        dmg, crit = self.cm.calculate_spell_damage(spell, {"intelligence": 20}, 3)
        self.assertEqual(dmg, 16)  # 10 + 5 + 1
        self.assertFalse(crit)

    def test_damage_spell_no_crit(self):
        spell = Spell("Bolt", 0, 10, 10, "damage")
        with mock.patch(RANDINT, side_effect=[10, 100]):  # base 10, crit roll misses
            dmg, crit = self.cm.calculate_spell_damage(spell, {"intelligence": 10}, 1)
        self.assertEqual(dmg, 10)
        self.assertFalse(crit)

    def test_damage_spell_crit(self):
        spell = Spell("Bolt", 0, 10, 10, "damage")
        with mock.patch(RANDINT, side_effect=[10, 1]):  # crit roll 1 <= 3% floor
            dmg, crit = self.cm.calculate_spell_damage(spell, {"intelligence": 10}, 1)
        self.assertEqual(dmg, 15)  # int(10 * 1.5)
        self.assertTrue(crit)


class HitChanceTests(unittest.TestCase):
    def setUp(self):
        self.cm = CombatManager(character_manager=None)

    def test_base_75_percent_boundary(self):
        att, dfn = {"dexterity": 10}, {"armor_class": 10}  # final hit chance 75
        with mock.patch(RANDINT, return_value=75):
            self.assertTrue(self.cm.calculate_hit_chance(att, dfn))
        with mock.patch(RANDINT, return_value=76):
            self.assertFalse(self.cm.calculate_hit_chance(att, dfn))

    def test_hit_chance_floored_at_5_percent(self):
        # High AC would drive the chance negative; it must clamp to 5%.
        att, dfn = {"dexterity": 10}, {"armor_class": 50}
        with mock.patch(RANDINT, return_value=5):
            self.assertTrue(self.cm.calculate_hit_chance(att, dfn))
        with mock.patch(RANDINT, return_value=6):
            self.assertFalse(self.cm.calculate_hit_chance(att, dfn))


class SpellAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.sm = SpellManager()

    def test_spells_unlock_by_level(self):
        self.assertEqual(len(self.sm.get_spells_for_aspect("fire", 1)), 1)
        self.assertEqual(len(self.sm.get_spells_for_aspect("fire", 3)), 2)
        self.assertEqual(len(self.sm.get_spells_for_aspect("fire", 5)), 3)

    def test_unknown_aspect_falls_back_to_fire(self):
        spells = self.sm.get_spells_for_aspect("banana", 1)
        self.assertEqual(spells[0].name, "Flame Bolt")

    def test_aspect_suffix_is_stripped(self):
        # "fire_level_3" should resolve to the "fire" library.
        spells = self.sm.get_spells_for_aspect("fire_level_3", 5)
        self.assertEqual(spells[0].name, "Flame Bolt")
        self.assertEqual(len(spells), 3)


if __name__ == "__main__":
    unittest.main()
