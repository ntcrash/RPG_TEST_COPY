# Magitech RPG

## Overview

Magitech RPG is a single-player turn-based role-playing game built with Python and Pygame. The game features a Zelda-inspired tile-based world map, character creation with D&D-style stats, turn-based combat system, and comprehensive loot mechanics. Players can create characters, explore a procedurally generated world, engage in combat, collect treasures, and progress through 20 levels across 5 unique worlds.

## Recent Changes

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
- **Main Dependency**: pygame 2.6.1
- **Display**: Requires VNC for desktop GUI display
- **Entry Point**: `game_states.py`

### Core Components

#### Game Engine
- **Main Game Loop**: `EnhancedGameManager` class in `game_states.py`
- **State Management**: Multiple game states (menu, character creation, gameplay, combat, etc.)
- **Rendering**: Pygame-based graphics with 800x600 resolution
- **Audio System**: Sound effects and music (with fallback for missing files)

#### Game Systems
- **Combat System**: Turn-based combat with D&D-style calculations (`enhanced_combat_system.py`)
- **Character System**: Six races and six classes with stat bonuses (`character_creation.py`)
- **World Generation**: Procedural tile-based world with multiple object types (`tile_map.py`)
- **Level System**: 20 levels across 5 unique worlds with progressive difficulty (`level_system.py`)
- **Store System**: In-game shops for purchasing equipment (`store_system.py`)
- **Rest System**: Strategic rest areas with cooldown timers (`rest_system.py`)
- **Settings System**: Configurable game settings (`settings_system.py`)
- **Crafting System**: Workshop for creating weapons, armor, accessories, and consumables (`crafting_system.py`)

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
├── game_states.py          # Main game engine and entry point
├── animated_player.py      # Player character animation
├── character_creation.py   # Character creation system
├── combat_system.py        # Combat mechanics
├── enhanced_combat_system.py # Enhanced combat with effects
├── tile_map.py             # World generation and tile system
├── ui_components.py        # UI elements and rendering
├── game_data.py            # Data management and character handling
├── level_system.py         # Multi-level world system
├── store_system.py         # Shop and trading system
├── rest_system.py          # Rest areas and recovery system
├── settings_system.py      # Game configuration
├── crafting_system.py      # Crafting workshops and recipes
├── game_config.json        # Game configuration settings
├── game_settings.json      # Player preferences
├── /Characters/            # Character save files
├── /Images/                # Game sprites and graphics
├── /Sounds/                # Audio files and sound effects
├── /Books/                 # Level and world data
└── /Enemies/               # Enemy configurations
```

### Development Notes

#### Running the Game
- Execute `python game_states.py` to start the game
- Game automatically creates sample files and directories on first run
- VNC display required for GUI interaction
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