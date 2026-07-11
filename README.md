# Magitech RPG

## Overview

Magitech RPG is a single-player turn-based role-playing game built with Python and the [Arcade](https://api.arcade.academy/) library (the renderer migration from Pygame completed in v2.2.5 — `pygame` is no longer a dependency). The game features a Zelda-inspired tile-based world map, character creation with D&D-style stats, turn-based combat system, and comprehensive loot mechanics. Players can create characters, explore a procedurally generated world, engage in combat, collect treasures, and progress through 20 levels across 5 unique worlds.

## Recent Changes

**2026-07-11 (v2.10.0)**: **Structured Paths** (roadmap P5 #31). The overworld now has clear dirt routes leading toward every important area. The boss dungeon (world centre), shop (top-right), and rest area (bottom-right) sat at fixed spots but nothing on the ground pointed the way. New `EnhancedTileMap.carve_landmark_paths(lines)` carves L-shaped dirt-path routes from the central hub out to the player spawn, shop, and rest area (crossings become `+` intersections), and `landmark_tiles(cols, rows)` locates each landmark from the grid size using the same pixel positions the game places them at. It runs inside `load_map_from_data` right after flower declutter, guarded so only full-size overworld maps get routed. Also regenerated the bundled `assets/map.txt` with the routes drawn in. +14 tests (`tests/test_structured_paths.py`); full suite **213 → 227** green. See CHANGELOG.md.

**2026-07-11 (v2.9.0)**: **Cleaner grass terrain** (roadmap P5 #30). The overworld is now clean, natural grass instead of a field of scattered flowers. `assets/map.txt` had been sprinkled with 40 decorative flower tiles that competed with paths and landmarks for attention. New `EnhancedTileMap.declutter_flowers(line, row)` swaps every flower marker (`FfRr`) for a grass variant (`G`/`g`/`d`, chosen deterministically by position so the ground stays varied but flower-free); it runs inside `load_map_from_data`, so no flower tile survives to the rendered map regardless of what's on disk. Also rewrote the bundled map (0 flowers remain) and stripped the flower-circle detail from the procedural fallback tileset. +9 tests (`tests/test_world_aesthetics.py`); full suite **204 → 213** green. See CHANGELOG.md.

**2026-07-11 (v2.8.0)**: **Special victory messages** (roadmap P5 #29). Winning a fight now shows a formatted victory banner instead of one flat line: boss kills get a five-line trophy banner (a `★ ═══ ★` border framing `★ 🏆 BOSS DEFEATED! 🏆 ★`, `Level Complete!`, and the `+XP / +Credits` reward), ordinary wins a compact `✦ Victory! ✦` + reward, and a highlighted `★ LEVEL UP! ★` line when you level. **Key fix**: the old messages used astral-plane emoji (🏆/🎉/⭐) that the Arcade renderer silently strips — so the "trophy" never actually showed on-screen; the banner is now built from Basic-Multilingual-Plane glyphs (★ ✦ ═) that render, with the 🏆 kept in the text for the real-pygame backend / logs. Logic lives in a pure, unit-tested `build_victory_messages(...)` helper. +10 tests (`tests/test_victory_messages.py`); full suite **194 → 204** green. See CHANGELOG.md.

**2026-07-11 (v2.7.0)**: **Golden glowing "BOSS DUNGEON" label** (roadmap P5 #28). The dungeon-entrance title no longer sits flat under a static drop-shadow — it now glows like enchanted signage: a pulsing radiant gold aura (3 concentric rings fanned in 8 directions, blending from a dark glow to bright gold with a breathing radius), a live shimmer driving the text + aura brightness, and a gentle ±2px hover. The post-boss **level portal** gets the same treatment in cool teal from the same themed code path. All helpers are pure and deterministic in the animation timer. +7 tests (`tests/test_dungeon_portal.py`, `LabelGlowTests`); full suite **187 → 194** green. See CHANGELOG.md.

**2026-07-11 (v2.6.0)**: **Mystical dungeon entrances** (roadmap P5 #27). Boss-dungeon entrances and the level portals left behind after a boss are now fully animated mystical gateways instead of three flat circles: a pulsing multi-ring glow halo, a three-arm swirling vortex spiralling into a bright pulsing core, and six rising, twinkling motes of light. A new themed palette also makes the two distinguishable — the post-boss **level portal** now renders in cool teal/cyan with a **"LEVEL PORTAL"** label, distinct from the violet gold-labelled **"BOSS DUNGEON"** entrance. All effect helpers are deterministic in the animation timer. +19 tests (`tests/test_dungeon_portal.py`); full suite **168 → 187** green. See CHANGELOG.md.

**2026-07-10 (v2.5.0)**: **Resource-node harvest feedback** (roadmap P5 #26). Rocks, metal veins, streams, and brush now show at a glance whether they can be gathered or are still regrowing, extending v2.4.0's tree feedback to every node. A shared `HarvestableNode` mixin gives them one `regrow_fraction()` progression: instead of a binary colour swap, each node tweens from a dark "spent" look back to full colour as it regrows (rock/metal refill their ore colour and rock shrinks while spent, streams brighten from murky to clear blue, brush greens up and fills back out), and a **pulsing sparkle** appears above a node only once it's harvestable. +13 tests (`tests/test_resource_node_feedback.py`); full suite **155 → 168** green. See CHANGELOG.md.

**2026-07-10 (v2.4.0)**: **Animated trees** (roadmap P5 #25). Tree canopies now sway with a breeze + gust + gentle bob (per-tree phase so a forest isn't in lock-step; trunk stays rooted), leafy trees render as a fuller multi-blob canopy with an outline and sun-catch highlight, and pine layers lean with the wind. Harvest state drives both colour and size: a depleted tree starts small and withered grey-brown and visibly tweens back to healthy green at full size as its respawn timer counts down (`regrow_fraction()`), so a tree's harvest/regrowth state is readable at a glance. +11 tests (`tests/test_tree_animation.py`); full suite **144 → 155** green. See CHANGELOG.md.

**2026-07-10 (v2.3.4)**: **Stop real pygame loading on every launch** (startup / repo hygiene). `Code/gfx.py` was importing real `pygame` eagerly at module load just to back a few never-exercised `__getattr__` fallbacks — so pygame's SDL load + support-prompt banner ran on every Arcade launch (and, since `pygame` was dropped as a dependency in v2.2.5, silently swallowed an `ImportError` on clean installs). Made that import lazy, cached, and banner-silenced (`_get_pygame()`, sets `PYGAME_HIDE_SUPPORT_PROMPT=1`); a normal play session now never imports pygame. Also gitignored `*.log` and removed a stray `importtime.log` profiling artifact. `py_compile` clean; full suite **144/144** green. See CHANGELOG.md.

**2026-07-10 (v2.3.3)**: **Fix overlapping in-game menus** (roadmap P5 #34). The combat log, spell menu, item menu, and store list were drawn at fixed y-coordinates sized for shorter lists and overlapped the panels beneath them. Lowered the combat log (y=390→455), raised the spell/item sub-menus (y=210→190) with an explicit 30px item row pitch, capped the store to 9 rows per page (was 12, ran into the control bar; PgUp/PgDn scroll the rest), and moved the leftover Arcade migration dev overlay behind `MEGITECH_DEBUG` (off by default) so it no longer draws over the live combat HUD. `py_compile` clean; full suite **144/144** green. See CHANGELOG.md.

**2026-07-10 (v2.3.2)**: **Window close & Quit now fully end the app** (roadmap P5 #24). The window "X" button, the Quit menu item, and Escape all now funnel through one idempotent `_shutdown()` in `arcade_app.py`: it saves progression once, closes the window, and calls `arcade.exit()` so the loop returns; `main()` then `os._exit(0)`s to guarantee no lingering background (audio) thread keeps the process alive. Fixes the old double-close (`on_close` → `_shutdown` **and** `super().on_close()`) and the "window vanished but app kept running" case. +5 arcade-guarded tests (`tests/test_window_close.py`); full suite **139 → 144** green. See CHANGELOG.md.

**2026-07-10 (v2.3.1)**: **Difficulty / balance regression checks** (roadmap P4 #15). New `tests/test_balance_regression.py` (16 tests) pins the exact numeric output of the balance-critical formulas — enemy HP scaling and difficulty-multiplier application (`EnemyManager.create_scaled_enemy`/`create_scaled_boss`), book-level→tier boundaries, the `[0.1, 3.0]` difficulty clamp, and armor-class (`10 + dex_bonus + best_armor`, taking the max armor bonus rather than the sum) — with all randomness pinned via `mock.patch`. Guards against the kind of silent tuning regressions the game hotfixed in v1.4.1/v1.7.3. Full suite **123 → 139** green. See CHANGELOG.md.

**2026-07-10 (v2.3.0)**: **Versioned save schema + automatic save-file migration** (roadmap P4 #14). Character saves (`Characters/*.json`) now carry a `Save_Version` and are healed on load: new `Code/save_migration.py` backfills every required field (weapon/armor slots, `Aspect1_Mana`, ability scores, `Inventory`, …), coerces numeric fields and clamps the non-negative ones, and stamps the current schema version — so older/partial saves no longer raise a `KeyError` in code that reads those fields by direct index. `CharacterManager.load_character()` runs the migration and re-writes the healed save to disk; the pass is conservative (only adds/fixes, never deletes unknown keys) and idempotent. +14 tests (`tests/test_save_migration.py`); full suite **109 → 123** green. See CHANGELOG.md.

**2026-07-10 (v2.2.5)**: Arcade migration **COMPLETE — `pygame` is no longer a dependency** (migration step 6, final part). Removed `pygame>=2.5` from `requirements.txt`; Arcade is now the sole runtime dependency. Simplified the backend switch to a single source of truth (`Code/backend.py`): unset/empty/`arcade` → the `Code.gfx` Arcade shim (default), `MEGITECH_BACKEND=pygame` → real pygame as an explicit self-install opt-in. Routed `Code/ui_components.py` and all 11 gameplay modules' bare `import pygame` through `Code.backend`, and reworked the test suite to run on the shim with no pygame installed. Verified **with pygame uninstalled**: 20/20 module import sweep, full suite **109/109** (1 skipped: display-dependent render_smoke), `py_compile` clean, backend resolution matrix correct. Roadmap **P1 #1 is closed**. See CHANGELOG.md.

**2026-07-10 (v2.2.4)**: Arcade migration — **display and event now run through the shim, not pygame** (migration step 6, part 3). Ported the last runtime call sites still delegating to real pygame: `pygame.display.set_mode`/`set_caption` (`main.py.__init__`) and `pygame.event.Event(...)` (crafting input). Added native `display` (`set_mode` → off-screen `gfx.Surface`; in-memory caption; lifecycle no-ops) and `event` (`Event` aliased to the native class; queue no-ops) modules to `Code/gfx.py`, plus a `NOEVENT` constant, and made `init()`/`quit()` native. **As of v2.2.4 nothing the game exercises at runtime routes through real pygame under the Arcade backend** — only unused extras (`locals`/`Color`/`Vector2`/`mouse`) still delegate. +7 tests; suite **102→109** green under both backends. The final step is dropping `pygame>=2.5` from `requirements.txt` and simplifying the backend switch (needs the test suite reworked to run without a real pygame install). See CHANGELOG.md.

**2026-07-10 (v2.2.3)**: Arcade migration — **sprite and input constants now run through the shim, not pygame** (migration step 6, part 2). `Code/tile_map.py` and `Code/animated_player.py` were the last two modules importing real pygame directly (via `from pygame.locals import *` and by subclassing `pygame.sprite.Sprite`). Added a native `Sprite` class + `sprite` namespace to `Code/gfx.py` (module-level, so it wins over the `__getattr__` delegation) and removed the `locals` star-imports (dead in `tile_map`; `Rect`/`K_*` qualified as `pygame.*` in `animated_player`). Both modules now import clean under both backends and carry `gfx.Sprite` in their MRO under Arcade. +4 tests; suite **98→102** green under both backends. Only `display`/`event` (both in `main.py`) still route through real pygame — the last piece before the dep can be dropped. See CHANGELOG.md.

**2026-07-10 (v2.2.2)**: Arcade migration — **audio and timing now run through Arcade, not pygame** (migration step 6, part 1). `Code/gfx.py` gained native `mixer` (`arcade.Sound`-backed SFX + streaming music, defensive no-op with no audio device), `time` (stdlib-clock `wait`/`Clock`/`get_ticks`), and an `error` exception class, so under the default Arcade backend nothing routes audio/timing through real pygame. +17 tests; suite **98/98**; verified against real `arcade.Sound` under xvfb (20/20 WAVs load, play/stop crash-free). `pygame` is still imported for the remaining `display`/`event`/`sprite`/`locals` delegations — porting those is the last step before the dep can be dropped. See CHANGELOG.md.

**2026-07-10 (v2.2.1)**: Arcade migration — **the deprecated pygame `run()` loop is removed; Arcade is the only entry point.** Deleted `EnhancedGameManager.run()` and the `MEGITECH_BACKEND=pygame` launch fallback, so `python main.py` unconditionally opens the Arcade window. `MEGITECH_BACKEND` now only selects the drawing binding used by the headless test suite. Verified: suite **85/85** (render_smoke 13/13), `python main.py` launches crash-free under xvfb. Note: `pygame` stays a runtime dependency — `Code/gfx.py` still delegates audio, timing, and input to it (dropping it is the final migration step). See CHANGELOG.md.

**2026-07-10 (v2.2.0)**: Arcade migration — **the default backend is flipped: `python main.py` now launches the Arcade window.** main.py sets `MEGITECH_BACKEND=arcade` (+ the headless SDL dummy video driver) before importing the game and delegates to `arcade_app.py`, so the game boots on the Arcade renderer out of the box. The legacy hand-rolled pygame `run()` loop is **deprecated but retained one release** as an opt-in fallback: `MEGITECH_BACKEND=pygame python main.py`. Verified: full suite **85/85**, both backend paths bind the correct renderer, all 13 screens render crash-free, and `python main.py` launches the Arcade window headlessly (xvfb) without error. See CHANGELOG.md.

**2026-07-10 (v2.1.19)**: Arcade migration — fixed a latent API-compat bug in the `gfx` shim's `Font`. `Font.__init__` stored the point size as `self.size`, shadowing pygame's standard `size(text) -> (w, h)` measuring *method* with an int, so `font.size("text")` would raise `'int' object is not callable`. Renamed the stored size to `self.font_size` so the method works, restoring the shim's drop-in `import pygame` contract. Full suite now **82/82**. See CHANGELOG.md.

**2026-07-10 (v2.1.21)**: Arcade migration — **on-device visual verification is done and now automated.** Every screen was confirmed to render through the `Code/gfx.py` shim under `MEGITECH_BACKEND=arcade`: all **13/13** game states (menu, character select/create, game board, store, inventory, character sheet, help, level select, settings, crafting, fight) paint crash-free. Added `tests/render_smoke.py` (drives the real game through every state headlessly, renders each to a PNG, asserts no crash + non-black frame) and `tests/test_render_smoke.py` (auto-uses `xvfb-run`, skips cleanly when arcade/display are absent). Full suite now **85/85**. This unblocks flipping the Arcade backend on by default (the last migration step). See CHANGELOG.md.

**2026-07-10 (v2.1.18)**: Arcade migration — fixed semi-transparent overlays rendering as solid black under the Arcade backend. The crafting and store/inventory screens dim the world behind their panels with a `fill(BLACK)` + `set_alpha(180/200)` overlay, but the `gfx` shim ignored the surface alpha when replaying an off-screen surface's fill/shape ops, so the overlay was fully opaque and hid everything behind it. Added `_apply_alpha()` and threaded it through every shape op in `Surface._replay`. Full suite now **80/80**. See CHANGELOG.md.

**2026-07-10 (v2.1.17)**: Arcade migration — added the first direct test coverage for the `Code/gfx.py` rendering shim (`tests/test_gfx.py`, 36 tests). It pins the shim's GPU-independent core — the pygame→Arcade Y-axis flip, color/rect/finite normalization, `_safe_text` emoji stripping, the `Rect` API, off-screen surface record/replay and `pygame.draw.*` op recording, `Font` metric fallback, and key/event constants — by forcing the no-arcade code path, so it runs deterministically headless whether or not `arcade` is installed. Full suite now **78/78**. This is a safety net for the remaining migration work (the on-device visual pass and any shim tuning it requires). See CHANGELOG.md.

**2026-07-10 (v2.1.14)**: Documentation sync — the "Project Architecture" section was frozen at the pre-v1.6 layout (it listed `game_states.py` as the entry point and a flat, root-level module list). Updated it to reflect the real structure: `main.py` (default pygame entry) and `arcade_app.py` (Arcade entry) at the root, all game modules under the `Code/` package, the `MEGITECH_BACKEND` runtime backend switch, centralized version metadata in `Code/version.py`, and the gitignored runtime save directories. See CHANGELOG.md.

**2026-07-09 (v2.1.9)**: Arcade migration — fixed the last standalone-import bug. `Code/combat_integration.py` referenced `game_data` as a top-level module (`from game_data import CharacterManager`) instead of the package path, so it failed to import outside the running game under both backends. Changed to `from Code.game_data import CharacterManager`. The full `Code/*.py` import sweep is now 20/20 clean under both the pygame and Arcade backends; the test suite stays 42/42 green. See CHANGELOG.md.

**2026-07-08 (v2.1.2)**: Added a Ruff linter config (`pyproject.toml`) — the project's first tooling config. It uses a high-signal rule set (`F`/`E9`/`B`) aimed at dead code and unused imports rather than a style reformat, and ignores `F403`/`F405` because the game deliberately distributes its `pygame` binding via `from Code.ui_components import *`. That drops the report from 527 raw findings to 43 real ones (unused imports/variables/loop vars, placeholder-less f-strings, one redefinition), now logged for a follow-up cleanup pass. Dev-only tools moved to `requirements-dev.txt`. Run with `ruff check .`. See CHANGELOG.md.

**2026-07-08 (v2.1.1)**: Added a minimal unit-test suite (`tests/`) using the standard-library `unittest` — no third-party runner required. It forces SDL's dummy drivers so the Pygame-coupled modules run headlessly (CI/containers), and covers combat math (`calculate_damage`/`calculate_spell_damage`/`calculate_hit_chance` + spell gating), level progression (unlock/selection/completion cascades), and crafting logic (recipes, materials, drop table). Run with `python -m unittest discover -s tests -v` — 78 tests, all green (now including `test_gfx.py`, which covers the Pygame→Arcade rendering shim). See `tests/README.md` and CHANGELOG.md.

**2026-07-08 (v2.1.0)**: Characters now spawn into their last-played level. Progression (`current_world`/`current_level`) was already persisted per character, but loading or creating a character jumped straight to the game board without rebuilding the world, so everyone spawned into World 1-1. A new `enter_game_board_for_current_level()` rebuilds the world for the persisted level, recenters the player, and snaps the camera before entering play. Explicit level selection is unchanged. See CHANGELOG.md.

**2026-07-08 (v2.0.6)**: Save-file tracking policy — `Characters/*.json` and `SaveProgression/*.json` are now treated as live per-player save state and are **gitignored**, not versioned. A fresh clone starts with no saved characters; the game creates them at runtime and the loader discovers characters by scanning the `Characters/` directory. Both folders are kept in the repo via `.gitkeep`. This ends the working-tree churn that previously came from playtesting. See CHANGELOG.md.

**2026-07-07 (v2.0.5)**: pygame → Arcade migration — backend now switches end-to-end. `Code/ui_components.py` selects the renderer from the `MEGITECH_BACKEND` env var (unset → real pygame, the default `python main.py` path; `arcade` → the `Code.gfx` Arcade shim, set automatically by `arcade_app.py`) and star-exports it to every module. `Code/gfx.py` is now a hybrid shim: rendering routes to Arcade while non-render calls (audio, timing, input) delegate to real pygame, and off-screen surfaces (HUD overlay, tile sheets) are recorded and replayed. See CHANGELOG.md for details.

**2025-09-08**: Project successfully imported and configured for Replit environment
- Installed Python 3.11 and pygame
- Configured VNC workflow for desktop game display
- Game runs successfully with all features functional
- Added comprehensive crafting system with 15+ recipes and material collection

## User Preferences

- Simple, everyday language for communication
- Prefer modular code architecture
- Focus on gameplay balance and user experience

## Project Architecture

### System Requirements
- **Language**: Python 3.11
- **Dependencies**: arcade ≥ 3.3 (sole runtime dependency) — see `requirements.txt`. `pygame` was dropped in v2.2.5.
- **Display**: Requires a desktop GUI (or VNC) to play; imports and tests run headless (no display, audio device, or pygame install needed)
- **Entry Points**: `python main.py` (default — launches Arcade) or `python arcade_app.py` (direct Arcade window)

> **Backend note (v2.2.5):** the pygame → [Arcade](https://api.arcade.academy/) migration is
> **complete** — `pygame` is no longer a dependency. `python main.py` opens the Arcade window (it
> sets `MEGITECH_BACKEND=arcade` before importing the game and delegates to `arcade_app.py`). The
> `Code/gfx.py` shim implements the pygame surface/draw/font/mixer/time/sprite/display/event API
> slice the game uses on top of Arcade, so no `import pygame` is required to run or test the game.
> `MEGITECH_BACKEND` selects the drawing binding via the single switch in `Code/backend.py`
> (star-exported by `Code/ui_components.py`): unset/empty/`arcade` → the `Code.gfx` shim (default),
> `MEGITECH_BACKEND=pygame` → real pygame as an explicit opt-in for developers who install pygame
> themselves. All game modules import the active backend via `Code/backend.py` rather than
> importing `pygame` directly.

### Core Components

#### Game Engine
- **Main Game Loop**: `EnhancedGameManager` class in `main.py`
- **State Management**: Multiple game states (menu, character creation, gameplay, combat, etc.) — see `GameState` in `main.py`
- **Rendering**: 800x600 window; Pygame by default, Arcade via the `Code/gfx.py` shim
- **Version Metadata**: centralized in `Code/version.py` (`__version__`, `CAPTION`)
- **Audio System**: Sound effects and music (with fallback for missing files)

#### Game Systems (all under `Code/`)
- **Combat System**: Turn-based combat with D&D-style calculations (`combat_system.py`, `enhanced_combat_system.py`, and the `*_integration.py` bridges)
- **Character System**: Six races and six classes with stat bonuses (`character_creation.py`)
- **World Generation**: Procedural tile-based world with multiple object types (`tile_map.py`)
- **Level System**: 20 levels across 5 unique worlds with progressive difficulty (`level_system.py`)
- **Store System**: In-game shops for purchasing equipment (`store_system.py`)
- **Rest System**: Strategic rest areas with cooldown timers (`rest_system.py`)
- **Inventory System**: Item management and equipment (`inventory_system.py`)
- **Settings System**: Configurable game settings (`settings_system.py`)
- **Crafting System**: Workshop for creating weapons, armor, accessories, and consumables (`crafting_system.py`)
- **Enemy Management**: Enemy loading and scaling (`enhanced_enemy_manager.py`)

#### Data Management
- **Character Data**: JSON-based character persistence in `/Characters/` directory
- **Game Configuration**: `game_config.json` and `game_settings.json`
- **Progress Tracking**: Level progression and world completion tracking
- **Save System**: Auto-save functionality with character and progress persistence

### Game Features

#### World System
- **5 Unique Worlds**: Grasslands → Ice Kingdom → Shadow Realm → Elemental Chaos → Cosmic Nexus
- **20 Total Levels**: 4 levels per world with progressive difficulty
- **Environmental Objects**: Trees, treasures, enemies, shops, rest areas
- **Dynamic Generation**: Level-appropriate content scaling

#### Combat & Progression
- **Turn-Based Combat**: Strategic combat with spells, weapons, and items
- **Character Classes**: Warrior, Wizard, Rogue, Cleric, Ranger, Sorcerer
- **Character Races**: Human, Elf, Dwarf, Halfling, Orc, Gnome
- **Level System**: Experience-based progression with stat improvements
- **Equipment System**: Weapons, armor, and consumables
- **Crafting System**: Comprehensive crafting with 15+ recipes, 15+ materials, and 4 rarity tiers

#### Audio & Visual
- **Sound Effects**: 40+ different sound effects for various game actions
- **Background Music**: Context-appropriate music for different game states
- **Animations**: Combat animations, spell effects, and visual feedback
- **UI Components**: Comprehensive user interface with multiple screens

### File Structure
```
/
├── main.py                     # Game engine + entry point (v2.2.1: unconditionally launches the Arcade window) — EnhancedGameManager
├── arcade_app.py               # Arcade window entry point (sets MEGITECH_BACKEND=arcade, drives the state machine)
├── requirements.txt            # Runtime deps (arcade only; pygame dropped in v2.2.5)
├── requirements-dev.txt        # Dev-only deps (ruff)
├── pyproject.toml              # Ruff linter config
├── CHANGELOG.md                # Version history
├── ROADMAP.md                  # Automation/agent backlog
├── Code/                       # All game modules (importable package)
│   ├── version.py              # Central version metadata (__version__, CAPTION)
│   ├── backend.py              # Runtime pygame/Arcade backend switch
│   ├── gfx.py                  # pygame→Arcade compatibility shim
│   ├── ui_components.py        # UI elements, rendering, backend star-export
│   ├── animated_player.py      # Player character animation
│   ├── character_creation.py   # Character creation system
│   ├── combat_system.py        # Combat mechanics
│   ├── enhanced_combat_system.py     # Enhanced combat with effects
│   ├── combat_integration.py         # Combat/game-state bridge
│   ├── enhanced_combat_integration.py
│   ├── enhanced_enemy_manager.py     # Enemy loading and scaling
│   ├── tile_map.py             # World generation and tile system
│   ├── game_data.py            # Data management and character handling
│   ├── level_system.py         # Multi-level world system
│   ├── store_system.py         # Shop and trading system
│   ├── rest_system.py          # Rest areas and recovery system
│   ├── inventory_system.py     # Inventory and equipment
│   ├── settings_system.py      # Game configuration
│   ├── crafting_system.py      # Crafting workshops and recipes
│   └── debug.py                # Gated debug output (MEGITECH_DEBUG)
├── tests/                      # Headless unittest suite
├── Characters/                 # Character save files (gitignored, runtime)
├── SaveProgression/            # Per-character level progression (gitignored, runtime)
├── Images/                     # Game sprites and graphics
├── Sounds/                     # Audio files and sound effects
├── Books/                      # Level and world data
└── Enemies/                    # Enemy configurations
```

### Development Notes

#### Running the Game
- Install dependencies: `pip install -r requirements.txt`
- Run (Arcade) — **v2.2.1**: `python main.py` (opens the Arcade window) or equivalently `python arcade_app.py`. The deprecated `MEGITECH_BACKEND=pygame` launch fallback was removed in v2.2.1.
- Game automatically creates sample files and directories on first run
- A desktop display (or VNC) is required for GUI interaction
- Game supports keyboard controls for all interactions

#### Running the Tests
- Execute `python -m unittest discover -s tests -v` from the repository root
- Uses the standard-library `unittest` (no extra dependencies — the suite runs on the `Code.gfx` shim with no pygame or display required)
- The Arcade render-verification test (`test_render_smoke.py`) skips automatically unless `arcade` is installed and a display (or `xvfb-run`) is available; run it directly on a headless box with `xvfb-run -a python3 tests/render_smoke.py`
- Runs headless via SDL dummy drivers — no display or audio device needed

#### Key Controls
- Arrow Keys: Movement
- L: Level select screen
- R: Open crafting workshop
- I: Inventory
- C: Character sheet
- H: Help screen
- F1: Toggle instructions
- ESC: Back/Exit from screens
- Various hotkeys for combat and menu navigation

#### Technical Features
- Modular architecture with separate systems
- Error handling for missing audio files
- Automatic save system
- Debug mode available via configuration
- Fallback systems for missing resources

The game is a comprehensive single-player RPG with extensive features and a polished gameplay experience.