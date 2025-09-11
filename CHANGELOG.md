# Changelog
All notable changes to this project will be documented in this file.

## - ToDo
- Dying needs to take credits
- Fix Main Game sound

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

