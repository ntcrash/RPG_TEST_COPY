"""Tests for helper pets — combat companions (roadmap P5 #32).

Covers the pure pet module (catalog integrity, shop/boss eligibility, the
deterministic per-turn assist math, and the boss-drop roll), the ``PetManager``
ownership/purchase logic on a character save, store integration (pets are for
sale and buy through the pet system), the save-schema migration that backfills
the new ``Pets`` / ``Active_Pet`` fields, and the combat manager applying an
active pet's assist each turn.

Pure/deterministic; runs headlessly on the ``Code.gfx`` shim (no GPU/audio).
Randomness is pinned via a seeded ``random.Random``.
"""

import random
import unittest

from Code import pet_system
from Code.pet_system import (
    PET_CATALOG,
    BOSS_DROP_CHANCE_PERCENT,
    all_pets,
    get_pet,
    shop_pets,
    boss_droppable_pets,
    compute_pet_assist,
    roll_boss_pet_drop,
    PetManager,
)
from Code.save_migration import (
    SAVE_SCHEMA_VERSION,
    migrate_character,
    validate_character,
)


class FakeCharManager:
    """Minimal stand-in for CharacterManager for pet/combat unit tests."""

    def __init__(self, character_data=None):
        self.character_data = character_data
        self.saved = 0

    def save_character(self):
        self.saved += 1

    def get_max_hp_for_level(self, level):
        return 100 + (level - 1) * 10


def fresh_character(**overrides):
    data = {
        "Name": "Hero", "Level": 1, "Hit_Points": 100, "Credits": 1000,
        "Pets": [], "Active_Pet": "",
    }
    data.update(overrides)
    return data


# --- Catalog ---------------------------------------------------------------
class CatalogTests(unittest.TestCase):
    def test_catalog_nonempty_and_unique_ids(self):
        ids = [p["id"] for p in PET_CATALOG]
        self.assertTrue(ids)
        self.assertEqual(len(ids), len(set(ids)), "pet ids must be unique")

    def test_every_pet_has_required_fields(self):
        required = {"id", "name", "assist", "power", "verb",
                    "unlock_level", "price", "source", "description"}
        for pet in PET_CATALOG:
            self.assertTrue(required.issubset(pet), f"{pet.get('id')} missing fields")
            self.assertIn(pet["assist"], ("attack", "heal", "leech"))
            self.assertIn(pet["source"], ("shop", "boss", "both"))
            self.assertGreaterEqual(pet["power"], 1)
            self.assertGreaterEqual(pet["unlock_level"], 1)

    def test_get_pet_returns_copy(self):
        pet = get_pet("wolf")
        self.assertEqual(pet["id"], "wolf")
        pet["power"] = 999  # mutating the copy must not touch the catalog
        self.assertNotEqual(get_pet("wolf")["power"], 999)

    def test_get_pet_unknown(self):
        self.assertIsNone(get_pet("nope"))

    def test_all_pets_matches_catalog(self):
        self.assertEqual(len(all_pets()), len(PET_CATALOG))


# --- Shop / boss eligibility ----------------------------------------------
class EligibilityTests(unittest.TestCase):
    def test_shop_pets_are_buyable_only(self):
        for pet in shop_pets():
            self.assertIn(pet["source"], ("shop", "both"))
            self.assertGreater(pet["price"], 0)

    def test_boss_only_pet_not_in_shop(self):
        shop_ids = {p["id"] for p in shop_pets()}
        self.assertIn("shade", {p["id"] for p in PET_CATALOG})
        self.assertNotIn("shade", shop_ids)

    def test_shop_pets_level_filter(self):
        low = {p["id"] for p in shop_pets(player_level=1)}
        high = {p["id"] for p in shop_pets(player_level=99)}
        self.assertIn("wolf", low)           # unlock 1
        self.assertNotIn("drake", low)       # unlock 5
        self.assertIn("drake", high)
        self.assertTrue(low.issubset(high))

    def test_boss_droppable_respects_level_and_owned(self):
        pool = {p["id"] for p in boss_droppable_pets(10, owned=[])}
        self.assertIn("shade", pool)         # boss-only, unlock 10
        self.assertIn("wolf", pool)          # both, unlock 1
        low = {p["id"] for p in boss_droppable_pets(1)}
        self.assertNotIn("shade", low)       # boss too low level
        owned_pool = {p["id"] for p in boss_droppable_pets(10, owned=["wolf", "shade"])}
        self.assertNotIn("wolf", owned_pool)
        self.assertNotIn("shade", owned_pool)


# --- Assist math -----------------------------------------------------------
class AssistTests(unittest.TestCase):
    def test_attack_assist_scales_with_level(self):
        wolf = get_pet("wolf")  # power 6
        self.assertEqual(compute_pet_assist(wolf, 1)["amount"], 6 + 0)
        self.assertEqual(compute_pet_assist(wolf, 10)["amount"], 6 + 5)
        a = compute_pet_assist(wolf, 4)
        self.assertEqual(a["type"], "attack")
        self.assertEqual(a["amount"], 6 + 2)
        self.assertEqual(a["heal"], 0)

    def test_heal_assist(self):
        a = compute_pet_assist(get_pet("sprite"), 6)  # power 5, +3
        self.assertEqual(a["type"], "heal")
        self.assertEqual(a["amount"], 8)
        self.assertEqual(a["heal"], 8)
        self.assertIn("Healing Sprite", a["message"])

    def test_leech_assist_heals_half(self):
        a = compute_pet_assist(get_pet("phoenix"), 8)  # power 9, +4 => 13
        self.assertEqual(a["type"], "leech")
        self.assertEqual(a["amount"], 13)
        self.assertEqual(a["heal"], 13 // 2)

    def test_assist_deterministic(self):
        wolf = get_pet("wolf")
        self.assertEqual(compute_pet_assist(wolf, 7), compute_pet_assist(wolf, 7))

    def test_assist_none_pet(self):
        self.assertIsNone(compute_pet_assist(None, 5))

    def test_message_contains_pet_name(self):
        for pet in PET_CATALOG:
            self.assertIn(pet["name"], compute_pet_assist(pet, 3)["message"])


# --- Boss drop roll --------------------------------------------------------
class BossDropTests(unittest.TestCase):
    def test_drop_when_roll_succeeds(self):
        # Seed chosen so the first randint(1,100) lands within the drop chance.
        rng = random.Random(1)
        # Find a seed deterministically: brute force a small range.
        for seed in range(200):
            r = random.Random(seed)
            if r.randint(1, 100) <= BOSS_DROP_CHANCE_PERCENT:
                rng = random.Random(seed)
                break
        pet_id = roll_boss_pet_drop(fresh_character(), boss_level=10, rng=rng)
        self.assertIsNotNone(pet_id)
        self.assertIsNotNone(get_pet(pet_id))

    def test_no_drop_when_roll_fails(self):
        for seed in range(200):
            r = random.Random(seed)
            if r.randint(1, 100) > BOSS_DROP_CHANCE_PERCENT:
                rng = random.Random(seed)
                break
        self.assertIsNone(roll_boss_pet_drop(fresh_character(), 10, rng=rng))

    def test_no_drop_when_pool_empty(self):
        # Own every boss-droppable pet -> nothing left to drop.
        owned = [p["id"] for p in PET_CATALOG if p["source"] in ("boss", "both")]
        cd = fresh_character(Pets=owned)
        self.assertIsNone(roll_boss_pet_drop(cd, 99, rng=random.Random(0)))

    def test_non_dict_char_data(self):
        self.assertIsNone(roll_boss_pet_drop(None, 10))


# --- PetManager ------------------------------------------------------------
class PetManagerTests(unittest.TestCase):
    def setUp(self):
        self.cm = FakeCharManager(fresh_character())
        self.pm = PetManager(self.cm)

    def test_no_character_is_safe(self):
        pm = PetManager(FakeCharManager(None))
        self.assertEqual(pm.owned_pet_ids(), [])
        self.assertIsNone(pm.active_pet())
        self.assertFalse(pm.own_pet("wolf"))
        self.assertEqual(pm.buy_pet("wolf")["result"], "no_character")

    def test_own_first_pet_auto_active(self):
        self.assertTrue(self.pm.own_pet("wolf", make_active=False))
        self.assertEqual(self.cm.character_data["Active_Pet"], "wolf")
        self.assertEqual(self.pm.owned_pet_ids(), ["wolf"])

    def test_own_duplicate_returns_false(self):
        self.pm.own_pet("wolf")
        self.assertFalse(self.pm.own_pet("wolf"))
        self.assertEqual(self.pm.owned_pet_ids().count("wolf"), 1)

    def test_own_unknown_pet_rejected(self):
        self.assertFalse(self.pm.own_pet("dragonzord"))

    def test_set_active_requires_ownership(self):
        self.assertFalse(self.pm.set_active("drake"))
        self.pm.own_pet("drake")
        self.assertTrue(self.pm.set_active("drake"))
        self.assertTrue(self.pm.set_active(""))  # clearing is allowed
        self.assertEqual(self.cm.character_data["Active_Pet"], "")

    def test_active_pet_ignores_stale_id(self):
        self.cm.character_data["Active_Pet"] = "wolf"  # not in Pets
        self.assertIsNone(self.pm.active_pet())
        self.pm.own_pet("wolf")
        self.assertEqual(self.pm.active_pet()["id"], "wolf")

    def test_buy_pet_success_deducts_credits(self):
        self.cm.character_data["Credits"] = 1000
        out = self.pm.buy_pet("wolf")  # price 800, unlock 1
        self.assertEqual(out["result"], "purchased")
        self.assertEqual(self.cm.character_data["Credits"], 200)
        self.assertTrue(self.pm.owns("wolf"))

    def test_buy_pet_insufficient_funds(self):
        self.cm.character_data["Credits"] = 100
        out = self.pm.buy_pet("wolf")
        self.assertEqual(out["result"], "insufficient_funds")
        self.assertEqual(out["needed"], 700)
        self.assertFalse(self.pm.owns("wolf"))
        self.assertEqual(self.cm.character_data["Credits"], 100)  # unchanged

    def test_buy_pet_level_locked(self):
        self.cm.character_data["Credits"] = 99999
        self.cm.character_data["Level"] = 1
        out = self.pm.buy_pet("drake")  # unlock 5
        self.assertEqual(out["result"], "level_locked")
        self.assertEqual(out["needed"], 5)

    def test_buy_pet_boss_only_not_for_sale(self):
        self.cm.character_data["Credits"] = 99999
        self.assertEqual(self.pm.buy_pet("shade")["result"], "not_for_sale")

    def test_buy_pet_already_owned(self):
        self.cm.character_data["Credits"] = 99999
        self.pm.buy_pet("wolf")
        self.assertEqual(self.pm.buy_pet("wolf")["result"], "already_owned")


# --- Save migration --------------------------------------------------------
class MigrationTests(unittest.TestCase):
    def test_schema_version_bumped(self):
        self.assertGreaterEqual(SAVE_SCHEMA_VERSION, 2)

    def test_migrate_backfills_pet_fields(self):
        data, changed, notes = migrate_character({})
        self.assertTrue(changed)
        self.assertEqual(data["Pets"], [])
        self.assertEqual(data["Active_Pet"], "")
        self.assertEqual(data["Save_Version"], SAVE_SCHEMA_VERSION)

    def test_migrate_resets_bad_pets_type(self):
        data, changed, _ = migrate_character({"Pets": "wolf"})
        self.assertEqual(data["Pets"], [])
        self.assertTrue(changed)

    def test_migrate_preserves_existing_pets(self):
        data, _, _ = migrate_character({"Pets": ["wolf"], "Active_Pet": "wolf"})
        self.assertEqual(data["Pets"], ["wolf"])
        self.assertEqual(data["Active_Pet"], "wolf")

    def test_validate_flags_missing_pets(self):
        issues = validate_character({})
        self.assertTrue(any("Pets" in i for i in issues))

    def test_validate_clean_after_migrate(self):
        data, _, _ = migrate_character({})
        self.assertEqual(validate_character(data), [])


# --- Store integration -----------------------------------------------------
class StoreIntegrationTests(unittest.TestCase):
    def setUp(self):
        from Code.store_system import StoreManager
        self.cm = FakeCharManager(fresh_character(Credits=5000, Level=5))
        self.store = StoreManager(self.cm)

    def _select(self, name):
        for i, item in enumerate(self.store.items):
            if item.name == name:
                self.store.selected_item = i
                return item
        raise AssertionError(f"{name} not in store")

    def test_pets_listed_in_store(self):
        pet_rows = [it for it in self.store.items if it.item_type == "pet"]
        self.assertTrue(pet_rows)
        names = {it.name for it in pet_rows}
        self.assertIn("Dire Wolf", names)
        self.assertNotIn("Void Shade", names)  # boss-only

    def test_buy_pet_through_store(self):
        self._select("Dire Wolf")
        result = self.store.attempt_purchase()
        self.assertEqual(result["result"], "purchased")
        self.assertIn("wolf", self.cm.character_data["Pets"])
        self.assertEqual(self.cm.character_data["Credits"], 5000 - 800)
        # Pets are not stuffed into the item Inventory.
        self.assertNotIn("Dire Wolf", self.cm.character_data.get("Inventory", {}))
        self.assertGreaterEqual(self.cm.saved, 1)

    def test_buy_pet_insufficient_funds_through_store(self):
        self.cm.character_data["Credits"] = 10
        self._select("Dire Wolf")
        result = self.store.attempt_purchase()
        self.assertEqual(result["result"], "insufficient_funds")
        self.assertNotIn("wolf", self.cm.character_data["Pets"])


# --- Combat integration (assist application) -------------------------------
class CombatAssistTests(unittest.TestCase):
    def _combat(self, char_data):
        from Code.enhanced_combat_system import EnhancedCombatManager
        cm = FakeCharManager(char_data)
        combat = EnhancedCombatManager(cm)
        combat.current_enemy = {"Name": "Goblin", "Hit_Points": 100, "Level": 3}
        return combat

    def test_attack_pet_damages_enemy(self):
        cd = fresh_character(Level=1, Pets=["wolf"], Active_Pet="wolf")
        combat = self._combat(cd)
        combat.pet_assist_turn()
        self.assertEqual(combat.current_enemy["Hit_Points"], 100 - 6)

    def test_heal_pet_restores_player_hp(self):
        cd = fresh_character(Level=6, Hit_Points=50, Pets=["sprite"], Active_Pet="sprite")
        combat = self._combat(cd)
        combat.pet_assist_turn()
        self.assertEqual(cd["Hit_Points"], 50 + 8)  # power 5 + level//2 (3)

    def test_heal_pet_does_not_overheal(self):
        cd = fresh_character(Level=6, Hit_Points=100, Pets=["sprite"], Active_Pet="sprite")
        combat = self._combat(cd)
        max_hp = combat.character_manager.get_max_hp_for_level(6)
        combat.pet_assist_turn()
        self.assertLessEqual(cd["Hit_Points"], max_hp)

    def test_leech_pet_damages_and_heals(self):
        cd = fresh_character(Level=8, Hit_Points=50, Pets=["phoenix"], Active_Pet="phoenix")
        combat = self._combat(cd)
        combat.pet_assist_turn()
        self.assertEqual(combat.current_enemy["Hit_Points"], 100 - 13)
        self.assertEqual(cd["Hit_Points"], 50 + 13 // 2)

    def test_no_active_pet_is_noop(self):
        cd = fresh_character(Level=5)
        combat = self._combat(cd)
        combat.pet_assist_turn()
        self.assertEqual(combat.current_enemy["Hit_Points"], 100)

    def test_assist_can_finish_enemy(self):
        cd = fresh_character(Level=1, Pets=["wolf"], Active_Pet="wolf")
        combat = self._combat(cd)
        combat.current_enemy["Hit_Points"] = 3
        combat.pet_assist_turn()
        self.assertLessEqual(combat.current_enemy["Hit_Points"], 0)


if __name__ == "__main__":
    unittest.main()
