# Megitech RPG — Automation Roadmap

Living backlog of work sized for autonomous/agent-driven execution. Generated 2026-07-07 from `README.md`, `CHANGELOG.md`, `HELP.md`, and a repo scan of `main.py` + `Code/`.

## How to work this list

- Gitflow: branch every item off `develop` as `feature/<slug>` (or `hotfix/<slug>` for P0 bugs), never commit directly to `main`.
- Version every merge: bump the version in `CHANGELOG.md` following the existing `MM/DD/YYYY - vX.Y.Z` convention and tag releases going forward
- Push every commit to `develop` per project convention.
- Check an item off by moving it to a `## Done` section with the commit hash and date, not by deleting it.

---

## P0 — Known bugs (carried from CHANGELOG.md ToDo)

## P1 — Repo hygiene (blocks safe automation)

1. [Release] **Continue to migrate the code from pygame to Arcade** Keep working on this step until it has been completely migrated. 
7. [Hotfix] **Add `requirements.txt`** — no dependency manifest exists; README states pygame 2.6.1 on Python 3.11 as the only real dependency, but pinning it removes an onboarding/automation guesswork step.

## P2 — Testing & CI (enables safe automated changes)

_(all items complete — see Done)_

## P3 — Documentation debt

11. [Hotfix] **Sync `README.md` architecture section with actual code** — README's "Recent Changes" section is frozen at a 2025-09-08 Replit import note; the file-structure list references `game_states.py` as entry point, but that file was renamed to `main.py` back in v1.6 per CHANGELOG. Update README to reflect current `main.py` + `Code/` module layout.
12. [Hotfix] **Reconcile version history** — CHANGELOG.md's early history (v20–v29, "GUI Client for Multiplayer") describes a multiplayer/server architecture (`NetworkManager_Class.py`, `Server_v1`–`v3`) that no longer appears in the current single-player codebase. Either archive that history clearly as "legacy multiplayer branch, discontinued" or confirm if multiplayer is still a live goal — affects whether future roadmap items should plan around a server component.

## P4 — Feature ideas (lower priority, larger scope)

14. [Hotfix] **Automated save-file migration check** — with a versioned save schema (`Characters/*.json`), add a lightweight migration/validation step so old saves don't silently break on load after combat/stat formula changes (e.g., the v1.7.3 spell-damage level-scaling change).
15. [Feature] **Difficulty/balance regression checks** — CHANGELOG shows multiple past hotfixes for difficulty multiplier and stat scaling bugs (v1.4.1, v1.7.3). Once #8's test suite exists, add regression tests pinning expected damage/AC output for a few reference character/enemy stat combos to catch future balance regressions automatically.
---

## P5 - Visual Enhancements
25. [Feature] **Animated Trees**: Enhance tree graphics and Swaying animation and color changes based on harvestable status
26. [Feature] **Resource Nodes**: Visual feedback showing when objects can be harvested vs depleted
27. [Feature] **Mystical Dungeons**: Animated portal entrances with glowing magical effects and floating particles
28. [Feature] **"BOSS DUNGEON" Text**: Golden glow effects and mystical styling
29. [Feature] **Special Victory Messages**: Boss defeats show trophy emojis and enhanced formatting
30. [Feature] **World Aesthetics**: Cleaner grass-based terrain without flower clutter
31. [Feature] **Structured Paths**: Clear walking routes toward important areas
32. [Feature] **Add helper pets** Add companion pets that can assist in combat, you would have to earn from loot of a boss, or buy
33. [Feature] **Add more spells** add more spells for different classes and based on character level

## P6 - Multi-player Enhancements

40. [Release] **Change version number to v3.0.1 - Add multi player** add multi player with server / client setup, using the existing client and added the server components, single player mode should not change
41. [Feature] **Add account creation** Add account, and characters under the account for multi player, single player should not change


## In Progress

- **pygame → Arcade GUI migration** (MAJOR, v2.x) — started 07/07/2026 on `feature/v2-arcade`, foundation released as **v2.0.1**. Added `Code/version.py` (central `__version__`), `Code/gfx.py` (pygame→Arcade compat shim with automatic y-axis flip), and `arcade_app.py` (new `arcade.Window` entry point driving the existing state machine at 15 Hz via translated key/text events). Legacy `python main.py` (pygame) stays runnable throughout.
  - **v2.0.5 (07/07/2026)** — backend now switches end-to-end. **Key finding**: per-module `import pygame` swaps are a no-op because `Code/ui_components.py` star-exports its `pygame` binding to every module + `main.py`, so the star import always wins. Fixed the real mechanism instead: (1) `ui_components` selects the backend from `MEGITECH_BACKEND` (unset→pygame, `arcade`→`Code.gfx`) and star-exports it everywhere; (2) `arcade_app` sets the env var so its window renders through the shim; (3) `gfx` became a **hybrid** — non-render attrs (`mixer`/`time`/`display`/`event`/`key`/`sprite`/`locals`/…) delegate to real pygame via module `__getattr__`, and `Surface` now records+replays **off-screen** draws (HUD overlay + tile-sheet `area` blits), with y-flip and sub-rect clipping. Headless stub tests (5) pass; `python main.py` unchanged.
  - **v2.1.5 (07/09/2026)** — migrated the two modules that do NOT star-import `ui_components` (so the runtime switch could not reach them): `tile_map` and `animated_player`. Added `Code/backend.py` — a DRY single-source-of-truth switch (`from Code.backend import pygame`, same `MEGITECH_BACKEND` logic as `ui_components`) and pointed both modules at it. Extended `Code/gfx.py` to cover their sprite-sheet needs: `Surface.subsurface(rect)` (frame extraction) and texture-backed `blit(..., area)` now **crop** the sheet to the requested cell (`_crop_texture` via `Texture.crop`, PIL-crop fallback). Import-verified headlessly on-device under BOTH backends (`SDL_VIDEODRIVER=dummy` and `+MEGITECH_BACKEND=arcade`): 17/18 modules import clean in each mode.
  - **Per-module migration status** (import route → backend when `MEGITECH_BACKEND=arcade`):
    - ✅ via `ui_components` star-switch (no per-file change needed, confirmed no-op): `character_creation`, `combat_system`, `combat_integration`, `crafting_system`, `enhanced_combat_system`, `enhanced_combat_integration`, `inventory_system`, `level_system`, `rest_system`, `settings_system`, `store_system`.
    - ✅ via `Code.backend` switch (v2.1.5): `tile_map`, `animated_player`.
    - ✅ backend source itself: `ui_components` (v2.0.5).
    - n/a (no pygame): `game_data`, `enhanced_enemy_manager`, `debug`, `version`.
  - **Remaining to fully retire pygame**:
    1. **On-device VISUAL verification** — `pip install arcade && MEGITECH_BACKEND=arcade python arcade_app.py`, then walk every screen (menu, character select/create, overworld tiles + player sprite, store, inventory, character sheet, combat, rest, settings, crafting, level select) and confirm it paints through `gfx`. Import-level is green; pixel-level needs eyes.
    2. **Extend the shim** for any primitive that renders wrong during (1) — most likely candidates: text metrics/alignment, alpha overlays, tile-sheet cell offsets.
    3. ✅ **Fixed pre-existing bug** (v2.1.9, 07/09/2026): `Code/combat_integration.py` bare `from game_data import CharacterManager` → `from Code.game_data import CharacterManager`. Full `Code/*.py` import sweep now 20/20 clean under both backends (was 19/20).
    4. **Flip the default** — once (1) passes, make `MEGITECH_BACKEND=arcade` the default (or drop the env gate) and retire the legacy pygame `run()` loop in `main.py`.

## Done

- **Add a CI workflow** (P2 #9) — done 07/09/2026 on `feature/arcade-migrate-assets`, released as v2.1.13. Added the repo's first GitHub Actions workflow (`.github/workflows/ci.yml`) that runs on every push and PR against `main` and `develop` (plus manual `workflow_dispatch`). Steps: checkout → set up Python 3.11 (pip-cached) → install `requirements.txt` + `requirements-dev.txt` → `python -m py_compile main.py arcade_app.py Code/*.py` → `ruff check .` → headless `python -m unittest discover -s tests -v`. `SDL_VIDEODRIVER`/`SDL_AUDIODRIVER` are forced to `dummy` at job scope so pygame imports without a display/audio device; a `concurrency` group cancels superseded runs. The ruff step is intentionally `continue-on-error` for now — the 43 pre-existing findings are deferred in the CHANGELOG ToDo — and flips to blocking once that cleanup lands. Locally verified before commit: workflow YAML parses, `py_compile` clean, ruff reports the expected 43 findings, and the suite is 42/42 green under the dummy SDL drivers. See CHANGELOG.md.
- **Fix spawn items so they are always accessible** (P1 #3) — done 07/09/2026 on `hotfix/spawn-accessible`, released as v2.1.4. World items (trees, rocks, metal veins, streams, brushes) were placed at random coordinates constrained only by min-distance to other spawned entities, with x/y ranges hardcoded to the old 800×600 window (world is really 768×576) and no clearance around the player start or key interactables — so a blocking rock/metal/tree could land on the player's spawn point (trapping them) or bury the rest area / shop / boss-dungeon centre. Added `get_spawn_bounds(margin)` (derives spawn ranges from `tile_map.get_world_pixel_size()`, clamped so they never invert) and `get_reserved_positions()` (player start, rest area, shop, dungeon centre); both spawn loops now reject candidates outside the derived bounds, on a non-walkable tile (`is_position_walkable`), or within `RESERVED_CLEARANCE = 70`px of any reserved point. New `tests/test_spawn_accessibility.py` (6 tests) drives the real placement loops across 60 seeds asserting the invariants; suite now 42/42 green. See CHANGELOG.md.
- **Replace 0-byte placeholder SFX** (P4 #17) — done 07/09/2026 on `feature/placeholder-sfx`, released as v2.1.3. Generated six real WAV effects to replace the empty 0-byte files that failed to load (`player_hurt`, `run_away`, `victory`, `menu_select`, `menu_move`, `door_open`). Synthesized procedurally with NumPy (44.1 kHz, 16-bit stereo, short envelopes): `menu_move` a 60 ms soft blip, `menu_select` a two-note up-confirm, `player_hurt` a descending tonal+noise grunt, `run_away` a rising whoosh sweep, `victory` a four-note C-E-G-C major arpeggio fanfare, and `door_open` a low modulated creak. All six load through `pygame.mixer.Sound` headlessly (dummy SDL drivers) with correct non-zero durations. The generator script logic is captured in CHANGELOG. See CHANGELOG.md.
- **Add a linter config** (P2 #10) — done 07/08/2026 on `feature/linter-config`, released as v2.1.2. Added the project's first `pyproject.toml` with a `[tool.ruff]` section: `py311`, `line-length = 120`, content/vendored dirs excluded, and a high-signal `select = ["F", "E9", "B"]` rule set (dead code, unused imports, syntax errors, bugbear) with style rules left off so it's not a reformat diff. Key finding: the game's deliberate `from Code.ui_components import *` backend switch (v2.0.5) makes `F403`/`F405` fire on nearly every pygame call — **484 of 527 raw findings**; ignoring them leaves **43 real findings** (13 unused imports, 12 unused vars, 13 unused loop vars, 4 placeholder-less f-strings, 1 redefinition), now logged in CHANGELOG ToDo for a dedicated cleanup pass (17 are `--fix`-safe). Added `requirements-dev.txt` for the dev-only `ruff` dep. Tests still 36/36 green; `py_compile` clean. See CHANGELOG.md.
- **Add a minimal test suite** (P2 #8) — done 07/08/2026 on `feature/test-suite`, released as v2.1.1. Added a `tests/` package (standard-library `unittest`, no third-party runner) that forces SDL dummy drivers so the Pygame-coupled modules import headlessly. Three modules — `test_combat_system.py` (damage/spell/hit-chance math + spell gating, randomness pinned via `mock.patch`), `test_level_system.py` (unlock/selection/completion cascades + content-count helpers, progression written to a temp CWD), and `test_crafting_system.py` (recipe/material catalog, level-gated availability, rarity colours, random drop table). **36 tests, all green**; `py_compile` clean. Run with `python -m unittest discover -s tests -v`. See CHANGELOG.md. (Surfaced a leftover unconditional DEBUG print at `Code/combat_system.py:266` — noted for a future run.)
- **Character spawns into last level played** (P1 #4) — done 07/08/2026 on `feature/spawn-last-level`, released as v2.1.0. `LevelManager` already persists `current_world`/`current_level` per character (`SaveProgression/progression_<name>.json`) and restores it on `set_character()`, but the character-select and character-create paths jumped straight to `GAME_BOARD` without rebuilding the world, so players always spawned into the default 1-1 world built at startup. Added `enter_game_board_for_current_level()` (rebuilds the world for the persisted level, recenters the player, snaps the camera) and called it from both the load-character and create-character paths. Explicit level selection is unchanged (still routes through `change_level`). See CHANGELOG.md.
- **Save-file tracking policy** (P1 #5) — done 07/08/2026 on `hotfix/save-file-policy`, released as v2.0.6. Decided runtime saves are live per-player state, not versioned source: gitignored `Characters/*.json` + `SaveProgression/*.json`, untracked the five previously committed saves via `git rm --cached`, and added `.gitkeep` to both dirs so a fresh clone keeps the folders. Loader already discovers characters by scanning the dir, so nothing depends on a committed save. See CHANGELOG.md.
- **Resource regeneration too fast** (P4 #16) — done 07/07/2026 on `hotfix/resource-regen-rate`, released as v2.0.4. Respawn timers were minutes×60 (seconds) but the loop runs at 15 FPS, so nodes regrew 15× too fast (~40–80s vs. intended 10–20 min). Corrected `max_respawn_time` in `Code/ui_components.py` (Tree/Stream/Rock/Metal/Brush) and `Code/crafting_system.py` (ResourceNode) to true 15-FPS frame counts. See CHANGELOG.md.
- **Remove/gate debug output** (P1 #6) — done 07/07/2026 on `feature/gate-debug-output`, released as v1.7.8. Added `Code/debug.py` with a DEBUG flag (off by default, opt-in via `MEGITECH_DEBUG` env var) and a `debug_print()` helper; replaced all 19 unconditional `print(f"DEBUG: ...")` calls in `Code/combat_system.py` (14) and `Code/settings_system.py` (5). See CHANGELOG.md.
- **Main game sound is broken** (P0 #2) — done 07/07/2026 on `hotfix/audio-path-fix`, released as v1.7.7. Fixed `../Sounds` vs `Sounds` path mismatch, made music resolve against the absolute Sounds dir regardless of working directory, and defined the missing `start_world_music()` hook. See CHANGELOG.md.
- **Dying doesn't take credits** (P0 #1) — done 07/07/2026 on `hotfix/death-credit-loss`, released as v1.7.6. Fixed legacy combat death path, boss-dungeon FIGHT-state fallthrough, keypress-path reward/penalty skip, and duplicated victory rewards. See CHANGELOG.md.
- **Add a `.gitignore`** + **Untrack committed `.pyc` files** (P1 #3 & #4) — done 07/07/2026 on `feature/repo-hygiene`, released as v1.7.5. See CHANGELOG.md.

_(move completed items to CHANGELOG.md)
