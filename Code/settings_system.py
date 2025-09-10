import pygame
import json
import os
from Code.ui_components import *


class GameSettings:
    """Game settings management class"""

    def __init__(self):
        self.settings_file = "../assets/game_settings.json"

        # Default settings
        self.defaults = {
            "master_volume": 0.7,
            "music_volume": 0.6,
            "sfx_volume": 0.8,
            "music_enabled": True,
            "sfx_enabled": True,
            "fullscreen": False,
            "show_fps": False,
            "auto_save": True,
            "difficulty_multiplier": 1.0,
            "animation_speed": 1.0,
            "combat_text_enabled": True,
            "screen_shake": True,
            "particle_effects": True,
            "show_instructions": False
        }

        # Current settings (loaded from file or defaults)
        self.settings = self.defaults.copy()
        self.load_settings()

    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    # Update settings with saved values, keeping defaults for missing keys
                    self.settings.update(saved_settings)
                    print("Settings loaded successfully")
            else:
                print("No settings file found, using defaults")
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.settings = self.defaults.copy()

    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            print("Settings saved successfully")
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def get(self, key):
        """Get a setting value"""
        return self.settings.get(key, self.defaults.get(key))

    def set(self, key, value):
        """Set a setting value"""
        if key in self.defaults:
            self.settings[key] = value
            return True
        return False

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.settings = self.defaults.copy()
        return self.save_settings()


class SettingsScreen:
    """Settings screen UI handler"""

    def __init__(self, game_settings, screen_width, screen_height):
        self.game_settings = game_settings
        self.screen_width = screen_width
        self.screen_height = screen_height

        # UI state
        self.selected_option = 0
        self.in_submenu = False
        self.submenu_type = None

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)

        # Settings categories and options
        self.setup_settings_menu()

    def setup_settings_menu(self):
        """Setup the settings menu structure"""
        self.settings_options = [
            {
                "name": "Audio Settings",
                "type": "submenu",
                "options": [
                    {"key": "music_enabled", "name": "Music Enabled", "type": "boolean"},
                    {"key": "sfx_enabled", "name": "Sound Effects", "type": "boolean"},
                    {"key": "master_volume", "name": "Master Volume", "type": "slider", "min": 0.0, "max": 1.0,
                     "step": 0.1},
                    {"key": "music_volume", "name": "Music Volume", "type": "slider", "min": 0.0, "max": 1.0,
                     "step": 0.1},
                    {"key": "sfx_volume", "name": "SFX Volume", "type": "slider", "min": 0.0, "max": 1.0, "step": 0.1}
                ]
            },
            {
                "name": "Display Settings",
                "type": "submenu",
                "options": [
                    {"key": "fullscreen", "name": "Fullscreen", "type": "boolean"},
                    {"key": "show_fps", "name": "Show FPS", "type": "boolean"},
                    {"key": "show_instructions", "name": "Show Instructions", "type": "boolean"},
                    {"key": "animation_speed", "name": "Animation Speed", "type": "slider", "min": 0.5, "max": 2.0,
                     "step": 0.1}
                ]
            },
            {
                "name": "Gameplay Settings",
                "type": "submenu",
                "options": [
                    {"key": "auto_save", "name": "Auto Save", "type": "boolean"},
                    {"key": "difficulty_multiplier", "name": "Difficulty", "type": "slider", "min": 0.5, "max": 2.0,
                     "step": 0.1},
                    {"key": "combat_text_enabled", "name": "Combat Text", "type": "boolean"},
                    {"key": "screen_shake", "name": "Screen Shake", "type": "boolean"},
                    {"key": "particle_effects", "name": "Particle Effects", "type": "boolean"}
                ]
            },
            {
                "name": "Reset to Defaults",
                "type": "action",
                "action": "reset_defaults"
            },
            {
                "name": "Save Settings",
                "type": "action",
                "action": "save_settings"
            },
            {
                "name": "Back to Main Menu",
                "type": "action",
                "action": "back"
            }
        ]

        self.current_submenu = None
        self.submenu_selected = 0

    def handle_input(self, key):
        """Handle input for settings screen"""
        if not self.in_submenu:
            # Main settings menu
            if key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.settings_options)
                return "navigate"
            elif key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.settings_options)
                return "navigate"
            elif key == pygame.K_RETURN:
                return self.activate_option()
            elif key == pygame.K_ESCAPE:
                return "back"
        else:
            # Submenu navigation
            if key == pygame.K_UP:
                self.submenu_selected = (self.submenu_selected - 1) % len(self.current_submenu["options"])
                return "navigate"
            elif key == pygame.K_DOWN:
                self.submenu_selected = (self.submenu_selected + 1) % len(self.current_submenu["options"])
                return "navigate"
            elif key == pygame.K_LEFT:
                return self.adjust_setting(-1)
            elif key == pygame.K_RIGHT:
                return self.adjust_setting(1)
            elif key == pygame.K_RETURN:
                return self.toggle_setting()
            elif key == pygame.K_ESCAPE:
                self.exit_submenu()
                return "navigate"

        return "continue"

    def activate_option(self):
        """Activate the selected main menu option"""
        option = self.settings_options[self.selected_option]

        if option["type"] == "submenu":
            self.current_submenu = option
            self.in_submenu = True
            self.submenu_selected = 0
            return "submenu"
        elif option["type"] == "action":
            return self.handle_action(option["action"])

        return "continue"

    def handle_action(self, action):
        """Handle action buttons"""
        if action == "reset_defaults":
            self.game_settings.reset_to_defaults()
            return "reset_defaults"
        elif action == "save_settings":
            success = self.game_settings.save_settings()
            return "save_success" if success else "save_failed"
        elif action == "back":
            return "back"

        return "continue"

    def exit_submenu(self):
        """Exit current submenu"""
        self.in_submenu = False
        self.current_submenu = None
        self.submenu_selected = 0

    def adjust_setting(self, direction):
        """Adjust slider setting"""
        if not self.in_submenu:
            return "continue"

        option = self.current_submenu["options"][self.submenu_selected]
        if option["type"] != "slider":
            return "continue"

        key = option["key"]
        current_value = self.game_settings.get(key)
        step = option["step"]
        min_val = option["min"]
        max_val = option["max"]

        new_value = current_value + (direction * step)
        new_value = max(min_val, min(max_val, new_value))
        new_value = round(new_value, 2)  # Round to 2 decimal places

        self.game_settings.set(key, new_value)
        return "setting_changed"

    def toggle_setting(self):
        """Toggle boolean setting"""
        if not self.in_submenu:
            return "continue"

        option = self.current_submenu["options"][self.submenu_selected]
        if option["type"] != "boolean":
            return "continue"

        key = option["key"]
        current_value = self.game_settings.get(key)
        self.game_settings.set(key, not current_value)
        return "setting_changed"

    def draw(self, screen):
        """Draw the settings screen"""
        screen.fill(MENU_BG)

        if not self.in_submenu:
            self.draw_main_menu(screen)
        else:
            self.draw_submenu(screen)

    def draw_main_menu(self, screen):
        """Draw main settings menu"""
        # Title
        title = self.title_font.render("SETTINGS", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 60))
        screen.blit(title, title_rect)

        # Menu options
        start_y = 150
        option_height = 50

        for i, option in enumerate(self.settings_options):
            y_pos = start_y + i * option_height

            # Option background
            option_rect = pygame.Rect(self.screen_width // 4, y_pos - 15, self.screen_width // 2, 40)

            if i == self.selected_option:
                # Selected option
                pygame.draw.rect(screen, MENU_HIGHLIGHT, option_rect)
                pygame.draw.rect(screen, MENU_SELECTED, option_rect, 3)
                color = MENU_SELECTED
            else:
                pygame.draw.rect(screen, MENU_ACCENT, option_rect)
                pygame.draw.rect(screen, MENU_TEXT, option_rect, 1)
                color = MENU_TEXT

            # Option text
            option_text = option['name']
            text_surface = self.font.render(option_text, True, color)
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, y_pos))
            screen.blit(text_surface, text_rect)

        # Instructions
        instructions = [
            "UP/DOWN: Navigate  ENTER: Select  ESC: Back"
        ]
        self.draw_instructions(screen, instructions)

    def draw_submenu(self, screen):
        """Draw settings submenu"""
        # Title
        title = self.title_font.render(self.current_submenu["name"].upper(), True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 60))
        screen.blit(title, title_rect)

        # Settings options
        start_y = 150
        option_height = 45

        for i, option in enumerate(self.current_submenu["options"]):
            y_pos = start_y + i * option_height

            # Option background
            option_rect = pygame.Rect(50, y_pos - 15, self.screen_width - 100, 35)

            if i == self.submenu_selected:
                pygame.draw.rect(screen, MENU_HIGHLIGHT, option_rect)
                pygame.draw.rect(screen, MENU_SELECTED, option_rect, 2)
                text_color = MENU_SELECTED
            else:
                text_color = WHITE

            # Setting name
            name_surface = self.font.render(option["name"], True, text_color)
            screen.blit(name_surface, (60, y_pos - 5))

            # Setting value
            value_text = self.get_setting_display_value(option)
            value_surface = self.font.render(value_text, True, text_color)
            value_rect = value_surface.get_rect(right=self.screen_width - 60, centery=y_pos)
            screen.blit(value_surface, value_rect)

        # Instructions
        instructions = [
            "UP/DOWN: Navigate  LEFT/RIGHT: Adjust  ENTER: Toggle  ESC: Back"
        ]
        self.draw_instructions(screen, instructions)

    def get_setting_display_value(self, option):
        """Get display value for a setting - ENHANCED VERSION"""
        key = option["key"]
        value = self.game_settings.get(key)

        if option["type"] == "boolean":
            return "ON" if value else "OFF"
        elif option["type"] == "slider":
            if key == "difficulty_multiplier":
                # Enhanced difficulty display names
                difficulty_names = {
                    0.5: "Very Easy",
                    0.6: "Easy",
                    0.8: "Normal-",
                    1.0: "Normal",
                    1.2: "Normal+",
                    1.4: "Hard",
                    1.6: "Very Hard",
                    1.8: "Expert",
                    2.0: "Nightmare"
                }
                return difficulty_names.get(value, f"{value:.1f}x")
            elif "volume" in key:
                return f"{int(value * 100)}%"
            else:
                return f"{value:.1f}"

        return str(value)

    def draw_instructions(self, screen, instructions):
        """Draw instruction text at bottom of screen"""
        instruction_y = self.screen_height - 80
        for instruction in instructions:
            instruction_surface = self.small_font.render(instruction, True, WHITE)
            instruction_rect = instruction_surface.get_rect(center=(self.screen_width // 2, instruction_y))
            screen.blit(instruction_surface, instruction_rect)
            instruction_y += 20


class SettingsIntegration:
    """Integration class to connect settings with main game"""

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.game_settings = GameSettings()
        self.settings_screen = SettingsScreen(self.game_settings,
                                              game_manager.WIDTH,
                                              game_manager.HEIGHT)

        # Apply initial settings
        self.apply_settings_to_game()

    def apply_settings_to_game(self):
        """Apply current settings to the game - ENHANCED VERSION"""
        # Apply audio settings
        if hasattr(self.game_manager, 'combat_integration'):
            sound_manager = self.game_manager.combat_integration.sound_manager
            sound_manager.music_enabled = self.game_settings.get("music_enabled")
            sound_manager.sfx_enabled = self.game_settings.get("sfx_enabled")
            sound_manager.set_master_volume(self.game_settings.get("master_volume"))

        # Apply display settings
        self.game_manager.show_instructions = self.game_settings.get("show_instructions")

        # Apply gameplay settings - FIXED DIFFICULTY APPLICATION
        difficulty = self.game_settings.get("difficulty_multiplier")

        # Apply to enemy manager if available
        if hasattr(self.game_manager, 'enemy_manager'):
            print(f"DEBUG: Applying difficulty {difficulty} to enemy_manager")
            if hasattr(self.game_manager.enemy_manager, 'set_difficulty_multiplier'):
                self.game_manager.enemy_manager.set_difficulty_multiplier(difficulty)
            else:
                # Fallback: set attribute directly
                self.game_manager.enemy_manager.difficulty_multiplier = difficulty

        # Also apply to character manager's enemy manager if it exists
        if hasattr(self.game_manager, 'character_manager'):
            char_mgr = self.game_manager.character_manager
            if hasattr(char_mgr, 'enemy_manager'):
                print(f"DEBUG: Applying difficulty {difficulty} to character_manager.enemy_manager")
                if hasattr(char_mgr.enemy_manager, 'set_difficulty_multiplier'):
                    char_mgr.enemy_manager.set_difficulty_multiplier(difficulty)
                else:
                    char_mgr.enemy_manager.difficulty_multiplier = difficulty

        # Apply to game states if available
        if hasattr(self.game_manager, 'game_states'):
            for state in self.game_manager.game_states.values():
                if hasattr(state, 'enemy_manager'):
                    print(f"DEBUG: Applying difficulty {difficulty} to game_state.enemy_manager")
                    if hasattr(state.enemy_manager, 'set_difficulty_multiplier'):
                        state.enemy_manager.set_difficulty_multiplier(difficulty)
                    else:
                        state.enemy_manager.difficulty_multiplier = difficulty

        # Apply to any combat systems
        if hasattr(self.game_manager, 'combat_integration'):
            combat_integration = self.game_manager.combat_integration
            if hasattr(combat_integration, 'combat_manager'):
                combat_mgr = combat_integration.combat_manager
                if hasattr(combat_mgr, 'character_manager'):
                    char_mgr = combat_mgr.character_manager
                    if hasattr(char_mgr, 'enemy_manager'):
                        print(f"DEBUG: Applying difficulty {difficulty} to combat.character_manager.enemy_manager")
                        if hasattr(char_mgr.enemy_manager, 'set_difficulty_multiplier'):
                            char_mgr.enemy_manager.set_difficulty_multiplier(difficulty)
                        else:
                            char_mgr.enemy_manager.difficulty_multiplier = difficulty

        print(f"DEBUG: Difficulty setting {difficulty} applied to all available enemy managers")

    def handle_settings_input(self, key):
        """Handle input for settings screen"""
        result = self.settings_screen.handle_input(key)

        if result == "back":
            self.apply_settings_to_game()  # Apply settings when leaving
            return "exit_settings"
        elif result in ["setting_changed", "reset_defaults"]:
            self.apply_settings_to_game()  # Apply settings immediately
            return "continue"
        elif result == "save_success":
            # Show save confirmation
            return "save_success"
        elif result == "save_failed":
            # Show save error
            return "save_failed"

        return "continue"

    def draw_settings(self, screen):
        """Draw the settings interface"""
        self.settings_screen.draw(screen)

    def get_setting(self, key):
        """Get a setting value"""
        return self.game_settings.get(key)

    def set_setting(self, key, value):
        """Set a setting value"""
        if self.game_settings.set(key, value):
            self.apply_settings_to_game()
            return True
        return False