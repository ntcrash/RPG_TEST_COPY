"""
Inventory and Store Management System for Magitech RPG
Handles inventory operations, item usage, equipment bonuses, and store transactions
"""

import pygame
import random
from ui_components import *


class InventoryManager:
    """Manages player inventory operations"""

    def __init__(self, character_manager):
        self.character_manager = character_manager

    def add_item(self, item_name, quantity=1):
        """Add item to player inventory"""
        if not self.character_manager.character_data:
            return False

        inventory = self.character_manager.character_data.get("Inventory", {})
        inventory[item_name] = inventory.get(item_name, 0) + quantity
        self.character_manager.character_data["Inventory"] = inventory
        return True

    def remove_item(self, item_name, quantity=1):
        """Remove item from player inventory"""
        if not self.character_manager.character_data:
            return False

        inventory = self.character_manager.character_data.get("Inventory", {})
        if inventory.get(item_name, 0) < quantity:
            return False

        inventory[item_name] -= quantity
        if inventory[item_name] <= 0:
            del inventory[item_name]
        self.character_manager.character_data["Inventory"] = inventory
        return True

    def get_item_quantity(self, item_name):
        """Get quantity of item in inventory"""
        if not self.character_manager.character_data:
            return 0
        inventory = self.character_manager.character_data.get("Inventory", {})
        return inventory.get(item_name, 0)

    def get_inventory(self):
        """Get player's inventory"""
        if not self.character_manager.character_data:
            return {}
        return self.character_manager.character_data.get("Inventory", {})

    def get_item_info(self, item_name):
        """Get detailed information about an item"""
        equipment_info = {
            # Weapons
            "Enhanced Spell Blade": {"type": "weapon", "stats": "+2 Str, +1 Dex, +5 Weapon Dmg", "bonuses": {"strength": 2, "dexterity": 1}},
            "Mystic Staff": {"type": "weapon", "stats": "+3 Int, +1 Wis, +3 Magic Dmg", "bonuses": {"intelligence": 3, "wisdom": 1}},
            "Warrior's Sword": {"type": "weapon", "stats": "+3 Str, +1 Con, +7 Weapon Dmg", "bonuses": {"strength": 3, "constitution": 1}},
            "Iron Sword": {"type": "weapon", "stats": "+1 Str, +3 Weapon Dmg", "bonuses": {"strength": 1}},
            "Silver Blade": {"type": "weapon", "stats": "+2 Str, +1 Dex, +4 Weapon Dmg", "bonuses": {"strength": 2, "dexterity": 1}},
            "Mithril Staff": {"type": "weapon", "stats": "+2 Int, +2 Wis, +4 Magic Dmg", "bonuses": {"intelligence": 2, "wisdom": 2}},
            "Dragon Slayer": {"type": "weapon", "stats": "+4 Str, +2 Con, +8 Weapon Dmg", "bonuses": {"strength": 4, "constitution": 2}},
            "Basic Staff": {"type": "weapon", "stats": "+1 Int, +1 Wis, +1 Magic Dmg", "bonuses": {"intelligence": 1, "wisdom": 1}},

            # Armor
            "Mystic Armor": {"type": "armor", "stats": "+2 Con, +1 Int, +5 AC", "bonuses": {"constitution": 2, "intelligence": 1}},
            "Plate Mail": {"type": "armor", "stats": "+3 Con, +1 Str, +7 AC", "bonuses": {"constitution": 3, "strength": 1}},
            "Leather Armor": {"type": "armor", "stats": "+2 Dex, +1 Con, +3 AC", "bonuses": {"dexterity": 2, "constitution": 1}},
            "Iron Chainmail": {"type": "armor", "stats": "+2 Con, +1 Str, +4 AC", "bonuses": {"constitution": 2, "strength": 1}},
            "Mithril Plate": {"type": "armor", "stats": "+3 Con, +1 Int, +6 AC", "bonuses": {"constitution": 3, "intelligence": 1}},
            "Phoenix Robes": {"type": "armor", "stats": "+3 Int, +2 Wis, +4 AC", "bonuses": {"intelligence": 3, "wisdom": 2}},
            "Basic Armor": {"type": "armor", "stats": "+1 Con, +2 AC", "bonuses": {"constitution": 1}},
            "Spell_Armor": {"type": "armor", "stats": "+1 Int, +1 Con, +3 AC", "bonuses": {"intelligence": 1, "constitution": 1}},

            # Accessories
            "Ring of Strength": {"type": "accessory", "stats": "+2 Strength", "bonuses": {"strength": 2}},
            "Amulet of Intelligence": {"type": "accessory", "stats": "+2 Intelligence", "bonuses": {"intelligence": 2}},
            "Boots of Dexterity": {"type": "accessory", "stats": "+2 Dexterity", "bonuses": {"dexterity": 2}},
            "Belt of Constitution": {"type": "accessory", "stats": "+2 Constitution", "bonuses": {"constitution": 2}},
            "Crown of Wisdom": {"type": "accessory", "stats": "+2 Wisdom", "bonuses": {"wisdom": 2}},
            "Pendant of Charisma": {"type": "accessory", "stats": "+2 Charisma", "bonuses": {"charisma": 2}},
            "Crystal Ring": {"type": "accessory", "stats": "+1 Int, +1 Wis", "bonuses": {"intelligence": 1, "wisdom": 1}},
            "Gold Amulet": {"type": "accessory", "stats": "+2 Con, +1 Str", "bonuses": {"constitution": 2, "strength": 1}},
            "Void Pendant": {"type": "accessory", "stats": "+3 Int, +2 Wis", "bonuses": {"intelligence": 3, "wisdom": 2}}
        }

        return equipment_info.get(item_name, {"type": "consumable", "stats": "Consumable item", "bonuses": {}})

    def is_equipment(self, item_name):
        """Check if an item is equipment (weapon, armor, accessory)"""
        item_info = self.get_item_info(item_name)
        return item_info["type"] in ["weapon", "armor", "accessory"]

    def get_equipped_items(self):
        """Get all currently equipped items"""
        if not self.character_manager.character_data:
            return {}

        equipped = {
            "Weapon1": self.character_manager.character_data.get("Weapon1", ""),
            "Weapon2": self.character_manager.character_data.get("Weapon2", ""),
            "Weapon3": self.character_manager.character_data.get("Weapon3", ""),
            "Armor_Slot_1": self.character_manager.character_data.get("Armor_Slot_1", ""),
            "Armor_Slot_2": self.character_manager.character_data.get("Armor_Slot_2", "")
        }

        # Remove empty slots
        return {slot: item for slot, item in equipped.items() if item and item != "Hands"}

    def equip_item(self, item_name):
        """Equip an item to the appropriate slot"""
        if not self.character_manager.character_data:
            return False, "No character loaded!"

        if self.get_item_quantity(item_name) <= 0:
            return False, "Item not in inventory!"

        item_info = self.get_item_info(item_name)
        item_type = item_info["type"]

        if item_type == "weapon":
            # Find first available weapon slot
            for slot in ["Weapon1", "Weapon2", "Weapon3"]:
                current_item = self.character_manager.character_data.get(slot, "")
                if not current_item or current_item == "Hands":
                    self.character_manager.character_data[slot] = item_name
                    self.character_manager.save_character()
                    return True, f"Equipped {item_name} to {slot}!"
            return False, "All weapon slots are full!"

        elif item_type == "armor":
            # Find first available armor slot
            for slot in ["Armor_Slot_1", "Armor_Slot_2"]:
                current_item = self.character_manager.character_data.get(slot, "")
                if not current_item:
                    self.character_manager.character_data[slot] = item_name
                    self.character_manager.save_character()
                    return True, f"Equipped {item_name} to {slot}!"
            return False, "All armor slots are full!"

        elif item_type == "accessory":
            # Accessories are automatically "equipped" if owned (legacy system)
            return True, f"{item_name} is equipped automatically!"

        else:
            return False, "This item cannot be equipped!"

    def unequip_item(self, slot_name):
        """Unequip an item from a specific slot"""
        if not self.character_manager.character_data:
            return False, "No character loaded!"

        current_item = self.character_manager.character_data.get(slot_name, "")
        if not current_item or current_item == "Hands":
            return False, "No item equipped in this slot!"

        # Clear the slot
        if slot_name.startswith("Weapon"):
            self.character_manager.character_data[slot_name] = "Hands"
        else:
            self.character_manager.character_data[slot_name] = ""

        self.character_manager.save_character()
        return True, f"Unequipped {current_item} from {slot_name}!"

    def get_equipment_stat_bonus(self, stat_name):
        """Calculate stat bonus from equipped items"""
        if not self.character_manager.character_data:
            return 0

        total_bonus = 0
        inventory = self.character_manager.character_data.get("Inventory", {})

        # Equipment stat bonuses mapping
        equipment_bonuses = {
            # Weapons
            "Enhanced Spell Blade": {"strength": 2, "dexterity": 1},
            "Mystic Staff": {"intelligence": 3, "wisdom": 1},
            "Warrior's Sword": {"strength": 3, "constitution": 1},
            "Iron Sword": {"strength": 1},
            "Silver Blade": {"strength": 2, "dexterity": 1},
            "Mithril Staff": {"intelligence": 2, "wisdom": 2},
            "Dragon Slayer": {"strength": 4, "constitution": 2},
            "Basic Staff": {"intelligence": 1, "wisdom": 1},

            # Armor
            "Mystic Armor": {"constitution": 2, "intelligence": 1},
            "Plate Mail": {"constitution": 3, "strength": 1},
            "Leather Armor": {"dexterity": 2, "constitution": 1},
            "Iron Chainmail": {"constitution": 2, "strength": 1},
            "Mithril Plate": {"constitution": 3, "intelligence": 1},
            "Phoenix Robes": {"intelligence": 3, "wisdom": 2},
            "Basic Armor": {"constitution": 1},
            "Spell_Armor": {"intelligence": 1, "constitution": 1},

            # Accessories
            "Ring of Strength": {"strength": 2},
            "Amulet of Intelligence": {"intelligence": 2},
            "Boots of Dexterity": {"dexterity": 2},
            "Belt of Constitution": {"constitution": 2},
            "Crown of Wisdom": {"wisdom": 2},
            "Pendant of Charisma": {"charisma": 2},
            "Crystal Ring": {"intelligence": 1, "wisdom": 1},
            "Gold Amulet": {"constitution": 2, "strength": 1},
            "Void Pendant": {"intelligence": 3, "wisdom": 2}
        }

        # Check equipped items
        equipped_items = [
            self.character_manager.character_data.get("Weapon1", ""),
            self.character_manager.character_data.get("Weapon2", ""),
            self.character_manager.character_data.get("Weapon3", ""),
            self.character_manager.character_data.get("Armor_Slot_1", ""),
            self.character_manager.character_data.get("Armor_Slot_2", "")
        ]

        for item in equipped_items:
            if item and item in equipment_bonuses:
                bonus = equipment_bonuses[item].get(stat_name.lower(), 0)
                total_bonus += bonus

        # Check inventory for accessories (assumes they're equipped if owned)
        for item_name, quantity in inventory.items():
            if quantity > 0 and item_name in equipment_bonuses:
                if item_name.startswith(("Ring", "Amulet", "Boots", "Belt", "Crown", "Pendant", "Crystal", "Gold", "Void")):
                    bonus = equipment_bonuses[item_name].get(stat_name.lower(), 0)
                    total_bonus += bonus

        return total_bonus

    def use_item_from_inventory(self, item_name):
        """Use an item from inventory"""
        if not self.character_manager.character_data:
            return False, "No character loaded!"

        inventory = self.character_manager.character_data.get("Inventory", {})

        if item_name not in inventory or inventory[item_name] <= 0:
            return False, "Item not in inventory!"

        level = self.character_manager.character_data.get("Level", 1)

        if "Health Potion" in item_name:
            effect_value = 25 if "Greater" not in item_name else 50
            if "Enhanced" in item_name:
                effect_value = 75
            current_hp = self.character_manager.character_data.get("Hit_Points", 100)
            max_hp = self.character_manager.get_max_hp_for_level(level)
            new_hp = min(max_hp, current_hp + effect_value)
            hp_restored = new_hp - current_hp
            self.character_manager.character_data["Hit_Points"] = new_hp

            inventory[item_name] -= 1
            if inventory[item_name] <= 0:
                del inventory[item_name]
            self.character_manager.character_data["Inventory"] = inventory

            return True, f"Restored {hp_restored} HP!"

        elif "Mana Potion" in item_name or "Mana Crystal" in item_name:
            effect_value = 15 if "Greater" not in item_name else 30
            if "Crystal" in item_name:
                effect_value = 50
            current_mana = self.character_manager.character_data.get("Aspect1_Mana", 10)
            max_mana = self.character_manager.get_max_mana_for_level(level)
            new_mana = min(max_mana, current_mana + effect_value)
            mana_restored = new_mana - current_mana
            self.character_manager.character_data["Aspect1_Mana"] = new_mana

            inventory[item_name] -= 1
            if inventory[item_name] <= 0:
                del inventory[item_name]
            self.character_manager.character_data["Inventory"] = inventory

            return True, f"Restored {mana_restored} MP!"

        elif "Full Restore" in item_name or "Starfire Elixir" in item_name:
            max_hp = self.character_manager.get_max_hp_for_level(level)
            max_mana = self.character_manager.get_max_mana_for_level(level)

            hp_restored = max_hp - self.character_manager.character_data.get("Hit_Points", 100)
            mana_restored = max_mana - self.character_manager.character_data.get("Aspect1_Mana", 50)

            self.character_manager.character_data["Hit_Points"] = max_hp
            self.character_manager.character_data["Aspect1_Mana"] = max_mana

            inventory[item_name] -= 1
            if inventory[item_name] <= 0:
                del inventory[item_name]
            self.character_manager.character_data["Inventory"] = inventory

            return True, f"Fully restored! +{hp_restored} HP, +{mana_restored} MP!"

        return False, "Cannot use this item!"

    def get_sellable_items(self):
        """Get items that can be sold to the store"""
        inventory = self.get_inventory()
        sellable = {}

        # Items that can be sold (not crafting materials)
        non_sellable = [
            "Iron Ore", "Wood", "Leather", "Cloth", "Stone", "Silver Ore",
            "Mithril Shard", "Crystal Fragment", "Dragon Scale", "Gold Ore",
            "Phoenix Feather", "Void Crystal", "Adamantine", "Starfire Essence", "Time Crystal"
        ]

        for item_name, quantity in inventory.items():
            if quantity > 0 and item_name not in non_sellable:
                sellable[item_name] = quantity

        return sellable

    def get_item_sell_price(self, item_name):
        """Get the sell price for an item (typically 50% of buy price)"""
        # Base prices for different item types
        base_prices = {
            # Consumables
            "Health Potion": 125,
            "Greater Health Potion": 225,
            "Enhanced Health Potion": 400,
            "Mana Potion": 200,
            "Greater Mana Potion": 400,
            "Mana Crystal": 600,
            "Full Restore": 100,
            "Starfire Elixir": 1000,

            # Weapons
            "Enhanced Spell Blade": 500,
            "Mystic Staff": 675,
            "Warrior's Sword": 700,
            "Iron Sword": 300,
            "Silver Blade": 600,
            "Mithril Staff": 800,
            "Dragon Slayer": 1500,

            # Armor
            "Mystic Armor": 1125,
            "Plate Mail": 1750,
            "Leather Armor": 575,
            "Iron Chainmail": 800,
            "Mithril Plate": 1200,
            "Phoenix Robes": 1400,

            # Accessories
            "Ring of Strength": 650,
            "Amulet of Intelligence": 650,
            "Boots of Dexterity": 625,
            "Crystal Ring": 500,
            "Gold Amulet": 750,
            "Void Pendant": 1200
        }

        return base_prices.get(item_name, 50)  # Default 50 credits for unknown items


class StoreItem:
    """Represents an item in the store"""

    def __init__(self, name, price, item_type, stat_value=0, description="", stat_bonuses=None):
        self.name = name
        self.price = price
        self.item_type = item_type
        self.stat_value = stat_value
        self.description = description
        self.stat_bonuses = stat_bonuses or {}


class EnhancedStoreManager:
    """Enhanced store system with buying and selling functionality"""

    def __init__(self, character_manager):
        self.character_manager = character_manager
        self.inventory_manager = InventoryManager(character_manager)
        self.items = self._initialize_store_items()
        self.selected_item = 0
        self.mode = "buy"  # "buy" or "sell"
        self.sellable_items = []

        # Scrolling and pagination
        self.scroll_offset = 0
        self.items_per_page = 12

        # UI fonts
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 20)

    def _initialize_store_items(self):
        """Initialize the store's inventory"""
        return [
            StoreItem("Health Potion", 250, "health_potion", 25, "Restores 25 HP"),
            StoreItem("Greater Health Potion", 450, "health_potion", 50, "Restores 50 HP"),
            StoreItem("Enhanced Health Potion", 800, "health_potion", 75, "Restores 75 HP"),
            StoreItem("Mana Potion", 400, "mana_potion", 15, "Restores 15 MP"),
            StoreItem("Greater Mana Potion", 800, "mana_potion", 30, "Restores 30 MP"),
            StoreItem("Mana Crystal", 1200, "mana_potion", 50, "Restores 50 MP"),
            StoreItem("Full Restore", 200, "full_restore", 0, "Fully restores HP and MP"),

            # Weapons with stat bonuses
            StoreItem("Enhanced Spell Blade", 1000, "weapon", 5, "+2 Str, +1 Dex, +5 Weapon Dmg",
                      {"strength": 2, "dexterity": 1}),
            StoreItem("Mystic Staff", 1350, "weapon", 3, "+3 Int, +1 Wis, +3 Magic Dmg",
                      {"intelligence": 3, "wisdom": 1}),
            StoreItem("Warrior's Sword", 1400, "weapon", 7, "+3 Str, +1 Con, +7 Weapon Dmg",
                      {"strength": 3, "constitution": 1}),
            StoreItem("Iron Sword", 600, "weapon", 3, "+1 Str, +3 Weapon Dmg",
                      {"strength": 1}),

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

    def switch_mode(self):
        """Switch between buy and sell mode"""
        self.mode = "sell" if self.mode == "buy" else "buy"
        self.selected_item = 0
        self.scroll_offset = 0

        if self.mode == "sell":
            self.update_sellable_items()

    def update_sellable_items(self):
        """Update the list of sellable items"""
        sellable_dict = self.inventory_manager.get_sellable_items()
        self.sellable_items = []

        for item_name, quantity in sellable_dict.items():
            sell_price = self.inventory_manager.get_item_sell_price(item_name)
            # Create a pseudo StoreItem for selling
            self.sellable_items.append({
                "name": item_name,
                "quantity": quantity,
                "price": sell_price,
                "description": f"Sell for {sell_price} credits each"
            })

    def get_current_items(self):
        """Get current items based on mode"""
        if self.mode == "buy":
            return self.items
        else:
            return self.sellable_items

    def get_affordable_items(self, credits):
        """Get items the player can afford (buy mode only)"""
        if self.mode != "buy":
            return []
        return [item for item in self.items if item.price <= credits]

    def handle_input(self, key):
        """Handle store input and return action result"""
        current_items = self.get_current_items()
        max_items = len(current_items)

        if max_items == 0:
            if key == pygame.K_TAB:
                self.switch_mode()
                return "mode_switched"
            return "no_items"

        if key == pygame.K_UP:
            self.selected_item = max(0, self.selected_item - 1)
            if self.selected_item < self.scroll_offset:
                self.scroll_offset = self.selected_item
        elif key == pygame.K_DOWN:
            self.selected_item = min(max_items - 1, self.selected_item + 1)
            if self.selected_item >= self.scroll_offset + self.items_per_page:
                self.scroll_offset = self.selected_item - self.items_per_page + 1
        elif key == pygame.K_RETURN:
            if self.mode == "buy":
                return self.attempt_purchase()
            else:
                return self.attempt_sale()
        elif key == pygame.K_TAB:
            self.switch_mode()
            return "mode_switched"
        elif key == pygame.K_ESCAPE:
            return "exit_store"

        return "input_handled"

    def attempt_purchase(self):
        """Attempt to purchase the selected item"""
        if not self.character_manager.character_data:
            return "no_character"

        selected_item = self.items[self.selected_item]
        current_credits = self.character_manager.character_data.get("Credits", 0)

        if current_credits >= selected_item.price:
            # Player can afford the item
            self.character_manager.character_data["Credits"] -= selected_item.price

            # Add item to inventory
            self.inventory_manager.add_item(selected_item.name, 1)

            # Auto-equip if it's equipment
            if selected_item.item_type in ["weapon", "armor", "accessory"]:
                self._auto_equip_item(selected_item)

            # Save character
            self.character_manager.save_character()

            return {"result": "purchased", "item": selected_item.name}
        else:
            return {"result": "insufficient_funds", "needed": selected_item.price - current_credits}

    def attempt_sale(self):
        """Attempt to sell the selected item"""
        if not self.character_manager.character_data or not self.sellable_items:
            return "no_items"

        selected_item = self.sellable_items[self.selected_item]
        item_name = selected_item["name"]
        sell_price = selected_item["price"]

        # Remove one item from inventory
        if self.inventory_manager.remove_item(item_name, 1):
            # Add credits to player
            current_credits = self.character_manager.character_data.get("Credits", 0)
            self.character_manager.character_data["Credits"] = current_credits + sell_price

            # Save character
            self.character_manager.save_character()

            # Update sellable items list
            self.update_sellable_items()

            # Adjust selection if needed
            if self.selected_item >= len(self.sellable_items) and len(self.sellable_items) > 0:
                self.selected_item = len(self.sellable_items) - 1

            return {"result": "sold", "item": item_name, "price": sell_price}
        else:
            return {"result": "sale_failed", "item": item_name}

    def _auto_equip_item(self, item):
        """Automatically equip item if appropriate slot is empty"""
        char_data = self.character_manager.character_data

        if item.item_type == "weapon":
            # Try to equip in first available weapon slot
            for slot in ["Weapon1", "Weapon2", "Weapon3"]:
                if not char_data.get(slot) or char_data.get(slot) == "Hands":
                    char_data[slot] = item.name
                    break
        elif item.item_type == "armor":
            # Try to equip in first available armor slot
            for slot in ["Armor_Slot_1", "Armor_Slot_2"]:
                if not char_data.get(slot):
                    char_data[slot] = item.name
                    break

    def draw_store(self, screen, width, height):
        """Draw the store interface"""
        # Semi-transparent background
        overlay = pygame.Surface((width, height))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        # Store panel
        panel_width, panel_height = 700, 500
        panel_x = (width - panel_width) // 2
        panel_y = (height - panel_height) // 2

        pygame.draw.rect(screen, MENU_BG, (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(screen, MENU_ACCENT, (panel_x, panel_y, panel_width, panel_height), 3)

        # Title with mode indicator
        mode_text = "BUYING" if self.mode == "buy" else "SELLING"
        title = self.large_font.render(f"GENERAL STORE - {mode_text}", True, MENU_SELECTED)
        title_rect = title.get_rect(center=(panel_x + panel_width // 2, panel_y + 30))
        screen.blit(title, title_rect)

        # Player credits
        if self.character_manager.character_data:
            credits = self.character_manager.character_data.get("Credits", 0)
            credits_text = self.font.render(f"Credits: {credits}", True, GOLD)
            screen.blit(credits_text, (panel_x + 20, panel_y + 60))

        # Mode switch instruction
        switch_text = self.small_font.render("TAB: Switch Buy/Sell Mode", True, MENU_TEXT)
        screen.blit(switch_text, (panel_x + panel_width - 200, panel_y + 60))

        current_items = self.get_current_items()

        if not current_items:
            no_items_text = "No items to sell" if self.mode == "sell" else "Store is empty"
            no_items = self.font.render(no_items_text, True, RED)
            no_items_rect = no_items.get_rect(center=(panel_x + panel_width // 2, panel_y + panel_height // 2))
            screen.blit(no_items, no_items_rect)
            return

        # Items list
        items_y_start = panel_y + 100
        visible_items = current_items[self.scroll_offset:self.scroll_offset + self.items_per_page]

        for i, item in enumerate(visible_items):
            actual_index = i + self.scroll_offset
            item_y = items_y_start + i * 30

            # Selection highlight
            if actual_index == self.selected_item:
                highlight_rect = pygame.Rect(panel_x + 10, item_y - 3, panel_width - 20, 26)
                pygame.draw.rect(screen, MENU_HIGHLIGHT, highlight_rect)

            if self.mode == "buy":
                # Buy mode - show store items
                # Check if affordable
                current_credits = self.character_manager.character_data.get("Credits", 0) if self.character_manager.character_data else 0
                affordable = current_credits >= item.price

                name_color = GREEN if affordable else RED
                name_text = self.font.render(f"{item.name} - {item.price} credits", True, name_color)
                screen.blit(name_text, (panel_x + 20, item_y))

                # Description
                desc_text = self.small_font.render(item.description, True, MENU_TEXT)
                screen.blit(desc_text, (panel_x + 20, item_y + 15))
            else:
                # Sell mode - show player items
                name_text = self.font.render(f"{item['name']} (x{item['quantity']}) - {item['price']} credits", True, GREEN)
                screen.blit(name_text, (panel_x + 20, item_y))

                # Description
                desc_text = self.small_font.render(item['description'], True, MENU_TEXT)
                screen.blit(desc_text, (panel_x + 20, item_y + 15))

        # Instructions
        instructions = [
            "UP/DOWN: Navigate items",
            "ENTER: Buy/Sell selected item",
            "TAB: Switch buy/sell mode",
            "ESC: Exit store"
        ]

        instruction_y = panel_y + panel_height - 80
        for instruction in instructions:
            instruction_surface = self.small_font.render(instruction, True, LIGHT_BLUE)
            screen.blit(instruction_surface, (panel_x + 20, instruction_y))
            instruction_y += 18


class StoreIntegration:
    """Integrates the enhanced store system with the main game"""

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.store_manager = EnhancedStoreManager(game_manager.character_manager)
        self.exit_cooldown = 0

    def handle_store_input(self, key):
        """Handle store input and manage state transitions"""
        result = self.store_manager.handle_input(key)

        if result == "exit_store":
            # Move player away from store to prevent immediate re-entry
            self.game_manager.animated_player.x += 30
            self.game_manager.animated_player.y += 30

            # Update camera to follow player
            self.game_manager.camera.update(self.game_manager.animated_player.x, self.game_manager.animated_player.y)

            # Set exit cooldown
            self.exit_cooldown = 30
            return "exit_store"
        elif isinstance(result, dict):
            if result["result"] == "purchased":
                print(f"Purchased: {result['item']}")
            elif result["result"] == "sold":
                print(f"Sold: {result['item']} for {result['price']} credits")
            elif result["result"] == "insufficient_funds":
                print(f"Need {result['needed']} more credits!")
            elif result["result"] == "sale_failed":
                print(f"Could not sell {result['item']}")

        return result

    def draw_store(self, screen):
        """Draw the store interface"""
        self.store_manager.draw_store(screen, self.game_manager.WIDTH, self.game_manager.HEIGHT)

    def update(self):
        """Update store integration"""
        if self.exit_cooldown > 0:
            self.exit_cooldown -= 1