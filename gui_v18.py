import math
import sys

from fight import *
from loot import *
from new_character_form import *
import os


def roll_dice(num, sides):
    return [random.randint(1, sides) for _ in range(num)]


def gui_fight(player_name, player_aspect1, roll, demon_name, demon_hit_points,
              demon_aspect1, player_hit_points, mana_level, weapon_level, player_level, player_stats=None):
    """Enhanced combat function that includes all player stats"""
    # Get player stats for combat calculations
    stats = player_stats or {}
    strength = stats.get('strength', 10)
    dexterity = stats.get('dexterity', 10)
    constitution = stats.get('constitution', 10)
    intelligence = stats.get('intelligence', 10)
    wisdom = stats.get('wisdom', 10)
    charisma = stats.get('charisma', 10)
    armor_class = stats.get('armor_class', 10)

    # Calculate stat modifiers (D&D style: (stat - 10) // 2)
    str_mod = (strength - 10) // 2
    dex_mod = (dexterity - 10) // 2
    con_mod = (constitution - 10) // 2
    int_mod = (intelligence - 10) // 2
    wis_mod = (wisdom - 10) // 2
    cha_mod = (charisma - 10) // 2

    # Enhanced damage calculation with stats
    base_damage = random.randint(8, 20)  # Reduced base since we're adding stat bonuses

    # Weapon level bonus (existing)
    weapon_bonus = weapon_level * 3

    # Stat bonuses for combat
    strength_bonus = max(0, str_mod * 2)  # Strength increases physical damage
    magic_bonus = max(0, int_mod * 1.5)  # Intelligence increases magical damage
    level_bonus = player_level * 2  # Level scaling

    # Calculate total damage
    total_damage = int(base_damage + weapon_bonus + strength_bonus + magic_bonus + level_bonus)

    # Apply damage
    new_enemy_hp = max(0, demon_hit_points - total_damage)
    new_player_hp = player_hit_points

    # Mana cost with wisdom modifier (wisdom reduces mana cost)
    base_mana_cost = max(1, player_level // 2)
    mana_cost = max(1, base_mana_cost - max(0, wis_mod))
    new_mana = max(0, mana_level - mana_cost)

    # XP calculation with enhanced factors
    if new_enemy_hp <= 0:
        xp_dice = roll_dice(2, 6)  # Roll 2d6 for XP
        level_multiplier = max(1, demon_hit_points // 25)  # Higher HP enemies give more XP
        intelligence_bonus = max(0, int_mod)  # Intelligence gives XP bonus
        xp = (sum(xp_dice) * 5 * level_multiplier) + (intelligence_bonus * 5)
    else:
        xp = 0

    # Combat messages with stat information
    damage_breakdown = f"Base: {base_damage}, Weapon: {weapon_bonus}, Str: {strength_bonus}, Magic: {int_mod}, Level: {level_bonus * player_level // 2}"

    return (xp, new_enemy_hp, "fire", new_player_hp, new_mana,
            f"{player_name} attacks with enhanced power!",
            f"Deals {total_damage} damage! ({damage_breakdown})",
            f"Enemy has {new_enemy_hp} HP left",
            f"Gained {xp} XP! (Rolled {xp_dice if new_enemy_hp <= 0 else 'N/A'})")


def gui_enemy_fight(player_hit_points, roll, player_aspect1, player_name,
                    magic_type, demon_name, demon_hit_points, demon_aspect1, mana_level, player_stats=None):
    """Enhanced enemy combat function that considers player's armor class"""
    # Get player defensive stats
    stats = player_stats or {}
    armor_class = stats.get('armor_class', 10)
    constitution = stats.get('constitution', 10)
    dexterity = stats.get('dexterity', 10)

    # Calculate defensive modifiers
    con_mod = (constitution - 10) // 2
    dex_mod = (dexterity - 10) // 2

    # Enemy attack roll vs player AC
    enemy_attack_roll = random.randint(1, 20) + (demon_hit_points // 25)  # Enemy level bonus

    if enemy_attack_roll >= armor_class:
        # Hit! Calculate damage
        base_damage = random.randint(5, 15)
        enemy_level = max(1, demon_hit_points // 25)
        level_bonus = enemy_level * 2
        total_damage = base_damage + level_bonus

        # Constitution reduces damage taken
        damage_reduction = max(0, con_mod)
        final_damage = max(1, total_damage - damage_reduction)  # Minimum 1 damage

        new_player_hp = max(0, player_hit_points - final_damage)
        message = f"{demon_name} hits for {final_damage} damage! (AC: {armor_class}, Reduced by {damage_reduction})"
    else:
        # Miss!
        new_player_hp = player_hit_points
        final_damage = 0
        message = f"{demon_name} attacks but misses! (Rolled {enemy_attack_roll} vs AC {armor_class})"

    return (new_player_hp, mana_level, message)

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Magitech RPG Adventure")

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


# Game states
class GameState:
    OPENING = 0
    MAIN_MENU = 1
    BOOK_SELECTION = 2
    CHAPTER_SELECTION = 3
    CHARACTER_SELECTION = 4
    NEW_CHARACTER = 5
    MAGIC_SELECTION = 6
    WEAPON_SELECTION = 7
    GAME_BOARD = 8
    FIGHT = 9
    LOOT = 10
    HELP = 11
    STORE = 12
    REST = 13
    INVENTORY = 14
    WORLD_SELECT = 15  # New state for world selection in-game
    BOSS_VICTORY = 16  # New state for boss victory screen
    CHARACTER_SHEET = 17  # New state for character sheet


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
        "• I - Open inventory (anytime)",
        "• C - Open character sheet (anytime)",
        "• B - Change book/chapter (anytime)",
        "• M - Toggle background music",
        "• ESC - Quit game",
        "",
        "COMBAT:",
        "• SPACE - Attack enemy",
        "• H - Use health potion",
        "• M - Use mana potion",
        "• I - Open inventory",
        "• ESC - Flee from battle",
        "CHARACTER CREATION:",
        "• Type - Enter character name",
        "• R - Re-roll stats",
        "• TAB/↑↓ - Navigate options",
        "",
    ],

    "gameplay": [
        "GAMEPLAY MECHANICS",
        "",
        "CHARACTER SYSTEM:",
        "• Health Points (HP) - Your life force",
        "• Mana Points (MP) - Required for magic attacks",
        "• Experience Points (XP) - Gained by defeating enemies (dice roll)",
        "• Level - Increases stats and abilities (Max 25)",
        "• Credits - Currency for purchasing items",
        "",
        "LEVELING SYSTEM:",
        "• Gain XP from combat and exploration",
        "• Each level increases HP, MP, and combat effectiveness",
        "• Higher level characters can tackle tougher challenges",
        "• Boss enemies scale with book difficulty",
        "",
        "COMBAT:",
        "• Magic attacks consume mana",
        "• Different aspects have different effects",
        "• XP gained from combat is based on dice rolls",
        "• Enemy difficulty scales with book selection",
        "• Death results in respawn with penalties"
    ],

    "tips": [
        "TIPS FOR SUCCESS",
        "",
        "CHARACTER PROGRESSION:",
        "• Check your character sheet (C key) regularly",
        "• Focus on leveling up in easier books first",
        "• Higher level books have stronger enemies and better rewards",
        "• Boss battles give massive XP and credit rewards",
        "",
        "RESOURCE MANAGEMENT:",
        "• Watch your mana - you can't fight without it!",
        "• Buy health and mana potions from shops",
        "• Rest areas fully restore HP/MP for a fee",
        "• Collect loot before fighting all enemies",
        "",
        "COMBAT STRATEGY:",
        "• Use potions during battle with H and M keys",
        "• Don't fight with low health or mana",
        "• Higher level enemies require better preparation",
        "• Fleeing from combat is sometimes wise"
    ]
}


class StoreItem:
    def __init__(self, name, price, item_type, effect_value, description, stat_bonuses=None):
        self.name = name
        self.price = price
        self.item_type = item_type
        self.effect_value = effect_value
        self.description = description
        self.stat_bonuses = stat_bonuses or {}


class Store:
    def __init__(self):
        self.items = [
            StoreItem("Health Potion", 250, "health_potion", 25, "Restores 25 HP"),
            StoreItem("Greater Health Potion", 450, "health_potion", 50, "Restores 50 HP"),
            StoreItem("Mana Potion", 400, "mana_potion", 15, "Restores 15 MP"),
            StoreItem("Greater Mana Potion", 800, "mana_potion", 30, "Restores 30 MP"),
            StoreItem("Full Restore", 200, "full_restore", 0, "Fully restores HP and MP"),

            # Weapons with stat bonuses
            StoreItem("Enhanced Spell Blade", 1000, "weapon", 5, "+2 Str, +1 Dex, +5 Weapon Dmg",
                      {"strength": 2, "dexterity": 1}),
            StoreItem("Mystic Staff", 1350, "weapon", 3, "+3 Int, +1 Wis, +3 Magic Dmg",
                      {"intelligence": 3, "wisdom": 1}),
            StoreItem("Warrior's Sword", 1400, "weapon", 7, "+3 Str, +1 Con, +7 Weapon Dmg",
                      {"strength": 3, "constitution": 1}),
            StoreItem("Shadow Dagger", 1250, "weapon", 4, "+3 Dex, +1 Cha, +4 Weapon Dmg",
                      {"dexterity": 3, "charisma": 1}),
            StoreItem("Holy Mace", 1320, "weapon", 6, "+2 Wis, +1 Str, +1 Cha, +6 Weapon Dmg",
                      {"wisdom": 2, "strength": 1, "charisma": 1}),

            # Armor with stat bonuses and AC
            StoreItem("Mystic Armor", 2250, "armor", 5, "+2 Con, +1 Int, +5 AC",
                      {"constitution": 2, "intelligence": 1}),
            StoreItem("Plate Mail", 3500, "armor", 7, "+3 Con, +1 Str, +7 AC",
                      {"constitution": 3, "strength": 1}),
            StoreItem("Leather Armor", 1150, "armor", 3, "+2 Dex, +1 Con, +3 AC",
                      {"dexterity": 2, "constitution": 1}),
            StoreItem("Robes of Power", 1400, "armor", 2, "+2 Int, +2 Wis, +2 AC",
                      {"intelligence": 2, "wisdom": 2}),
            StoreItem("Cloak of Charisma", 1200, "armor", 1, "+3 Cha, +1 Dex, +1 AC",
                      {"charisma": 3, "dexterity": 1}),

            # Accessories with stat bonuses
            StoreItem("Ring of Strength", 1300, "accessory", 0, "+2 Strength",
                      {"strength": 2}),
            StoreItem("Amulet of Intelligence", 1300, "accessory", 0, "+2 Intelligence",
                      {"intelligence": 2}),
            StoreItem("Boots of Dexterity", 1250, "accessory", 0, "+2 Dexterity",
                      {"dexterity": 2}),
            StoreItem("Belt of Constitution", 1350, "accessory", 0, "+2 Constitution",
                      {"constitution": 2}),
            StoreItem("Crown of Wisdom", 1300, "accessory", 0, "+2 Wisdom",
                      {"wisdom": 2}),
            StoreItem("Pendant of Charisma", 1250, "accessory", 0, "+2 Charisma",
                      {"charisma": 2})
        ]
        self.selected_item = 0

    def get_affordable_items(self, credits):
        return [item for item in self.items if item.price <= credits]


class HealthManaBar:
    def __init__(self, x, y, width, height, max_value, current_value, bar_color, bg_color, label=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_value = max_value
        self.current_value = current_value
        self.bar_color = bar_color
        self.bg_color = bg_color
        self.label = label
        self.font = pygame.font.Font(None, 24)

    def update(self, current_value, max_value=None):
        self.current_value = max(0, current_value)
        if max_value is not None:
            self.max_value = max_value

    def draw(self, screen):
        # Draw background
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height))

        # Draw fill bar
        if self.max_value > 0:
            fill_ratio = max(0, min(1, self.current_value / self.max_value))  # Clamp between 0 and 1
            fill_width = int(fill_ratio * self.width)
            if fill_width > 0:
                pygame.draw.rect(screen, self.bar_color, (self.x, self.y, fill_width, self.height))

        # Draw border
        pygame.draw.rect(screen, UI_BORDER_COLOR, (self.x, self.y, self.width, self.height), 2)

        # Draw label text
        text = f"{self.label}: {int(self.current_value)}/{int(self.max_value)}"
        text_surface = self.font.render(text, True, WHITE)
        text_x = self.x + (self.width - text_surface.get_width()) // 2
        text_y = self.y + (self.height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))


class DamageText:
    def __init__(self, x, y, text, color=DAMAGE_TEXT_COLOR):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.timer = 60
        self.font = pygame.font.Font(None, 28)
        self.alpha = 255

    def update(self):
        self.timer -= 1
        self.y -= 2
        self.alpha = max(0, int(255 * (self.timer / 60)))
        return self.timer > 0

    def draw(self, screen):
        text_surface = self.font.render(self.text, True, self.color)
        text_surface.set_alpha(self.alpha)
        screen.blit(text_surface, (self.x, self.y))


class RestArea:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 60
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.rest_cost = 75

    def draw(self, screen):
        pygame.draw.rect(screen, (0, 100, 200), self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 3)

        tent_points = [
            (self.x + 30, self.y + 10),
            (self.x + 10, self.y + 50),
            (self.x + 50, self.y + 50)
        ]
        pygame.draw.polygon(screen, (150, 200, 255), tent_points)
        pygame.draw.polygon(screen, BLACK, tent_points, 2)

        rest_font = pygame.font.Font(None, 16)
        text = rest_font.render("REST", True, WHITE)
        text_rect = text.get_rect(center=(self.x + 30, self.y - 10))
        screen.blit(text, text_rect)


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def add_particle(self, x, y, color=(255, 255, 255)):
        self.particles.append({
            'x': x, 'y': y, 'vx': random.uniform(-2, 2), 'vy': random.uniform(-3, -1),
            'life': 30, 'color': color, 'size': random.randint(2, 4)
        })

    def update(self):
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            particle['size'] = max(1, particle['size'] - 0.1)
            if particle['life'] <= 0:
                self.particles.remove(particle)

    def draw(self, screen):
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / 30))
            color = (*particle['color'], alpha)
            pygame.draw.circle(screen, particle['color'],
                               (int(particle['x']), int(particle['y'])), int(particle['size']))


class CharacterCreator:
    def __init__(self):
        self.name = ""
        self.cursor_visible = True
        self.cursor_timer = 0
        self.selected_option = 0  # 0 = name, 1 = race, 2 = class, 3 = stats, 4 = create, 5 = back
        self.stats = self.roll_new_stats()
        self.max_name_length = 20

        # Race and class data
        self.races = {
            "Human": {
                "description": "Versatile and adaptable",
                "bonuses": {"strength": 1, "dexterity": 1, "constitution": 1, "intelligence": 1, "wisdom": 1,
                            "charisma": 1},
                "traits": ["Extra skill point", "Bonus feat", "Adaptable"]
            },
            "Elf": {
                "description": "Graceful and magical",
                "bonuses": {"dexterity": 2, "intelligence": 2, "constitution": -1},
                "traits": ["Low-light vision", "Magic resistance", "Keen senses"]
            },
            "Dwarf": {
                "description": "Hardy and resilient",
                "bonuses": {"constitution": 2, "strength": 1, "charisma": -1},
                "traits": ["Darkvision", "Poison resistance", "Magic resistance"]
            },
            "Halfling": {
                "description": "Small but brave",
                "bonuses": {"dexterity": 2, "charisma": 1, "strength": -1},
                "traits": ["Lucky", "Brave", "Small size bonus"]
            },
            "Orc": {
                "description": "Strong and fierce",
                "bonuses": {"strength": 2, "constitution": 1, "intelligence": -1, "charisma": -1},
                "traits": ["Darkvision", "Fierce", "Intimidating"]
            },
            "Tiefling": {
                "description": "Fiendish heritage",
                "bonuses": {"intelligence": 1, "charisma": 2, "wisdom": -1},
                "traits": ["Fire resistance", "Darkness spell", "Fiendish magic"]
            }
        }

        self.classes = {
            "War Mage": {
                "description": "Master of spell and sword",
                "primary_stats": ["Intelligence", "Strength"],
                "hp_bonus": 6,
                "mp_bonus": 8,
                "starting_equipment": ["Spell Blade", "Spell Pistol", "Spell Armor"],
                "magic_aspects": ["fire_level_1", "ice_level_1", "lightning_level_1"]
            },
            "Battle Cleric": {
                "description": "Divine warrior-priest",
                "primary_stats": ["Wisdom", "Strength"],
                "hp_bonus": 8,
                "mp_bonus": 6,
                "starting_equipment": ["Holy Mace", "Shield", "Plate Armor"],
                "magic_aspects": ["healing_level_1", "light_level_1", "protection_level_1"]
            },
            "Arcane Scholar": {
                "description": "Pure magical researcher",
                "primary_stats": ["Intelligence", "Wisdom"],
                "hp_bonus": 2,
                "mp_bonus": 12,
                "starting_equipment": ["Mystic Staff", "Robes", "Spell Focus"],
                "magic_aspects": ["arcane_level_1", "telekinesis_level_1", "illusion_level_1"]
            },
            "Shadow Rogue": {
                "description": "Stealthy spell-thief",
                "primary_stats": ["Dexterity", "Intelligence"],
                "hp_bonus": 4,
                "mp_bonus": 6,
                "starting_equipment": ["Shadow Daggers", "Leather Armor", "Thieves' Tools"],
                "magic_aspects": ["shadow_level_1", "stealth_level_1", "poison_level_1"]
            },
            "Elemental Knight": {
                "description": "Guardian of nature's power",
                "primary_stats": ["Strength", "Wisdom"],
                "hp_bonus": 10,
                "mp_bonus": 4,
                "starting_equipment": ["Elemental Sword", "Nature Armor", "Elemental Shield"],
                "magic_aspects": ["earth_level_1", "water_level_1", "air_level_1"]
            },
            "Technomancer": {
                "description": "Fusion of magic and technology",
                "primary_stats": ["Intelligence", "Dexterity"],
                "hp_bonus": 4,
                "mp_bonus": 10,
                "starting_equipment": ["Mana Rifle", "Tech Armor", "Gadgets"],
                "magic_aspects": ["tech_level_1", "energy_level_1", "construct_level_1"]
            }
        }

        self.selected_race = "Human"
        self.selected_class = "War Mage"

    def roll_new_stats(self):
        """Roll new random stats for character"""
        stats = {}
        stat_names = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]

        for stat in stat_names:
            # Roll 3d6+3 for each stat (6-21 range, average ~13.5)
            rolls = roll_dice(3, 6)
            stats[stat] = sum(rolls) + 3

        return stats

    def get_stat_modifier(self, stat_value):
        """Get D&D style stat modifier"""
        return (stat_value - 10) // 2

    def get_total_stats(self):
        """Get stats including racial bonuses"""
        total_stats = self.stats.copy()
        race_bonuses = self.races[self.selected_race]["bonuses"]

        for stat, bonus in race_bonuses.items():
            total_stats[stat] += bonus

        return total_stats

    def calculate_derived_stats(self):
        """Calculate HP, MP, and AC based on rolled stats, race, and class"""
        total_stats = self.get_total_stats()

        # Base stats
        base_hp = 100
        base_mp = 50
        base_ac = 10

        # Stat bonuses
        con_bonus = max(0, self.get_stat_modifier(total_stats["constitution"]) * 3)
        int_bonus = max(0, self.get_stat_modifier(total_stats["intelligence"]) * 2)
        wis_bonus = max(0, self.get_stat_modifier(total_stats["wisdom"]) * 1)
        dex_bonus = max(0, self.get_stat_modifier(total_stats["dexterity"]))

        # Class bonuses
        class_data = self.classes[self.selected_class]
        hp_class_bonus = class_data["hp_bonus"]
        mp_class_bonus = class_data["mp_bonus"]

        total_hp = base_hp + con_bonus + hp_class_bonus
        total_mp = base_mp + int_bonus + wis_bonus + mp_class_bonus
        total_ac = base_ac + dex_bonus

        return total_hp, total_mp, total_ac


class GameManager:
    def __init__(self):
        self.current_state = GameState.OPENING
        self.selected_option = 0
        self.selected_book_option = 0
        self.selected_chapter_option = 0
        self.selected_magic_option = 0
        self.selected_weapon_option = 0
        self.help_section = 0  # For help navigation
        self.world_select_panel = 0  # 0 = books, 1 = chapters

        # Game data
        self.loaded_player_attr = {}
        self.loaded_enemy_attr = {}
        self.loaded_book_attr = {}
        self.player_file = ""
        self.enemy_file_path = ""
        self.original_magic_key = "Aspect1"
        self.current_book_name = ""
        self.current_chapter_name = ""
        self.current_book_level = 1
        self.character_creator = CharacterCreator()

        # Game world
        self.player_pos = [WIDTH // 2, HEIGHT // 2]
        self.player_speed = 3
        self.player_size = 25
        self.last_interaction_pos = None  # Track last interaction position

        # Visual effects
        self.particles = ParticleSystem()
        self.menu_animation_timer = 0

        # Combat
        self.damage_texts = []
        self.combat_messages = []
        self.action_triggered = False
        self.loot_triggered = False
        self.boss_fight_triggered = False

        # Store and Rest
        self.store = Store()
        self.store_positions = []
        self.rest_areas = []
        self.selected_store_item = 0
        self.selected_inventory_item = 0
        self.rest_message = ""
        self.rest_timer = 0
        self.previous_state = GameState.GAME_BOARD
        self.store_scroll_offset = 0
        self.items_per_page = 8  # Number of items visible at once

        # Boss victory tracking
        self.boss_victory_message = ""
        self.boss_xp_gained = 0
        self.boss_credits_gained = 0

        # Load assets and setup
        self.load_assets()

    def get_all_player_stats(self):
        """Get all player stats for combat including armor class"""
        if not self.loaded_player_attr:
            return {}

        return {
            'strength': self.get_total_stat('strength'),
            'dexterity': self.get_total_stat('dexterity'),
            'constitution': self.get_total_stat('constitution'),
            'intelligence': self.get_total_stat('intelligence'),
            'wisdom': self.get_total_stat('wisdom'),
            'charisma': self.get_total_stat('charisma'),
            'armor_class': self.get_armor_class()
        }

    def get_equipment_stat_bonus(self, stat_name):
        """Calculate stat bonus from equipped items"""
        if not self.loaded_player_attr:
            return 0

        total_bonus = 0
        inventory = self.loaded_player_attr.get("Inventory", {})

        # Check equipped items for stat bonuses
        equipped_items = [
            self.loaded_player_attr.get("Weapon1", ""),
            self.loaded_player_attr.get("Weapon2", ""),
            self.loaded_player_attr.get("Weapon3", ""),
            self.loaded_player_attr.get("Armor_Slot_1", ""),
            self.loaded_player_attr.get("Armor_Slot_2", "")
        ]

        # Define equipment stat bonuses
        equipment_bonuses = {
            # Weapons
            "Enhanced Spell Blade": {"strength": 2, "dexterity": 1},
            "Mystic Staff": {"intelligence": 3, "wisdom": 1},
            "Warrior's Sword": {"strength": 3, "constitution": 1},
            "Shadow Dagger": {"dexterity": 3, "charisma": 1},
            "Holy Mace": {"wisdom": 2, "strength": 1, "charisma": 1},

            # Armor
            "Mystic Armor": {"constitution": 2, "intelligence": 1},
            "Plate Mail": {"constitution": 3, "strength": 1},
            "Leather Armor": {"dexterity": 2, "constitution": 1},
            "Robes of Power": {"intelligence": 2, "wisdom": 2},
            "Cloak of Charisma": {"charisma": 3, "dexterity": 1},

            # Accessories (provide bonuses when in inventory)
            "Ring of Strength": {"strength": 2},
            "Amulet of Intelligence": {"intelligence": 2},
            "Boots of Dexterity": {"dexterity": 2},
            "Belt of Constitution": {"constitution": 2},
            "Crown of Wisdom": {"wisdom": 2},
            "Pendant of Charisma": {"charisma": 2}
        }

        # Check equipped items
        for item in equipped_items:
            if item and item in equipment_bonuses:
                bonus = equipment_bonuses[item].get(stat_name.lower(), 0)
                total_bonus += bonus

        # Check inventory for accessories that provide bonuses when owned
        for item_name, quantity in inventory.items():
            if quantity > 0 and item_name in equipment_bonuses:
                # Accessories provide bonuses just by being in inventory (worn)
                if item_name.startswith(("Ring", "Amulet", "Boots", "Belt", "Crown", "Pendant")):
                    bonus = equipment_bonuses[item_name].get(stat_name.lower(), 0)
                    total_bonus += bonus

        return total_bonus

    def draw_enhanced_character_creation(self):
        """Draw the enhanced character creation screen with race and class selection"""
        screen.fill(MENU_BG)

        # Update cursor blinking
        self.character_creator.cursor_timer += 1
        if self.character_creator.cursor_timer >= 30:
            self.character_creator.cursor_visible = not self.character_creator.cursor_visible
            self.character_creator.cursor_timer = 0

        # Header
        header_rect = pygame.Rect(0, 15, WIDTH, 70)
        self.draw_gradient_rect(screen, MENU_ACCENT, MENU_HIGHLIGHT, header_rect)

        title = large_font.render("✨ CREATE NEW CHARACTER ✨", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title, title_rect)

        # Main content area - split into left and right panels
        left_panel = pygame.Rect(20, 100, 380, 420)
        right_panel = pygame.Rect(420, 100, 360, 420)

        # Left panel - Character creation options
        self.draw_gradient_rect(screen, (40, 60, 100), (20, 30, 50), left_panel)
        pygame.draw.rect(screen, MENU_SELECTED if self.character_creator.selected_option <= 3 else MENU_TEXT,
                         left_panel, 2)

        left_y = 110

        # 1. Character name section
        name_title = font.render("🏷️ CHARACTER NAME:", True, MENU_SELECTED)
        screen.blit(name_title, (30, left_y))
        left_y += 25

        name_box = pygame.Rect(30, left_y, 360, 30)
        box_color = MENU_HIGHLIGHT if self.character_creator.selected_option == 0 else (60, 60, 80)
        border_color = MENU_SELECTED if self.character_creator.selected_option == 0 else MENU_TEXT

        pygame.draw.rect(screen, box_color, name_box)
        pygame.draw.rect(screen, border_color, name_box, 2)

        display_name = self.character_creator.name if self.character_creator.name else "Enter name..."
        name_color = WHITE if self.character_creator.name else GRAY

        if self.character_creator.selected_option == 0 and self.character_creator.cursor_visible and self.character_creator.name:
            display_name += "|"
        elif self.character_creator.selected_option == 0 and self.character_creator.cursor_visible and not self.character_creator.name:
            display_name = "|"

        name_surface = small_font.render(display_name, True, name_color)
        screen.blit(name_surface, (name_box.x + 8, name_box.y + 8))
        left_y += 45

        # 2. Race selection
        race_title = font.render("🧬 RACE:", True, MENU_SELECTED)
        screen.blit(race_title, (30, left_y))
        left_y += 25

        race_box = pygame.Rect(30, left_y, 360, 30)
        race_color = MENU_HIGHLIGHT if self.character_creator.selected_option == 1 else (60, 60, 80)
        race_border = MENU_SELECTED if self.character_creator.selected_option == 1 else MENU_TEXT

        pygame.draw.rect(screen, race_color, race_box)
        pygame.draw.rect(screen, race_border, race_box, 2)

        race_text = small_font.render(f"◄ {self.character_creator.selected_race} ►", True, WHITE)
        race_rect = race_text.get_rect(center=race_box.center)
        screen.blit(race_text, race_rect)
        left_y += 35

        # Race description
        race_desc = self.character_creator.races[self.character_creator.selected_race]["description"]
        desc_text = small_font.render(race_desc, True, LIGHT_BLUE)
        screen.blit(desc_text, (35, left_y))
        left_y += 25

        # 3. Class selection
        class_title = font.render("🎭 CLASS:", True, MENU_SELECTED)
        screen.blit(class_title, (30, left_y))
        left_y += 25

        class_box = pygame.Rect(30, left_y, 360, 30)
        class_color = MENU_HIGHLIGHT if self.character_creator.selected_option == 2 else (60, 60, 80)
        class_border = MENU_SELECTED if self.character_creator.selected_option == 2 else MENU_TEXT

        pygame.draw.rect(screen, class_color, class_box)
        pygame.draw.rect(screen, class_border, class_box, 2)

        class_text = small_font.render(f"◄ {self.character_creator.selected_class} ►", True, WHITE)
        class_rect = class_text.get_rect(center=class_box.center)
        screen.blit(class_text, class_rect)
        left_y += 35

        # Class description
        class_desc = self.character_creator.classes[self.character_creator.selected_class]["description"]
        desc_text = small_font.render(class_desc, True, LIGHT_BLUE)
        screen.blit(desc_text, (35, left_y))
        left_y += 25

        # 4. Stats section
        stats_title = font.render("🎲 CHARACTER STATS:", True, MENU_SELECTED)
        screen.blit(stats_title, (30, left_y))
        left_y += 25

        # Re-roll button
        reroll_box = pygame.Rect(30, left_y, 180, 30)
        reroll_color = MENU_HIGHLIGHT if self.character_creator.selected_option == 3 else (60, 60, 80)
        reroll_border = MENU_SELECTED if self.character_creator.selected_option == 3 else MENU_TEXT

        pygame.draw.rect(screen, reroll_color, reroll_box)
        pygame.draw.rect(screen, reroll_border, reroll_box, 2)

        reroll_text = small_font.render("🎲 RE-ROLL STATS (R)", True, WHITE)
        reroll_rect = reroll_text.get_rect(center=reroll_box.center)
        screen.blit(reroll_text, reroll_rect)
        left_y += 40

        # Display current stats with racial bonuses
        stat_names = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
        total_stats = self.character_creator.get_total_stats()
        race_bonuses = self.character_creator.races[self.character_creator.selected_race]["bonuses"]

        for i, stat_name in enumerate(stat_names):
            stat_key = stat_name.lower()
            base_value = self.character_creator.stats[stat_key]
            total_value = total_stats[stat_key]
            racial_bonus = race_bonuses.get(stat_key, 0)
            modifier = self.character_creator.get_stat_modifier(total_value)

            # Color coding based on total stat quality
            if total_value >= 16:
                stat_color = GREEN  # Excellent
            elif total_value >= 14:
                stat_color = LIGHT_BLUE  # Good
            elif total_value >= 12:
                stat_color = WHITE  # Average
            else:
                stat_color = ORANGE  # Below average

            # Format stat display
            if racial_bonus != 0:
                bonus_text = f" ({base_value}{racial_bonus:+d})"
                modifier_text = f" [{modifier:+d}]"
            else:
                bonus_text = ""
                modifier_text = f" [{modifier:+d}]"

            stat_text = small_font.render(f"{stat_name[:3].upper()}: {total_value}{bonus_text}{modifier_text}", True,
                                          stat_color)
            screen.blit(stat_text, (35 + (i % 2) * 170, left_y + (i // 2) * 20))

        # Right panel - Character preview
        self.draw_gradient_rect(screen, (60, 40, 80), (30, 20, 40), right_panel)
        pygame.draw.rect(screen, MENU_TEXT, right_panel, 2)

        # Character preview
        preview_y = 110
        preview_title = font.render("👤 CHARACTER PREVIEW", True, MENU_SELECTED)
        screen.blit(preview_title, (430, preview_y))
        preview_y += 30

        # Basic info
        char_info = [
            f"📛 Name: {self.character_creator.name if self.character_creator.name else 'Unnamed'}",
            f"🧬 Race: {self.character_creator.selected_race}",
            f"🎭 Class: {self.character_creator.selected_class}",
            f"⭐ Level: 1"
        ]

        for info in char_info:
            info_text = small_font.render(info, True, WHITE)
            screen.blit(info_text, (430, preview_y))
            preview_y += 18
        preview_y += 10

        # Derived stats
        derived_title = small_font.render("📊 DERIVED STATS:", True, MENU_SELECTED)
        screen.blit(derived_title, (430, preview_y))
        preview_y += 20

        hp, mp, ac = self.character_creator.calculate_derived_stats()

        derived_stats = [
            f"❤️ Health Points: {hp}",
            f"🔮 Mana Points: {mp}",
            f"🛡️ Armor Class: {ac}",
            f"💰 Starting Credits: 2000"
        ]

        for stat in derived_stats:
            stat_text = small_font.render(stat, True, WHITE)
            screen.blit(stat_text, (430, preview_y))
            preview_y += 18
        preview_y += 10

        # Racial traits
        traits_title = small_font.render("🌟 RACIAL TRAITS:", True, MENU_SELECTED)
        screen.blit(traits_title, (430, preview_y))
        preview_y += 20

        race_traits = self.character_creator.races[self.character_creator.selected_race]["traits"]
        for trait in race_traits[:3]:  # Show first 3 traits
            trait_text = small_font.render(f"• {trait}", True, LIGHT_BLUE)
            screen.blit(trait_text, (430, preview_y))
            preview_y += 16
        preview_y += 10

        # Starting equipment
        equipment_title = small_font.render("⚔️ STARTING EQUIPMENT:", True, MENU_SELECTED)
        screen.blit(equipment_title, (430, preview_y))
        preview_y += 20

        class_equipment = self.character_creator.classes[self.character_creator.selected_class]["starting_equipment"]
        for equipment in class_equipment:
            equipment_text = small_font.render(f"• {equipment}", True, WHITE)
            screen.blit(equipment_text, (430, preview_y))
            preview_y += 16

        # Action buttons
        button_y = HEIGHT - 100

        # Create character button
        create_box = pygame.Rect(50, button_y, 200, 35)
        create_color = MENU_HIGHLIGHT if self.character_creator.selected_option == 4 else (60, 60, 80)
        create_border = MENU_SELECTED if self.character_creator.selected_option == 4 else MENU_TEXT
        create_enabled = len(self.character_creator.name.strip()) > 0

        if not create_enabled:
            create_color = (40, 40, 40)
            create_border = GRAY

        pygame.draw.rect(screen, create_color, create_box)
        pygame.draw.rect(screen, create_border, create_box, 2)

        create_text_color = WHITE if create_enabled else GRAY
        create_text = font.render("✅ CREATE CHARACTER", True, create_text_color)
        create_rect = create_text.get_rect(center=create_box.center)
        screen.blit(create_text, create_rect)

        # Back button
        back_box = pygame.Rect(280, button_y, 120, 35)
        back_color = MENU_HIGHLIGHT if self.character_creator.selected_option == 5 else (60, 60, 80)
        back_border = MENU_SELECTED if self.character_creator.selected_option == 5 else MENU_TEXT

        pygame.draw.rect(screen, back_color, back_box)
        pygame.draw.rect(screen, back_border, back_box, 2)

        back_text = font.render("🔙 BACK", True, WHITE)
        back_rect = back_text.get_rect(center=back_box.center)
        screen.blit(back_text, back_rect)

        # Instructions
        instruction_bg = pygame.Rect(0, HEIGHT - 50, WIDTH, 50)
        pygame.draw.rect(screen, MENU_ACCENT, instruction_bg)

        instructions = [
            "TAB/↑↓ Navigate  •  ←→ Change Race/Class  •  Type Name  •  R Re-roll  •  ENTER Confirm  •  ESC Back",
            "💡 Race bonuses affect stats, Class affects HP/MP and equipment"
        ]

        for i, instruction in enumerate(instructions):
            instruction_font = small_font if i == 1 else small_font
            instruction_color = MENU_TEXT if i == 1 else WHITE
            text = instruction_font.render(instruction, True, instruction_color)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT - 35 + i * 15))
            screen.blit(text, text_rect)

    def create_character_from_creator(self):
        """Create character data from character creator"""
        if not self.character_creator.name.strip():
            return None

        # Calculate derived stats
        hp, mp, ac = self.character_creator.calculate_derived_stats()
        total_stats = self.character_creator.get_total_stats()

        # Get class-specific data
        class_data = self.character_creator.classes[self.character_creator.selected_class]
        magic_aspects = class_data["magic_aspects"]

        new_char = {
            "Name": self.character_creator.name.strip(),
            "Race": self.character_creator.selected_race,
            "Type": self.character_creator.selected_class,
            "Aspect1": magic_aspects[0] if magic_aspects else "fire_level_1",
            "Aspect2": magic_aspects[1] if len(magic_aspects) > 1 else "",
            "Aspect3": magic_aspects[2] if len(magic_aspects) > 2 else "",
            "Aspect1_Mana": mp,
            "Aspect2_Mana": mp // 2 if len(magic_aspects) > 1 else 0,
            "Aspect3_Mana": mp // 3 if len(magic_aspects) > 2 else 0,
            "Weapon1": "Spell Pistol",  # Default, will be updated based on class
            "Weapon2": "Hands",
            "Weapon3": "Spell_Blade",  # Default, will be updated based on class
            "Armor_Slot_1": "Spell_Armor",  # Default, will be updated based on class
            "Armor_Slot_2": "",
            "Level": 1,
            "Hit_Points": hp,
            "Experience_Points": 0,
            "Credits": 2000,
            "Inventory": {},
            # Use the total stats (base + racial bonuses)
            "strength": total_stats["strength"],
            "dexterity": total_stats["dexterity"],
            "constitution": total_stats["constitution"],
            "intelligence": total_stats["intelligence"],
            "wisdom": total_stats["wisdom"],
            "charisma": total_stats["charisma"]
        }

        return new_char

    def load_assets(self):
        """Load all game assets"""
        try:
            self.character_image = pygame.image.load('Images/war_mage.png').convert_alpha()
            self.character_image = pygame.transform.scale(self.character_image, (20, 30))
        except:
            self.character_image = pygame.Surface((20, 30))
            self.character_image.fill(BLUE)

        try:
            self.target_image = pygame.image.load('Images/target.png')
            self.target_image = pygame.transform.scale(self.target_image, (30, 30))
        except:
            self.target_image = pygame.Surface((30, 30))
            self.target_image.fill(RED)

        try:
            self.inactive_image = pygame.image.load('Images/download.jpeg')
            self.inactive_image = pygame.transform.scale(self.inactive_image, (30, 30))
        except:
            self.inactive_image = pygame.Surface((30, 30))
            self.inactive_image.fill(GRAY)

        try:
            pygame.mixer.init()
            pygame.mixer.music.load("Sounds/Apoxode_-_Electric_1.mp3")
            pygame.mixer.music.set_volume(0.2)
            self.music_available = True
        except:
            self.music_available = False

        self.music_playing = False

    def get_player_level(self):
        """Calculate player level from XP"""
        if not self.loaded_player_attr:
            return 1

        xp = self.loaded_player_attr.get("Experience_Points", 0)
        # XP required for each level: level * 150 (increased for level 35 cap)
        level = min(50, max(1, int(xp // 150) + 1))
        return level

    def get_max_hp_for_level(self, level):
        """Get max HP based on level and constitution"""
        base_hp = 100
        level_bonus = (level - 1) * 10
        constitution = self.get_total_stat("constitution")
        constitution_bonus = max(0, (constitution - 10) // 2) * 3  # +3 HP per constitution modifier
        return base_hp + level_bonus + constitution_bonus

    def get_max_mana_for_level(self, level):
        """Get max mana based on level and intelligence/wisdom"""
        base_mana = 50
        level_bonus = (level - 1) * 5
        intelligence = self.get_total_stat("intelligence")
        wisdom = self.get_total_stat("wisdom")
        int_bonus = max(0, (intelligence - 10) // 2) * 2  # +2 MP per intelligence modifier
        wis_bonus = max(0, (wisdom - 10) // 2) * 1  # +1 MP per wisdom modifier
        return base_mana + level_bonus + int_bonus + wis_bonus

    def get_base_stat(self, stat_name):
        """Get base stat value before equipment bonuses"""
        if not self.loaded_player_attr:
            return 10
        return self.loaded_player_attr.get(stat_name.lower(), 10)

    def get_equipment_stat_bonus(self, stat_name):
        """Calculate stat bonus from equipped items"""
        if not self.loaded_player_attr:
            return 0

        total_bonus = 0
        inventory = self.loaded_player_attr.get("Inventory", {})

        # Check equipped items for stat bonuses
        equipped_items = [
            self.loaded_player_attr.get("Weapon1", ""),
            self.loaded_player_attr.get("Weapon2", ""),
            self.loaded_player_attr.get("Weapon3", ""),
            self.loaded_player_attr.get("Armor_Slot_1", ""),
            self.loaded_player_attr.get("Armor_Slot_2", "")
        ]

        # Define equipment stat bonuses
        equipment_bonuses = {
            # Weapons
            "Enhanced Spell Blade": {"strength": 2, "dexterity": 1},
            "Mystic Staff": {"intelligence": 3, "wisdom": 1},
            "Warrior's Sword": {"strength": 3, "constitution": 1},
            "Shadow Dagger": {"dexterity": 3, "charisma": 1},
            "Holy Mace": {"wisdom": 2, "strength": 1, "charisma": 1},

            # Armor
            "Mystic Armor": {"constitution": 2, "intelligence": 1},
            "Plate Mail": {"constitution": 3, "strength": 1},
            "Leather Armor": {"dexterity": 2, "constitution": 1},
            "Robes of Power": {"intelligence": 2, "wisdom": 2},
            "Cloak of Charisma": {"charisma": 3, "dexterity": 1},

            # Special items
            "Ring of Strength": {"strength": 2},
            "Amulet of Intelligence": {"intelligence": 2},
            "Boots of Dexterity": {"dexterity": 2},
            "Belt of Constitution": {"constitution": 2},
            "Crown of Wisdom": {"wisdom": 2},
            "Pendant of Charisma": {"charisma": 2}
        }

        for item in equipped_items:
            if item and item in equipment_bonuses:
                bonus = equipment_bonuses[item].get(stat_name.lower(), 0)
                total_bonus += bonus

        return total_bonus

    def get_total_stat(self, stat_name):
        """Get total stat value including equipment bonuses"""
        base = self.get_base_stat(stat_name)
        equipment_bonus = self.get_equipment_stat_bonus(stat_name)
        return base + equipment_bonus

    def get_armor_class(self):
        """Calculate armor class from dexterity and equipment"""
        if not self.loaded_player_attr:
            return 10

        base_ac = 10
        dexterity = self.get_total_stat("dexterity")
        dex_bonus = max(0, (dexterity - 10) // 2)

        # Armor bonuses
        armor_bonuses = {
            "Mystic Armor": 5,
            "Plate Mail": 7,
            "Leather Armor": 3,
            "Robes of Power": 2,
            "Cloak of Charisma": 1
        }

        armor_bonus = 0
        equipped_armor = [
            self.loaded_player_attr.get("Armor_Slot_1", ""),
            self.loaded_player_attr.get("Armor_Slot_2", "")
        ]

        for armor in equipped_armor:
            if armor in armor_bonuses:
                armor_bonus = max(armor_bonus, armor_bonuses[armor])  # Take highest armor bonus

        return base_ac + dex_bonus + armor_bonus

    def initialize_character_stats(self, character_data):
        """Initialize character stats if they don't exist"""
        default_stats = {
            "strength": 12,
            "dexterity": 12,
            "constitution": 14,
            "intelligence": 13,
            "wisdom": 11,
            "charisma": 10
        }

        for stat, value in default_stats.items():
            if stat not in character_data:
                character_data[stat] = value

        return character_data

    def level_up_check(self):
        """Check if player should level up and apply benefits"""
        if not self.loaded_player_attr:
            return False

        current_level = self.loaded_player_attr.get("Level", 1)
        calculated_level = self.get_player_level()

        if calculated_level > current_level and calculated_level <= 50:
            # Level up!
            self.loaded_player_attr["Level"] = calculated_level

            # Increase max HP and mana
            new_max_hp = self.get_max_hp_for_level(calculated_level)
            new_max_mana = self.get_max_mana_for_level(calculated_level)

            # Restore some HP/Mana on level up
            current_hp = self.loaded_player_attr.get("Hit_Points", 100)
            current_mana = self.loaded_player_attr.get(f"{self.original_magic_key}_Mana", 50)

            self.loaded_player_attr["Hit_Points"] = min(new_max_hp, current_hp + 25)
            self.loaded_player_attr[f"{self.original_magic_key}_Mana"] = min(new_max_mana, current_mana + 10)

            # Add level up visual effect
            self.damage_texts.append(DamageText(self.player_pos[0], self.player_pos[1],
                                                f"LEVEL UP! Level {calculated_level}!", GOLD))

            # Save character
            if self.player_file:
                with open(self.player_file, 'w') as f:
                    json.dump(self.loaded_player_attr, f, indent=4)

            return True
        return False

    def setup_world(self, chapter_info=None):
        """Setup game world elements based on chapter"""
        # Adjust difficulty based on chapter and book level
        if chapter_info and "Level" in chapter_info:
            self.current_book_level = chapter_info.get("Level", 1)
            base_enemies = max(3, min(8, self.current_book_level + 2))
            base_loot = max(2, min(6, self.current_book_level))
        else:
            self.current_book_level = 1
            base_enemies = 4
            base_loot = 3

        loot_dice = roll_dice(1, 4)
        enemy_dice = roll_dice(1, 4)
        self.num_loot = base_loot + loot_dice[0]
        self.num_enemies = base_enemies + enemy_dice[0]

        self.loot_positions = self.generate_random_positions(self.num_loot)
        self.enemy_positions = self.generate_random_positions(self.num_enemies)
        self.boss_positions = []

        # Position stores and rest areas away from center spawn
        self.store_positions = [{"pos": (WIDTH - 80, 50), "active": True}]
        self.rest_areas = [RestArea(WIDTH - 80, HEIGHT - 80)]  # Moved to bottom right

        # Load chapter-specific background if available
        try:
            if chapter_info and "background" in chapter_info:
                bg_file = f"Images/{chapter_info['background']}"
                self.background_image = pygame.image.load(bg_file)
                self.background_image = pygame.transform.scale(self.background_image, (WIDTH, HEIGHT))
            else:
                self.background_image = pygame.image.load('Images/book_1_chapter_1_map.png')
                self.background_image = pygame.transform.scale(self.background_image, (WIDTH, HEIGHT))
        except:
            self.background_image = self.create_gradient_background()

    def create_gradient_background(self):
        """Create a nice gradient background"""
        background = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            color_value = int(30 + (y / HEIGHT) * 40)
            color = (color_value, color_value + 10, color_value + 20)
            pygame.draw.line(background, color, (0, y), (WIDTH, y))
        return background

    def generate_random_positions(self, num_items):
        """Generate random positions for items, avoiding spawn area"""
        positions = []
        spawn_area = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 200)

        for _ in range(num_items):
            attempts = 0
            while attempts < 50:  # Prevent infinite loop
                pos = (random.randint(50, WIDTH - 80), random.randint(50, HEIGHT - 80))
                if not spawn_area.collidepoint(pos):
                    positions.append({"pos": pos, "active": True})
                    break
                attempts += 1

        return positions

    def move_player_away_from_interaction(self):
        """Move player away from last interaction point"""
        if self.last_interaction_pos:
            # Calculate direction away from interaction point
            dx = self.player_pos[0] - self.last_interaction_pos[0]
            dy = self.player_pos[1] - self.last_interaction_pos[1]

            # Normalize and move player away
            distance = (dx ** 2 + dy ** 2) ** 0.5
            if distance > 0:
                move_distance = 70  # Move player 70 pixels away
                self.player_pos[0] += int((dx / distance) * move_distance)
                self.player_pos[1] += int((dy / distance) * move_distance)

                # Keep player in bounds
                self.player_pos[0] = max(25, min(WIDTH - 25, self.player_pos[0]))
                self.player_pos[1] = max(25, min(HEIGHT - 25, self.player_pos[1]))

    def draw_gradient_rect(self, surface, color1, color2, rect):
        """Draw a rectangle with gradient"""
        for y in range(rect.height):
            ratio = y / rect.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surface, (r, g, b),
                             (rect.x, rect.y + y), (rect.x + rect.width, rect.y + y))

    def draw_enhanced_opening(self):
        """Draw enhanced opening screen with animations"""
        self.menu_animation_timer += 1

        # Animated background
        screen.fill(MENU_BG)

        # Add some animated particles
        if self.menu_animation_timer % 10 == 0:
            self.particles.add_particle(random.randint(0, WIDTH), random.randint(0, HEIGHT),
                                        (100, 150, 255))

        self.particles.update()
        self.particles.draw(screen)

        # Main title with glow effect
        glow_offset = int(5 * abs(pygame.math.Vector2(1, 0).rotate(self.menu_animation_timer * 2).x))

        # Glow effect
        for offset in range(3, 0, -1):
            glow_color = (50, 100, 150)
            title_glow = title_font.render("MAGITECH RPG", True, glow_color)
            for dx in range(-offset, offset + 1):
                for dy in range(-offset, offset + 1):
                    if dx * dx + dy * dy <= offset * offset:
                        screen.blit(title_glow, (WIDTH // 2 - title_glow.get_width() // 2 + dx,
                                                 100 + dy))

        # Main title
        title_surface = title_font.render("MAGITECH RPG", True, MENU_SELECTED)
        title_rect = title_surface.get_rect(center=(WIDTH // 2, 100))
        screen.blit(title_surface, title_rect)

        # Subtitle
        subtitle_surface = subtitle_font.render("Where Magic Meets Technology", True, MENU_TEXT)
        subtitle_rect = subtitle_surface.get_rect(center=(WIDTH // 2, 150))
        screen.blit(subtitle_surface, subtitle_rect)

        # Animated prompt
        alpha = int(128 + 127 * math.sin(self.menu_animation_timer * 0.1))
        prompt_color = (*MENU_SELECTED[:3], alpha)

        # Create surface with per-pixel alpha
        prompt_surface = font.render("Press any key to begin your adventure...", True, MENU_SELECTED)
        prompt_surface.set_alpha(alpha)
        prompt_rect = prompt_surface.get_rect(center=(WIDTH // 2, HEIGHT - 150))
        screen.blit(prompt_surface, prompt_rect)

        # Help prompt
        help_text = small_font.render("Press H for Help", True, MENU_TEXT)
        help_rect = help_text.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        screen.blit(help_text, help_rect)

    def draw_enhanced_menu(self, title, options, selected_index, subtitle=""):
        """Draw enhanced menu with better visuals"""
        screen.fill(MENU_BG)

        # Update particles
        if self.menu_animation_timer % 15 == 0:
            self.particles.add_particle(random.randint(0, WIDTH), HEIGHT, (100, 150, 200))
        self.particles.update()
        self.particles.draw(screen)

        # Title background
        title_bg = pygame.Rect(0, 50, WIDTH, 100)
        self.draw_gradient_rect(screen, MENU_ACCENT, MENU_HIGHLIGHT, title_bg)

        # Title
        title_surface = large_font.render(title, True, WHITE)
        title_rect = title_surface.get_rect(center=(WIDTH // 2, 100))
        screen.blit(title_surface, title_rect)

        # Subtitle
        if subtitle:
            subtitle_surface = font.render(subtitle, True, MENU_TEXT)
            subtitle_rect = subtitle_surface.get_rect(center=(WIDTH // 2, 130))
            screen.blit(subtitle_surface, subtitle_rect)

        # Menu options
        start_y = 200
        option_height = 50

        for i, option in enumerate(options):
            y_pos = start_y + i * option_height

            # Option background
            option_rect = pygame.Rect(WIDTH // 4, y_pos - 15, WIDTH // 2, 40)

            if i == selected_index:
                # Animated selection
                pulse = int(10 * abs(math.sin(self.menu_animation_timer * 0.15)))
                expanded_rect = option_rect.inflate(pulse, pulse // 2)
                self.draw_gradient_rect(screen, MENU_HIGHLIGHT, MENU_ACCENT, expanded_rect)
                pygame.draw.rect(screen, MENU_SELECTED, expanded_rect, 3)
                color = MENU_SELECTED
            else:
                self.draw_gradient_rect(screen, MENU_ACCENT, MENU_BG, option_rect)
                pygame.draw.rect(screen, MENU_TEXT, option_rect, 1)
                color = MENU_TEXT

            # Option text
            display_name = option.replace(".json", "").replace("_", " ").title()
            if display_name == "New Character":
                display_name = "✨ Create New Character"

            text_surface = font.render(display_name, True, color)
            text_rect = text_surface.get_rect(center=(WIDTH // 2, y_pos))
            screen.blit(text_surface, text_rect)

        # Instructions
        instructions = [
            "↑↓ Navigate    ENTER Select    ESC Back"
        ]

        instruction_y = HEIGHT - 80
        for instruction in instructions:
            text = small_font.render(instruction, True, MENU_TEXT)
            text_rect = text.get_rect(center=(WIDTH // 2, instruction_y))
            screen.blit(text, text_rect)
            instruction_y += 25

    def draw_character_sheet(self):
        """Draw the character sheet screen with full stats"""
        screen.fill(MENU_BG)

        # Header
        header_rect = pygame.Rect(0, 0, WIDTH, 80)
        self.draw_gradient_rect(screen, MENU_ACCENT, MENU_HIGHLIGHT, header_rect)

        title = large_font.render("📋 CHARACTER SHEET", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, 40))
        screen.blit(title, title_rect)

        if not self.loaded_player_attr:
            no_char_text = font.render("No character loaded!", True, WHITE)
            no_char_rect = no_char_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(no_char_text, no_char_rect)
            return

        # Initialize stats if they don't exist
        self.loaded_player_attr = self.initialize_character_stats(self.loaded_player_attr)

        # Character info panels - reorganized for more space
        left_panel = pygame.Rect(20, 90, WIDTH // 3 - 10, HEIGHT - 140)
        middle_panel = pygame.Rect(WIDTH // 3 + 10, 90, WIDTH // 3 - 20, HEIGHT - 140)
        right_panel = pygame.Rect(2 * WIDTH // 3 + 10, 90, WIDTH // 3 - 30, HEIGHT - 140)

        self.draw_gradient_rect(screen, (30, 50, 80), (20, 30, 50), left_panel)
        pygame.draw.rect(screen, MENU_TEXT, left_panel, 2)

        self.draw_gradient_rect(screen, (50, 30, 80), (30, 20, 50), middle_panel)
        pygame.draw.rect(screen, MENU_TEXT, middle_panel, 2)

        self.draw_gradient_rect(screen, (80, 30, 50), (50, 20, 30), right_panel)
        pygame.draw.rect(screen, MENU_TEXT, right_panel, 2)

        # Left panel - Basic Info & Core Stats
        left_y = 100
        name = self.loaded_player_attr.get("Name", "Unknown")
        race = self.loaded_player_attr.get("Race", "Human")
        char_type = self.loaded_player_attr.get("Type", "War Mage")
        level = self.loaded_player_attr.get("Level", 1)
        xp = self.loaded_player_attr.get("Experience_Points", 0)
        credits = self.loaded_player_attr.get("Credits", 0)

        # Calculate XP to next level
        current_level_xp = (level - 1) * 150
        next_level_xp = level * 150 if level < 35 else current_level_xp
        xp_progress = xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp if level < 35 else 0

        basic_info = [
            ("📛 Name:", name[:15]),
            ("🧬 Race:", race),
            ("🎭 Class:", char_type),
            ("⭐ Level:", f"{level}/50"),
            ("💫 XP:", f"{xp:,}"),
            ("💰 Credits:", f"{credits:,}")
        ]

        basic_title = font.render("CHARACTER INFO", True, MENU_SELECTED)
        screen.blit(basic_title, (30, left_y))
        left_y += 30

        for label, value in basic_info:
            label_text = small_font.render(label, True, MENU_TEXT)
            value_text = small_font.render(str(value), True, WHITE)
            screen.blit(label_text, (30, left_y))
            screen.blit(value_text, (30, left_y + 15))
            left_y += 30

        # XP Progress Bar
        if level < 50 and xp_needed > 0:
            left_y += 5
            xp_bar_rect = pygame.Rect(30, left_y, WIDTH // 3 - 40, 15)
            pygame.draw.rect(screen, (50, 50, 50), xp_bar_rect)
            progress_width = int((xp_progress / xp_needed) * (WIDTH // 3 - 40))
            if progress_width > 0:
                pygame.draw.rect(screen, GOLD, (30, left_y, progress_width, 15))
            pygame.draw.rect(screen, WHITE, xp_bar_rect, 2)
            left_y += 25

        # Core Stats
        left_y += 10
        stats_title = font.render("ATTRIBUTES", True, MENU_SELECTED)
        screen.blit(stats_title, (30, left_y))
        left_y += 25

        core_stats = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        for stat in core_stats:
            base_value = self.get_base_stat(stat)
            total_value = self.get_total_stat(stat)
            bonus = total_value - base_value

            stat_label = small_font.render(f"{stat.title()}:", True, MENU_TEXT)
            if bonus > 0:
                stat_value = small_font.render(f"{total_value} (+{bonus})", True, GREEN)
            else:
                stat_value = small_font.render(f"{total_value}", True, WHITE)

            screen.blit(stat_label, (30, left_y))
            screen.blit(stat_value, (30, left_y + 15))
            left_y += 30

        # Middle panel - Combat Stats & Derived Values
        middle_y = 100
        hp = self.loaded_player_attr.get("Hit_Points", 100)
        max_hp = self.get_max_hp_for_level(level)
        mana = self.loaded_player_attr.get(f"{self.original_magic_key}_Mana", 50)
        max_mana = self.get_max_mana_for_level(level)
        armor_class = self.get_armor_class()

        combat_title = font.render("COMBAT STATS", True, MENU_SELECTED)
        screen.blit(combat_title, (WIDTH // 3 + 20, middle_y))
        middle_y += 30

        # Health bar
        hp_label = small_font.render("❤️ Health:", True, MENU_TEXT)
        hp_value = small_font.render(f"{hp}/{max_hp}", True, WHITE)
        screen.blit(hp_label, (WIDTH // 3 + 20, middle_y))
        screen.blit(hp_value, (WIDTH // 3 + 20, middle_y + 15))
        middle_y += 30

        hp_bar_rect = pygame.Rect(WIDTH // 3 + 20, middle_y, WIDTH // 3 - 40, 15)
        pygame.draw.rect(screen, HEALTH_BAR_BG, hp_bar_rect)
        if max_hp > 0:
            hp_width = int((hp / max_hp) * (WIDTH // 3 - 40))
            if hp_width > 0:
                pygame.draw.rect(screen, HEALTH_BAR_COLOR, (WIDTH // 3 + 20, middle_y, hp_width, 15))
        pygame.draw.rect(screen, WHITE, hp_bar_rect, 2)
        middle_y += 25

        # Mana bar
        mana_label = small_font.render("🔮 Mana:", True, MENU_TEXT)
        mana_value = small_font.render(f"{mana}/{max_mana}", True, WHITE)
        screen.blit(mana_label, (WIDTH // 3 + 20, middle_y))
        screen.blit(mana_value, (WIDTH // 3 + 20, middle_y + 15))
        middle_y += 30

        mana_bar_rect = pygame.Rect(WIDTH // 3 + 20, middle_y, WIDTH // 3 - 40, 15)
        pygame.draw.rect(screen, MANA_BAR_BG, mana_bar_rect)
        if max_mana > 0:
            mana_width = int((mana / max_mana) * (WIDTH // 3 - 40))
            if mana_width > 0:
                pygame.draw.rect(screen, MANA_BAR_COLOR, (WIDTH // 3 + 20, middle_y, mana_width, 15))
        pygame.draw.rect(screen, WHITE, mana_bar_rect, 2)
        middle_y += 25

        # Armor Class and derived stats
        combat_stats = [
            ("🛡️ Armor Class:", f"{armor_class}"),
            ("💪 Attack Bonus:", f"+{max(0, (self.get_total_stat('strength') - 10) // 2)}"),
            ("🎯 Hit Chance:", f"+{max(0, (self.get_total_stat('dexterity') - 10) // 2)}"),
            ("🧠 Spell Power:", f"+{max(0, (self.get_total_stat('intelligence') - 10) // 2)}"),
            ("🔮 Spell Save:", f"+{max(0, (self.get_total_stat('wisdom') - 10) // 2)}"),
            ("💬 Social Bonus:", f"+{max(0, (self.get_total_stat('charisma') - 10) // 2)}")
        ]

        middle_y += 10
        for label, value in combat_stats:
            label_text = small_font.render(label, True, MENU_TEXT)
            value_text = small_font.render(str(value), True, WHITE)
            screen.blit(label_text, (WIDTH // 3 + 20, middle_y))
            screen.blit(value_text, (WIDTH // 3 + 20, middle_y + 15))
            middle_y += 30

        # Right panel - Equipment & Magic
        right_y = 100
        equipment_title = font.render("EQUIPMENT", True, MENU_SELECTED)
        screen.blit(equipment_title, (2 * WIDTH // 3 + 20, right_y))
        right_y += 25

        equipment_stats = [
            ("⚔️ Primary:", self.loaded_player_attr.get("Weapon1", "None")),
            ("🗡️ Secondary:", self.loaded_player_attr.get("Weapon2", "None")),
            ("🔮 Spell Focus:", self.loaded_player_attr.get("Weapon3", "None")),
            ("🛡️ Armor:", self.loaded_player_attr.get("Armor_Slot_1", "None")),
            ("🎽 Cloak:", self.loaded_player_attr.get("Armor_Slot_2", "None"))
        ]

        for label, value in equipment_stats:
            label_text = small_font.render(label, True, MENU_TEXT)
            # Truncate long equipment names
            display_value = str(value)[:12] + "..." if len(str(value)) > 12 else str(value)
            value_text = small_font.render(display_value, True, WHITE)
            screen.blit(label_text, (2 * WIDTH // 3 + 20, right_y))
            screen.blit(value_text, (2 * WIDTH // 3 + 20, right_y + 15))
            right_y += 30

        # Magic Aspects
        right_y += 10
        magic_title = small_font.render("🔮 MAGIC ASPECTS", True, MENU_SELECTED)
        screen.blit(magic_title, (2 * WIDTH // 3 + 20, right_y))
        right_y += 20

        for i in range(1, 4):
            aspect_key = f"Aspect{i}"
            mana_key = f"Aspect{i}_Mana"
            aspect = self.loaded_player_attr.get(aspect_key, "")
            aspect_mana = self.loaded_player_attr.get(mana_key, 0)

            if aspect:
                display_aspect = aspect.replace("_", " ").title()[:10]
                aspect_text = small_font.render(f"{display_aspect}: {aspect_mana}", True, WHITE)
                screen.blit(aspect_text, (2 * WIDTH // 3 + 20, right_y))
                right_y += 20

        # Current World Info
        if self.current_book_name and self.current_chapter_name:
            right_y += 10
            world_title = small_font.render("🌍 ADVENTURE", True, MENU_SELECTED)
            screen.blit(world_title, (2 * WIDTH // 3 + 20, right_y))
            right_y += 20

            book_text = small_font.render(f"📚 {self.current_book_name[:12]}", True, WHITE)
            chapter_text = small_font.render(f"📖 {self.current_chapter_name[:12]}", True, WHITE)
            level_text = small_font.render(f"⚡ Difficulty: Lv.{self.current_book_level}", True, WHITE)

            screen.blit(book_text, (2 * WIDTH // 3 + 20, right_y))
            screen.blit(chapter_text, (2 * WIDTH // 3 + 20, right_y + 15))
            screen.blit(level_text, (2 * WIDTH // 3 + 20, right_y + 30))

        # Instructions
        instruction_rect = pygame.Rect(0, HEIGHT - 40, WIDTH, 40)
        pygame.draw.rect(screen, MENU_ACCENT, instruction_rect)

        instruction = font.render("ESC Return to Game", True, WHITE)
        instruction_rect = instruction.get_rect(center=(WIDTH // 2, HEIGHT - 20))
        screen.blit(instruction, instruction_rect)

    def draw_boss_victory_screen(self):
        """Draw the boss victory screen with rewards"""
        screen.fill(MENU_BG)

        # Celebration particles
        if self.menu_animation_timer % 5 == 0:
            self.particles.add_particle(random.randint(0, WIDTH), random.randint(0, HEIGHT),
                                        random.choice([(255, 215, 0), (255, 255, 255), (255, 100, 100)]))
        self.particles.update()
        self.particles.draw(screen)

        # Victory header
        header_rect = pygame.Rect(0, 50, WIDTH, 120)
        self.draw_gradient_rect(screen, (150, 50, 50), (255, 100, 100), header_rect)

        title = title_font.render("🏆 BOSS DEFEATED! 🏆", True, GOLD)
        title_rect = title.get_rect(center=(WIDTH // 2, 110))
        screen.blit(title, title_rect)

        # Victory details
        details_panel = pygame.Rect(WIDTH // 6, 200, 2 * WIDTH // 3, 200)
        self.draw_gradient_rect(screen, (40, 60, 100), (20, 30, 50), details_panel)
        pygame.draw.rect(screen, GOLD, details_panel, 3)

        details_y = 230
        victory_details = [
            f"🎉 {self.boss_victory_message}",
            "",
            f"⭐ XP Gained: {self.boss_xp_gained}",
            f"💰 Credits Gained: {self.boss_credits_gained}",
            "",
            "🌟 The realm has been renewed!",
            "🗺️ Choose your next adventure!"
        ]

        for detail in victory_details:
            if detail:
                color = GOLD if "🎉" in detail or "🌟" in detail or "🗺️" in detail else WHITE
                font_to_use = font if not detail.startswith("⭐") and not detail.startswith("💰") else subtitle_font
                text = font_to_use.render(detail, True, color)
                text_rect = text.get_rect(center=(WIDTH // 2, details_y))
                screen.blit(text, text_rect)
            details_y += 25

        # Options
        options_panel = pygame.Rect(WIDTH // 4, 420, WIDTH // 2, 100)
        self.draw_gradient_rect(screen, MENU_ACCENT, MENU_HIGHLIGHT, options_panel)
        pygame.draw.rect(screen, MENU_SELECTED, options_panel, 2)

        option_texts = [
            "SPACE - Choose New Adventure",
            "C - Continue in Current World",
            "ESC - Return to Main Menu"
        ]

        options_y = 440
        for option in option_texts:
            text = font.render(option, True, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, options_y))
            screen.blit(text, text_rect)
            options_y += 20

    def draw_world_selection_screen(self):
        """Draw the world/chapter selection screen accessible during gameplay"""
        screen.fill(MENU_BG)

        # Header
        header_rect = pygame.Rect(0, 30, WIDTH, 100)
        self.draw_gradient_rect(screen, MENU_ACCENT, MENU_HIGHLIGHT, header_rect)

        title = large_font.render("🌍 SELECT NEW ADVENTURE", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, 80))
        screen.blit(title, title_rect)

        # Current world info
        if self.current_book_name and self.current_chapter_name:
            current_text = font.render(f"Current: {self.current_book_name} - {self.current_chapter_name}", True,
                                       MENU_TEXT)
            current_rect = current_text.get_rect(center=(WIDTH // 2, 110))
            screen.blit(current_text, current_rect)

        # Book selection panel
        books = self.get_book_list()
        if books:
            book_panel = pygame.Rect(50, 150, WIDTH // 2 - 75, HEIGHT - 220)
            panel_color = MENU_HIGHLIGHT if self.world_select_panel == 0 else MENU_ACCENT
            self.draw_gradient_rect(screen, panel_color, (20, 30, 50), book_panel)
            pygame.draw.rect(screen, MENU_SELECTED if self.world_select_panel == 0 else MENU_TEXT, book_panel, 2)

            book_title = font.render("📚 BOOKS", True, MENU_SELECTED)
            screen.blit(book_title, (60, 160))

            # Display books
            for i, book in enumerate(books[:8]):  # Limit to 8 books
                y_pos = 190 + i * 30
                if i == self.selected_book_option and self.world_select_panel == 0:
                    pygame.draw.rect(screen, MENU_HIGHLIGHT, (60, y_pos - 5, WIDTH // 2 - 95, 25))
                    color = MENU_SELECTED
                else:
                    color = WHITE

                display_name = book.replace(".json", "").replace("_", " ").title()
                text = small_font.render(display_name[:25], True, color)
                screen.blit(text, (65, y_pos))

        # Chapter selection panel
        if self.loaded_book_attr:
            chapter_panel = pygame.Rect(WIDTH // 2 + 25, 150, WIDTH // 2 - 75, HEIGHT - 220)
            panel_color = MENU_HIGHLIGHT if self.world_select_panel == 1 else MENU_ACCENT
            self.draw_gradient_rect(screen, panel_color, (30, 20, 50), chapter_panel)
            pygame.draw.rect(screen, MENU_SELECTED if self.world_select_panel == 1 else MENU_TEXT, chapter_panel, 2)

            chapter_title = font.render("📖 CHAPTERS", True, MENU_SELECTED)
            screen.blit(chapter_title, (WIDTH // 2 + 35, 160))

            chapters = self.get_chapters_from_book()
            for i, chapter in enumerate(chapters[:8]):  # Limit to 8 chapters
                y_pos = 190 + i * 30
                if i == self.selected_chapter_option and self.world_select_panel == 1:
                    pygame.draw.rect(screen, MENU_HIGHLIGHT, (WIDTH // 2 + 35, y_pos - 5, WIDTH // 2 - 95, 25))
                    color = MENU_SELECTED
                else:
                    color = WHITE

                display_name = chapter.replace("_", " ").title()

                # Get chapter level for display
                chapter_level = self.get_chapter_level(chapter)
                display_text = f"{display_name[:20]} (Lv.{chapter_level})"

                text = small_font.render(display_text, True, color)
                screen.blit(text, (WIDTH // 2 + 40, y_pos))

        # Instructions
        instruction_rect = pygame.Rect(0, HEIGHT - 60, WIDTH, 60)
        pygame.draw.rect(screen, MENU_ACCENT, instruction_rect)

        instructions = "↑↓ Navigate    ←→ Switch Panel    ENTER Select    ESC Cancel"
        text = font.render(instructions, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        screen.blit(text, text_rect)

    def get_chapter_level(self, chapter_name):
        """Get the level of a specific chapter"""
        if not self.loaded_book_attr:
            return 1

        for key, value in self.loaded_book_attr.items():
            if key.startswith("Chapter") and value == chapter_name:
                level_key = f"{key}_Level"
                return self.loaded_book_attr.get(level_key, 1)
        return 1

    def draw_help_screen(self):
        """Draw enhanced help screen"""
        screen.fill(MENU_BG)

        # Header
        header_rect = pygame.Rect(0, 0, WIDTH, 80)
        self.draw_gradient_rect(screen, MENU_ACCENT, MENU_HIGHLIGHT, header_rect)

        title = large_font.render("GAME HELP", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 25))

        # Section tabs
        sections = ["Overview", "Controls", "Gameplay", "Tips"]
        tab_width = WIDTH // len(sections)

        for i, section in enumerate(sections):
            tab_rect = pygame.Rect(i * tab_width, 80, tab_width, 40)

            if i == self.help_section:
                pygame.draw.rect(screen, MENU_HIGHLIGHT, tab_rect)
                pygame.draw.rect(screen, MENU_SELECTED, tab_rect, 2)
                color = MENU_SELECTED
            else:
                pygame.draw.rect(screen, MENU_ACCENT, tab_rect)
                color = MENU_TEXT

            text = font.render(section, True, color)
            text_rect = text.get_rect(center=tab_rect.center)
            screen.blit(text, text_rect)

        # Content area
        content_rect = pygame.Rect(20, 140, WIDTH - 40, HEIGHT - 200)
        pygame.draw.rect(screen, (20, 25, 40), content_rect)
        pygame.draw.rect(screen, MENU_TEXT, content_rect, 2)

        # Help content
        section_key = list(HELP_CONTENT.keys())[self.help_section]
        content_lines = HELP_CONTENT[section_key]

        y_offset = 150
        for line in content_lines:
            if y_offset > HEIGHT - 80:
                break

            if line == "":
                y_offset += 15
                continue

            # Style headers
            if line.isupper() and not line.startswith("•"):
                color = MENU_SELECTED
                font_to_use = font
            elif line.startswith("•"):
                color = MENU_TEXT
                font_to_use = small_font
                line = "  " + line  # Indent bullets
            else:
                color = MENU_TEXT
                font_to_use = small_font

            text = font_to_use.render(line, True, color)
            screen.blit(text, (30, y_offset))
            y_offset += 25

        # Navigation instructions
        nav_rect = pygame.Rect(0, HEIGHT - 60, WIDTH, 60)
        pygame.draw.rect(screen, MENU_ACCENT, nav_rect)

        instructions = "← → Change Section    ESC Return to Menu"
        text = font.render(instructions, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
        screen.blit(text, text_rect)

    def get_book_list(self):
        """Get list of available books"""
        books_dir = "Books"
        if os.path.exists(books_dir):
            return [f for f in os.listdir(books_dir) if f.endswith('.json')]
        return []

    def get_character_list(self):
        """Get list of available characters"""
        chars_dir = "Characters"
        if os.path.exists(chars_dir):
            chars = [f for f in os.listdir(chars_dir) if f.endswith('.json')]
            chars.append("New Character")
            return chars
        return ["New Character"]

    def get_chapters_from_book(self):
        """Get chapters from currently loaded book"""
        if not self.loaded_book_attr:
            return []

        chapters = []
        for key, value in self.loaded_book_attr.items():
            if key.startswith("Chapter") and not key.endswith(("_Level", "_Enemy_Type")) and value:
                chapters.append(value)
        return chapters

    def load_book_and_chapter(self, book_file, chapter_index):
        """Load a specific book and chapter"""
        try:
            book_path = os.path.join("Books", book_file)
            with open(book_path, 'r') as f:
                self.loaded_book_attr = json.load(f)

            chapters = self.get_chapters_from_book()
            if 0 <= chapter_index < len(chapters):
                self.current_book_name = book_file.replace(".json", "").replace("_", " ").title()
                self.current_chapter_name = chapters[chapter_index]

                # Get chapter level and enemy type
                chapter_key = None
                for key, value in self.loaded_book_attr.items():
                    if key.startswith("Chapter") and value == chapters[chapter_index]:
                        chapter_key = key
                        break

                chapter_info = {}
                if chapter_key:
                    level_key = f"{chapter_key}_Level"
                    enemy_key = f"{chapter_key}_Enemy_Type"
                    chapter_info["Level"] = self.loaded_book_attr.get(level_key, 1)
                    chapter_info["Enemy_Type"] = self.loaded_book_attr.get(enemy_key, "demon")

                # Setup the world with new chapter
                self.setup_world(chapter_info)
                return True

        except Exception as e:
            print(f"Failed to load book/chapter: {e}")
            return False

        return False

    def create_scaled_enemy(self):
        """Create an enemy scaled to current book level"""
        base_hp = 75
        level_scaling = self.current_book_level * 25
        scaled_hp = base_hp + level_scaling

        enemy_names = [
            "Wild Demon", "Fire Elemental", "Shadow Beast", "Ice Troll",
            "Void Wraith", "Dragon Spawn", "Nightmare Fiend", "Frost Giant"
        ]

        enemy_name = random.choice(enemy_names)
        if self.current_book_level >= 3:
            enemy_name = f"Elite {enemy_name}"
        if self.current_book_level >= 5:
            enemy_name = f"Ancient {enemy_name}"

        return {
            "Name": enemy_name,
            "Hit_Points": scaled_hp,
            "Aspect1": f"fire_level_{min(3, self.current_book_level)}",
            "Level": self.current_book_level,
            "Experience_Points": 0
        }

    def create_scaled_boss(self):
        """Create a boss scaled to current book level"""
        base_hp = 150
        level_scaling = self.current_book_level * 50
        scaled_hp = base_hp + level_scaling

        boss_titles = [
            "💀 DEMON LORD 💀", "🔥 FIRE SOVEREIGN 🔥", "❄️ FROST KING ❄️",
            "🌑 SHADOW EMPEROR 🌑", "⚡ STORM MASTER ⚡", "🐉 DRAGON OVERLORD 🐉"
        ]

        boss_name = random.choice(boss_titles)
        if self.current_book_level >= 5:
            boss_name = f"LEGENDARY {boss_name}"

        return {
            "Name": boss_name,
            "Hit_Points": scaled_hp,
            "Aspect1": f"fire_level_{min(5, self.current_book_level + 1)}",
            "Level": self.current_book_level + 2,
            "Experience_Points": 0
        }

    def handle_collision(self, pos, positions):
        """Check for collision between player and objects"""
        player_rect = pygame.Rect(self.player_pos[0], self.player_pos[1], self.player_size, self.player_size)
        for obj in positions:
            if obj["active"]:
                obj_rect = pygame.Rect(obj["pos"][0], obj["pos"][1], 30, 30)
                if player_rect.colliderect(obj_rect):
                    return True, obj
        return False, None

    def draw_enhanced_ui_bars(self):
        """Draw health and mana bars on screen"""
        if not self.loaded_player_attr:
            return

        level = self.loaded_player_attr.get("Level", 1)
        health = self.loaded_player_attr.get("Hit_Points", 100)
        max_health = self.get_max_hp_for_level(level)
        mana = self.loaded_player_attr.get(f"{self.original_magic_key}_Mana", 10)
        max_mana = self.get_max_mana_for_level(level)

        ui_panel = pygame.Rect(10, 10, 380, 140)
        pygame.draw.rect(screen, UI_BG_COLOR, ui_panel)
        pygame.draw.rect(screen, UI_BORDER_COLOR, ui_panel, 2)

        health_bar = HealthManaBar(20, 20, 200, 25, max_health, health,
                                   HEALTH_BAR_COLOR, HEALTH_BAR_BG, "HP")
        health_bar.draw(screen)

        mana_bar = HealthManaBar(20, 55, 200, 25, max_mana, mana,
                                 MANA_BAR_COLOR, MANA_BAR_BG, "MP")
        mana_bar.draw(screen)

        name_text = small_font.render(f"Name: {self.loaded_player_attr.get('Name', 'Unknown')}", True, WHITE)
        level_text = small_font.render(f"Level: {level}/50", True, WHITE)
        credits_text = small_font.render(f"Credits: {self.loaded_player_attr.get('Credits', 0)}", True, WHITE)

        # Get current stats for display
        total_stats = self.get_all_player_stats()  # ADD THIS
        ac_text = small_font.render(f"AC: {total_stats['armor_class']}", True, LIGHT_BLUE)  # ADD THIS

        # Show key combat stats
        str_bonus = (total_stats['strength'] - 10) // 2  # ADD THIS
        int_bonus = (total_stats['intelligence'] - 10) // 2  # ADD THIS
        combat_text = small_font.render(f"Att: +{max(0, str_bonus)}, Spell: +{max(0, int_bonus)}", True,
                                        GREEN)  # ADD THIS

        # XP Progress
        xp = self.loaded_player_attr.get("Experience_Points", 0)
        current_level_xp = (level - 1) * 100
        next_level_xp = level * 100 if level < 25 else current_level_xp
        xp_progress = xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp if level < 25 else 0

        if level < 50:
            xp_text = small_font.render(f"XP: {xp_progress}/{xp_needed}", True, GOLD)
        else:
            xp_text = small_font.render(f"XP: MAX LEVEL", True, GOLD)

        # Show current world
        if self.current_book_name and self.current_chapter_name:
            world_text = small_font.render(f"World: {self.current_chapter_name[:20]}", True, LIGHT_BLUE)
            level_text2 = small_font.render(f"Difficulty: Lv.{self.current_book_level}", True, ORANGE)
            screen.blit(world_text, (230, 95))
            screen.blit(level_text2, (230, 115))

        screen.blit(name_text, (230, 25))
        screen.blit(level_text, (230, 45))
        screen.blit(credits_text, (230, 65))
        screen.blit(xp_text, (20, 90))

        screen.blit(ac_text, (230, 85))
        screen.blit(combat_text, (20, 90))

        # XP Progress bar - made smaller
        if level < 50 and xp_needed > 0:
            xp_bar_rect = pygame.Rect(20, 110, 150, 12)  # Reduced width and height
            pygame.draw.rect(screen, (50, 50, 50), xp_bar_rect)
            progress_width = int((xp_progress / xp_needed) * 150)  # Adjusted for new width
            if progress_width > 0:
                pygame.draw.rect(screen, GOLD, (20, 110, progress_width, 12))
            pygame.draw.rect(screen, WHITE, xp_bar_rect, 1)

    def draw_store_screen(self):
        """Draw the store interface with scrolling"""
        screen.fill(MENU_BG)

        # Header
        header_rect = pygame.Rect(0, 0, WIDTH, 120)
        self.draw_gradient_rect(screen, MENU_ACCENT, MENU_HIGHLIGHT, header_rect)

        title = large_font.render("🏪 MAGIC SHOP", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title, title_rect)

        credits = self.loaded_player_attr.get("Credits", 0) if self.loaded_player_attr else 0
        credits_text = font.render(f"💰 Credits: {credits}", True, GOLD)
        screen.blit(credits_text, (50, 80))

        # Calculate scrolling parameters
        total_items = len(self.store.items)
        max_scroll = max(0, total_items - self.items_per_page)

        # Ensure selected item is visible
        if self.selected_store_item < self.store_scroll_offset:
            self.store_scroll_offset = self.selected_store_item
        elif self.selected_store_item >= self.store_scroll_offset + self.items_per_page:
            self.store_scroll_offset = self.selected_store_item - self.items_per_page + 1

        # Clamp scroll offset
        self.store_scroll_offset = max(0, min(self.store_scroll_offset, max_scroll))

        # Store items area
        items_area = pygame.Rect(20, 140, WIDTH - 40, 360)
        pygame.draw.rect(screen, (20, 25, 40), items_area)
        pygame.draw.rect(screen, MENU_TEXT, items_area, 2)

        # Get affordable items
        affordable_items = self.store.get_affordable_items(credits) if self.loaded_player_attr else []

        # Display visible items
        y_start = 150
        item_height = 45

        visible_items = self.store.items[self.store_scroll_offset:self.store_scroll_offset + self.items_per_page]

        for i, item in enumerate(visible_items):
            actual_index = self.store_scroll_offset + i
            y_pos = y_start + i * item_height

            # Item background
            item_rect = pygame.Rect(30, y_pos, WIDTH - 60, item_height - 5)

            if actual_index == self.selected_store_item:
                # Animated selection
                pulse = int(5 * abs(math.sin(self.menu_animation_timer * 0.2)))
                expanded_rect = item_rect.inflate(pulse, pulse // 2)
                self.draw_gradient_rect(screen, MENU_HIGHLIGHT, MENU_ACCENT, expanded_rect)
                pygame.draw.rect(screen, MENU_SELECTED, expanded_rect, 3)
                text_color = MENU_SELECTED
            else:
                self.draw_gradient_rect(screen, (40, 40, 60), (20, 20, 40), item_rect)
                pygame.draw.rect(screen, MENU_TEXT, item_rect, 1)
                text_color = WHITE

            # Check if item is affordable
            affordable = item in affordable_items
            if not affordable:
                text_color = GRAY

            # Item details
            name_text = font.render(item.name, True, text_color)
            price_color = GOLD if affordable else GRAY
            price_text = font.render(f"{item.price} credits", True, price_color)
            desc_text = small_font.render(item.description, True, text_color)

            # Position text
            screen.blit(name_text, (40, y_pos + 5))
            screen.blit(price_text, (WIDTH - 180, y_pos + 5))
            screen.blit(desc_text, (40, y_pos + 25))

            # Affordable indicator
            if affordable:
                check_text = small_font.render("✓", True, GREEN)
                screen.blit(check_text, (WIDTH - 40, y_pos + 15))
            else:
                x_text = small_font.render("✗", True, RED)
                screen.blit(x_text, (WIDTH - 40, y_pos + 15))

        # Scroll indicators
        if total_items > self.items_per_page:
            # Scrollbar background
            scrollbar_rect = pygame.Rect(WIDTH - 25, 140, 15, 360)
            pygame.draw.rect(screen, (40, 40, 40), scrollbar_rect)
            pygame.draw.rect(screen, MENU_TEXT, scrollbar_rect, 1)

            # Scrollbar thumb
            if max_scroll > 0:
                thumb_height = max(20, int(360 * self.items_per_page / total_items))
                thumb_y = 140 + int((360 - thumb_height) * self.store_scroll_offset / max_scroll)
                thumb_rect = pygame.Rect(WIDTH - 24, thumb_y, 13, thumb_height)
                pygame.draw.rect(screen, MENU_ACCENT, thumb_rect)
                pygame.draw.rect(screen, MENU_SELECTED, thumb_rect, 1)

            # Scroll arrows
            if self.store_scroll_offset > 0:
                up_arrow = font.render("▲", True, MENU_SELECTED)
                screen.blit(up_arrow, (WIDTH - 22, 120))
            else:
                up_arrow = font.render("▲", True, GRAY)
                screen.blit(up_arrow, (WIDTH - 22, 120))

            if self.store_scroll_offset < max_scroll:
                down_arrow = font.render("▼", True, MENU_SELECTED)
                screen.blit(down_arrow, (WIDTH - 22, 510))
            else:
                down_arrow = font.render("▼", True, GRAY)
                screen.blit(down_arrow, (WIDTH - 22, 510))

        # Item counter
        counter_text = small_font.render(f"Item {self.selected_store_item + 1} of {total_items}", True, MENU_TEXT)
        screen.blit(counter_text, (50, 510))

        # Selected item details panel (if there's space)
        if self.selected_store_item < len(self.store.items):
            selected_item = self.store.items[self.selected_store_item]

            detail_panel = pygame.Rect(50, 530, WIDTH - 100, 50)
            self.draw_gradient_rect(screen, (30, 50, 80), (20, 30, 50), detail_panel)
            pygame.draw.rect(screen, MENU_TEXT, detail_panel, 1)

            # Item type and effects
            type_text = small_font.render(f"Type: {selected_item.item_type.replace('_', ' ').title()}", True, WHITE)
            screen.blit(type_text, (60, 540))

            if selected_item.item_type in ["health_potion", "mana_potion"]:
                effect_text = small_font.render(f"Restores: {selected_item.effect_value} points", True, GREEN)
                screen.blit(effect_text, (60, 555))
            elif selected_item.stat_bonuses:
                bonus_text = ", ".join(
                    [f"{stat.title()}: +{bonus}" for stat, bonus in selected_item.stat_bonuses.items()])
                effect_text = small_font.render(f"Bonuses: {bonus_text}", True, LIGHT_BLUE)
                screen.blit(effect_text, (60, 555))

        # Instructions
        instruction_rect = pygame.Rect(0, HEIGHT - 50, WIDTH, 50)
        pygame.draw.rect(screen, MENU_ACCENT, instruction_rect)

        instructions = "↑↓ Navigate    ENTER Purchase    ESC Return"
        if total_items > self.items_per_page:
            instructions += "    PAGE UP/DOWN Scroll"

        text = font.render(instructions, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT - 25))
        screen.blit(text, text_rect)

    def draw_rest_screen(self):
        """Draw the rest interface"""
        screen.fill(MENU_BG)

        # Header
        header_rect = pygame.Rect(0, 0, WIDTH, 120)
        self.draw_gradient_rect(screen, (0, 100, 150), (0, 150, 200), header_rect)

        title = large_font.render("🏕️ REST CAMP", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, 60))
        screen.blit(title, title_rect)

        # Current stats
        level = self.loaded_player_attr.get("Level", 1)
        health = self.loaded_player_attr.get("Hit_Points", 100)
        max_health = self.get_max_hp_for_level(level)
        mana = self.loaded_player_attr.get(f"{self.original_magic_key}_Mana", 10)
        max_mana = self.get_max_mana_for_level(level)
        credits = self.loaded_player_attr.get("Credits", 0)

        # Stats panel
        stats_panel = pygame.Rect(WIDTH // 4, 150, WIDTH // 2, 200)
        self.draw_gradient_rect(screen, (30, 50, 80), (20, 30, 50), stats_panel)
        pygame.draw.rect(screen, MENU_TEXT, stats_panel, 2)

        stats_y = 170
        stats_text = [
            f"❤️ Health: {health}/{max_health}",
            f"🔮 Mana: {mana}/{max_mana}",
            f"💰 Credits: {credits}",
            "",
            f"💳 Rest Cost: {self.rest_areas[0].rest_cost} credits"
        ]

        for stat in stats_text:
            if stat:
                text = font.render(stat, True, WHITE)
                text_rect = text.get_rect(center=(WIDTH // 2, stats_y))
                screen.blit(text, text_rect)
            stats_y += 35

        # Rest message
        if self.rest_message:
            message_text = font.render(self.rest_message, True, GREEN)
            message_rect = message_text.get_rect(center=(WIDTH // 2, stats_y + 20))
            screen.blit(message_text, message_rect)

        # Instructions
        can_afford = credits >= self.rest_areas[0].rest_cost
        needs_rest = health < max_health or mana < max_mana

        instruction_rect = pygame.Rect(0, HEIGHT - 80, WIDTH, 80)
        pygame.draw.rect(screen, MENU_ACCENT, instruction_rect)

        if needs_rest and can_afford:
            instruction = "SPACE Rest (restores full HP and MP)"
            color = GREEN
        elif not can_afford:
            instruction = "❌ Not enough credits to rest"
            color = RED
        elif not needs_rest:
            instruction = "✅ You are already at full health and mana"
            color = LIGHT_BLUE
        else:
            instruction = "ESC Return to game"
            color = WHITE

        instruction_text = font.render(instruction, True, color)
        instruction_rect = instruction_text.get_rect(center=(WIDTH // 2, HEIGHT - 50))
        screen.blit(instruction_text, instruction_rect)

        esc_text = small_font.render("ESC Return", True, MENU_TEXT)
        esc_rect = esc_text.get_rect(center=(WIDTH // 2, HEIGHT - 20))
        screen.blit(esc_text, esc_rect)

    def draw_inventory_screen(self):
        """Draw the inventory interface"""
        screen.fill(MENU_BG)

        # Header
        header_rect = pygame.Rect(0, 0, WIDTH, 100)
        self.draw_gradient_rect(screen, MENU_ACCENT, MENU_HIGHLIGHT, header_rect)

        title = large_font.render("🎒 INVENTORY", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title, title_rect)

        inventory = self.loaded_player_attr.get("Inventory", {})

        if not inventory:
            # Empty inventory
            empty_panel = pygame.Rect(WIDTH // 4, HEIGHT // 3, WIDTH // 2, 100)
            self.draw_gradient_rect(screen, (40, 40, 60), (20, 20, 40), empty_panel)
            pygame.draw.rect(screen, MENU_TEXT, empty_panel, 2)

            empty_text = font.render("Your inventory is empty!", True, WHITE)
            empty_rect = empty_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(empty_text, empty_rect)
        else:
            # Display inventory items
            y_start = 130
            inventory_items = list(inventory.items())

            for i, (item_name, quantity) in enumerate(inventory_items):
                y_pos = y_start + i * 60

                item_rect = pygame.Rect(50, y_pos, WIDTH - 100, 50)

                if i == self.selected_inventory_item:
                    # Animated selection
                    pulse = int(5 * abs(math.sin(self.menu_animation_timer * 0.2)))
                    expanded_rect = item_rect.inflate(pulse, pulse // 2)
                    self.draw_gradient_rect(screen, MENU_HIGHLIGHT, MENU_ACCENT, expanded_rect)
                    pygame.draw.rect(screen, MENU_SELECTED, expanded_rect, 3)
                else:
                    self.draw_gradient_rect(screen, (40, 40, 60), (20, 20, 40), item_rect)
                    pygame.draw.rect(screen, MENU_TEXT, item_rect, 1)

                name_text = font.render(f"{item_name} x{quantity}", True, WHITE)
                screen.blit(name_text, (60, y_pos + 15))

                # Find item description
                description = "Unknown item"
                for store_item in self.store.items:
                    if store_item.name == item_name:
                        description = store_item.description
                        break

                desc_text = small_font.render(description, True, GRAY)
                screen.blit(desc_text, (400, y_pos + 20))

        # Instructions
        instruction_rect = pygame.Rect(0, HEIGHT - 80, WIDTH, 80)
        pygame.draw.rect(screen, MENU_ACCENT, instruction_rect)

        instructions = [
            "↑↓ Navigate    ENTER Use Item    ESC Return"
        ]

        for i, instruction in enumerate(instructions):
            text = font.render(instruction, True, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT - 50 + i * 25))
            screen.blit(text, text_rect)

    def draw_enhanced_fight_screen(self):
        """Draw the enhanced fight screen with fixed enemy HP bar"""
        # Animated background
        for y in range(HEIGHT):
            color_intensity = int(20 + (y / HEIGHT) * 40 + 10 * math.sin(self.menu_animation_timer * 0.1))
            color = (max(0, color_intensity), 0, max(0, color_intensity))
            pygame.draw.line(screen, color, (0, y), (WIDTH, y))

        # Title with battle effects
        title_surface = title_font.render("⚔️ BATTLE! ⚔️", True, WHITE)
        title_rect = title_surface.get_rect(center=(WIDTH // 2, 50))
        screen.blit(title_surface, title_rect)

        # Combat arena
        arena_rect = pygame.Rect(50, 100, WIDTH - 100, HEIGHT - 300)
        self.draw_gradient_rect(screen, (60, 40, 80), (40, 20, 60), arena_rect)
        pygame.draw.rect(screen, WHITE, arena_rect, 3)

        # Player and enemy sections
        player_section = pygame.Rect(70, 120, (WIDTH - 140) // 2 - 20, HEIGHT - 340)
        enemy_section = pygame.Rect((WIDTH // 2) + 20, 120, (WIDTH - 140) // 2 - 20, HEIGHT - 340)

        self.draw_gradient_rect(screen, (50, 70, 50), (30, 50, 30), player_section)
        pygame.draw.rect(screen, GREEN, player_section, 2)

        self.draw_gradient_rect(screen, (70, 50, 50), (50, 30, 30), enemy_section)
        pygame.draw.rect(screen, RED, enemy_section, 2)

        # Character names and levels
        if self.loaded_player_attr and self.loaded_enemy_attr:
            player_name = self.loaded_player_attr.get("Name", "Player")
            player_level = self.loaded_player_attr.get("Level", 1)
            enemy_name = self.loaded_enemy_attr.get("Name", "Enemy")
            enemy_level = self.loaded_enemy_attr.get("Level", 1)

            player_name_surface = font.render(f"🛡️ {player_name} (Lv.{player_level})", True, WHITE)
            screen.blit(player_name_surface, (80, 130))

            enemy_name_surface = font.render(f"💀 {enemy_name} (Lv.{enemy_level})", True, WHITE)
            screen.blit(enemy_name_surface, (WIDTH // 2 + 30, 130))

            # Character sprites with animation
            player_offset = int(3 * math.sin(self.menu_animation_timer * 0.1))
            enemy_offset = int(3 * math.sin(self.menu_animation_timer * 0.15))

            player_char_rect = pygame.Rect(100, 160 + player_offset, 40, 60)
            enemy_char_rect = pygame.Rect(WIDTH // 2 + 50, 160 + enemy_offset, 40, 60)

            pygame.draw.rect(screen, BLUE, player_char_rect)
            pygame.draw.rect(screen, WHITE, player_char_rect, 2)
            pygame.draw.rect(screen, RED, enemy_char_rect)
            pygame.draw.rect(screen, WHITE, enemy_char_rect, 2)

            # Health and mana bars with proper calculations - FIXED
            player_level = self.loaded_player_attr.get("Level", 1)
            player_health = self.loaded_player_attr.get("Hit_Points", 100)
            player_max_health = self.get_max_hp_for_level(player_level)
            player_mana = self.loaded_player_attr.get(f"{self.original_magic_key}_Mana", 10)
            player_max_mana = self.get_max_mana_for_level(player_level)

            # Enemy HP calculation - FIXED
            enemy_health = self.loaded_enemy_attr.get("Hit_Points", 100)

            # Calculate enemy max HP properly
            enemy_max_health = enemy_health

            # If we have a record of the enemy's starting HP, use that
            if hasattr(self, 'enemy_starting_hp'):
                enemy_max_health = self.enemy_starting_hp
            else:
                # Try to determine max HP from enemy level or use a reasonable estimate
                enemy_level = self.loaded_enemy_attr.get("Level", 1)
                estimated_max_hp = 75 + (enemy_level * 25)  # Base calculation

                # If current HP is higher than our estimate, use current HP as max
                if enemy_health > estimated_max_hp:
                    enemy_max_health = enemy_health
                else:
                    enemy_max_health = estimated_max_hp

                # Store for future reference
                self.enemy_starting_hp = enemy_max_health

            # Player health bar - FIXED: Pass current HP correctly
            player_health_bar = HealthManaBar(80, 240, 150, 20, player_max_health, player_health,
                                              HEALTH_BAR_COLOR, HEALTH_BAR_BG, "HP")
            player_health_bar.draw(screen)

            # Player mana bar - FIXED: Pass current mana correctly
            player_mana_bar = HealthManaBar(80, 270, 150, 20, player_max_mana, player_mana,
                                            MANA_BAR_COLOR, MANA_BAR_BG, "MP")
            player_mana_bar.draw(screen)

            # Enemy health bar - FIXED: Pass current HP correctly
            enemy_health_bar = HealthManaBar(WIDTH // 2 + 30, 240, 150, 20, enemy_max_health, enemy_health,
                                             ENEMY_HEALTH_COLOR, HEALTH_BAR_BG, "Enemy HP")
            enemy_health_bar.draw(screen)

            # Additional health info display
            player_hp_text = small_font.render(f"{player_health}/{player_max_health} HP", True, WHITE)
            screen.blit(player_hp_text, (80, 220))

            player_mp_text = small_font.render(f"{player_mana}/{player_max_mana} MP", True, WHITE)
            screen.blit(player_mp_text, (80, 295))

            enemy_hp_text = small_font.render(f"{enemy_health}/{enemy_max_health} HP", True, WHITE)
            screen.blit(enemy_hp_text, (WIDTH // 2 + 30, 220))

        # Combat log
        log_area = pygame.Rect(50, HEIGHT - 180, WIDTH - 100, 120)
        self.draw_gradient_rect(screen, (20, 20, 40), (10, 10, 20), log_area)
        pygame.draw.rect(screen, WHITE, log_area, 2)

        # Display messages
        y_offset = HEIGHT - 170
        for message, color in self.combat_messages[-5:]:
            if message.strip():
                text_surface = small_font.render(message[:70], True, color)
                screen.blit(text_surface, (60, y_offset))
                y_offset += 22

        # Floating damage text
        for damage_text in self.damage_texts[:]:
            if damage_text.update():
                damage_text.draw(screen)
            else:
                self.damage_texts.remove(damage_text)

        # Combat options
        options_bg = pygame.Rect(50, HEIGHT - 50, WIDTH - 100, 40)
        self.draw_gradient_rect(screen, MENU_ACCENT, MENU_BG, options_bg)
        pygame.draw.rect(screen, WHITE, options_bg, 2)

        # Check battle status and show appropriate instructions
        if self.loaded_player_attr and self.loaded_enemy_attr:
            player_alive = self.loaded_player_attr.get("Hit_Points", 0) > 0
            enemy_alive = self.loaded_enemy_attr.get("Hit_Points", 0) > 0

            if not player_alive:
                death_text = font.render("💀 YOU DIED! Press SPACE or ESC to continue", True, RED)
                death_rect = death_text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
                screen.blit(death_text, death_rect)
            elif not enemy_alive:
                victory_text = font.render("🏆 VICTORY! Press SPACE or ESC to continue", True, GREEN)
                victory_rect = victory_text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
                screen.blit(victory_text, victory_rect)
            else:
                instructions = "SPACE Attack    H Health Potion    M Mana Potion    I Inventory    ESC Flee"
                continue_surface = small_font.render(instructions, True, WHITE)
                continue_rect = continue_surface.get_rect(center=(WIDTH // 2, HEIGHT - 30))
                screen.blit(continue_surface, continue_rect)

    def purchase_item(self, item):
        """Purchase an item from the store and apply stat bonuses"""
        credits = self.loaded_player_attr.get("Credits", 0)

        if credits < item.price:
            return False, "Not enough credits!"

        self.loaded_player_attr["Credits"] -= item.price

        if item.item_type in ["health_potion", "mana_potion"]:
            inventory = self.loaded_player_attr.get("Inventory", {})
            if item.name in inventory:
                inventory[item.name] += 1
            else:
                inventory[item.name] = 1
            self.loaded_player_attr["Inventory"] = inventory
            return True, f"Added {item.name} to inventory!"

        elif item.item_type == "full_restore":
            level = self.loaded_player_attr.get("Level", 1)
            self.loaded_player_attr["Hit_Points"] = self.get_max_hp_for_level(level)
            self.loaded_player_attr[f"{self.original_magic_key}_Mana"] = self.get_max_mana_for_level(level)
            return True, "Fully restored HP and MP!"

        elif item.item_type in ["weapon", "armor", "accessory"]:
            # Add to inventory first
            inventory = self.loaded_player_attr.get("Inventory", {})
            if item.name in inventory:
                inventory[item.name] += 1
            else:
                inventory[item.name] = 1
            self.loaded_player_attr["Inventory"] = inventory

            # Auto-equip logic with stat bonus application
            equipped = False
            if item.item_type == "weapon":
                if not self.loaded_player_attr.get("Weapon1"):
                    self.loaded_player_attr["Weapon1"] = item.name
                    equipped = True
                elif not self.loaded_player_attr.get("Weapon3"):
                    self.loaded_player_attr["Weapon3"] = item.name
                    equipped = True

                if equipped:
                    inventory[item.name] -= 1
                    if inventory[item.name] <= 0:
                        del inventory[item.name]
                    # Apply stat bonuses immediately when equipped
                    self.apply_equipment_stat_bonuses(item)
                    return True, f"Equipped {item.name}! Stats updated!"

            elif item.item_type == "armor":
                if not self.loaded_player_attr.get("Armor_Slot_1"):
                    self.loaded_player_attr["Armor_Slot_1"] = item.name
                    equipped = True
                elif not self.loaded_player_attr.get("Armor_Slot_2"):
                    self.loaded_player_attr["Armor_Slot_2"] = item.name
                    equipped = True

                if equipped:
                    inventory[item.name] -= 1
                    if inventory[item.name] <= 0:
                        del inventory[item.name]
                    # Apply stat bonuses immediately when equipped
                    self.apply_equipment_stat_bonuses(item)
                    return True, f"Equipped {item.name}! Stats updated!"

            elif item.item_type == "accessory":
                # Accessories are automatically "equipped" when in inventory
                # Apply stat bonuses immediately
                self.apply_equipment_stat_bonuses(item)
                return True, f"Acquired {item.name}! Stats updated!"

            return True, f"Added {item.name} to inventory!"

        return False, "Unknown item type!"

    def apply_equipment_stat_bonuses(self, item):
        """Apply stat bonuses from equipment to character base stats"""
        if not item.stat_bonuses:
            return

        # Note: In this system, we don't modify base stats directly
        # The get_total_stat() method calculates bonuses dynamically
        # This ensures stats are always calculated correctly

        # Add visual feedback for stat changes
        for stat, bonus in item.stat_bonuses.items():
            if bonus > 0:
                self.damage_texts.append(
                    DamageText(self.player_pos[0], self.player_pos[1] - 30,
                               f"+{bonus} {stat.title()}!", GREEN)
                )

    def use_item_from_inventory(self, item_name):
        """Use an item from inventory"""
        inventory = self.loaded_player_attr.get("Inventory", {})

        if item_name not in inventory or inventory[item_name] <= 0:
            return False, "Item not in inventory!"

        item = None
        for store_item in self.store.items:
            if store_item.name == item_name:
                item = store_item
                break

        if not item:
            return False, "Unknown item!"

        level = self.loaded_player_attr.get("Level", 1)

        if item.item_type == "health_potion":
            current_hp = self.loaded_player_attr.get("Hit_Points", 100)
            max_hp = self.get_max_hp_for_level(level)
            new_hp = min(max_hp, current_hp + item.effect_value)
            self.loaded_player_attr["Hit_Points"] = new_hp
            hp_restored = new_hp - current_hp

            inventory[item_name] -= 1
            if inventory[item_name] <= 0:
                del inventory[item_name]
            self.loaded_player_attr["Inventory"] = inventory

            return True, f"Restored {hp_restored} HP!"

        elif item.item_type == "mana_potion":
            current_mana = self.loaded_player_attr.get(f"{self.original_magic_key}_Mana", 10)
            max_mana = self.get_max_mana_for_level(level)
            new_mana = min(max_mana, current_mana + item.effect_value)
            self.loaded_player_attr[f"{self.original_magic_key}_Mana"] = new_mana
            mana_restored = new_mana - current_mana

            inventory[item_name] -= 1
            if inventory[item_name] <= 0:
                del inventory[item_name]
            self.loaded_player_attr["Inventory"] = inventory

            return True, f"Restored {mana_restored} MP!"

        return False, "Cannot use this item!"

    def rest_player(self):
        """Rest the player to restore health and mana"""
        credits = self.loaded_player_attr.get("Credits", 0)
        rest_cost = self.rest_areas[0].rest_cost

        if credits < rest_cost:
            return False, "Not enough credits to rest!"

        level = self.loaded_player_attr.get("Level", 1)
        max_hp = self.get_max_hp_for_level(level)
        max_mana = self.get_max_mana_for_level(level)
        current_hp = self.loaded_player_attr.get("Hit_Points", 100)
        current_mana = self.loaded_player_attr.get(f"{self.original_magic_key}_Mana", 10)

        if current_hp >= max_hp and current_mana >= max_mana:
            return False, "You are already at full health and mana!"

        self.loaded_player_attr["Credits"] -= rest_cost
        self.loaded_player_attr["Hit_Points"] = max_hp
        self.loaded_player_attr[f"{self.original_magic_key}_Mana"] = max_mana

        return True, "You feel refreshed! HP and MP fully restored!"

    def enhanced_fight_logic(self):
        """Enhanced fight logic with boss mechanics and dice-based XP"""
        if self.loaded_player_attr[f"{self.original_magic_key}_Mana"] <= 0:
            self.combat_messages.append((f"No mana remaining!", (255, 0, 0)))
            return 2

        player_name = self.loaded_player_attr["Name"]
        player_level = self.loaded_player_attr.get("Level", 1)
        player_health = self.loaded_player_attr["Hit_Points"]
        enemy_name = self.loaded_enemy_attr["Name"]
        enemy_health = self.loaded_enemy_attr["Hit_Points"]
        enemy_level = self.loaded_enemy_attr.get("Level", 1)
        player_aspect1 = self.loaded_player_attr["Aspect1"]
        enemy_aspect1 = self.loaded_enemy_attr["Aspect1"]

        # Store enemy starting HP on first combat action (ADDED)
        if not hasattr(self, 'enemy_starting_hp'):
            self.enemy_starting_hp = enemy_health

        # Check if this is a boss fight
        is_boss = "DEMON LORD" in enemy_name or "SOVEREIGN" in enemy_name or "KING" in enemy_name or "EMPEROR" in enemy_name or "OVERLORD" in enemy_name or enemy_health > 150

        player_stats = self.get_all_player_stats()

        rolls = roll_dice(1, 20)
        try:
            result = gui_fight(
                player_name=player_name,
                player_aspect1=player_aspect1,
                roll=rolls[0],
                demon_name=enemy_name,
                demon_hit_points=enemy_health,
                demon_aspect1=enemy_aspect1,
                player_hit_points=player_health,
                mana_level=self.loaded_player_attr[f"{self.original_magic_key}_Mana"],
                weapon_level=player_level if is_boss else max(1, player_level // 3),
                player_level=player_level,
                player_stats=player_stats  # ADD THIS LINE
            )

            xp, enemy_hp_left, magic_type, player_hp_left, new_mana, msg1, msg2, msg3, msg4 = result

            # Clean messages
            clean_msg1 = msg1.replace('\033[91m', '').replace('\033[35m', '').replace('\033[38;5;208m', '').replace(
                '\033[92m', '').replace('\033[0m', '').replace('\n', '').strip()
            clean_msg2 = msg2.replace('\033[91m', '').replace('\033[35m', '').replace('\033[38;5;208m', '').replace(
                '\033[92m', '').replace('\033[0m', '').replace('\n', '').strip()
            clean_msg3 = msg3.replace('\033[91m', '').replace('\033[35m', '').replace('\033[38;5;208m', '').replace(
                '\033[92m', '').replace('\033[0m', '').replace('\n', '').strip()
            clean_msg4 = msg4.replace('\033[91m', '').replace('\033[35m', '').replace('\033[38;5;208m', '').replace(
                '\033[92m', '').replace('\033[0m', '').replace('\n', '').strip()

            self.combat_messages.extend([
                (clean_msg1, (0, 255, 0)),
                (clean_msg2, (0, 255, 0)),
                (clean_msg3, (0, 255, 0)),
                (clean_msg4, (255, 255, 0))
            ])

            damage = enemy_health - enemy_hp_left
            if damage > 0:
                self.damage_texts.append(DamageText(WIDTH // 2 + 70, 200, f"-{damage}", DAMAGE_TEXT_COLOR))

            player_damage = player_health - player_hp_left  # Calculate damage taken
            if player_damage > 0:
                self.damage_texts.append(DamageText(120, 200, f"-{player_damage}", (255, 0, 0)))

            self.loaded_player_attr[f"{self.original_magic_key}_Mana"] = new_mana
            self.loaded_player_attr["Hit_Points"] = player_hp_left  # This should update player HP
            self.loaded_enemy_attr["Hit_Points"] = enemy_hp_left

            if enemy_hp_left <= 0:
                # Reset enemy starting HP when combat ends (ADDED)
                if hasattr(self, 'enemy_starting_hp'):
                    delattr(self, 'enemy_starting_hp')

                if is_boss:
                    self.combat_messages.append(("🏆 BOSS DEFEATED! LEGENDARY VICTORY! 🏆", (255, 215, 0)))
                    # Boss gives much more XP and credits with dice rolls
                    boss_xp_dice = roll_dice(6, 8)  # Roll 6d8 for boss XP
                    boss_xp = sum(boss_xp_dice) * (10 + enemy_level * 2)  # Level scaling
                    boss_credits_dice = roll_dice(4, 10)  # Roll 4d10 for boss credits
                    boss_credits = sum(boss_credits_dice) * (50 + enemy_level * 10)

                    self.loaded_player_attr["Credits"] += boss_credits
                    current_xp = self.loaded_player_attr.get("Experience_Points", 0)
                    self.loaded_player_attr["Experience_Points"] = current_xp + boss_xp

                    # Store boss victory info for victory screen
                    self.boss_victory_message = f"💀 {enemy_name} has been vanquished! 💀"
                    self.boss_xp_gained = boss_xp
                    self.boss_credits_gained = boss_credits

                    self.combat_messages.append(
                        (f"💰 Gained {boss_credits} credits! (Rolled {boss_credits_dice}) 💰", (255, 215, 0)))
                    self.combat_messages.append((f"⭐ Gained {boss_xp} XP! (Rolled {boss_xp_dice}) ⭐", (255, 215, 0)))

                    # Check for level up
                    self.level_up_check()

                    # Reset world after boss defeat
                    self.boss_fight_triggered = False
                    self.boss_positions = []

                    # Save character progress
                    if self.player_file:
                        with open(self.player_file, 'w') as f:
                            json.dump(self.loaded_player_attr, f, indent=4)

                    return 4  # Special return code for boss victory
                else:
                    self.combat_messages.append(("Victory! Enemy defeated!", (0, 255, 0)))
                    current_xp = self.loaded_player_attr.get("Experience_Points", 0)
                    # Scale XP with enemy level
                    final_xp = xp * max(1, enemy_level)
                    self.loaded_player_attr["Experience_Points"] = current_xp + final_xp

                    # Check for level up
                    self.level_up_check()

                if self.player_file:
                    with open(self.player_file, 'w') as f:
                        json.dump(self.loaded_player_attr, f, indent=4)
                return 1

            if player_hp_left > 0:
                enemy_rolls = roll_dice(1, 20)

                # Boss enemies get enhanced attacks
                if is_boss:
                    # Boss gets multiple attacks or enhanced damage
                    for attack_round in range(1 if random.randint(1, 3) == 1 else 2):
                        enemy_result = gui_enemy_fight(
                            player_hit_points=player_hp_left,
                            roll=enemy_rolls[0] + (5 if is_boss else 0),
                            player_aspect1=player_aspect1,
                            player_name=player_name,
                            magic_type=magic_type,
                            demon_name=enemy_name,
                            demon_hit_points=enemy_hp_left,
                            demon_aspect1=enemy_aspect1,
                            mana_level=new_mana,
                            player_stats=player_stats  # ADD THIS LINE
                        )

                        player_hp_left, new_mana, enemy_message = enemy_result

                        if attack_round > 0:
                            enemy_message = f"🔥 BOSS FURY ATTACK! {enemy_message}"

                        clean_enemy_msg = enemy_message.replace('\033[91m', '').replace('\033[35m', '').replace(
                            '\033[38;5;208m', '').replace('\033[92m', '').replace('\033[0m', '').replace('\n',
                                                                                                         ' ').strip()

                        self.combat_messages.append((clean_enemy_msg, (255, 0, 0)))

                        if player_hp_left <= 0:
                            break
                else:
                    enemy_result = gui_enemy_fight(
                        player_hit_points=player_hp_left,
                        roll=enemy_rolls[0] + (5 if is_boss else 0),
                        player_aspect1=player_aspect1,
                        player_name=player_name,
                        magic_type=magic_type,
                        demon_name=enemy_name,
                        demon_hit_points=enemy_hp_left,
                        demon_aspect1=enemy_aspect1,
                        mana_level=new_mana,
                        player_stats=player_stats  # ADD THIS LINE
                    )

                    player_hp_left, new_mana, enemy_message = enemy_result

                    clean_enemy_msg = enemy_message.replace('\033[91m', '').replace('\033[35m', '').replace(
                        '\033[38;5;208m', '').replace('\033[92m', '').replace('\033[0m', '').replace('\n',
                                                                                                     ' ').strip()

                    self.combat_messages.append((clean_enemy_msg, (255, 0, 0)))

                # Add player damage text
                player_damage = self.loaded_player_attr["Hit_Points"] - player_hp_left
                if player_damage > 0:
                    self.damage_texts.append(DamageText(120, 200, f"-{player_damage}", (255, 0, 0)))

                # UPDATE PLAYER STATS - This is crucial!
                self.loaded_player_attr["Hit_Points"] = player_hp_left
                self.loaded_player_attr[f"{self.original_magic_key}_Mana"] = new_mana

                if player_hp_left <= 0:
                    if is_boss:
                        self.combat_messages.append(
                            ("💀 Defeated by the Boss! Your legend ends here... 💀", (255, 0, 0)))
                    else:
                        self.combat_messages.append(("You have been defeated!", (255, 0, 0)))
                    if self.player_file:
                        with open(self.player_file, 'w') as f:
                            json.dump(self.loaded_player_attr, f, indent=4)
                    return 3

            return 0

        except Exception as e:
            print(f"Combat error: {e}")
            self.combat_messages.append((f"Combat error occurred!", (255, 0, 0)))
            return 2

    def handle_player_death(self):
        """Handle player death - respawn with penalty"""
        self.player_pos = [WIDTH // 2, HEIGHT // 2]
        level = self.loaded_player_attr.get("Level", 1)

        # Respawn with reduced stats
        self.loaded_player_attr["Hit_Points"] = self.get_max_hp_for_level(level) // 2
        self.loaded_player_attr[f"{self.original_magic_key}_Mana"] = self.get_max_mana_for_level(level) // 2

        current_credits = self.loaded_player_attr.get("Credits", 0)
        penalty = max(50, current_credits // 5)  # Lose 20% of credits, minimum 50
        self.loaded_player_attr["Credits"] = max(0, current_credits - penalty)

        if self.player_file:
            with open(self.player_file, 'w') as f:
                json.dump(self.loaded_player_attr, f, indent=4)

        return f"You died! Lost {penalty} credits. Respawned with reduced health and mana."

    def run(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True

        while running:
            self.menu_animation_timer += 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    # Handle inventory access from game board
                    if event.key == pygame.K_i and self.loaded_player_attr and self.current_state == GameState.GAME_BOARD:
                        self.previous_state = self.current_state
                        self.current_state = GameState.INVENTORY
                        self.selected_inventory_item = 0
                        continue

                    # Handle character sheet access from game board
                    if event.key == pygame.K_c and self.loaded_player_attr and self.current_state == GameState.GAME_BOARD:
                        self.previous_state = self.current_state
                        self.current_state = GameState.CHARACTER_SHEET
                        continue

                    # Handle world selection access from game board
                    if event.key == pygame.K_b and self.loaded_player_attr and self.current_state == GameState.GAME_BOARD:
                        self.previous_state = self.current_state
                        self.current_state = GameState.WORLD_SELECT
                        self.selected_book_option = 0
                        self.selected_chapter_option = 0
                        self.world_select_panel = 0
                        continue

                    result = self.handle_keypress(event.key)
                    if not result:
                        running = False

            self.update()
            self.draw()
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()

    def handle_keypress(self, key):
        """Handle keyboard input based on current state"""
        if self.current_state == GameState.OPENING:
            if key == pygame.K_h:
                self.current_state = GameState.HELP
                self.help_section = 0
            else:
                self.current_state = GameState.MAIN_MENU

        elif self.current_state == GameState.MAIN_MENU:
            menu_options = ["Start Game", "Help", "Quit"]
            if key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(menu_options)
            elif key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(menu_options)
            elif key == pygame.K_RETURN:
                if self.selected_option == 0:  # Start Game
                    self.current_state = GameState.BOOK_SELECTION
                elif self.selected_option == 1:  # Help
                    self.current_state = GameState.HELP
                    self.help_section = 0
                elif self.selected_option == 2:  # Quit
                    return False
            elif key == pygame.K_ESCAPE:
                return False

        elif self.current_state == GameState.HELP:
            if key == pygame.K_ESCAPE:
                # Return to previous state (main menu or game)
                if hasattr(self, 'previous_state') and self.previous_state == GameState.GAME_BOARD:
                    self.current_state = GameState.GAME_BOARD
                else:
                    self.current_state = GameState.MAIN_MENU
            elif key == pygame.K_LEFT:
                self.help_section = (self.help_section - 1) % len(HELP_CONTENT)
            elif key == pygame.K_RIGHT:
                self.help_section = (self.help_section + 1) % len(HELP_CONTENT)

        elif self.current_state == GameState.BOOK_SELECTION:
            books = self.get_book_list()
            if books:
                if key == pygame.K_UP:
                    self.selected_book_option = (self.selected_book_option - 1) % len(books)
                elif key == pygame.K_DOWN:
                    self.selected_book_option = (self.selected_book_option + 1) % len(books)
                elif key == pygame.K_RETURN:
                    book_file = books[self.selected_book_option]
                    try:
                        book_path = os.path.join("Books", book_file)
                        with open(book_path, 'r') as f:
                            self.loaded_book_attr = json.load(f)
                        self.current_state = GameState.CHAPTER_SELECTION
                        self.selected_chapter_option = 0
                    except:
                        print(f"Failed to load book: {book_file}")
                elif key == pygame.K_ESCAPE:
                    self.current_state = GameState.MAIN_MENU
            else:
                if key == pygame.K_RETURN or key == pygame.K_ESCAPE:
                    self.current_state = GameState.CHARACTER_SELECTION

        elif self.current_state == GameState.CHAPTER_SELECTION:
            chapters = self.get_chapters_from_book()
            if chapters:
                if key == pygame.K_UP:
                    self.selected_chapter_option = (self.selected_chapter_option - 1) % len(chapters)
                elif key == pygame.K_DOWN:
                    self.selected_chapter_option = (self.selected_chapter_option + 1) % len(chapters)
                elif key == pygame.K_RETURN:
                    self.current_state = GameState.CHARACTER_SELECTION
                    self.selected_option = 0
                elif key == pygame.K_ESCAPE:
                    self.current_state = GameState.BOOK_SELECTION
            else:
                if key == pygame.K_RETURN or key == pygame.K_ESCAPE:
                    self.current_state = GameState.CHARACTER_SELECTION

        elif self.current_state == GameState.CHARACTER_SELECTION:
            chars = self.get_character_list()
            if key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(chars)
            elif key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(chars)
            elif key == pygame.K_RETURN:
                if chars[self.selected_option] == "New Character":
                    self.current_state = GameState.NEW_CHARACTER
                else:
                    char_file = chars[self.selected_option]
                    try:
                        char_path = os.path.join("Characters", char_file)
                        with open(char_path, 'r') as f:
                            self.loaded_player_attr = json.load(f)
                        self.player_file = char_path
                        self.current_state = GameState.MAGIC_SELECTION
                        self.selected_magic_option = 0
                    except:
                        print(f"Failed to load character: {char_file}")
            elif key == pygame.K_ESCAPE:
                self.current_state = GameState.CHAPTER_SELECTION if self.loaded_book_attr else GameState.BOOK_SELECTION

        elif self.current_state == GameState.NEW_CHARACTER:
            if key == pygame.K_ESCAPE:
                # Reset character creator when leaving
                self.character_creator = CharacterCreator()
                self.current_state = GameState.CHARACTER_SELECTION
            elif key == pygame.K_TAB or key == pygame.K_UP:
                self.character_creator.selected_option = (self.character_creator.selected_option - 1) % 6
            elif key == pygame.K_DOWN:
                self.character_creator.selected_option = (self.character_creator.selected_option + 1) % 6
            elif key == pygame.K_LEFT:
                if self.character_creator.selected_option == 1:  # Race selection
                    races = list(self.character_creator.races.keys())
                    current_index = races.index(self.character_creator.selected_race)
                    self.character_creator.selected_race = races[(current_index - 1) % len(races)]
                elif self.character_creator.selected_option == 2:  # Class selection
                    classes = list(self.character_creator.classes.keys())
                    current_index = classes.index(self.character_creator.selected_class)
                    self.character_creator.selected_class = classes[(current_index - 1) % len(classes)]
            elif key == pygame.K_RIGHT:
                if self.character_creator.selected_option == 1:  # Race selection
                    races = list(self.character_creator.races.keys())
                    current_index = races.index(self.character_creator.selected_race)
                    self.character_creator.selected_race = races[(current_index + 1) % len(races)]
                elif self.character_creator.selected_option == 2:  # Class selection
                    classes = list(self.character_creator.classes.keys())
                    current_index = classes.index(self.character_creator.selected_class)
                    self.character_creator.selected_class = classes[(current_index + 1) % len(classes)]
            elif key == pygame.K_r:
                # Re-roll stats
                self.character_creator.stats = self.character_creator.roll_new_stats()
            elif key == pygame.K_RETURN:
                if self.character_creator.selected_option == 0:
                    # Name input - do nothing special, typing handles it
                    pass
                elif self.character_creator.selected_option == 1:
                    # Cycle race
                    races = list(self.character_creator.races.keys())
                    current_index = races.index(self.character_creator.selected_race)
                    self.character_creator.selected_race = races[(current_index + 1) % len(races)]
                elif self.character_creator.selected_option == 2:
                    # Cycle class
                    classes = list(self.character_creator.classes.keys())
                    current_index = classes.index(self.character_creator.selected_class)
                    self.character_creator.selected_class = classes[(current_index + 1) % len(classes)]
                elif self.character_creator.selected_option == 3:
                    # Re-roll stats
                    self.character_creator.stats = self.character_creator.roll_new_stats()
                elif self.character_creator.selected_option == 4:
                    # Create character
                    if len(self.character_creator.name.strip()) > 0:
                        new_char = self.create_character_from_creator()
                        if new_char:
                            # Save character
                            os.makedirs("Characters", exist_ok=True)
                            char_file = os.path.join("Characters", f"{new_char['Name']}.json")
                            # Check if character already exists
                            counter = 1
                            original_name = new_char['Name']
                            while os.path.exists(char_file):
                                new_char['Name'] = f"{original_name}_{counter}"
                                char_file = os.path.join("Characters", f"{new_char['Name']}.json")
                                counter += 1
                            with open(char_file, 'w') as f:

                                json.dump(new_char, f, indent=4)

                            self.loaded_player_attr = new_char

                            self.player_file = char_file

                            # Reset character creator

                            self.character_creator = CharacterCreator()

                            self.current_state = GameState.MAGIC_SELECTION

                            self.selected_magic_option = 0

                elif self.character_creator.selected_option == 5:

                    # Back

                    self.character_creator = CharacterCreator()

                    self.current_state = GameState.CHARACTER_SELECTION


            # Handle text input for character name

            elif self.character_creator.selected_option == 0:

                if key == pygame.K_BACKSPACE:

                    self.character_creator.name = self.character_creator.name[:-1]

                else:

                    # Handle regular character input

                    char = pygame.key.name(key)

                    if len(char) == 1 and len(self.character_creator.name) < self.character_creator.max_name_length:

                        # Check if shift is held for uppercase

                        mods = pygame.key.get_pressed()

                        if mods[pygame.K_LSHIFT] or mods[pygame.K_RSHIFT]:

                            if char.isalpha():

                                char = char.upper()

                            elif char.isdigit():

                                # Handle shifted number symbols

                                shift_numbers = {'1': '!', '2': '@', '3': '#', '4': '$', '5': '%',

                                                 '6': '^', '7': '&', '8': '*', '9': '(', '0': ')'}

                                char = shift_numbers.get(char, char)

                        # Only allow alphanumeric characters, spaces, and basic punctuation

                        if char.isalnum() or char in [' ', '-', '_', "'", '.']:
                            self.character_creator.name += char

        elif self.current_state == GameState.MAGIC_SELECTION:
            magic_aspects = [v for k, v in self.loaded_player_attr.items()
                             if k.startswith("Aspect") and not k.endswith("_Mana") and v]
            if magic_aspects:
                if key == pygame.K_UP:
                    self.selected_magic_option = (self.selected_magic_option - 1) % len(magic_aspects)
                elif key == pygame.K_DOWN:
                    self.selected_magic_option = (self.selected_magic_option + 1) % len(magic_aspects)
                elif key == pygame.K_RETURN:
                    self.original_magic_key = f"Aspect{self.selected_magic_option + 1}"
                    self.current_state = GameState.WEAPON_SELECTION
                    self.selected_weapon_option = 0
                elif key == pygame.K_ESCAPE:
                    self.current_state = GameState.CHARACTER_SELECTION

        elif self.current_state == GameState.WEAPON_SELECTION:
            weapons = [v for k, v in self.loaded_player_attr.items()
                       if k.startswith("Weapon") and v]
            if weapons:
                if key == pygame.K_UP:
                    self.selected_weapon_option = (self.selected_weapon_option - 1) % len(weapons)
                elif key == pygame.K_DOWN:
                    self.selected_weapon_option = (self.selected_weapon_option + 1) % len(weapons)
                elif key == pygame.K_RETURN:
                    # Setup initial world and enter game
                    chapter_info = {}
                    if self.loaded_book_attr:
                        chapters = self.get_chapters_from_book()
                        if chapters and self.selected_chapter_option < len(chapters):
                            selected_chapter = chapters[self.selected_chapter_option]
                            self.current_chapter_name = selected_chapter
                            # Find chapter level
                            for key, value in self.loaded_book_attr.items():
                                if key.startswith("Chapter") and value == selected_chapter:
                                    level_key = f"{key}_Level"
                                    enemy_key = f"{key}_Enemy_Type"
                                    chapter_info["Level"] = self.loaded_book_attr.get(level_key, 1)
                                    chapter_info["Enemy_Type"] = self.loaded_book_attr.get(enemy_key, "demon")
                                    break
                        if hasattr(self, 'selected_book_option'):
                            books = self.get_book_list()
                            if books and self.selected_book_option < len(books):
                                self.current_book_name = books[self.selected_book_option].replace(".json", "").replace(
                                    "_", " ").title()

                    self.setup_world(chapter_info)
                    self.current_state = GameState.GAME_BOARD
                elif key == pygame.K_ESCAPE:
                    self.current_state = GameState.MAGIC_SELECTION

        elif self.current_state == GameState.CHARACTER_SHEET:
            if key == pygame.K_ESCAPE:
                self.current_state = self.previous_state if hasattr(self, 'previous_state') else GameState.GAME_BOARD

        elif self.current_state == GameState.WORLD_SELECT:
            books = self.get_book_list()
            chapters = self.get_chapters_from_book()

            if key == pygame.K_ESCAPE:
                self.current_state = self.previous_state
            elif key == pygame.K_LEFT:
                self.world_select_panel = 0  # Switch to book panel
            elif key == pygame.K_RIGHT:
                self.world_select_panel = 1  # Switch to chapter panel
            elif key == pygame.K_UP:
                if self.world_select_panel == 0 and books:  # Book panel
                    self.selected_book_option = (self.selected_book_option - 1) % len(books)
                    # Load book when selection changes
                    book_file = books[self.selected_book_option]
                    try:
                        book_path = os.path.join("Books", book_file)
                        with open(book_path, 'r') as f:
                            self.loaded_book_attr = json.load(f)
                        self.selected_chapter_option = 0
                    except:
                        pass
                elif self.world_select_panel == 1 and chapters:  # Chapter panel
                    self.selected_chapter_option = (self.selected_chapter_option - 1) % len(chapters)
            elif key == pygame.K_DOWN:
                if self.world_select_panel == 0 and books:  # Book panel
                    self.selected_book_option = (self.selected_book_option + 1) % len(books)
                    # Load book when selection changes
                    book_file = books[self.selected_book_option]
                    try:
                        book_path = os.path.join("Books", book_file)
                        with open(book_path, 'r') as f:
                            self.loaded_book_attr = json.load(f)
                        self.selected_chapter_option = 0
                    except:
                        pass
                elif self.world_select_panel == 1 and chapters:  # Chapter panel
                    self.selected_chapter_option = (self.selected_chapter_option + 1) % len(chapters)
            elif key == pygame.K_RETURN:
                if books and self.loaded_book_attr and chapters:
                    book_file = books[self.selected_book_option]
                    if self.load_book_and_chapter(book_file, self.selected_chapter_option):
                        self.current_state = GameState.GAME_BOARD
                        # Move player to center to avoid immediate interactions
                        self.player_pos = [WIDTH // 2, HEIGHT // 2]

        elif self.current_state == GameState.BOSS_VICTORY:
            if key == pygame.K_SPACE:
                # Choose new adventure
                self.current_state = GameState.WORLD_SELECT
                self.selected_book_option = 0
                self.selected_chapter_option = 0
                self.world_select_panel = 0
            elif key == pygame.K_c:
                # Continue in current world - regenerate enemies and loot
                self.setup_world()
                self.current_state = GameState.GAME_BOARD
                self.player_pos = [WIDTH // 2, HEIGHT // 2]
            elif key == pygame.K_ESCAPE:
                # Return to main menu
                self.current_state = GameState.MAIN_MENU
                self.selected_option = 0

        elif self.current_state == GameState.GAME_BOARD:
            if key == pygame.K_ESCAPE:
                return False
            elif key == pygame.K_h:
                self.previous_state = self.current_state
                self.current_state = GameState.HELP
                self.help_section = 0
            elif key == pygame.K_m and self.music_available:
                if self.music_playing:
                    pygame.mixer.music.pause()
                else:
                    if not pygame.mixer.music.get_busy():
                        pygame.mixer.music.play(-1)
                    else:
                        pygame.mixer.music.unpause()
                self.music_playing = not self.music_playing


        elif self.current_state == GameState.STORE:

            if key == pygame.K_ESCAPE:

                self.current_state = GameState.GAME_BOARD

                self.move_player_away_from_interaction()

                self.store_scroll_offset = 0  # Reset scroll when leaving

            elif key == pygame.K_UP:

                self.selected_store_item = (self.selected_store_item - 1) % len(self.store.items)

            elif key == pygame.K_DOWN:

                self.selected_store_item = (self.selected_store_item + 1) % len(self.store.items)

            elif key == pygame.K_PAGEUP:

                # Scroll up by page

                self.store_scroll_offset = max(0, self.store_scroll_offset - self.items_per_page)

                self.selected_store_item = max(0, self.selected_store_item - self.items_per_page)

            elif key == pygame.K_PAGEDOWN:

                # Scroll down by page

                max_scroll = max(0, len(self.store.items) - self.items_per_page)

                self.store_scroll_offset = min(max_scroll, self.store_scroll_offset + self.items_per_page)

                self.selected_store_item = min(len(self.store.items) - 1,
                                               self.selected_store_item + self.items_per_page)

            elif key == pygame.K_HOME:

                # Go to first item

                self.selected_store_item = 0

                self.store_scroll_offset = 0

            elif key == pygame.K_END:

                # Go to last item

                self.selected_store_item = len(self.store.items) - 1

                max_scroll = max(0, len(self.store.items) - self.items_per_page)

                self.store_scroll_offset = max_scroll

            elif key == pygame.K_RETURN:

                if self.loaded_player_attr and self.selected_store_item < len(self.store.items):

                    item = self.store.items[self.selected_store_item]

                    success, message = self.purchase_item(item)

                    print(message)  # You might want to display this in-game instead

                    if success and self.player_file:
                        with open(self.player_file, 'w') as f:
                            json.dump(self.loaded_player_attr, f, indent=4)

        elif self.current_state == GameState.REST:
            if key == pygame.K_ESCAPE:
                self.current_state = GameState.GAME_BOARD
                self.move_player_away_from_interaction()
                self.rest_message = ""
            elif key == pygame.K_SPACE:
                success, message = self.rest_player()
                self.rest_message = message
                self.rest_timer = 120
                if success and self.player_file:
                    with open(self.player_file, 'w') as f:
                        json.dump(self.loaded_player_attr, f, indent=4)

        elif self.current_state == GameState.INVENTORY:
            inventory = self.loaded_player_attr.get("Inventory", {})
            inventory_items = list(inventory.items())

            if key == pygame.K_ESCAPE:
                self.current_state = self.previous_state if hasattr(self, 'previous_state') else GameState.GAME_BOARD
            elif inventory_items:
                if key == pygame.K_UP:
                    self.selected_inventory_item = (self.selected_inventory_item - 1) % len(inventory_items)
                elif key == pygame.K_DOWN:
                    self.selected_inventory_item = (self.selected_inventory_item + 1) % len(inventory_items)
                elif key == pygame.K_RETURN:
                    item_name = inventory_items[self.selected_inventory_item][0]
                    success, message = self.use_item_from_inventory(item_name)
                    print(message)
                    if success and self.player_file:
                        with open(self.player_file, 'w') as f:
                            json.dump(self.loaded_player_attr, f, indent=4)
                        if "HP" in message:
                            self.damage_texts.append(DamageText(150, 200, message, HEAL_TEXT_COLOR))
                        elif "MP" in message:
                            self.damage_texts.append(DamageText(150, 230, message, (0, 150, 255)))

        elif self.current_state == GameState.FIGHT:
            player_alive = self.loaded_player_attr.get("Hit_Points", 0) > 0
            enemy_alive = self.loaded_enemy_attr.get("Hit_Points", 0) > 0

            if key == pygame.K_SPACE:
                if not player_alive:
                    death_message = self.handle_player_death()
                    print(death_message)
                    self.current_state = GameState.GAME_BOARD
                elif not enemy_alive:
                    self.current_state = GameState.GAME_BOARD
                else:
                    result = self.enhanced_fight_logic()
                    if result == 4:  # Boss victory
                        self.current_state = GameState.BOSS_VICTORY

            elif key == pygame.K_ESCAPE:
                if not player_alive:
                    death_message = self.handle_player_death()
                    print(death_message)
                elif not enemy_alive:
                    pass
                else:
                    self.combat_messages.append(("You fled from combat!", (255, 255, 0)))
                self.current_state = GameState.GAME_BOARD

            elif key == pygame.K_h:
                inventory = self.loaded_player_attr.get("Inventory", {})
                health_potions = [item for item in inventory.keys() if "Health Potion" in item]
                if health_potions:
                    success, message = self.use_item_from_inventory(health_potions[0])
                    if success:
                        self.combat_messages.append((message, HEAL_TEXT_COLOR))
                        self.damage_texts.append(DamageText(120, 200, message, HEAL_TEXT_COLOR))
                        if self.player_file:
                            with open(self.player_file, 'w') as f:
                                json.dump(self.loaded_player_attr, f, indent=4)
                    else:
                        self.combat_messages.append(("No health potions available!", (255, 0, 0)))
                else:
                    self.combat_messages.append(("No health potions in inventory!", (255, 0, 0)))

            elif key == pygame.K_m:
                inventory = self.loaded_player_attr.get("Inventory", {})
                mana_potions = [item for item in inventory.keys() if "Mana Potion" in item]
                if mana_potions:
                    success, message = self.use_item_from_inventory(mana_potions[0])
                    if success:
                        self.combat_messages.append((message, (0, 150, 255)))
                        self.damage_texts.append(DamageText(120, 230, message, (0, 150, 255)))
                        if self.player_file:
                            with open(self.player_file, 'w') as f:
                                json.dump(self.loaded_player_attr, f, indent=4)
                    else:
                        self.combat_messages.append(("No mana potions available!", (255, 0, 0)))
                else:
                    self.combat_messages.append(("No mana potions in inventory!", (255, 0, 0)))

        return True

    def update(self):
        """Update game logic"""
        if self.rest_timer > 0:
            self.rest_timer -= 1
            if self.rest_timer <= 0:
                self.rest_message = ""

        # Update particles
        self.particles.update()

        if self.current_state == GameState.GAME_BOARD:
            keys = pygame.key.get_pressed()

            # Player movement
            if keys[pygame.K_LEFT]:
                self.player_pos[0] -= self.player_speed
            if keys[pygame.K_RIGHT]:
                self.player_pos[0] += self.player_speed
            if keys[pygame.K_UP]:
                self.player_pos[1] -= self.player_speed
            if keys[pygame.K_DOWN]:
                self.player_pos[1] += self.player_speed

            # Keep player in bounds
            self.player_pos[0] = max(0, min(WIDTH - self.player_size, self.player_pos[0]))
            self.player_pos[1] = max(0, min(HEIGHT - self.player_size, self.player_pos[1]))

            # Check collisions with enemies
            enemy_collision, enemy_obj = self.handle_collision(self.player_pos, self.enemy_positions)
            if enemy_collision:
                enemy_obj["active"] = False
                self.last_interaction_pos = enemy_obj["pos"]

                # Reset enemy starting HP tracking for new fight (ADDED)
                if hasattr(self, 'enemy_starting_hp'):
                    delattr(self, 'enemy_starting_hp')

                self.loaded_enemy_attr = self.create_scaled_enemy()
                self.current_state = GameState.FIGHT
                self.action_triggered = False
                self.combat_messages = []
                self.damage_texts = []

            # Check collisions with loot
            loot_collision, loot_obj = self.handle_collision(self.player_pos, self.loot_positions)
            if loot_collision:
                loot_obj["active"] = False
                # Use dice roll for loot credits - scale with book level
                loot_dice = roll_dice(2, 6)  # Roll 2d6 for loot
                credits = sum(loot_dice) * (10 + self.current_book_level * 5)  # Level scaling
                self.loaded_player_attr["Credits"] += credits

                # Add visual feedback with dice roll info
                self.damage_texts.append(DamageText(self.player_pos[0], self.player_pos[1],
                                                    f"+{credits} Credits! (Rolled {loot_dice})", GOLD))

                # Add particles for loot collection
                for _ in range(10):
                    self.particles.add_particle(self.player_pos[0] + 15, self.player_pos[1] + 15, GOLD)

                if self.player_file:
                    with open(self.player_file, 'w') as f:
                        json.dump(self.loaded_player_attr, f, indent=4)

            # Check collisions with store
            store_collision, store_obj = self.handle_collision(self.player_pos, self.store_positions)
            if store_collision:
                self.last_interaction_pos = store_obj["pos"]
                self.current_state = GameState.STORE
                self.selected_store_item = 0

            # Check collisions with rest areas
            player_rect = pygame.Rect(self.player_pos[0], self.player_pos[1], self.player_size, self.player_size)
            for rest_area in self.rest_areas:
                if player_rect.colliderect(rest_area.rect):
                    self.last_interaction_pos = (rest_area.x, rest_area.y)
                    self.current_state = GameState.REST
                    self.rest_message = ""

            # Check collisions with boss
            if self.boss_fight_triggered:
                boss_collision, boss_obj = self.handle_collision(self.player_pos, self.boss_positions)
                if boss_collision:
                    boss_obj["active"] = False
                    self.last_interaction_pos = boss_obj["pos"]
                    # Load boss enemy data
                    try:
                        boss_file = os.path.join("Enemies", "boss_demon.json")
                        with open(boss_file, 'r') as f:
                            base_boss = json.load(f)
                        # Override with scaled boss data
                        self.loaded_enemy_attr = self.create_scaled_boss()
                    except:
                        # Create a scaled boss if file doesn't exist
                        self.loaded_enemy_attr = self.create_scaled_boss()

                    self.current_state = GameState.FIGHT
                    self.action_triggered = False
                    self.combat_messages = [("💀 A POWERFUL BOSS APPEARS! 💀", (255, 0, 0))]
                    self.damage_texts = []

    def draw(self):
        """Draw current state"""
        if self.current_state == GameState.OPENING:
            self.draw_enhanced_opening()

        elif self.current_state == GameState.MAIN_MENU:
            menu_options = ["🎮 Start Game", "❓ Help", "🚪 Quit"]
            self.draw_enhanced_menu("MAGITECH RPG", menu_options, self.selected_option,
                                    "Choose your destiny, brave adventurer!")

        elif self.current_state == GameState.HELP:
            self.draw_help_screen()

        elif self.current_state == GameState.BOOK_SELECTION:
            books = self.get_book_list()
            if books:
                self.draw_enhanced_menu("📚 Select Your Adventure Book", books, self.selected_book_option,
                                        "Each book contains different magical worlds to explore")
            else:
                screen.fill(MENU_BG)
                title = large_font.render("📚 No Adventure Books Found", True, WHITE)
                title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 3))
                screen.blit(title, title_rect)

                subtitle = font.render("Create a Books directory with .json adventure files", True, MENU_TEXT)
                subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                screen.blit(subtitle, subtitle_rect)

                continue_text = small_font.render("Press ENTER to continue with default adventure", True, MENU_SELECTED)
                continue_rect = continue_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
                screen.blit(continue_text, continue_rect)

        elif self.current_state == GameState.CHAPTER_SELECTION:
            chapters = self.get_chapters_from_book()
            if chapters:
                # Add level info to chapter names
                chapter_display = []
                for chapter in chapters:
                    level = self.get_chapter_level(chapter)
                    chapter_display.append(f"{chapter} (Level {level})")
                self.draw_enhanced_menu("📖 Choose Your Chapter", chapter_display, self.selected_chapter_option,
                                        "Each chapter offers unique challenges and rewards")
            else:
                screen.fill(MENU_BG)
                title = large_font.render("📖 No Chapters Available", True, WHITE)
                title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                screen.blit(title, title_rect)

        elif self.current_state == GameState.CHARACTER_SELECTION:
            chars = self.get_character_list()
            self.draw_enhanced_menu("⚔️ Choose Your Hero", chars, self.selected_option,
                                    "Select an existing character or create a new one")


        elif self.current_state == GameState.NEW_CHARACTER:
            self.draw_enhanced_character_creation()

        elif self.current_state == GameState.MAGIC_SELECTION:
            if self.loaded_player_attr:
                magic_aspects = [v for k, v in self.loaded_player_attr.items()
                                 if k.startswith("Aspect") and not k.endswith("_Mana") and v]
                if magic_aspects:
                    self.draw_enhanced_menu("🔮 Choose Your Magic Aspect", magic_aspects, self.selected_magic_option,
                                            "Your magical aspect determines your combat abilities")

        elif self.current_state == GameState.WEAPON_SELECTION:
            if self.loaded_player_attr:
                weapons = [v for k, v in self.loaded_player_attr.items()
                           if k.startswith("Weapon") and v]
                if weapons:
                    self.draw_enhanced_menu("⚔️ Choose Your Weapon", weapons, self.selected_weapon_option,
                                            "Your weapon will aid you in battle")

        elif self.current_state == GameState.CHARACTER_SHEET:
            self.draw_character_sheet()

        elif self.current_state == GameState.WORLD_SELECT:
            self.draw_world_selection_screen()

        elif self.current_state == GameState.BOSS_VICTORY:
            self.draw_boss_victory_screen()

        elif self.current_state == GameState.GAME_BOARD:
            # Draw background
            screen.blit(self.background_image, (0, 0))

            # Draw particles
            self.particles.draw(screen)

            # Draw enhanced UI bars
            self.draw_enhanced_ui_bars()

            # Draw player character with glow effect
            glow_surface = pygame.Surface((self.player_size + 6, self.player_size + 6))
            glow_surface.fill((100, 150, 255))
            glow_surface.set_alpha(100)
            screen.blit(glow_surface, (self.player_pos[0] - 3, self.player_pos[1] - 3))
            screen.blit(self.character_image, self.player_pos)

            # Draw enemies with enhanced visuals - scale appearance with level
            for enemy in self.enemy_positions:
                if enemy["active"]:
                    # Pulsing red glow for active enemies - stronger for higher level
                    pulse_intensity = 30 + (self.current_book_level * 10)
                    pulse = int(50 + pulse_intensity * abs(math.sin(self.menu_animation_timer * 0.1)))
                    glow_surface = pygame.Surface((40, 40))
                    glow_surface.fill((255, 50, 50))
                    glow_surface.set_alpha(pulse)
                    screen.blit(glow_surface, (enemy["pos"][0] - 5, enemy["pos"][1] - 5))
                    screen.blit(self.target_image, enemy["pos"])

                    # Draw level indicator for higher level enemies
                    if self.current_book_level > 1:
                        level_text = small_font.render(f"Lv.{self.current_book_level}", True, WHITE)
                        screen.blit(level_text, (enemy["pos"][0], enemy["pos"][1] - 15))
                else:
                    screen.blit(self.inactive_image, enemy["pos"])

            # Draw loot with sparkle effect
            for loot in self.loot_positions:
                if loot["active"]:
                    # Animated sparkle effect
                    sparkle_offset = int(5 * math.sin(self.menu_animation_timer * 0.15))
                    pygame.draw.circle(screen, GOLD,
                                       (loot["pos"][0] + 15, loot["pos"][1] + 15), 15 + sparkle_offset // 2)
                    pygame.draw.circle(screen, BLACK,
                                       (loot["pos"][0] + 15, loot["pos"][1] + 15), 15 + sparkle_offset // 2, 2)

                    # Add sparkle particles occasionally
                    if self.menu_animation_timer % 20 == 0:
                        self.particles.add_particle(loot["pos"][0] + 15, loot["pos"][1] + 15, GOLD)

            # Draw stores with enhanced visuals
            for store in self.store_positions:
                if store["active"]:
                    store_rect = pygame.Rect(store["pos"][0], store["pos"][1], 60, 60)
                    self.draw_gradient_rect(screen, (128, 0, 128), (200, 50, 200), store_rect)
                    pygame.draw.rect(screen, WHITE, store_rect, 3)

                    # Animated dollar sign
                    pulse = int(5 * abs(math.sin(self.menu_animation_timer * 0.1)))
                    store_font = pygame.font.Font(None, 36 + pulse)
                    dollar_text = store_font.render("$", True, GOLD)
                    dollar_rect = dollar_text.get_rect(center=(store["pos"][0] + 30, store["pos"][1] + 30))
                    screen.blit(dollar_text, dollar_rect)

                    shop_font = pygame.font.Font(None, 16)
                    shop_text = shop_font.render("SHOP", True, WHITE)
                    shop_rect = shop_text.get_rect(center=(store["pos"][0] + 30, store["pos"][1] - 10))
                    screen.blit(shop_text, shop_rect)

            # Draw rest areas
            for rest_area in self.rest_areas:
                rest_area.draw(screen)

            # Draw boss if triggered
            if self.boss_fight_triggered:
                for boss in self.boss_positions:
                    if boss["active"]:
                        # Larger, more menacing boss appearance with level scaling
                        boss_pulse = int(
                            (10 + self.current_book_level * 2) * abs(math.sin(self.menu_animation_timer * 0.08)))
                        boss_size = 25 + self.current_book_level * 3
                        pygame.draw.circle(screen, (200, 0, 0),
                                           (boss["pos"][0] + 25, boss["pos"][1] + 25), boss_size + boss_pulse)
                        pygame.draw.circle(screen, (100, 0, 0),
                                           (boss["pos"][0] + 25, boss["pos"][1] + 25),
                                           (boss_size - 5) + boss_pulse // 2)
                        pygame.draw.circle(screen, BLACK,
                                           (boss["pos"][0] + 25, boss["pos"][1] + 25), boss_size + boss_pulse, 3)

                        # Boss level indicator
                        boss_level_text = font.render(f"BOSS Lv.{self.current_book_level + 2}", True, WHITE)
                        screen.blit(boss_level_text, (boss["pos"][0] - 10, boss["pos"][1] - 20))

            # Check if all enemies defeated for boss spawn
            if all(not enemy["active"] for enemy in self.enemy_positions) and not self.boss_fight_triggered:
                self.boss_fight_triggered = True
                self.boss_positions = [{"pos": (WIDTH // 2, HEIGHT // 2), "active": True}]

            # Enhanced instructions panel
            instruction_bg = pygame.Rect(10, HEIGHT - 200, 420, 190)
            self.draw_gradient_rect(screen, UI_BG_COLOR, (50, 50, 50), instruction_bg)
            pygame.draw.rect(screen, UI_BORDER_COLOR, instruction_bg, 2)

            instructions = [
                "🎮 CONTROLS:",
                "← → ↑ ↓  Move character",
                "Walk into enemies to fight",
                "💰 Walk into shop to buy items",
                "🏕️ Walk into tent to rest",
                "🎒 I - Open inventory",
                "📋 C - Character sheet",
                "🗺️ B - Change world/chapter",
                "❓ H - Help system",
                "🎵 M - Toggle music  ESC - Quit"
            ]

            for i, instruction in enumerate(instructions):
                color = MENU_SELECTED if i == 0 else WHITE
                font_to_use = font if i == 0 else small_font
                text = font_to_use.render(instruction, True, color)
                screen.blit(text, (15, HEIGHT - 190 + i * 20))

            # Draw floating damage texts
            for damage_text in self.damage_texts[:]:
                if damage_text.update():
                    damage_text.draw(screen)
                else:
                    self.damage_texts.remove(damage_text)

        elif self.current_state == GameState.STORE:
            self.draw_store_screen()

        elif self.current_state == GameState.REST:
            self.draw_rest_screen()

        elif self.current_state == GameState.INVENTORY:
            self.draw_inventory_screen()

        elif self.current_state == GameState.FIGHT:
            self.draw_enhanced_fight_screen()

        elif self.current_state == GameState.LOOT:
            screen.fill(MENU_BG)

            # Header with gradient
            header_rect = pygame.Rect(0, 0, WIDTH, 150)
            self.draw_gradient_rect(screen, MENU_ACCENT, MENU_HIGHLIGHT, header_rect)

            title = large_font.render("💰 TREASURE FOUND!", True, GOLD)
            title_rect = title.get_rect(center=(WIDTH // 2, 75))
            screen.blit(title, title_rect)

            # Loot panel
            loot_panel = pygame.Rect(WIDTH // 4, 200, WIDTH // 2, 150)
            self.draw_gradient_rect(screen, (60, 40, 20), (100, 70, 30), loot_panel)
            pygame.draw.rect(screen, GOLD, loot_panel, 3)

            loot_text = font.render("You discovered valuable treasure!", True, WHITE)
            loot_rect = loot_text.get_rect(center=(WIDTH // 2, 275))
            screen.blit(loot_text, loot_rect)

            # Instructions
            instruction_rect = pygame.Rect(0, HEIGHT - 60, WIDTH, 60)
            pygame.draw.rect(screen, MENU_ACCENT, instruction_rect)

            continue_text = font.render("SPACE Continue your adventure", True, WHITE)
            continue_rect = continue_text.get_rect(center=(WIDTH // 2, HEIGHT - 30))
            screen.blit(continue_text, continue_rect)


# Main execution
if __name__ == "__main__":
    # Create necessary directories if they don't exist
    directories = ["Books", "Characters", "Enemies", "Images", "Sounds"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

    # Create a sample enemy file if it doesn't exist
    enemy_file = "Enemies/demon_level_1.json"
    if not os.path.exists(enemy_file):
        sample_enemy = {
            "Name": "Fire Demon",
            "Hit_Points": 75,
            "Aspect1": "fire_level_1",
            "Level": 1,
            "Experience_Points": 0
        }
        with open(enemy_file, 'w') as f:
            json.dump(sample_enemy, f, indent=4)
        print(f"Created sample enemy file: {enemy_file}")

    # Create a sample boss file if it doesn't exist
    boss_file = "Enemies/boss_demon.json"
    if not os.path.exists(boss_file):
        sample_boss = {
            "Name": "💀 DEMON LORD 💀",
            "Hit_Points": 200,
            "Aspect1": "fire_level_3",
            "Level": 5,
            "Experience_Points": 0
        }
        with open(boss_file, 'w') as f:
            json.dump(sample_boss, f, indent=4)
        print(f"Created sample boss file: {boss_file}")

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

    for book_info in sample_books:
        if not os.path.exists(book_info["file"]):
            with open(book_info["file"], 'w') as f:
                json.dump(book_info["data"], f, indent=4)
            print(f"Created sample book file: {book_info['file']}")

    # Start the game
    game = GameManager()

    # Start background music if available
    if game.music_available:
        try:
            pygame.mixer.music.play(-1)
            pygame.mixer.music.pause()  # Start paused
            print("Background music loaded successfully")
        except Exception as e:
            print(f"Could not start background music: {e}")

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

    # Run the game
    try:
        game.run()
    except Exception as e:
        print(f"Game error: {e}")
        pygame.quit()
        sys.exit()