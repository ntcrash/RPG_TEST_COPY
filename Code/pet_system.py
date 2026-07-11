"""Helper pets — combat companions (roadmap P5 #32).

Pets are companion creatures that assist the player in combat. A pet is
acquired one of two ways: as a random drop for **defeating a boss**, or by
**buying it from the shop**. Once a pet is owned and set active, it performs an
automatic *assist* every combat round — striking the enemy, mending the
player's wounds, or a bit of both — scaled by the pet's power and the player's
level.

This module is deliberately pure and free of any rendering / audio so it can be
unit-tested headlessly and shared by every consumer:

* ``Code/enhanced_combat_system.py`` calls :func:`compute_pet_assist` each turn
  and applies the result to the enemy / player HP it owns.
* ``Code/enhanced_combat_integration.py`` rolls :func:`roll_boss_pet_drop` on a
  boss victory.
* ``Code/store_system.py`` lists :func:`shop_pets` for sale and buys via
  :meth:`PetManager.own_pet`.

Ownership lives on the character save (see ``Code/save_migration.py``):

    character_data["Pets"]        -> list of owned pet ids (acquisition order)
    character_data["Active_Pet"]  -> id of the pet currently assisting ("" = none)
"""

import random

# --- Pet catalog ------------------------------------------------------------
# Each pet is a plain dict so it round-trips through JSON/tests with no class.
#   id           : stable key stored on the save
#   name         : display name
#   description  : shop / detail blurb
#   assist       : "attack" (damage enemy), "heal" (restore player HP), or
#                  "leech" (damage enemy + heal player for half)
#   power        : base assist amount before the per-level bonus
#   verb         : third-person verb used in the combat-log message
#   unlock_level : minimum player level to buy / for a boss to drop it
#   price        : shop cost in credits (0 == not sold, boss-only)
#   source       : "shop" (buy only), "boss" (drop only), or "both"
#
# Amounts are intentionally modest: a pet is a steady chip of extra value each
# round, not a replacement for the player's own attacks/spells. The premium and
# boss-only pets hit harder and unlock later so acquisition stays a progression.
PET_CATALOG = (
    {
        "id": "wolf", "name": "Dire Wolf", "assist": "attack", "power": 6,
        "verb": "mauls", "unlock_level": 1, "price": 800, "source": "both",
        "description": "A loyal wolf that mauls your foe for extra damage each turn.",
    },
    {
        "id": "sprite", "name": "Healing Sprite", "assist": "heal", "power": 5,
        "verb": "mends", "unlock_level": 2, "price": 1200, "source": "both",
        "description": "A gentle sprite that mends your wounds a little each turn.",
    },
    {
        "id": "drake", "name": "Ember Drake", "assist": "attack", "power": 11,
        "verb": "scorches", "unlock_level": 5, "price": 2400, "source": "both",
        "description": "A young dragon that scorches the enemy with dragonfire.",
    },
    {
        "id": "phoenix", "name": "Phoenix", "assist": "leech", "power": 9,
        "verb": "sears", "unlock_level": 8, "price": 4000, "source": "both",
        "description": "Sears the enemy and channels half the life back to you.",
    },
    {
        "id": "shade", "name": "Void Shade", "assist": "attack", "power": 15,
        "verb": "rends", "unlock_level": 10, "price": 0, "source": "boss",
        "description": "A shadow bound to you by conquering a boss; rends with dark power.",
    },
)

# Index for O(1) id lookup.
_PET_BY_ID = {pet["id"]: pet for pet in PET_CATALOG}

# Percent chance a boss victory drops a (new, eligible) pet.
BOSS_DROP_CHANCE_PERCENT = 35

# Log colours (RGB) — kept here so the module has no ui_components dependency.
_ATTACK_COLOR = (255, 170, 60)   # warm orange
_HEAL_COLOR = (80, 230, 120)     # green


def all_pets():
    """Return the full pet catalog (list of dict copies)."""
    return [dict(pet) for pet in PET_CATALOG]


def get_pet(pet_id):
    """Return the catalog entry (a copy) for ``pet_id``, or ``None``."""
    pet = _PET_BY_ID.get(pet_id)
    return dict(pet) if pet else None


def shop_pets(player_level=None):
    """Pets available to buy, optionally filtered to the player's level.

    A pet is buyable when its ``source`` is ``"shop"`` or ``"both"`` and it has
    a positive price. When ``player_level`` is given, only pets whose
    ``unlock_level`` the player has reached are returned.
    """
    out = []
    for pet in PET_CATALOG:
        if pet["source"] not in ("shop", "both") or pet["price"] <= 0:
            continue
        if player_level is not None and player_level < pet["unlock_level"]:
            continue
        out.append(dict(pet))
    return out


def boss_droppable_pets(boss_level, owned=None):
    """Pets a boss of ``boss_level`` can drop that the player does not own yet.

    Eligible when ``source`` is ``"boss"`` or ``"both"`` and the boss level is
    at least the pet's ``unlock_level``.
    """
    owned = set(owned or ())
    out = []
    for pet in PET_CATALOG:
        if pet["source"] not in ("boss", "both"):
            continue
        if pet["id"] in owned:
            continue
        if boss_level < pet["unlock_level"]:
            continue
        out.append(dict(pet))
    return out


def compute_pet_assist(pet, player_level):
    """Compute a pet's per-turn assist as a plain, display-free dict.

    Pure and deterministic (no randomness) so combat is predictable and the
    math is trivially testable. Returns a dict with keys:

        type    : "attack", "heal", or "leech"
        amount  : damage dealt to the enemy (attack/leech) or HP restored (heal)
        heal    : HP returned to the player (leech only; 0 otherwise)
        message : combat-log line (no raw number; the floating text shows it)
        color   : RGB tuple for the log line

    The amount is ``power`` plus a modest ``player_level // 2`` scaling bonus,
    so a companion stays relevant as the hero grows without outshining them.
    """
    if not pet:
        return None
    level = max(1, int(player_level or 1))
    bonus = level // 2
    amount = max(1, int(pet["power"]) + bonus)
    name = pet["name"]
    verb = pet.get("verb", "helps")
    assist = pet["assist"]

    if assist == "heal":
        return {
            "type": "heal", "amount": amount, "heal": amount,
            "message": f"{name} {verb} your wounds!", "color": _HEAL_COLOR,
        }
    if assist == "leech":
        heal = max(1, amount // 2)
        return {
            "type": "leech", "amount": amount, "heal": heal,
            "message": f"{name} {verb} the enemy and heals you!",
            "color": _ATTACK_COLOR,
        }
    # default / "attack"
    return {
        "type": "attack", "amount": amount, "heal": 0,
        "message": f"{name} {verb} the enemy!", "color": _ATTACK_COLOR,
    }


def roll_boss_pet_drop(char_data, boss_level, rng=random):
    """Maybe award a pet for beating a boss; return the dropped pet id or None.

    With :data:`BOSS_DROP_CHANCE_PERCENT` probability, picks a random pet the
    boss is eligible to drop and the player does not already own. ``rng`` is
    injectable so tests can pin the outcome. Does **not** mutate ``char_data`` —
    the caller records ownership via :class:`PetManager`.
    """
    if not isinstance(char_data, dict):
        return None
    owned = char_data.get("Pets", []) or []
    pool = boss_droppable_pets(boss_level, owned)
    if not pool:
        return None
    if rng.randint(1, 100) > BOSS_DROP_CHANCE_PERCENT:
        return None
    return rng.choice(pool)["id"]


class PetManager:
    """Read/write the player's owned pets and active companion on the save.

    Thin wrapper over ``character_manager.character_data``; every mutation is
    reflected straight onto the live character dict so the existing
    ``save_character`` flow persists it. Safe to construct with no loaded
    character (all queries degrade to empty / no-op).
    """

    def __init__(self, character_manager):
        self.character_manager = character_manager

    # -- internal helpers ----------------------------------------------------
    @property
    def _cd(self):
        return getattr(self.character_manager, "character_data", None)

    def _ensure_fields(self, cd):
        if not isinstance(cd.get("Pets"), list):
            cd["Pets"] = []
        if not isinstance(cd.get("Active_Pet"), str):
            cd["Active_Pet"] = ""

    # -- queries -------------------------------------------------------------
    def owned_pet_ids(self):
        """List of owned pet ids (copy)."""
        cd = self._cd
        if not cd:
            return []
        pets = cd.get("Pets", [])
        return list(pets) if isinstance(pets, list) else []

    def owns(self, pet_id):
        return pet_id in self.owned_pet_ids()

    def active_pet_id(self):
        cd = self._cd
        if not cd:
            return ""
        pid = cd.get("Active_Pet", "")
        return pid if isinstance(pid, str) else ""

    def active_pet(self):
        """Catalog entry for the active pet, or ``None``.

        Returns None if there is no active pet, the active id is not owned, or
        the id is not a known catalog pet (stale save).
        """
        pid = self.active_pet_id()
        if not pid or not self.owns(pid):
            return None
        return get_pet(pid)

    # -- mutations -----------------------------------------------------------
    def own_pet(self, pet_id, make_active=True):
        """Record ``pet_id`` as owned. Returns True if newly added.

        The first pet a player ever owns is auto-set active; subsequent pets
        are made active only when ``make_active`` is True.
        """
        cd = self._cd
        if not cd or get_pet(pet_id) is None:
            return False
        self._ensure_fields(cd)
        if pet_id in cd["Pets"]:
            return False
        first_pet = len(cd["Pets"]) == 0
        cd["Pets"].append(pet_id)
        if make_active or first_pet or not cd["Active_Pet"]:
            cd["Active_Pet"] = pet_id
        return True

    def set_active(self, pet_id):
        """Set the active pet. ``""`` clears it. Returns True on success."""
        cd = self._cd
        if not cd:
            return False
        self._ensure_fields(cd)
        if pet_id == "":
            cd["Active_Pet"] = ""
            return True
        if pet_id not in cd["Pets"]:
            return False
        cd["Active_Pet"] = pet_id
        return True

    def buy_pet(self, pet_id):
        """Purchase a pet from the shop, deducting credits.

        Returns a result dict mirroring the store's convention:
          {"result": "purchased", "pet": name}
          {"result": "already_owned"}
          {"result": "not_for_sale"}
          {"result": "level_locked", "needed": unlock_level}
          {"result": "insufficient_funds", "needed": credits_short}
          {"result": "no_character"}
        """
        cd = self._cd
        if not cd:
            return {"result": "no_character"}
        pet = get_pet(pet_id)
        if pet is None or pet["source"] not in ("shop", "both") or pet["price"] <= 0:
            return {"result": "not_for_sale"}
        if self.owns(pet_id):
            return {"result": "already_owned"}
        level = int(cd.get("Level", 1) or 1)
        if level < pet["unlock_level"]:
            return {"result": "level_locked", "needed": pet["unlock_level"]}
        credits = int(cd.get("Credits", 0) or 0)
        if credits < pet["price"]:
            return {"result": "insufficient_funds", "needed": pet["price"] - credits}
        cd["Credits"] = credits - pet["price"]
        self.own_pet(pet_id, make_active=True)
        return {"result": "purchased", "pet": pet["name"]}
