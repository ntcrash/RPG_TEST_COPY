import pygame
import random
import string
import os
import json
from ui_components import *


class CharacterCreation:
    """Character creation interface with customization options"""

    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)

        # Character data
        self.character_name = ""
        self.selected_race = 0
        self.selected_class = 0
        self.selected_aspect = 0

        # Current field being edited
        self.current_field = 0  # 0=name, 1=race, 2=class, 3=aspect, 4=reroll, 5=create

        # Available options
        self.races = [
            {"name": "Human", "desc": "Balanced stats, +2 to any one stat"},
            {"name": "Syhian", "desc": "+2 Dex, +1 Int, -1 Con"},
            {"name": "Drifter", "desc": "+2 Con, +1 Str, -1 Dex"},
            {"name": "Hatchling", "desc": "-2 Dex, -4 Cha, +3 Str, fire resistance"},
            {"name": "Necromancer", "desc": "+2 Str, +1 Con, -1 Int"},
            {"name": "Dragon", "desc": "+4 Str, +1 Cha, fire resistance"}
        ]

        self.classes = [
            {"name": "Tech Mage", "desc": "Warrior class, high HP and weapon skills"},
            {"name": "War Mage", "desc": "Magic warrior, balanced magic and combat"},
            {"name": "True Mage", "desc": "Pure magic user, high mana and spells"},
            {"name": "Warrior", "desc": "Stealthy fighter, high dex and critical hits"},
            {"name": "Paladin", "desc": "Divine magic, healing and support spells"},
            {"name": "Healer", "desc": "Nature warrior, bow skills and tracking"}
        ]

        self.aspects = [
            {"name": "Fire", "desc": "Fire magic, burn damage over time"},
            {"name": "Water", "desc": "Ice magic, slow and freeze effects"},
            {"name": "Dream", "desc": "Lightning magic, chain damage"},
            {"name": "Earth", "desc": "Earth magic, armor and shield spells"},
            {"name": "Life", "desc": "Light magic, healing and protection"},
            {"name": "Void", "desc": "Dark magic, debuffs and drain life"}
        ]

        # Character stats (rolled)
        self.base_stats = self.roll_stats()

        # Input handling
        self.cursor_timer = 0
        self.show_cursor = True

    def roll_stats(self):
        """Roll 6 stats using 4d6 drop lowest method"""
        stats = {}
        stat_names = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]

        for stat in stat_names:
            # Roll 4d6, drop lowest
            rolls = [random.randint(1, 6) for _ in range(4)]
            rolls.sort(reverse=True)
            stats[stat] = sum(rolls[:3])  # Take highest 3

        return stats

    def get_racial_bonuses(self, race_name):
        """Get stat bonuses for selected race"""
        bonuses = {
            "strength": 0, "dexterity": 0, "constitution": 0,
            "intelligence": 0, "wisdom": 0, "charisma": 0
        }

        if race_name == "Human":
            # Human gets +2 to highest stat
            highest_stat = max(self.base_stats.keys(), key=lambda k: self.base_stats[k])
            bonuses[highest_stat] = 2
        elif race_name == "Syhian":
            bonuses["dexterity"] = 2
            bonuses["intelligence"] = 1
            bonuses["constitution"] = -1
        elif race_name == "Drifter":
            bonuses["constitution"] = 2
            bonuses["strength"] = 1
            bonuses["dexterity"] = -1
        elif race_name == "Hatchling":
            bonuses["dexterity"] = 2
            bonuses["charisma"] = 1
            bonuses["strength"] = -1
        elif race_name == "Necromancer":
            bonuses["strength"] = 2
            bonuses["constitution"] = 1
            bonuses["intelligence"] = -1
        elif race_name == "Dragon":
            bonuses["strength"] = 2
            bonuses["charisma"] = 1

        return bonuses

    def get_final_stats(self):
        """Get final stats with racial bonuses applied"""
        race_name = self.races[self.selected_race]["name"]
        bonuses = self.get_racial_bonuses(race_name)

        final_stats = {}
        for stat in self.base_stats:
            final_stats[stat] = max(1, self.base_stats[stat] + bonuses[stat])

        return final_stats

    def get_starting_hp(self):
        """Calculate starting HP based on class and constitution"""
        class_hp = {
            "Tech Mage": 100,
            "War Mage": 130,
            "True Mage": 80,
            "Warrior": 140,
            "Paladin": 90,
            "Healer": 80
        }

        class_name = self.classes[self.selected_class]["name"]
        base_hp = class_hp.get(class_name, 100)

        # Constitution bonus
        con_bonus = max(0, (self.get_final_stats()["constitution"] - 10) // 2) * 5

        return base_hp + con_bonus

    def get_starting_mana(self):
        """Calculate starting mana based on class and intelligence/wisdom"""
        class_mana = {
            "Tech Mage": 30,
            "War Mage": 60,
            "True Mage": 80,
            "Warrior": 40,
            "Paladin": 70,
            "Healer": 90
        }

        class_name = self.classes[self.selected_class]["name"]
        base_mana = class_mana.get(class_name, 50)

        # Intelligence and wisdom bonuses
        final_stats = self.get_final_stats()
        int_bonus = max(0, (final_stats["intelligence"] - 10) // 2) * 3
        wis_bonus = max(0, (final_stats["wisdom"] - 10) // 2) * 2

        return base_mana + int_bonus + wis_bonus

    def handle_event(self, event):
        """Handle pygame events including text input"""
        if event.type == pygame.KEYDOWN:
            # Handle navigation and special keys first
            if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_TAB, pygame.K_LEFT, pygame.K_RIGHT,
                             pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                return self.handle_keypress(event.key)
            # Don't handle other keys here - let TEXTINPUT handle them
            return "continue"
        elif event.type == pygame.TEXTINPUT and self.current_field == 0:
            # Handle text input for name field only
            if len(self.character_name) < 20:
                # Only allow letters, spaces, apostrophes, and hyphens
                char = event.text
                if char.isalpha() or char in [" ", "'", "-"]:
                    # Auto-capitalize first letter or after space
                    if len(self.character_name) == 0 or (
                            len(self.character_name) > 0 and self.character_name[-1] == " "):
                        char = char.upper()
                    else:
                        char = char.lower()
                    self.character_name += char
            return "continue"
        return None

    def handle_keypress(self, key):
        """Handle keyboard input for character creation"""
        # Navigation keys
        if key == pygame.K_UP:
            self.current_field = (self.current_field - 1) % 6
        elif key == pygame.K_DOWN:
            self.current_field = (self.current_field + 1) % 6
        elif key == pygame.K_TAB:
            self.current_field = (self.current_field + 1) % 6

        # Field-specific actions
        elif key == pygame.K_LEFT:
            if self.current_field == 1:  # Race
                self.selected_race = (self.selected_race - 1) % len(self.races)
            elif self.current_field == 2:  # Class
                self.selected_class = (self.selected_class - 1) % len(self.classes)
            elif self.current_field == 3:  # Aspect
                self.selected_aspect = (self.selected_aspect - 1) % len(self.aspects)

        elif key == pygame.K_RIGHT:
            if self.current_field == 1:  # Race
                self.selected_race = (self.selected_race + 1) % len(self.races)
            elif self.current_field == 2:  # Class
                self.selected_class = (self.selected_class + 1) % len(self.classes)
            elif self.current_field == 3:  # Aspect
                self.selected_aspect = (self.selected_aspect + 1) % len(self.aspects)

        # Action keys
        elif key == pygame.K_RETURN:
            if self.current_field == 4:  # Re-roll stats
                self.base_stats = self.roll_stats()
                return "reroll"
            elif self.current_field == 5:  # Create character
                if self.character_name.strip():
                    return "create"
                else:
                    return "need_name"

        elif key == pygame.K_ESCAPE:
            return "cancel"

        # Simple backspace for name field
        elif self.current_field == 0 and key == pygame.K_BACKSPACE:
            self.character_name = self.character_name[:-1]

        return "continue"

    def create_character_data(self):
        """Create the character data dictionary"""
        final_stats = self.get_final_stats()
        race_name = self.races[self.selected_race]["name"]
        class_name = self.classes[self.selected_class]["name"]
        aspect_name = self.aspects[self.selected_aspect]["name"].lower()

        character_data = {
            "Name": self.character_name.strip().title(),
            "Race": race_name,
            "Type": class_name,
            "Level": 1,
            "Hit_Points": self.get_starting_hp(),
            "Credits": 1000,
            "Experience_Points": 0,
            "Aspect1": f"{aspect_name}_level_1",
            "Aspect1_Mana": self.get_starting_mana(),
            "Weapon1": "Iron Sword" if class_name in ["Warrior", "Tech Mage", "War Mage"] else "Spell Pistol",
            "Weapon2": "",
            "Weapon3": "Basic Staff" if class_name in ["True Mage", "Paladin", "Healer"] else "Spell_Blade",
            "Armor_Slot_1": "Leather Armor" if class_name == "True Mage" else "Basic Armor",
            "Armor_Slot_2": "",
            "Inventory": {},
            "strength": final_stats["strength"],
            "dexterity": final_stats["dexterity"],
            "constitution": final_stats["constitution"],
            "intelligence": final_stats["intelligence"],
            "wisdom": final_stats["wisdom"],
            "charisma": final_stats["charisma"]
        }

        return character_data

    def save_character(self):
        """Save the created character to file"""
        character_data = self.create_character_data()

        # Ensure Characters directory exists
        os.makedirs("Characters", exist_ok=True)

        # Create filename from character name
        safe_name = "".join(c for c in self.character_name if c.isalnum() or c in [" ", "-", "'"])
        safe_name = safe_name.replace(" ", "_").lower()
        filename = f"Characters/{safe_name}.json"

        # Make sure filename is unique
        counter = 1
        original_filename = filename
        while os.path.exists(filename):
            name_part = original_filename.replace(".json", "")
            filename = f"{name_part}_{counter}.json"
            counter += 1

        try:
            with open(filename, 'w') as f:
                json.dump(character_data, f, indent=4)
            return filename
        except Exception as e:
            print(f"Error saving character: {e}")
            return None

    def update(self):
        """Update animations"""
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.show_cursor = not self.show_cursor
            self.cursor_timer = 0

    def draw(self, screen):
        """Draw the character creation screen"""
        screen.fill(MENU_BG)

        # Title
        title = self.title_font.render("CREATE CHARACTER", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 40))
        screen.blit(title, title_rect)

        # Left column - Character options
        left_x = 50
        y_pos = 100

        # Name input
        name_color = MENU_SELECTED if self.current_field == 0 else WHITE
        name_label = self.font.render("Name:", True, name_color)
        screen.blit(name_label, (left_x, y_pos))

        # Name input box
        name_box = pygame.Rect(left_x + 100, y_pos - 5, 200, 30)
        box_color = MENU_SELECTED if self.current_field == 0 else MENU_TEXT
        pygame.draw.rect(screen, (20, 20, 40), name_box)
        pygame.draw.rect(screen, box_color, name_box, 2)

        # Name text with cursor
        display_name = self.character_name if self.character_name else "Enter name..."
        text_color = WHITE if self.character_name else MENU_TEXT

        if self.current_field == 0 and self.show_cursor:
            if self.character_name:
                display_name += "|"
            else:
                display_name = "|"
                text_color = WHITE

        name_surface = self.font.render(display_name, True, text_color)
        screen.blit(name_surface, (left_x + 105, y_pos))

        y_pos += 60

        # Race dropdown
        race_color = MENU_SELECTED if self.current_field == 1 else WHITE
        race_label = self.font.render("Race:", True, race_color)
        screen.blit(race_label, (left_x, y_pos))

        race_text = f"< {self.races[self.selected_race]['name']} >"
        race_surface = self.font.render(race_text, True, race_color)
        screen.blit(race_surface, (left_x + 100, y_pos))

        # Race description
        race_desc = self.small_font.render(self.races[self.selected_race]['desc'], True, MENU_TEXT)
        screen.blit(race_desc, (left_x + 100, y_pos + 25))

        y_pos += 70

        # Class dropdown
        class_color = MENU_SELECTED if self.current_field == 2 else WHITE
        class_label = self.font.render("Class:", True, class_color)
        screen.blit(class_label, (left_x, y_pos))

        class_text = f"< {self.classes[self.selected_class]['name']} >"
        class_surface = self.font.render(class_text, True, class_color)
        screen.blit(class_surface, (left_x + 100, y_pos))

        # Class description
        class_desc = self.small_font.render(self.classes[self.selected_class]['desc'], True, MENU_TEXT)
        screen.blit(class_desc, (left_x + 100, y_pos + 25))

        y_pos += 70

        # Magic Aspect dropdown
        aspect_color = MENU_SELECTED if self.current_field == 3 else WHITE
        aspect_label = self.font.render("Magic:", True, aspect_color)
        screen.blit(aspect_label, (left_x, y_pos))

        aspect_text = f"< {self.aspects[self.selected_aspect]['name']} >"
        aspect_surface = self.font.render(aspect_text, True, aspect_color)
        screen.blit(aspect_surface, (left_x + 100, y_pos))

        # Aspect description
        aspect_desc = self.small_font.render(self.aspects[self.selected_aspect]['desc'], True, MENU_TEXT)
        screen.blit(aspect_desc, (left_x + 100, y_pos + 25))

        y_pos += 80

        # Re-roll button
        reroll_color = MENU_SELECTED if self.current_field == 4 else WHITE
        reroll_text = self.font.render("🎲 Re-roll Stats", True, reroll_color)
        screen.blit(reroll_text, (left_x, y_pos))

        y_pos += 50

        # Create button
        create_color = MENU_SELECTED if self.current_field == 5 else WHITE
        create_text = self.font.render("✅ Create Character", True, create_color)
        screen.blit(create_text, (left_x, y_pos))

        # Right column - Stats and preview
        right_x = 450
        y_pos = 100

        # Stats display
        stats_title = self.font.render("ABILITY SCORES", True, MENU_SELECTED)
        screen.blit(stats_title, (right_x, y_pos))
        y_pos += 40

        final_stats = self.get_final_stats()
        racial_bonuses = self.get_racial_bonuses(self.races[self.selected_race]["name"])

        for stat_name in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            base_val = self.base_stats[stat_name]
            racial_bonus = racial_bonuses[stat_name]
            final_val = final_stats[stat_name]

            # Ability modifier
            modifier = (final_val - 10) // 2
            mod_text = f"+{modifier}" if modifier >= 0 else str(modifier)

            stat_display = f"{stat_name.title()}: {base_val}"
            if racial_bonus != 0:
                bonus_sign = "+" if racial_bonus > 0 else ""
                stat_display += f" {bonus_sign}{racial_bonus}"
            stat_display += f" = {final_val} ({mod_text})"

            color = GREEN if racial_bonus > 0 else RED if racial_bonus < 0 else WHITE
            stat_surface = self.small_font.render(stat_display, True, color)
            screen.blit(stat_surface, (right_x, y_pos))
            y_pos += 22

        y_pos += 20

        # Derived stats
        derived_title = self.font.render("DERIVED STATS", True, MENU_SELECTED)
        screen.blit(derived_title, (right_x, y_pos))
        y_pos += 30

        hp_text = f"Hit Points: {self.get_starting_hp()}"
        hp_surface = self.small_font.render(hp_text, True, WHITE)
        screen.blit(hp_surface, (right_x, y_pos))
        y_pos += 22

        mana_text = f"Mana Points: {self.get_starting_mana()}"
        mana_surface = self.small_font.render(mana_text, True, WHITE)
        screen.blit(mana_surface, (right_x, y_pos))
        y_pos += 22

        # Armor class calculation
        dex_mod = (final_stats["dexterity"] - 10) // 2
        ac = 10 + dex_mod
        ac_text = f"Armor Class: {ac} (10 + Dex)"
        ac_surface = self.small_font.render(ac_text, True, WHITE)
        screen.blit(ac_surface, (right_x, y_pos))

        # Instructions
        instructions = [
            "↑↓: Navigate fields",
            "←→: Change selections",
            "Type: Enter name when on name field",
            "ENTER: Re-roll stats or Create character",
            "ESC: Cancel and go back"
        ]

        y_pos = self.screen_height - 120
        for instruction in instructions:
            text = self.small_font.render(instruction, True, MENU_TEXT)
            screen.blit(text, (50, y_pos))
            y_pos += 18