"""Unit tests for Code/crafting_system.py recipe / material logic (roadmap P2 #8).

Covers recipe/material initialisation, level-gated recipe availability, rarity
colour lookup, and the random material drop table. The inventory-mutating paths
(`can_craft_recipe` / `craft_item`) are intentionally out of scope here because
they pull in the full InventoryManager + on-disk character save; this suite
stays on the pure logic.
"""

import os
import unittest
from unittest import mock

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("MEGITECH_BACKEND", "arcade")

from Code.backend import pygame  # noqa: E402  (default: Code.gfx shim)

pygame.init()

from Code import crafting_system as cs  # noqa: E402
from Code.crafting_system import (  # noqa: E402
    CraftingManager,
    CraftingMaterial,
    CraftingRecipe,
    get_random_crafting_material,
)


class _FakeCharacterManager:
    """Minimal stand-in exposing only what CraftingManager reads."""

    def __init__(self, level):
        self.character_data = {"Level": level}


class RecipeAvailabilityTests(unittest.TestCase):
    def test_level_1_gets_only_starter_recipes(self):
        mgr = CraftingManager(_FakeCharacterManager(1))
        available = mgr.get_available_recipes()
        names = {r.name for r in available}
        self.assertEqual(names, {"Iron Sword", "Leather Armor"})

    def test_high_level_unlocks_all_recipes(self):
        mgr = CraftingManager(_FakeCharacterManager(10))
        self.assertEqual(len(mgr.get_available_recipes()), len(mgr.recipes))

    def test_no_character_data_returns_empty(self):
        mgr = CraftingManager(_FakeCharacterManager(1))
        mgr.character_manager.character_data = None
        self.assertEqual(mgr.get_available_recipes(), [])

    def test_available_recipes_respect_level_requirement(self):
        mgr = CraftingManager(_FakeCharacterManager(5))
        for recipe in mgr.get_available_recipes():
            self.assertLessEqual(recipe.level_required, 5)


class MaterialTests(unittest.TestCase):
    def setUp(self):
        self.mgr = CraftingManager(_FakeCharacterManager(1))

    def test_material_catalog_size(self):
        self.assertEqual(len(self.mgr.crafting_materials), 15)

    def test_rarity_color_known_material(self):
        self.assertEqual(self.mgr.get_material_rarity_color("Iron Ore"), cs.GRAY)

    def test_rarity_color_unknown_defaults_white(self):
        self.assertEqual(self.mgr.get_material_rarity_color("Unobtainium"), cs.WHITE)

    def test_material_defaults_to_common(self):
        mat = CraftingMaterial("Test Ore")
        self.assertEqual(mat.rarity, "Common")


class RecipeDataclassTests(unittest.TestCase):
    def test_recipe_fields(self):
        recipe = CraftingRecipe(
            "Iron Sword", {"Iron Ore": 3, "Wood": 1}, "Iron Sword", 1, 1, "Basic", "Weapon"
        )
        self.assertEqual(recipe.result_item, "Iron Sword")
        self.assertEqual(recipe.level_required, 1)
        self.assertEqual(recipe.materials_required["Iron Ore"], 3)
        self.assertEqual(recipe.recipe_type, "Weapon")


class RandomDropTests(unittest.TestCase):
    COMMON = {"Iron Ore", "Wood", "Leather", "Cloth", "Stone"}
    LEGENDARY = {"Starfire Essence", "Time Crystal"}

    def test_low_roll_common_drop_from_weak_enemy(self):
        with mock.patch("Code.crafting_system.random.randint", return_value=1):
            material = get_random_crafting_material(enemy_level=1)
        self.assertIn(material, self.COMMON)

    def test_high_roll_yields_no_drop(self):
        with mock.patch("Code.crafting_system.random.randint", return_value=100):
            material = get_random_crafting_material(enemy_level=1)
        self.assertIsNone(material)

    def test_treasure_legendary_branch(self):
        with mock.patch("Code.crafting_system.random.randint", return_value=3):
            material = get_random_crafting_material(from_treasure=True)
        self.assertIn(material, self.LEGENDARY)


if __name__ == "__main__":
    unittest.main()
