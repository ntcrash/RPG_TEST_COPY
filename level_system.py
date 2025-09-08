import pygame
import json
import os
import random
from ui_components import *


class WorldLevel:
    """Represents a world level with specific properties"""

    def __init__(self, world, level, name, description, recommended_level=1,
                 enemy_multiplier=1.0, loot_multiplier=1.0, special_features=None):
        self.world = world
        self.level = level
        self.name = name
        self.description = description
        self.recommended_level = recommended_level
        self.enemy_multiplier = enemy_multiplier
        self.loot_multiplier = loot_multiplier
        self.special_features = special_features or []
        self.is_unlocked = False

    def get_display_name(self):
        return f"World {self.world}-{self.level}: {self.name}"

    def get_difficulty_description(self):
        if self.enemy_multiplier <= 1.2:
            return "Easy"
        elif self.enemy_multiplier <= 1.8:
            return "Normal"
        elif self.enemy_multiplier <= 2.5:
            return "Hard"
        elif self.enemy_multiplier <= 3.5:
            return "Expert"
        else:
            return "Nightmare"


class LevelManager:
    """Manages world levels and progression"""

    def __init__(self, character_name=None):
        self.current_world = 1
        self.current_level = 1
        self.levels = {}
        self.unlocked_levels = set()
        self.character_name = character_name

        # Make progression file character-specific
        # Ensure Characters directory exists
        os.makedirs("SaveProgression", exist_ok=True)
        if character_name:
            self.progression_file = f"SaveProgression/progression_{character_name.replace(' ', '_').replace('.json', '')}.json"
        else:
            self.progression_file = "SaveProgression/progression_default.json"

        self.initialize_levels()
        self.load_progression()

    def set_character(self, character_name):
        """Update character name and reload progression for character-specific progress"""
        if character_name != self.character_name:
            self.character_name = character_name
            if character_name:
                self.progression_file = f"SaveProgression/progression_{character_name.replace(' ', '_').replace('.json', '')}.json"
            else:
                self.progression_file = "SaveProgression/progression_default.json"

            # Reset and reload progression for the new character
            self.current_world = 1
            self.current_level = 1
            self.unlocked_levels = set()
            self.load_progression()

    def initialize_levels(self):
        """Initialize all available levels"""
        level_data = [
            # World 1 - Tutorial/Beginner Area
            (1, 1, "Green Fields", "Peaceful grasslands perfect for beginners", 1, 1.0, 1.0, ["tutorial"]),
            (1, 2, "Dark Woods", "Mysterious forest with stronger enemies", 3, 1.3, 1.2, ["dense_trees"]),
            (
                1, 3, "Ancient Ruins", "Old structures hiding dangerous secrets", 5, 1.6, 1.4,
                ["ruins", "treasure_bonus"]),
            (1, 4, "Dragon's Lair", "The lair of an ancient fire dragon", 8, 2.0, 1.8, ["boss_level", "fire_theme"]),

            # World 2 - Ice Kingdom
            (2, 1, "Frozen Tundra", "Vast icy plains with ice creatures", 6, 1.4, 1.3, ["ice_theme", "slow_effect"]),
            (2, 2, "Crystal Caverns", "Underground caves filled with ice crystals", 8, 1.7, 1.5,
             ["crystal_bonus", "echo_chamber"]),
            (2, 3, "Frost Citadel", "Ancient fortress of ice and snow", 10, 2.1, 1.7, ["fortress", "ice_traps"]),
            (2, 4, "Glacier Throne", "Domain of the Ice King", 12, 2.5, 2.0, ["boss_level", "ice_storm"]),

            # World 3 - Shadow Realm
            (3, 1, "Shadow Forest", "Dark woodland where shadows come alive", 10, 1.8, 1.6,
             ["shadow_theme", "stealth_enemies"]),
            (3, 2, "Void Caverns", "Caves that exist between reality and nightmare", 12, 2.2, 1.8,
             ["void_effects", "teleporters"]),
            (3, 3, "Nightmare Citadel", "Fortress of pure darkness", 15, 2.8, 2.2, ["nightmare_mode", "illusions"]),
            (3, 4, "Shadow Emperor's Throne", "Final battle against the Shadow Emperor", 18, 3.5, 2.8,
             ["boss_level", "shadow_mastery"]),

            # World 4 - Elemental Chaos
            (4, 1, "Elemental Crossroads", "Where all elements collide", 15, 2.0, 1.9,
             ["multi_element", "chaos_effects"]),
            (4, 2, "Storm Peaks", "Mountains wreathed in eternal lightning", 17, 2.4, 2.1,
             ["lightning_theme", "storm_effects"]),
            (4, 3, "Molten Core", "The heart of a volcanic world", 20, 2.9, 2.5, ["fire_theme", "lava_damage"]),
            (4, 4, "Primordial Chaos", "Where the first magic was born", 25, 4.0, 3.5, ["boss_level", "chaos_mastery"]),

            # World 5 - Endgame Content
            (5, 1, "Astral Plains", "Realm between worlds", 22, 2.8, 2.4, ["astral_theme", "time_effects"]),
            (5, 2, "Dimensional Rift", "Tear in the fabric of reality", 25, 3.2, 2.8,
             ["dimension_shift", "reality_warping"]),
            (5, 3, "Cosmic Battlefield", "Where gods once fought", 30, 3.8, 3.2, ["cosmic_theme", "divine_enemies"]),
            (5, 4, "The Nexus", "Center of all magical power", 35, 5.0, 4.0, ["boss_level", "ultimate_challenge"]),
        ]

        for world, level, name, desc, rec_level, enemy_mult, loot_mult, features in level_data:
            level_key = f"{world}-{level}"
            self.levels[level_key] = WorldLevel(world, level, name, desc, rec_level,
                                                enemy_mult, loot_mult, features)

        # Always unlock the first level
        self.unlocked_levels.add("1-1")

    def load_progression(self):
        """Load player progression from file"""
        try:
            if os.path.exists(self.progression_file):
                with open(self.progression_file, 'r') as f:
                    data = json.load(f)
                    self.current_world = data.get("current_world", 1)
                    self.current_level = data.get("current_level", 1)
                    self.unlocked_levels = set(data.get("unlocked_levels", ["1-1"]))
        except Exception as e:
            print(f"Error loading progression: {e}")
            # Reset to defaults
            self.current_world = 1
            self.current_level = 1
            self.unlocked_levels = {"1-1"}

    def save_progression(self):
        """Save player progression to file"""
        try:
            data = {
                "current_world": self.current_world,
                "current_level": self.current_level,
                "unlocked_levels": list(self.unlocked_levels)
            }
            with open(self.progression_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving progression: {e}")

    def get_current_level_key(self):
        """Get current level as key string"""
        return f"{self.current_world}-{self.current_level}"

    def get_current_level(self):
        """Get current WorldLevel object"""
        key = self.get_current_level_key()
        return self.levels.get(key)

    def set_current_level(self, world, level):
        """Set current level and save progression"""
        level_key = f"{world}-{level}"
        if level_key in self.levels and level_key in self.unlocked_levels:
            self.current_world = world
            self.current_level = level
            self.save_progression()
            return True
        return False

    def unlock_level(self, world, level):
        """Unlock a specific level"""
        level_key = f"{world}-{level}"
        if level_key in self.levels:
            self.unlocked_levels.add(level_key)
            self.save_progression()
            return True
        return False

    def complete_current_level(self):
        """Mark current level as complete and unlock next level"""
        current_key = self.get_current_level_key()
        current = self.get_current_level()

        if not current:
            return False

        # Unlock next level in same world
        next_level_key = f"{current.world}-{current.level + 1}"
        if next_level_key in self.levels:
            self.unlock_level(current.world, current.level + 1)

        # If this was the last level of a world, unlock first level of next world
        if current.level == 4:  # Assuming 4 levels per world
            next_world_key = f"{current.world + 1}-1"
            if next_world_key in self.levels:
                self.unlock_level(current.world + 1, 1)

        return True

    def get_unlocked_levels(self):
        """Get list of unlocked WorldLevel objects"""
        unlocked = []
        for level_key in sorted(self.unlocked_levels):
            if level_key in self.levels:
                level = self.levels[level_key]
                level.is_unlocked = True
                unlocked.append(level)
        return unlocked

    def get_all_levels_by_world(self):
        """Get all levels organized by world"""
        worlds = {}
        for level_key, level in self.levels.items():
            world = level.world
            if world not in worlds:
                worlds[world] = []
            level.is_unlocked = level_key in self.unlocked_levels
            worlds[world].append(level)

        # Sort levels within each world
        for world in worlds:
            worlds[world].sort(key=lambda x: x.level)

        return worlds


class WorldLevelGenerator:
    """Generates world content based on level properties"""

    def __init__(self, level_manager):
        self.level_manager = level_manager

    def generate_level_content(self, world_level):
        """Generate specific content for a world level"""
        content = {
            "enemy_count": self._calculate_enemy_count(world_level),
            "enemy_types": self._get_enemy_types(world_level),
            "treasure_count": self._calculate_treasure_count(world_level),
            "special_objects": self._get_special_objects(world_level),
            "map_theme": self._get_map_theme(world_level),
            "background_color": self._get_background_color(world_level),
            "ambient_effects": self._get_ambient_effects(world_level)
        }
        return content

    def _calculate_enemy_count(self, world_level):
        """Calculate number of enemies for this level"""
        base_count = 6
        level_factor = (world_level.world - 1) * 4 + world_level.level
        return int(base_count + (level_factor * 2) * world_level.enemy_multiplier)

    def _calculate_treasure_count(self, world_level):
        """Calculate number of treasure objects for this level"""
        base_count = 3
        level_factor = (world_level.world - 1) * 2 + world_level.level
        return int(base_count + level_factor * world_level.loot_multiplier)

    def _get_enemy_types(self, world_level):
        """Get enemy types appropriate for this level"""
        enemy_types = ["basic"]

        if world_level.recommended_level >= 5:
            enemy_types.append("elite")
        if world_level.recommended_level >= 10:
            enemy_types.append("champion")
        if world_level.recommended_level >= 15:
            enemy_types.append("ancient")
        if "boss_level" in world_level.special_features:
            enemy_types.append("boss")

        return enemy_types

    def _get_special_objects(self, world_level):
        """Get special objects for this level"""
        objects = []

        if "treasure_bonus" in world_level.special_features:
            objects.extend(["rare_treasure", "rare_treasure"])
        if "boss_level" in world_level.special_features:
            objects.append("boss_arena")
        if "crystal_bonus" in world_level.special_features:
            objects.extend(["magic_crystal", "power_crystal"])
        if "teleporters" in world_level.special_features:
            objects.extend(["teleporter", "teleporter"])

        return objects

    def _get_map_theme(self, world_level):
        """Get map theme based on world"""
        themes = {
            1: "grassland",
            2: "ice",
            3: "shadow",
            4: "elemental",
            5: "cosmic"
        }
        return themes.get(world_level.world, "grassland")

    def _get_background_color(self, world_level):
        """Get background color for the world"""
        colors = {
            1: (34, 139, 34),  # Forest green
            2: (135, 206, 250),  # Light blue (ice)
            3: (25, 25, 55),  # Dark blue/purple (shadow)
            4: (139, 69, 19),  # Saddle brown (elemental)
            5: (75, 0, 130)  # Indigo (cosmic)
        }
        return colors.get(world_level.world, (34, 139, 34))

    def _get_ambient_effects(self, world_level):
        """Get ambient effects for the level"""
        effects = []

        if "ice_theme" in world_level.special_features:
            effects.append("snow_particles")
        if "fire_theme" in world_level.special_features:
            effects.append("ember_particles")
        if "shadow_theme" in world_level.special_features:
            effects.append("shadow_wisps")
        if "lightning_theme" in world_level.special_features:
            effects.append("lightning_flashes")
        if "cosmic_theme" in world_level.special_features:
            effects.append("star_field")

        return effects


class LevelSelectScreen:
    """Level selection interface"""

    def __init__(self, level_manager, screen_width, screen_height):
        self.level_manager = level_manager
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.selected_world = 1
        self.selected_level = 1
        self.scroll_offset = 0
        self.levels_per_page = 8

        # UI fonts
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)

        # Get unlocked levels
        self.unlocked_levels = self.level_manager.get_unlocked_levels()
        self.worlds = self.level_manager.get_all_levels_by_world()

        self.animation_timer = 0

    def handle_input(self, key):
        """Handle level selection input"""
        if key == pygame.K_ESCAPE:
            return "back"

        elif key == pygame.K_LEFT:
            # Navigate worlds
            available_worlds = list(self.worlds.keys())
            if self.selected_world in available_worlds:
                current_index = available_worlds.index(self.selected_world)
                if current_index > 0:
                    self.selected_world = available_worlds[current_index - 1]
                    self.selected_level = 1

        elif key == pygame.K_RIGHT:
            # Navigate worlds
            available_worlds = list(self.worlds.keys())
            if self.selected_world in available_worlds:
                current_index = available_worlds.index(self.selected_world)
                if current_index < len(available_worlds) - 1:
                    self.selected_world = available_worlds[current_index + 1]
                    self.selected_level = 1

        elif key == pygame.K_UP:
            if self.selected_level > 1:
                self.selected_level -= 1

        elif key == pygame.K_DOWN:
            if self.selected_world in self.worlds:
                max_level = len(self.worlds[self.selected_world])
                if self.selected_level < max_level:
                    self.selected_level += 1

        elif key == pygame.K_RETURN:
            # Select level
            level_key = f"{self.selected_world}-{self.selected_level}"
            if level_key in self.level_manager.unlocked_levels:
                if self.level_manager.set_current_level(self.selected_world, self.selected_level):
                    return "level_selected"
            else:
                return "level_locked"

        return "continue"

    def update(self):
        """Update animations"""
        self.animation_timer += 1

    def draw(self, screen):
        """Draw level selection screen"""
        screen.fill(MENU_BG)

        # Title
        title = self.title_font.render("SELECT LEVEL", True, WHITE)
        title_rect = title.get_rect(center=(self.screen_width // 2, 50))
        screen.blit(title, title_rect)

        # Current level indicator
        current_level = self.level_manager.get_current_level()
        if current_level:
            current_text = f"Current: {current_level.get_display_name()}"
            current_surface = self.small_font.render(current_text, True, MENU_SELECTED)
            current_rect = current_surface.get_rect(center=(self.screen_width // 2, 85))
            screen.blit(current_surface, current_rect)

        # World tabs
        self.draw_world_tabs(screen)

        # Level list for selected world
        self.draw_level_list(screen)

        # Instructions
        self.draw_instructions(screen)

    def draw_world_tabs(self, screen):
        """Draw world selection tabs"""
        tab_width = 120
        tab_height = 30
        start_x = (self.screen_width - (len(self.worlds) * tab_width)) // 2
        y_pos = 120

        for i, world_num in enumerate(sorted(self.worlds.keys())):
            x_pos = start_x + i * tab_width

            # Check if world has any unlocked levels
            world_unlocked = any(level.is_unlocked for level in self.worlds[world_num])

            # Tab background
            tab_rect = pygame.Rect(x_pos, y_pos, tab_width - 5, tab_height)

            if world_num == self.selected_world:
                color = MENU_SELECTED
                border_color = WHITE
                border_width = 3
            elif world_unlocked:
                color = MENU_ACCENT
                border_color = MENU_TEXT
                border_width = 1
            else:
                color = MENU_BG
                border_color = GRAY
                border_width = 1

            pygame.draw.rect(screen, color, tab_rect)
            pygame.draw.rect(screen, border_color, tab_rect, border_width)

            # Tab text
            world_name = f"World {world_num}"
            text_color = BLACK if world_num == self.selected_world else (WHITE if world_unlocked else GRAY)
            tab_text = self.small_font.render(world_name, True, text_color)
            text_rect = tab_text.get_rect(center=tab_rect.center)
            screen.blit(tab_text, text_rect)

    def draw_level_list(self, screen):
        """Draw list of levels for selected world"""
        if self.selected_world not in self.worlds:
            return

        levels = self.worlds[self.selected_world]
        start_y = 180
        level_height = 45

        for i, level in enumerate(levels):
            y_pos = start_y + i * level_height

            # Level background
            level_rect = pygame.Rect(50, y_pos, self.screen_width - 100, level_height - 5)

            is_selected = (i + 1) == self.selected_level
            is_current = (level.world == self.level_manager.current_world and
                          level.level == self.level_manager.current_level)

            if is_selected:
                # Animated selection
                pulse = int(10 * abs(math.sin(self.animation_timer * 0.15)))
                expanded_rect = level_rect.inflate(pulse, pulse // 2)
                color = MENU_HIGHLIGHT
                border_color = MENU_SELECTED
                border_width = 3
            elif is_current:
                color = MENU_ACCENT
                border_color = GOLD
                border_width = 2
            elif level.is_unlocked:
                color = UI_BG_COLOR
                border_color = MENU_TEXT
                border_width = 1
            else:
                color = (20, 20, 20)
                border_color = GRAY
                border_width = 1

            draw_rect = expanded_rect if is_selected else level_rect
            pygame.draw.rect(screen, color, draw_rect)
            pygame.draw.rect(screen, border_color, draw_rect, border_width)

            # Level info
            info_x = draw_rect.x + 10
            info_y = draw_rect.y + 5

            # Level name
            name_color = MENU_SELECTED if is_selected else (WHITE if level.is_unlocked else GRAY)
            level_name = f"{level.level}. {level.name}"
            name_surface = self.font.render(level_name, True, name_color)
            screen.blit(name_surface, (info_x, info_y))

            # Level details
            if level.is_unlocked or is_selected:
                details = f"Rec. Level: {level.recommended_level} | Difficulty: {level.get_difficulty_description()}"
                detail_color = MENU_TEXT if level.is_unlocked else GRAY
                detail_surface = self.small_font.render(details, True, detail_color)
                screen.blit(detail_surface, (info_x, info_y + 20))

                # Current level indicator
                if is_current:
                    current_indicator = self.small_font.render("CURRENT", True, GOLD)
                    screen.blit(current_indicator, (draw_rect.right - 80, info_y + 5))
            else:
                # Locked indicator
                locked_text = self.small_font.render("LOCKED", True, RED)
                screen.blit(locked_text, (info_x, info_y + 20))

    def draw_instructions(self, screen):
        """Draw control instructions"""
        instructions = [
            "← → : Navigate Worlds    ↑ ↓ : Navigate Levels",
            "ENTER: Select Level    ESC: Back to Game"
        ]

        instruction_y = self.screen_height - 60
        for instruction in instructions:
            instruction_surface = self.small_font.render(instruction, True, WHITE)
            instruction_rect = instruction_surface.get_rect(center=(self.screen_width // 2, instruction_y))
            screen.blit(instruction_surface, instruction_rect)
            instruction_y += 20