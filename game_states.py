import pygame
import sys
import math
import random
import os

# Import our custom modules
from animated_player import AnimatedPlayer
from tile_map import EnhancedTileMap
from ui_components import *
from game_data import CharacterManager, EnemyManager, Store, create_sample_files


class GameState:
    """Game state constants"""
    OPENING = 0
    MAIN_MENU = 1
    GAME_BOARD = 2
    FIGHT = 3
    STORE = 4
    INVENTORY = 5
    CHARACTER_SHEET = 6
    HELP = 7

def is_too_close(x, y, positions, min_distance=20):
    """Check if (x,y) is too close to any position in positions."""
    for px, py in positions:
        if math.dist((x, y), (px, py)) < min_distance:
            return True
    return False


class EnhancedGameManager:
    """Main game manager with modular architecture"""

    def __init__(self):
        # Initialize Pygame
        pygame.init()

        # Screen settings
        self.WIDTH, self.HEIGHT = 800, 600
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Magitech RPG Adventure Game")

        # Game state
        self.current_state = GameState.OPENING
        self.selected_option = 0
        self.animation_timer = 0

        # Initialize subsystems
        self.character_manager = CharacterManager()
        self.enemy_manager = EnemyManager()
        self.store = Store()

        # Initialize visual systems
        self.ui_renderer = UIRenderer(self.WIDTH, self.HEIGHT)
        self.particles = ParticleSystem()
        self.damage_texts = []

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

        # Combat system
        self.current_enemy = None
        self.combat_messages = []

        # Setup initial world
        self.setup_world_objects()

        # Add static shop in top-right corner
        static_shop = Shop(world_width - 80, 20)  # Top-right corner
        self.shops.append(static_shop)

        # Add static shop in top-right corner
        static_rest = RestArea(world_width - 80, 750)  # Top-right corner
        self.rests.append(static_rest)

    def load_map_data(self):
        """Load map data and create tiles"""
        self.map_tiles = self.tile_map.load_map_from_file("map.txt")

    def setup_world_objects(self):
        """Setup game world objects based on map"""
        # Clear existing objects
        self.enemies.clear()
        self.treasures.clear()
        # self.treasure_positions.clear()
        self.shops.clear()
        self.rests.clear()

        # Parse map for object positions
        object_positions = self.tile_map.parse_map_for_objects()

        # Create treasures - make them smaller
        treasure_positions = object_positions.get('treasures', [])
        if not treasure_positions:
            # Add some manual treasure positions
            treasure_positions = [
                (random.randint(50, 750), random.randint(50, 550))  # adjust to map size
                for _ in range(8)  # same number of treasures as your original list
            ]

            for x, y in treasure_positions:
                treasure = Treasure(x, y)
                self.treasures.append(treasure)

        # Create enemies - ensure they spawn
        enemy_positions = object_positions.get('enemies', [])
        if not enemy_positions:
            # Generate enemy positions with spacing rules
            enemy_positions = []
            num_enemies = 18  # adjust as needed
            max_attempts = 1000  # safety cap to avoid infinite loops

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

    def handle_keypress(self, key):
        """Handle keyboard input based on current state"""
        if self.current_state == GameState.OPENING:
            self.current_state = GameState.MAIN_MENU

        elif self.current_state == GameState.MAIN_MENU:
            if key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % 4
            elif key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % 4
            elif key == pygame.K_RETURN:
                if self.selected_option == 0:  # Start Game
                    if not self.character_manager.load_character("Characters/test_hero.json"):
                        self.character_manager.create_sample_character()
                    self.current_state = GameState.GAME_BOARD

                elif self.selected_option == 1:  # Load Character
                    self.load_character_menu()

                elif self.selected_option == 2:  # Help
                    self.current_state = GameState.HELP

                elif self.selected_option == 3:  # Quit
                    return False

            elif key == pygame.K_ESCAPE:
                return False

        elif self.current_state == GameState.GAME_BOARD:
            if key == pygame.K_ESCAPE:
                return False
            elif key == pygame.K_i:
                self.current_state = GameState.INVENTORY
            elif key == pygame.K_c:
                self.current_state = GameState.CHARACTER_SHEET
            elif key == pygame.K_h:
                self.current_state = GameState.HELP

        elif self.current_state == GameState.INVENTORY:
            if key == pygame.K_ESCAPE or key == pygame.K_i:
                self.current_state = GameState.GAME_BOARD

        elif self.current_state == GameState.CHARACTER_SHEET:
            if key == pygame.K_ESCAPE or key == pygame.K_c:
                self.current_state = GameState.GAME_BOARD

        elif self.current_state == GameState.STORE:
            if key == pygame.K_ESCAPE:
                self.current_state = GameState.GAME_BOARD

        elif self.current_state == GameState.HELP:
            if key == pygame.K_ESCAPE or key == pygame.K_h:
                self.current_state = GameState.GAME_BOARD

        elif self.current_state == GameState.FIGHT:
            if key == pygame.K_SPACE:
                self.handle_combat_action()
            elif key == pygame.K_ESCAPE:
                self.current_state = GameState.GAME_BOARD

        return True

    def load_character_menu(self):
        """Simple character loading - loads first available character"""
        chars_dir = "Characters"
        if os.path.exists(chars_dir):
            char_files = [f for f in os.listdir(chars_dir) if f.endswith('.json')]
            if char_files:
                char_path = os.path.join(chars_dir, char_files[0])
                if self.character_manager.load_character(char_path):
                    self.current_state = GameState.GAME_BOARD

    def handle_combat_action(self):
        """Handle combat action"""
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
            return

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

        # Update floating damage texts
        for damage_text in self.damage_texts[:]:
            if not damage_text.update():
                self.damage_texts.remove(damage_text)

        if self.current_state == GameState.GAME_BOARD:
            # Update animated player position
            world_width, world_height = self.tile_map.get_world_pixel_size()
            moved = self.animated_player.update_position(world_width, world_height)

            # Update camera if player moved
            if moved:
                self.camera.update(self.animated_player.x + self.animated_player.display_width // 2,
                                   self.animated_player.y + self.animated_player.display_height // 2)

            # Check for collisions
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
        title_surface = self.ui_renderer.title_font.render("MAGITECH RPG Game", True, MENU_SELECTED)
        title_rect = title_surface.get_rect(center=(self.WIDTH // 2, 150))
        self.screen.blit(title_surface, title_rect)

        # Subtitle
        subtitle = self.ui_renderer.font.render("With Animated Characters and Tile Maps", True, MENU_TEXT)
        subtitle_rect = subtitle.get_rect(center=(self.WIDTH // 2, 200))
        self.screen.blit(subtitle, subtitle_rect)

        # Animated prompt
        alpha = int(128 + 127 * math.sin(self.animation_timer * 0.1))
        prompt_surface = self.ui_renderer.font.render("Press any key to begin your adventure...", True, MENU_SELECTED)
        prompt_surface.set_alpha(alpha)
        prompt_rect = prompt_surface.get_rect(center=(self.WIDTH // 2, self.HEIGHT - 150))
        self.screen.blit(prompt_surface, prompt_rect)

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

        # Draw UI overlay
        self.ui_renderer.draw_ui_overlay(self.screen, self.character_manager.character_data)

        # Draw instructions
        instructions = [
            "Arrow Keys: Move character",
            "Walk into objects to interact",
            "I: Inventory  C: Character Sheet  H: Help",
            "ESC: Quit"
        ]
        self.ui_renderer.draw_instructions_panel(self.screen, instructions)

        # Draw floating damage texts with proper world-to-screen conversion
        for damage_text in self.damage_texts:
            if hasattr(damage_text, 'world_pos') and damage_text.world_pos:
                damage_text.draw_at_world_pos(self.screen, self.camera)
            else:
                damage_text.draw(self.screen)

        # Draw particles
        self.particles.draw(self.screen)

    def draw_fight_screen(self):
        """Draw the fight screen"""
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

    def draw_store_screen(self):
        """Draw the store screen"""
        self.screen.fill(MENU_BG)

        title = self.ui_renderer.large_font.render("🪙 MAGIC SHOP", True, WHITE)
        title_rect = title.get_rect(center=(self.WIDTH // 2, 50))
        self.screen.blit(title, title_rect)

        if self.character_manager.character_data:
            credits = self.character_manager.character_data.get("Credits", 0)
            credits_text = self.ui_renderer.font.render(f"💰 Credits: {credits}", True, GOLD)
            self.screen.blit(credits_text, (50, 100))

        # Simple store display
        y_pos = 150
        for i, item in enumerate(self.store.items[:10]):  # Show first 10 items
            color = GREEN if (self.character_manager.character_data and
                              item.price <= self.character_manager.character_data.get("Credits", 0)) else RED

            item_text = self.ui_renderer.small_font.render(f"{item.name} - {item.price} credits", True, color)
            self.screen.blit(item_text, (50, y_pos))
            y_pos += 25

        # Instructions
        instruction = self.ui_renderer.font.render("ESC: Return to game", True, WHITE)
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

        help_text = [
            "ENHANCED MAGITECH RPG",
            "",
            "CONTROLS:",
            "Arrow Keys - Move your character",
            "I - Open inventory",
            "C - Open character sheet",
            "H - Open help screen",
            "Walk into enemies (red circles) to fight",
            "Walk into treasure (gold circles) to collect",
            "Walk into shops (purple squares) to buy items",
            "",
            "FEATURES:",
            "- Animated character sprites",
            "- Tile-based world map",
            "- Camera follows player",
            "- Enhanced visual effects",
            "- Character progression system",
            "",
            "Press ESC or H to return"
        ]

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
        if self.current_state == GameState.OPENING:
            self.draw_opening_screen()

        elif self.current_state == GameState.MAIN_MENU:
            menu_options = ["🎮 Start Game", "📁 Load Character", "❓ Help", "🚪 Quit"]
            self.ui_renderer.draw_enhanced_menu(self.screen, "MAGITECH RPG", menu_options,
                                                self.selected_option, "Choose your destiny!",
                                                self.animation_timer)

        elif self.current_state == GameState.GAME_BOARD:
            self.draw_game_board()

        elif self.current_state == GameState.FIGHT:
            self.draw_fight_screen()

        elif self.current_state == GameState.STORE:
            self.draw_store_screen()

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

        print("🎮 Enhanced Magitech RPG - Modular Edition")
        print("=" * 50)
        print("Features:")
        print("• 🏃 Animated character with 8-frame sprites")
        print("• 🗺️ Tile-based world map system")
        print("• 📷 Smooth camera following")
        print("• ✨ Modular code architecture")
        print("• 🎯 Enhanced collision detection")
        print("=" * 50)

        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    result = self.handle_keypress(event.key)
                    if not result:
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