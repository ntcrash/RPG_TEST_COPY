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
3. [Hotfix] **Fix Spawn items so they are always accessible**
4. [Feature] **Character should spawn into last level played** unless selected another level.
7. [Hotfix] **Add `requirements.txt`** — no dependency manifest exists; README states pygame 2.6.1 on Python 3.11 as the only real dependency, but pinning it removes an onboarding/automation guesswork step.

## P2 — Testing & CI (enables safe automated changes)

8. [Hotfix] **Add a minimal test suite** — no `tests/` directory or test framework currently exists. Start with unit tests for pure-logic modules least coupled to Pygame's display: `Code/crafting_system.py` (recipe/material logic), `Code/level_system.py` (progression/unlock logic), `Code/combat_system.py` damage/hit-chance calculations (`calculate_spell_damage`, hit chance functions flagged by the DEBUG prints above — good coverage target).
9. [Hotfix] **Add a CI workflow** (GitHub Actions) — run the new test suite plus a `python -m py_compile` / lint pass on push and PR against `develop` and `main`, matching the gitflow branches already in use.
10. [Hotfix] **Add a linter config** (`ruff` or `flake8`) — codebase is large (main.py alone is ~1,950 lines) with no enforced style; a lint pass would catch dead code and unused imports cheaply before larger refactors.

## P3 — Documentation debt

11. [Hotfix] **Sync `README.md` architecture section with actual code** — README's "Recent Changes" section is frozen at a 2025-09-08 Replit import note; the file-structure list references `game_states.py` as entry point, but that file was renamed to `main.py` back in v1.6 per CHANGELOG. Update README to reflect current `main.py` + `Code/` module layout.
12. [Hotfix] **Reconcile version history** — CHANGELOG.md's early history (v20–v29, "GUI Client for Multiplayer") describes a multiplayer/server architecture (`NetworkManager_Class.py`, `Server_v1`–`v3`) that no longer appears in the current single-player codebase. Either archive that history clearly as "legacy multiplayer branch, discontinued" or confirm if multiplayer is still a live goal — affects whether future roadmap items should plan around a server component.

## P4 — Feature ideas (lower priority, larger scope)

14. [Hotfix] **Automated save-file migration check** — with a versioned save schema (`Characters/*.json`), add a lightweight migration/validation step so old saves don't silently break on load after combat/stat formula changes (e.g., the v1.7.3 spell-damage level-scaling change).
15. [Feature] **Difficulty/balance regression checks** — CHANGELOG shows multiple past hotfixes for difficulty multiplier and stat scaling bugs (v1.4.1, v1.7.3). Once #8's test suite exists, add regression tests pinning expected damage/AC output for a few reference character/enemy stat combos to catch future balance regressions automatically.
17. [Hotfix] **Replace 0-byte placeholder SFX** — `Sounds/player_hurt.wav`, `run_away.wav`, `victory.wav`, `menu_select.wav`, `menu_move.wav`, and `door_open.wav` are empty files and fail to load (code degrades gracefully, but these effects are silent). Source or generate real audio. (Surfaced while fixing P0 #2.)
---

## P5 - Visual Enhancements
25. [Feature] **Animated Trees**: Swaying animation and color changes based on harvestable status
26. [Feature] **Resource Nodes**: Visual feedback showing when objects can be harvested vs depleted
27. [Feature] **Mystical Dungeons**: Animated portal entrances with glowing magical effects and floating particles
28. [Feature] **"BOSS DUNGEON" Text**: Golden glow effects and mystical styling
29. [Feature] **Special Victory Messages**: Boss defeats show trophy emojis and enhanced formatting
30. [Feature] **World Aesthetics**: Cleaner grass-based terrain without flower clutter
31. [Feature] **Structured Paths**: Clear walking routes toward important areas

## P6 - Multi-player Enhancements

40. [Release] **Change version number to v3.0.1 - Add multi player** add multi player with server / client setup, using the existing client and added the server components, single player mode should not change
41. [Feature] **Add account creation** Add account, and characters under the account for multi player, single player should not change


## In Progress

- **pygame → Arcade GUI migration** (MAJOR, v2.x) — started 07/07/2026 on `feature/v2-arcade`, foundation released as **v2.0.1**. Added `Code/version.py` (central `__version__`), `Code/gfx.py` (pygame→Arcade compat shim with automatic y-axis flip), and `arcade_app.py` (new `arcade.Window` entry point driving the existing state machine at 15 Hz via translated key/text events). Legacy `python main.py` (pygame) stays runnable throughout.
  - **v2.0.5 (07/07/2026)** — backend now switches end-to-end. **Key finding**: per-module `import pygame` swaps are a no-op because `Code/ui_components.py` star-exports its `pygame` binding to every module + `main.py`, so the star import always wins. Fixed the real mechanism instead: (1) `ui_components` selects the backend from `MEGITECH_BACKEND` (unset→pygame, `arcade`→`Code.gfx`) and star-exports it everywhere; (2) `arcade_app` sets the env var so its window renders through the shim; (3) `gfx` became a **hybrid** — non-render attrs (`mixer`/`time`/`display`/`event`/`key`/`sprite`/`locals`/…) delegate to real pygame via module `__getattr__`, and `Surface` now records+replays **off-screen** draws (HUD overlay + tile-sheet `area` blits), with y-flip and sub-rect clipping. Headless stub tests (5) pass; `python main.py` unchanged.
  - **Remaining**: with the switch in place, the shim's render coverage is now the work. Verify on-device (`pip install arcade && python arcade_app.py`); confirm each render module (`ui_components`, `tile_map`, `enhanced_combat_system`, `inventory_system`, `store_system`, `rest_system`, `settings_system`, `crafting_system`, `character_creation`, `animated_player`, `level_system`, `combat_system`) paints correctly through `gfx` and extend the shim where a primitive is missing; note `tile_map` + `animated_player` don't star-import `ui_components`, so they still bind real pygame and need their own line-1 swap once the shim covers their `sprite`/`locals`/sheet use. Then retire pygame.

## Done

- **Save-file tracking policy** (P1 #5) — done 07/08/2026 on `hotfix/save-file-policy`, released as v2.0.6. Decided runtime saves are live per-player state, not versioned source: gitignored `Characters/*.json` + `SaveProgression/*.json`, untracked the five previously committed saves via `git rm --cached`, and added `.gitkeep` to both dirs so a fresh clone keeps the folders. Loader already discovers characters by scanning the dir, so nothing depends on a committed save. See CHANGELOG.md.
- **Resource regeneration too fast** (P4 #16) — done 07/07/2026 on `hotfix/resource-regen-rate`, released as v2.0.4. Respawn timers were minutes×60 (seconds) but the loop runs at 15 FPS, so nodes regrew 15× too fast (~40–80s vs. intended 10–20 min). Corrected `max_respawn_time` in `Code/ui_components.py` (Tree/Stream/Rock/Metal/Brush) and `Code/crafting_system.py` (ResourceNode) to true 15-FPS frame counts. See CHANGELOG.md.
- **Remove/gate debug output** (P1 #6) — done 07/07/2026 on `feature/gate-debug-output`, released as v1.7.8. Added `Code/debug.py` with a DEBUG flag (off by default, opt-in via `MEGITECH_DEBUG` env var) and a `debug_print()` helper; replaced all 19 unconditional `print(f"DEBUG: ...")` calls in `Code/combat_system.py` (14) and `Code/settings_system.py` (5). See CHANGELOG.md.
- **Main game sound is broken** (P0 #2) — done 07/07/2026 on `hotfix/audio-path-fix`, released as v1.7.7. Fixed `../Sounds` vs `Sounds` path mismatch, made music resolve against the absolute Sounds dir regardless of working directory, and defined the missing `start_world_music()` hook. See CHANGELOG.md.
- **Dying doesn't take credits** (P0 #1) — done 07/07/2026 on `hotfix/death-credit-loss`, released as v1.7.6. Fixed legacy combat death path, boss-dungeon FIGHT-state fallthrough, keypress-path reward/penalty skip, and duplicated victory rewards. See CHANGELOG.md.
- **Add a `.gitignore`** + **Untrack committed `.pyc` files** (P1 #3 & #4) — done 07/07/2026 on `feature/repo-hygiene`, released as v1.7.5. See CHANGELOG.md.

_(move completed items to CHANGELOG.md)
