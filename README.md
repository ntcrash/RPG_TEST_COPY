# Magitech RPG

## Overview

Magitech RPG is a single-player turn-based role-playing game built with Python (currently migrating its renderer from Pygame to the Arcade library). The game features a Zelda-inspired tile-based world map, character creation with D&D-style stats, turn-based combat system, and comprehensive loot mechanics. Players can create characters, explore a procedurally generated world, engage in combat, collect treasures, and progress through 20 levels across 5 unique worlds.

## Recent Changes

**2026-07-10 (v2.1.14)**: Documentation sync — the "Project Architecture" section was frozen at the pre-v1.6 layout (it listed `game_states.py` as the entry point and a flat, root-level module list). Updated it to reflect the real structure: `main.py` (default pygame entry) and `arcade_app.py` (Arcade entry) at the root, all game modules under the `Code/` package, the `MEGITECH_BACKEND` runtime backend switch, centralized version metadata in `Code/version.py`, and the gitignored runtime save directories. See CHANGELOG.md.

**2026-07-09 (v2.1.9)**: Arcade migration — fixed the last standalone-import bug. `Code/combat_integration.py` referenced `game_data` as a top-level module (`from game_data import CharacterManager`) instead of the package path, so it failed to import outside the running game under both backends. Changed to `from Code.game_data import CharacterManager`. The full `Code/*.py` import sweep is now 20/20 clean under both the pygame and Arcade backends; the test suite stays 42/42 green. See CHANGELOG.md.

**2026-07-08 (v2.1.2)**: Added a Ruff linter config (`pyproject.toml`) — the project's first tooling config. It uses a high-signal rule set (`F`/`E9`/`B`) aimed at dead code and unused imports rather than a style reformat, and ignores `F403`/`F405` because the game deliberately distributes its `pygame` binding via `from Code.ui_components import *`. That drops the report from 527 raw findings to 43 real ones (unused imports/variables/loop vars, placeholder-less f-strings, one redefinition), now logged for a follow-up cleanup pass. Dev-only tools moved to `requirements-dev.txt`. Run with `ruff check .`. See CHANGELOG.md.

**2026-07-08 (v2.1.1)**: Added a minimal unit-test suite (`tests/`) using the standard-library `unittest` — no third-party runner required. It forces SDL's dummy drivers so the Pygame-coupled modules run headlessly (CI/containers), and covers combat math (`calculate_damage`/`calculate_spell_damage`/`calculate_hit_chance` + spell gating), level progression (unlock/selection/completion cascades), and crafting logic (recipes, materials, drop table). Run with `python -m unittest discover -s tests -v` — 36 tests, all green. See `tests/README.md` and CHANGELOG.md.

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
- **Dependencies**: pygame ≥ 2.5 (legacy renderer) and arcade ≥ 3.3 (new renderer) — see `requirements.txt`
- **Display**: Requires a desktop GUI (or VNC) to play; imports and tests run headless via SDL dummy drivers
- **Entry Points**: `main.py` (default, pygame) or `arcade_app.py` (Arcade backend)

> **Backend note (v2.x migration):** the game is mid-migration from Pygame to the
> [Arcade](https://api.arcade.academy/) library. The renderer is selected at runtime by the
> `MEGITECH_BACKEND` env var — unset falls back to real pygame (`python main.py`), while
> `arcade_app.py` sets `MEGITECH_BACKEND=arcade` to route drawing through the `Code/gfx.py`
> Arcade compatibility shim. All game modules import the active backend via
> `Code/backend.py` / `Code/ui_components.py` rather than importing `pygame` directly.

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
├── main.py                     # Main game engine + default (pygame) entry point — EnhancedGameManager
├── arcade_app.py               # Arcade entry point (sets MEGITECH_BACKEND=arcade, drives the state machine)
├── requirements.txt            # Runtime deps (pygame, arcade)
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
- Default (Pygame) backend: `python main.py`
- Arcade backend (v2.x migration): `MEGITECH_BACKEND=arcade python arcade_app.py`
- Game automatically creates sample files and directories on first run
- A desktop display (or VNC) is required for GUI interaction
- Game supports keyboard controls for all interactions

#### Running the Tests
- Execute `python -m unittest discover -s tests -v` from the repository root
- Uses the standard-library `unittest` (no extra dependencies beyond pygame)
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