"""
Character Creation Form for Magitech RPG
Handles character creation UI and validation - FIXED TEXT INPUT BUG
"""

import pygame
import random
import time
from typing import Dict, List, Tuple, Optional, Any


class CharacterCreationForm:
    """Character creation form with enhanced UI and validation"""

    def __init__(self, network_manager):
        # Character creation steps
        self.steps = [
            "name",  # 0: Enter name
            "race",  # 1: Select race
            "class",  # 2: Select class
            "stats",  # 3: Allocate stats
            "appearance",  # 4: Choose appearance
            "confirm"  # 5: Confirm and create
        ]

        self.network_manager = network_manager

        # Form state
        self.step = 0  # Current step in creation process
        self.character_data = self.initialize_character_data()

        # UI state
        self.selected_option = 0
        self.input_active = True  # FIX: Start with input active for name step
        self.input_text = ""
        self.error_message = ""
        self.success_message = ""
        self.message_timer = 0

        # Debug: Print initial state
        print(f"Character creation initialized - Step: {self.step} ({self.steps[0]}), Input active: {self.input_active}")

        # Available options
        self.races = ["Human", "Elf", "Dwarf", "Halfling", "Orc", "Gnome"]
        self.classes = ["Warrior", "Wizard", "Rogue", "Cleric", "Ranger", "Sorcerer"]
        self.appearances = ["Blue", "Red", "Green", "Purple", "Orange", "Yellow"]

        # Race bonuses
        self.race_bonuses = {
            "Human": {"strength": 1, "constitution": 1},
            "Elf": {"dexterity": 2, "intelligence": 1},
            "Dwarf": {"constitution": 2, "strength": 1},
            "Halfling": {"dexterity": 2, "charisma": 1},
            "Orc": {"strength": 2, "constitution": 1},
            "Gnome": {"intelligence": 2, "wisdom": 1}
        }

        # Class bonuses
        self.class_bonuses = {
            "Warrior": {"strength": 2, "constitution": 2},
            "Wizard": {"intelligence": 3, "wisdom": 1},
            "Rogue": {"dexterity": 3, "charisma": 1},
            "Cleric": {"wisdom": 2, "constitution": 1, "charisma": 1},
            "Ranger": {"dexterity": 2, "wisdom": 2},
            "Sorcerer": {"intelligence": 2, "charisma": 2}
        }

        # Stat point allocation
        self.available_points = 25
        self.min_stat = 8
        self.max_stat = 18

        # Colors for UI
        self.colors = {
            'WHITE': (255, 255, 255),
            'BLACK': (0, 0, 0),
            'GRAY': (128, 128, 128),
            'LIGHT_GRAY': (200, 200, 200),
            'DARK_GRAY': (64, 64, 64),
            'GREEN': (0, 255, 0),
            'RED': (255, 0, 0),
            'BLUE': (0, 0, 255),
            'PURPLE': (128, 0, 128),
            'ORANGE': (255, 165, 0),
            'YELLOW': (255, 255, 0),
            'GOLD': (255, 215, 0),
            'MENU_BG': (15, 20, 35),
            'MENU_ACCENT': (45, 85, 135),
            'MENU_HIGHLIGHT': (65, 105, 165),
            'MENU_TEXT': (220, 220, 220),
            'MENU_SELECTED': (255, 215, 0)
        }

        # Fonts
        try:
            self.fonts = {
                'title': pygame.font.Font(None, 48),
                'subtitle': pygame.font.Font(None, 36),
                'normal': pygame.font.Font(None, 28),
                'small': pygame.font.Font(None, 20),
                'large': pygame.font.Font(None, 40)
            }
        except:
            self.fonts = {
                'title': pygame.font.Font(None, 48),
                'subtitle': pygame.font.Font(None, 36),
                'normal': pygame.font.Font(None, 28),
                'small': pygame.font.Font(None, 20),
                'large': pygame.font.Font(None, 40)
            }

    def initialize_character_data(self) -> Dict:
        """Initialize character data with default values"""
        return {
            'Name': '',
            'race': '',
            'class': '',
            'level': 1,
            'experience': 0,
            'hit_points': 100,
            'max_hit_points': 100,
            'mana_level': 50,
            'max_mana': 50,
            'weapon_level': 1,
            'armor_level': 1,
            'gold': 100,
            'stats': {
                'strength': 10,
                'dexterity': 10,
                'constitution': 10,
                'intelligence': 10,
                'wisdom': 10,
                'charisma': 10
            },
            'inventory': [
                {'name': 'Health Potion', 'type': 'consumable', 'quantity': 3},
                {'name': 'Mana Potion', 'type': 'consumable', 'quantity': 2},
                {'name': 'Basic Sword', 'type': 'weapon', 'damage': 6}
            ],
            'appearance': 'Blue',
            'armor_class': 10
        }

    def handle_keydown(self, event):
        """Handle keyboard input for character creation"""
        if self.message_timer > 0:
            # Clear messages on any key press
            self.clear_messages()
            return

        # FIX: Handle name step input more intuitively
        if self.steps[self.step] == "name":
            self.handle_name_input(event)
        elif self.input_active:
            self.handle_text_input(event)
        else:
            self.handle_navigation(event)

    def handle_name_input(self, event):
        """Handle name input specifically - FIXED VERSION"""
        # Debug: Print what key was pressed
        print(f"Name input - Key: {event.key}, Unicode: '{event.unicode}', Printable: {event.unicode.isprintable() if hasattr(event, 'unicode') else 'No unicode'}")

        if event.key == pygame.K_RETURN:
            # Process name when Enter is pressed
            self.process_name_input()
        elif event.key == pygame.K_BACKSPACE:
            # Always allow backspace
            if len(self.input_text) > 0:
                self.input_text = self.input_text[:-1]
                print(f"Backspace - new text: '{self.input_text}'")
        elif event.key == pygame.K_ESCAPE:
            # Escape goes back instead of clearing (more intuitive)
            self.go_back()
        elif event.key == pygame.K_TAB:
            # Tab can toggle input focus if needed
            self.input_active = not self.input_active
        else:
            # Allow typing immediately without needing to "activate" input
            if hasattr(event, 'unicode') and event.unicode.isprintable() and len(self.input_text) < 20:
                self.input_text += event.unicode
                self.input_active = True  # Ensure input is active when typing
                print(f"Added '{event.unicode}' - new text: '{self.input_text}'")

    def handle_text_input(self, event):
        """Handle text input for other steps (kept for compatibility)"""
        if event.key == pygame.K_RETURN:
            self.input_active = False
        elif event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
        elif event.key == pygame.K_ESCAPE:
            self.input_active = False
            self.input_text = ""
        else:
            if event.unicode.isprintable() and len(self.input_text) < 20:
                self.input_text += event.unicode

    def handle_navigation(self, event):
        """Handle navigation input"""
        current_step = self.steps[self.step]

        if event.key == pygame.K_UP:
            self.selected_option = max(0, self.selected_option - 1)
        elif event.key == pygame.K_DOWN:
            max_options = self.get_max_options()
            self.selected_option = min(max_options - 1, self.selected_option + 1)
        elif event.key == pygame.K_LEFT:
            if current_step == "stats":
                self.decrease_stat()
        elif event.key == pygame.K_RIGHT:
            if current_step == "stats":
                self.increase_stat()
        elif event.key == pygame.K_RETURN:
            self.select_option()
        elif event.key == pygame.K_ESCAPE:
            self.go_back()

    def handle_click(self, pos):
        """Handle mouse clicks"""
        # Convert to character creation specific click handling
        # For now, just clear messages
        if self.message_timer > 0:
            self.clear_messages()

    def update(self, dt):
        """Update character creation form"""
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.clear_messages()

    def render(self, screen):
        """Render character creation form"""
        screen.fill(self.colors['MENU_BG'])

        # Title
        title_text = "Create New Character"
        title_surface = self.fonts['title'].render(title_text, True, self.colors['MENU_TEXT'])
        title_rect = title_surface.get_rect(center=(400, 50))
        screen.blit(title_surface, title_rect)

        # Step indicator
        step_text = f"Step {self.step + 1} of {len(self.steps)}: {self.steps[self.step].title()}"
        step_surface = self.fonts['normal'].render(step_text, True, self.colors['GOLD'])
        step_rect = step_surface.get_rect(center=(400, 90))
        screen.blit(step_surface, step_rect)

        # Render current step
        current_step = self.steps[self.step]
        if current_step == "name":
            self.render_name_step(screen)
        elif current_step == "race":
            self.render_race_step(screen)
        elif current_step == "class":
            self.render_class_step(screen)
        elif current_step == "stats":
            self.render_stats_step(screen)
        elif current_step == "appearance":
            self.render_appearance_step(screen)
        elif current_step == "confirm":
            self.render_confirm_step(screen)

        # Navigation instructions
        self.render_instructions(screen)

        # Messages
        self.render_messages(screen)

    def render_name_step(self, screen):
        """Render name input step - FIXED VERSION"""
        # Instructions
        instruction_text = "Enter your character's name:"
        instruction_surface = self.fonts['normal'].render(instruction_text, True, self.colors['MENU_TEXT'])
        screen.blit(instruction_surface, (200, 150))

        # FIX: Show current input text, or placeholder if empty
        display_text = self.input_text if self.input_text else "Type your name here..."
        text_color = self.colors['WHITE'] if self.input_text else self.colors['GRAY']
        name_surface = self.fonts['large'].render(display_text, True, text_color)

        # Input box - always show as active for name step
        input_rect = pygame.Rect(200, 190, 400, 40)
        border_color = self.colors['MENU_SELECTED'] if self.input_text else self.colors['WHITE']
        pygame.draw.rect(screen, border_color, input_rect, 2)
        screen.blit(name_surface, (210, 200))

        # Cursor - show when actively typing or when field is focused
        if self.input_text and int(time.time() * 2) % 2:
            cursor_x = 210 + name_surface.get_width()
            pygame.draw.line(screen, self.colors['WHITE'], (cursor_x, 195), (cursor_x, 225), 2)

        # FIX: Better instructions
        if not self.input_text:
            start_instruction = "Start typing to enter your character's name"
            start_surface = self.fonts['small'].render(start_instruction, True, self.colors['GRAY'])
            screen.blit(start_surface, (200, 240))
        else:
            continue_instruction = "Press Enter to continue"
            continue_surface = self.fonts['small'].render(continue_instruction, True, self.colors['GOLD'])
            screen.blit(continue_surface, (200, 240))

    def render_race_step(self, screen):
        """Render race selection step"""
        instruction_text = "Choose your character's race:"
        instruction_surface = self.fonts['normal'].render(instruction_text, True, self.colors['MENU_TEXT'])
        screen.blit(instruction_surface, (200, 150))

        # Race options
        for i, race in enumerate(self.races):
            y_pos = 200 + i * 40
            color = self.colors['MENU_SELECTED'] if i == self.selected_option else self.colors['MENU_TEXT']

            race_surface = self.fonts['normal'].render(race, True, color)
            screen.blit(race_surface, (220, y_pos))

            # Race bonus info
            bonuses = self.race_bonuses[race]
            bonus_text = ", ".join([f"+{v} {k.title()}" for k, v in bonuses.items()])
            bonus_surface = self.fonts['small'].render(f"({bonus_text})", True, self.colors['GRAY'])
            screen.blit(bonus_surface, (320, y_pos + 5))

            # Selection indicator
            if i == self.selected_option:
                pygame.draw.rect(screen, self.colors['MENU_ACCENT'], (200, y_pos - 5, 450, 35), 2)

    def render_class_step(self, screen):
        """Render class selection step"""
        instruction_text = "Choose your character's class:"
        instruction_surface = self.fonts['normal'].render(instruction_text, True, self.colors['MENU_TEXT'])
        screen.blit(instruction_surface, (200, 150))

        # Class options
        for i, char_class in enumerate(self.classes):
            y_pos = 200 + i * 40
            color = self.colors['MENU_SELECTED'] if i == self.selected_option else self.colors['MENU_TEXT']

            class_surface = self.fonts['normal'].render(char_class, True, color)
            screen.blit(class_surface, (220, y_pos))

            # Class bonus info
            bonuses = self.class_bonuses[char_class]
            bonus_text = ", ".join([f"+{v} {k.title()}" for k, v in bonuses.items()])
            bonus_surface = self.fonts['small'].render(f"({bonus_text})", True, self.colors['GRAY'])
            screen.blit(bonus_surface, (320, y_pos + 5))

            # Selection indicator
            if i == self.selected_option:
                pygame.draw.rect(screen, self.colors['MENU_ACCENT'], (200, y_pos - 5, 450, 35), 2)

    def render_stats_step(self, screen):
        """Render stat allocation step"""
        instruction_text = f"Allocate your ability scores (Points remaining: {self.available_points}):"
        instruction_surface = self.fonts['normal'].render(instruction_text, True, self.colors['MENU_TEXT'])
        screen.blit(instruction_surface, (150, 150))

        controls_text = "Use Up/Down to select, Left/Right to adjust"
        controls_surface = self.fonts['small'].render(controls_text, True, self.colors['GRAY'])
        screen.blit(controls_surface, (150, 175))

        # Stat options
        stats = list(self.character_data['stats'].keys())
        for i, stat in enumerate(stats):
            y_pos = 210 + i * 35
            color = self.colors['MENU_SELECTED'] if i == self.selected_option else self.colors['MENU_TEXT']

            # Stat name
            stat_name = stat.replace('_', ' ').title()
            stat_surface = self.fonts['normal'].render(stat_name, True, color)
            screen.blit(stat_surface, (200, y_pos))

            # Current value
            current_value = self.character_data['stats'][stat]
            value_surface = self.fonts['normal'].render(str(current_value), True, color)
            screen.blit(value_surface, (350, y_pos))

            # Adjustment buttons
            decrease_color = self.colors['RED'] if current_value > self.min_stat else self.colors['DARK_GRAY']
            increase_color = self.colors['GREEN'] if current_value < self.max_stat and self.available_points > 0 else self.colors['DARK_GRAY']

            decrease_surface = self.fonts['normal'].render("[-]", True, decrease_color)
            increase_surface = self.fonts['normal'].render("[+]", True, increase_color)
            screen.blit(decrease_surface, (400, y_pos))
            screen.blit(increase_surface, (450, y_pos))

            # Selection indicator
            if i == self.selected_option:
                pygame.draw.rect(screen, self.colors['MENU_ACCENT'], (180, y_pos - 5, 320, 30), 2)

        # Total points info
        total_points = sum(self.character_data['stats'].values())
        total_text = f"Total ability points: {total_points}"
        total_surface = self.fonts['small'].render(total_text, True, self.colors['GRAY'])
        screen.blit(total_surface, (200, 420))

    def render_appearance_step(self, screen):
        """Render appearance selection step"""
        instruction_text = "Choose your character's appearance color:"
        instruction_surface = self.fonts['normal'].render(instruction_text, True, self.colors['MENU_TEXT'])
        screen.blit(instruction_surface, (200, 150))

        # Appearance options
        for i, appearance in enumerate(self.appearances):
            y_pos = 200 + i * 40
            color = self.colors['MENU_SELECTED'] if i == self.selected_option else self.colors['MENU_TEXT']

            # Color name
            appearance_surface = self.fonts['normal'].render(appearance, True, color)
            screen.blit(appearance_surface, (220, y_pos))

            # Color preview circle
            preview_color = getattr(self.colors, appearance.upper(), self.colors['WHITE'])
            pygame.draw.circle(screen, preview_color, (400, y_pos + 15), 15)
            pygame.draw.circle(screen, self.colors['WHITE'], (400, y_pos + 15), 15, 2)

            # Selection indicator
            if i == self.selected_option:
                pygame.draw.rect(screen, self.colors['MENU_ACCENT'], (200, y_pos - 5, 250, 35), 2)

    def render_confirm_step(self, screen):
        """Render confirmation step"""
        instruction_text = "Review your character:"
        instruction_surface = self.fonts['normal'].render(instruction_text, True, self.colors['MENU_TEXT'])
        screen.blit(instruction_surface, (200, 150))

        y_offset = 190

        # Character summary
        summary_items = [
            f"Name: {self.character_data['Name']}",
            f"Race: {self.character_data['race']}",
            f"Class: {self.character_data['class']}",
            f"Appearance: {self.character_data['appearance']}",
            "",
            "Ability Scores:"
        ]

        for item in summary_items:
            if item:
                summary_surface = self.fonts['normal'].render(item, True, self.colors['MENU_TEXT'])
                screen.blit(summary_surface, (220, y_offset))
            y_offset += 25

        # Stats
        for stat, value in self.character_data['stats'].items():
            stat_text = f"  {stat.replace('_', ' ').title()}: {value}"
            stat_surface = self.fonts['small'].render(stat_text, True, self.colors['GRAY'])
            screen.blit(stat_surface, (240, y_offset))
            y_offset += 20

        # Confirmation options
        y_offset += 20
        options = ["Create Character", "Go Back"]
        for i, option in enumerate(options):
            color = self.colors['MENU_SELECTED'] if i == self.selected_option else self.colors['MENU_TEXT']
            option_surface = self.fonts['normal'].render(option, True, color)
            screen.blit(option_surface, (220, y_offset + i * 40))

            if i == self.selected_option:
                pygame.draw.rect(screen, self.colors['MENU_ACCENT'], (200, y_offset + i * 40 - 5, 200, 35), 2)

    def render_instructions(self, screen):
        """Render navigation instructions"""
        instructions = []
        current_step = self.steps[self.step]

        if current_step == "name":
            # FIX: Updated instructions for name step
            instructions = ["Type to enter name", "Enter: Continue", "Escape: Go back"]
        elif current_step == "stats":
            instructions = ["↑↓: Select stat", "←→: Adjust value", "Enter: Continue", "Escape: Go back"]
        else:
            instructions = ["↑↓: Navigate", "Enter: Select", "Escape: Go back"]

        y_start = 520
        for i, instruction in enumerate(instructions):
            instruction_surface = self.fonts['small'].render(instruction, True, self.colors['GRAY'])
            screen.blit(instruction_surface, (50, y_start + i * 20))

    def render_messages(self, screen):
        """Render error/success messages"""
        if self.error_message:
            error_surface = self.fonts['normal'].render(self.error_message, True, self.colors['RED'])
            error_rect = error_surface.get_rect(center=(400, 100))
            # Background for better visibility
            bg_rect = error_rect.inflate(20, 10)
            pygame.draw.rect(screen, self.colors['BLACK'], bg_rect)
            pygame.draw.rect(screen, self.colors['RED'], bg_rect, 2)
            screen.blit(error_surface, error_rect)

        if self.success_message:
            success_surface = self.fonts['normal'].render(self.success_message, True, self.colors['GREEN'])
            success_rect = success_surface.get_rect(center=(400, 100))
            # Background for better visibility
            bg_rect = success_rect.inflate(20, 10)
            pygame.draw.rect(screen, self.colors['BLACK'], bg_rect)
            pygame.draw.rect(screen, self.colors['GREEN'], bg_rect, 2)
            screen.blit(success_surface, success_rect)

    def get_max_options(self) -> int:
        """Get maximum options for current step"""
        current_step = self.steps[self.step]
        if current_step == "race":
            return len(self.races)
        elif current_step == "class":
            return len(self.classes)
        elif current_step == "stats":
            return len(self.character_data['stats'])
        elif current_step == "appearance":
            return len(self.appearances)
        elif current_step == "confirm":
            return 2  # Create Character, Go Back
        return 1

    def select_option(self):
        """Handle option selection - UPDATED"""
        current_step = self.steps[self.step]

        if current_step == "name":
            # FIX: Name step now just processes the input directly
            self.process_name_input()
        elif current_step == "race":
            self.character_data['race'] = self.races[self.selected_option]
            self.apply_race_bonuses()
            self.next_step()
        elif current_step == "class":
            self.character_data['class'] = self.classes[self.selected_option]
            self.apply_class_bonuses()
            self.next_step()
        elif current_step == "stats":
            # Stats are adjusted with left/right arrows, enter continues
            if self.available_points == 0 or self.confirm_stats():
                self.finalize_stats()
                self.next_step()
        elif current_step == "appearance":
            self.character_data['appearance'] = self.appearances[self.selected_option]
            self.next_step()
        elif current_step == "confirm":
            if self.selected_option == 0:  # Create Character
                self.create_character()
            else:  # Go Back
                self.go_back()

    def process_name_input(self):
        """Process name input - IMPROVED"""
        name = self.input_text.strip()
        if not name:
            self.show_error("Name cannot be empty!")
            return

        if len(name) < 2:
            self.show_error("Name must be at least 2 characters!")
            return

        if len(name) > 20:
            self.show_error("Name cannot exceed 20 characters!")
            return

        # Check for valid characters
        if not all(c.isalnum() or c.isspace() or c in "'-" for c in name):
            self.show_error("Name contains invalid characters!")
            return

        self.character_data['Name'] = name
        # FIX: Don't clear input_text, but deactivate input for other steps
        self.input_active = False
        self.next_step()

    def increase_stat(self):
        """Increase selected stat"""
        if self.available_points <= 0:
            return

        stats = list(self.character_data['stats'].keys())
        current_stat = stats[self.selected_option]
        current_value = self.character_data['stats'][current_stat]

        if current_value < self.max_stat:
            self.character_data['stats'][current_stat] += 1
            self.available_points -= 1

    def decrease_stat(self):
        """Decrease selected stat"""
        stats = list(self.character_data['stats'].keys())
        current_stat = stats[self.selected_option]
        current_value = self.character_data['stats'][current_stat]

        if current_value > self.min_stat:
            self.character_data['stats'][current_stat] -= 1
            self.available_points += 1

    def apply_race_bonuses(self):
        """Apply racial bonuses to stats"""
        race = self.character_data['race']
        if race in self.race_bonuses:
            bonuses = self.race_bonuses[race]
            for stat, bonus in bonuses.items():
                self.character_data['stats'][stat] += bonus

    def apply_class_bonuses(self):
        """Apply class bonuses to stats"""
        char_class = self.character_data['class']
        if char_class in self.class_bonuses:
            bonuses = self.class_bonuses[char_class]
            for stat, bonus in bonuses.items():
                self.character_data['stats'][stat] += bonus

    def confirm_stats(self) -> bool:
        """Confirm if player wants to continue with remaining points"""
        return self.available_points <= 5  # Allow continuing with some points unspent

    def finalize_stats(self):
        """Finalize character stats and calculate derived values"""
        stats = self.character_data['stats']

        # Calculate derived values
        constitution = stats['constitution']
        intelligence = stats['intelligence']

        # Hit points based on constitution and class
        con_bonus = (constitution - 10) // 2
        class_hp_bonus = {
            'Warrior': 10, 'Cleric': 8, 'Ranger': 8,
            'Rogue': 6, 'Wizard': 4, 'Sorcerer': 4
        }

        base_hp = 100 + con_bonus * 5
        class_bonus = class_hp_bonus.get(self.character_data['class'], 6)
        self.character_data['hit_points'] = base_hp + class_bonus
        self.character_data['max_hit_points'] = self.character_data['hit_points']

        # Mana points based on intelligence and class
        int_bonus = (intelligence - 10) // 2
        class_mana_bonus = {
            'Wizard': 30, 'Sorcerer': 25, 'Cleric': 20,
            'Ranger': 10, 'Warrior': 5, 'Rogue': 5
        }

        base_mana = 50 + int_bonus * 5
        mana_bonus = class_mana_bonus.get(self.character_data['class'], 10)
        self.character_data['mana_level'] = base_mana + mana_bonus
        self.character_data['max_mana'] = self.character_data['mana_level']

        # Armor class based on dexterity
        dex_bonus = (stats['dexterity'] - 10) // 2
        self.character_data['armor_class'] = 10 + dex_bonus

        # Starting gold based on class
        class_gold = {
            'Warrior': 150, 'Cleric': 120, 'Ranger': 130,
            'Rogue': 140, 'Wizard': 100, 'Sorcerer': 110
        }
        self.character_data['gold'] = class_gold.get(self.character_data['class'], 100)

    def next_step(self):
        """Move to next step"""
        self.step += 1
        self.selected_option = 0
        self.clear_messages()

        # FIX: Reset input state for non-name steps
        if self.step < len(self.steps) and self.steps[self.step] != "name":
            self.input_active = False
        elif self.step < len(self.steps) and self.steps[self.step] == "name":
            self.input_active = True

    def go_back(self):
        """Go back to previous step or exit"""
        if self.step > 0:
            self.step -= 1
            self.selected_option = 0
            self.clear_messages()

            # FIX: Reactivate input if going back to name step
            if self.step < len(self.steps) and self.steps[self.step] == "name":
                self.input_active = True
            else:
                self.input_active = False
        else:
            # Exit character creation - this should be handled by parent
            pass

    def create_character(self):
        """Create and save the character"""
        # Validate character data
        if not self.character_data['Name']:
            self.show_error("Character name is required!")
            return

        if not self.character_data['race']:
            self.show_error("Race selection is required!")
            return

        if not self.character_data['class']:
            self.show_error("Class selection is required!")
            return

        # Save character to server
        success, data = self.network_manager.save_character(self.character_data)

        if success:
            character_id = data.get('character_id')
            self.show_success(f"Character '{self.character_data['Name']}' created successfully!")
            # Character creation complete - parent should handle state change
            return True
        else:
            self.show_error(f"Failed to create character: {data}")
            return False

    def show_error(self, message: str):
        """Show error message"""
        self.error_message = message
        self.success_message = ""
        self.message_timer = 3.0

    def show_success(self, message: str):
        """Show success message"""
        self.success_message = message
        self.error_message = ""
        self.message_timer = 3.0

    def clear_messages(self):
        """Clear all messages"""
        self.error_message = ""
        self.success_message = ""
        self.message_timer = 0

    def is_complete(self) -> bool:
        """Check if character creation is complete"""
        return self.success_message and "created successfully" in self.success_message

    def get_character_data(self) -> Dict:
        """Get the created character data"""
        return self.character_data.copy()