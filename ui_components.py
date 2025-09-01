import pygame
import random
import math

# Color constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

# Enhanced UI Colors
DARK_BLUE = (25, 25, 55)
LIGHT_BLUE = (100, 150, 255)
HEALTH_BAR_COLOR = (255, 50, 50)
HEALTH_BAR_BG = (100, 0, 0)
MANA_BAR_COLOR = (50, 100, 255)
MANA_BAR_BG = (0, 0, 100)
UI_BG_COLOR = (30, 30, 30)
UI_BORDER_COLOR = (100, 100, 100)
ENEMY_HEALTH_COLOR = (255, 100, 100)
DAMAGE_TEXT_COLOR = (255, 255, 0)
HEAL_TEXT_COLOR = (0, 255, 0)

# Menu colors
MENU_BG = (15, 20, 35)
MENU_ACCENT = (45, 85, 135)
MENU_HIGHLIGHT = (65, 105, 165)
MENU_TEXT = (220, 220, 220)
MENU_SELECTED = (255, 215, 0)


class HealthManaBar:
    """Health and Mana bar display component"""

    def __init__(self, x, y, width, height, max_value, current_value, bar_color, bg_color, label=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.max_value = max_value
        self.current_value = current_value
        self.bar_color = bar_color
        self.bg_color = bg_color
        self.label = label
        self.font = pygame.font.Font(None, 24)

    def update(self, current_value, max_value=None):
        self.current_value = max(0, current_value)
        if max_value is not None:
            self.max_value = max_value

    def draw(self, screen):
        # Draw background
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height))

        # Draw fill bar
        if self.max_value > 0:
            fill_ratio = max(0, min(1, self.current_value / self.max_value))
            fill_width = int(fill_ratio * self.width)
            if fill_width > 0:
                pygame.draw.rect(screen, self.bar_color, (self.x, self.y, fill_width, self.height))

        # Draw border
        pygame.draw.rect(screen, UI_BORDER_COLOR, (self.x, self.y, self.width, self.height), 2)

        # Draw label text
        text = f"{self.label}: {int(self.current_value)}/{int(self.max_value)}"
        text_surface = self.font.render(text, True, WHITE)
        text_x = self.x + (self.width - text_surface.get_width()) // 2
        text_y = self.y + (self.height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))


class DamageText:
    """Floating damage text effect"""

    def __init__(self, x, y, text, color=DAMAGE_TEXT_COLOR):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.timer = 60
        self.font = pygame.font.Font(None, 28)
        self.alpha = 255
        self.world_pos = None  # For world coordinate tracking

    def update(self):
        self.timer -= 1
        self.y -= 2
        self.alpha = max(0, int(255 * (self.timer / 60)))
        return self.timer > 0

    def draw(self, screen):
        text_surface = self.font.render(self.text, True, self.color)
        text_surface.set_alpha(self.alpha)
        screen.blit(text_surface, (self.x, self.y))

    def draw_at_world_pos(self, screen, camera):
        """Draw damage text at world position using camera"""
        if self.world_pos:
            screen_x, screen_y = camera.world_to_screen(self.world_pos[0], self.world_pos[1])
            screen_y -= (60 - self.timer) * 2  # Float upward
            text_surface = self.font.render(self.text, True, self.color)
            text_surface.set_alpha(self.alpha)
            screen.blit(text_surface, (screen_x, screen_y))
        else:
            self.draw(screen)


class ParticleSystem:
    """Particle effect system for visual enhancement"""

    def __init__(self):
        self.particles = []

    def add_particle(self, x, y, color=(255, 255, 255)):
        self.particles.append({
            'x': x, 'y': y, 'vx': random.uniform(-2, 2), 'vy': random.uniform(-3, -1),
            'life': 30, 'color': color, 'size': random.randint(2, 4)
        })

    def update(self):
        for particle in self.particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['life'] -= 1
            particle['size'] = max(1, particle['size'] - 0.1)
            if particle['life'] <= 0:
                self.particles.remove(particle)

    def draw(self, screen):
        for particle in self.particles:
            pygame.draw.circle(screen, particle['color'],
                               (int(particle['x']), int(particle['y'])), int(particle['size']))


class RestArea:
    """Rest area for healing and mana restoration"""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 60
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.rest_cost = 75

    def draw(self, screen, camera_x=0, camera_y=0):
        # Adjust position for camera
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        # Only draw if visible
        if (-self.width < screen_x < screen.get_width() and
                -self.height < screen_y < screen.get_height()):
            draw_rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
            pygame.draw.rect(screen, (0, 100, 200), draw_rect)
            pygame.draw.rect(screen, WHITE, draw_rect, 3)

            # Draw tent shape
            tent_points = [
                (screen_x + 30, screen_y + 10),
                (screen_x + 10, screen_y + 50),
                (screen_x + 50, screen_y + 50)
            ]
            pygame.draw.polygon(screen, (150, 200, 255), tent_points)
            pygame.draw.polygon(screen, BLACK, tent_points, 2)

            # Rest label
            rest_font = pygame.font.Font(None, 16)
            text = rest_font.render("REST", True, WHITE)
            text_rect = text.get_rect(center=(screen_x + 30, screen_y - 10))
            screen.blit(text, text_rect)


class UIRenderer:
    """Handles drawing of UI elements and menus"""

    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Load fonts
        try:
            self.title_font = pygame.font.Font(None, 64)
            self.large_font = pygame.font.Font(None, 48)
            self.font = pygame.font.Font(None, 28)
            self.small_font = pygame.font.Font(None, 20)
        except:
            self.title_font = pygame.font.Font(None, 64)
            self.large_font = pygame.font.Font(None, 48)
            self.font = pygame.font.Font(None, 28)
            self.small_font = pygame.font.Font(None, 20)

    def draw_gradient_rect(self, surface, color1, color2, rect):
        """Draw a rectangle with gradient effect"""
        for y in range(rect.height):
            ratio = y / rect.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            pygame.draw.line(surface, (r, g, b),
                             (rect.x, rect.y + y), (rect.x + rect.width, rect.y + y))

    def draw_enhanced_menu(self, screen, title, options, selected_index, subtitle="", animation_timer=0):
        """Draw enhanced menu with animations"""
        screen.fill(MENU_BG)

        # Title background
        title_bg = pygame.Rect(0, 50, self.width, 100)
        self.draw_gradient_rect(screen, MENU_ACCENT, MENU_HIGHLIGHT, title_bg)

        # Title
        title_surface = self.large_font.render(title, True, WHITE)
        title_rect = title_surface.get_rect(center=(self.width // 2, 100))
        screen.blit(title_surface, title_rect)

        # Subtitle
        if subtitle:
            subtitle_surface = self.font.render(subtitle, True, MENU_TEXT)
            subtitle_rect = subtitle_surface.get_rect(center=(self.width // 2, 130))
            screen.blit(subtitle_surface, subtitle_rect)

        # Menu options
        start_y = 200
        option_height = 50

        for i, option in enumerate(options):
            y_pos = start_y + i * option_height

            # Option background
            option_rect = pygame.Rect(self.width // 4, y_pos - 15, self.width // 2, 40)

            if i == selected_index:
                # Animated selection
                pulse = int(10 * abs(math.sin(animation_timer * 0.15)))
                expanded_rect = option_rect.inflate(pulse, pulse // 2)
                self.draw_gradient_rect(screen, MENU_HIGHLIGHT, MENU_ACCENT, expanded_rect)
                pygame.draw.rect(screen, MENU_SELECTED, expanded_rect, 3)
                color = MENU_SELECTED
            else:
                self.draw_gradient_rect(screen, MENU_ACCENT, MENU_BG, option_rect)
                pygame.draw.rect(screen, MENU_TEXT, option_rect, 1)
                color = MENU_TEXT

            # Option text
            display_name = option.replace(".json", "").replace("_", " ").title()
            text_surface = self.font.render(display_name, True, color)
            text_rect = text_surface.get_rect(center=(self.width // 2, y_pos))
            screen.blit(text_surface, text_rect)

    def draw_ui_overlay(self, screen, player_data):
        """Draw UI overlay with player stats"""
        if not player_data:
            return

        # UI panel background
        ui_panel = pygame.Rect(10, 10, 350, 120)
        pygame.draw.rect(screen, UI_BG_COLOR, ui_panel)
        pygame.draw.rect(screen, UI_BORDER_COLOR, ui_panel, 2)

        # Player info
        name = player_data.get("Name", "Unknown")
        level = player_data.get("Level", 1)
        hp = player_data.get("Hit_Points", 100)
        credits = player_data.get("Credits", 0)

        info_lines = [
            f"Name: {name}",
            f"Level: {level}",
            f"HP: {hp}",
            f"Credits: {credits}"
        ]

        for i, line in enumerate(info_lines):
            text_surface = self.small_font.render(line, True, WHITE)
            screen.blit(text_surface, (20, 20 + i * 25))

    def draw_instructions_panel(self, screen, instructions):
        """Draw instructions panel at bottom of screen"""
        panel_height = len(instructions) * 20 + 20
        instruction_panel = pygame.Rect(10, self.height - panel_height - 10, 400, panel_height)
        pygame.draw.rect(screen, UI_BG_COLOR, instruction_panel)
        pygame.draw.rect(screen, UI_BORDER_COLOR, instruction_panel, 2)

        for i, instruction in enumerate(instructions):
            text_surface = self.small_font.render(instruction, True, WHITE)
            screen.blit(text_surface, (20, self.height - panel_height + i * 20))


class Camera:
    """Camera system for following the player"""

    def __init__(self, screen_width, screen_height, world_width, world_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.world_width = world_width
        self.world_height = world_height
        self.x = 0
        self.y = 0

    def update(self, target_x, target_y):
        """Update camera to follow target (usually the player)"""
        # Calculate target camera position (center target on screen)
        target_camera_x = target_x - self.screen_width // 2
        target_camera_y = target_y - self.screen_height // 2

        # Clamp camera to world bounds
        self.x = max(0, min(self.world_width - self.screen_width, target_camera_x))
        self.y = max(0, min(self.world_height - self.screen_height, target_camera_y))

    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        return (world_x - self.x, world_y - self.y)

    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        return (screen_x + self.x, screen_y + self.y)

    def is_visible(self, world_x, world_y, obj_width=30, obj_height=30):
        """Check if an object at world coordinates is visible on screen"""
        screen_x, screen_y = self.world_to_screen(world_x, world_y)
        return (-obj_width < screen_x < self.screen_width and
                -obj_height < screen_y < self.screen_height)


class WorldObject:
    """Base class for world objects (enemies, loot, stores, etc.)"""

    def __init__(self, x, y, obj_type, active=True):
        self.x = x
        self.y = y
        self.obj_type = obj_type
        self.active = active
        self.width = 30
        self.height = 30

    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen, camera):
        """Draw the object (to be overridden by subclasses)"""
        if not self.active:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        if camera.is_visible(self.x, self.y, self.width, self.height):
            pygame.draw.rect(screen, GRAY, (screen_x, screen_y, self.width, self.height))


class Enemy(WorldObject):
    """Enemy object with pulsing red appearance"""

    def __init__(self, x, y, enemy_data=None):
        super().__init__(x, y, "enemy")
        self.enemy_data = enemy_data or {"Name": "Wild Demon", "Hit_Points": 75}
        self.width = 20
        self.height = 20

    def draw(self, screen, camera, animation_timer=0):
        if not self.active:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        if camera.is_visible(self.x, self.y, self.width, self.height):

            # Smaller sparkling enemy effect
            sparkle = int(5 * abs(math.sin(animation_timer * 0.15)))  # Reduced sparkle
            treasure_radius = 10 + sparkle  # Smaller radius
            pygame.draw.circle(screen, RED,
                               (screen_x + 10, screen_y + 10), treasure_radius)
            pygame.draw.circle(screen, BLACK,
                               (screen_x + 10, screen_y + 10), treasure_radius, 2)

            # Draw "E" symbol
            font = pygame.font.Font(None, 16)  # Smaller font
            text = font.render("E", True, BLACK)
            text_rect = text.get_rect(center=(screen_x + 10, screen_y + 10))
            screen.blit(text, text_rect)


class Treasure(WorldObject):
    """Treasure object with smaller sparkling gold appearance"""

    def __init__(self, x, y, value=None):
        super().__init__(x, y, "treasure")
        self.value = value or random.randint(50, 150)
        # self.value = value
        # Make treasure smaller
        self.width = 20  # Reduced from 30
        self.height = 20  # Reduced from 30

    def draw(self, screen, camera, animation_timer=0):
        if not self.active:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        if camera.is_visible(self.x, self.y, self.width, self.height):
            # Smaller sparkling treasure effect
            sparkle = int(5 * abs(math.sin(animation_timer * 0.15)))  # Reduced sparkle
            treasure_radius = 10 + sparkle  # Smaller radius
            pygame.draw.circle(screen, GOLD,
                               (screen_x + 10, screen_y + 10), treasure_radius)
            pygame.draw.circle(screen, BLACK,
                               (screen_x + 10, screen_y + 10), treasure_radius, 2)

            # Draw "$" symbol
            font = pygame.font.Font(None, 16)  # Smaller font
            text = font.render("$", True, BLACK)
            text_rect = text.get_rect(center=(screen_x + 10, screen_y + 10))
            screen.blit(text, text_rect)


class Shop(WorldObject):
    """Shop object with animated store appearance"""

    def __init__(self, x, y):
        super().__init__(x, y, "shop")
        self.width = 50
        self.height = 50

    def draw(self, screen, camera, animation_timer=0):
        if not self.active:
            return

        screen_x, screen_y = camera.world_to_screen(self.x, self.y)
        if camera.is_visible(self.x, self.y, self.width, self.height):
            # Animated store
            store_rect = pygame.Rect(screen_x, screen_y, self.width, self.height)
            pygame.draw.rect(screen, PURPLE, store_rect)
            pygame.draw.rect(screen, WHITE, store_rect, 3)

            # Shop sign with pulse effect
            pulse = int(5 * abs(math.sin(animation_timer * 0.1)))
            font_size = 28 + pulse
            font = pygame.font.Font(None, font_size)
            shop_text = font.render("S", True, GOLD)
            shop_rect = shop_text.get_rect(center=(screen_x + 25, screen_y + 25))
            screen.blit(shop_text, shop_rect)