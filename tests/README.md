# Tests

Unit tests for Magitech RPG's pure-logic modules (roadmap P2 #8). These cover
combat math, level progression, and crafting logic without needing a display or
audio device — `tests/__init__.py` forces SDL's dummy video/audio drivers so the
Pygame-coupled modules import cleanly in headless environments (CI, containers).

## Running

From the repository root:

```bash
python -m unittest discover -s tests -v
```

No third-party test runner is required — everything uses the standard-library
`unittest`. Pygame must be installed (`pip install -r requirements.txt`).

## Coverage

- `test_combat_system.py` — `CombatManager.calculate_damage`,
  `calculate_spell_damage`, `calculate_hit_chance`, and `SpellManager`
  level-gated spell availability. Randomness is pinned with `mock.patch`.
- `test_level_system.py` — `LevelManager` unlock/selection/completion cascades
  and `WorldLevelGenerator` content-count helpers.
- `test_crafting_system.py` — recipe/material catalog, level-gated recipe
  availability, rarity colours, and the random material drop table.
- `test_spawn_accessibility.py` — world-item placement invariants (bounds,
  walkability, clearance around reserved zones) across many seeds.
- `test_gfx.py` — the `Code/gfx.py` Pygame→Arcade rendering shim: coordinate
  Y-flip, color/rect normalization, `_safe_text` emoji stripping, the `Rect`
  API, off-screen surface record/replay + `pygame.draw.*` op recording, `Font`
  metric fallback, and key/event constants. Forces the no-arcade code path so it
  runs deterministically headless with or without `arcade` installed.
