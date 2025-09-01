import json
import os
import random


def roll_dice(num, sides):
    """Roll dice for random events"""
    return [random.randint(1, sides) for _ in range(num)]


class StoreItem:
    """Store item with stats and effects"""

    def __init__(self, name, price, item_type, effect_value, description, stat_bonuses=None):
        self.name = name
        self.price = price
        self.item_type = item_type
        self.effect_value = effect_value
        self.description = description
        self.stat_bonuses = stat_bonuses or {}


class Store:
    """Game store with items and purchasing logic"""

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

            # Armor with stat bonuses and AC
            StoreItem("Mystic Armor", 2250, "armor", 5, "+2 Con, +1 Int, +5 AC",
                      {"constitution": 2, "intelligence": 1}),
            StoreItem("Plate Mail", 3500, "armor", 7, "+3 Con, +1 Str, +7 AC",
                      {"constitution": 3, "strength": 1}),
            StoreItem("Leather Armor", 1150, "armor", 3, "+2 Dex, +1 Con, +3 AC",
                      {"dexterity": 2, "constitution": 1}),

            # Accessories with stat bonuses
            StoreItem("Ring of Strength", 1300, "accessory", 0, "+2 Strength",
                      {"strength": 2}),
            StoreItem("Amulet of Intelligence", 1300, "accessory", 0, "+2 Intelligence",
                      {"intelligence": 2}),
            StoreItem("Boots of Dexterity", 1250, "accessory", 0, "+2 Dexterity",
                      {"dexterity": 2})
        ]
        self.selected_item = 0

    def get_affordable_items(self, credits):
        return [item for item in self.items if item.price <= credits]


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
                return True
        except Exception as e:
            print(f"Failed to load character: {e}")
            return False

    def save_character(self):
        """Save current character to file"""
        if self.character_file and self.character_data:
            try:
                with open(self.character_file, 'w') as f:
                    json.dump(self.character_data, f, indent=4)
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
        base_hp = 100
        level_bonus = (level - 1) * 10
        constitution = self.get_total_stat("constitution")
        constitution_bonus = max(0, (constitution - 10) // 2) * 3
        return base_hp + level_bonus + constitution_bonus

    def get_max_mana_for_level(self, level):
        """Get max mana based on level and intelligence/wisdom"""
        base_mana = 50
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

            # Armor
            "Mystic Armor": {"constitution": 2, "intelligence": 1},
            "Plate Mail": {"constitution": 3, "strength": 1},
            "Leather Armor": {"dexterity": 2, "constitution": 1},

            # Accessories
            "Ring of Strength": {"strength": 2},
            "Amulet of Intelligence": {"intelligence": 2},
            "Boots of Dexterity": {"dexterity": 2}
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

        # Check inventory for accessories
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
            "Leather Armor": 3
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

            self.save_character()
            return True
        return False

    def use_item_from_inventory(self, item_name):
        """Use an item from inventory"""
        inventory = self.character_data.get("Inventory", {})

        if item_name not in inventory or inventory[item_name] <= 0:
            return False, "Item not in inventory!"

        level = self.character_data.get("Level", 1)

        if "Health Potion" in item_name:
            effect_value = 25 if "Greater" not in item_name else 50
            current_hp = self.character_data.get("Hit_Points", 100)
            max_hp = self.get_max_hp_for_level(level)
            new_hp = min(max_hp, current_hp + effect_value)
            self.character_data["Hit_Points"] = new_hp
            hp_restored = new_hp - current_hp

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
            self.character_data["Aspect1_Mana"] = new_mana
            mana_restored = new_mana - current_mana

            inventory[item_name] -= 1
            if inventory[item_name] <= 0:
                del inventory[item_name]
            self.character_data["Inventory"] = inventory

            return True, f"Restored {mana_restored} MP!"

        return False, "Cannot use this item!"


class EnemyManager:
    """Manages enemy creation and scaling"""

    def __init__(self):
        self.current_book_level = 1

    def create_scaled_enemy(self):
        """Create an enemy scaled to current difficulty"""
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
        """Create a boss scaled to current difficulty"""
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
            "Experience_Points": 0
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
                "Chapter3_Enemy_Type": "dragon"
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
                "Chapter2_Enemy_Type": "ice_golem"
            }
        }
    ]

    for book_info in sample_books:
        if not os.path.exists(book_info["file"]):
            with open(book_info["file"], 'w') as f:
                json.dump(book_info["data"], f, indent=4)
            print(f"Created sample book file: {book_info['file']}")


if __name__ == "__main__":
    # Test the data management system
    create_sample_files()

    char_mgr = CharacterManager()
    char_mgr.create_sample_character()

    enemy_mgr = EnemyManager()
    enemy = enemy_mgr.create_scaled_enemy()
    print(f"Created enemy: {enemy}")

    store = Store()
    print(f"Store has {len(store.items)} items")