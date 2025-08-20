"""
Magitech RPG Adventure - Main Game Client - FIXED VERSION
Enhanced multiplayer implementation with proper synchronization and Zelda-inspired world
"""

import pygame
import math
import time
import random
import sys
import os
from typing import Dict, List, Tuple, Optional

# Import game modules
from NetworkManager_Class import NetworkManager
from combat_system import CombatSystem
from world_map import WorldMap
from fight import *
from loot import *
from new_character_form import *

# Initialize Pygame
pygame.init()

# Screen settings
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Magitech RPG Adventure - Fixed Multiplayer")

# Enhanced color palette
COLORS = {
    'WHITE': (255, 255, 255),
    'BLACK': (0, 0, 0),
    'BLUE': (0, 0, 255),
    'GRAY': (200, 200, 200),
    'GREEN': (0, 255, 0),
    'RED': (255, 0, 0),
    'PURPLE': (128, 0, 128),
    'ORANGE': (255, 165, 0),
    'DARK_BLUE': (25, 25, 55),
    'LIGHT_BLUE': (100, 150, 255),
    'GOLD': (255, 215, 0),
    'SILVER': (192, 192, 192),
    'HEALTH_BAR_COLOR': (255, 50, 50),
    'HEALTH_BAR_BG': (100, 0, 0),
    'MANA_BAR_COLOR': (50, 100, 255),
    'MANA_BAR_BG': (0, 0, 100),
    'UI_BG_COLOR': (30, 30, 30),
    'UI_BORDER_COLOR': (100, 100, 100),
    'MENU_BG': (15, 20, 35),
    'MENU_ACCENT': (45, 85, 135),
    'MENU_HIGHLIGHT': (65, 105, 165),
    'MENU_TEXT': (220, 220, 220),
    'MENU_SELECTED': (255, 215, 0)
}

# Fonts
try:
    FONTS = {
        'title': pygame.font.Font(None, 64),
        'subtitle': pygame.font.Font(None, 36),
        'normal': pygame.font.Font(None, 28),
        'small': pygame.font.Font(None, 20),
        'large': pygame.font.Font(None, 48)
    }
except:
    FONTS = {
        'title': pygame.font.Font(None, 64),
        'subtitle': pygame.font.Font(None, 36),
        'normal': pygame.font.Font(None, 28),
        'small': pygame.font.Font(None, 20),
        'large': pygame.font.Font(None, 48)
    }


# Game states
class GameState:
    MAIN_MENU = "main_menu"
    LOGIN = "login"
    REGISTER = "register"
    CHARACTER_SELECT = "character_select"
    CHARACTER_CREATE = "character_create"
    SESSION_BROWSER = "session_browser"
    SESSION_CREATE = "session_create"
    GAME_WORLD = "game_world"
    COMBAT = "combat"
    INVENTORY = "inventory"
    SETTINGS = "settings"


class Player:
    def __init__(self):
        self.x = 400
        self.y = 300
        self.speed = 120  # pixels per second
        self.size = 24
        self.color = COLORS['BLUE']
        self.character_data = {}
        self.last_network_update = 0
        self.network_update_interval = 0.05  # Update network every 50ms for smoother movement
        self.movement_threshold = 2  # Minimum movement to trigger network update

    def update(self, dt: float, keys, world_map: WorldMap):
        """Update player movement with collision detection"""
        old_x, old_y = self.x, self.y

        # Calculate movement
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -self.speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed * dt
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -self.speed * dt
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed * dt

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            dx *= 0.707  # 1/sqrt(2)
            dy *= 0.707

        # Check collision for X movement
        new_x = self.x + dx
        tile_x = int(new_x // world_map.tile_size)
        tile_y = int(self.y // world_map.tile_size)

        if world_map.is_passable(tile_x, tile_y):
            self.x = new_x

        # Check collision for Y movement
        new_y = self.y + dy
        tile_x = int(self.x // world_map.tile_size)
        tile_y = int(new_y // world_map.tile_size)

        if world_map.is_passable(tile_x, tile_y):
            self.y = new_y

        # Keep player in bounds
        self.x = max(self.size, min(world_map.width * world_map.tile_size - self.size, self.x))
        self.y = max(self.size, min(world_map.height * world_map.tile_size - self.size, self.y))

        # Return True if position changed significantly
        distance_moved = ((self.x - old_x) ** 2 + (self.y - old_y) ** 2) ** 0.5
        return distance_moved > self.movement_threshold

    def render(self, screen: pygame.Surface, world_map: WorldMap):
        """Render player on screen"""
        screen_x, screen_y = world_map.world_to_screen(self.x, self.y)

        # Draw player circle
        pygame.draw.circle(screen, self.color, (int(screen_x), int(screen_y)), self.size)
        pygame.draw.circle(screen, COLORS['WHITE'], (int(screen_x), int(screen_y)), self.size, 2)

        # Draw player name if available
        if self.character_data.get('Name'):
            name_surface = FONTS['small'].render(self.character_data['Name'], True, COLORS['WHITE'])
            name_rect = name_surface.get_rect(center=(screen_x, screen_y - self.size - 15))
            screen.blit(name_surface, name_rect)


class Game:
    def __init__(self):
        self.state = GameState.MAIN_MENU
        self.running = True
        self.clock = pygame.time.Clock()

        # Network and systems - FIXED SERVER URL
        self.network_manager = NetworkManager(server_url="http://localhost:8000", debug=True)
        self.combat_system = CombatSystem(self.network_manager)
        self.world_map = WorldMap()

        # Game objects
        self.player = Player()
        self.other_players = {}

        # Enhanced synchronization tracking
        self.last_sequence = 0
        self.sync_failures = 0
        self.max_sync_failures = 5

        # UI state
        self.input_text = ""
        self.input_active = False
        self.menu_selection = 0
        self.error_message = ""
        self.info_message = ""
        self.message_timer = 0

        # Login/Register data
        self.username = ""
        self.password = ""
        self.login_step = 0  # 0=username, 1=password

        # Session data
        self.sessions_list = []
        self.selected_session = 0
        self.session_name = ""

        # Character data
        self.characters_list = []
        self.selected_character = 0
        self.character_form = None

        # Game world state
        self.last_sync = 0
        self.sync_interval = 0.2  # More frequent sync for better responsiveness
        self.last_position_update = 0

        # Chat system
        self.chat_messages = []
        self.chat_input = ""
        self.chat_visible = False

        # self.check_network_capabilities()

        # Set sync method based on capabilities
        if hasattr(self.network_manager, 'sync_session_enhanced'):
            print("Using enhanced synchronization")
        elif hasattr(self.network_manager, 'sync_session'):
            print("Using basic synchronization")
        else:
            print("Using manual synchronization fallback")

        print("Magitech RPG Adventure initialized - FIXED VERSION")

    def run(self):
        """Main game loop"""
        while self.running:
            dt = self.clock.tick(60) / 1000.0  # Delta time in seconds

            self.handle_events()
            self.update(dt)
            self.render()

        # Cleanup
        if self.network_manager.is_connected():
            self.network_manager.logout()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event.pos)

    def handle_keydown(self, event):
        """Handle keyboard input - FIXED VERSION"""
        if self.state == GameState.GAME_WORLD:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.MAIN_MENU
            elif event.key == pygame.K_i:
                self.state = GameState.INVENTORY
            elif event.key == pygame.K_RETURN:
                if self.chat_visible:
                    self.send_chat_message()
                else:
                    self.chat_visible = True
            elif event.key == pygame.K_SPACE:
                self.interact_with_world()
            elif self.chat_visible:
                self.handle_chat_input(event)

        elif self.state == GameState.COMBAT:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.GAME_WORLD

        elif self.state == GameState.CHARACTER_CREATE:
            # FIXED: Route keyboard input to character form
            if self.character_form:
                # If character form has handle_keydown method, use it
                if hasattr(self.character_form, 'handle_keydown'):
                    result = self.character_form.handle_keydown(event)
                    if result:
                        if result.get('action') == 'character_created':
                            self.load_characters_list()
                            self.state = GameState.CHARACTER_SELECT
                            self.show_info("Character created successfully!")
                        elif result.get('action') == 'cancel':
                            self.state = GameState.CHARACTER_SELECT
                        elif result.get('action') == 'error':
                            self.show_error(result.get('message', 'Character creation failed'))
                else:
                    # Fallback: handle input directly
                    self.handle_character_creation_input(event)
            elif event.key == pygame.K_ESCAPE:
                self.state = GameState.CHARACTER_SELECT

        elif self.input_active:
            self.handle_text_input(event)

        else:
            self.handle_menu_navigation(event)

    def handle_text_input(self, event):
        """Handle text input for forms"""
        if event.key == pygame.K_RETURN:
            self.process_text_input()
        elif event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
        elif event.key == pygame.K_ESCAPE:
            self.input_active = False
            self.input_text = ""
        else:
            if event.unicode.isprintable():
                self.input_text += event.unicode

    def handle_chat_input(self, event):
        """Handle chat input"""
        if event.key == pygame.K_RETURN:
            self.send_chat_message()
        elif event.key == pygame.K_BACKSPACE:
            self.chat_input = self.chat_input[:-1]
        elif event.key == pygame.K_ESCAPE:
            self.chat_visible = False
            self.chat_input = ""
        else:
            if event.unicode.isprintable():
                self.chat_input += event.unicode

    def handle_menu_navigation(self, event):
        """Handle menu navigation"""
        if event.key == pygame.K_UP:
            self.menu_selection = max(0, self.menu_selection - 1)
        elif event.key == pygame.K_DOWN:
            max_options = self.get_max_menu_options()
            self.menu_selection = min(max_options - 1, self.menu_selection + 1)
        elif event.key == pygame.K_RETURN:
            self.select_menu_option()
        elif event.key == pygame.K_ESCAPE:
            self.go_back()

    def handle_mouse_click(self, pos):
        """Handle mouse clicks - UPDATED"""
        if self.state == GameState.COMBAT:
            self.combat_system.handle_click(pos)
        elif self.state == GameState.CHARACTER_CREATE and self.character_form:
            # Let character form handle the click
            if hasattr(self.character_form, 'handle_click'):
                result = self.character_form.handle_click(pos)
                if result:
                    if result.get('action') == 'character_created':
                        self.load_characters_list()
                        self.state = GameState.CHARACTER_SELECT
                        self.show_info("Character created successfully!")
                    elif result.get('action') == 'cancel':
                        self.state = GameState.CHARACTER_SELECT

    def handle_character_creation_input(self, event):
        """Fallback character creation input handling"""
        # Initialize character creation state if needed
        if not hasattr(self, 'char_creation_name'):
            self.char_creation_name = ""
        if not hasattr(self, 'char_creation_step'):
            self.char_creation_step = 0  # 0 = name input

        if event.key == pygame.K_RETURN:
            if self.char_creation_step == 0:  # Name input
                if len(self.char_creation_name.strip()) >= 2:
                    # Create character with basic settings
                    success, data = self.network_manager.create_character({
                        'name': self.char_creation_name.strip(),
                        'class': 'Fighter',  # Default class
                        'race': 'Human',  # Default race
                    })

                    if success:
                        self.show_info("Character created successfully!")
                        self.load_characters_list()
                        self.state = GameState.CHARACTER_SELECT
                    else:
                        self.show_error(f"Failed to create character: {data}")

                    # Reset creation state
                    self.char_creation_name = ""
                    self.char_creation_step = 0
                else:
                    self.show_error("Character name must be at least 2 characters")

        elif event.key == pygame.K_BACKSPACE:
            if self.char_creation_step == 0:
                self.char_creation_name = self.char_creation_name[:-1]

        elif event.key == pygame.K_ESCAPE:
            self.char_creation_name = ""
            self.char_creation_step = 0
            self.state = GameState.CHARACTER_SELECT

        else:
            # Add character to name
            if event.unicode.isprintable() and self.char_creation_step == 0:
                if len(self.char_creation_name) < 20:
                    self.char_creation_name += event.unicode

    def update(self, dt: float):
        """Update game state"""
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.error_message = ""
                self.info_message = ""

        # State-specific updates
        if self.state == GameState.GAME_WORLD:
            self.update_game_world(dt)
        elif self.state == GameState.COMBAT:
            self.combat_system.update(dt)
        elif self.state == GameState.CHARACTER_CREATE and self.character_form:
            self.character_form.update(dt)

        # Enhanced network synchronization
        if self.network_manager.is_in_session():
            current_time = time.time()
            if current_time - self.last_sync > self.sync_interval:
                self.sync_with_server()
                self.last_sync = current_time

    def update_game_world(self, dt: float):
        """Update game world state"""
        if not self.network_manager.is_in_session():
            self.state = GameState.SESSION_BROWSER
            return

        # Update player movement
        keys = pygame.key.get_pressed()
        position_changed = self.player.update(dt, keys, self.world_map)

        # Send position update if changed significantly
        if position_changed:
            current_time = time.time()
            if current_time - self.player.last_network_update > self.player.network_update_interval:
                success = self.network_manager.update_position(self.player.x, self.player.y)
                if success:
                    self.player.last_network_update = current_time
                    self.sync_failures = 0
                else:
                    self.sync_failures += 1
                    if self.sync_failures >= self.max_sync_failures:
                        self.show_error("Connection lost - trying to reconnect...")

        # Update camera
        self.world_map.update_camera(self.player.x, self.player.y, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Check for combat activities
        combat_activities = self.network_manager.get_recent_activities('combat_started', 1)
        if combat_activities and not self.combat_system.combat_ui_visible:
            self.state = GameState.COMBAT
            self.combat_system.combat_ui_visible = True

    def sync_with_server(self):
        """Robust synchronization with multiple fallback methods"""
        try:
            sync_success = False

            # Method 1: Try enhanced sync
            if hasattr(self.network_manager, 'sync_session_enhanced'):
                try:
                    sync_data = self.network_manager.sync_session_enhanced(self.last_sequence)
                    if sync_data and sync_data.get('success'):
                        self.process_sync_data(sync_data)
                        sync_success = True
                except Exception as e:
                    print(f"Enhanced sync failed: {e}")

            # Method 2: Try basic sync
            if not sync_success and hasattr(self.network_manager, 'sync_session'):
                try:
                    sync_data = self.network_manager.sync_session()
                    if sync_data and sync_data.get('success'):
                        self.process_sync_data(sync_data)
                        sync_success = True
                except Exception as e:
                    print(f"Basic sync failed: {e}")

            # Method 3: Manual sync
            if not sync_success:
                try:
                    sync_data = self.manual_sync_session()
                    if sync_data:
                        self.process_sync_data(sync_data)
                        sync_success = True
                except Exception as e:
                    print(f"Manual sync failed: {e}")

            # Method 4: Ultra-basic fallback
            if not sync_success:
                sync_success = self.basic_sync_fallback()

            # Handle sync results
            if sync_success:
                self.sync_failures = 0
            else:
                self.sync_failures += 1
                if self.sync_failures >= self.max_sync_failures:
                    self.show_error("Connection issues - trying to reconnect...")

        except Exception as e:
            print(f"Sync error: {e}")
            self.sync_failures += 1

    def process_sync_data(self, sync_data):
        """Process synchronization data from server"""
        try:
            # Update sequence tracking if available
            if 'latest_sequence' in sync_data:
                self.last_sequence = sync_data.get('latest_sequence', self.last_sequence)

            # Update other players
            if 'players' in sync_data:
                self.update_other_players(sync_data.get('players', []))

            # Process new activities
            if 'activities' in sync_data:
                activities = sync_data.get('activities', [])
                self.process_activities(activities)

            # Update chat messages if any
            if 'chat_messages' in sync_data:
                self.chat_messages = sync_data['chat_messages'][-20:]  # Keep last 20 messages

        except Exception as e:
            print(f"Error processing sync data: {e}")

    def process_activities(self, activities: List[Dict]):
        """Process activities from server"""
        for activity in activities:
            activity_type = activity.get('type')
            data = activity.get('data', {})
            username = activity.get('username', 'Unknown')

            if activity_type == 'player_joined':
                self.show_info(f"{username} joined the session")
            elif activity_type == 'player_left':
                self.show_info(f"{username} left the session")
            elif activity_type == 'chat_message':
                message = data.get('message', '')
                self.chat_messages.append({
                    'username': username,
                    'message': message,
                    'timestamp': activity.get('timestamp', time.time())
                })
                self.chat_messages = self.chat_messages[-20:]  # Keep only recent
            elif activity_type == 'position_update':
                # Position updates are handled in update_other_players
                pass
            elif activity_type in ['combat_started', 'combat_action', 'enemy_action', 'turn_changed', 'combat_ended']:
                # Let combat system handle these
                pass

    def update_other_players(self, players_data: List[Dict]):
        """Enhanced other players update with interpolation"""
        current_time = time.time()
        new_players = {}

        for player_data in players_data:
            if player_data['user_id'] != self.network_manager.user_id:
                player_id = player_data['user_id']

                new_pos = player_data['position']

                if player_id in self.other_players:
                    # Existing player - update position with smooth interpolation
                    old_player = self.other_players[player_id]

                    # Simple interpolation for smoother movement
                    old_x, old_y = old_player['x'], old_player['y']
                    new_x, new_y = new_pos['x'], new_pos['y']

                    # Interpolate if the distance isn't too large
                    distance = ((new_x - old_x) ** 2 + (new_y - old_y) ** 2) ** 0.5

                    if distance < 100:  # Only interpolate for small movements
                        lerp_factor = 0.3  # Smooth interpolation
                        interpolated_x = old_x + (new_x - old_x) * lerp_factor
                        interpolated_y = old_y + (new_y - old_y) * lerp_factor
                    else:
                        # Large movement - just jump to new position
                        interpolated_x, interpolated_y = new_x, new_y

                    new_players[player_id] = {
                        'x': interpolated_x,
                        'y': interpolated_y,
                        'username': player_data['username'],
                        'character_data': player_data.get('character_data', {}),
                        'color': old_player.get('color', self.generate_player_color(player_id)),
                        'last_update': current_time
                    }
                else:
                    # New player
                    new_players[player_id] = {
                        'x': new_pos['x'],
                        'y': new_pos['y'],
                        'username': player_data['username'],
                        'character_data': player_data.get('character_data', {}),
                        'color': self.generate_player_color(player_id),
                        'last_update': current_time
                    }

        self.other_players = new_players

    def generate_player_color(self, player_id: str) -> Tuple[int, int, int]:
        """Generate consistent color for player based on ID"""
        random.seed(hash(player_id))
        colors = [
            COLORS['RED'], COLORS['GREEN'], COLORS['PURPLE'],
            COLORS['ORANGE'], COLORS['GOLD'], COLORS['SILVER']
        ]
        return random.choice(colors)

    def render(self):
        """Render current game state"""
        screen.fill(COLORS['BLACK'])

        if self.state == GameState.MAIN_MENU:
            self.render_main_menu()
        elif self.state == GameState.LOGIN:
            self.render_login()
        elif self.state == GameState.REGISTER:
            self.render_register()
        elif self.state == GameState.CHARACTER_SELECT:
            self.render_character_select()
        elif self.state == GameState.CHARACTER_CREATE:
            self.render_character_create()
        elif self.state == GameState.SESSION_BROWSER:
            self.render_session_browser()
        elif self.state == GameState.SESSION_CREATE:
            self.render_session_create()
        elif self.state == GameState.GAME_WORLD:
            self.render_game_world()
        elif self.state == GameState.COMBAT:
            self.render_combat()
        elif self.state == GameState.INVENTORY:
            self.render_inventory()

        # Render messages
        self.render_messages()

        pygame.display.flip()

    def render_main_menu(self):
        """Render main menu"""
        screen.fill(COLORS['MENU_BG'])

        # Title
        title_surface = FONTS['title'].render("Magitech RPG Adventure", True, COLORS['MENU_TEXT'])
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_surface, title_rect)

        # Subtitle
        subtitle_surface = FONTS['subtitle'].render("Fixed Multiplayer Edition", True, COLORS['GOLD'])
        subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, 200))
        screen.blit(subtitle_surface, subtitle_rect)

        # Menu options
        options = ["Login", "Register", "Exit"]
        for i, option in enumerate(options):
            color = COLORS['MENU_SELECTED'] if i == self.menu_selection else COLORS['MENU_TEXT']
            option_surface = FONTS['normal'].render(option, True, color)
            option_rect = option_surface.get_rect(center=(SCREEN_WIDTH // 2, 300 + i * 50))
            screen.blit(option_surface, option_rect)

        # Instructions
        instruction_surface = FONTS['small'].render("Use Arrow Keys and Enter to navigate", True, COLORS['GRAY'])
        instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, 500))
        screen.blit(instruction_surface, instruction_rect)

    def render_login(self):
        """Render login screen"""
        screen.fill(COLORS['MENU_BG'])

        title_surface = FONTS['large'].render("Login", True, COLORS['MENU_TEXT'])
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_surface, title_rect)

        # Username field
        username_label = FONTS['normal'].render("Username:", True, COLORS['MENU_TEXT'])
        screen.blit(username_label, (200, 250))

        username_value = self.username if self.login_step != 0 else (self.input_text if self.input_active else "")
        username_surface = FONTS['normal'].render(username_value, True, COLORS['WHITE'])
        username_rect = pygame.Rect(200, 280, 400, 30)
        pygame.draw.rect(screen, COLORS['WHITE'] if self.login_step == 0 and self.input_active else COLORS['GRAY'],
                         username_rect, 2)
        screen.blit(username_surface, (210, 285))

        # Password field
        password_label = FONTS['normal'].render("Password:", True, COLORS['MENU_TEXT'])
        screen.blit(password_label, (200, 330))

        password_display = "*" * len(self.password) if self.login_step != 1 else (
            "*" * len(self.input_text) if self.input_active else "")
        password_surface = FONTS['normal'].render(password_display, True, COLORS['WHITE'])
        password_rect = pygame.Rect(200, 360, 400, 30)
        pygame.draw.rect(screen, COLORS['WHITE'] if self.login_step == 1 and self.input_active else COLORS['GRAY'],
                         password_rect, 2)
        screen.blit(password_surface, (210, 365))

        # Instructions
        if not self.input_active:
            instruction = "Press Enter to start, Escape to go back"
        elif self.login_step == 0:
            instruction = "Enter username, press Enter to continue"
        else:
            instruction = "Enter password, press Enter to login"

        instruction_surface = FONTS['small'].render(instruction, True, COLORS['GRAY'])
        instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, 450))
        screen.blit(instruction_surface, instruction_rect)

    def render_register(self):
        """Render registration screen"""
        screen.fill(COLORS['MENU_BG'])

        title_surface = FONTS['large'].render("Register", True, COLORS['MENU_TEXT'])
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_surface, title_rect)

        # Similar to login but for registration
        username_label = FONTS['normal'].render("Username:", True, COLORS['MENU_TEXT'])
        screen.blit(username_label, (200, 250))

        username_value = self.username if self.login_step != 0 else (self.input_text if self.input_active else "")
        username_surface = FONTS['normal'].render(username_value, True, COLORS['WHITE'])
        username_rect = pygame.Rect(200, 280, 400, 30)
        pygame.draw.rect(screen, COLORS['WHITE'] if self.login_step == 0 and self.input_active else COLORS['GRAY'],
                         username_rect, 2)
        screen.blit(username_surface, (210, 285))

        password_label = FONTS['normal'].render("Password:", True, COLORS['MENU_TEXT'])
        screen.blit(password_label, (200, 330))

        password_display = "*" * len(self.password) if self.login_step != 1 else (
            "*" * len(self.input_text) if self.input_active else "")
        password_surface = FONTS['normal'].render(password_display, True, COLORS['WHITE'])
        password_rect = pygame.Rect(200, 360, 400, 30)
        pygame.draw.rect(screen, COLORS['WHITE'] if self.login_step == 1 and self.input_active else COLORS['GRAY'],
                         password_rect, 2)
        screen.blit(password_surface, (210, 365))

        if not self.input_active:
            instruction = "Press Enter to start, Escape to go back"
        elif self.login_step == 0:
            instruction = "Enter username (3+ characters), press Enter to continue"
        else:
            instruction = "Enter password (6+ characters), press Enter to register"

        instruction_surface = FONTS['small'].render(instruction, True, COLORS['GRAY'])
        instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, 450))
        screen.blit(instruction_surface, instruction_rect)

    def render_character_select(self):
        """Render character selection screen"""
        screen.fill(COLORS['MENU_BG'])

        title_surface = FONTS['large'].render("Select Character", True, COLORS['MENU_TEXT'])
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_surface, title_rect)

        if not self.characters_list:
            no_chars_surface = FONTS['normal'].render("No characters found. Create a new one!", True, COLORS['GRAY'])
            no_chars_rect = no_chars_surface.get_rect(center=(SCREEN_WIDTH // 2, 250))
            screen.blit(no_chars_surface, no_chars_rect)

            options = ["Create New Character", "Back"]
        else:
            # Display characters
            for i, character in enumerate(self.characters_list):
                color = COLORS['MENU_SELECTED'] if i == self.selected_character else COLORS['MENU_TEXT']
                char_name = character.get('name', 'Unknown')
                char_surface = FONTS['normal'].render(f"{char_name}", True, color)
                char_rect = char_surface.get_rect(center=(SCREEN_WIDTH // 2, 200 + i * 40))
                screen.blit(char_surface, char_rect)

            options = ["Select Character", "Create New Character", "Delete Character", "Back"]

        # Menu options
        start_y = 350 if self.characters_list else 300
        for i, option in enumerate(options):
            color = COLORS['MENU_SELECTED'] if i == self.menu_selection else COLORS['MENU_TEXT']
            option_surface = FONTS['normal'].render(option, True, color)
            option_rect = option_surface.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 40))
            screen.blit(option_surface, option_rect)

    def render_character_create(self):
        """Render character creation screen - UPDATED"""
        if self.character_form and hasattr(self.character_form, 'render'):
            self.character_form.render(screen)
        else:
            # Fallback simple character creation screen
            screen.fill(COLORS['MENU_BG'])

            title_surface = FONTS['large'].render("Create Character", True, COLORS['MENU_TEXT'])
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 150))
            screen.blit(title_surface, title_rect)

            # Character name input
            if not hasattr(self, 'char_creation_name'):
                self.char_creation_name = ""

            name_label = FONTS['normal'].render("Character Name:", True, COLORS['MENU_TEXT'])
            screen.blit(name_label, (200, 250))

            name_surface = FONTS['normal'].render(self.char_creation_name, True, COLORS['WHITE'])
            name_rect = pygame.Rect(200, 280, 400, 30)
            pygame.draw.rect(screen, COLORS['WHITE'], name_rect, 2)
            screen.blit(name_surface, (210, 285))

            # Instructions
            instruction1 = FONTS['small'].render("Enter character name (2-20 characters)", True, COLORS['GRAY'])
            instruction1_rect = instruction1.get_rect(center=(SCREEN_WIDTH // 2, 350))
            screen.blit(instruction1, instruction1_rect)

            instruction2 = FONTS['small'].render("Press Enter to create, Escape to cancel", True, COLORS['GRAY'])
            instruction2_rect = instruction2.get_rect(center=(SCREEN_WIDTH // 2, 380))
            screen.blit(instruction2, instruction2_rect)

            # Character info preview
            info_y = 420
            info_texts = [
                "Default Class: Fighter",
                "Default Race: Human",
                "Starting Level: 1"
            ]

            for info_text in info_texts:
                info_surface = FONTS['small'].render(info_text, True, COLORS['MENU_TEXT'])
                info_rect = info_surface.get_rect(center=(SCREEN_WIDTH // 2, info_y))
                screen.blit(info_surface, info_rect)
                info_y += 25

    def render_session_browser(self):
        """Render session browser"""
        screen.fill(COLORS['MENU_BG'])

        title_surface = FONTS['large'].render("Game Sessions", True, COLORS['MENU_TEXT'])
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_surface, title_rect)

        if not self.sessions_list:
            no_sessions_surface = FONTS['normal'].render("No active sessions. Create a new one!", True, COLORS['GRAY'])
            no_sessions_rect = no_sessions_surface.get_rect(center=(SCREEN_WIDTH // 2, 250))
            screen.blit(no_sessions_surface, no_sessions_rect)
        else:
            # Display sessions
            for i, session in enumerate(self.sessions_list):
                color = COLORS['MENU_SELECTED'] if i == self.selected_session else COLORS['MENU_TEXT']
                session_text = f"{session['name']} ({session['current_players']}/{session['max_players']})"
                session_surface = FONTS['normal'].render(session_text, True, color)
                session_rect = session_surface.get_rect(center=(SCREEN_WIDTH // 2, 180 + i * 30))
                screen.blit(session_surface, session_rect)

        # Menu options
        options = ["Join Session", "Create Session", "Refresh", "Back to Characters"]
        start_y = 350
        for i, option in enumerate(options):
            color = COLORS['MENU_SELECTED'] if i == self.menu_selection else COLORS['MENU_TEXT']
            option_surface = FONTS['normal'].render(option, True, color)
            option_rect = option_surface.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 40))
            screen.blit(option_surface, option_rect)

    def render_session_create(self):
        """Render session creation screen"""
        screen.fill(COLORS['MENU_BG'])

        title_surface = FONTS['large'].render("Create Session", True, COLORS['MENU_TEXT'])
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 150))
        screen.blit(title_surface, title_rect)

        # Session name input
        name_label = FONTS['normal'].render("Session Name:", True, COLORS['MENU_TEXT'])
        screen.blit(name_label, (200, 250))

        name_display = self.input_text if self.input_active else self.session_name
        name_surface = FONTS['normal'].render(name_display, True, COLORS['WHITE'])
        name_rect = pygame.Rect(200, 280, 400, 30)
        pygame.draw.rect(screen, COLORS['WHITE'] if self.input_active else COLORS['GRAY'], name_rect, 2)
        screen.blit(name_surface, (210, 285))

        if not self.input_active:
            instruction = "Press Enter to edit name, Escape to go back"
        else:
            instruction = "Enter session name, press Enter to create"

        instruction_surface = FONTS['small'].render(instruction, True, COLORS['GRAY'])
        instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, 400))
        screen.blit(instruction_surface, instruction_rect)

    def render_game_world(self):
        """Render game world with Zelda-inspired map"""
        # Render world map
        self.world_map.render(screen, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Render other players with smooth movement
        for player_data in self.other_players.values():
            screen_x, screen_y = self.world_map.world_to_screen(player_data['x'], player_data['y'])

            # Only render if on screen
            if -50 <= screen_x <= SCREEN_WIDTH + 50 and -50 <= screen_y <= SCREEN_HEIGHT + 50:
                pygame.draw.circle(screen, player_data['color'], (int(screen_x), int(screen_y)), 24)
                pygame.draw.circle(screen, COLORS['WHITE'], (int(screen_x), int(screen_y)), 24, 2)

                # Player name
                name_surface = FONTS['small'].render(player_data['username'], True, COLORS['WHITE'])
                name_rect = name_surface.get_rect(center=(screen_x, screen_y - 40))
                screen.blit(name_surface, name_rect)

        # Render player
        self.player.render(screen, self.world_map)

        # Render UI
        self.render_game_ui()

        # Render chat
        if self.chat_visible:
            self.render_chat()

    def render_game_ui(self):
        """Render enhanced game UI overlay"""
        # Character stats panel
        if self.player.character_data:
            ui_rect = pygame.Rect(10, 10, 220, 140)
            pygame.draw.rect(screen, COLORS['UI_BG_COLOR'], ui_rect)
            pygame.draw.rect(screen, COLORS['UI_BORDER_COLOR'], ui_rect, 2)

            y_offset = 20
            char_name = self.player.character_data.get('Name', 'Unknown')
            name_surface = FONTS['small'].render(f"Name: {char_name}", True, COLORS['WHITE'])
            screen.blit(name_surface, (15, y_offset))

            y_offset += 20
            level = self.player.character_data.get('level', 1)
            level_surface = FONTS['small'].render(f"Level: {level}", True, COLORS['WHITE'])
            screen.blit(level_surface, (15, y_offset))

            y_offset += 20
            hp = self.player.character_data.get('hit_points', 100)
            max_hp = self.player.character_data.get('max_hit_points', 100)
            hp_surface = FONTS['small'].render(f"HP: {hp}/{max_hp}", True, COLORS['WHITE'])
            screen.blit(hp_surface, (15, y_offset))

            # Health bar
            y_offset += 20
            health_bar_rect = pygame.Rect(15, y_offset, 200, 10)
            pygame.draw.rect(screen, COLORS['HEALTH_BAR_BG'], health_bar_rect)
            if max_hp > 0:
                health_width = int(200 * (hp / max_hp))
                health_fill_rect = pygame.Rect(15, y_offset, health_width, 10)
                pygame.draw.rect(screen, COLORS['HEALTH_BAR_COLOR'], health_fill_rect)

            y_offset += 15
            mana = self.player.character_data.get('mana_level', 50)
            max_mana = self.player.character_data.get('max_mana', 50)
            mana_surface = FONTS['small'].render(f"MP: {mana}/{max_mana}", True, COLORS['WHITE'])
            screen.blit(mana_surface, (15, y_offset))

            # Mana bar
            y_offset += 20
            mana_bar_rect = pygame.Rect(15, y_offset, 200, 10)
            pygame.draw.rect(screen, COLORS['MANA_BAR_BG'], mana_bar_rect)
            if max_mana > 0:
                mana_width = int(200 * (mana / max_mana))
                mana_fill_rect = pygame.Rect(15, y_offset, mana_width, 10)
                pygame.draw.rect(screen, COLORS['MANA_BAR_COLOR'], mana_fill_rect)

        # Network status indicator
        status_color = COLORS['GREEN'] if self.sync_failures == 0 else COLORS['ORANGE'] if self.sync_failures < 3 else \
        COLORS['RED']
        status_text = "Connected" if self.sync_failures == 0 else f"Sync Issues ({self.sync_failures})"
        status_surface = FONTS['small'].render(status_text, True, status_color)
        screen.blit(status_surface, (10, SCREEN_HEIGHT - 30))

        # Instructions
        instructions = [
            "WASD/Arrows: Move",
            "Space: Interact",
            "Enter: Chat",
            "I: Inventory",
            "Esc: Menu"
        ]

        for i, instruction in enumerate(instructions):
            instruction_surface = FONTS['small'].render(instruction, True, COLORS['WHITE'])
            screen.blit(instruction_surface, (SCREEN_WIDTH - 150, 10 + i * 20))

    def render_chat(self):
        """Render enhanced chat interface"""
        chat_rect = pygame.Rect(10, SCREEN_HEIGHT - 200, 450, 180)
        pygame.draw.rect(screen, (0, 0, 0, 180), chat_rect)
        pygame.draw.rect(screen, COLORS['WHITE'], chat_rect, 2)

        # Chat title
        title_surface = FONTS['small'].render("Chat", True, COLORS['GOLD'])
        screen.blit(title_surface, (15, SCREEN_HEIGHT - 195))

        # Chat messages
        for i, msg in enumerate(self.chat_messages[-7:]):  # Show last 7 messages
            msg_text = f"{msg.get('username', 'Unknown')}: {msg.get('message', '')}"
            msg_surface = FONTS['small'].render(msg_text, True, COLORS['WHITE'])
            screen.blit(msg_surface, (15, SCREEN_HEIGHT - 170 + i * 18))

        # Chat input
        input_rect = pygame.Rect(15, SCREEN_HEIGHT - 35, 430, 25)
        pygame.draw.rect(screen, COLORS['WHITE'], input_rect, 1)
        input_surface = FONTS['small'].render(self.chat_input, True, COLORS['WHITE'])
        screen.blit(input_surface, (20, SCREEN_HEIGHT - 32))

        # Input prompt
        prompt_surface = FONTS['small'].render("Type message and press Enter...", True, COLORS['GRAY'])
        if not self.chat_input:
            screen.blit(prompt_surface, (20, SCREEN_HEIGHT - 32))

    def render_combat(self):
        """Render combat screen"""
        # Render world background
        self.render_game_world()

        # Render combat UI
        self.combat_system.render_combat_ui(screen, FONTS['normal'])

    def render_inventory(self):
        """Render inventory screen"""
        screen.fill(COLORS['MENU_BG'])

        title_surface = FONTS['large'].render("Inventory", True, COLORS['MENU_TEXT'])
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 100))
        screen.blit(title_surface, title_rect)

        # Display items
        inventory = self.player.character_data.get('inventory', [])
        if not inventory:
            no_items_surface = FONTS['normal'].render("No items in inventory", True, COLORS['GRAY'])
            no_items_rect = no_items_surface.get_rect(center=(SCREEN_WIDTH // 2, 250))
            screen.blit(no_items_surface, no_items_rect)
        else:
            for i, item in enumerate(inventory):
                item_text = f"{item.get('name', 'Unknown Item')} x{item.get('quantity', 1)}"
                item_surface = FONTS['normal'].render(item_text, True, COLORS['WHITE'])
                screen.blit(item_surface, (100, 180 + i * 30))

        # Instructions
        instruction_surface = FONTS['small'].render("Press Escape to return", True, COLORS['GRAY'])
        instruction_rect = instruction_surface.get_rect(center=(SCREEN_WIDTH // 2, 500))
        screen.blit(instruction_surface, instruction_rect)

    def render_messages(self):
        """Render error/info messages"""
        if self.error_message:
            error_surface = FONTS['normal'].render(self.error_message, True, COLORS['RED'])
            error_rect = error_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
            # Add background for better visibility
            bg_rect = error_rect.inflate(20, 10)
            pygame.draw.rect(screen, COLORS['BLACK'], bg_rect)
            pygame.draw.rect(screen, COLORS['RED'], bg_rect, 2)
            screen.blit(error_surface, error_rect)

        if self.info_message:
            info_surface = FONTS['normal'].render(self.info_message, True, COLORS['GREEN'])
            info_rect = info_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
            # Add background for better visibility
            bg_rect = info_rect.inflate(20, 10)
            pygame.draw.rect(screen, COLORS['BLACK'], bg_rect)
            pygame.draw.rect(screen, COLORS['GREEN'], bg_rect, 2)
            screen.blit(info_surface, info_rect)

    # Helper methods for menu navigation and state management

    def get_max_menu_options(self) -> int:
        """Get maximum menu options for current state"""
        if self.state == GameState.MAIN_MENU:
            return 3
        elif self.state == GameState.CHARACTER_SELECT:
            return 4 if self.characters_list else 2
        elif self.state == GameState.SESSION_BROWSER:
            return 4
        return 1

    def select_menu_option(self):
        """Handle menu option selection"""
        if self.state == GameState.MAIN_MENU:
            if self.menu_selection == 0:  # Login
                self.state = GameState.LOGIN
                self.reset_input_state()
            elif self.menu_selection == 1:  # Register
                self.state = GameState.REGISTER
                self.reset_input_state()
            elif self.menu_selection == 2:  # Exit
                self.running = False

        elif self.state == GameState.CHARACTER_SELECT:
            if not self.characters_list:
                if self.menu_selection == 0:  # Create New Character
                    self.start_character_creation()
                elif self.menu_selection == 1:  # Back
                    self.network_manager.logout()
                    self.state = GameState.MAIN_MENU
            else:
                if self.menu_selection == 0:  # Select Character
                    self.select_character()
                elif self.menu_selection == 1:  # Create New Character
                    self.start_character_creation()
                elif self.menu_selection == 2:  # Delete Character
                    self.delete_character()
                elif self.menu_selection == 3:  # Back
                    self.network_manager.logout()
                    self.state = GameState.MAIN_MENU

        elif self.state == GameState.SESSION_BROWSER:
            if self.menu_selection == 0:  # Join Session
                self.join_selected_session()
            elif self.menu_selection == 1:  # Create Session
                self.state = GameState.SESSION_CREATE
                self.reset_input_state()
            elif self.menu_selection == 2:  # Refresh
                self.refresh_sessions_list()
            elif self.menu_selection == 3:  # Back
                self.state = GameState.CHARACTER_SELECT

        elif self.state in [GameState.LOGIN, GameState.REGISTER, GameState.SESSION_CREATE]:
            if not self.input_active:
                self.input_active = True
                self.input_text = ""

    def go_back(self):
        """Handle back navigation"""
        if self.state == GameState.LOGIN or self.state == GameState.REGISTER:
            self.state = GameState.MAIN_MENU
        elif self.state == GameState.CHARACTER_SELECT:
            self.network_manager.logout()
            self.state = GameState.MAIN_MENU
        elif self.state == GameState.SESSION_BROWSER:
            self.state = GameState.CHARACTER_SELECT
        elif self.state == GameState.SESSION_CREATE:
            self.state = GameState.SESSION_BROWSER
        elif self.state == GameState.GAME_WORLD:
            self.network_manager.leave_session()
            self.state = GameState.SESSION_BROWSER
        elif self.state == GameState.INVENTORY:
            self.state = GameState.GAME_WORLD
        elif self.state == GameState.COMBAT:
            self.state = GameState.GAME_WORLD

        self.reset_menu_state()

    def reset_input_state(self):
        """Reset input state"""
        self.input_active = False
        self.input_text = ""
        self.login_step = 0
        self.menu_selection = 0

    def reset_menu_state(self):
        """Reset menu state"""
        self.menu_selection = 0
        self.input_active = False
        self.input_text = ""

    def process_text_input(self):
        """Process text input based on current state"""
        if self.state == GameState.LOGIN:
            if self.login_step == 0:  # Username
                self.username = self.input_text
                self.input_text = ""
                self.login_step = 1
            else:  # Password
                self.password = self.input_text
                self.input_text = ""
                self.input_active = False
                self.attempt_login()

        elif self.state == GameState.REGISTER:
            if self.login_step == 0:  # Username
                if len(self.input_text) >= 3:
                    self.username = self.input_text
                    self.input_text = ""
                    self.login_step = 1
                else:
                    self.show_error("Username must be at least 3 characters")
            else:  # Password
                if len(self.input_text) >= 6:
                    self.password = self.input_text
                    self.input_text = ""
                    self.input_active = False
                    self.attempt_register()
                else:
                    self.show_error("Password must be at least 6 characters")

        elif self.state == GameState.SESSION_CREATE:
            if self.input_text.strip():
                self.session_name = self.input_text.strip()
                self.input_text = ""
                self.input_active = False
                self.create_session()
            else:
                self.show_error("Session name cannot be empty")

    def attempt_login(self):
        """Attempt to login"""
        success, data = self.network_manager.login(self.username, self.password)
        if success:
            self.show_info("Login successful!")
            self.load_characters_list()
            self.state = GameState.CHARACTER_SELECT
        else:
            self.show_error(f"Login failed: {data}")

        self.reset_input_state()

    def attempt_register(self):
        """Attempt to register"""
        success, data = self.network_manager.register(self.username, self.password)
        if success:
            self.show_info("Registration successful!")
            self.load_characters_list()
            self.state = GameState.CHARACTER_SELECT
        else:
            self.show_error(f"Registration failed: {data}")

        self.reset_input_state()

    def load_characters_list(self):
        """Load characters list from server"""
        self.characters_list = self.network_manager.get_characters()
        self.selected_character = 0

    def start_character_creation(self):
        """Start character creation"""
        self.character_form = CharacterCreationForm(self.network_manager)
        self.state = GameState.CHARACTER_CREATE

    def select_character(self):
        """Select and load character"""
        if self.characters_list and 0 <= self.selected_character < len(self.characters_list):
            character = self.characters_list[self.selected_character]
            success, data = self.network_manager.load_character(character['id'])
            if success:
                self.player.character_data = self.network_manager.character_data
                self.show_info(f"Character {character['name']} loaded!")
                self.refresh_sessions_list()
                self.state = GameState.SESSION_BROWSER
            else:
                self.show_error(f"Failed to load character: {data}")

    def delete_character(self):
        """Delete selected character"""
        if self.characters_list and 0 <= self.selected_character < len(self.characters_list):
            character = self.characters_list[self.selected_character]
            success, data = self.network_manager.delete_character(character['id'])
            if success:
                self.show_info(f"Character {character['name']} deleted!")
                self.load_characters_list()
            else:
                self.show_error(f"Failed to delete character: {data}")

    def refresh_sessions_list(self):
        """Refresh sessions list"""
        self.sessions_list = self.network_manager.get_sessions()
        self.selected_session = 0

    def join_selected_session(self):
        """Join selected session"""
        if self.sessions_list and 0 <= self.selected_session < len(self.sessions_list):
            session = self.sessions_list[self.selected_session]
            success, data = self.network_manager.join_session(session['id'],
                                                              self.network_manager.character_id)
            if success:
                self.show_info(f"Joined session {session['name']}!")

                # Set player spawn position
                spawn_x, spawn_y = self.world_map.get_spawn_position()
                self.player.x = spawn_x
                self.player.y = spawn_y

                # Update position on server
                self.network_manager.update_position(self.player.x, self.player.y)

                # Reset sync tracking
                self.last_sequence = 0
                self.sync_failures = 0

                self.state = GameState.GAME_WORLD
            else:
                self.show_error(f"Failed to join session: {data}")

    def create_session(self):
        """Create new session"""
        success, data = self.network_manager.create_session(self.session_name)
        if success:
            session_id = data.get('session_id')
            # Automatically join the created session
            success2, data2 = self.network_manager.join_session(session_id,
                                                                self.network_manager.character_id)
            if success2:
                self.show_info(f"Session '{self.session_name}' created and joined!")

                # Set player spawn position
                spawn_x, spawn_y = self.world_map.get_spawn_position()
                self.player.x = spawn_x
                self.player.y = spawn_y

                # Update position on server
                self.network_manager.update_position(self.player.x, self.player.y)

                # Reset sync tracking
                self.last_sequence = 0
                self.sync_failures = 0

                self.state = GameState.GAME_WORLD
            else:
                self.show_error(f"Created session but failed to join: {data2}")
        else:
            self.show_error(f"Failed to create session: {data}")

        self.session_name = ""

    def send_chat_message(self):
        """Send chat message"""
        if self.chat_input.strip() and self.network_manager.is_in_session():
            success, data = self.network_manager.send_chat_message(self.chat_input.strip())
            if not success:
                self.show_error(f"Failed to send message: {data}")

        self.chat_input = ""
        self.chat_visible = False

    def interact_with_world(self):
        """Interact with world objects"""
        # Get tile position
        tile_x = int(self.player.x // self.world_map.tile_size)
        tile_y = int(self.player.y // self.world_map.tile_size)

        # Try interaction
        interaction_result = self.world_map.interact_with_tile(tile_x, tile_y, self.player.character_data)

        if interaction_result:
            result_type = interaction_result['type']
            message = interaction_result['message']

            if result_type == 'loot':
                # Handle loot
                items = interaction_result['items']
                for item in items:
                    if item['type'] == 'gold':
                        # Add gold to character
                        current_gold = self.player.character_data.get('gold', 0)
                        self.player.character_data['gold'] = current_gold + item['amount']
                    else:
                        # Add item to inventory
                        inventory = self.player.character_data.get('inventory', [])
                        inventory.append(item)
                        self.player.character_data['inventory'] = inventory

                self.show_info(message)

            elif result_type == 'dungeon':
                # Start combat encounter
                dungeon_data = interaction_result['dungeon_data']
                enemy_data = self.generate_dungeon_enemy(dungeon_data)
                success = self.combat_system.start_combat(enemy_data)
                if success:
                    self.state = GameState.COMBAT
                else:
                    self.show_error("Failed to start combat")

            elif result_type == 'blessing':
                # Apply blessing
                blessing = interaction_result['blessing']
                self.apply_blessing(blessing)
                self.show_info(message)

            else:
                self.show_info(message)

    def generate_dungeon_enemy(self, dungeon_data: Dict) -> Dict:
        """Generate enemy for dungeon"""
        dungeon_level = dungeon_data.get('level', 1)
        dungeon_type = dungeon_data.get('type', 'cave')

        # Enemy types based on dungeon
        enemy_types = {
            'cave': ['Goblin', 'Orc', 'Cave Troll'],
            'ruins': ['Skeleton', 'Ghost', 'Ancient Guardian'],
            'tower': ['Wizard', 'Gargoyle', 'Fire Elemental']
        }

        enemies = enemy_types.get(dungeon_type, ['Goblin'])
        enemy_name = random.choice(enemies)

        # Scale enemy to dungeon level
        base_hp = 25
        base_ac = 12

        return {
            'name': f"Level {dungeon_level} {enemy_name}",
            'level': dungeon_level,
            'hit_points': base_hp + (dungeon_level * 10),
            'max_hit_points': base_hp + (dungeon_level * 10),
            'armor_class': base_ac + dungeon_level,
            'attack_bonus': dungeon_level + 2,
            'damage_dice': '1d8' if dungeon_level <= 2 else '2d6',
            'damage_bonus': dungeon_level,
            'type': dungeon_type
        }

    def apply_blessing(self, blessing: str):
        """Apply shrine blessing to character"""
        if blessing == 'health':
            current_hp = self.player.character_data.get('hit_points', 100)
            max_hp = self.player.character_data.get('max_hit_points', 100)
            self.player.character_data['hit_points'] = max_hp
        elif blessing == 'mana':
            max_mana = self.player.character_data.get('max_mana', 50)
            self.player.character_data['mana_level'] = max_mana
        elif blessing == 'strength':
            current_str = self.player.character_data.get('stats', {}).get('strength', 10)
            if 'stats' not in self.player.character_data:
                self.player.character_data['stats'] = {}
            self.player.character_data['stats']['strength'] = min(20, current_str + 1)
        elif blessing == 'wisdom':
            current_wis = self.player.character_data.get('stats', {}).get('wisdom', 10)
            if 'stats' not in self.player.character_data:
                self.player.character_data['stats'] = {}
            self.player.character_data['stats']['wisdom'] = min(20, current_wis + 1)

    def show_error(self, message: str):
        """Show error message"""
        self.error_message = message
        self.message_timer = 4.0
        print(f"Error: {message}")

    def show_info(self, message: str):
        """Show info message"""
        self.info_message = message
        self.message_timer = 3.0
        print(f"Info: {message}")

    def basic_sync_fallback(self):
        """Ultra-simple sync fallback that should work with any NetworkManager"""
        try:
            # Just check if we're still connected and in session
            if hasattr(self.network_manager, 'is_connected') and not self.network_manager.is_connected():
                self.sync_failures += 1
                return False

            if hasattr(self.network_manager, 'is_in_session') and not self.network_manager.is_in_session():
                self.state = GameState.SESSION_BROWSER
                return False

            # Try to get any available data
            players_data = []

            # Try different methods to get player data
            for method_name in ['get_session_players', 'get_players', 'get_other_players']:
                if hasattr(self.network_manager, method_name):
                    try:
                        method = getattr(self.network_manager, method_name)
                        result = method()
                        if result:
                            players_data = result
                            break
                    except:
                        continue

            # Update other players if we got data
            if players_data:
                self.update_other_players(players_data)

            self.sync_failures = 0
            return True

        except Exception as e:
            print(f"Basic sync fallback error: {e}")
            self.sync_failures += 1
            return False


def main():
    """Main function"""
    try:
        game = Game()
        game.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
