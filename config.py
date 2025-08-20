import pygame

# Screen settings
WIDTH, HEIGHT = 900, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Magitech RPG Adventure")

# Initialize Pygame
pygame.init()
# Fonts
try:
    title_font = pygame.font.Font(None, 64)
    subtitle_font = pygame.font.Font(None, 36)
    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 20)
    large_font = pygame.font.Font(None, 48)
except:
    title_font = pygame.font.Font(None, 64)
    subtitle_font = pygame.font.Font(None, 36)
    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 20)
    large_font = pygame.font.Font(None, 48)

# Updated constants at the top of your file
SERVER_URL = "http://localhost:8080"
UPDATE_INTERVAL = 0.2  # Update server every 200ms
SYNC_INTERVAL = 0.5    # Sync with other players every second

# Add these new constants for better multiplayer experience
POSITION_THRESHOLD = 3  # Minimum pixels to move before sending update
MAX_SYNC_FAILURES = 5   # Max failed syncs before reconnection attempt

# Enhanced color palette
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

# Enhanced UI Colors
DARK_BLUE = (25, 25, 55)
LIGHT_BLUE = (100, 150, 255)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
HEALTH_BAR_COLOR = (255, 50, 50)
HEALTH_BAR_BG = (100, 0, 0)
MANA_BAR_COLOR = (50, 100, 255)
MANA_BAR_BG = (0, 0, 100)
UI_BG_COLOR = (30, 30, 30)
UI_BORDER_COLOR = (100, 100, 100)
ENEMY_HEALTH_COLOR = (255, 100, 100)
DAMAGE_TEXT_COLOR = (255, 255, 0)
HEAL_TEXT_COLOR = (0, 255, 0)

# Menu colors
MENU_BG = (15, 20, 35)
MENU_ACCENT = (45, 85, 135)
MENU_HIGHLIGHT = (65, 105, 165)
MENU_TEXT = (220, 220, 220)
MENU_SELECTED = (255, 215, 0)

# Help content
HELP_CONTENT = {
    "overview": [
        "MAGITECH RPG ADVENTURE",
        "",
        "Welcome to a magical world where technology and sorcery collide!",
        "You are a War Mage, wielding both spell and blade in your quest",
        "for glory and treasure.",
        "",
        "OBJECTIVE:",
        "• Explore the game world and defeat enemies",
        "• Collect loot and gain experience",
        "• Visit shops to buy equipment and potions",
        "• Rest at camps to restore your health and mana",
        "• Level up to become the ultimate War Mage (Max Level 50)!"
    ],

    "controls": [
        "GAME CONTROLS",
        "",
        "MENU NAVIGATION:",
        "• Arrow Keys - Navigate menu options",
        "• Enter - Select option",
        "• ESC - Go back/Exit",
        "",
        "GAME WORLD:",
        "• Arrow Keys - Move your character",
        "• Walk into objects to interact with them",
        "• Ctrl+I - Open inventory",
        "• Ctrl+C - Open character sheet",
        "• Ctrl+B - Change book/chapter",
        "• Ctrl+H - Open help system",
        "• M - Toggle background music",
        "• ESC - Logout (multiplayer) / Quit (single player)",
        "",
        "MULTIPLAYER:",
        "• T - Toggle chat window",
        "• Type freely in chat when open",
        "• ESC - Close chat / Logout from session",
        "",
        "COMBAT:",
        "• SPACE - Attack enemy",
        "• H - Use health potion",
        "• M - Use mana potion",
        "• Ctrl+I - Open inventory",
        "• ESC - Flee from battle"
    ],

    "gameplay": [
        "GAMEPLAY MECHANICS",
        "",
        "CHARACTER SYSTEM:",
        "• Health Points (HP) - Your life force",
        "• Mana Points (MP) - Required for magic attacks",
        "• Experience Points (XP) - Gained by defeating enemies",
        "• Level - Increases stats and abilities (Max 50)",
        "• Credits - Currency for purchasing items",
        "",
        "KEYBOARD SHORTCUTS:",
        "• Ctrl+I - Quick access to inventory",
        "• Ctrl+C - View character statistics",
        "• Ctrl+B - Change adventure world/chapter",
        "• Ctrl+H - Open this help system",
        "• T - Multiplayer chat (when in session)",
        "",
        "MULTIPLAYER:",
        "• Join sessions with other players",
        "• Real-time position updates",
        "• Chat system for communication",
        "• Shared world exploration",
        "",
        "COMBAT:",
        "• Magic attacks consume mana",
        "• Different aspects have different effects",
        "• XP gained from combat is dice-based",
        "• Enemy difficulty scales with book selection"
    ],

    "tips": [
        "TIPS FOR SUCCESS",
        "",
        "CHARACTER PROGRESSION:",
        "• Use Ctrl+C to check your character sheet regularly",
        "• Focus on leveling up in easier books first",
        "• Higher level books have stronger enemies and better rewards",
        "• Boss battles give massive XP and credit rewards",
        "",
        "RESOURCE MANAGEMENT:",
        "• Watch your mana - you can't fight without it!",
        "• Buy health and mana potions from shops",
        "• Rest areas fully restore HP/MP for a fee",
        "• Use Ctrl+I to quickly check your inventory",
        "",
        "MULTIPLAYER TIPS:",
        "• Use T to open chat and coordinate with other players",
        "• Chat input accepts all letters and symbols",
        "• Use ESC to logout cleanly from multiplayer sessions",
        "• Ctrl shortcuts work when chat is closed",
        "",
        "COMBAT STRATEGY:",
        "• Use potions during battle with H and M keys",
        "• Don't fight with low health or mana",
        "• Higher level enemies require better preparation",
        "• Fleeing from combat is sometimes wise"
    ]
}

LOAD_MESSAGE = """
    print("=" * 60)
    print("🎮 ENHANCED MAGITECH RPG ADVENTURE v2.0")
    print("=" * 60)
    print("Welcome to the enhanced Magitech RPG!")
    print("NEW FEATURES:")
    print("• 📚 Fixed book and chapter navigation")
    print("• 📋 Character sheet screen (C key)")
    print("• ⭐ Level system with max level 35")
    print("• 🎲 Dice-based XP system with level scaling")
    print("• 🎲 Dice-based loot system with level scaling")
    print("• 🏆 Scaled boss battles and enemy difficulty")
    print("• 🗺️ Enhanced world/chapter selection")
    print("• 💪 HP/MP scaling with character level")
    print("• 🌟 Automatic level-up system with benefits")
    print("• ⭐ Max level increased to 50!")
    print("=" * 60)
    print("CONTROLS:")
    print("• Arrow Keys - Move and navigate menus")
    print("• I - Open inventory during gameplay")
    print("• C - Open character sheet during gameplay")
    print("• B - Change world/chapter during gameplay")
    print("• H - Open help system")
    print("• M - Toggle background music")
    print("• ESC - Back/Quit")
    print("=" * 60)
    print("LEVELING SYSTEM:")
    print("• Gain XP from combat (dice-based)")
    print("• Each level increases max HP (+10 + Con bonus) and MP (+5 + Int/Wis bonus)")
    print("• Higher level enemies give more XP")
    print("• Boss battles scale with book difficulty")
    print("• Level cap: 50")
    print("• Equipment provides stat bonuses")
    print("=" * 60)
    print("STAT SYSTEM:")
    print("• Strength - Increases melee damage and carry capacity")
    print("• Dexterity - Improves AC, hit chance, and initiative")
    print("• Constitution - Boosts HP and fortitude")
    print("• Intelligence - Enhances spell power and mana")
    print("• Wisdom - Improves spell saves and mana")
    print("• Charisma - Affects social interactions and some spells")
    print("• Armor Class - Reduces incoming damage")
    print("=" * 60)
"""

# Create multiple sample book files with proper level scaling
sample_books = [
    {
        "file": "Books/1_fire_realm.json",
        "data": {
            "Title": "The Fire Realm Chronicles",
            "Chapter1": "The Burning Wastelands",
            "Chapter1_Level": 1,
            "Chapter1_Enemy_Type": "demon",
            "Chapter2": "The Molten Caverns",
            "Chapter2_Level": 3,
            "Chapter2_Enemy_Type": "fire_elemental",
            "Chapter3": "The Dragon's Lair",
            "Chapter3_Level": 5,
            "Chapter3_Enemy_Type": "dragon"
        }
    },
    {
        "file": "Books/3_ice_kingdom.json",
        "data": {
            "Title": "The Ice Kingdom Saga",
            "Chapter1": "The Frozen Tundra",
            "Chapter1_Level": 2,
            "Chapter1_Enemy_Type": "ice_troll",
            "Chapter2": "The Crystal Caves",
            "Chapter2_Level": 4,
            "Chapter2_Enemy_Type": "ice_golem",
            "Chapter3": "The Frost Giant's Fortress",
            "Chapter3_Level": 7,
            "Chapter3_Enemy_Type": "frost_giant"
        }
    },
    {
        "file": "Books/2_shadow_realm.json",
        "data": {
            "Title": "The Shadow Realm Mysteries",
            "Chapter1": "The Dark Forest",
            "Chapter1_Level": 3,
            "Chapter1_Enemy_Type": "shadow_beast",
            "Chapter2": "The Void Citadel",
            "Chapter2_Level": 6,
            "Chapter2_Enemy_Type": "void_wraith",
            "Chapter3": "The Nightmare's End",
            "Chapter3_Level": 10,
            "Chapter3_Enemy_Type": "nightmare_lord"
        }
    },
    {
        "file": "Books/4_ancient_ruins.json",
        "data": {
            "Title": "The Ancient Ruins Expedition",
            "Chapter1": "The Forgotten Temple",
            "Chapter1_Level": 8,
            "Chapter1_Enemy_Type": "ancient_guardian",
            "Chapter2": "The Cursed Catacombs",
            "Chapter2_Level": 12,
            "Chapter2_Enemy_Type": "undead_champion",
            "Chapter3": "The Elder God's Chamber",
            "Chapter3_Level": 15,
            "Chapter3_Enemy_Type": "elder_god"
        }
    },
    {
        "file": "Books/5_legendary_trials.json",
        "data": {
            "Title": "The Legendary Trials",
            "Chapter1": "Trial of Elements",
            "Chapter1_Level": 18,
            "Chapter1_Enemy_Type": "elemental_master",
            "Chapter2": "Trial of Champions",
            "Chapter2_Level": 22,
            "Chapter2_Enemy_Type": "legendary_warrior",
            "Chapter3": "The Final Ascension",
            "Chapter3_Level": 25,
            "Chapter3_Enemy_Type": "cosmic_entity"
        }
    }
]
