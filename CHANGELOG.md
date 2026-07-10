# Changelog
All notable changes to this project will be documented in this file.

## - ToDo
- Fix the 43 Ruff findings surfaced by the new linter (13 unused imports, 12 unused variables, 13 unused loop vars, 4 placeholder-less f-strings, 1 redefinition) — deferred from v2.1.2 to keep that change config-only

## 07/09/2026 - v2.1.7
### 🕹️ Arcade migration: fix character movement (held-key state) (roadmap P1 #1)
**Game loaded and rendered under Arcade, but the character wouldn't move.** Continuous movement (`AnimatedPlayer.update_position`, and `main.py:1088`) polls `pygame.key.get_pressed()`, but under the Arcade backend the real pygame window receives no input — Arcade owns the window — so `get_pressed()` was always all-False. (Menus worked because they use discrete KEYDOWN events, which were already translated.)
- **File: `Code/gfx.py`** — added a real `key` module to the shim: a module-level held-key set plus `set_key(keyint, down)` and a pygame-shaped `key.get_pressed()` that indexes it (`_PressedKeys`, `_KeyModule`). Any other `pygame.key.*` attribute (`get_mods`, `name`, `set_repeat`, …) still delegates to real pygame. Because the shim now defines `key`, it takes precedence over the hybrid `__getattr__` passthrough.
- **File: `arcade_app.py`** — `on_key_press` now calls `gfx.set_key(key, True)` (in addition to firing the discrete KEYDOWN for menu nav), and a new `on_key_release` calls `gfx.set_key(key, False)`. So the shim's held-key state mirrors what Arcade sees, and polled movement works.
- **Verification**: shim key-state smoke test passes (press→held→release); import harness still 17/18 under both backends. Arrow-key movement should now work on-device — re-run and report any remaining `draw() error:` lines for the next shim-coverage batch.

## 07/09/2026 - v2.1.6
### 🐞 Arcade migration: complete the shim's Rect API + harden shutdown frame (roadmap P1 #1)
**On-device run surfaced per-frame `draw() error: 'Rect' object has no attribute 'inflate'` — the shim's `Rect` was missing methods real `pygame.Rect` has, so any module using them silently failed to paint. Also a benign `No GL context` traceback on the final frame after the window closes.**
- **File: `Code/gfx.py`** — completed `Rect` to match the pygame.Rect surface the code uses: methods `inflate`/`inflate_ip` (grow/shrink keeping center), `copy`, `move_ip`, `colliderect`, `clamp`, `union`, `contains`, and `collidepoint((x,y))` tuple form; plus `w`/`h`/`size` aliases and the `topright`/`bottomleft`/`bottomright`/`midtop`/`midbottom`/`midleft`/`midright` anchors (get + set). Verified in isolation: `inflate` preserves center, `copy` is independent, `colliderect` hit/miss correct.
- **File: `arcade_app.py`** — `on_draw` now guards `self.clear()` and early-returns on a new `_closing` flag (set in `_shutdown`). After the window closes, pyglet can fire one more scheduled frame with no GL context; this skips that dying frame instead of dumping a `pyglet.gl.lib.GLException` traceback (process already exits 0).
- **Verification**: `Rect` smoke test passes; import harness still 17/18 under both backends. Remaining errors from the on-device run should now be down to genuinely-missing render primitives (report the next batch of `draw() error:` lines and I'll extend the shim).

## 07/09/2026 - v2.1.5
### 🎮 Arcade migration: switch the two non-star-import modules + shim sprite-sheet support (roadmap P1 #1)
**The runtime backend switch (v2.0.5) reaches every module that does `from Code.ui_components import *`, but `Code/tile_map.py` and `Code/animated_player.py` don't — they bound real pygame directly, so they never rendered through the Arcade shim. Migrated both, and taught the shim the sprite-sheet operations they need.**
- **File: `Code/backend.py`** (new) — DRY single-source-of-truth backend switch (`from Code.backend import pygame`) using the same `MEGITECH_BACKEND` logic as `ui_components` (unset → real pygame; `arcade` → `Code.gfx`). Lets a module that can't reach the `ui_components` star-export flip backends with a one-line import.
- **File: `Code/tile_map.py`** — `import pygame` → `from Code.backend import pygame`. Tile-sheet cell blits (`screen.blit(sheet, pos, area)`) now route through the shim.
- **File: `Code/animated_player.py`** — `import pygame` → `from Code.backend import pygame`. Sprite-frame extraction now routes through the shim. (`from pygame.locals import *` and `pygame.sprite.Sprite` keep delegating to real pygame — backend-agnostic.)
- **File: `Code/gfx.py`** — added the sprite-sheet primitives these modules require: `Surface.subsurface(rect)` (frame extraction) and texture-backed `blit(source, dest, area)` now **crop** the sheet to the requested cell instead of drawing the whole texture. New helpers `_crop_texture` (uses `arcade.Texture.crop`, PIL-crop fallback) and `_rect_xywh`.
- **Verification**: headless import harness on-device under BOTH backends (`SDL_VIDEODRIVER=dummy`, and again with `MEGITECH_BACKEND=arcade`) — 17/18 modules import clean in each mode. The one failure, `Code/combat_integration.py`'s bare `import game_data`, is a pre-existing relative-import bug (identical in both backends, unrelated to this change) and is logged in ROADMAP P1 #1 remaining work. Pixel-level rendering still needs an on-device visual pass (`MEGITECH_BACKEND=arcade python arcade_app.py`).

## 07/09/2026 - v2.1.4
### 🗺️ Spawned items are now always accessible (roadmap P1 #3)
**World items (trees, rocks, metal veins, streams, brushes) were placed at random coordinates constrained ONLY by min-distance to other spawned entities. They didn't reserve space around the player's spawn point or the key interactables, and the x/y ranges were hardcoded to the old 800×600 window instead of the actual 768×576 world — so a blocking rock/metal/tree could land on the player's start point (trapping them) or on top of the rest area, shop, or the world-centre where the boss dungeon appears (burying an interactable), and none of the ranges would adapt if the map size changed.**
- **World-derived spawn bounds** — new `EnhancedGameManager.get_spawn_bounds(margin)` computes the min/max spawn x,y from `tile_map.get_world_pixel_size()` with an inset margin, replacing the hardcoded `random.randint(40, 760)` / `(60, 740)` / `(40, 560)` ranges in `create_trees` and `create_map_objects`. Every item now lands inside reachable world bounds and the logic scales automatically if the tile dimensions change. Bounds are clamped so they never invert on a tiny world.
- **Reserved interactable zones** — new `get_reserved_positions()` returns the player start `(480, 480)`, the rest-area corner `(w-60, h-60)`, the shop `(w-80, 20)`, and the boss-dungeon centre `(w/2, h/2)`. Both spawn loops now reject any candidate within `RESERVED_CLEARANCE = 70`px of these points (larger than the 50px interaction radius so an interactable is never buried, and larger than the player sprite so the spawn point is never blocked). This replaces the old ad-hoc "avoid player start by 80px" check that covered trees only.
- **Walkable-tile guard** — candidates are now validated against `tile_map.is_position_walkable()` before placement, future-proofing the pipeline for non-uniform maps (all tiles are walkable today, so behaviour is unchanged now).
- **New regression test** — `tests/test_spawn_accessibility.py` (6 tests): pins `get_spawn_bounds` (default world, scaling, tiny-world clamp) and `get_reserved_positions`, then drives the real `create_map_objects` and `create_trees` loops across 60 RNG seeds each, asserting every placed item stays inside bounds and ≥70px from every reserved point. Uses a bare `__new__` instance + lightweight stubs so it runs headlessly. Suite now **42 tests, all green**; `py_compile` clean; no new Ruff findings. See ROADMAP.md P1 #3 (moved to Done).

## 07/09/2026 - v2.1.3
### 🔊 Replaced 0-byte placeholder SFX with real audio (roadmap P4 #17)
**Six sound effects shipped as empty 0-byte `.wav` files (`player_hurt`, `run_away`, `victory`, `menu_select`, `menu_move`, `door_open`), so `pygame.mixer.Sound` failed to load them — the game degraded gracefully but those cues were silent (surfaced while fixing the P0 #2 audio-path bug).**
- **Generated real audio procedurally** with NumPy (no external asset dependency, reproducible via a fixed RNG seed). All files are 44.1 kHz, 16-bit stereo with short attack/release envelopes so they don't click:
  - `menu_move.wav` — 60 ms soft 880 Hz blip (navigation tick).
  - `menu_select.wav` — 130 ms two-note up-confirm (660 → 990 Hz).
  - `player_hurt.wav` — 250 ms descending 300→120 Hz tone mixed with noise (grunt/impact).
  - `run_away.wav` — 300 ms rising 200→1400 Hz whoosh sweep with a fading noise layer (flee).
  - `victory.wav` — 800 ms four-note C-E-G-C (523/659/784/1047 Hz) major-arpeggio fanfare with a second harmonic.
  - `door_open.wav` — 400 ms low 90→140 Hz creak with an 18 Hz flutter amplitude-modulation and light noise.
- **Verification**: each file loads through `pygame.mixer.Sound` under headless dummy SDL drivers (`SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`) and reports its expected non-zero length. No code changes were needed — the loader in `Code/enhanced_combat_system.py` already referenced these filenames; only the assets were missing. See ROADMAP.md P4 #17 (moved to Done).

## 07/08/2026 - v2.1.2
### 🧹 Added a Ruff linter config (roadmap P2 #10)
**The codebase is large (`main.py` alone is ~1,950 lines) with no enforced style or dead-code check, so unused imports and stray dead code accumulated silently before every refactor.**
- **New `pyproject.toml`** with a `[tool.ruff]` section — the project's first tooling config. Targets `py311`, `line-length = 120`, and excludes vendored/generated/content dirs (`venv`, `__pycache__`, `Books`, `assets`, `Images`, `Sounds`, `Characters`, `Enemies`, `SaveProgression`).
- **High-signal, low-noise rule set**: `select = ["F", "E9", "B"]` (pyflakes dead-code/unused-import/undefined-name checks, syntax errors, and flake8-bugbear likely-bugs). Style rules (E1/E2/E3/E7, W) are deliberately left OFF so this is not a reformat diff.
- **Silenced the star-import noise**: the whole game distributes its `pygame` binding via `from Code.ui_components import *` (the documented v2.0.5 backend switch), which makes `F403`/`F405` fire on essentially every pygame call — **484 of 527 raw findings were that pattern**. Ignoring `F403`/`F405` (plus `B008`/`B905`) drops the report to **43 real findings**: 13 unused imports, 12 unused variables, 13 unused loop control vars, 4 f-strings without placeholders, 1 redefinition. Per-file ignores relax `F401`/`F811` in `tests/` and `F401` in `__init__.py` re-export shims.
- **New `requirements-dev.txt`** — dev-only tools (`ruff>=0.15`) kept separate from the runtime `requirements.txt` so playing the game needs no linter install.
- **Scope note**: this change adds the config only; the 43 findings it surfaces are logged under ToDo above for a dedicated cleanup pass (17 are Ruff `--fix`-safe). Run with `ruff check .`. Tests still green (36/36); `py_compile` clean. See ROADMAP.md P2 #10 (moved to Done).

## 07/08/2026 - v2.1.1
### 🧪 Added a minimal unit-test suite (roadmap P2 #8)
**The project had no `tests/` directory or test framework, so there was no automated safety net for the pure-logic modules — every balance/formula change had to be verified by hand in-game.**
- **New `tests/` package** using only the standard-library `unittest` (no third-party runner needed). `tests/__init__.py` forces SDL's dummy video/audio drivers (`SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`) so the Pygame-coupled game modules import and run in a headless environment (CI, containers) with no display or sound card.
- **`tests/test_combat_system.py`** — pins `CombatManager.calculate_damage`, `calculate_spell_damage`, and `calculate_hit_chance` (strength/int/wisdom/level bonuses, critical multipliers, the 5%/75% hit-chance boundaries and the 5% floor) plus `SpellManager` level-gated spell availability. Randomness is controlled with `mock.patch` on the module's `random.randint` so every expected value is exact.
- **`tests/test_level_system.py`** — covers `LevelManager` unlock gating, level selection, and the completion cascade (finishing a boss level unlocks the next world), plus the deterministic `WorldLevelGenerator` enemy/treasure count helpers. Progression JSON is written inside a temp CWD so the repo is never touched.
- **`tests/test_crafting_system.py`** — covers recipe/material catalog sizes, level-gated recipe availability, rarity-colour lookup, and the random material drop table (with `random.randint` patched to hit each rarity branch).
- **Run**: `python -m unittest discover -s tests -v`. Current status: **36 tests, all green** (`Ran 36 tests ... OK`). `py_compile` clean. See `tests/README.md` and ROADMAP.md P2 #8 (moved to Done).
- **Note for next run**: while writing the combat tests I saw one unconditional `print("DEBUG: Spell base damage ...")` still live at `Code/combat_system.py:266` — it slipped past the v1.7.8 debug-gating pass. Small follow-up, not addressed here to keep this change scoped to the test suite.

## 07/08/2026 - v2.1.0
### ✨ Characters now spawn into their last-played level (roadmap P1 #4)
**Loading (or creating) a character sent the player straight to the game board without rebuilding the world, so every character spawned into the default World 1-1 regardless of how far they'd progressed.**
- **Root cause**: `LevelManager` already persists `current_world`/`current_level` per character in `SaveProgression/progression_<name>.json` and restores it via `set_character()` → `load_progression()`. But the `CHARACTER_SELECT` and `CREATE_CHARACTER` key-handlers set `current_state = GameState.GAME_BOARD` *without* calling `setup_world_for_current_level()`. The world had only been built once, at startup, for the default 1-1 level — so the restored progression pointer was ignored and the player always landed in 1-1.
- **File: `main.py`** — added `enter_game_board_for_current_level()`: recenters the player (480, 480), calls `setup_world_for_current_level()` to regenerate the world/enemies/theme for the persisted level, snaps the camera to the player, then enters `GAME_BOARD`. Mirrors the world-setup half of `change_level()`.
- **File: `main.py`** — both the load-character and create-character paths now call `enter_game_board_for_current_level()` after `set_character()` instead of setting the state inline.
- **Unchanged**: explicit level selection still routes through `change_level()` (the "unless selected another level" case), and a brand-new character correctly starts in 1-1 (its fresh progression defaults there).
- **Verification**: `py_compile` clean; a headless progression round-trip test confirms a character advanced to World 2-3 has that level restored on re-select, which `enter_game_board_for_current_level()` then builds. See ROADMAP.md P1 #4 (moved to Done).

## 07/08/2026 - v2.0.6
### 🧹 Save-file tracking policy — runtime saves are no longer versioned (roadmap P1 #5)
**`Characters/*.json` and `SaveProgression/*.json` were tracked in git, so every local playtest produced a noisy uncommitted diff (character level/credits/inventory churn) that had nothing to do with code changes and risked clobbering another machine's saves on merge.**
- **Decision**: these are *live per-player save state*, not source or fixtures, so they are now **gitignored** rather than versioned. A fresh clone starts with no saved characters; the in-game character-creation flow writes them at runtime, and the loader already discovers characters by scanning `Characters/` for `*.json` (`Code/game_data.py`), so nothing depends on a committed save existing.
- **File: `.gitignore`** — added `Characters/*.json` and `SaveProgression/*.json` (with `!*/.gitkeep` negations), plus ignores for the stray `_t2` scratch file and `.git/*.stalebak` lock backups.
- **Untracked** the five previously committed live saves (`Characters/nora.json`, `Characters/vozy.json`, `SaveProgression/progression_Nora.json`, `progression_Vozy.json`, `progression_default.json`) via `git rm --cached` — the files stay on disk for the local player, they just leave version control.
- **Added** `Characters/.gitkeep` and `SaveProgression/.gitkeep` so both directories still exist in a fresh clone.
- Effect: playtesting no longer dirties the working tree with save churn, and pulling on another machine can't overwrite local progress. See ROADMAP.md P1 #5 (moved to Done).

## 07/07/2026 - v2.0.5
### 🚀 pygame → Arcade migration — central backend switch + hybrid shim (roadmap P1 #1)
**The Arcade backend is now wired end-to-end: rendering can route through `Code.gfx` (Arcade) while audio/timing/input keep using real pygame — controlled by a single switch. The legacy `python main.py` path is byte-for-byte unchanged.**
- **Why this was the blocker**: every gameplay module gets its `pygame` name from `Code/ui_components.py` via `from Code.ui_components import *` (and `main.py` has *no* pygame import of its own). Because that star-export re-binds `pygame` in each importer, flipping an individual module's own `import pygame` line had no effect — the star import always won. So the backend can only be switched from one place: ui_components.
- **File: `Code/ui_components.py`** — added the single backend switch. Reads `MEGITECH_BACKEND`: unset → `import pygame` (legacy, unchanged); `=arcade` → `from Code import gfx as pygame`. This selection star-exports to every gameplay module **and** `main.py` at once.
- **File: `arcade_app.py`** — sets `MEGITECH_BACKEND=arcade` before importing the game, so its `arcade.Window` now actually renders through the shim; marks its window surface `is_screen=True` so screen draws paint immediately (not recorded).
- **File: `Code/gfx.py`** — made the shim a **hybrid**: a module-level `__getattr__` (PEP 562) delegates any non-render attribute (`mixer`, `time`, `display`, `event`, `key`, `mouse`, `sprite`, `locals`, `error`, `Color`, …) to real pygame, while `draw`/`font`/`Rect`/`Surface`/`image`/`transform`/key-constants stay Arcade-backed. `init()`/`quit()` now delegate to real pygame so audio/font subsystems still initialize.
- **File: `Code/gfx.py`** — `Surface` now supports **off-screen draw targets**: a plain sized surface records draw ops (`fill`/`rect`/`circle`/`ellipse`/`line`/`lines`/`polygon`/`blit`) and **replays** them — translated, y-flipped, and optionally sub-rect clipped — when blitted onto the window. This unlocks the two patterns every render module uses: the semi-transparent HUD overlay (`Surface((w,h), SRCALPHA)` → draw onto it → blit to screen) and tile-sheet cell blitting (`screen.blit(sheet, pos, area_rect)`). Accepts pygame's positional `flags` arg (e.g. `SRCALPHA`).
- **Verification**: added a headless stub-backed test suite (5 tests, all passing): default path binds real pygame; arcade path binds gfx and star-exports it; hybrid delegation returns real pygame submodules; overlay replay produces correct y-flipped Arcade coords; tile-sheet `area` blit selects only the addressed cell. Full-tree `py_compile` clean.
- **⚠️ On-device smoke test still pending**: sandbox has no display/Arcade install; `pip install arcade && python arcade_app.py` on the Mac remains the final visual check.

## 07/07/2026 - v2.0.4
### 🐞 Resource regeneration was ~15× too fast (roadmap P4 #16)
**Harvestable resource nodes respawned every 40–80 seconds instead of the 10–20 minutes their own comments claimed.**
- **Root cause**: respawn timers were computed as `minutes * 60` (i.e. *seconds*) but the game loop runs at 15 FPS (`clock.tick(15)`), so each value was consumed as *frames* and ran 15× too fast.
- **File: `Code/ui_components.py`** — corrected `max_respawn_time` to true 15-FPS frame counts: Tree & Stream 600→9000 (10 min), Rock 900→13500 (15 min), Metal 1200→18000 (20 min), Brush 750→11250 (12.5 min).
- **File: `Code/crafting_system.py`** — `ResourceNode` respawn 3000→4500 (default arg and `max_respawn_time`), now a true 5 minutes at 15 FPS.
- Effect: harvested trees, rocks, metal, streams, brush, and crafting material nodes now take their intended real-world minutes to regrow, making resources a meaningful constraint again.

## 07/07/2026 - v2.0.3
### 🐞 Arcade foundation hotfix — pygame/Arcade OpenGL context conflict
**`python arcade_app.py` opened the window then crashed with `pyglet.gl.lib.GLException: No GL context; create a Window first`.**
- **Root cause**: `EnhancedGameManager.__init__` still calls `pygame.display.set_mode()` (needed so un-migrated modules can build fonts/convert images). On a real SDL video driver that creates a *second* OpenGL context and makes it current, stealing the context from Arcade/pyglet — so Arcade's `self.clear()` had no GL context.
- **File: `arcade_app.py`** - Set `SDL_VIDEODRIVER=dummy` before pygame's display initializes, giving pygame a valid off-screen video mode (surface/convert/font ops still work) with no real GL context to steal. Audio driver untouched, so sound still works. Also call `self.switch_to()` after building the manager to reclaim pyglet's GL context.
- **Note**: the per-frame `draw() error: argument 1 must be pygame.surface.Surface, not Surface` messages are expected and harmless during migration — they are un-migrated modules calling real pygame draw on the gfx shim surface, caught so the window stays alive. They disappear module-by-module as each is ported to `Code.gfx`.

## 07/07/2026 - v2.0.2
### 🐞 Arcade foundation hotfix — Window.screen attribute collision
**`python arcade_app.py` crashed on launch with `AttributeError: can't set attribute`.**
- **File: `arcade_app.py`** - `arcade.Window` (via pyglet) already defines a read-only `screen` property for the display, so the manager's render-target assignment `self.screen = gfx.Surface(...)` collided with it. Renamed the window's shim surface to `self._surface` and pointed `self.game.screen` at it instead. Window now constructs and launches.

## 07/07/2026 - v2.0.1
### 🚀 MAJOR: pygame → Arcade migration — foundation (Roadmap: GUI backend swap)
**Beginning the move from pygame to Arcade 3.x. This release lays the foundation; the legacy pygame path stays fully runnable while modules migrate one at a time.**
- **File: `Code/version.py`** (new) - Central single-source-of-truth for the game version (`__version__ = "2.0.1"`), window `CAPTION`, and active render `BACKEND`. Replaces scattered hardcoded version strings.
- **File: `Code/gfx.py`** (new) - pygame→Arcade compatibility/rendering shim. Emulates the exact slice of the pygame surface/draw/font API the codebase uses (`Surface.fill/blit/get_rect/set_alpha`, `draw.rect/circle/polygon/line/lines/ellipse`, `font.Font.render`, `image.load`, `transform.scale`, key + event constants) backed by Arcade draw calls. Handles the pygame(top-left, y-down) → Arcade(bottom-left, y-up) coordinate flip automatically so per-module migration is mechanical rather than a rewrite.
- **File: `arcade_app.py`** (new) - New Arcade `Window` entry point. Replaces main.py's hand-rolled `while running:` loop with `on_update`/`on_draw` callbacks, throttled to the original 15 Hz logic tick. Translates Arcade (pyglet) key + text events into the pygame-shaped events the existing `EnhancedGameManager` state machine already consumes — the game's state machine runs unchanged on the Arcade loop. Includes an on-screen backend/state overlay so the window is never blank during migration.
- **File: `main.py`** - Window caption now sourced from `Code.version.CAPTION` (central version) instead of a hardcoded string. No behavior change; `python main.py` still runs the legacy pygame build.
- **File: `requirements.txt`** (new) - Pins both backends during transition: `pygame>=2.5`, `arcade>=3.3`.
- **Migration path**: each render module (`ui_components`, `tile_map`, combat, inventory, store, rest, settings, crafting, character_creation, animated_player) will be ported `import pygame` → `from Code import gfx as pygame`, committed individually per gitflow, until pygame is fully retired.
- **⚠️ Verification pending on-device**: this sandbox has no display and no Arcade install; `pip install arcade` then `python arcade_app.py` on the Mac is required to smoke-test the window/loop/input foundation.

## 07/07/2026 - v1.7.8
### 🐞 Gate Debug Output (Roadmap P1 #6) ✅
**Verbose developer diagnostics no longer spam the player console**
- **File: `Code/debug.py`** (new) - Added a central `DEBUG` flag (off by default, opt-in via the `MEGITECH_DEBUG` env var) and a `debug_print()` helper that only emits when DEBUG is enabled, prefixing output with `DEBUG:` to preserve the prior log format
- **File: `Code/combat_system.py`** - Replaced all 14 unconditional `print(f"DEBUG: ...")` calls (spell/hit/damage/crit/stat diagnostics) with `debug_print(...)`
- **File: `Code/settings_system.py`** - Replaced all 5 unconditional `print(f"DEBUG: ...")` difficulty-application calls with `debug_print(...)`
- **Verified**: `py_compile` passes on all three files; with DEBUG off (default) `debug_print` is silent, and `MEGITECH_DEBUG=1` restores full output

## 07/07/2026 - v1.7.7
### 🔊 Main Game Sound Fix (Roadmap P0 #2) ✅
**Background music now plays correctly regardless of how the game is launched**
- **File: `Code/enhanced_combat_system.py`** - `SoundManager.play_music()` now resolves relative/working-directory-dependent paths against the absolute `sounds_dir`, so music loads no matter the current working directory (SFX already used absolute paths; music did not)
- **File: `Code/enhanced_combat_integration.py`** - Fixed `../Sounds` vs `Sounds` mismatch where `end_combat()` and the GAME_BOARD branch of `play_contextual_music()` checked `os.path.exists("../Sounds/world_music.ogg")` (always false from the repo root) but tried to play `"Sounds/world_music.ogg"` — world music never resumed. Now pass bare filenames and let `play_music()` resolve them
- **File: `Code/enhanced_combat_integration.py`** - Defined the missing `start_world_music()` hook on the game manager; `main.py` called `self.start_world_music()` when fleeing combat, which raised `AttributeError` (undefined method)
- **File: `Code/enhanced_combat_integration.py`** - Stopped calling `create_sound_directories()` during init and repointed it at the absolute Sounds dir; it previously created a stray `../Sounds` folder and wrote empty placeholder `.wav`/`.ogg` files that then failed to load
- **Verified**: headless smoke test (SDL dummy driver) confirms `world_music.ogg` and `battle_music.ogg` load and play from a non-repo working directory; missing menu/shop music degrades gracefully
- **Note**: Six SFX files ship as 0-byte placeholders and still can't load (`player_hurt`, `run_away`, `victory`, `menu_select`, `menu_move`, `door_open`) — tracked as ROADMAP #17

## 07/07/2026 - v1.7.6
### 💀 Death Credit Loss Fix (Roadmap P0 #1) ✅
**Dying now deducts credits on every death path**
- **File: `main.py`** - Legacy combat death (`handle_combat_action`) now deducts 5-15% of credits on death (was: respawn with no penalty)
- **File: `main.py`** - Removed duplicated victory block in `handle_combat_action` that double-awarded XP and credits
- **File: `main.py`** - `enter_boss_dungeon()` only switches to FIGHT state if `start_combat()` succeeds; previously a cooldown-blocked start left the game in FIGHT state with the penalty-free legacy combat path active
- **File: `Code/enhanced_combat_integration.py`** - `handle_combat_input()` now routes victory/defeat through `handle_victory()`/`handle_defeat()` before ending combat (rewards/penalties were skipped on the keypress path)
- **File: `Code/enhanced_combat_integration.py`** - Death now always costs at least 1 credit when the player has any (int truncation made small balances lose 0)

## 07/07/2026 - v1.7.5
### 🧹 Repo Hygiene (Roadmap items #3 & #4) ✅
**Added .gitignore and removed compiled bytecode from version control**
- **File: `.gitignore`** (new) - Ignores `__pycache__/`, `*.pyc`, `venv/`, `.idea/`, `.vscode/`, `.DS_Store`, and build artifacts
- **Untracked**: 13 compiled `.pyc` files under `Code/__pycache__/` and `assets/__pycache__/` plus root `.DS_Store` removed from git tracking (`git rm --cached`) - files remain on disk but no longer generate noisy diffs
- **File: `main.py`** - Main menu subtitle updated to "Start your Adventure NOW!"
- **Note**: Save-file tracking policy (`Characters/*.json`, `SaveProgression/*.json`) intentionally left unchanged pending roadmap item #5 decision

## 09/10/2025 - v1.7.3
### 🎮 UI Square Outline Fixes ✅
**Fixed menu item square outlines to properly fit all text content**
- **File: `Code/ui_components.py`** - Enhanced `draw_enhanced_menu()` function to dynamically calculate rectangle width based on actual text dimensions instead of using fixed width
- **File: `Code/inventory_system.py`** - Updated inventory item selection highlights to size rectangles based on item text content with proper padding
- **File: `Code/enhanced_combat_system.py`** - Fixed spell selection menu highlights to accommodate varying spell name lengths with dynamic width calculation
- **Result**: Menu items, inventory items, and spell selection now show perfectly fitted square outlines that expand to contain all text content

### 🏰 Boss Dungeon System Final Fixes ✅
**Resolved final combat system integration issues**
- **File: `main.py`** - Fixed `enter_boss_dungeon()` method to use correct `combat_integration` attribute instead of non-existent `enhanced_combat_manager`
- **File: `main.py`** - Corrected GameState reference from non-existent `ENHANCED_COMBAT` to proper `FIGHT` state
- **Result**: Boss dungeon spacebar interaction now properly starts boss battles with visual "🐉 BOSS BATTLE BEGINS! 🐉" feedback

### 📊 XP Bar System Fix ✅
**Fixed XP progress bar not updating or showing incorrect progress**
- **Problem**: Two different XP calculation systems were conflicting - character leveling used 150 XP per level, but XP bar used complex exponential system
- **File: `Code/ui_components.py`** - Updated `_get_xp_for_level()` method to match the simple 150 XP per level system used in `Code/game_data.py`
- **Result**: XP bar now correctly shows progress toward next level, updating properly after combat victories and other XP gains

### 🔮 Magic Damage Level Scaling ✅
**Enhanced magic damage to scale with both player stats and level**
- **File: `Code/enhanced_combat_system.py`** - Enhanced `calculate_spell_damage()` method to include player level parameter and level-based damage bonus
- **File: `Code/combat_system.py`** - Updated legacy combat system's spell damage calculation to include level scaling
- **Mechanics**: Magic damage now receives +1 damage bonus every 2 character levels (level bonus = (level-1)/2)
- **Critical Enhancement**: Spell critical hit chance now slightly increases with level (+1% every 5 levels)
- **Result**: All magic spells (damage, healing, drain) become more powerful as the player progresses in level, in addition to existing Intelligence/Wisdom stat bonuses


## 09/09/2025 - v1.7.1
### 🌍 Interactive Map Objects System
- **Tree Harvesting**: Trees now provide crafting materials when interacted with using spacebar
- **Resource Nodes**: Rocks, metal veins, streams, and brushes all provide crafting materials
- **Respawn Timers**: All harvestable objects respawn after being depleted
- **Balanced World Generation**: Reduced spawn counts for better navigation (8 trees vs 20+, fewer resource nodes)
- **World Aesthetics**: Removed flowers entirely, replaced with grass tiles for cleaner appearance
- **Structured Paths**: Created walking paths from center toward shop and rest areas in bottom-right

### 🏰 Boss Dungeon System
- **Boss Dungeons**: Mystical portal dungeons now spawn when all enemies are defeated in a level
- **Level Progression**: Players must defeat a boss to unlock the next level instead of auto-completing
- **Boss Battles**: Challenging boss enemies scaled to current world and difficulty level
- **Enhanced Rewards**: Boss victories provide 500 base credits vs 200 for regular completion

### 📁 Files Modified:

#### **main.py** (Extensive Changes):
- Added `self.dungeons = []` list for boss dungeon tracking
- Added `self.trees = []`, `self.rocks = []`, `self.metals = []`, `self.streams = []`, `self.brushes = []` lists
- Modified `check_level_completion()` to spawn dungeons instead of completing immediately
- Added `complete_level_after_boss()` method for post-boss level completion
- Added `enter_boss_dungeon()` method to trigger boss fights
- Enhanced `check_interactive_objects()` to detect all interactive objects (trees, rocks, metals, streams, brushes, dungeons)
- Completely rewrote `handle_map_object_interaction()` to handle spacebar harvesting and dungeon entry
- Added dungeon drawing in `draw_game_board()` method
- Updated tree respawn timers in `update()` method
- Updated help instructions to include harvesting and dungeon interaction
- Enhanced collision detection for trees and other objects

#### **Code/enhanced_combat_integration.py**:
- Modified `handle_victory()` method to detect boss fights via "Tier" == "boss"
- Added automatic level completion when boss enemies are defeated
- Enhanced victory messages for boss defeats with special formatting
- Boss victories now trigger `complete_level_after_boss()` automatically

#### **Code/ui_components.py**:
- Enhanced `Tree` class with harvesting mechanics, respawn timers, and material generation
- Enhanced `Rock` class with interactive mining and material drops
- Enhanced `Metal` class with vein harvesting and ore generation
- Enhanced `Stream` class with water collection mechanics
- Enhanced `Brush` class with foliage harvesting
- Added comprehensive `Dungeon` class with mystical portal effects, animations, and boss fight integration

#### **Code/tile_map.py**:
- Modified world generation to reduce object spawn counts
- Removed flower generation entirely
- Enhanced path generation toward shop and rest areas
- Improved object placement algorithms for better navigation

### 🎮 Gameplay Changes:
- **Interactive World**: All trees, rocks, metal veins, streams, and brushes can be harvested for crafting materials
- **Spacebar Interaction**: Universal spacebar key for harvesting resources and entering dungeons
- **Resource Management**: Objects respawn after depletion, creating sustainable resource gathering
- **Level Progression**: Level completion now requires defeating a boss in a mystical dungeon
- **Boss Dungeons**: Portal entrances appear in center of map with animated magical effects
- **Enhanced Combat**: Boss enemies provide significantly higher XP and credit rewards
- **Cleaner Navigation**: Reduced object density for easier movement and exploration

### 🎨 Visual Enhancements:
- **Animated Trees**: Swaying animation and color changes based on harvestable status
- **Resource Nodes**: Visual feedback showing when objects can be harvested vs depleted
- **Mystical Dungeons**: Animated portal entrances with glowing magical effects and floating particles
- **"BOSS DUNGEON" Text**: Golden glow effects and mystical styling
- **Special Victory Messages**: Boss defeats show trophy emojis and enhanced formatting
- **World Aesthetics**: Cleaner grass-based terrain without flower clutter
- **Structured Paths**: Clear walking routes toward important areas

### 🔧 Technical Improvements:
- **Modular Object System**: All interactive objects follow consistent patterns for harvesting and respawn
- **Boss Enemy Integration**: Proper boss scaling using existing `create_scaled_boss()` method
- **Enhanced Combat System**: Boss fight detection via enemy "Tier" property
- **Dungeon Architecture**: Portal objects integrate seamlessly with existing interaction system
- **Performance Optimization**: Reduced object counts improve game performance
- **Material Integration**: All harvested materials connect to existing crafting system
- **State Management**: Proper tracking of object states, respawn timers, and dungeon availability

### 🎯 User Experience:
- **Clear Progression**: Clear enemies → Enter dungeon → Defeat boss → Next level
- **Resource Gathering**: Intuitive spacebar interaction for all harvestable objects
- **Visual Feedback**: Console messages and visual effects for all player actions
- **Balanced Difficulty**: Higher stakes and rewards for level completion
- **Engaging Endgame**: More exciting conclusion to each level via boss battles
- **Maintained Features**: All existing systems (crafting, shops, rest areas) continue to work seamlessly

### 📋 Console Output Examples:
```
Harvested: Wood
Harvested: Iron Ore  
Harvested: Leather
Boss dungeon has appeared! Approach and press spacebar to enter.
🏰 BOSS DUNGEON APPEARS! 🏰
🐉 BOSS BATTLE BEGINS! 🐉
🏆 BOSS DEFEATED! Level Complete! Gained 500 XP and 750 credits!
```
- Spacebar interaction to enter boss dungeons
- Boss enemies provide significantly higher XP and credit rewards
- Visual feedback for dungeon appearance and boss victories

### 🎨 Visual Enhancements:
- Animated portal entrances with glowing magical effects
- Floating mystical particles around dungeon portals
- "BOSS DUNGEON" text with golden glow effects
- Special boss victory messages with trophy emojis

### 🔧 Technical Improvements:
- Proper boss enemy scaling using existing `create_scaled_boss()` method
- Integration with enhanced combat system for boss battles
- Dungeon objects follow same interaction pattern as other map objects
- Boss fight detection via enemy "Tier" property

### 🎯 User Experience:
- Clear progression system: Clear enemies → Enter dungeon → Defeat boss → Next level
- Higher stakes and rewards for level completion
- More engaging end-game for each level
- Maintains all existing features (harvesting, crafting, shops, rest areas)

## 09/08/2025 - v1.6
### - Fixed v.1.6.1
- Bug fixes, rest area, xp bar, xp when clearing world, combat increase. progression fixed to single player.
- Cleaned up file system, renamed game_states.py to main.py

## 09/07/2025 - v1.5.x
09/07/2025 - v1.5.2 - CRAFTING UPDATE
- Added
🔨 Complete Crafting System

New crafting_system.py module with comprehensive crafting mechanics
30+ crafting materials across 5 tiers (Common to Legendary)
20+ crafting recipes for consumables, weapons, armor, and accessories
Material drops from enemies and treasures based on level and type
Boss enemies have increased drop rates for rare materials
Treasure chests provide different material loot tables

⚗️ Crafting Features

Recipe categories: Consumables, Weapons, Armor, Accessories
Level requirements for advanced recipes
Material tier system (Common, Uncommon, Rare, Epic, Legendary)
Visual crafting UI with category filtering
Recipe availability based on player level and materials
Real-time inventory checking for craftable items

🎮 Crafting Integration

Press 'F' to open crafting menu
Arrow keys to navigate recipes
Left/Right arrows to change categories
Enter/Space to craft selected item
Materials automatically added to inventory from combat and treasures
Floating text notifications for material drops
Sound effects for successful crafting and material collection

📦 Material Drop System

Dynamic drop rates based on enemy level
Elite enemies: 2x drop rate multiplier
Boss enemies: Better tier materials
Treasure scaling: Higher value = better materials
Quantity varies by material tier (Common: 1-3, Rare: 1)

- Changed
🔧 Enhanced Loot System

Enemies now drop both items and crafting materials
Treasures provide credits and crafting materials
Combat rewards include material notifications
Updated floating text system for multi-line drops

## 09/05/2025 - v1.4.1
### - Fixed
🔧 **Difficulty Mode System** - Fixed difficulty multiplier not being applied to enemy HP and stats
- Added `set_difficulty_multiplier()` method to EnemyManager
- Enhanced settings integration to properly apply difficulty to all enemy managers
- Enemy HP and level now scale correctly with difficulty setting (0.5x to 2.0x)
- Added debug logging for difficulty application verification

⚔️ **Player Combat Stats Integration** - Fixed player stats not being used in combat calculations
- Enhanced `get_player_stats()` method with proper error handling and fallbacks
- Added `get_stats_from_character_data()` fallback method for direct stat reading
- Fixed combat damage, hit chance, and spell damage calculations to use actual player stats
- Added comprehensive debug logging for stat calculations
- Improved stat validation and null value handling

🎯 **Combat Balance Improvements**
- Enemy stats now properly scale with difficulty multiplier
- Added armor class scaling for enemies based on difficulty
- Enhanced critical hit calculations using actual player dexterity
- Improved spell damage scaling with intelligence/wisdom modifiers
- Added difficulty multiplier storage in enemy data for combat reference

### - Enhanced
📊 **Debug Information** - Added extensive debug logging for combat stat calculations
🎮 **Difficulty Display** - Enhanced difficulty setting display names (Very Easy to Nightmare)
⚙️ **Settings Integration** - Improved settings application across all game managers

## 09/04/2025 - v1.3.0 - ENVIRONMENTAL TREE SYSTEM
### - Added
🌳 **Complete Tree System**
- Tree class with collision detection for blocking player movement
- Three tree types: Normal, Oak, and Pine with distinct visual styles
- Animated tree swaying effects for more natural environment
- World-themed tree generation based on current level/world
- Smart tree placement avoiding conflicts with other objects
- Collision system prevents player from walking through trees

🎨 **Enhanced Environmental Generation**
- Level-based tree count and type selection
- World 1 (Grassland): 15-25 mixed trees (Normal, Oak)
- World 2 (Ice): 8-15 Pine trees for arctic theme
- World 3 (Shadow): 12-20 darker trees for mysterious atmosphere
- World 4 (Elemental): 5-12 mixed types for chaotic environment
- World 5 (Cosmic): 3-8 mystical trees for otherworldly feel

🎮 **Improved Gameplay Mechanics**
- Tree collision detection with movement rollback system
- Trees drawn behind other objects for proper depth layering
- Updated movement system to handle environmental obstacles
- Enhanced world navigation requiring strategic pathfinding around trees

🔧 **Technical Improvements**
- Tree objects inherit proper collision and drawing systems
- Integration with existing world generation and level systems
- Camera-aware tree rendering for performance optimization
- Proper tree scaling and positioning within world bounds

### - Changed
🗺️ **World Generation Updates**
- Modified setup_enhanced_world_objects() to include tree creation
- Enhanced setup_world_objects() fallback method with tree support
- Updated collision detection to prioritize tree blocking
- Improved object spacing algorithms to accommodate larger tree objects

🎯 **Movement System Enhancements**
- Added previous position tracking for collision rollback
- Tree collision checking with movement prevention
- Enhanced player update loop with environmental obstacle detection
- Improved camera update logic to handle blocked movement

### - Technical Details
- Tree class with configurable size, type, and collision properties
- Smart positioning algorithm with 45-pixel minimum distance from other objects
- Visual variety with trunk colors, leaf colors, and size variations
- Animation system with subtle swaying based on world position and time
- Proper integration with existing game state and level management systems

---

## 09/03/2025 - v1.3.0 - MULTI-LEVEL SYSTEM WITH WORLD PROGRESSION
### - Added
🗺️ Complete Multi-Level System

5 distinct worlds with 4 levels each (20 total levels)
Progressive difficulty scaling with world themes
Level completion system with automatic unlocking
World progression: Grasslands → Ice Kingdom → Shadow Realm → Elemental Chaos → Cosmic Nexus
Level persistence system saves current world/level on exit
Each world has unique enemy types, themes, and visual styles

🎮 Enhanced Level Selection Interface

Comprehensive level select screen accessible from main menu and in-game (L key)
Visual world tabs with unlock status indicators
Level difficulty ratings (Easy, Normal, Hard, Expert, Nightmare)
Recommended character level for each area
Current level highlighting and selection animations
Locked level indicators with progression requirements

⚔️ World-Themed Enemy System

5 unique enemy themes matching world aesthetics
50+ different enemy types across all difficulty tiers
Theme-specific boss encounters for each world
Progressive enemy scaling: Basic → Elite → Champion → Ancient → Boss
World-appropriate enemy names and combat aspects
Enhanced reward multipliers based on enemy tier

🌍 Dynamic World Generation

Level-based enemy and treasure spawning
Multiple rest areas in higher difficulty worlds
World-specific background colors and atmospheric effects
Treasure quantity scaling with world difficulty
Strategic rest area placement for challenging levels

📊 Enhanced Progression System

Level completion bonuses with scaling rewards
Automatic next-level unlocking upon area completion
World progression tracking with persistent save system
Enhanced status overlay showing current world and difficulty
Character progression now tied to world completion

🎨 Visual and Audio Enhancements

World-specific color schemes and themes
Enhanced status display with level information
Improved enemy variety with thematic designs
Level completion celebration effects
World transition animations and feedback

- Technical Improvements

Modular LevelManager class for progression tracking
WorldLevelGenerator for dynamic content creation
LevelSelectScreen with full navigation system
Enhanced EnemyManager with theme-based generation
Persistent progression system with JSON save files
Integration with existing combat and character systems

- Gameplay Balance

Difficulty curves calibrated for character progression
World-appropriate loot multipliers (1.0x to 4.0x)
Enemy health scaling from 60 HP (basic) to 666 HP (final boss)
Strategic rest area placement increases with world difficulty
Level completion requirements encourage full exploration

## 09/03/2025 - v1.2.0 - REST SYSTEM WITH COOLDOWN
### - Added
🛌 **Complete Rest System**
- Strategic rest areas placed throughout the world (8 locations)
- 3-minute cooldown timer system for balanced gameplay
- 75-90% HP/MP restoration with randomized recovery amounts
- Visual availability indicators (pulsing when ready, cooldown display)
- Enhanced rest area graphics with blue tent designs
- Free healing alternative to expensive consumable potions

🎨 **Enhanced Rest Area Visuals**
- Dynamic color-coded rest areas (blue=available, red=cooldown, gray=recently used)
- Pulsing animations and glow effects for available rest areas
- Cooldown timer display directly on rest areas
- "Walk into to rest" interaction hints with fade effects
- Enhanced tent graphics with improved visual feedback

📊 **Rest Status HUD System**
- Bottom-left corner rest status display
- Real-time cooldown timer (MM:SS format)
- "Rest Available" indicator when ready to use
- Integration with existing UI systems
- Persistent status tracking across game sessions

🎵 **Audio Integration**
- Rest interaction sound effects
- Healing audio feedback for successful rest
- Error sounds for cooldown attempts
- Integration with existing enhanced audio system

⚖️ **Balanced Resource Management**
- Strategic rest area placement in world corners and center
- Collision detection prioritizes rest areas for better UX  
- Rest areas safe from enemy spawn interference
- Cooldown system prevents rest spam while allowing strategic planning

### - Technical Improvements
- Modular RestManager class for cooldown and interaction logic
- EnhancedRestArea class extending base RestArea with animations
- Integration with existing collision detection system
- Proper world-to-screen coordinate conversion for rest areas
- Rest system update loop integration with main game logic

## 09/02/2025 - v1.1.2 - COMBAT SYSTEM HOTFIX
### - Fixed
🔧 Combat System Fixes

Fixed 'EnhancedCombatManager' object has no attribute 'add_combat_log' error
Enhanced music loading error handling to prevent crashes when sound files are missing
Improved sound system fallback behavior for missing audio files
Added proper error messages for missing music files instead of silent failures
Fixed combat system integration issues that were causing crashes on startup
Fixed "invalid color argument" errors in UI components and combat animations
Fixed "invalid color argument" error when colliding with enemies and entering combat
CRITICAL FIX: Replaced Unicode emojis with ASCII text in combat interface to prevent rendering errors
Fixed combat title rendering error that was preventing combat screen from displaying
Replaced all problematic Unicode characters (⚔️🔮🧪🏃❤️💙⭐🔥❄️⚡✨💚) with safe ASCII alternatives
Added comprehensive error handling in combat text creation and rendering
Fixed color validation in combat animations and particle systems
Added coordinate validation to prevent invalid drawing positions

- Improved
🎵 Audio System Improvements

Better file existence checking before attempting to load music files
More graceful degradation when sound system is unavailable
Enhanced error reporting for debugging audio issues
Sound system now continues working even if individual files are missing

🎨 Visual System Improvements

Added robust color validation throughout the UI system
Enhanced drawing coordinate handling to prevent rendering errors
Improved animation system stability with better value bounds checking
Better fallback handling for visual effects when rendering fails
Added comprehensive error handling in combat text and animation systems
Enhanced combat entry animations with safer initialization
Improved particle system color validation
Combat interface now uses safe ASCII characters instead of Unicode emojis for better compatibility

## 09/02/2025 - v1.1.1 - MODULAR STORE SYSTEM
### - Added
🏪 **Store System Modularization**
- Created dedicated store_system.py module for better code organization
- Enhanced StoreManager class with improved functionality and UI
- StoreIntegration class for seamless game integration
- Improved error handling and visual feedback for purchases
- Better separation of concerns between game logic and store functionality

### - Changed
📦 **Code Architecture Improvements**
- Moved Store class and StoreItem class to store_system.py
- Refactored game_states.py to use new modular store system
- Simplified store input handling and purchase logic
- Enhanced store UI with better visual organization
- Improved collision detection for store interactions

### - Fixed
🔧 **Store System Fixes**
- Fixed store exit cooldown handling through proper integration
- Improved store navigation and scrolling functionality
- Better visual feedback for purchase attempts and insufficient funds
- Enhanced auto-equipment functionality for purchased items

## 09/01/2025 - v1.1.0 - COMBAT EDITION WITH SOUND & ANIMATION
### - Added
🎵 **Complete Audio System Integration**
- Dynamic background music system (menu, world, combat, shop themes)
- Comprehensive sound effects library (40+ different sounds)
- Contextual audio that changes based on game state
- Volume controls and audio fallback for missing files

⚔️ **Enhanced Combat System**
- Advanced turn-based combat with visual effects
- Animated spell casting circles with rotating magical runes
- Sword slash animations with motion blur trails
- Impact flash effects for hits and critical strikes
- Healing sparkle animations for restoration spells
- Screen shake effects for powerful attacks and criticals
- Enhanced floating combat text with bounce and fade effects

🎭 **Visual Combat Enhancements**
- Spell-specific animations (fire, ice, lightning, heal, drain)
- Combat animation system with multiple effect types
- Pulsing health warnings when HP is low
- Enhanced UI with animated selection highlights
- Status effect icons and visual indicators
- Combat log with color-coded messages and fade effects

🔊 **Sound Effect Categories**
- Combat sounds: sword hits, spell casting, critical hits
- UI sounds: menu navigation, item pickup, shop interactions  
- World sounds: footsteps, door opening, treasure collection
- Victory/defeat musical stings and fanfares
- Character-specific sounds for different spell types

⏰ **Combat Balance System**
- Post-combat immunity periods to prevent spam
- Combat entry cooldowns for strategic gameplay
- Enhanced reward system based on enemy difficulty
- Level-scaled loot drops and experience gains
- Elite/Ancient enemy bonus reward multipliers

🎯 **Enhanced Game Integration**
- Seamless integration with existing game systems
- Automatic sound directory creation with placeholders
- Backward compatibility with existing save files
- No breaking changes to existing gameplay mechanics

### - Technical Improvements
- Modular sound manager with fallback support
- Enhanced combat manager with animation pipeline
- Improved combat text system with multiple effect types
- Screen shake system with intensity scaling
- Audio context switching based on game state

## 09/01/2025 - v1.0.4
### - Fixed
🏪 Store exit collision loop - Player now moves away from store on exit
🔒 Added store entry cooldown to prevent immediate re-entry
🎯 Enhanced store exit with proper player repositioning and camera update

## 09/01/2025 - v1.0.3
### - Added
- 🎮 Enhanced Magitech RPG - Combat Edition
- 🏃 Animated character with 8-frame sprites
- 🗺️ Tile-based world map system
- 📷 Smooth camera following
- ✨ Modular code architecture
- 🎯 Enhanced collision detection
- 👤 Character selection system
- 🎛️ Toggleable instructions panel (F1)
- ⚔️ Advanced turn-based combat system
- 🔮 Spell casting with mana management
- 💊 Inventory items usable in combat
- 📊 Character stats affect combat
- 🌟 Status effects and critical hits

## 08/17/2025 - v29...
### - Added
- Added delete character from local and server (v24)
- Added delete session from server (v25)
- Added sync multiplayer game board/book/chapter/enemy/loot (v26)
- Added Take turns in multi-player battle with all players. (v27)
- Added config.py holds mostly vars that could be easily changed
- Added NetworkManager_Class.py moved class to it
- Added classes.py and moved all other classes to it

### - Fixed
- Server_v1 with the correct functions to fix session deletion.
- Server_v1 to sync player and game status/book/chapter/enemy/loot
- Fixed Server_v2 database location to assets folder 
- Fixed Server_v3 with turns in the fight screen while in multi-player
- Fixed Single player combat screen health and damage issues
- Fixed ESC from game board single player, now directs you back to the main menu
- Started cleaning up code
- Fixed Need to nerf player damage, by making the enemy stronger
- Clean up old files

### - Bugs
- Second players actions not syncing to server... (Working on this v28)
- Delete character from server not an option at this time...
- Need to nerf player damage... 
- Battle screen not taking turns

## 08/16/2025 - v23
### - Notes
This is a GUI Client for Multiplayer
This is based off the GUI_v18 Single player game... (This is the BEST Code at this time 08/14/2025)
This uses Server_v1 as of 08/14/2025
- Server_v1 uses HTTP on port 8080, API, and JSON...
This is NOT working code at this time, going to be merging the client_gui_v2 into this codeset.

### Added
- Added Class NetworkManager
- Added all extra imports
- Changed to v23, v20 seemed pretty close.
- Multiplayer Create screen now has dropdowns for Class and Race

### - Fixed
- Chat window not in front (FIXED)
- Battling with multiplayer game board not showing other player, Session getting stuck on server. (FIXED)
- Need to change game board sub menus to ctrl key vs just letter, causing issues. (FIXED)
- Fixed Character data not saving to server


## - 2025-07-25
### Added
- Basic structure and initial features.

### Fixed
- None




The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Describe new features.
- If applicable, mention the issue or pull request number (e.g., #123).

### Changed
- Describe changes in existing functionality.
- For example, refactoring or improvements to existing features.

### Deprecated
- Describe features that are still available but will be removed in future releases.
- Explain why they are deprecated and suggest alternatives.

### Removed
- Describe features that have been removed in this release.
- Link to previous changelog entries or discussions if necessary.

### Fixed
- Describe bug fixes.
- Mention the bug report or issue number (e.g., #456).

### Security
- Describe any security vulnerabilities addressed.

