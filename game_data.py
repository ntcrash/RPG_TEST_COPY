import json
import os
import random


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
        os.makedirs("Characters", exist_ok=True)
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
        chars_dir = "Characters"
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
        """Calculate stat bonus from equipped items"""
        if not self.character_data:
            return 0

        total_bonus = 0
        inventory = self.character_data.get("Inventory", {})

        # Equipment stat bonuses mapping
        equipment_bonuses = {
            # Weapons
            "Enhanced Spell Blade": {"strength": 2, "dexterity": 1},
            "Mystic Staff": {"intelligence": 3, "wisdom": 1},
            "Warrior's Sword": {"strength": 3, "constitution": 1},
            "Iron Sword": {"strength": 1},
            "Basic Staff": {"intelligence": 1, "wisdom": 1},

            # Armor
            "Mystic Armor": {"constitution": 2, "intelligence": 1},
            "Plate Mail": {"constitution": 3, "strength": 1},
            "Leather Armor": {"dexterity": 2, "constitution": 1},
            "Basic Armor": {"constitution": 1},
            "Spell_Armor": {"intelligence": 1, "constitution": 1},

            # Accessories
            "Ring of Strength": {"strength": 2},
            "Amulet of Intelligence": {"intelligence": 2},
            "Boots of Dexterity": {"dexterity": 2},
            "Belt of Constitution": {"constitution": 2},
            "Crown of Wisdom": {"wisdom": 2},
            "Pendant of Charisma": {"charisma": 2}
        }

        # Check equipped items
        equipped_items = [
            self.character_data.get("Weapon1", ""),
            self.character_data.get("Weapon2", ""),
            self.character_data.get("Weapon3", ""),
            self.character_data.get("Armor_Slot_1", ""),
            self.character_data.get("Armor_Slot_2", "")
        ]

        for item in equipped_items:
            if item and item in equipment_bonuses:
                bonus = equipment_bonuses[item].get(stat_name.lower(), 0)
                total_bonus += bonus

        # Check inventory for accessories (assumes they're equipped if owned)
        for item_name, quantity in inventory.items():
            if quantity > 0 and item_name in equipment_bonuses:
                if item_name.startswith(("Ring", "Amulet", "Boots", "Belt", "Crown", "Pendant")):
                    bonus = equipment_bonuses[item_name].get(stat_name.lower(), 0)
                    total_bonus += bonus

        return total_bonus

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
            self.character_data["Level"] = calculated_level

            # Increase max HP and mana
            new_max_hp = self.get_max_hp_for_level(calculated_level)
            new_max_mana = self.get_max_mana_for_level(calculated_level)

            # Restore some HP/Mana on level up
            current_hp = self.character_data.get("Hit_Points", 100)
            current_mana = self.character_data.get("Aspect1_Mana", 50)

            self.character_data["Hit_Points"] = min(new_max_hp, current_hp + 25)
            self.character_data["Aspect1_Mana"] = min(new_max_mana, current_mana + 10)

            print(f"LEVEL UP! {self.character_data.get('Name', 'Player')} reached level {calculated_level}")
            self.save_character()
            return True
        return False

    def use_item_from_inventory(self, item_name):
        """Use an item from inventory"""
        if not self.character_data:
            return False, "No character loaded!"

        inventory = self.character_data.get("Inventory", {})

        if item_name not in inventory or inventory[item_name] <= 0:
            return False, "Item not in inventory!"

        level = self.character_data.get("Level", 1)

        if "Health Potion" in item_name:
            effect_value = 25 if "Greater" not in item_name else 50
            current_hp = self.character_data.get("Hit_Points", 100)
            max_hp = self.get_max_hp_for_level(level)
            new_hp = min(max_hp, current_hp + effect_value)
            hp_restored = new_hp - current_hp
            self.character_data["Hit_Points"] = new_hp

            inventory[item_name] -= 1
            if inventory[item_name] <= 0:
                del inventory[item_name]
            self.character_data["Inventory"] = inventory

            return True, f"Restored {hp_restored} HP!"

        elif "Mana Potion" in item_name:
            effect_value = 15 if "Greater" not in item_name else 30
            current_mana = self.character_data.get("Aspect1_Mana", 10)
            max_mana = self.get_max_mana_for_level(level)
            new_mana = min(max_mana, current_mana + effect_value)
            mana_restored = new_mana - current_mana
            self.character_data["Aspect1_Mana"] = new_mana

            inventory[item_name] -= 1
            if inventory[item_name] <= 0:
                del inventory[item_name]
            self.character_data["Inventory"] = inventory

            return True, f"Restored {mana_restored} MP!"

        elif "Full Restore" in item_name:
            max_hp = self.get_max_hp_for_level(level)
            max_mana = self.get_max_mana_for_level(level)

            hp_restored = max_hp - self.character_data.get("Hit_Points", 100)
            mana_restored = max_mana - self.character_data.get("Aspect1_Mana", 50)

            self.character_data["Hit_Points"] = max_hp
            self.character_data["Aspect1_Mana"] = max_mana

            inventory[item_name] -= 1
            if inventory[item_name] <= 0:
                del inventory[item_name]
            self.character_data["Inventory"] = inventory

            return True, f"Fully restored! +{hp_restored} HP, +{mana_restored} MP!"

        return False, "Cannot use this item!"

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
    """Manages enemy creation and scaling"""

    def __init__(self):
        self.current_book_level = 1
        self.enemy_templates = self._create_enemy_templates()

    def _create_enemy_templates(self):
        """Create enemy templates for different types and difficulties"""
        return {
            "basic": [
                {"name": "Wild Demon", "hp_base": 75, "aspect": "fire_level_1"},
                {"name": "Shadow Beast", "hp_base": 70, "aspect": "void_level_1"},
                {"name": "Forest Troll", "hp_base": 85, "aspect": "earth_level_1"},
                {"name": "Ice Wraith", "hp_base": 65, "aspect": "water_level_1"},
                {"name": "Lightning Sprite", "hp_base": 60, "aspect": "dream_level_1"},
                {"name": "Radiant Guardian", "hp_base": 80, "aspect": "life_level_1"}
            ],
            "elite": [
                {"name": "Elite Fire Elemental", "hp_base": 120, "aspect": "fire_level_2"},
                {"name": "Elite Void Wraith", "hp_base": 115, "aspect": "void_level_2"},
                {"name": "Elite Earth Golem", "hp_base": 135, "aspect": "earth_level_2"},
                {"name": "Elite Frost Giant", "hp_base": 110, "aspect": "water_level_2"},
                {"name": "Elite Storm Lord", "hp_base": 105, "aspect": "dream_level_2"},
                {"name": "Elite Angel", "hp_base": 125, "aspect": "life_level_2"}
            ],
            "ancient": [
                {"name": "Ancient Dragon Spawn", "hp_base": 200, "aspect": "fire_level_3"},
                {"name": "Ancient Shadow Emperor", "hp_base": 190, "aspect": "void_level_3"},
                {"name": "Ancient Mountain King", "hp_base": 220, "aspect": "earth_level_3"},
                {"name": "Ancient Leviathan", "hp_base": 180, "aspect": "water_level_3"},
                {"name": "Ancient Storm Master", "hp_base": 170, "aspect": "dream_level_3"},
                {"name": "Ancient Seraph", "hp_base": 210, "aspect": "life_level_3"}
            ],
            "boss": [
                {"name": "💀 DEMON LORD 💀", "hp_base": 300, "aspect": "fire_level_4"},
                {"name": "🌑 SHADOW EMPEROR 🌑", "hp_base": 280, "aspect": "void_level_4"},
                {"name": "🗻 MOUNTAIN SOVEREIGN 🗻", "hp_base": 350, "aspect": "earth_level_4"},
                {"name": "🌊 OCEAN TYRANT 🌊", "hp_base": 260, "aspect": "water_level_4"},
                {"name": "⚡ STORM OVERLORD ⚡", "hp_base": 250, "aspect": "dream_level_4"},
                {"name": "☀️ LIGHT EMPEROR ☀️", "hp_base": 320, "aspect": "life_level_4"}
            ]
        }

    def create_scaled_enemy(self):
        """Create an enemy scaled to current difficulty"""
        # Determine enemy tier based on book level
        if self.current_book_level <= 2:
            tier = "basic"
        elif self.current_book_level <= 4:
            tier = "elite"
        elif self.current_book_level <= 6:
            tier = "ancient"
        else:
            tier = "boss"

        # Select random enemy from tier
        enemy_template = random.choice(self.enemy_templates[tier])

        # Scale HP based on current book level
        base_hp = enemy_template["hp_base"]
        level_scaling = (self.current_book_level - 1) * 15
        scaled_hp = base_hp + level_scaling + random.randint(-10, 10)

        # Create enemy data
        enemy_data = {
            "Name": enemy_template["name"],
            "Hit_Points": max(1, scaled_hp),
            "Aspect1": enemy_template["aspect"],
            "Level": self.current_book_level,
            "Experience_Points": 0,
            "Tier": tier
        }

        return enemy_data

    def create_scaled_boss(self):
        """Create a boss scaled to current difficulty"""
        boss_template = random.choice(self.enemy_templates["boss"])

        base_hp = boss_template["hp_base"]
        level_scaling = (self.current_book_level - 1) * 25
        scaled_hp = base_hp + level_scaling + random.randint(-20, 20)

        boss_data = {
            "Name": boss_template["name"],
            "Hit_Points": max(1, scaled_hp),
            "Aspect1": boss_template["aspect"],
            "Level": self.current_book_level + 2,
            "Experience_Points": 0,
            "Tier": "boss"
        }

        return boss_data

    def create_specific_enemy(self, enemy_type, level_override=None):
        """Create a specific type of enemy"""
        level = level_override or self.current_book_level

        # Find enemy by name or type
        for tier, enemies in self.enemy_templates.items():
            for enemy in enemies:
                if enemy_type.lower() in enemy["name"].lower():
                    base_hp = enemy["hp_base"]
                    level_scaling = (level - 1) * 15
                    scaled_hp = base_hp + level_scaling

                    return {
                        "Name": enemy["name"],
                        "Hit_Points": max(1, scaled_hp),
                        "Aspect1": enemy["aspect"],
                        "Level": level,
                        "Experience_Points": 0,
                        "Tier": tier
                    }

        # Fallback to basic enemy
        return self.create_scaled_enemy()

    def set_difficulty_level(self, level):
        """Set the current difficulty level"""
        self.current_book_level = max(1, min(10, level))

    def get_enemy_reward_multiplier(self, enemy_data):
        """Get reward multiplier based on enemy tier"""
        tier = enemy_data.get("Tier", "basic")
        multipliers = {
            "basic": 1.0,
            "elite": 1.5,
            "ancient": 2.0,
            "boss": 3.0
        }
        return multipliers.get(tier, 1.0)


def create_sample_files():
    """Create sample game files if they don't exist"""

    # Create directories
    directories = ["Books", "Characters", "Enemies", "Images", "Sounds"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

    # Create sample enemy file
    enemy_file = "Enemies/demon_level_1.json"
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
    config_file = "game_config.json"
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