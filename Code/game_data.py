import json
import os
import random
from pathlib import Path


def roll_dice(num, sides):
    """Roll dice for random events"""
    return [random.randint(1, sides) for _ in range(num)]


class CharacterManager:
    """Manages character data, stats, and progression"""

    def __init__(self):
        self.character_data = {}
        self.character_file = ""

    def create_sample_character(self):
        """Create a sample character for testing"""
        sample_character = {
            "Name": "Test Hero",
            "Race": "Human",
            "Type": "War Mage",
            "Level": 1,
            "Hit_Points": 100,
            "Credits": 1000,
            "Experience_Points": 0,
            "Aspect1": "fire_level_1",
            "Aspect1_Mana": 50,
            "Weapon1": "Spell Pistol",
            "Weapon2": "Hands",
            "Weapon3": "Spell_Blade",
            "Armor_Slot_1": "Spell_Armor",
            "Armor_Slot_2": "",
            "Inventory": {},
            "strength": 14,
            "dexterity": 12,
            "constitution": 16,
            "intelligence": 15,
            "wisdom": 13,
            "charisma": 11
        }

        # Ensure Characters directory exists
        os.makedirs("../Characters", exist_ok=True)
        char_file = "Characters/test_hero.json"

        with open(char_file, 'w') as f:
            json.dump(sample_character, f, indent=4)

        self.character_data = sample_character
        self.character_file = char_file
        return char_file

    def load_character(self, char_file):
        """Load character from file"""
        try:
            with open(char_file, 'r') as f:
                self.character_data = json.load(f)
                self.character_file = char_file
                print(f"Successfully loaded character: {self.character_data.get('Name', 'Unknown')}")
                return True
        except Exception as e:
            print(f"Failed to load character from {char_file}: {e}")
            return False

    def save_character(self):
        """Save current character to file"""
        if self.character_file and self.character_data:
            try:
                with open(self.character_file, 'w') as f:
                    json.dump(self.character_data, f, indent=4)
                print(f"Character saved: {self.character_data.get('Name', 'Unknown')}")
                return True
            except Exception as e:
                print(f"Failed to save character: {e}")
                return False
        return False

    def get_character_list(self):
        """Get list of available characters"""
        # chars_dir = "../Characters"
        # Get the directory where your script is located
        script_dir = Path(__file__).parent

        # Build paths
        chars_dir = script_dir.parent / 'Characters'
        # demon_file = enemies_dir / 'demon_level_1.json'

        if os.path.exists(chars_dir):
            chars = [f for f in os.listdir(chars_dir) if f.endswith('.json')]
            chars.append("New Character")
            return chars
        return ["New Character"]

    def get_player_level(self):
        """Calculate player level from XP"""
        if not self.character_data:
            return 1

        xp = self.character_data.get("Experience_Points", 0)
        level = min(50, max(1, int(xp // 150) + 1))
        return level

    def get_max_hp_for_level(self, level):
        """Get max HP based on level and constitution"""
        if not self.character_data:
            return 100

        # Base HP varies by class
        class_type = self.character_data.get("Type", "Unknown")
        base_hp_by_class = {
            "Tech Mage": 100,
            "War Mage": 130,
            "True Mage": 80,
            "Warrior": 140,
            "Paladin": 90,
            "Healer": 80
        }

        base_hp = base_hp_by_class.get(class_type, 100)
        level_bonus = (level - 1) * 10
        constitution = self.get_total_stat("constitution")
        constitution_bonus = max(0, (constitution - 10) // 2) * 3

        return base_hp + level_bonus + constitution_bonus

    def get_max_mana_for_level(self, level):
        """Get max mana based on level and intelligence/wisdom"""
        if not self.character_data:
            return 50

        # Base mana varies by class
        class_type = self.character_data.get("Type", "Unknown")
        base_mana_by_class = {
            "Tech Mage": 30,
            "War Mage": 60,
            "True Mage": 80,
            "Warrior": 40,
            "Paladin": 70,
            "Healer": 90
        }

        base_mana = base_mana_by_class.get(class_type, 50)
        level_bonus = (level - 1) * 5
        intelligence = self.get_total_stat("intelligence")
        wisdom = self.get_total_stat("wisdom")
        int_bonus = max(0, (intelligence - 10) // 2) * 2
        wis_bonus = max(0, (wisdom - 10) // 2) * 1

        return base_mana + level_bonus + int_bonus + wis_bonus

    def get_base_stat(self, stat_name):
        """Get base stat value before equipment bonuses"""
        if not self.character_data:
            return 10
        return self.character_data.get(stat_name.lower(), 10)

    def get_equipment_stat_bonus(self, stat_name):
        """Calculate stat bonus from equipped items - MOVED TO INVENTORY SYSTEM"""
        # This method has been moved to inventory_system.py
        # Use the InventoryManager for equipment stat calculations
        from Code.inventory_system import InventoryManager
        inventory_manager = InventoryManager(self)
        return inventory_manager.get_equipment_stat_bonus(stat_name)

    def get_total_stat(self, stat_name):
        """Get total stat value including equipment bonuses"""
        base = self.get_base_stat(stat_name)
        equipment_bonus = self.get_equipment_stat_bonus(stat_name)
        return base + equipment_bonus

    def get_armor_class(self):
        """Calculate armor class from dexterity and equipment"""
        if not self.character_data:
            return 10

        base_ac = 10
        dexterity = self.get_total_stat("dexterity")
        dex_bonus = max(0, (dexterity - 10) // 2)

        # Armor bonuses
        armor_bonuses = {
            "Mystic Armor": 5,
            "Plate Mail": 7,
            "Leather Armor": 3,
            "Basic Armor": 2,
            "Spell_Armor": 3
        }

        armor_bonus = 0
        equipped_armor = [
            self.character_data.get("Armor_Slot_1", ""),
            self.character_data.get("Armor_Slot_2", "")
        ]

        for armor in equipped_armor:
            if armor in armor_bonuses:
                armor_bonus = max(armor_bonus, armor_bonuses[armor])

        return base_ac + dex_bonus + armor_bonus

    def get_weapon_damage_bonus(self):
        """Calculate weapon damage bonus from equipped weapons"""
        if not self.character_data:
            return 0

        weapon_bonuses = {
            "Enhanced Spell Blade": 5,
            "Mystic Staff": 3,
            "Warrior's Sword": 7,
            "Iron Sword": 2,
            "Basic Staff": 1,
            "Spell Pistol": 3,
            "Spell_Blade": 4
        }

        total_bonus = 0
        equipped_weapons = [
            self.character_data.get("Weapon1", ""),
            self.character_data.get("Weapon2", ""),
            self.character_data.get("Weapon3", "")
        ]

        for weapon in equipped_weapons:
            if weapon in weapon_bonuses:
                total_bonus += weapon_bonuses[weapon]

        return total_bonus

    def level_up_check(self):
        """Check if player should level up and apply benefits"""
        if not self.character_data:
            return False

        current_level = self.character_data.get("Level", 1)
        calculated_level = self.get_player_level()

        if calculated_level > current_level and calculated_level <= 50:
            levels_gained = calculated_level - current_level
            self.character_data["Level"] = calculated_level

            # Increase base stats slightly for each level gained
            stats_to_increase = ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']
            stat_increases = {}

            for _ in range(levels_gained):
                for stat in stats_to_increase:
                    # Small chance to increase each stat by 1 (25% chance per level)
                    if random.randint(1, 4) == 1:
                        current_stat = self.character_data.get(stat, 10)
                        if current_stat < 25:  # Cap stats at 25
                            self.character_data[stat] = current_stat + 1
                            stat_increases[stat] = stat_increases.get(stat, 0) + 1

            # Increase max HP and mana
            new_max_hp = self.get_max_hp_for_level(calculated_level)
            new_max_mana = self.get_max_mana_for_level(calculated_level)

            # Restore some HP/Mana on level up
            current_hp = self.character_data.get("Hit_Points", 100)
            current_mana = self.character_data.get("Aspect1_Mana", 50)

            self.character_data["Hit_Points"] = min(new_max_hp, current_hp + 25)
            self.character_data["Aspect1_Mana"] = min(new_max_mana, current_mana + 10)

            # Create level up message with stat improvements
            level_message = f"LEVEL UP! {self.character_data.get('Name', 'Player')} reached level {calculated_level}"
            if stat_increases:
                stat_text = ", ".join([f"{stat}+{bonus}" for stat, bonus in stat_increases.items()])
                level_message += f" - Stats increased: {stat_text}"

            print(level_message)
            self.save_character()
            return True
        return False

    def use_item_from_inventory(self, item_name):
        """Use an item from inventory - MOVED TO INVENTORY SYSTEM"""
        # This method has been moved to inventory_system.py
        # Use the InventoryManager for item usage
        from Code.inventory_system import InventoryManager
        inventory_manager = InventoryManager(self)
        return inventory_manager.use_item_from_inventory(item_name)

    def get_character_summary(self):
        """Get a summary of the character for display purposes"""
        if not self.character_data:
            return "No character loaded"

        name = self.character_data.get("Name", "Unknown")
        level = self.character_data.get("Level", 1)
        race = self.character_data.get("Race", "Human")
        char_class = self.character_data.get("Type", "Unknown")
        hp = self.character_data.get("Hit_Points", 100)
        max_hp = self.get_max_hp_for_level(level)
        credits = self.character_data.get("Credits", 0)
        xp = self.character_data.get("Experience_Points", 0)

        return f"{name} (Lv.{level} {race} {char_class}) - HP: {hp}/{max_hp}, Credits: {credits}, XP: {xp}"


class EnemyManager:
    """Enhanced enemy manager with level-based scaling and difficulty multiplier"""

    def __init__(self):
        self.current_book_level = 1
        self.world_theme = "grassland"  # Current world theme
        self.difficulty_multiplier = 1.0  # Add difficulty multiplier attribute
        self.enemy_templates = self._create_enhanced_enemy_templates()

    def set_difficulty_multiplier(self, multiplier):
        """Set the difficulty multiplier from settings"""
        self.difficulty_multiplier = max(0.1, min(3.0, multiplier))  # Clamp between 0.1 and 3.0

    def _create_enhanced_enemy_templates(self):
        """Create enhanced enemy templates organized by world themes"""
        return {
            "grassland": {
                "basic": [
                    {"name": "Wild Goblin", "hp_base": 60, "aspect": "earth_level_1"},
                    {"name": "Forest Wolf", "hp_base": 70, "aspect": "life_level_1"},
                    {"name": "Bandit Scout", "hp_base": 65, "aspect": "fire_level_1"},
                    {"name": "Wild Boar", "hp_base": 80, "aspect": "earth_level_1"},
                ],
                "elite": [
                    {"name": "Goblin Chieftain", "hp_base": 120, "aspect": "earth_level_2"},
                    {"name": "Alpha Wolf", "hp_base": 130, "aspect": "life_level_2"},
                    {"name": "Bandit Leader", "hp_base": 125, "aspect": "fire_level_2"},
                    {"name": "Giant Boar", "hp_base": 140, "aspect": "earth_level_2"},
                ],
                "champion": [
                    {"name": "Orc Warlord", "hp_base": 180, "aspect": "fire_level_3"},
                    {"name": "Dire Wolf Pack Leader", "hp_base": 170, "aspect": "life_level_3"},
                    {"name": "Forest Guardian", "hp_base": 190, "aspect": "life_level_3"},
                ],
                "ancient": [
                    {"name": "Ancient Treant", "hp_base": 250, "aspect": "life_level_4"},
                    {"name": "Elder Dragon Wyrmling", "hp_base": 280, "aspect": "fire_level_4"},
                ],
                "boss": [
                    {"name": "🐉 FOREST DRAGON KING 🐉", "hp_base": 400, "aspect": "fire_level_5"},
                ]
            },
            "ice": {
                "basic": [
                    {"name": "Ice Goblin", "hp_base": 70, "aspect": "water_level_1"},
                    {"name": "Frost Wolf", "hp_base": 75, "aspect": "water_level_1"},
                    {"name": "Frozen Warrior", "hp_base": 80, "aspect": "water_level_1"},
                    {"name": "Ice Sprite", "hp_base": 65, "aspect": "water_level_1"},
                ],
                "elite": [
                    {"name": "Frost Giant", "hp_base": 140, "aspect": "water_level_2"},
                    {"name": "Ice Shaman", "hp_base": 120, "aspect": "water_level_2"},
                    {"name": "Blizzard Bear", "hp_base": 150, "aspect": "water_level_2"},
                ],
                "champion": [
                    {"name": "Crystal Guardian", "hp_base": 200, "aspect": "water_level_3"},
                    {"name": "Frozen Lich", "hp_base": 180, "aspect": "water_level_3"},
                ],
                "ancient": [
                    {"name": "Ancient Ice Wyrm", "hp_base": 300, "aspect": "water_level_4"},
                    {"name": "Primordial Frost", "hp_base": 280, "aspect": "water_level_4"},
                ],
                "boss": [
                    {"name": "❄️ ICE TITAN OVERLORD ❄️", "hp_base": 450, "aspect": "water_level_5"},
                ]
            },
            "shadow": {
                "basic": [
                    {"name": "Shadow Imp", "hp_base": 55, "aspect": "void_level_1"},
                    {"name": "Dark Wraith", "hp_base": 60, "aspect": "void_level_1"},
                    {"name": "Phantom Scout", "hp_base": 58, "aspect": "void_level_1"},
                ],
                "elite": [
                    {"name": "Shadow Assassin", "hp_base": 110, "aspect": "void_level_2"},
                    {"name": "Dark Sorcerer", "hp_base": 100, "aspect": "void_level_2"},
                    {"name": "Void Stalker", "hp_base": 115, "aspect": "void_level_2"},
                ],
                "champion": [
                    {"name": "Shadow Lord", "hp_base": 160, "aspect": "void_level_3"},
                    {"name": "Dark Overlord", "hp_base": 170, "aspect": "void_level_3"},
                ],
                "ancient": [
                    {"name": "Ancient Darkness", "hp_base": 260, "aspect": "void_level_4"},
                    {"name": "Void Ancient", "hp_base": 270, "aspect": "void_level_4"},
                ],
                "boss": [
                    {"name": "🌑 SHADOW REALM MASTER 🌑", "hp_base": 500, "aspect": "void_level_5"},
                ]
            },
            "elemental": {
                "basic": [
                    {"name": "Fire Elemental", "hp_base": 70, "aspect": "fire_level_1"},
                    {"name": "Earth Golem", "hp_base": 90, "aspect": "earth_level_1"},
                    {"name": "Air Spirit", "hp_base": 60, "aspect": "air_level_1"},
                    {"name": "Water Nymph", "hp_base": 65, "aspect": "water_level_1"},
                ],
                "elite": [
                    {"name": "Greater Fire Elemental", "hp_base": 130, "aspect": "fire_level_2"},
                    {"name": "Stone Titan", "hp_base": 160, "aspect": "earth_level_2"},
                    {"name": "Storm Lord", "hp_base": 120, "aspect": "air_level_2"},
                    {"name": "Tsunami Spirit", "hp_base": 125, "aspect": "water_level_2"},
                ],
                "champion": [
                    {"name": "Inferno Guardian", "hp_base": 190, "aspect": "fire_level_3"},
                    {"name": "Mountain King", "hp_base": 220, "aspect": "earth_level_3"},
                    {"name": "Hurricane Master", "hp_base": 175, "aspect": "air_level_3"},
                    {"name": "Tidal Force", "hp_base": 185, "aspect": "water_level_3"},
                ],
                "ancient": [
                    {"name": "Primordial Fire", "hp_base": 280, "aspect": "fire_level_4"},
                    {"name": "Elder Earth Spirit", "hp_base": 320, "aspect": "earth_level_4"},
                    {"name": "Ancient Wind", "hp_base": 260, "aspect": "air_level_4"},
                    {"name": "Oceanic Ancient", "hp_base": 270, "aspect": "water_level_4"},
                ],
                "boss": [
                    {"name": "⚡ ELEMENTAL NEXUS ⚡", "hp_base": 550, "aspect": "life_level_5"},
                ]
            },
            "cosmic": {
                "basic": [
                    {"name": "Star Wisp", "hp_base": 80, "aspect": "void_level_1"},
                    {"name": "Cosmic Drifter", "hp_base": 85, "aspect": "dream_level_1"},
                    {"name": "Nebula Spawn", "hp_base": 75, "aspect": "void_level_1"},
                ],
                "elite": [
                    {"name": "Starborn Warrior", "hp_base": 150, "aspect": "void_level_2"},
                    {"name": "Galactic Hunter", "hp_base": 140, "aspect": "dream_level_2"},
                    {"name": "Void Sentinel", "hp_base": 155, "aspect": "void_level_2"},
                ],
                "champion": [
                    {"name": "Galactic Destroyer", "hp_base": 240, "aspect": "void_level_4"},
                    {"name": "Starborn Titan", "hp_base": 250, "aspect": "life_level_4"},
                ],
                "ancient": [
                    {"name": "Ancient Cosmic Entity", "hp_base": 400, "aspect": "void_level_5"},
                    {"name": "Universe Devourer", "hp_base": 420, "aspect": "dream_level_5"},
                ],
                "boss": [
                    {"name": "✨ THE NEXUS GUARDIAN ✨", "hp_base": 666, "aspect": "life_level_5"},
                ]
            }
        }

    def set_world_theme(self, theme):
        """Set the current world theme"""
        valid_themes = ["grassland", "ice", "shadow", "elemental", "cosmic"]
        if theme in valid_themes:
            self.world_theme = theme
        else:
            self.world_theme = "grassland"

    def create_scaled_enemy(self):
        """Create an enemy scaled to current difficulty and world theme"""
        # Determine enemy tier based on book level
        if self.current_book_level <= 3:
            tier = "basic"
        elif self.current_book_level <= 6:
            tier = "elite"
        elif self.current_book_level <= 10:
            tier = "champion"
        elif self.current_book_level <= 15:
            tier = "ancient"
        else:
            tier = "boss"

        # Get enemies for current world theme
        theme_enemies = self.enemy_templates.get(self.world_theme, self.enemy_templates["grassland"])
        tier_enemies = theme_enemies.get(tier, theme_enemies["basic"])

        # Select random enemy from tier
        enemy_template = random.choice(tier_enemies)

        # Scale HP based on current book level
        base_hp = enemy_template["hp_base"]
        level_scaling = (self.current_book_level - 1) * 12
        random_variance = random.randint(-10, 15)

        # Apply difficulty multiplier
        scaled_hp = base_hp + level_scaling + random_variance
        final_hp = int(scaled_hp * self.difficulty_multiplier)

        # Create enemy data
        enemy_data = {
            "Name": enemy_template["name"],
            "Hit_Points": max(1, final_hp),
            "Aspect1": enemy_template["aspect"],
            "Level": max(1, int(self.current_book_level * self.difficulty_multiplier)),
            "Experience_Points": 0,
            "Tier": tier,
            "Theme": self.world_theme,
            "difficulty_multiplier": self.difficulty_multiplier  # Store for combat calculations
        }

        return enemy_data

    def create_scaled_boss(self):
        """Create a boss scaled to current difficulty"""
        theme_enemies = self.enemy_templates.get(self.world_theme, self.enemy_templates["grassland"])
        boss_template = random.choice(theme_enemies["boss"])

        base_hp = boss_template["hp_base"]
        level_scaling = (self.current_book_level - 1) * 30
        random_variance = random.randint(-30, 50)

        # Apply difficulty multiplier to boss
        scaled_hp = base_hp + level_scaling + random_variance
        final_hp = int(scaled_hp * self.difficulty_multiplier)

        boss_data = {
            "Name": boss_template["name"],
            "Hit_Points": max(1, final_hp),
            "Aspect1": boss_template["aspect"],
            "Level": max(1, int((self.current_book_level + 3) * self.difficulty_multiplier)),
            "Experience_Points": 0,
            "Tier": "boss",
            "Theme": self.world_theme,
            "difficulty_multiplier": self.difficulty_multiplier  # Store for combat calculations
        }

        return boss_data

    def create_specific_enemy(self, enemy_type, level_override=None):
        """Create a specific type of enemy"""
        level = level_override or self.current_book_level

        # Search through all themes and tiers for the enemy type
        for theme_name, theme_data in self.enemy_templates.items():
            for tier, enemies in theme_data.items():
                for enemy in enemies:
                    if enemy_type.lower() in enemy["name"].lower():
                        base_hp = enemy["hp_base"]
                        level_scaling = (level - 1) * 15
                        random_variance = random.randint(-5, 10)

                        # Apply difficulty multiplier
                        scaled_hp = base_hp + level_scaling + random_variance
                        final_hp = int(scaled_hp * self.difficulty_multiplier)

                        return {
                            "Name": enemy["name"],
                            "Hit_Points": max(1, final_hp),
                            "Aspect1": enemy["aspect"],
                            "Level": max(1, int(level * self.difficulty_multiplier)),
                            "Experience_Points": 0,
                            "Tier": tier,
                            "Theme": theme_name,
                            "difficulty_multiplier": self.difficulty_multiplier
                        }

        # Fallback to basic enemy
        return self.create_scaled_enemy()

    def set_difficulty_level(self, level):
        """Set the current difficulty level and automatically determine theme"""
        self.current_book_level = max(1, min(25, level))

        # Auto-set theme based on level range
        if level <= 4:
            self.set_world_theme("grassland")
        elif level <= 8:
            self.set_world_theme("ice")
        elif level <= 12:
            self.set_world_theme("shadow")
        elif level <= 18:
            self.set_world_theme("elemental")
        else:
            self.set_world_theme("cosmic")

    def get_enemy_stats_for_combat(self, enemy_data):
        """Get enemy stats for combat calculations with difficulty scaling"""
        level = enemy_data.get("Level", 1)
        difficulty_mult = enemy_data.get("difficulty_multiplier", 1.0)

        # Base stats scaled by level and difficulty
        base_stat_bonus = int((level - 1) * difficulty_mult)

        return {
            "strength": 10 + base_stat_bonus,
            "dexterity": 10 + base_stat_bonus,
            "constitution": 12 + base_stat_bonus,
            "intelligence": 8 + base_stat_bonus,
            "wisdom": 8 + base_stat_bonus,
            "charisma": 6,
            "armor_class": 10 + int(base_stat_bonus * 0.5),  # AC scales slower
            "difficulty_multiplier": difficulty_mult
        }


def create_sample_files():
    """Create sample game files if they don't exist"""

    # Create directories
    directories = ["Books", "Characters", "Enemies", "Images", "Sounds"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

    # Create sample enemy file
    # enemy_file = "../Enemies/demon_level_1.json"

    # Get the directory where your script is located
    script_dir = Path(__file__).parent

    # Build paths
    enemies_dir = script_dir.parent / 'Enemies'
    sounds_dir = script_dir.parent / 'Sounds'
    enemy_file = enemies_dir / 'demon_level_1.json'

    if not os.path.exists(enemy_file):
        sample_enemy = {
            "Name": "Fire Demon",
            "Hit_Points": 75,
            "Aspect1": "fire_level_1",
            "Level": 1,
            "Experience_Points": 0,
            "Tier": "basic"
        }
        with open(enemy_file, 'w') as f:
            json.dump(sample_enemy, f, indent=4)
        print(f"Created sample enemy file: {enemy_file}")

    # Create sample books
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
                "Chapter3_Enemy_Type": "dragon",
                "Recommended_Level": 1,
                "Rewards": {
                    "experience_multiplier": 1.2,
                    "credit_bonus": 500,
                    "special_items": ["Fire Resistance Ring", "Flame Sword"]
                }
            }
        },
        {
            "file": "Books/2_ice_kingdom.json",
            "data": {
                "Title": "The Ice Kingdom Saga",
                "Chapter1": "The Frozen Tundra",
                "Chapter1_Level": 2,
                "Chapter1_Enemy_Type": "ice_troll",
                "Chapter2": "The Crystal Caves",
                "Chapter2_Level": 4,
                "Chapter2_Enemy_Type": "ice_golem",
                "Chapter3": "The Frost Throne",
                "Chapter3_Level": 6,
                "Chapter3_Enemy_Type": "ice_king",
                "Recommended_Level": 3,
                "Rewards": {
                    "experience_multiplier": 1.3,
                    "credit_bonus": 750,
                    "special_items": ["Ice Shard Amulet", "Frost Armor"]
                }
            }
        },
        {
            "file": "Books/3_shadow_realm.json",
            "data": {
                "Title": "The Shadow Realm Mysteries",
                "Chapter1": "The Dark Forest",
                "Chapter1_Level": 4,
                "Chapter1_Enemy_Type": "shadow_beast",
                "Chapter2": "The Void Citadel",
                "Chapter2_Level": 6,
                "Chapter2_Enemy_Type": "void_wraith",
                "Chapter3": "The Emperor's Throne",
                "Chapter3_Level": 8,
                "Chapter3_Enemy_Type": "shadow_emperor",
                "Recommended_Level": 5,
                "Rewards": {
                    "experience_multiplier": 1.5,
                    "credit_bonus": 1000,
                    "special_items": ["Shadow Cloak", "Void Blade", "Dark Mastery Tome"]
                }
            }
        }
    ]

    for book_info in sample_books:
        if not os.path.exists(book_info["file"]):
            with open(book_info["file"], 'w') as f:
                json.dump(book_info["data"], f, indent=4)
            print(f"Created sample book file: {book_info['file']}")

    # Create game configuration file
    # config_file = "../assets/game_config.json"

    # Get the directory where your script is located
    script_dir = Path(__file__).parent

    # Build paths
    config_dir = script_dir.parent / 'assets'
    config_file = config_dir / 'game_config.json'


    if not os.path.exists(config_file):
        game_config = {
            "version": "1.1.1",
            "settings": {
                "default_credits": 1000,
                "max_level": 50,
                "xp_per_level": 150,
                "save_interval": 30,
                "difficulty_scaling": 1.2
            },
            "balance": {
                "combat_multipliers": {
                    "player_damage": 1.0,
                    "enemy_damage": 1.0,
                    "critical_chance_base": 5,
                    "experience_gain": 1.0,
                    "credit_gain": 1.0
                }
            },
            "features": {
                "enhanced_combat": True,
                "sound_effects": True,
                "animations": True,
                "auto_save": True
            }
        }
        with open(config_file, 'w') as f:
            json.dump(game_config, f, indent=4)
        print(f"Created game configuration file: {config_file}")


if __name__ == "__main__":
    # Test the data management system
    create_sample_files()

    # Test character manager
    char_mgr = CharacterManager()
    char_file = char_mgr.create_sample_character()
    print(f"Created sample character: {char_mgr.get_character_summary()}")

    # Test enemy manager
    enemy_mgr = EnemyManager()

    # Test different difficulty levels
    for level in [1, 3, 5, 7]:
        enemy_mgr.set_difficulty_level(level)
        enemy = enemy_mgr.create_scaled_enemy()
        boss = enemy_mgr.create_scaled_boss()
        print(f"Level {level} - Enemy: {enemy['Name']} ({enemy['Hit_Points']} HP)")
        print(f"Level {level} - Boss: {boss['Name']} ({boss['Hit_Points']} HP)")

    print(f"Character Manager loaded {len(char_mgr.get_character_list())} characters")
    print("Game data system initialized successfully!")