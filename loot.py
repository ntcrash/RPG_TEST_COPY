"""
Loot System for Magitech RPG
Handles item generation, treasure, and rewards
"""

import random
import json
from typing import Dict, List, Optional, Any, Tuple


class ItemType:
    """Item type constants"""
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    ACCESSORY = "accessory"
    TREASURE = "treasure"
    QUEST = "quest"
    MATERIAL = "material"


class ItemRarity:
    """Item rarity constants"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class LootManager:
    """Manages loot generation and item database"""

    def __init__(self):
        self.item_templates = self._initialize_item_templates()
        self.loot_tables = self._initialize_loot_tables()
        self.treasure_classes = self._initialize_treasure_classes()

    def _initialize_item_templates(self) -> Dict[str, Dict]:
        """Initialize base item templates"""
        return {
            # Weapons
            "rusty_sword": {
                "name": "Rusty Sword",
                "type": ItemType.WEAPON,
                "rarity": ItemRarity.COMMON,
                "damage_dice": "1d6",
                "damage_bonus": 0,
                "weapon_type": "sword",
                "value": 10,
                "weight": 3,
                "description": "A worn but serviceable blade.",
                "requirements": {"strength": 8}
            },
            "iron_sword": {
                "name": "Iron Sword",
                "type": ItemType.WEAPON,
                "rarity": ItemRarity.COMMON,
                "damage_dice": "1d8",
                "damage_bonus": 1,
                "weapon_type": "sword",
                "value": 50,
                "weight": 4,
                "description": "A sturdy iron blade.",
                "requirements": {"strength": 10}
            },
            "steel_sword": {
                "name": "Steel Sword",
                "type": ItemType.WEAPON,
                "rarity": ItemRarity.UNCOMMON,
                "damage_dice": "1d8",
                "damage_bonus": 2,
                "weapon_type": "sword",
                "value": 150,
                "weight": 4,
                "description": "A finely crafted steel blade.",
                "requirements": {"strength": 12}
            },
            "enchanted_blade": {
                "name": "Enchanted Blade",
                "type": ItemType.WEAPON,
                "rarity": ItemRarity.RARE,
                "damage_dice": "1d8",
                "damage_bonus": 3,
                "weapon_type": "sword",
                "value": 500,
                "weight": 3,
                "description": "A magically enhanced sword that glows with inner light.",
                "requirements": {"strength": 12},
                "magical": True,
                "enchantments": ["sharp", "light"]
            },
            "fire_blade": {
                "name": "Flame Tongue",
                "type": ItemType.WEAPON,
                "rarity": ItemRarity.EPIC,
                "damage_dice": "1d8",
                "damage_bonus": 4,
                "extra_damage": "1d6 fire",
                "weapon_type": "sword",
                "value": 1500,
                "weight": 4,
                "description": "A legendary sword wreathed in eternal flames.",
                "requirements": {"strength": 14},
                "magical": True,
                "enchantments": ["flaming", "magic"]
            },

            # Armor
            "leather_armor": {
                "name": "Leather Armor",
                "type": ItemType.ARMOR,
                "rarity": ItemRarity.COMMON,
                "armor_class": 2,
                "armor_type": "light",
                "value": 25,
                "weight": 10,
                "description": "Basic leather protection.",
                "requirements": {}
            },
            "chain_mail": {
                "name": "Chain Mail",
                "type": ItemType.ARMOR,
                "rarity": ItemRarity.COMMON,
                "armor_class": 4,
                "armor_type": "medium",
                "value": 150,
                "weight": 25,
                "description": "Interlocked metal rings provide good protection.",
                "requirements": {"strength": 12}
            },
            "plate_armor": {
                "name": "Plate Armor",
                "type": ItemType.ARMOR,
                "rarity": ItemRarity.UNCOMMON,
                "armor_class": 6,
                "armor_type": "heavy",
                "value": 600,
                "weight": 45,
                "description": "Full plate armor offering excellent protection.",
                "requirements": {"strength": 15}
            },
            "mage_robes": {
                "name": "Mage Robes",
                "type": ItemType.ARMOR,
                "rarity": ItemRarity.UNCOMMON,
                "armor_class": 1,
                "armor_type": "robes",
                "value": 200,
                "weight": 3,
                "description": "Robes woven with magical threads.",
                "requirements": {"intelligence": 12},
                "magical": True,
                "enchantments": ["mana_boost"]
            },

            # Consumables
            "health_potion": {
                "name": "Health Potion",
                "type": ItemType.CONSUMABLE,
                "rarity": ItemRarity.COMMON,
                "value": 25,
                "weight": 0.5,
                "description": "Restores health when consumed.",
                "effect": {"type": "heal", "amount": "2d4+2"},
                "consumable": True
            },
            "mana_potion": {
                "name": "Mana Potion",
                "type": ItemType.CONSUMABLE,
                "rarity": ItemRarity.COMMON,
                "value": 30,
                "weight": 0.5,
                "description": "Restores magical energy.",
                "effect": {"type": "mana", "amount": "2d6+4"},
                "consumable": True
            },
            "greater_health_potion": {
                "name": "Greater Health Potion",
                "type": ItemType.CONSUMABLE,
                "rarity": ItemRarity.UNCOMMON,
                "value": 100,
                "weight": 0.5,
                "description": "Restores significant health.",
                "effect": {"type": "heal", "amount": "4d4+4"},
                "consumable": True
            },
            "antidote": {
                "name": "Antidote",
                "type": ItemType.CONSUMABLE,
                "rarity": ItemRarity.COMMON,
                "value": 40,
                "weight": 0.5,
                "description": "Neutralizes poison.",
                "effect": {"type": "cure_poison"},
                "consumable": True
            },
            "strength_elixir": {
                "name": "Elixir of Strength",
                "type": ItemType.CONSUMABLE,
                "rarity": ItemRarity.RARE,
                "value": 300,
                "weight": 0.5,
                "description": "Temporarily increases strength.",
                "effect": {"type": "stat_boost", "stat": "strength", "amount": 4, "duration": 300},
                "consumable": True
            },

            # Accessories
            "ring_of_protection": {
                "name": "Ring of Protection",
                "type": ItemType.ACCESSORY,
                "rarity": ItemRarity.RARE,
                "value": 800,
                "weight": 0.1,
                "description": "Provides magical protection.",
                "effect": {"type": "ac_bonus", "amount": 1},
                "slot": "ring",
                "magical": True
            },
            "amulet_of_health": {
                "name": "Amulet of Health",
                "type": ItemType.ACCESSORY,
                "rarity": ItemRarity.EPIC,
                "value": 2000,
                "weight": 0.5,
                "description": "Greatly enhances vitality.",
                "effect": {"type": "stat_set", "stat": "constitution", "value": 19},
                "slot": "neck",
                "magical": True
            },
            "boots_of_speed": {
                "name": "Boots of Speed",
                "type": ItemType.ACCESSORY,
                "rarity": ItemRarity.RARE,
                "value": 1200,
                "weight": 2,
                "description": "Increases movement speed.",
                "effect": {"type": "speed_boost", "amount": 1.5},
                "slot": "feet",
                "magical": True
            },

            # Treasure
            "gold_coins": {
                "name": "Gold Coins",
                "type": ItemType.TREASURE,
                "rarity": ItemRarity.COMMON,
                "value": 1,  # Per coin
                "weight": 0.02,  # Per coin
                "description": "Standard currency.",
                "stackable": True
            },
            "gems": {
                "name": "Precious Gems",
                "type": ItemType.TREASURE,
                "rarity": ItemRarity.UNCOMMON,
                "value": 100,
                "weight": 0.1,
                "description": "Valuable gemstones.",
                "stackable": True
            },
            "art_object": {
                "name": "Art Object",
                "type": ItemType.TREASURE,
                "rarity": ItemRarity.RARE,
                "value": 500,
                "weight": 5,
                "description": "A valuable work of art."
            }
        }

    def _initialize_loot_tables(self) -> Dict[str, Dict]:
        """Initialize loot tables for different encounter types"""
        return {
            "goblin": {
                "items": [
                    {"item": "rusty_sword", "chance": 30, "quantity": (1, 1)},
                    {"item": "health_potion", "chance": 40, "quantity": (1, 2)},
                    {"item": "gold_coins", "chance": 80, "quantity": (5, 15)},
                    {"item": "leather_armor", "chance": 20, "quantity": (1, 1)}
                ]
            },
            "orc": {
                "items": [
                    {"item": "iron_sword", "chance": 25, "quantity": (1, 1)},
                    {"item": "chain_mail", "chance": 15, "quantity": (1, 1)},
                    {"item": "health_potion", "chance": 35, "quantity": (1, 2)},
                    {"item": "gold_coins", "chance": 90, "quantity": (10, 30)}
                ]
            },
            "skeleton": {
                "items": [
                    {"item": "rusty_sword", "chance": 40, "quantity": (1, 1)},
                    {"item": "antidote", "chance": 25, "quantity": (1, 1)},
                    {"item": "gold_coins", "chance": 60, "quantity": (3, 12)},
                    {"item": "gems", "chance": 10, "quantity": (1, 1)}
                ]
            },
            "dragon": {
                "items": [
                    {"item": "fire_blade", "chance": 15, "quantity": (1, 1)},
                    {"item": "plate_armor", "chance": 20, "quantity": (1, 1)},
                    {"item": "amulet_of_health", "chance": 10, "quantity": (1, 1)},
                    {"item": "greater_health_potion", "chance": 60, "quantity": (2, 5)},
                    {"item": "gold_coins", "chance": 100, "quantity": (100, 500)},
                    {"item": "gems", "chance": 80, "quantity": (3, 10)},
                    {"item": "art_object", "chance": 40, "quantity": (1, 3)}
                ]
            },
            "chest_common": {
                "items": [
                    {"item": "health_potion", "chance": 50, "quantity": (1, 3)},
                    {"item": "mana_potion", "chance": 40, "quantity": (1, 2)},
                    {"item": "gold_coins", "chance": 90, "quantity": (20, 80)},
                    {"item": "iron_sword", "chance": 25, "quantity": (1, 1)},
                    {"item": "leather_armor", "chance": 30, "quantity": (1, 1)}
                ]
            },
            "chest_rare": {
                "items": [
                    {"item": "enchanted_blade", "chance": 30, "quantity": (1, 1)},
                    {"item": "mage_robes", "chance": 25, "quantity": (1, 1)},
                    {"item": "ring_of_protection", "chance": 20, "quantity": (1, 1)},
                    {"item": "greater_health_potion", "chance": 60, "quantity": (2, 4)},
                    {"item": "strength_elixir", "chance": 35, "quantity": (1, 2)},
                    {"item": "gold_coins", "chance": 95, "quantity": (100, 300)},
                    {"item": "gems", "chance": 70, "quantity": (2, 6)}
                ]
            },
            "boss": {
                "items": [
                    {"item": "fire_blade", "chance": 25, "quantity": (1, 1)},
                    {"item": "plate_armor", "chance": 30, "quantity": (1, 1)},
                    {"item": "amulet_of_health", "chance": 15, "quantity": (1, 1)},
                    {"item": "boots_of_speed", "chance": 20, "quantity": (1, 1)},
                    {"item": "greater_health_potion", "chance": 80, "quantity": (3, 6)},
                    {"item": "strength_elixir", "chance": 60, "quantity": (2, 4)},
                    {"item": "gold_coins", "chance": 100, "quantity": (200, 800)},
                    {"item": "gems", "chance": 90, "quantity": (5, 15)},
                    {"item": "art_object", "chance": 50, "quantity": (1, 2)}
                ]
            }
        }

    def _initialize_treasure_classes(self) -> Dict[str, Dict]:
        """Initialize treasure class system"""
        return {
            "TC1": {  # Poor
                "gold_chance": 60,
                "gold_amount": (1, 10),
                "item_chance": 20,
                "item_types": ["health_potion", "rusty_sword"]
            },
            "TC2": {  # Below Average
                "gold_chance": 70,
                "gold_amount": (5, 25),
                "item_chance": 30,
                "item_types": ["health_potion", "mana_potion", "iron_sword", "leather_armor"]
            },
            "TC3": {  # Average
                "gold_chance": 80,
                "gold_amount": (10, 50),
                "item_chance": 40,
                "item_types": ["health_potion", "mana_potion", "iron_sword", "chain_mail", "antidote"]
            },
            "TC4": {  # Good
                "gold_chance": 85,
                "gold_amount": (25, 100),
                "item_chance": 50,
                "item_types": ["greater_health_potion", "steel_sword", "chain_mail", "gems"]
            },
            "TC5": {  # Excellent
                "gold_chance": 90,
                "gold_amount": (50, 200),
                "item_chance": 60,
                "item_types": ["enchanted_blade", "plate_armor", "ring_of_protection", "gems", "art_object"]
            },
            "TC6": {  # Legendary
                "gold_chance": 95,
                "gold_amount": (100, 500),
                "item_chance": 80,
                "item_types": ["fire_blade", "amulet_of_health", "boots_of_speed", "art_object"]
            }
        }

    def generate_loot(self, encounter_type: str, player_level: int = 1) -> List[Dict]:
        """Generate loot for an encounter"""
        if encounter_type not in self.loot_tables:
            # Fallback to basic loot
            return self.generate_basic_loot(player_level)

        loot_table = self.loot_tables[encounter_type]
        generated_loot = []

        for item_entry in loot_table["items"]:
            roll = random.randint(1, 100)
            if roll <= item_entry["chance"]:
                # Determine quantity
                min_qty, max_qty = item_entry["quantity"]
                quantity = random.randint(min_qty, max_qty)

                # Create item instance
                item = self.create_item(item_entry["item"], quantity)
                if item:
                    generated_loot.append(item)

        return generated_loot

    def generate_basic_loot(self, player_level: int) -> List[Dict]:
        """Generate basic loot based on player level"""
        loot = []

        # Always some gold
        gold_amount = random.randint(player_level * 5, player_level * 15)
        loot.append(self.create_item("gold_coins", gold_amount))

        # Chance for health potion
        if random.randint(1, 100) <= 60:
            loot.append(self.create_item("health_potion", 1))

        # Chance for equipment based on level
        if player_level >= 3 and random.randint(1, 100) <= 30:
            equipment_options = ["iron_sword", "leather_armor", "mana_potion"]
            chosen_item = random.choice(equipment_options)
            loot.append(self.create_item(chosen_item, 1))

        return [item for item in loot if item]  # Filter out None items

    def generate_treasure_class_loot(self, treasure_class: str) -> List[Dict]:
        """Generate loot using treasure class system"""
        if treasure_class not in self.treasure_classes:
            return []

        tc = self.treasure_classes[treasure_class]
        loot = []

        # Gold
        if random.randint(1, 100) <= tc["gold_chance"]:
            min_gold, max_gold = tc["gold_amount"]
            gold_amount = random.randint(min_gold, max_gold)
            loot.append(self.create_item("gold_coins", gold_amount))

        # Items
        if random.randint(1, 100) <= tc["item_chance"]:
            item_type = random.choice(tc["item_types"])
            item = self.create_item(item_type, 1)
            if item:
                loot.append(item)

        return loot

    def create_item(self, item_template: str, quantity: int = 1) -> Optional[Dict]:
        """Create an item instance from template"""
        if item_template not in self.item_templates:
            return None

        template = self.item_templates[item_template].copy()

        # Add instance-specific data
        item = {
            "id": self.generate_item_id(),
            "template": item_template,
            "quantity": quantity,
            **template
        }

        # Apply random variations for magical items
        if template.get("magical"):
            item = self.apply_magical_variations(item)

        return item

    def generate_item_id(self) -> str:
        """Generate unique item ID"""
        import time
        return f"item_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"

    def apply_magical_variations(self, item: Dict) -> Dict:
        """Apply random variations to magical items"""
        # Chance for enhanced versions
        if random.randint(1, 100) <= 10:  # 10% chance for enhanced
            item["name"] = f"Enhanced {item['name']}"
            item["value"] = int(item["value"] * 1.5)

            if item["type"] == ItemType.WEAPON:
                item["damage_bonus"] = item.get("damage_bonus", 0) + 1
            elif item["type"] == ItemType.ARMOR:
                item["armor_class"] = item.get("armor_class", 0) + 1

        return item

    def get_item_description(self, item: Dict) -> str:
        """Get full item description including stats"""
        description = item.get("description", "")

        # Add stat information
        if item["type"] == ItemType.WEAPON:
            damage_info = item.get("damage_dice", "")
            if item.get("damage_bonus", 0) > 0:
                damage_info += f"+{item['damage_bonus']}"
            description += f"\nDamage: {damage_info}"

            if item.get("extra_damage"):
                description += f"\nExtra: {item['extra_damage']}"

        elif item["type"] == ItemType.ARMOR:
            ac = item.get("armor_class", 0)
            description += f"\nArmor Class: +{ac}"

        # Add value and weight
        description += f"\nValue: {item.get('value', 0)} gold"
        description += f"\nWeight: {item.get('weight', 0)} lbs"

        # Add requirements
        if item.get("requirements"):
            req_text = ", ".join([f"{stat.title()}: {value}" for stat, value in item["requirements"].items()])
            description += f"\nRequirements: {req_text}"

        return description

    def can_character_use_item(self, character: Dict, item: Dict) -> Tuple[bool, str]:
        """Check if character can use item"""
        requirements = item.get("requirements", {})

        for stat, required_value in requirements.items():
            character_value = character.get("stats", {}).get(stat, 10)
            if character_value < required_value:
                return False, f"Requires {stat.title()}: {required_value} (you have {character_value})"

        return True, "Can use"

    def apply_item_effect(self, character: Dict, item: Dict) -> Tuple[Dict, str]:
        """Apply item effect to character"""
        if not item.get("effect"):
            return character, "No effect"

        effect = item["effect"]
        effect_type = effect["type"]

        if effect_type == "heal":
            # Parse healing amount (e.g., "2d4+2")
            heal_amount = self.parse_dice_string(effect["amount"])
            current_hp = character.get("hit_points", 100)
            max_hp = character.get("max_hit_points", 100)
            new_hp = min(max_hp, current_hp + heal_amount)
            character["hit_points"] = new_hp
            return character, f"Healed {heal_amount} hit points"

        elif effect_type == "mana":
            # Parse mana amount
            mana_amount = self.parse_dice_string(effect["amount"])
            current_mana = character.get("mana_level", 50)
            max_mana = character.get("max_mana", 50)
            new_mana = min(max_mana, current_mana + mana_amount)
            character["mana_level"] = new_mana
            return character, f"Restored {mana_amount} mana"

        elif effect_type == "stat_boost":
            # Temporary stat boost
            stat = effect["stat"]
            amount = effect["amount"]
            duration = effect.get("duration", 300)  # 5 minutes default

            # Add to temporary effects
            if "temp_effects" not in character:
                character["temp_effects"] = {}

            character["temp_effects"][f"{stat}_boost"] = {
                "amount": amount,
                "duration": duration,
                "remaining": duration
            }

            return character, f"Increased {stat} by {amount} for {duration} seconds"

        elif effect_type == "cure_poison":
            if "status_effects" in character and "poison" in character["status_effects"]:
                del character["status_effects"]["poison"]
                return character, "Cured of poison"
            else:
                return character, "Not poisoned"

        return character, "Unknown effect"

    def parse_dice_string(self, dice_string: str) -> int:
        """Parse dice notation (e.g., '2d4+2') and roll"""
        try:
            # Simple parser for XdY+Z format
            if '+' in dice_string:
                dice_part, bonus = dice_string.split('+')
                bonus = int(bonus)
            elif '-' in dice_string:
                dice_part, penalty = dice_string.split('-')
                bonus = -int(penalty)
            else:
                dice_part = dice_string
                bonus = 0

            if 'd' in dice_part:
                num_dice, dice_sides = map(int, dice_part.split('d'))
                total = sum(random.randint(1, dice_sides) for _ in range(num_dice))
                return total + bonus
            else:
                return int(dice_part) + bonus
        except:
            return 1  # Fallback

    def get_item_by_id(self, item_id: str, inventory: List[Dict]) -> Optional[Dict]:
        """Find item by ID in inventory"""
        for item in inventory:
            if item.get("id") == item_id:
                return item
        return None

    def remove_item_from_inventory(self, item_id: str, inventory: List[Dict], quantity: int = 1) -> List[Dict]:
        """Remove item(s) from inventory"""
        for i, item in enumerate(inventory):
            if item.get("id") == item_id:
                if item.get("stackable") and item.get("quantity", 1) > quantity:
                    item["quantity"] -= quantity
                else:
                    inventory.pop(i)
                break
        return inventory

    def add_item_to_inventory(self, item: Dict, inventory: List[Dict]) -> List[Dict]:
        """Add item to inventory, stacking if possible"""
        if item.get("stackable"):
            # Try to stack with existing item
            for existing_item in inventory:
                if (existing_item.get("template") == item.get("template") and
                    existing_item.get("stackable")):
                    existing_item["quantity"] += item.get("quantity", 1)
                    return inventory

        # Add as new item
        inventory.append(item)
        return inventory

    def get_inventory_value(self, inventory: List[Dict]) -> int:
        """Calculate total value of inventory"""
        total_value = 0
        for item in inventory:
            item_value = item.get("value", 0)
            quantity = item.get("quantity", 1)
            total_value += item_value * quantity
        return total_value

    def get_inventory_weight(self, inventory: List[Dict]) -> float:
        """Calculate total weight of inventory"""
        total_weight = 0.0
        for item in inventory:
            item_weight = item.get("weight", 0.0)
            quantity = item.get("quantity", 1)
            total_weight += item_weight * quantity
        return total_weight

    def can_afford_item(self, character: Dict, item_value: int) -> bool:
        """Check if character can afford item"""
        gold = character.get("gold", 0)
        return gold >= item_value

    def buy_item(self, character: Dict, item: Dict) -> Tuple[bool, str]:
        """Buy item for character"""
        item_value = item.get("value", 0)
        if not self.can_afford_item(character, item_value):
            return False, f"Not enough gold (need {item_value}, have {character.get('gold', 0)})"

        # Deduct gold
        character["gold"] = character.get("gold", 0) - item_value

        # Add to inventory
        inventory = character.get("inventory", [])
        character["inventory"] = self.add_item_to_inventory(item, inventory)

        return True, f"Purchased {item['name']} for {item_value} gold"

    def sell_item(self, character: Dict, item_id: str, quantity: int = 1) -> Tuple[bool, str]:
        """Sell item from character inventory"""
        inventory = character.get("inventory", [])
        item = self.get_item_by_id(item_id, inventory)

        if not item:
            return False, "Item not found"

        if item.get("quantity", 1) < quantity:
            return False, "Not enough items to sell"

        # Calculate sell value (usually 50% of purchase price)
        sell_value = int(item.get("value", 0) * 0.5) * quantity

        # Remove item(s)
        character["inventory"] = self.remove_item_from_inventory(item_id, inventory, quantity)

        # Add gold
        character["gold"] = character.get("gold", 0) + sell_value

        return True, f"Sold {quantity}x {item['name']} for {sell_value} gold"


# Global loot manager instance
loot_manager = LootManager()


def generate_encounter_loot(encounter_type: str, player_level: int = 1) -> List[Dict]:
    """Generate loot for encounter (convenience function)"""
    return loot_manager.generate_loot(encounter_type, player_level)


def create_random_item(item_type: str = None, rarity: str = None) -> Optional[Dict]:
    """Create random item of specified type/rarity"""
    templates = loot_manager.item_templates

    # Filter by type and rarity
    valid_templates = []
    for template_id, template in templates.items():
        if item_type and template.get("type") != item_type:
            continue
        if rarity and template.get("rarity") != rarity:
            continue
        valid_templates.append(template_id)

    if not valid_templates:
        return None

    chosen_template = random.choice(valid_templates)
    return loot_manager.create_item(chosen_template, 1)


def generate_shop_inventory(shop_type: str = "general", level: int = 1) -> List[Dict]:
    """Generate shop inventory"""
    inventory = []

    if shop_type == "general":
        # Basic items always available
        basic_items = ["health_potion", "mana_potion", "antidote", "leather_armor", "iron_sword"]
        for item_id in basic_items:
            item = loot_manager.create_item(item_id, random.randint(1, 5))
            if item:
                inventory.append(item)

    elif shop_type == "magic":
        # Magic shop items
        magic_items = ["mage_robes", "ring_of_protection", "strength_elixir", "greater_health_potion"]
        for item_id in magic_items:
            if random.randint(1, 100) <= 60:  # 60% chance each item is in stock
                item = loot_manager.create_item(item_id, random.randint(1, 3))
                if item:
                    inventory.append(item)

    elif shop_type == "weapon":
        # Weapon shop
        weapon_items = ["rusty_sword", "iron_sword", "steel_sword", "enchanted_blade"]
        for item_id in weapon_items:
            if level >= loot_manager.item_templates[item_id].get("requirements", {}).get("strength", 0):
                item = loot_manager.create_item(item_id, 1)
                if item:
                    inventory.append(item)

    elif shop_type == "armor":
        # Armor shop
        armor_items = ["leather_armor", "chain_mail", "plate_armor"]
        for item_id in armor_items:
            if level >= loot_manager.item_templates[item_id].get("requirements", {}).get("strength", 0):
                item = loot_manager.create_item(item_id, 1)
                if item:
                    inventory.append(item)

    return inventory
