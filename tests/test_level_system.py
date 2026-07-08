"""Unit tests for Code/level_system.py progression / unlock logic (roadmap P2 #8).

Covers level initialisation, unlock gating, level completion cascades, and the
deterministic content-count helpers. Each test runs inside a temp working
directory so progression JSON is written to disposable files, never the repo.
"""

import os
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MEGITECH_BACKEND", "pygame")

import pygame  # noqa: E402

pygame.init()

from Code.level_system import LevelManager, WorldLevel, WorldLevelGenerator  # noqa: E402


class LevelManagerTests(unittest.TestCase):
    def setUp(self):
        # Isolate progression file writes inside a throwaway CWD.
        self._prev_cwd = os.getcwd()
        self._tmp = tempfile.mkdtemp(prefix="megitech_levels_")
        os.chdir(self._tmp)
        # LevelManager.save_progression() writes to ./SaveProgression/; create it
        # here so the (temp, disposable) saves succeed rather than being swallowed.
        os.makedirs("SaveProgression", exist_ok=True)
        self.lm = LevelManager(character_name="unit_test")
        # Start from a known clean progression regardless of any stray file.
        self.lm.current_world = 1
        self.lm.current_level = 1
        self.lm.unlocked_levels = {"1-1"}

    def tearDown(self):
        os.chdir(self._prev_cwd)

    def test_initializes_twenty_levels_with_only_first_unlocked(self):
        self.assertEqual(len(self.lm.levels), 20)
        self.assertIn("1-1", self.lm.unlocked_levels)
        self.assertNotIn("1-2", self.lm.unlocked_levels)
        self.assertEqual(self.lm.get_current_level_key(), "1-1")

    def test_cannot_select_locked_level(self):
        self.assertFalse(self.lm.set_current_level(1, 2))  # 1-2 not unlocked yet
        self.assertEqual(self.lm.get_current_level_key(), "1-1")

    def test_unlock_then_select(self):
        self.assertTrue(self.lm.unlock_level(1, 2))
        self.assertTrue(self.lm.set_current_level(1, 2))
        self.assertEqual(self.lm.current_level, 2)

    def test_unlock_nonexistent_level_fails(self):
        self.assertFalse(self.lm.unlock_level(9, 9))
        self.assertNotIn("9-9", self.lm.unlocked_levels)

    def test_complete_level_unlocks_next_in_world(self):
        self.assertTrue(self.lm.complete_current_level())  # on 1-1
        self.assertIn("1-2", self.lm.unlocked_levels)

    def test_completing_boss_level_unlocks_next_world(self):
        self.lm.current_world = 1
        self.lm.current_level = 4  # boss level of world 1
        self.lm.complete_current_level()
        self.assertIn("2-1", self.lm.unlocked_levels)

    def test_get_current_level_returns_worldlevel(self):
        level = self.lm.get_current_level()
        self.assertIsInstance(level, WorldLevel)
        self.assertEqual(level.name, "Green Fields")


class WorldLevelTests(unittest.TestCase):
    def test_display_name_format(self):
        wl = WorldLevel(2, 3, "Frost Citadel", "desc")
        self.assertEqual(wl.get_display_name(), "World 2-3: Frost Citadel")

    def test_defaults_locked(self):
        wl = WorldLevel(1, 1, "X", "desc")
        self.assertFalse(wl.is_unlocked)


class ContentGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.gen = WorldLevelGenerator(level_manager=None)

    def test_enemy_count_for_1_1(self):
        wl = WorldLevel(1, 1, "Green Fields", "d", enemy_multiplier=1.0)
        # base 6 + (level_factor 1 * 2) * 1.0 = 8
        self.assertEqual(self.gen._calculate_enemy_count(wl), 8)

    def test_treasure_count_for_1_1(self):
        wl = WorldLevel(1, 1, "Green Fields", "d", loot_multiplier=1.0)
        # base 3 + level_factor 1 * 1.0 = 4
        self.assertEqual(self.gen._calculate_treasure_count(wl), 4)

    def test_higher_world_scales_up_enemy_count(self):
        low = WorldLevel(1, 1, "a", "d", enemy_multiplier=1.0)
        high = WorldLevel(3, 4, "b", "d", enemy_multiplier=2.8)
        self.assertGreater(
            self.gen._calculate_enemy_count(high),
            self.gen._calculate_enemy_count(low),
        )


if __name__ == "__main__":
    unittest.main()
