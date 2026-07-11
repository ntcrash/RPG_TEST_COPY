"""Difficulty / balance regression checks (roadmap P4 #15).

The CHANGELOG records repeated past hotfixes for the difficulty-multiplier and
stat-scaling systems (v1.4.1, v1.7.3). These tests pin the *expected numeric
output* of the balance-critical formulas for a handful of reference
character/enemy stat combos, so a future edit that silently changes the tuning
(HP scaling, difficulty multiplier, armor-class, damage bonuses) fails loudly
instead of shipping a balance regression.

Randomness is pinned via ``mock.patch`` so every expected value is exact.
Complements ``tests/test_combat_system.py`` (which covers the pure
CombatManager math); this file focuses on the enemy-scaling and armor-class
surfaces those hotfixes touched.
"""

import os
import unittest
from unittest import mock

# Headless SDL must be configured before the backend is imported.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MEGITECH_BACKEND", "arcade")

from Code.backend import pygame  # noqa: E402  (default: Code.gfx shim)

pygame.init()

from Code.game_data import CharacterManager, EnemyManager  # noqa: E402

CHOICE = "Code.game_data.random.choice"
RANDINT = "Code.game_data.random.randint"


class EnemyHPScalingTests(unittest.TestCase):
    """Pin `create_scaled_enemy` HP = (hp_base + (level-1)*12 + variance) * mult."""

    def setUp(self):
        self.em = EnemyManager()
        self.em.world_theme = "grassland"

    def _wild_goblin(self):
        return {"name": "Wild Goblin", "hp_base": 60, "aspect": "earth_level_1"}

    def test_level1_normal_difficulty_is_base_hp(self):
        self.em.current_book_level = 1
        self.em.difficulty_multiplier = 1.0
        with mock.patch(CHOICE, return_value=self._wild_goblin()), \
                mock.patch(RANDINT, return_value=0):  # zero variance
            enemy = self.em.create_scaled_enemy()
        self.assertEqual(enemy["Hit_Points"], 60)  # 60 + 0 + 0
        self.assertEqual(enemy["Level"], 1)
        self.assertEqual(enemy["Tier"], "basic")

    def test_level5_adds_48_from_level_scaling(self):
        self.em.current_book_level = 5
        self.em.difficulty_multiplier = 1.0
        with mock.patch(CHOICE, return_value=self._wild_goblin()), \
                mock.patch(RANDINT, return_value=0):
            enemy = self.em.create_scaled_enemy()
        # 60 + (5-1)*12 + 0 = 108
        self.assertEqual(enemy["Hit_Points"], 108)
        self.assertEqual(enemy["Level"], 5)

    def test_hard_difficulty_doubles_scaled_hp_and_level(self):
        self.em.current_book_level = 3
        self.em.difficulty_multiplier = 2.0
        with mock.patch(CHOICE, return_value=self._wild_goblin()), \
                mock.patch(RANDINT, return_value=0):
            enemy = self.em.create_scaled_enemy()
        # (60 + (3-1)*12 + 0) * 2.0 = 168 ; level int(3*2.0)=6
        self.assertEqual(enemy["Hit_Points"], 168)
        self.assertEqual(enemy["Level"], 6)

    def test_easy_difficulty_halves_hp(self):
        self.em.current_book_level = 1
        self.em.difficulty_multiplier = 0.5
        with mock.patch(CHOICE, return_value=self._wild_goblin()), \
                mock.patch(RANDINT, return_value=0):
            enemy = self.em.create_scaled_enemy()
        self.assertEqual(enemy["Hit_Points"], 30)  # int(60 * 0.5)
        self.assertEqual(enemy["Level"], 1)  # max(1, int(1*0.5))

    def test_variance_is_applied_before_multiplier(self):
        self.em.current_book_level = 1
        self.em.difficulty_multiplier = 2.0
        with mock.patch(CHOICE, return_value=self._wild_goblin()), \
                mock.patch(RANDINT, return_value=15):  # max variance
            enemy = self.em.create_scaled_enemy()
        # (60 + 0 + 15) * 2.0 = 150
        self.assertEqual(enemy["Hit_Points"], 150)

    def test_hp_never_below_one(self):
        self.em.current_book_level = 1
        self.em.difficulty_multiplier = 0.1
        with mock.patch(CHOICE, return_value=self._wild_goblin()), \
                mock.patch(RANDINT, return_value=-10):  # min variance
            enemy = self.em.create_scaled_enemy()
        # (60 - 10) * 0.1 = 5 -> still >= 1
        self.assertEqual(enemy["Hit_Points"], 5)


class EnemyTierBoundaryTests(unittest.TestCase):
    """Pin the book-level -> tier mapping in `create_scaled_enemy`."""

    def setUp(self):
        self.em = EnemyManager()
        self.em.world_theme = "grassland"
        self.em.difficulty_multiplier = 1.0

    def _tier_at(self, level):
        self.em.current_book_level = level
        with mock.patch(RANDINT, return_value=0):
            return self.em.create_scaled_enemy()["Tier"]

    def test_tier_boundaries(self):
        cases = {
            1: "basic", 3: "basic",
            4: "elite", 6: "elite",
            7: "champion", 10: "champion",
            11: "ancient", 15: "ancient",
            16: "boss", 25: "boss",
        }
        for level, expected in cases.items():
            with self.subTest(level=level):
                self.assertEqual(self._tier_at(level), expected)


class BossScalingTests(unittest.TestCase):
    """Pin `create_scaled_boss` HP = (hp_base + (level-1)*30 + variance) * mult."""

    def setUp(self):
        self.em = EnemyManager()
        self.em.world_theme = "grassland"

    def test_boss_level_scaling_is_30_per_level(self):
        self.em.current_book_level = 4
        self.em.difficulty_multiplier = 1.0
        # grassland has a single boss template (hp_base 400).
        with mock.patch(RANDINT, return_value=0):
            boss = self.em.create_scaled_boss()
        # 400 + (4-1)*30 + 0 = 490 ; level max(1,int((4+3)*1.0))=7
        self.assertEqual(boss["Hit_Points"], 490)
        self.assertEqual(boss["Level"], 7)
        self.assertEqual(boss["Tier"], "boss")

    def test_boss_difficulty_multiplier(self):
        self.em.current_book_level = 1
        self.em.difficulty_multiplier = 1.5
        with mock.patch(RANDINT, return_value=0):
            boss = self.em.create_scaled_boss()
        # 400 * 1.5 = 600 ; level int((1+3)*1.5)=6
        self.assertEqual(boss["Hit_Points"], 600)
        self.assertEqual(boss["Level"], 6)


class DifficultyMultiplierClampTests(unittest.TestCase):
    """`set_difficulty_multiplier` must clamp to [0.1, 3.0]."""

    def setUp(self):
        self.em = EnemyManager()

    def test_upper_clamp(self):
        self.em.set_difficulty_multiplier(5.0)
        self.assertEqual(self.em.difficulty_multiplier, 3.0)

    def test_lower_clamp(self):
        self.em.set_difficulty_multiplier(0.01)
        self.assertEqual(self.em.difficulty_multiplier, 0.1)

    def test_value_within_range_untouched(self):
        self.em.set_difficulty_multiplier(1.5)
        self.assertEqual(self.em.difficulty_multiplier, 1.5)


class ArmorClassTests(unittest.TestCase):
    """Pin `CharacterManager.get_armor_class` = 10 + dex_bonus + best_armor.

    Armor bonuses are taken as a MAX across equipped armor, never summed — the
    v1.x balance work depended on this. Gear here is chosen so equipment gives
    no dexterity bonus except where explicitly noted.
    """

    def _char(self, **overrides):
        cm = CharacterManager()
        data = {
            "dexterity": 14,          # (14-10)//2 = +2
            "Weapon1": "Hands", "Weapon2": "Hands", "Weapon3": "Hands",
            "Armor_Slot_1": "", "Armor_Slot_2": "",
            "Inventory": {},
        }
        data.update(overrides)
        cm.character_data = data
        return cm

    def test_no_armor_dex_only(self):
        cm = self._char()
        self.assertEqual(cm.get_armor_class(), 12)  # 10 + 2 + 0

    def test_plate_mail_adds_seven(self):
        cm = self._char(Armor_Slot_1="Plate Mail")
        self.assertEqual(cm.get_armor_class(), 19)  # 10 + 2 + 7

    def test_two_armors_take_the_max_not_the_sum(self):
        cm = self._char(Armor_Slot_1="Plate Mail", Armor_Slot_2="Basic Armor")
        # max(7, 2) = 7, NOT 7 + 2 = 9 -> AC 19, not 21.
        self.assertEqual(cm.get_armor_class(), 19)

    def test_no_character_data_defaults_to_ten(self):
        cm = CharacterManager()
        cm.character_data = {}
        self.assertEqual(cm.get_armor_class(), 10)


if __name__ == "__main__":
    unittest.main()
