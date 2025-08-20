# Changelog
All notable changes to this project will be documented in this file.

## - ToDo
- Add melee only attack
- Add Different Spell cast in fight
- Add multiplayer health and mana display
- Add more levels to books and chapters
- Clean up code... 
- Get rid of Debugging... 
- Battle screen not taking turns
- Dying needs to take credits

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

