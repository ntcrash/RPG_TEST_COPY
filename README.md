# Magitech RPG

## Overview

Magitech RPG is a multiplayer turn-based role-playing game built with Python and Pygame. The game features a Zelda-inspired tile-based world map, real-time multiplayer functionality, character creation with D&D-style stats, turn-based combat system, and comprehensive loot mechanics. Players can create characters, explore a procedurally generated world, engage in combat, and interact with other players in real-time sessions.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Client Architecture
- **Game Client**: Built with Pygame for rendering and game loop management
- **Modular Design**: Separate modules for combat (combat_system.py), world generation (world_map.py), character creation (new_character_form.py), and network communication (network_manager.py)
- **State Management**: Centralized game state handling in main.py with distributed subsystem states

### Game Systems
- **Combat System**: Turn-based combat with D&D-style stat calculations and modifiers
- **Character System**: Six races (Human, Elf, Dwarf, Halfling, Orc, Gnome) and six classes (Warrior, Wizard, Rogue, Cleric, Ranger, Sorcerer) with stat bonuses
- **World Generation**: Procedural tile-based world with forests, lakes, mountains, towns, and dungeons
- **Loot System**: Comprehensive item generation with multiple rarities and types (weapons, armor, consumables, accessories)

### Data Storage
- **JSON**: Local file-based storage for users, characters, items, and sessions
- **Character Persistence**: Full character data including stats, inventory, and progress

## External Dependencies

### Core Libraries
- **Pygame**: Game rendering, input handling, and audio system

### System Libraries
- **Threading**: Concurrent operations and real-time updates
- **JSON**: Data serialization for network communication
- **Random**: Procedural generation and game mechanics
- **Time/DateTime**: Game timing and session management
- **UUID**: Unique identifier generation for sessions and entities
