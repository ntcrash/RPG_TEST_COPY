# Magitech RPG

## Overview

Magitech RPG is a single-player turn-based role-playing game built with Python and Pygame. The game features a Zelda-inspired tile-based world map, character creation with D&D-style stats, turn-based combat system, and comprehensive loot mechanics. Players can create characters, explore a procedurally generated world, engage in combat, collect treasures, and progress through 20 levels across 5 unique worlds.

## Recent Changes

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