import pygame
import random
import math
from Code.ui_components import *


class RestManager:
    """Manages rest areas and cooldown timers"""

    def __init__(self, character_manager):
        self.character_manager = character_manager
        self.rest_cooldown = 0  # Cooldown timer in frames (15 fps)
        self.cooldown_duration = 2700  # 3 minutes at 15 fps (15 * 60 * 3)
        self.rest_cost = 0  # Free resting
        self.last_rest_message = ""

        # UI fonts
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)

    def can_rest(self):
        """Check if player can rest (not in cooldown)"""
        return self.rest_cooldown <= 0

    def get_cooldown_time_remaining(self):
        """Get remaining cooldown time in seconds"""
        if self.rest_cooldown <= 0:
            return 0
        return max(0, self.rest_cooldown // 15)  # Convert frames to seconds

    def attempt_rest(self):
        """Attempt to rest and recover HP/MP"""
        if not self.character_manager.character_data:
            return {"success": False, "message": "No character loaded!"}

        if not self.can_rest():
            remaining = self.get_cooldown_time_remaining()
            minutes = remaining // 60
            seconds = remaining % 60
            return {
                "success": False,
                "message": f"Must wait {minutes:02d}:{seconds:02d} before resting again"
            }

        char_data = self.character_manager.character_data
        level = char_data.get("Level", 1)

        # Calculate max HP and MP
        max_hp = self.character_manager.get_max_hp_for_level(level)
        max_mp = self.character_manager.get_max_mana_for_level(level)

        # Current HP and MP
        current_hp = char_data.get("Hit_Points", 100)
        current_mp = char_data.get("Aspect1_Mana", 50)

        # Check if already at full health/mana
        if current_hp >= max_hp and current_mp >= max_mp:
            return {
                "success": False,
                "message": "You are already at full health and mana!"
            }

        # Calculate restoration amounts (75-100% recovery)
        hp_restore = max_hp - current_hp
        mp_restore = max_mp - current_mp

        # Apply partial restoration for balance (75-90% of missing)
        hp_gained = int(hp_restore * random.uniform(0.75, 0.90))
        mp_gained = int(mp_restore * random.uniform(0.75, 0.90))

        # Ensure at least some benefit if not at full
        if hp_restore > 0 and hp_gained == 0:
            hp_gained = min(5, hp_restore)
        if mp_restore > 0 and mp_gained == 0:
            mp_gained = min(3, mp_restore)

        # Apply the restoration
        char_data["Hit_Points"] = min(max_hp, current_hp + hp_gained)
        char_data["Aspect1_Mana"] = min(max_mp, current_mp + mp_gained)

        # Start cooldown
        self.rest_cooldown = self.cooldown_duration

        # Save character
        self.character_manager.save_character()

        # Create success message
        message_parts = []
        if hp_gained > 0:
            message_parts.append(f"Restored {hp_gained} HP")
        if mp_gained > 0:
            message_parts.append(f"Restored {mp_gained} MP")

        if message_parts:
            message = "Rested successfully! " + ", ".join(message_parts)
        else:
            message = "You feel refreshed!"

        self.last_rest_message = message

        return {
            "success": True,
            "message": message,
            "hp_gained": hp_gained,
            "mp_gained": mp_gained
        }

    def update(self):
        """Update cooldown timer"""
        if self.rest_cooldown > 0:
            self.rest_cooldown -= 1

    def draw_rest_status(self, screen, x, y):
        """Draw rest status information"""
        if self.rest_cooldown > 0:
            remaining = self.get_cooldown_time_remaining()
            minutes = remaining // 60
            seconds = remaining % 60

            # Cooldown status
            cooldown_text = f"Rest Cooldown: {minutes:02d}:{seconds:02d}"
            cooldown_color = RED if remaining > 30 else ORANGE

            text_surface = self.small_font.render(cooldown_text, True, cooldown_color)
            screen.blit(text_surface, (x, y))
        else:
            # Available status
            available_text = "Rest Available - Walk into a rest area"
            text_surface = self.small_font.render(available_text, True, GREEN)
            screen.blit(text_surface, (x, y))

    def draw_rest_hud(self, screen, width, height):
        """Draw rest HUD element near player info in top-left"""
        # Draw near the player info in top-left area
        hud_x = 10
        hud_y = 140  # Position below the player status overlay

        # Background
        hud_rect = pygame.Rect(hud_x, hud_y, 270, 25)
        pygame.draw.rect(screen, (0, 0, 0, 128), hud_rect)
        pygame.draw.rect(screen, UI_BORDER_COLOR, hud_rect, 1)

        # Rest status
        if self.rest_cooldown > 0:
            remaining = self.get_cooldown_time_remaining()
            minutes = remaining // 60
            seconds = remaining % 60

            status_text = f"🛌 Rest Cooldown: {minutes:02d}:{seconds:02d}"
            text_color = RED if remaining > 60 else ORANGE
        else:
            status_text = "🛌 Rest Available (Bottom-Right Corner)"
            text_color = GREEN

        text_surface = self.small_font.render(status_text, True, text_color)
        screen.blit(text_surface, (hud_x + 5, hud_y + 5))


class EnhancedRestArea(RestArea):
    """Enhanced rest area with visual feedback and interaction"""

    def __init__(self, x, y, rest_manager):
        super().__init__(x, y)
        self.rest_manager = rest_manager
        self.interaction_cooldown = 0
        self.pulse_timer = 0

    def update(self):
        """Update rest area animations and cooldowns"""
        if self.interaction_cooldown > 0:
            self.interaction_cooldown -= 1
        self.pulse_timer += 1

    def can_interact(self):
        """Check if player can interact with this rest area"""
        return (self.interaction_cooldown <= 0 and
                self.rest_manager.can_rest())

    def attempt_interaction(self):
        """Attempt to use this rest area"""
        if self.interaction_cooldown > 0:
            return {"success": False, "message": "Just used this rest area!"}

        # Set short interaction cooldown to prevent spam
        self.interaction_cooldown = 30  # 2 seconds

        # Attempt rest through rest manager
        return self.rest_manager.attempt_rest()

    def draw(self, screen, camera_x=0, camera_y=0):
        """Enhanced drawing with availability indicators"""
        # Adjust position for camera
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y

        # Only draw if visible
        if (-self.width < screen_x < screen.get_width() and
                -self.height < screen_y < screen.get_height()):

            # Base area for tent (larger for better visibility)
            draw_rect = pygame.Rect(screen_x, screen_y, 50, 50)  # Made larger

            # Base color depends on availability
            if self.can_interact():
                base_color = (0, 150, 250)  # Bright blue when available
                # Add pulsing effect
                pulse = int(15 * abs(math.sin(self.pulse_timer * 0.1)))
                border_color = (min(255, 0 + pulse), min(255, 150 + pulse), min(255, 250 + pulse))
            elif not self.rest_manager.can_rest():
                base_color = (100, 50, 50)  # Dark red when on cooldown
                border_color = (150, 75, 75)
            else:
                base_color = (100, 100, 150)  # Gray when recently used
                border_color = (150, 150, 200)

            # Draw base area
            pygame.draw.rect(screen, base_color, draw_rect)
            pygame.draw.rect(screen, border_color, draw_rect, 2)

            # Draw tent shape (larger and more detailed)
            tent_center_x = screen_x + 25  # Center of 50px area
            tent_center_y = screen_y + 25  # Center of 50px area

            # Main tent triangle
            tent_points = [
                (tent_center_x, tent_center_y - 15),  # Top point
                (tent_center_x - 20, tent_center_y + 15),  # Bottom left
                (tent_center_x + 20, tent_center_y + 15)  # Bottom right
            ]

            tent_color = (220, 240, 255) if self.can_interact() else (180, 180, 200)
            pygame.draw.polygon(screen, tent_color, tent_points)
            pygame.draw.polygon(screen, BLACK, tent_points, 2)

            # Tent entrance flap
            flap_points = [
                (tent_center_x - 5, tent_center_y + 15),
                (tent_center_x + 5, tent_center_y + 15),
                (tent_center_x, tent_center_y + 5)
            ]
            pygame.draw.polygon(screen, (100, 120, 140), flap_points)

            # Tent pole
            pygame.draw.line(screen, (139, 69, 19),
                           (tent_center_x, tent_center_y - 15),
                           (tent_center_x, tent_center_y + 15), 3)

            # Rest label with status - positioned above tent
            rest_font = pygame.font.Font(None, 14)
            if self.can_interact():
                label_text = "REST"
                label_color = WHITE
            elif not self.rest_manager.can_rest():
                remaining = self.rest_manager.get_cooldown_time_remaining()
                minutes = remaining // 60
                seconds = remaining % 60
                label_text = f"{minutes:02d}:{seconds:02d}"
                label_color = RED
            else:
                label_text = "USED"
                label_color = GRAY

            text = rest_font.render(label_text, True, label_color)
            text_rect = text.get_rect(center=(tent_center_x, screen_y - 10))

            # Text background
            bg_rect = text_rect.inflate(6, 2)
            pygame.draw.rect(screen, (0, 0, 0, 180), bg_rect)

            screen.blit(text, text_rect)

            # Interaction hint when available
            if self.can_interact():
                hint_font = pygame.font.Font(None, 10)
                hint_text = hint_font.render("Walk into tent", True, WHITE)
                hint_rect = hint_text.get_rect(center=(tent_center_x, screen_y + 60))

                # Subtle fade effect
                alpha = int(150 + 100 * abs(math.sin(self.pulse_timer * 0.2)))
                hint_bg = pygame.Rect(hint_rect.x - 3, hint_rect.y, hint_rect.width + 6, hint_rect.height + 2)
                pygame.draw.rect(screen, (0, 0, 0, alpha), hint_bg)

                hint_text.set_alpha(alpha)
                screen.blit(hint_text, hint_rect)