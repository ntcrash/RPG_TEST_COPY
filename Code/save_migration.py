"""Save-file schema versioning + lightweight migration/validation.

Character saves (``Characters/*.json``) are live player state written by the
running game. Over the project's history the combat/stat formulas and the set of
fields a character carries have changed (e.g. the v1.7.3 spell-damage
level-scaling rework), and older saves on disk can be missing keys that newer
code reads by direct index (``character_data["Aspect1_Mana"]`` and friends). A
missing key there is an uncaught ``KeyError`` that crashes mid-combat.

This module gives saves a versioned schema (``Save_Version``) and a single,
dependency-free ``migrate_character`` pass that:

* backfills every required field with a sensible default,
* coerces numeric fields to ``int`` (clamping the ones that must be >= 0),
* guarantees ``Inventory`` is a dict and the six ability scores exist,
* stamps the current ``SAVE_SCHEMA_VERSION``.

It is intentionally conservative: it only *adds* missing structure and fixes
obviously-wrong types. It never deletes unknown keys, so hand-authored or
future fields survive a round-trip untouched. ``CharacterManager.load_character``
runs this on every load and re-saves when anything changed, so an old save is
healed the first time it is opened rather than silently breaking later.
"""

# Bump this whenever the required-field set or a coercion rule changes so that
# older saves are detectably out of date and get re-written on next load.
SAVE_SCHEMA_VERSION = 1

# The six D&D-style ability scores the game reads via the lowercase key
# (see CharacterManager.get_base_stat, which lowercases and defaults to 10).
STAT_KEYS = (
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
)

# Required top-level fields and their defaults for a brand-new/partial save.
# Mirrors CharacterManager.create_sample_character so a migrated save is
# indistinguishable in shape from a freshly created one.
FIELD_DEFAULTS = {
    "Name": "Unknown Hero",
    "Race": "Human",
    "Type": "War Mage",
    "Level": 1,
    "Hit_Points": 100,
    "Credits": 0,
    "Experience_Points": 0,
    "Aspect1": "fire_level_1",
    "Aspect1_Mana": 50,
    "Weapon1": "Hands",
    "Weapon2": "Hands",
    "Weapon3": "Hands",
    "Armor_Slot_1": "",
    "Armor_Slot_2": "",
}

# Fields that must be whole numbers.
INT_FIELDS = ("Level", "Hit_Points", "Credits", "Experience_Points", "Aspect1_Mana")
# Numeric fields that must never go negative.
NON_NEGATIVE_FIELDS = ("Hit_Points", "Credits", "Experience_Points", "Aspect1_Mana")


def _coerce_int(value, default):
    """Best-effort conversion of a stored value to int; ``default`` on failure."""
    if isinstance(value, bool):  # bool is a subclass of int; treat as invalid here
        return default
    if isinstance(value, int):
        return value
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def validate_character(data):
    """Return a list of human-readable issues with ``data`` (empty == clean).

    Read-only: does not modify ``data``. Handy for tests and diagnostics.
    """
    issues = []
    if not isinstance(data, dict):
        return [f"save is not a JSON object (got {type(data).__name__})"]

    for field in FIELD_DEFAULTS:
        if field not in data:
            issues.append(f"missing field: {field}")
    for field in INT_FIELDS:
        if field in data and not isinstance(data[field], int):
            issues.append(f"non-int field: {field}={data[field]!r}")
    for stat in STAT_KEYS:
        if stat not in data:
            issues.append(f"missing ability score: {stat}")
    if "Inventory" not in data:
        issues.append("missing field: Inventory")
    elif not isinstance(data["Inventory"], dict):
        issues.append(f"Inventory is not an object: {data['Inventory']!r}")
    if data.get("Save_Version") != SAVE_SCHEMA_VERSION:
        issues.append(
            f"schema out of date: Save_Version={data.get('Save_Version')!r} "
            f"(current {SAVE_SCHEMA_VERSION})"
        )
    return issues


def migrate_character(data):
    """Heal a loaded character dict in place-ish and stamp the schema version.

    Returns ``(migrated_dict, changed, notes)`` where ``changed`` is True if any
    field was added or coerced and ``notes`` is a list of what was done. A
    non-dict input is replaced wholesale with a default character.
    """
    notes = []

    if not isinstance(data, dict):
        notes.append(f"replaced non-object save ({type(data).__name__}) with defaults")
        data = {}
        changed = True
    else:
        changed = False

    # Backfill required string/scalar fields.
    for field, default in FIELD_DEFAULTS.items():
        if field not in data:
            data[field] = default
            notes.append(f"added {field}={default!r}")
            changed = True

    # Coerce numeric fields and clamp the non-negative ones.
    for field in INT_FIELDS:
        original = data.get(field)
        coerced = _coerce_int(original, FIELD_DEFAULTS.get(field, 0))
        if field in NON_NEGATIVE_FIELDS and coerced < 0:
            coerced = 0
        if coerced != original or not isinstance(original, int):
            data[field] = coerced
            if coerced != original:
                notes.append(f"coerced {field}: {original!r} -> {coerced}")
                changed = True

    # Ensure the six ability scores exist.
    for stat in STAT_KEYS:
        if stat not in data:
            data[stat] = 10
            notes.append(f"added ability score {stat}=10")
            changed = True
        else:
            coerced = _coerce_int(data[stat], 10)
            if coerced != data[stat]:
                notes.append(f"coerced {stat}: {data[stat]!r} -> {coerced}")
                data[stat] = coerced
                changed = True

    # Inventory must be a dict of item -> count.
    inv = data.get("Inventory")
    if not isinstance(inv, dict):
        data["Inventory"] = {}
        notes.append("reset Inventory to empty object")
        changed = True

    # Stamp the schema version last.
    if data.get("Save_Version") != SAVE_SCHEMA_VERSION:
        data["Save_Version"] = SAVE_SCHEMA_VERSION
        notes.append(f"stamped Save_Version={SAVE_SCHEMA_VERSION}")
        changed = True

    return data, changed, notes
