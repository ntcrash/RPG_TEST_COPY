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
- **Real-time Updates**: Continuous synchronization with server for multiplayer features

### Server Architecture
- **HTTP REST API**: Flask-based server (server.py) handling all client-server communication
- **Session Management**: Multi-player session support with real-time position tracking
- **Database Layer**: SQLite database for persistent storage of user accounts, characters, and game state
- **Thread-safe Operations**: Comprehensive locking mechanisms for concurrent player actions

### Game Systems
- **Combat System**: Turn-based combat with D&D-style stat calculations and modifiers
- **Character System**: Six races (Human, Elf, Dwarf, Halfling, Orc, Gnome) and six classes (Warrior, Wizard, Rogue, Cleric, Ranger, Sorcerer) with stat bonuses
- **World Generation**: Procedural tile-based world with forests, lakes, mountains, towns, and dungeons
- **Loot System**: Comprehensive item generation with multiple rarities and types (weapons, armor, consumables, accessories)

### Network Architecture
- **REST API Communication**: HTTP requests for all server interactions
- **Real-time Synchronization**: Frequent position and state updates (50ms client updates, 200ms server sync)
- **Activity Tracking**: Sequence-based activity system for maintaining game state consistency
- **Combat Sessions**: Server-managed turn-based combat with timeout mechanisms

### Data Storage
- **SQLite Database**: Local file-based storage for users, characters, items, and sessions
- **Session State**: In-memory storage for active game sessions and real-time player data
- **Character Persistence**: Full character data including stats, inventory, and progress

## External Dependencies

### Core Libraries
- **Pygame**: Game rendering, input handling, and audio system
- **Flask**: Web server framework for REST API
- **Flask-CORS**: Cross-origin resource sharing for web client support
- **SQLite3**: Built-in Python database for persistence
- **Requests**: HTTP client library for server communication
- **Werkzeug**: Password hashing and security utilities

### System Libraries
- **Threading**: Concurrent operations and real-time updates
- **JSON**: Data serialization for network communication
- **Random**: Procedural generation and game mechanics
- **Time/DateTime**: Game timing and session management
- **UUID**: Unique identifier generation for sessions and entities

### Potential Integrations
- **Database Migration**: System designed to support future PostgreSQL migration while maintaining Drizzle ORM compatibility
- **Web Client**: CORS-enabled server ready for browser-based client implementation
- **Asset Management**: Extensible asset system for future graphics and audio content