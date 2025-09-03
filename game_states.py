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
from store_system import StoreIntegration
from enhanced_combat_integration import integrate_enhanced_combat_with_game_states, setup_enhanced_audio_system


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
        pygame.display.set_caption("Magitech RPG - Combat Edition with Sound & Animation")

        # Game state
        self.current_state = GameState.OPENING
        self.selected_option = 0
        self.animation_timer = 0

        # UI settings
        self.show_instructions = False  # Setting to toggle instructions

        # Initialize subsystems
        self.character_manager = CharacterManager()
        self.enemy_manager = EnemyManager()

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

        # Combat system variables (for legacy compatibility)
        self.current_enemy = None
        self.combat_messages = []

        # Setup initial world
        self.setup_world_objects()

        # Add static shop in top-right corner
        static_shop = Shop(world_width - 80, 20)  # Top-right corner
        self.shops.append(static_shop)

        # Add static rest area in bottom-right corner
        static_rest = RestArea(world_width - 80, 750)  # Bottom-right corner
        self.rests.append(static_rest)

        # Initialize enhanced combat integration system
        integrate_enhanced_combat_with_game_states(self)
        setup_enhanced_audio_system(self)

        # Initialize store integration
        self.store_integration = StoreIntegration(self)

    def load_character_list(self):
        """Load list of available characters"""
        self.available_characters = self.character_manager.get_character_list()
        self.selected_character = 0

    def load_map_data(self):
        """Load map data and create tiles"""
        self.map_tiles = self.tile_map.load_map_from_file("map.txt")

    def setup_world_objects(self):
        """Setup game world objects based on map"""
        # Clear existing objects
        self.enemies.clear()
        self.treasures.clear()
        self.shops.clear()
        self.rests.clear()

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

    def check_collisions(self):
        """Check for collisions between player and world objects"""
        # Skip collision checks during store exit cooldown
        if (hasattr(self, 'store_integration') and self.store_integration and
                self.store_integration.exit_cooldown > 0):
            return None, None

        player_rect = pygame.Rect(self.animated_player.x, self.animated_player.y,
                                  self.animated_player.display_width, self.animated_player.display_height)

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
                self.selected_option = (self.selected_option - 1) % 3
            elif key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % 3
            elif key == pygame.K_RETURN:
                if self.selected_option == 0:  # Start Game
                    self.load_character_list()
                    self.current_state = GameState.CHARACTER_SELECT

                elif self.selected_option == 1:  # Help
                    self.current_state = GameState.HELP

                elif self.selected_option == 2:  # Quit
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
            elif key == pygame.K_F1:  # Key to toggle instructions
                self.show_instructions = not self.show_instructions

        elif self.current_state == GameState.INVENTORY:
            if key == pygame.K_ESCAPE or key == pygame.K_i:
                self.current_state = GameState.GAME_BOARD

        elif self.current_state == GameState.CHARACTER_SHEET:
            if key == pygame.K_ESCAPE or key == pygame.K_c:
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

        if self.current_state == GameState.GAME_BOARD:
            # Update animated player position
            world_width, world_height = self.tile_map.get_world_pixel_size()
            moved = self.animated_player.update_position(world_width, world_height)

            # Update camera if player moved
            if moved:
                self.camera.update(self.animated_player.x + self.animated_player.display_width // 2,
                                   self.animated_player.y + self.animated_player.display_height // 2)

            # Check for collisions (now enhanced with combat integration)
            collision_type, collision_obj = self.check_collisions()

            if collision_type == "enemy":
                collision_obj.active = False
                self.current_enemy = collision_obj
                self.current_state = GameState.FIGHT
                self.combat_messages = []

            elif collision_type == "treasure":
                collision_obj.active = False
                # Add credits to player
                credits_gained = collision_obj.value
                if self.character_manager.character_data:
                    current_credits = self.character_manager.character_data.get("Credits", 0)
                    self.character_manager.character_data["Credits"] = current_credits + credits_gained

                    # Add visual feedback at player world position
                    damage_text = DamageText(0, 0, f"+{credits_gained} Credits!", GOLD)
                    damage_text.world_pos = (self.animated_player.x, self.animated_player.y)
                    self.damage_texts.append(damage_text)

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
        title_surface = self.ui_renderer.title_font.render("MAGITECH RPG - COMBAT EDITION", True, MENU_SELECTED)
        title_rect = title_surface.get_rect(center=(self.WIDTH // 2, 150))
        self.screen.blit(title_surface, title_rect)

        # Subtitle
        subtitle = self.ui_renderer.font.render("With Enhanced Combat, Sound & Animation", True, MENU_TEXT)
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
                menu_options.append("🆕 Create New Character")
            else:
                # Format character filename nicely
                char_name = char.replace(".json", "").replace("_", " ").title()
                menu_options.append(f"👤 {char_name}")

        self.ui_renderer.draw_enhanced_menu(self.screen, "SELECT CHARACTER", menu_options,
                                            self.selected_character, "Choose your hero!",
                                            self.animation_timer)

        # Instructions
        instructions = [
            "↑↓ Navigate characters",
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
        # Draw tile map background
        if self.map_tiles:
            self.tile_map.draw(self.map_tiles, self.screen, -self.camera.x, -self.camera.y)
        else:
            self.screen.fill((50, 100, 50))  # Fallback green background

        # Draw world objects
        for enemy in self.enemies:
            enemy.draw(self.screen, self.camera, self.animation_timer)

        for treasure in self.treasures:
            treasure.draw(self.screen, self.camera, self.animation_timer)

        for shop in self.shops:
            shop.draw(self.screen, self.camera, self.animation_timer)

        # Draw animated player at correct screen position
        screen_x, screen_y = self.camera.world_to_screen(self.animated_player.x, self.animated_player.y)
        self.animated_player.draw_at_screen_position(self.screen, screen_x, screen_y)

        # Draw new semi-transparent status overlay
        self.ui_renderer.draw_status_overlay(self.screen, self.character_manager)

        # Draw instructions only if enabled
        if self.show_instructions:
            instructions = [
                "Arrow Keys: Move character",
                "Walk into objects to interact",
                "I: Inventory  C: Character Sheet  H: Help",
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
        """Draw the inventory screen"""
        self.screen.fill(MENU_BG)

        title = self.ui_renderer.large_font.render("🎒 INVENTORY", True, WHITE)
        title_rect = title.get_rect(center=(self.WIDTH // 2, 50))
        self.screen.blit(title, title_rect)

        if not self.character_manager.character_data:
            no_char_text = self.ui_renderer.font.render("No character loaded!", True, WHITE)
            no_char_rect = no_char_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(no_char_text, no_char_rect)
            return

        inventory = self.character_manager.character_data.get("Inventory", {})

        if not inventory:
            empty_text = self.ui_renderer.font.render("Your inventory is empty!", True, WHITE)
            empty_rect = empty_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(empty_text, empty_rect)
        else:
            y_pos = 120
            for item_name, quantity in inventory.items():
                item_text = self.ui_renderer.font.render(f"{item_name} x{quantity}", True, WHITE)
                self.screen.blit(item_text, (100, y_pos))
                y_pos += 30

        # Instructions
        instruction = self.ui_renderer.small_font.render("Press ESC or I to return", True, MENU_TEXT)
        instruction_rect = instruction.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 50))
        self.screen.blit(instruction, instruction_rect)

    def draw_character_sheet(self):
        """Draw the character sheet screen"""
        self.screen.fill(MENU_BG)

        title = self.ui_renderer.large_font.render("📋 CHARACTER SHEET", True, WHITE)
        title_rect = title.get_rect(center=(self.WIDTH // 2, 50))
        self.screen.blit(title, title_rect)

        if not self.character_manager.character_data:
            no_char_text = self.ui_renderer.font.render("No character loaded!", True, WHITE)
            no_char_rect = no_char_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(no_char_text, no_char_rect)
            return

        # Character info
        char_info = [
            f"Name: {self.character_manager.character_data.get('Name', 'Unknown')}",
            f"Race: {self.character_manager.character_data.get('Race', 'Human')}",
            f"Type: {self.character_manager.character_data.get('Type', 'Unknown')}",
            f"Level: {self.character_manager.character_data.get('Level', 1)}",
            f"HP: {self.character_manager.character_data.get('Hit_Points', 100)}",
            f"XP: {self.character_manager.character_data.get('Experience_Points', 0)}",
            f"Credits: {self.character_manager.character_data.get('Credits', 0)}",
            "",
            "STATS:",
            f"Strength: {self.character_manager.get_total_stat('strength')}",
            f"Dexterity: {self.character_manager.get_total_stat('dexterity')}",
            f"Constitution: {self.character_manager.get_total_stat('constitution')}",
            f"Intelligence: {self.character_manager.get_total_stat('intelligence')}",
            f"Wisdom: {self.character_manager.get_total_stat('wisdom')}",
            f"Charisma: {self.character_manager.get_total_stat('charisma')}",
            f"Armor Class: {self.character_manager.get_armor_class()}"
        ]

        y_pos = 100
        for info in char_info:
            if info == "":
                y_pos += 15
                continue

            if info == "STATS:":
                color = MENU_SELECTED
                font_to_use = self.ui_renderer.font
            else:
                color = WHITE
                font_to_use = self.ui_renderer.small_font

            text = font_to_use.render(info, True, color)
            self.screen.blit(text, (100, y_pos))
            y_pos += 25

        # Instructions
        instruction = self.ui_renderer.small_font.render("Press ESC or C to return", True, MENU_TEXT)
        instruction_rect = instruction.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 50))
        self.screen.blit(instruction, instruction_rect)

    def draw_help_screen(self):
        """Draw help screen"""
        self.screen.fill(MENU_BG)

        title = self.ui_renderer.large_font.render("❓ HELP", True, WHITE)
        title_rect = title.get_rect(center=(self.WIDTH // 2, 50))
        self.screen.blit(title, title_rect)

        help_text = load_help_text()

        y_pos = 100
        for line in help_text:
            if line == "":
                y_pos += 15
                continue

            if line.isupper() and ":" not in line:
                color = MENU_SELECTED
                font_to_use = self.ui_renderer.font
            else:
                color = MENU_TEXT
                font_to_use = self.ui_renderer.small_font

            text = font_to_use.render(line, True, color)
            text_rect = text.get_rect(center=(self.WIDTH // 2, y_pos))
            self.screen.blit(text, text_rect)
            y_pos += 25

    def draw(self):
        """Draw current state"""
        # Debug: Print current state occasionally
        # if self.animation_timer % 60 == 0:  # Every 4 seconds at 15 FPS
            # print(f"Current draw state: {self.current_state}")

        if self.current_state == GameState.OPENING:
            self.draw_opening_screen()

        elif self.current_state == GameState.MAIN_MENU:
            menu_options = ["🎮 Start Game", "❓ Help", "🚪 Quit"]
            self.ui_renderer.draw_enhanced_menu(self.screen, "MAGITECH RPG", menu_options,
                                                self.selected_option, "Choose your destiny!",
                                                self.animation_timer)

        elif self.current_state == GameState.CHARACTER_SELECT:
            self.draw_character_select_screen()

        elif self.current_state == GameState.CREATE_CHARACTER:
            self.draw_create_character_screen()

        elif self.current_state == GameState.GAME_BOARD:
            self.draw_game_board()

        elif self.current_state == GameState.FIGHT:
            self.draw_fight_screen()

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

        print(f"{changelog}")

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