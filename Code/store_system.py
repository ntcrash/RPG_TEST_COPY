import pygame
import random
from Code.ui_components import *


class StoreItem:
    """Store item with stats and effects"""

    def __init__(self, name, price, item_type, effect_value, description, stat_bonuses=None):
        self.name = name
        self.price = price
        self.item_type = item_type
        self.effect_value = effect_value
        self.description = description
        self.stat_bonuses = stat_bonuses or {}


class StoreManager:
    """Enhanced store system with improved UI and functionality"""

    def __init__(self, character_manager):
        self.character_manager = character_manager
        self.items = self._initialize_store_items()
        self.selected_item = 0

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

    def get_affordable_items(self, credits):
        """Get items the player can afford"""
        return [item for item in self.items if item.price <= credits]

    def handle_input(self, key):
        """Handle store input and return action result"""
        max_items = len(self.items)

        if key == pygame.K_UP:
            self.selected_item = (self.selected_item - 1) % max_items
            # Adjust scroll if needed
            if self.selected_item < self.scroll_offset:
                self.scroll_offset = self.selected_item
            return "navigate"

        elif key == pygame.K_DOWN:
            self.selected_item = (self.selected_item + 1) % max_items
            # Adjust scroll if needed
            if self.selected_item >= self.scroll_offset + self.items_per_page:
                self.scroll_offset = self.selected_item - self.items_per_page + 1
            return "navigate"

        elif key == pygame.K_PAGEUP:
            # Scroll up by page
            self.scroll_offset = max(0, self.scroll_offset - self.items_per_page)
            self.selected_item = max(0, self.selected_item - self.items_per_page)
            return "navigate"

        elif key == pygame.K_PAGEDOWN:
            # Scroll down by page
            self.scroll_offset = min(max_items - self.items_per_page,
                                     self.scroll_offset + self.items_per_page)
            self.selected_item = min(max_items - 1,
                                     self.selected_item + self.items_per_page)
            return "navigate"

        elif key == pygame.K_RETURN:
            return self.attempt_purchase()

        elif key == pygame.K_ESCAPE:
            return "exit"

        return "continue"

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
            inventory = self.character_manager.character_data.get("Inventory", {})

            if selected_item.item_type in ["health_potion", "mana_potion", "full_restore"]:
                # Consumable items
                inventory[selected_item.name] = inventory.get(selected_item.name, 0) + 1
            elif selected_item.item_type in ["weapon", "armor", "accessory"]:
                # Equipment items
                inventory[selected_item.name] = inventory.get(selected_item.name, 0) + 1
                # Auto-equip if slot is empty
                self._auto_equip_item(selected_item)

            self.character_manager.character_data["Inventory"] = inventory

            # Save character
            self.character_manager.save_character()

            return {"result": "purchased", "item": selected_item.name}
        else:
            return {"result": "insufficient_funds", "needed": selected_item.price - current_credits}

    def _auto_equip_item(self, item):
        """Automatically equip an item if the appropriate slot is empty"""
        if not self.character_manager.character_data:
            return

        char_data = self.character_manager.character_data

        if item.item_type == "weapon":
            # Equip to first empty weapon slot
            if not char_data.get("Weapon1"):
                char_data["Weapon1"] = item.name
            elif not char_data.get("Weapon2"):
                char_data["Weapon2"] = item.name
            elif not char_data.get("Weapon3"):
                char_data["Weapon3"] = item.name

        elif item.item_type == "armor":
            # Equip to first empty armor slot
            if not char_data.get("Armor_Slot_1"):
                char_data["Armor_Slot_1"] = item.name
            elif not char_data.get("Armor_Slot_2"):
                char_data["Armor_Slot_2"] = item.name

    def draw_store_screen(self, screen, width, height):
        """Draw the complete store screen"""
        screen.fill(MENU_BG)

        # Store title
        title = self.large_font.render("🏪 MAGIC SHOP", True, WHITE)
        title_rect = title.get_rect(center=(width // 2, 40))
        screen.blit(title, title_rect)

        if not self.character_manager.character_data:
            no_char_text = self.font.render("No character loaded!", True, WHITE)
            no_char_rect = no_char_text.get_rect(center=(width // 2, height // 2))
            screen.blit(no_char_text, no_char_rect)
            return

        current_credits = self.character_manager.character_data.get("Credits", 0)
        credits_text = self.font.render(f"💰 Credits: {current_credits}", True, GOLD)
        screen.blit(credits_text, (20, 80))

        # Draw item list (left side)
        self._draw_item_list(screen)

        # Draw item details (right side)
        self._draw_item_details(screen, width)

        # Draw instructions (bottom)
        self._draw_instructions(screen, width, height)

    def _draw_item_list(self, screen):
        """Draw the scrollable item list"""
        current_credits = self.character_manager.character_data.get("Credits", 0)

        # Calculate visible items based on scroll
        max_items = len(self.items)
        start_index = self.scroll_offset
        end_index = min(start_index + self.items_per_page, max_items)

        y_pos = 120
        item_height = 35

        for i in range(start_index, end_index):
            item = self.items[i]
            can_afford = current_credits >= item.price

            # Set colors based on selection and affordability
            if i == self.selected_item:
                if can_afford:
                    item_color = MENU_SELECTED
                    bg_color = MENU_HIGHLIGHT
                else:
                    item_color = RED
                    bg_color = (100, 50, 50)

                # Draw selection background
                selection_rect = pygame.Rect(15, y_pos - 3, 370, item_height - 5)
                pygame.draw.rect(screen, bg_color, selection_rect)
                pygame.draw.rect(screen, item_color, selection_rect, 2)
            else:
                item_color = WHITE if can_afford else GRAY

            # Item name and price
            item_text = f"{item.name} - {item.price}💰"
            text_surface = self.small_font.render(item_text, True, item_color)
            screen.blit(text_surface, (20, y_pos))

            # Item description (smaller font)
            desc_surface = pygame.font.Font(None, 16).render(item.description[:45], True, MENU_TEXT)
            screen.blit(desc_surface, (20, y_pos + 18))

            y_pos += item_height

        # Scroll indicators
        if self.scroll_offset > 0:
            up_arrow = self.small_font.render("↑ More items above", True, LIGHT_BLUE)
            screen.blit(up_arrow, (20, 100))

        if end_index < max_items:
            down_arrow = self.small_font.render("↓ More items below", True, LIGHT_BLUE)
            screen.blit(down_arrow, (20, y_pos + 10))

    def _draw_item_details(self, screen, width):
        """Draw detailed information about the selected item"""
        if self.selected_item >= len(self.items):
            return

        selected_item = self.items[self.selected_item]
        current_credits = self.character_manager.character_data.get("Credits", 0)

        # Details panel
        details_rect = pygame.Rect(400, 120, 380, 350)
        pygame.draw.rect(screen, UI_BG_COLOR, details_rect)
        pygame.draw.rect(screen, UI_BORDER_COLOR, details_rect, 2)

        detail_y = 130

        # Item name (header)
        name_surface = self.font.render(selected_item.name, True, MENU_SELECTED)
        screen.blit(name_surface, (410, detail_y))
        detail_y += 35

        # Item details
        details = [
            f"Type: {selected_item.item_type.replace('_', ' ').title()}",
            f"Price: {selected_item.price} credits",
            f"Description: {selected_item.description}"
        ]

        for detail in details:
            # Handle word wrapping for long descriptions
            if detail.startswith("Description:") and len(detail) > 35:
                lines = [detail[:35] + "...", detail[35:70] + "..." if len(detail) > 70 else detail[35:]]
                for line in lines:
                    if line.strip():
                        detail_surface = self.small_font.render(line, True, WHITE)
                        screen.blit(detail_surface, (410, detail_y))
                        detail_y += 18
            else:
                detail_surface = self.small_font.render(detail, True, WHITE)
                screen.blit(detail_surface, (410, detail_y))
                detail_y += 20

        # Effect value
        if selected_item.effect_value > 0:
            if selected_item.item_type in ["health_potion", "mana_potion"]:
                effect_text = f"Restores: {selected_item.effect_value} points"
            elif selected_item.item_type == "weapon":
                effect_text = f"Weapon Damage: +{selected_item.effect_value}"
            elif selected_item.item_type == "armor":
                effect_text = f"Armor Class: +{selected_item.effect_value}"
            else:
                effect_text = f"Effect Value: {selected_item.effect_value}"

            effect_surface = self.small_font.render(effect_text, True, LIGHT_BLUE)
            screen.blit(effect_surface, (410, detail_y))
            detail_y += 25

        # Stat bonuses if applicable
        if selected_item.stat_bonuses:
            detail_y += 10
            bonus_title = self.small_font.render("Stat Bonuses:", True, MENU_SELECTED)
            screen.blit(bonus_title, (410, detail_y))
            detail_y += 20

            for stat, bonus in selected_item.stat_bonuses.items():
                bonus_text = f"+{bonus} {stat.title()}"
                bonus_surface = self.small_font.render(bonus_text, True, GREEN)
                screen.blit(bonus_surface, (420, detail_y))
                detail_y += 18

        # Purchase status
        detail_y += 20
        if current_credits >= selected_item.price:
            status_text = "✅ Can afford this item"
            status_color = GREEN
        else:
            needed = selected_item.price - current_credits
            status_text = f"❌ Need {needed} more credits"
            status_color = RED

        status_surface = self.small_font.render(status_text, True, status_color)
        screen.blit(status_surface, (410, detail_y))

    def _draw_instructions(self, screen, width, height):
        """Draw control instructions"""
        instructions = [
            "↑↓: Navigate items  PgUp/PgDn: Scroll page",
            "ENTER: Purchase item  🔴 ESC: Return to game"
        ]

        instruction_y = height - 50
        for i, instruction in enumerate(instructions):
            color = MENU_SELECTED if "ESC" in instruction else WHITE
            instruction_surface = self.small_font.render(instruction, True, color)
            instruction_rect = instruction_surface.get_rect(center=(width // 2, instruction_y))
            screen.blit(instruction_surface, instruction_rect)
            instruction_y += 18

        # Item counter
        counter_text = f"Item {self.selected_item + 1} of {len(self.items)}"
        counter_surface = pygame.font.Font(None, 16).render(counter_text, True, MENU_TEXT)
        screen.blit(counter_surface, (width - 150, 100))


class StoreIntegration:
    """Integration class to connect store with main game"""

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.store_manager = StoreManager(game_manager.character_manager)
        self.exit_cooldown = 0

    def handle_store_input(self, key):
        """Handle store input and return appropriate game action"""
        result = self.store_manager.handle_input(key)

        if result == "exit":
            # Move player away from store to prevent collision loop
            self.game_manager.animated_player.x = max(0, self.game_manager.animated_player.x - 60)

            # Update camera to follow the moved player
            self.game_manager.camera.update(
                self.game_manager.animated_player.x + self.game_manager.animated_player.display_width // 2,
                self.game_manager.animated_player.y + self.game_manager.animated_player.display_height // 2
            )

            # Set cooldown to prevent immediate re-entry
            self.exit_cooldown = 30
            return "exit_store"

        elif isinstance(result, dict):
            if result["result"] == "purchased":
                # Add visual feedback for purchase
                self.game_manager.damage_texts.append(
                    DamageText(400, 300, f"Purchased {result['item']}!", GREEN)
                )
                return "purchased"
            elif result["result"] == "insufficient_funds":
                # Add visual feedback for insufficient funds
                self.game_manager.damage_texts.append(
                    DamageText(400, 300, "Not enough credits!", RED)
                )
                return "insufficient_funds"

        return "continue"

    def update(self):
        """Update store cooldowns"""
        if self.exit_cooldown > 0:
            self.exit_cooldown -= 1

    def draw_store(self, screen):
        """Draw the store interface"""
        self.store_manager.draw_store_screen(screen, screen.get_width(), screen.get_height())