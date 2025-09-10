"""
Crafting System for Magitech RPG
Handles crafting materials, recipes, and the crafting interface
"""

import pygame
import json
import random
from Code.ui_components import *


class CraftingMaterial:
    """Represents a crafting material with properties"""

    def __init__(self, name, rarity="Common", description="", color=GRAY):
        self.name = name
        self.rarity = rarity
        self.description = description
        self.color = color


class CraftingRecipe:
    """Represents a crafting recipe"""

    def __init__(self, name, materials_required, result_item, result_quantity=1,
                 level_required=1, description="", recipe_type="Equipment"):
        self.name = name
        self.materials_required = materials_required  # Dict: {material_name: quantity}
        self.result_item = result_item
        self.result_quantity = result_quantity
        self.level_required = level_required
        self.description = description
        self.recipe_type = recipe_type


class CraftingManager:
    """Manages the crafting system"""

    def __init__(self, character_manager):
        self.character_manager = character_manager
        self.crafting_materials = self._initialize_materials()
        self.recipes = self._initialize_recipes()
        self.crafting_active = False
        self.selected_recipe_index = 0
        self.scroll_offset = 0
        self.max_visible_recipes = 8

    def _initialize_materials(self):
        """Initialize crafting materials"""
        materials = {
            # Common materials
            "Iron Ore": CraftingMaterial("Iron Ore", "Common", "Basic metal ore for crafting", GRAY),
            "Wood": CraftingMaterial("Wood", "Common", "Sturdy wood for crafting", (139, 69, 19)),
            "Leather": CraftingMaterial("Leather", "Common", "Flexible leather for armor", (160, 82, 45)),
            "Cloth": CraftingMaterial("Cloth", "Common", "Basic fabric for robes", WHITE),
            "Stone": CraftingMaterial("Stone", "Common", "Hard stone for weapons", GRAY),

            # Uncommon materials
            "Silver Ore": CraftingMaterial("Silver Ore", "Uncommon", "Precious silver ore", (192, 192, 192)),
            "Mithril Shard": CraftingMaterial("Mithril Shard", "Uncommon", "Lightweight magical metal", LIGHT_BLUE),
            "Crystal Fragment": CraftingMaterial("Crystal Fragment", "Uncommon", "Magical crystal piece", PURPLE),
            "Dragon Scale": CraftingMaterial("Dragon Scale", "Uncommon", "Tough protective scale", GREEN),

            # Rare materials
            "Gold Ore": CraftingMaterial("Gold Ore", "Rare", "Valuable gold ore", GOLD),
            "Phoenix Feather": CraftingMaterial("Phoenix Feather", "Rare", "Magical fire-resistant feather", RED),
            "Void Crystal": CraftingMaterial("Void Crystal", "Rare", "Dark magical crystal", PURPLE),
            "Adamantine": CraftingMaterial("Adamantine", "Rare", "Strongest known metal", (50, 50, 50)),

            # Legendary materials
            "Starfire Essence": CraftingMaterial("Starfire Essence", "Legendary", "Pure cosmic energy", (255, 215, 0)),
            "Time Crystal": CraftingMaterial("Time Crystal", "Legendary", "Crystal that bends time", (0, 255, 255)),
        }
        return materials

    def _initialize_recipes(self):
        """Initialize crafting recipes"""
        recipes = [
            # Weapon recipes
            CraftingRecipe("Iron Sword", {"Iron Ore": 3, "Wood": 1}, "Iron Sword", 1, 1, "Basic iron sword", "Weapon"),
            CraftingRecipe("Silver Blade", {"Silver Ore": 2, "Iron Ore": 1, "Wood": 1}, "Silver Blade", 1, 3, "Sharp silver sword", "Weapon"),
            CraftingRecipe("Mithril Staff", {"Mithril Shard": 2, "Wood": 2, "Crystal Fragment": 1}, "Mithril Staff", 1, 5, "Lightweight magical staff", "Weapon"),
            CraftingRecipe("Dragon Slayer", {"Adamantine": 3, "Dragon Scale": 2, "Gold Ore": 1}, "Dragon Slayer", 1, 8, "Legendary dragon-slaying sword", "Weapon"),

            # Armor recipes
            CraftingRecipe("Leather Armor", {"Leather": 4, "Cloth": 2}, "Leather Armor", 1, 1, "Basic leather protection", "Armor"),
            CraftingRecipe("Iron Chainmail", {"Iron Ore": 5, "Leather": 2}, "Iron Chainmail", 1, 3, "Strong metal armor", "Armor"),
            CraftingRecipe("Mithril Plate", {"Mithril Shard": 4, "Silver Ore": 2, "Leather": 1}, "Mithril Plate", 1, 6, "Lightweight magical armor", "Armor"),
            CraftingRecipe("Phoenix Robes", {"Phoenix Feather": 3, "Cloth": 4, "Gold Ore": 1}, "Phoenix Robes", 1, 7, "Fire-resistant magical robes", "Armor"),

            # Accessory recipes
            CraftingRecipe("Crystal Ring", {"Crystal Fragment": 2, "Silver Ore": 1}, "Crystal Ring", 1, 2, "Ring that boosts mana", "Accessory"),
            CraftingRecipe("Gold Amulet", {"Gold Ore": 3, "Dragon Scale": 1}, "Gold Amulet", 1, 4, "Amulet that boosts health", "Accessory"),
            CraftingRecipe("Void Pendant", {"Void Crystal": 2, "Adamantine": 1, "Phoenix Feather": 1}, "Void Pendant", 1, 9, "Dark magical pendant", "Accessory"),

            # Consumable recipes
            CraftingRecipe("Enhanced Health Potion", {"Phoenix Feather": 1, "Crystal Fragment": 1}, "Enhanced Health Potion", 3, 4, "Powerful healing potion", "Consumable"),
            CraftingRecipe("Mana Crystal", {"Crystal Fragment": 2, "Mithril Shard": 1}, "Mana Crystal", 2, 3, "Restores large amount of mana", "Consumable"),
            CraftingRecipe("Starfire Elixir", {"Starfire Essence": 1, "Phoenix Feather": 1, "Time Crystal": 1}, "Starfire Elixir", 1, 10, "Ultimate power elixir", "Consumable"),
        ]
        return recipes

    def get_available_recipes(self):
        """Get recipes the player can potentially craft based on level"""
        if not self.character_manager.character_data:
            return []

        player_level = self.character_manager.character_data.get("Level", 1)
        return [recipe for recipe in self.recipes if recipe.level_required <= player_level]

    def can_craft_recipe(self, recipe):
        """Check if player has materials to craft a recipe"""
        if not self.character_manager.character_data:
            return False

        from inventory_system import InventoryManager
        inventory_manager = InventoryManager(self.character_manager)

        for material_name, required_quantity in recipe.materials_required.items():
            if inventory_manager.get_item_quantity(material_name) < required_quantity:
                return False
        return True

    def craft_item(self, recipe):
        """Attempt to craft an item"""
        if not self.can_craft_recipe(recipe):
            return False, "Insufficient materials!"

        from inventory_system import InventoryManager
        inventory_manager = InventoryManager(self.character_manager)

        # Remove materials from inventory
        for material_name, required_quantity in recipe.materials_required.items():
            inventory_manager.remove_item(material_name, required_quantity)

        # Add crafted item to inventory
        inventory_manager.add_item(recipe.result_item, recipe.result_quantity)

        # Save character data
        self.character_manager.save_character()

        return True, f"Successfully crafted {recipe.result_item}!"

    def add_crafting_material(self, material_name, quantity=1):
        """Add crafting material to player inventory"""
        if not self.character_manager.character_data:
            return False

        from inventory_system import InventoryManager
        inventory_manager = InventoryManager(self.character_manager)
        return inventory_manager.add_item(material_name, quantity)

    def get_material_rarity_color(self, material_name):
        """Get color based on material rarity"""
        if material_name in self.crafting_materials:
            return self.crafting_materials[material_name].color
        return WHITE


class CraftingIntegration:
    """Integrates crafting system with main game"""

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.crafting_manager = CraftingManager(game_manager.character_manager)

    def handle_crafting_input(self, keys_pressed, key_events):
        """Handle input for crafting interface"""
        if not self.crafting_manager.crafting_active:
            return

        available_recipes = self.crafting_manager.get_available_recipes()
        if not available_recipes:
            return

        for event in key_events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.crafting_manager.selected_recipe_index = max(0, self.crafting_manager.selected_recipe_index - 1)
                    if self.crafting_manager.selected_recipe_index < self.crafting_manager.scroll_offset:
                        self.crafting_manager.scroll_offset = self.crafting_manager.selected_recipe_index

                elif event.key == pygame.K_DOWN:
                    max_index = len(available_recipes) - 1
                    self.crafting_manager.selected_recipe_index = min(max_index, self.crafting_manager.selected_recipe_index + 1)
                    if self.crafting_manager.selected_recipe_index >= self.crafting_manager.scroll_offset + self.crafting_manager.max_visible_recipes:
                        self.crafting_manager.scroll_offset = self.crafting_manager.selected_recipe_index - self.crafting_manager.max_visible_recipes + 1

                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Craft selected recipe
                    if 0 <= self.crafting_manager.selected_recipe_index < len(available_recipes):
                        recipe = available_recipes[self.crafting_manager.selected_recipe_index]
                        success, message = self.crafting_manager.craft_item(recipe)
                        if hasattr(self.game_manager, 'combat_integration'):
                            self.game_manager.combat_integration.sound_manager.play_sound("menu_select" if success else "sword_miss")
                        return message

                elif event.key == pygame.K_ESCAPE:
                    self.crafting_manager.crafting_active = False
                    return "Closed crafting interface"

        return None

    def draw_crafting_interface(self, screen):
        """Draw the crafting interface"""
        if not self.crafting_manager.crafting_active:
            return

        # Semi-transparent background
        overlay = pygame.Surface((screen.get_width(), screen.get_height()))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))

        # Main crafting panel
        panel_width, panel_height = 600, 500
        panel_x = (screen.get_width() - panel_width) // 2
        panel_y = (screen.get_height() - panel_height) // 2

        pygame.draw.rect(screen, MENU_BG, (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(screen, MENU_ACCENT, (panel_x, panel_y, panel_width, panel_height), 3)

        # Title
        title_font = pygame.font.Font(None, 36)
        title = title_font.render("Crafting Workshop", True, MENU_SELECTED)
        title_rect = title.get_rect(center=(panel_x + panel_width // 2, panel_y + 30))
        screen.blit(title, title_rect)

        # Get available recipes
        available_recipes = self.crafting_manager.get_available_recipes()

        if not available_recipes:
            no_recipes = pygame.font.Font(None, 24).render("No recipes available at your level", True, RED)
            no_recipes_rect = no_recipes.get_rect(center=(panel_x + panel_width // 2, panel_y + panel_height // 2))
            screen.blit(no_recipes, no_recipes_rect)
            return

        # Recipe list
        recipe_y_start = panel_y + 70
        recipe_font = pygame.font.Font(None, 20)
        small_font = pygame.font.Font(None, 16)

        visible_recipes = available_recipes[self.crafting_manager.scroll_offset:self.crafting_manager.scroll_offset + self.crafting_manager.max_visible_recipes]

        for i, recipe in enumerate(visible_recipes):
            actual_index = i + self.crafting_manager.scroll_offset
            recipe_y = recipe_y_start + i * 50

            # Selection highlight
            if actual_index == self.crafting_manager.selected_recipe_index:
                highlight_rect = pygame.Rect(panel_x + 10, recipe_y - 5, panel_width - 20, 45)
                pygame.draw.rect(screen, MENU_HIGHLIGHT, highlight_rect)
                pygame.draw.rect(screen, MENU_SELECTED, highlight_rect, 2)

            # Recipe name
            can_craft = self.crafting_manager.can_craft_recipe(recipe)
            name_color = GREEN if can_craft else RED
            name_text = recipe_font.render(recipe.name, True, name_color)
            screen.blit(name_text, (panel_x + 20, recipe_y))

            # Required materials
            materials_text = ", ".join([f"{name} ({qty})" for name, qty in recipe.materials_required.items()])
            materials_surface = small_font.render(f"Requires: {materials_text}", True, MENU_TEXT)
            screen.blit(materials_surface, (panel_x + 20, recipe_y + 20))

            # Level requirement
            level_text = small_font.render(f"Level {recipe.level_required}", True, YELLOW)
            screen.blit(level_text, (panel_x + panel_width - 100, recipe_y))

        # Instructions
        instructions = [
            "Arrow Keys: Navigate recipes",
            "ENTER/SPACE: Craft selected item",
            "ESC: Close crafting"
        ]

        instruction_y = panel_y + panel_height - 80
        instruction_font = pygame.font.Font(None, 18)
        for instruction in instructions:
            instruction_surface = instruction_font.render(instruction, True, LIGHT_BLUE)
            screen.blit(instruction_surface, (panel_x + 20, instruction_y))
            instruction_y += 20


class CraftingNode:
    """Harvestable crafting material node on the world map"""

    def __init__(self, x, y, material_name, respawn_time=3000):
        import math
        self.x = x
        self.y = y
        self.width = 25
        self.height = 25
        self.material_name = material_name
        self.active = True
        self.respawn_timer = 0
        # self.max_respawn_time = respawn_time  # 5 minutes at 15 FPS
        self.max_respawn_time = 3000  # 5 minutes at 15 FPS

        # Material colors based on type
        material_colors = {
            "Iron Ore": GRAY, "Wood": (139, 69, 19), "Leather": (160, 82, 45),
            "Cloth": WHITE, "Stone": GRAY, "Silver Ore": (192, 192, 192),
            "Mithril Shard": LIGHT_BLUE, "Crystal Fragment": PURPLE, "Dragon Scale": GREEN,
            "Gold Ore": GOLD, "Phoenix Feather": RED, "Void Crystal": PURPLE,
            "Adamantine": (50, 50, 50), "Starfire Essence": (255, 215, 0), "Time Crystal": (0, 255, 255)
        }

        self.color = material_colors.get(material_name, WHITE)

        # Determine rarity for visual effects
        common = ["Iron Ore", "Wood", "Leather", "Cloth", "Stone"]
        uncommon = ["Silver Ore", "Mithril Shard", "Crystal Fragment", "Dragon Scale"]
        rare = ["Gold Ore", "Phoenix Feather", "Void Crystal", "Adamantine"]
        legendary = ["Starfire Essence", "Time Crystal"]

        if material_name in common:
            self.rarity = "Common"
        elif material_name in uncommon:
            self.rarity = "Uncommon"
        elif material_name in rare:
            self.rarity = "Rare"
        else:
            self.rarity = "Legendary"

    def update(self):
        """Update respawn timer"""
        if not self.active and self.respawn_timer > 0:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.active = True

    def harvest(self):
        """Harvest the material and start respawn timer"""
        if self.active:
            self.active = False
            self.respawn_timer = self.max_respawn_time
            return self.material_name
        return None

    def draw(self, screen, camera, animation_timer=0):
        """Draw the crafting node"""
        if not self.active:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        if camera.is_visible(self.x, self.y, self.width, self.height):
            import math
            # Pulsing effect based on rarity
            pulse_intensity = 1.0
            if self.rarity == "Uncommon":
                pulse_intensity = 1.2
            elif self.rarity == "Rare":
                pulse_intensity = 1.5
            elif self.rarity == "Legendary":
                pulse_intensity = 2.0

            pulse = int(3 * abs(math.sin(animation_timer * 0.1 * pulse_intensity)))
            node_size = 10 + pulse

            # Draw outer glow
            pygame.draw.circle(screen, self.color,
                             (int(screen_x + 10), int(screen_y + 10)), node_size + 2)
            # Draw inner core
            pygame.draw.circle(screen, WHITE,
                             (int(screen_x + 10), int(screen_y + 10)), node_size - 3)
            # Draw center dot
            pygame.draw.circle(screen, self.color,
                             (int(screen_x + 10), int(screen_y + 10)), 3)


def get_random_crafting_material(enemy_level=1, from_treasure=False):
    """Get a random crafting material based on enemy level or treasure type"""
    # Define material pools by rarity
    common_materials = ["Iron Ore", "Wood", "Leather", "Cloth", "Stone"]
    uncommon_materials = ["Silver Ore", "Mithril Shard", "Crystal Fragment", "Dragon Scale"]
    rare_materials = ["Gold Ore", "Phoenix Feather", "Void Crystal", "Adamantine"]
    legendary_materials = ["Starfire Essence", "Time Crystal"]

    # Determine drop chances based on source
    if from_treasure:
        # Treasures have slightly better chances
        if random.randint(1, 100) <= 5:  # 5% legendary
            return random.choice(legendary_materials)
        elif random.randint(1, 100) <= 15:  # 15% rare
            return random.choice(rare_materials)
        elif random.randint(1, 100) <= 35:  # 35% uncommon
            return random.choice(uncommon_materials)
        else:  # 45% common
            return random.choice(common_materials)
    else:
        # Enemy drops based on level
        if enemy_level >= 8 and random.randint(1, 100) <= 2:  # 2% legendary from high-level enemies
            return random.choice(legendary_materials)
        elif enemy_level >= 5 and random.randint(1, 100) <= 8:  # 8% rare from mid-high level enemies
            return random.choice(rare_materials)
        elif enemy_level >= 3 and random.randint(1, 100) <= 25:  # 25% uncommon from mid-level enemies
            return random.choice(uncommon_materials)
        elif random.randint(1, 100) <= 60:  # 60% common from any enemy
            return random.choice(common_materials)

    return None  # No material dropped