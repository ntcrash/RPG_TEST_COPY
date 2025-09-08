import pygame
import sys
import math
import random
import os

# Import our custom modules
from animated_player import AnimatedPlayer
from tile_map import EnhancedTileMap
from ui_components import *
from game_data import CharacterManager, EnemyManager, create_sample_files
from character_creation import CharacterCreation
# Store system now imported from inventory_system.py
from enhanced_combat_integration import integrate_enhanced_combat_with_game_states, setup_enhanced_audio_system
from rest_system import RestManager, EnhancedRestArea
from level_system import LevelManager, WorldLevelGenerator, LevelSelectScreen
from settings_system import SettingsIntegration


class GameState:
    """Game state constants"""
    OPENING = 0
    MAIN_MENU = 1
    CHARACTER_SELECT = 2
    CREATE_CHARACTER = 3
    GAME_BOARD = 4
    FIGHT = 5
    STORE = 6
    INVENTORY = 7
    CHARACTER_SHEET = 8
    HELP = 9
    LEVEL_SELECT = 10
    SETTINGS = 11
    CRAFTING = 12


def is_too_close(x, y, positions, min_distance=20):
    """Check if (x,y) is too close to any position in positions."""
    for px, py in positions:
        if math.dist((x, y), (px, py)) < min_distance:
            return True
    return False


def load_help_text(filepath="HELP.md") -> list[str]:
    """Load help text from a markdown file into a list of strings."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.rstrip("\n") for line in f]
    except FileNotFoundError:
        return ["Help file not found."]


def load_changelog_text(filepath="CHANGELOG.md") -> list[str]:
    """Load Changelog text from a markdown file into a list of strings."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.rstrip("\n") for line in f]
    except FileNotFoundError:
        return ["Changelog file not found."]


class EnhancedGameManager:
    """Main game manager with modular architecture and enhanced combat"""

    def __init__(self):
        # Initialize Pygame
        pygame.init()

        # Screen settings
        self.WIDTH, self.HEIGHT = 800, 600
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Magitech RPG - Multi-Level Edition")

        # Game state
        self.current_state = GameState.OPENING
        self.selected_option = 0
        self.animation_timer = 0

        # UI settings
        self.show_instructions = False  # Setting to toggle instructions

        # Initialize subsystems
        self.character_manager = CharacterManager()
        self.enemy_manager = EnemyManager()

        # Initialize level system with character-specific progression
        character_name = None
        if hasattr(self, 'character_manager') and self.character_manager.character_data:
            character_name = self.character_manager.character_data.get('Name')
        self.level_manager = LevelManager(character_name=character_name)
        self.world_generator = WorldLevelGenerator(self.level_manager)
        self.level_select_screen = None

        # Initialize rest system
        self.rest_manager = RestManager(self.character_manager)

        # Initialize crafting system
        from crafting_system import CraftingIntegration
        self.crafting_integration = CraftingIntegration(self)

        # Initialize visual systems
        self.ui_renderer = UIRenderer(self.WIDTH, self.HEIGHT)
        self.particles = ParticleSystem()
        self.damage_texts = []

        # Character selection variables
        self.available_characters = []
        self.selected_character = 0

        # Character creation system
        self.character_creator = None

        # Initialize player and world
        self.animated_player = AnimatedPlayer('Images/80SpriteSheetNEW.png')
        # Start player in center of larger world
        world_center_x = 480  # 40 tiles * 24 pixels / 2 = 480
        world_center_y = 480  # 40 tiles * 24 pixels / 2 = 480
        self.animated_player.x = world_center_x
        self.animated_player.y = world_center_y

        # Initialize tile map
        self.tile_map = EnhancedTileMap()
        self.map_tiles = None
        self.current_level_content = None
        self.load_map_data()

        # Initialize camera
        world_width, world_height = self.tile_map.get_world_pixel_size()
        self.camera = Camera(self.WIDTH, self.HEIGHT, world_width, world_height)

        # Game objects
        self.world_objects = []
        self.enemies = []
        self.treasures = []
        self.shops = []
        self.rests = []
        self.trees = []  # New list for trees
        self.crafting_nodes = []  # New list for crafting material nodes

        # Combat system variables (for legacy compatibility)
        self.current_enemy = None
        self.combat_messages = []

        # Setup initial world
        self.setup_world_for_current_level()

        # FINAL SAFETY CHECK - Always ensure shop exists
        world_width, world_height = self.tile_map.get_world_pixel_size()
        if len(self.shops) == 0:
            print("INITIALIZATION SHOP CREATION - no shops after initial setup")
            init_shop = Shop(world_width - 80, 20)
            init_shop.active = True
            self.shops.append(init_shop)
            print(f"Initialization shop created at ({world_width - 80}, 20)")

        print(f"=== GAME INITIALIZATION COMPLETE ===")
        print(
            f"Final object counts: {len(self.enemies)} enemies, {len(self.treasures)} treasures, {len(self.shops)} shops, {len(self.rests)} rest areas, {len(self.trees)} trees")
        if len(self.shops) > 0:
            for i, shop in enumerate(self.shops):
                print(f"  Shop {i}: pos=({shop.x}, {shop.y}), active={shop.active}")
        print("=========================================")

        # Static objects that should always be present
        # Note: Static shop is added in setup methods, no need to add here again

        # Initialize enhanced combat integration system
        integrate_enhanced_combat_with_game_states(self)
        setup_enhanced_audio_system(self)

        # Initialize store integration
        from inventory_system import StoreIntegration
        self.store_integration = StoreIntegration(self)

        # Initialize settings integration
        self.settings_integration = SettingsIntegration(self)

        # Load settings
        self.load_settings()

    def load_character_list(self):
        """Load list of available characters"""
        self.available_characters = self.character_manager.get_character_list()
        self.selected_character = 0

    def load_map_data(self):
        """Load map data and create tiles"""
        self.map_tiles = self.tile_map.load_map_from_file("map.txt")

    def setup_world_for_current_level(self):
        """Setup game world based on current level"""
        current_level = self.level_manager.get_current_level()
        if not current_level:
            # Fallback to default setup
            self.setup_world_objects()
            return

        # Generate content for current level
        self.current_level_content = self.world_generator.generate_level_content(current_level)

        # Set enemy manager difficulty and theme
        world_level_difficulty = (current_level.world - 1) * 4 + current_level.level
        self.enemy_manager.set_difficulty_level(world_level_difficulty)

        # Set world theme based on current world
        theme_mapping = {1: "grassland", 2: "ice", 3: "shadow", 4: "elemental", 5: "cosmic"}
        world_theme = theme_mapping.get(current_level.world, "grassland")
        self.enemy_manager.set_world_theme(world_theme)

        # Setup world objects based on generated content
        self.setup_enhanced_world_objects()

    def setup_enhanced_world_objects(self):
        """Setup enhanced world objects based on level content"""
        # Clear existing objects
        self.enemies.clear()
        self.treasures.clear()
        self.shops.clear()
        self.rests.clear()
        self.trees.clear()  # Clear trees too
        self.crafting_nodes.clear()  # Clear crafting nodes too

        if not self.current_level_content:
            self.setup_world_objects()  # Fallback
            return

        # Create enemies based on level content
        enemy_count = self.current_level_content["enemy_count"]
        enemy_types = self.current_level_content["enemy_types"]

        enemy_positions = []
        max_attempts = 1000
        attempts = 0

        while len(enemy_positions) < enemy_count and attempts < max_attempts:
            attempts += 1
            x = random.randint(50, 750)
            y = random.randint(50, 550)

            if not is_too_close(x, y, enemy_positions, min_distance=30):
                enemy_positions.append((x, y))

        # Create enemies with appropriate types
        for x, y in enemy_positions:
            enemy_type = random.choice(enemy_types)
            if enemy_type == "boss":
                enemy_data = self.enemy_manager.create_scaled_boss()
            else:
                enemy_data = self.enemy_manager.create_scaled_enemy()

            # Apply level multipliers
            current_level = self.level_manager.get_current_level()
            if current_level:
                enemy_data["Hit_Points"] = int(enemy_data["Hit_Points"] * current_level.enemy_multiplier)
                enemy_data["Level"] = max(1, int(enemy_data["Level"] * current_level.enemy_multiplier))

            enemy = Enemy(x, y, enemy_data)
            self.enemies.append(enemy)

        # Create treasures based on level content
        treasure_count = self.current_level_content["treasure_count"]
        treasure_positions = []

        attempts = 0
        while len(treasure_positions) < treasure_count and attempts < max_attempts:
            attempts += 1
            x = random.randint(50, 750)
            y = random.randint(50, 550)

            all_positions = enemy_positions + treasure_positions
            if not is_too_close(x, y, all_positions, min_distance=25):
                treasure_positions.append((x, y))

        for x, y in treasure_positions:
            # Apply loot multiplier to treasure value
            base_value = random.randint(50, 150)
            current_level = self.level_manager.get_current_level()
            if current_level:
                treasure_value = int(base_value * current_level.loot_multiplier)
            else:
                treasure_value = base_value

            treasure = Treasure(x, y, treasure_value)
            self.treasures.append(treasure)

        # Create trees for environmental decoration
        self.create_trees(enemy_positions + treasure_positions)

        # Create crafting material nodes
        all_positions = enemy_positions + treasure_positions + [(tree.x, tree.y) for tree in self.trees]
        self.create_crafting_nodes(all_positions)

        # Create rest areas - multiple rest areas for higher levels
        world_width, world_height = self.tile_map.get_world_pixel_size()
        current_level = self.level_manager.get_current_level()

        # Number of rest areas based on world difficulty
        rest_area_count = 1 + (current_level.world - 1) if current_level else 1
        rest_positions = [
            (world_width - 120, world_height - 120),  # Bottom-right (always)
            (80, world_height - 120),  # Bottom-left
            (world_width - 120, 80),  # Top-right
            (80, 80),  # Top-left
            (world_width // 2, world_height // 2),  # Center
        ]

        all_object_positions = enemy_positions + treasure_positions

        # Ensure at least one rest area is always created
        rests_created = 0
        for i in range(min(rest_area_count, len(rest_positions))):
            rest_x, rest_y = rest_positions[i]

            # For the first rest area, create it regardless of proximity to ensure at least one exists
            if i == 0 or not is_too_close(rest_x, rest_y, all_object_positions, min_distance=60):
                rest_area = EnhancedRestArea(rest_x, rest_y, self.rest_manager)
                self.rests.append(rest_area)
                rests_created += 1

        # Fallback: If no rest areas were created (shouldn't happen now), force create one at bottom-right
        if rests_created == 0:
            fallback_rest = EnhancedRestArea(world_width - 120, world_height - 120, self.rest_manager)
            self.rests.append(fallback_rest)

    def create_trees(self, existing_positions):
        """Create trees for environmental decoration"""
        current_level = self.level_manager.get_current_level()

        # Determine tree count and types based on world theme
        if current_level:
            if current_level.world == 1:  # Grassland
                tree_count = random.randint(15, 25)
                tree_types = ["normal", "oak", "normal", "oak", "normal"]
            elif current_level.world == 2:  # Ice world
                tree_count = random.randint(8, 15)
                tree_types = ["pine", "pine", "pine"]  # Mostly pine trees for ice world
            elif current_level.world == 3:  # Shadow realm
                tree_count = random.randint(12, 20)
                tree_types = ["normal", "oak"]  # Darker looking trees
            elif current_level.world == 4:  # Elemental chaos
                tree_count = random.randint(5, 12)
                tree_types = ["normal", "pine", "oak"]  # Mixed types
            else:  # Cosmic world
                tree_count = random.randint(3, 8)
                tree_types = ["oak", "normal"]  # Fewer, more mystical trees
        else:
            # Default fallback
            tree_count = random.randint(12, 20)
            tree_types = ["normal", "oak", "pine"]

        tree_positions = []
        max_attempts = 1000
        attempts = 0

        while len(tree_positions) < tree_count and attempts < max_attempts:
            attempts += 1
            x = random.randint(60, 740)  # Leave border space
            y = random.randint(60, 540)

            # Check distance from all existing objects (enemies, treasures, rest areas)
            all_positions = existing_positions + tree_positions

            # Trees need more space since they're larger
            if not is_too_close(x, y, all_positions, min_distance=45):
                # Also avoid the player starting area
                player_start_x, player_start_y = 480, 480
                if math.dist((x, y), (player_start_x, player_start_y)) > 80:
                    tree_positions.append((x, y))

        # Create trees with varied types
        for x, y in tree_positions:
            tree_type = random.choice(tree_types)
            tree = Tree(x, y, tree_type)
            self.trees.append(tree)

        print(f"Created {len(self.trees)} trees of types: {set(tree.tree_type for tree in self.trees)}")

    def create_crafting_nodes(self, existing_positions):
        """Create harvestable crafting material nodes"""
        from crafting_system import CraftingNode

        # Determine number of crafting nodes based on level
        current_level = self.level_manager.get_current_level()
        if current_level:
            node_count = random.randint(8, 15)
        else:
            node_count = random.randint(8, 12)

        node_positions = []
        max_attempts = 1000
        attempts = 0

        while len(node_positions) < node_count and attempts < max_attempts:
            attempts += 1
            x = random.randint(40, 760)
            y = random.randint(40, 560)

            # Check distance from all existing objects
            all_positions = existing_positions + node_positions
            if not is_too_close(x, y, all_positions, min_distance=35):
                node_positions.append((x, y))

        # Create crafting nodes with varied materials
        common_materials = ["Iron Ore", "Wood", "Leather", "Cloth", "Stone"]
        uncommon_materials = ["Silver Ore", "Mithril Shard", "Crystal Fragment", "Dragon Scale"]
        rare_materials = ["Gold Ore", "Phoenix Feather", "Void Crystal"]

        for x, y in node_positions:
            # 70% common, 20% uncommon, 8% rare, 2% legendary
            roll = random.randint(1, 100)
            if roll <= 70:
                material = random.choice(common_materials)
            elif roll <= 90:
                material = random.choice(uncommon_materials)
            elif roll <= 98:
                material = random.choice(rare_materials)
            else:
                material = random.choice(["Starfire Essence", "Time Crystal"])

            # Longer respawn time for rarer materials
            if material in rare_materials:
                respawn_time = 1200  # 20 minutes
            elif material in uncommon_materials:
                respawn_time = 900  # 15 minutes
            else:
                respawn_time = 600  # 10 minutes

            crafting_node = CraftingNode(x, y, material, respawn_time)
            self.crafting_nodes.append(crafting_node)

        print(f"Created {len(self.crafting_nodes)} crafting material nodes")

    def setup_world_objects(self):
        """Setup game world objects based on map (fallback method)"""
        # Clear existing objects
        self.enemies.clear()
        self.treasures.clear()
        self.shops.clear()
        self.rests.clear()
        self.trees.clear()

        # Parse map for object positions
        object_positions = self.tile_map.parse_map_for_objects()

        # Create treasures - make them smaller
        treasure_positions = object_positions.get('treasures', [])
        if not treasure_positions:
            # Add some manual treasure positions
            treasure_positions = [
                (random.randint(50, 750), random.randint(50, 550))
                for _ in range(8)
            ]

        for x, y in treasure_positions:
            treasure = Treasure(x, y)
            self.treasures.append(treasure)

        # Create enemies - ensure they spawn
        enemy_positions = object_positions.get('enemies', [])
        if not enemy_positions:
            # Generate enemy positions with spacing rules
            enemy_positions = []
            num_enemies = 18
            max_attempts = 1000

            attempts = 0
            while len(enemy_positions) < num_enemies and attempts < max_attempts:
                attempts += 1
                x = random.randint(50, 750)
                y = random.randint(50, 550)

                # Check distance from treasures and already-placed enemies
                if not is_too_close(x, y, treasure_positions, min_distance=20) and \
                        not is_too_close(x, y, enemy_positions, min_distance=20):
                    enemy_positions.append((x, y))

            # Create enemies
            for x, y in enemy_positions:
                enemy = Enemy(x, y, self.enemy_manager.create_scaled_enemy())
                self.enemies.append(enemy)

        # Create trees (fallback version with default settings)
        self.create_trees(enemy_positions + treasure_positions)

        # Create crafting nodes (fallback)
        all_positions = enemy_positions + treasure_positions + [(tree.x, tree.y) for tree in self.trees]
        self.create_crafting_nodes(all_positions)

        # Create rest areas - single rest area in bottom-right
        world_width, world_height = self.tile_map.get_world_pixel_size()

        # Single rest area in bottom-right corner with some inset
        rest_x = world_width - 120
        rest_y = world_height - 120

        # Make sure rest area doesn't conflict with other objects
        too_close_to_existing = False
        for enemy in self.enemies:
            if math.dist((rest_x, rest_y), (enemy.x, enemy.y)) < 50:
                too_close_to_existing = True
                break

        for treasure in self.treasures:
            if math.dist((rest_x, rest_y), (treasure.x, treasure.y)) < 40:
                too_close_to_existing = True
                break

        # Create the rest area regardless of conflicts (move conflicting objects if needed)
        if too_close_to_existing:
            # Move any conflicting enemies or treasures
            for enemy in self.enemies[:]:
                if math.dist((rest_x, rest_y), (enemy.x, enemy.y)) < 50:
                    enemy.x = max(50, enemy.x - 80)  # Move enemy left

            for treasure in self.treasures[:]:
                if math.dist((rest_x, rest_y), (treasure.x, treasure.y)) < 40:
                    treasure.x = max(50, treasure.x - 60)  # Move treasure left

        # Create the single rest area
        rest_area = EnhancedRestArea(rest_x, rest_y, self.rest_manager)
        self.rests.append(rest_area)

    def check_tree_collision(self, player_rect):
        """Check if player is colliding with any trees"""
        for tree in self.trees:
            if tree.active and tree.is_blocking():
                if player_rect.colliderect(tree.get_rect()):
                    return tree
        return None

    def check_level_completion(self):
        """Check if current level is completed and handle progression"""
        # Level is completed when all enemies are defeated
        active_enemies = [enemy for enemy in self.enemies if enemy.active]

        if len(active_enemies) == 0 and len(self.enemies) > 0:
            # Level completed!
            current_level = self.level_manager.get_current_level()
            if current_level:
                # Award completion bonus
                if self.character_manager.character_data:
                    completion_bonus = int(200 * current_level.loot_multiplier)
                    self.character_manager.character_data["Credits"] += completion_bonus
                    self.character_manager.character_data["Experience_Points"] += int(
                        100 * current_level.enemy_multiplier)

                    # Visual feedback
                    damage_text = DamageText(0, 0, f"Level Complete! +{completion_bonus} Credits!", GOLD)
                    damage_text.world_pos = (self.animated_player.x, self.animated_player.y - 40)
                    self.damage_texts.append(damage_text)

                    # Check for level up
                    self.character_manager.level_up_check()
                    self.character_manager.save_character()

                # Unlock next level
                self.level_manager.complete_current_level()

                return True

        return False

    def change_level(self, world, level):
        """Change to a specific level"""
        if self.level_manager.set_current_level(world, level):
            # Reset player position to center
            world_center_x = 480
            world_center_y = 480
            self.animated_player.x = world_center_x
            self.animated_player.y = world_center_y

            # Setup new world
            self.setup_world_for_current_level()

            # Update camera
            self.camera.update(
                self.animated_player.x + self.animated_player.display_width // 2,
                self.animated_player.y + self.animated_player.display_height // 2
            )

            return True
        return False

    def check_collisions(self):
        """Check for collisions between player and world objects"""
        # Skip collision checks during store exit cooldown
        if (hasattr(self, 'store_integration') and self.store_integration and
                self.store_integration.exit_cooldown > 0):
            return None, None

        player_rect = pygame.Rect(self.animated_player.x, self.animated_player.y,
                                  self.animated_player.display_width, self.animated_player.display_height)

        # Check tree collisions first (blocking movement)
        tree_collision = self.check_tree_collision(player_rect)
        if tree_collision:
            return "tree", tree_collision

        # Check crafting node collisions
        for node in self.crafting_nodes:
            if node.active:
                node_rect = pygame.Rect(node.x, node.y, node.width, node.height)
                if player_rect.colliderect(node_rect):
                    return "crafting_node", node

        # Check rest area collisions first (highest priority for UX)
        for rest_area in self.rests:
            if rest_area.active:
                rest_rect = pygame.Rect(rest_area.x, rest_area.y, rest_area.width, rest_area.height)
                if player_rect.colliderect(rest_rect):
                    return "rest", rest_area

        # Check enemy collisions
        for enemy in self.enemies:
            if enemy.active:
                enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
                if player_rect.colliderect(enemy_rect):
                    return "enemy", enemy

        # Check treasure collisions
        for treasure in self.treasures:
            if treasure.active:
                treasure_rect = pygame.Rect(treasure.x, treasure.y, treasure.width, treasure.height)
                if player_rect.colliderect(treasure_rect):
                    return "treasure", treasure

        # Check shop collisions
        for shop in self.shops:
            if shop.active:
                shop_rect = pygame.Rect(shop.x, shop.y, shop.width, shop.height)
                if player_rect.colliderect(shop_rect):
                    return "shop", shop

        return None, None

    def handle_event(self, event):
        """Handle pygame events based on current state"""
        if event.type == pygame.KEYDOWN:
            return self.handle_keypress(event.key)
        elif self.current_state == GameState.CREATE_CHARACTER and self.character_creator:
            # Pass text input events to character creator
            if event.type == pygame.TEXTINPUT:
                result = self.character_creator.handle_event(event)
                if result:
                    return True
        return None

    def handle_keypress(self, key):
        """Handle keyboard input based on current state"""
        if self.current_state == GameState.OPENING:
            self.current_state = GameState.MAIN_MENU

        elif self.current_state == GameState.MAIN_MENU:
            if key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % 5  # Now 5 options
            elif key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % 5  # Now 5 options
            elif key == pygame.K_RETURN:
                if self.selected_option == 0:  # Start Game
                    self.load_character_list()
                    self.current_state = GameState.CHARACTER_SELECT

                elif self.selected_option == 1:  # Level Select
                    self.level_select_screen = LevelSelectScreen(self.level_manager, self.WIDTH, self.HEIGHT)
                    self.current_state = GameState.LEVEL_SELECT

                elif self.selected_option == 2:  # Settings
                    self.current_state = GameState.SETTINGS

                elif self.selected_option == 3:  # Help
                    self.current_state = GameState.HELP

                elif self.selected_option == 4:  # Quit
                    return False

            elif key == pygame.K_ESCAPE:
                return False

        elif self.current_state == GameState.CHARACTER_SELECT:
            if key == pygame.K_UP:
                self.selected_character = (self.selected_character - 1) % len(self.available_characters)
            elif key == pygame.K_DOWN:
                self.selected_character = (self.selected_character + 1) % len(self.available_characters)
            elif key == pygame.K_RETURN:
                selected_char = self.available_characters[self.selected_character]

                if selected_char == "New Character":
                    # Initialize character creator
                    self.character_creator = CharacterCreation(self.WIDTH, self.HEIGHT)
                    self.current_state = GameState.CREATE_CHARACTER
                else:
                    char_path = os.path.join("Characters", selected_char)
                    if self.character_manager.load_character(char_path):
                        # Update level manager with character-specific progression
                        character_name = self.character_manager.character_data.get('Name')
                        self.level_manager.set_character(character_name)
                        self.current_state = GameState.GAME_BOARD
                    else:
                        print(f"Failed to load character: {selected_char}")

            elif key == pygame.K_ESCAPE:
                self.current_state = GameState.MAIN_MENU

        elif self.current_state == GameState.CREATE_CHARACTER:
            if self.character_creator:
                result = self.character_creator.handle_keypress(key)

                if result == "create":
                    # Save character and start game
                    char_file = self.character_creator.save_character()
                    if char_file and self.character_manager.load_character(char_file):
                        # Update level manager with character-specific progression
                        character_name = self.character_manager.character_data.get('Name')
                        self.level_manager.set_character(character_name)
                        self.current_state = GameState.GAME_BOARD
                    else:
                        print("Failed to create character")

                elif result == "cancel":
                    self.character_creator = None
                    self.current_state = GameState.CHARACTER_SELECT

                elif result == "need_name":
                    # Could add a message here about needing a name
                    pass

        elif self.current_state == GameState.GAME_BOARD:
            if key == pygame.K_ESCAPE:
                self.current_state = GameState.MAIN_MENU
            elif key == pygame.K_i:
                self.current_state = GameState.INVENTORY
            elif key == pygame.K_c:
                self.current_state = GameState.CHARACTER_SHEET
            elif key == pygame.K_h:
                self.current_state = GameState.HELP
            elif key == pygame.K_l:  # Level select shortcut
                self.level_select_screen = LevelSelectScreen(self.level_manager, self.WIDTH, self.HEIGHT)
                self.current_state = GameState.LEVEL_SELECT
            elif key == pygame.K_r:  # Crafting shortcut
                self.crafting_integration.crafting_manager.crafting_active = True
                self.current_state = GameState.CRAFTING
            elif key == pygame.K_F1:  # Key to toggle instructions
                self.show_instructions = not self.show_instructions

        elif self.current_state == GameState.INVENTORY:
            if key == pygame.K_ESCAPE or key == pygame.K_i:
                self.current_state = GameState.GAME_BOARD
            elif key == pygame.K_UP:
                if hasattr(self, 'inventory_items') and self.inventory_items:
                    self.selected_inventory_item = (self.selected_inventory_item - 1) % len(self.inventory_items)
            elif key == pygame.K_DOWN:
                if hasattr(self, 'inventory_items') and self.inventory_items:
                    self.selected_inventory_item = (self.selected_inventory_item + 1) % len(self.inventory_items)
            elif key == pygame.K_e:
                # Equip selected item
                if hasattr(self, 'inventory_items') and self.inventory_items and hasattr(self,
                                                                                         'selected_inventory_item'):
                    item_name = list(self.inventory_items.keys())[
                        self.selected_inventory_item] if self.selected_inventory_item < len(
                        self.inventory_items) else None
                    if item_name:
                        from inventory_system import InventoryManager
                        inventory_manager = InventoryManager(self.character_manager)
                        if inventory_manager.is_equipment(item_name):
                            success, message = inventory_manager.equip_item(item_name)
                            print(message)
            elif key == pygame.K_u:
                # Use selected item
                if hasattr(self, 'inventory_items') and self.inventory_items and hasattr(self,
                                                                                         'selected_inventory_item'):
                    item_name = list(self.inventory_items.keys())[
                        self.selected_inventory_item] if self.selected_inventory_item < len(
                        self.inventory_items) else None
                    if item_name and ("Potion" in item_name or "Restore" in item_name):
                        success, message = self.character_manager.use_item_from_inventory(item_name)
                        print(message)

        elif self.current_state == GameState.CHARACTER_SHEET:
            if key == pygame.K_ESCAPE or key == pygame.K_c:
                self.current_state = GameState.GAME_BOARD
            elif key == pygame.K_UP:
                if hasattr(self, 'equipment_slots') and self.equipment_slots:
                    self.selected_equipment_slot = (self.selected_equipment_slot - 1) % len(self.equipment_slots)
            elif key == pygame.K_DOWN:
                if hasattr(self, 'equipment_slots') and self.equipment_slots:
                    self.selected_equipment_slot = (self.selected_equipment_slot + 1) % len(self.equipment_slots)
            elif key == pygame.K_q:
                # Unequip selected slot
                if hasattr(self, 'equipment_slots') and self.equipment_slots and hasattr(self,
                                                                                         'selected_equipment_slot'):
                    slot_name = list(self.equipment_slots.keys())[
                        self.selected_equipment_slot] if self.selected_equipment_slot < len(
                        self.equipment_slots) else None
                    if slot_name:
                        from inventory_system import InventoryManager
                        inventory_manager = InventoryManager(self.character_manager)
                        success, message = inventory_manager.unequip_item(slot_name)
                        print(message)

        elif self.current_state == GameState.CRAFTING:
            if hasattr(self, 'crafting_integration') and self.crafting_integration:
                # Handle crafting input and get result message
                key_events = [pygame.event.Event(pygame.KEYDOWN, key=key)]
                keys_pressed = pygame.key.get_pressed()
                result = self.crafting_integration.handle_crafting_input(keys_pressed, key_events)

                if result and "Closed crafting" in result:
                    self.current_state = GameState.GAME_BOARD
                elif result:
                    # Could display the result message (crafted item, etc)
                    print(result)
            else:
                # Fallback if crafting system not available
                self.current_state = GameState.GAME_BOARD

        elif self.current_state == GameState.STORE:
            if hasattr(self, 'store_integration') and self.store_integration:
                result = self.store_integration.handle_store_input(key)

                if result == "exit_store":
                    self.current_state = GameState.GAME_BOARD
                elif result in ["purchased", "insufficient_funds"]:
                    pass  # Visual feedback handled by store system

                return True
            else:
                # Fallback to main menu if store system not available
                self.current_state = GameState.MAIN_MENU

        elif self.current_state == GameState.LEVEL_SELECT:
            if self.level_select_screen:
                result = self.level_select_screen.handle_input(key)

                if result == "back":
                    self.current_state = GameState.MAIN_MENU
                elif result == "level_selected":
                    # Change to selected level and return to game
                    self.change_level(self.level_select_screen.selected_world,
                                      self.level_select_screen.selected_level)
                    self.current_state = GameState.GAME_BOARD
                elif result == "level_locked":
                    # Show message about locked level
                    pass
            else:
                self.current_state = GameState.MAIN_MENU

        elif self.current_state == GameState.SETTINGS:
            if hasattr(self, 'settings_integration') and self.settings_integration:
                result = self.settings_integration.handle_settings_input(key)

                if result == "exit_settings":
                    self.current_state = GameState.MAIN_MENU
                elif result in ["save_success", "save_failed"]:
                    # Could add visual feedback here
                    pass
                return True
            else:
                # Fallback if settings not available
                self.current_state = GameState.MAIN_MENU

        elif self.current_state == GameState.HELP:
            if key == pygame.K_ESCAPE or key == pygame.K_h:
                if hasattr(self, 'previous_state') and self.previous_state:
                    self.current_state = self.previous_state
                else:
                    self.current_state = GameState.MAIN_MENU

        elif self.current_state == GameState.FIGHT:
            if key == pygame.K_SPACE:
                self.handle_combat_action()
            elif key == pygame.K_ESCAPE:
                self.current_state = GameState.GAME_BOARD
                # Ensure world music resumes after combat
                self.start_world_music()

        return True

    def handle_combat_action(self):
        """Handle combat action (legacy method for compatibility)"""
        if not self.current_enemy or not self.character_manager.character_data:
            return

        # Player attacks
        player_damage = random.randint(15, 35)
        self.current_enemy.enemy_data["Hit_Points"] -= player_damage
        self.combat_messages.append((f"You deal {player_damage} damage!", GREEN))

        # Add damage text with world coordinates
        damage_text = DamageText(0, 0, f"-{player_damage}", DAMAGE_TEXT_COLOR)
        damage_text.world_pos = (self.current_enemy.x, self.current_enemy.y)
        self.damage_texts.append(damage_text)

        if self.current_enemy.enemy_data["Hit_Points"] <= 0:
            # Victory
            xp_gained = random.randint(25, 75)
            credits_gained = random.randint(50, 150)

            self.character_manager.character_data["Experience_Points"] += xp_gained
            self.character_manager.character_data["Credits"] += credits_gained

        if self.current_enemy.enemy_data["Hit_Points"] <= 0:
            # Victory
            xp_gained = random.randint(25, 75)
            credits_gained = random.randint(50, 150)

            self.character_manager.character_data["Experience_Points"] += xp_gained
            self.character_manager.character_data["Credits"] += credits_gained

            self.combat_messages.append((f"Victory! Gained {xp_gained} XP and {credits_gained} credits!", GOLD))

            # Check for level up
            self.character_manager.level_up_check()

            # Save character
            self.character_manager.save_character()

            # Return to game board after short delay
            pygame.time.wait(1000)
            self.current_state = GameState.GAME_BOARD
            self.current_enemy = None

        # Enemy attacks back
        enemy_damage = random.randint(10, 25)
        self.character_manager.character_data["Hit_Points"] -= enemy_damage
        self.combat_messages.append((f"Enemy deals {enemy_damage} damage!", RED))

        # Add player damage text with world coordinates
        damage_text = DamageText(0, 0, f"-{enemy_damage}", RED)
        damage_text.world_pos = (self.animated_player.x, self.animated_player.y)
        self.damage_texts.append(damage_text)

        if self.character_manager.character_data["Hit_Points"] <= 0:
            # Player death
            self.combat_messages.append(("You have been defeated!", RED))
            self.character_manager.character_data["Hit_Points"] = 50  # Respawn with half health

            # Save character
            self.character_manager.save_character()

            pygame.time.wait(1000)
            self.current_state = GameState.GAME_BOARD
            self.current_enemy = None

    def update(self):
        """Update game logic"""
        self.animation_timer += 1
        self.particles.update()

        # Update rest manager
        self.rest_manager.update()

        # Update rest areas
        for rest_area in self.rests:
            rest_area.update()

        # Update level select screen if active
        if self.current_state == GameState.LEVEL_SELECT and self.level_select_screen:
            self.level_select_screen.update()

        # Update character creator if active
        if self.current_state == GameState.CREATE_CHARACTER and self.character_creator:
            self.character_creator.update()

        # Update floating damage texts
        for damage_text in self.damage_texts[:]:
            if not damage_text.update():
                self.damage_texts.remove(damage_text)

        # Update store integration
        if hasattr(self, 'store_integration') and self.store_integration:
            self.store_integration.update()

        # Update crafting nodes
        for crafting_node in self.crafting_nodes:
            crafting_node.update()

        if self.current_state == GameState.GAME_BOARD:
            # Store previous player position for collision rollback
            prev_x = self.animated_player.x
            prev_y = self.animated_player.y

            # Update animated player position
            world_width, world_height = self.tile_map.get_world_pixel_size()
            moved = self.animated_player.update_position(world_width, world_height)

            # Check for tree collisions and prevent movement if blocked
            if moved:
                player_rect = pygame.Rect(self.animated_player.x, self.animated_player.y,
                                          self.animated_player.display_width, self.animated_player.display_height)

                # Check if player is colliding with trees
                tree_collision = self.check_tree_collision(player_rect)
                if tree_collision:
                    # Rollback movement - player can't walk through trees
                    self.animated_player.x = prev_x
                    self.animated_player.y = prev_y
                    moved = False  # Don't update camera if movement was blocked

            # Update camera if player moved
            if moved:
                self.camera.update(self.animated_player.x + self.animated_player.display_width // 2,
                                   self.animated_player.y + self.animated_player.display_height // 2)

            # Check for level completion
            self.check_level_completion()

            # Check for collisions (now enhanced with combat integration and rest areas)
            collision_type, collision_obj = self.check_collisions()

            if collision_type == "tree":
                # Trees block movement, but this is handled in the movement check above
                pass

            elif collision_type == "rest":
                # Handle rest area interaction
                result = collision_obj.attempt_interaction()

                if result["success"]:
                    # Add visual feedback for successful rest
                    if hasattr(self, 'combat_integration') and self.combat_integration:
                        self.combat_integration.play_world_sound("heal", 0.8)

                    # Add floating text for HP/MP restoration
                    if "hp_gained" in result and result["hp_gained"] > 0:
                        damage_text = DamageText(0, 0, f"+{result['hp_gained']} HP", HEAL_TEXT_COLOR)
                        damage_text.world_pos = (self.animated_player.x, self.animated_player.y - 20)
                        self.damage_texts.append(damage_text)

                    if "mp_gained" in result and result["mp_gained"] > 0:
                        damage_text = DamageText(0, 0, f"+{result['mp_gained']} MP", (100, 150, 255))
                        damage_text.world_pos = (self.animated_player.x, self.animated_player.y - 40)
                        self.damage_texts.append(damage_text)
                else:
                    # Add visual feedback for failed rest attempt
                    if hasattr(self, 'combat_integration') and self.combat_integration:
                        self.combat_integration.play_world_sound("menu_select", 0.5)

                    # Show cooldown message
                    damage_text = DamageText(0, 0, "On Cooldown!", RED)
                    damage_text.world_pos = (self.animated_player.x, self.animated_player.y - 20)
                    self.damage_texts.append(damage_text)

            elif collision_type == "enemy":
                collision_obj.active = False
                self.current_enemy = collision_obj
                self.current_state = GameState.FIGHT
                self.combat_messages = []

            elif collision_type == "treasure":
                collision_obj.active = False

                if self.character_manager.character_data:
                    # 25% chance to get crafting material instead of credits
                    from crafting_system import get_random_crafting_material

                    if random.randint(1, 100) <= 25:
                        # Give crafting material
                        crafting_material = get_random_crafting_material(from_treasure=True)
                        if crafting_material:
                            from inventory_system import InventoryManager
                            inventory_manager = InventoryManager(self.character_manager)
                            inventory_manager.add_item(crafting_material, 1)

                            # Add visual feedback
                            damage_text = DamageText(0, 0, f"Found {crafting_material}!", (255, 215, 0))
                            damage_text.world_pos = (self.animated_player.x, self.animated_player.y)
                            self.damage_texts.append(damage_text)

                            # Play crafting material sound
                            if hasattr(self, 'combat_integration') and self.combat_integration:
                                self.combat_integration.play_world_sound("item_pickup")
                    else:
                        # Give credits as normal
                        credits_gained = collision_obj.value
                        current_credits = self.character_manager.character_data.get("Credits", 0)
                        self.character_manager.character_data["Credits"] = current_credits + credits_gained

                        # Add visual feedback at player world position
                        damage_text = DamageText(0, 0, f"+{credits_gained} Credits!", GOLD)
                        damage_text.world_pos = (self.animated_player.x, self.animated_player.y)
                        self.damage_texts.append(damage_text)

                        # Play coin pickup sound
                        if hasattr(self, 'combat_integration') and self.combat_integration:
                            self.combat_integration.play_world_sound("coin_pickup")

                    # Save character
                    self.character_manager.save_character()

            elif collision_type == "crafting_node":
                # Harvest crafting material
                material = collision_obj.harvest()
                if material and self.character_manager.character_data:
                    # Use the new inventory system
                    from inventory_system import InventoryManager
                    inventory_manager = InventoryManager(self.character_manager)
                    inventory_manager.add_item(material, 1)

                    # Add visual feedback
                    damage_text = DamageText(0, 0, f"Harvested {material}!", (255, 215, 0))
                    damage_text.world_pos = (self.animated_player.x, self.animated_player.y - 20)
                    self.damage_texts.append(damage_text)

                    # Play harvest sound
                    if hasattr(self, 'combat_integration') and self.combat_integration:
                        self.combat_integration.play_world_sound("item_pickup")

                    # Save character
                    self.character_manager.save_character()

            elif collision_type == "shop":
                self.current_state = GameState.STORE

    def draw_opening_screen(self):
        """Draw the opening screen"""
        self.screen.fill(MENU_BG)

        # Add animated particles
        if self.animation_timer % 10 == 0:
            self.particles.add_particle(random.randint(0, self.WIDTH),
                                        random.randint(0, self.HEIGHT),
                                        LIGHT_BLUE)

        self.particles.draw(self.screen)

        # Title with glow effect
        title_surface = self.ui_renderer.title_font.render("MAGITECH RPG - MULTI-LEVEL EDITION", True, MENU_SELECTED)
        title_rect = title_surface.get_rect(center=(self.WIDTH // 2, 150))
        self.screen.blit(title_surface, title_rect)

        # Subtitle
        subtitle = self.ui_renderer.font.render("With Enhanced Combat, Sound & 20 Levels", True, MENU_TEXT)
        subtitle_rect = subtitle.get_rect(center=(self.WIDTH // 2, 200))
        self.screen.blit(subtitle, subtitle_rect)

        # Animated prompt
        alpha = int(128 + 127 * math.sin(self.animation_timer * 0.1))
        prompt_surface = self.ui_renderer.font.render("Press any key to begin your adventure...", True, MENU_SELECTED)
        prompt_surface.set_alpha(alpha)
        prompt_rect = prompt_surface.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 150))
        self.screen.blit(prompt_surface, prompt_rect)

    def draw_character_select_screen(self):
        """Draw the character selection screen"""
        menu_options = []
        for char in self.available_characters:
            if char == "New Character":
                menu_options.append("Create New Character")
            else:
                # Format character filename nicely
                char_name = char.replace(".json", "").replace("_", " ").title()
                menu_options.append(f"Load {char_name}")

        self.ui_renderer.draw_enhanced_menu(self.screen, "SELECT CHARACTER", menu_options,
                                            self.selected_character, "Choose your hero!",
                                            self.animation_timer)

        # Instructions
        instructions = [
            "UP/DOWN: Navigate characters",
            "ENTER: Select character",
            "ESC: Back to main menu"
        ]
        self.ui_renderer.draw_instructions_panel(self.screen, instructions)

    def draw_create_character_screen(self):
        """Draw the create character screen"""
        if self.character_creator:
            self.character_creator.draw(self.screen)
        else:
            # Fallback if character creator isn't initialized
            self.screen.fill(MENU_BG)
            error_text = self.ui_renderer.font.render("Character creator not initialized!", True, RED)
            error_rect = error_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(error_text, error_rect)

    def draw_game_board(self):
        """Draw the main game board"""
        # Get level background color
        bg_color = (50, 100, 50)  # Default green
        current_level = self.level_manager.get_current_level()
        if current_level:
            bg_color = self.world_generator._get_background_color(current_level)

        # Draw tile map background or colored background
        if self.map_tiles:
            self.tile_map.draw(self.map_tiles, self.screen, -self.camera.x, -self.camera.y)
        else:
            self.screen.fill(bg_color)

        # Draw trees first (behind other objects)
        for tree in self.trees:
            tree.draw(self.screen, self.camera, self.animation_timer)

        # Draw world objects with debug info
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera, self.animation_timer)

        for treasure in self.treasures:
            treasure.draw(self.screen, self.camera, self.animation_timer)

        # Debug: Always try to draw shops and rests
        for i, shop in enumerate(self.shops):
            shop.draw(self.screen, self.camera, self.animation_timer)

        for i, rest_area in enumerate(self.rests):
            rest_area.draw(self.screen, self.camera.x, self.camera.y)

        # Draw crafting nodes
        for crafting_node in self.crafting_nodes:
            crafting_node.draw(self.screen, self.camera, self.animation_timer)

        # Draw animated player at correct screen position
        screen_x, screen_y = self.camera.world_to_screen(self.animated_player.x, self.animated_player.y)
        self.animated_player.draw_at_screen_position(self.screen, screen_x, screen_y)

        # Draw enhanced status overlay with level info
        self.draw_enhanced_status_overlay()

        # Draw rest status HUD
        self.rest_manager.draw_rest_hud(self.screen, self.WIDTH, self.HEIGHT)

        # Draw instructions only if enabled
        if self.show_instructions:
            instructions = [
                "Arrow Keys: Move character",
                "Walk into objects to interact",
                "Rest areas: Restore HP/MP (3min cooldown)",
                "Trees block your path - walk around them",
                "I: Inventory  C: Character  H: Help  L: Level Select  R: Crafting",
                "F1: Toggle this panel  ESC: Main Menu"
            ]
            self.ui_renderer.draw_instructions_panel(self.screen, instructions)
        else:
            # Draw a small toggle hint in the corner
            hint_text = self.ui_renderer.small_font.render("F1: Show Help", True, WHITE)
            hint_bg = pygame.Rect(10, self.HEIGHT - 25, hint_text.get_width() + 10, 20)
            pygame.draw.rect(self.screen, (0, 0, 0, 128), hint_bg)
            self.screen.blit(hint_text, (15, self.HEIGHT - 22))

        # Draw floating damage texts with proper world-to-screen conversion
        for damage_text in self.damage_texts:
            if hasattr(damage_text, 'world_pos') and damage_text.world_pos:
                damage_text.draw_at_world_pos(self.screen, self.camera)
            else:
                damage_text.draw(self.screen)

        # Draw particles
        self.particles.draw(self.screen)

    def draw_enhanced_status_overlay(self):
        """Draw enhanced status overlay with level information"""
        # Draw standard status overlay
        self.ui_renderer.draw_status_overlay(self.screen, self.character_manager)

        # Add level information
        current_level = self.level_manager.get_current_level()
        if current_level:
            # Level info overlay
            level_overlay = pygame.Surface((300, 40), pygame.SRCALPHA)
            level_overlay.fill((0, 0, 0, 128))

            level_text = f"Level: {current_level.get_display_name()}"
            difficulty_text = f"Difficulty: {current_level.get_difficulty_description()}"

            level_surface = self.ui_renderer.small_font.render(level_text, True, WHITE)
            difficulty_surface = self.ui_renderer.small_font.render(difficulty_text, True, MENU_SELECTED)

            level_overlay.blit(level_surface, (10, 5))
            level_overlay.blit(difficulty_surface, (10, 20))

            # Blit level overlay below main status overlay
            self.screen.blit(level_overlay, (10, 140))

    def draw_fight_screen(self):
        """Draw the fight screen - now enhanced with advanced combat"""
        # Check if we have the combat integration active
        if hasattr(self, 'combat_integration') and self.combat_integration.in_combat:
            # Use the advanced combat system
            self.combat_integration.draw_combat(self.screen)
        else:
            # Fallback to simple combat display
            self.screen.fill((50, 0, 0))  # Dark red background

            # Title
            title = self.ui_renderer.large_font.render("BATTLE!", True, WHITE)
            title_rect = title.get_rect(center=(self.WIDTH // 2, 100))
            self.screen.blit(title, title_rect)

            if self.character_manager.character_data and self.current_enemy:
                player_name = self.character_manager.character_data.get("Name", "Player")
                enemy_name = self.current_enemy.enemy_data.get("Name", "Enemy")
                player_hp = self.character_manager.character_data.get("Hit_Points", 100)
                enemy_hp = self.current_enemy.enemy_data.get("Hit_Points", 75)

                # Player info
                player_text = self.ui_renderer.font.render(f"{player_name}: {player_hp} HP", True, GREEN)
                self.screen.blit(player_text, (100, 200))

                # Enemy info
                enemy_text = self.ui_renderer.font.render(f"{enemy_name}: {enemy_hp} HP", True, RED)
                self.screen.blit(enemy_text, (100, 250))

                # Combat messages
                y_pos = 300
                for message, color in self.combat_messages[-5:]:
                    text = self.ui_renderer.small_font.render(message[:60], True, color)
                    self.screen.blit(text, (50, y_pos))
                    y_pos += 25

                # Instructions
                instruction = self.ui_renderer.font.render("SPACE: Attack  ESC: Flee", True, WHITE)
                instruction_rect = instruction.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 100))
                self.screen.blit(instruction, instruction_rect)

    def draw_inventory_screen(self):
        """Draw the enhanced inventory screen with equipment options"""
        self.screen.fill(MENU_BG)

        title = self.ui_renderer.large_font.render("INVENTORY", True, WHITE)
        title_rect = title.get_rect(center=(self.WIDTH // 2, 50))
        self.screen.blit(title, title_rect)

        if not self.character_manager.character_data:
            no_char_text = self.ui_renderer.font.render("No character loaded!", True, WHITE)
            no_char_rect = no_char_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(no_char_text, no_char_rect)
            return

        from inventory_system import InventoryManager
        inventory_manager = InventoryManager(self.character_manager)
        inventory = inventory_manager.get_inventory()

        # Update inventory items for navigation
        self.inventory_items = inventory
        if not hasattr(self, 'selected_inventory_item'):
            self.selected_inventory_item = 0
        if not hasattr(self, 'inventory_scroll_offset'):
            self.inventory_scroll_offset = 0
        # Keep selection within bounds
        if self.inventory_items and self.selected_inventory_item >= len(self.inventory_items):
            self.selected_inventory_item = len(self.inventory_items) - 1

        # Update scroll offset based on selection
        max_visible_items = 12  # Number of items visible on screen at once
        if self.selected_inventory_item < self.inventory_scroll_offset:
            self.inventory_scroll_offset = self.selected_inventory_item
        elif self.selected_inventory_item >= self.inventory_scroll_offset + max_visible_items:
            self.inventory_scroll_offset = self.selected_inventory_item - max_visible_items + 1

        if not inventory:
            empty_text = self.ui_renderer.font.render("Your inventory is empty!", True, WHITE)
            empty_rect = empty_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(empty_text, empty_rect)
        else:
            # Column headers
            item_header = self.ui_renderer.font.render("ITEM", True, MENU_SELECTED)
            quantity_header = self.ui_renderer.font.render("QTY", True, MENU_SELECTED)
            stats_header = self.ui_renderer.font.render("STATS", True, MENU_SELECTED)
            action_header = self.ui_renderer.font.render("ACTION", True, MENU_SELECTED)

            self.screen.blit(item_header, (50, 90))
            self.screen.blit(quantity_header, (200, 90))
            self.screen.blit(stats_header, (250, 90))
            self.screen.blit(action_header, (500, 90))

            # Draw separator line
            pygame.draw.line(self.screen, MENU_ACCENT, (50, 110), (650, 110), 2)

            y_pos = 120
            max_visible_items = 12
            scroll_offset = getattr(self, 'inventory_scroll_offset', 0)

            # Convert inventory to list for slicing
            inventory_list = list(inventory.items())
            visible_items = inventory_list[scroll_offset:scroll_offset + max_visible_items]

            for display_index, (item_name, quantity) in enumerate(visible_items):
                actual_index = scroll_offset + display_index
                item_info = inventory_manager.get_item_info(item_name)

                # Highlight selected item
                if hasattr(self, 'selected_inventory_item') and actual_index == self.selected_inventory_item:
                    highlight_rect = pygame.Rect(45, y_pos - 3, 600, 30)
                    pygame.draw.rect(self.screen, MENU_HIGHLIGHT, highlight_rect)

                # Item name
                item_color = MENU_SELECTED if (hasattr(self,
                                                       'selected_inventory_item') and actual_index == self.selected_inventory_item) else WHITE
                item_text = self.ui_renderer.font.render(f"{item_name}", True, item_color)
                self.screen.blit(item_text, (50, y_pos))

                # Quantity
                qty_text = self.ui_renderer.font.render(f"x{quantity}", True, WHITE)
                self.screen.blit(qty_text, (200, y_pos))

                # Stats (for equipment)
                if inventory_manager.is_equipment(item_name):
                    stats_text = self.ui_renderer.small_font.render(item_info["stats"], True, LIGHT_BLUE)
                    self.screen.blit(stats_text, (250, y_pos))

                    # Action button for equipment
                    action_text = self.ui_renderer.small_font.render("[E] Equip", True, GREEN)
                    self.screen.blit(action_text, (500, y_pos))
                else:
                    # For consumables, show "[U] Use" option
                    if "Potion" in item_name or "Restore" in item_name:
                        action_text = self.ui_renderer.small_font.render("[U] Use", True, YELLOW)
                        self.screen.blit(action_text, (500, y_pos))

                y_pos += 35

            # Show scroll indicators
            if scroll_offset > 0:
                up_arrow = self.ui_renderer.small_font.render("▲ More items above", True, LIGHT_BLUE)
                self.screen.blit(up_arrow, (450, 90))

            if scroll_offset + max_visible_items < len(inventory_list):
                down_arrow = self.ui_renderer.small_font.render("▼ More items below", True, LIGHT_BLUE)
                self.screen.blit(down_arrow, (450, y_pos + 10))

        # Instructions
        instructions = [
            "ESC/I: Return to game",
            "↑↓: Navigate items",
            "E: Equip selected item (equipment only)",
            "U: Use selected item (consumables only)"
        ]

        instruction_y = self.HEIGHT - 80
        for instruction in instructions:
            instruction_surface = self.ui_renderer.small_font.render(instruction, True, MENU_TEXT)
            instruction_rect = instruction_surface.get_rect(center=(self.WIDTH // 2, instruction_y))
            self.screen.blit(instruction_surface, instruction_rect)
            instruction_y += 20

    def draw_character_sheet(self):
        """Draw the enhanced character sheet with equipment details"""
        self.screen.fill(MENU_BG)

        title = self.ui_renderer.large_font.render("CHARACTER SHEET", True, WHITE)
        title_rect = title.get_rect(center=(self.WIDTH // 2, 50))
        self.screen.blit(title, title_rect)

        if not self.character_manager.character_data:
            no_char_text = self.ui_renderer.font.render("No character loaded!", True, WHITE)
            no_char_rect = no_char_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(no_char_text, no_char_rect)
            return

        from inventory_system import InventoryManager
        inventory_manager = InventoryManager(self.character_manager)
        equipped_items = inventory_manager.get_equipped_items()

        # Update equipment slots for navigation
        self.equipment_slots = equipped_items
        if not hasattr(self, 'selected_equipment_slot'):
            self.selected_equipment_slot = 0
        # Keep selection within bounds
        if self.equipment_slots and self.selected_equipment_slot >= len(self.equipment_slots):
            self.selected_equipment_slot = len(self.equipment_slots) - 1

        # Left column - Character info and stats
        char_info = [
            f"Name: {self.character_manager.character_data.get('Name', 'Unknown')}",
            f"Race: {self.character_manager.character_data.get('Race', 'Human')}",
            f"Type: {self.character_manager.character_data.get('Type', 'Unknown')}",
            f"Level: {self.character_manager.character_data.get('Level', 1)}",
            f"HP: {self.character_manager.character_data.get('Hit_Points', 100)}",
            f"XP: {self.character_manager.character_data.get('Experience_Points', 0)}",
            f"Credits: {self.character_manager.character_data.get('Credits', 0)}",
            "",
            "CORE STATS:"
        ]

        # Add stats with base/bonus breakdown
        stats = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        for stat in stats:
            base_stat = self.character_manager.get_base_stat(stat)
            equipment_bonus = inventory_manager.get_equipment_stat_bonus(stat)
            total_stat = base_stat + equipment_bonus

            if equipment_bonus > 0:
                stat_line = f"{stat.capitalize()}: {total_stat} ({base_stat}+{equipment_bonus})"
                char_info.append(stat_line)
            else:
                char_info.append(f"{stat.capitalize()}: {total_stat}")

        char_info.append(f"Armor Class: {self.character_manager.get_armor_class()}")

        y_pos = 100
        for info in char_info:
            if info == "":
                y_pos += 15
                continue

            if info == "CORE STATS:":
                color = MENU_SELECTED
                font_to_use = self.ui_renderer.font
            else:
                color = WHITE
                font_to_use = self.ui_renderer.small_font

            text = font_to_use.render(info, True, color)
            self.screen.blit(text, (50, y_pos))
            y_pos += 22

        # Right column - Equipment
        equipment_title = self.ui_renderer.font.render("EQUIPPED ITEMS:", True, MENU_SELECTED)
        self.screen.blit(equipment_title, (400, 100))

        equip_y = 130
        slot_names = {
            "Weapon1": "Main Hand",
            "Weapon2": "Off Hand",
            "Weapon3": "Extra Weapon",
            "Armor_Slot_1": "Armor",
            "Armor_Slot_2": "Extra Armor"
        }

        for slot_index, (slot, item_name) in enumerate(equipped_items.items()):
            slot_display = slot_names.get(slot, slot)

            # Highlight selected equipment slot
            if hasattr(self, 'selected_equipment_slot') and slot_index == self.selected_equipment_slot:
                highlight_rect = pygame.Rect(395, equip_y - 3, 300, 30)
                pygame.draw.rect(self.screen, MENU_HIGHLIGHT, highlight_rect)

            slot_color = MENU_SELECTED if (hasattr(self,
                                                   'selected_equipment_slot') and slot_index == self.selected_equipment_slot) else LIGHT_BLUE
            item_color = MENU_SELECTED if (hasattr(self,
                                                   'selected_equipment_slot') and slot_index == self.selected_equipment_slot) else WHITE

            slot_text = self.ui_renderer.small_font.render(f"{slot_display}:", True, slot_color)
            self.screen.blit(slot_text, (400, equip_y))

            item_text = self.ui_renderer.small_font.render(item_name, True, item_color)
            self.screen.blit(item_text, (520, equip_y))

            # Show item stats
            item_info = inventory_manager.get_item_info(item_name)
            if item_info.get("stats"):
                stats_text = self.ui_renderer.small_font.render(f"({item_info['stats']})", True, GREEN)
                self.screen.blit(stats_text, (400, equip_y + 15))
                equip_y += 40
            else:
                equip_y += 25

        # Show unequip instructions
        if equipped_items:
            unequip_text = self.ui_renderer.small_font.render("[Q] Unequip selected slot", True, YELLOW)
            self.screen.blit(unequip_text, (400, equip_y + 20))

        # Instructions
        instructions = [
            "ESC/C: Return to game",
            "Q: Unequip item from slot"
        ]

        instruction_y = self.HEIGHT - 60
        for instruction in instructions:
            instruction_surface = self.ui_renderer.small_font.render(instruction, True, MENU_TEXT)
            instruction_rect = instruction_surface.get_rect(center=(self.WIDTH // 2, instruction_y))
            self.screen.blit(instruction_surface, instruction_rect)
            instruction_y += 20

    def draw_help_screen(self):
        """Draw help screen"""
        self.screen.fill(MENU_BG)

        title = self.ui_renderer.large_font.render("HELP", True, WHITE)
        title_rect = title.get_rect(center=(self.WIDTH // 2, 50))
        self.screen.blit(title, title_rect)

        help_text = load_help_text()

        y_pos = 100
        line_count = 0
        max_lines = 20  # Limit lines to fit on screen

        for line in help_text:
            if line_count >= max_lines:
                break

            if line == "":
                y_pos += 15
                continue

            if line.startswith("##") or line.isupper() and ":" not in line:
                color = MENU_SELECTED
                font_to_use = self.ui_renderer.font
            else:
                color = MENU_TEXT
                font_to_use = self.ui_renderer.small_font

            # Remove markdown formatting
            display_line = line.replace("##", "").replace("**", "").replace("- ", "").strip()
            if len(display_line) > 70:
                display_line = display_line[:67] + "..."

            text = font_to_use.render(display_line, True, color)
            screen_center = self.WIDTH // 2
            text_rect = text.get_rect(center=(screen_center, y_pos))
            self.screen.blit(text, text_rect)
            y_pos += 18
            line_count += 1

        # Instructions
        instruction = self.ui_renderer.small_font.render("Press ESC or H to return", True, MENU_TEXT)
        instruction_rect = instruction.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 30))
        self.screen.blit(instruction, instruction_rect)

    def load_settings(self):
        """Load settings - placeholder for compatibility"""
        pass

    def draw(self):
        """Draw current state"""
        if self.current_state == GameState.OPENING:
            self.draw_opening_screen()

        elif self.current_state == GameState.MAIN_MENU:
            menu_options = ["Start Game", "Level Select", "Settings", "Help", "Quit"]
            self.ui_renderer.draw_enhanced_menu(self.screen, "MAGITECH RPG", menu_options,
                                                self.selected_option, "Choose your destiny!",
                                                self.animation_timer)

        elif self.current_state == GameState.CRAFTING:
            # Draw game board as background
            self.draw_game_board()
            # Draw crafting interface overlay
            if hasattr(self, 'crafting_integration') and self.crafting_integration:
                self.crafting_integration.draw_crafting_interface(self.screen)

        elif self.current_state == GameState.CHARACTER_SELECT:
            self.draw_character_select_screen()

        elif self.current_state == GameState.CREATE_CHARACTER:
            self.draw_create_character_screen()

        elif self.current_state == GameState.GAME_BOARD:
            self.draw_game_board()

        elif self.current_state == GameState.FIGHT:
            self.draw_fight_screen()

        elif self.current_state == GameState.LEVEL_SELECT:
            if self.level_select_screen:
                self.level_select_screen.draw(self.screen)
            else:
                # Fallback
                self.screen.fill(MENU_BG)
                error_text = self.ui_renderer.font.render("Level select not available!", True, RED)
                error_rect = error_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
                self.screen.blit(error_text, error_rect)

        elif self.current_state == GameState.SETTINGS:
            if hasattr(self, 'settings_integration') and self.settings_integration:
                self.settings_integration.draw_settings(self.screen)
            else:
                # Fallback if settings system not available
                self.screen.fill(MENU_BG)
                error_text = self.ui_renderer.font.render("Settings system not available!", True, RED)
                error_rect = error_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
                self.screen.blit(error_text, error_rect)

        elif self.current_state == GameState.STORE:
            if hasattr(self, 'store_integration') and self.store_integration:
                self.store_integration.draw_store(self.screen)
            else:
                # Fallback if store system not available
                self.screen.fill(MENU_BG)
                error_text = self.ui_renderer.font.render("Store system not available!", True, RED)
                error_rect = error_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
                self.screen.blit(error_text, error_rect)

        elif self.current_state == GameState.INVENTORY:
            self.draw_inventory_screen()

        elif self.current_state == GameState.CHARACTER_SHEET:
            self.draw_character_sheet()

        elif self.current_state == GameState.HELP:
            self.draw_help_screen()

    def run(self):
        """Main game loop"""
        clock = pygame.time.Clock()
        running = True

        changelog = load_changelog_text()
        print("=== MAGITECH RPG - MULTI-LEVEL EDITION ===")
        print("Now featuring 20 levels across 5 unique worlds!")
        print("Press L during gameplay for level select")
        print("Trees now populate the world - walk around them!")
        print("Settings menu available from main menu!")
        print("==========================================")

        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    # Use new event handler
                    result = self.handle_event(event)
                    if result is False:
                        running = False

            # Update game logic
            self.update()

            # Draw everything
            self.draw()

            # Update display
            pygame.display.flip()
            clock.tick(15)

        # Save progression before quitting
        if hasattr(self, 'level_manager'):
            self.level_manager.save_progression()

        pygame.quit()
        sys.exit()


# Main execution
if __name__ == "__main__":
    # Create necessary files and directories
    create_sample_files()

    try:
        # Start the enhanced game
        game = EnhancedGameManager()
        game.run()
    except Exception as e:
        print(f"Game error: {e}")
        pygame.quit()
        sys.exit()