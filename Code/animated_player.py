import pygame
from pygame.locals import *
import random


class AnimatedPlayer(pygame.sprite.Sprite):
    """Enhanced Player class with animation from RPG2 demo"""

    def __init__(self, sprite_sheet_path="80SpriteSheetNEW.png"):
        super().__init__()
        self.x = 0
        self.y = 0
        self.height = 80
        self.width = 80
        self.speed = 4  # Reduced for better control
        self.frame = 0
        self.state = 0  # 0=up, 1=down, 2=right, 3=left, 4-7=idle states
        self.buffer = 15

        # Load sprite sheet
        try:
            self.spriteSheet = pygame.image.load(sprite_sheet_path)
        except:
            # Create fallback sprite if file doesn't exist
            self.spriteSheet = pygame.Surface((640, 640))
            self.spriteSheet.fill((0, 100, 200))

        self.image = self.spriteSheet.subsurface(Rect(self.x, self.y, self.width, self.height))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        # Increased scale for bigger player
        self.scale = 0.5  # Increased from 0.3 to 0.5
        self.display_width = int(self.width * self.scale)
        self.display_height = int(self.height * self.scale)

    def update_position(self, screen_width, screen_height):
        """Update player position based on key presses"""
        # Reset to idle states if no movement
        if self.state == 0:
            self.state = 4  # Up idle
        elif self.state == 1:
            self.state = 5  # Down idle
        elif self.state == 2:
            self.state = 6  # Right idle
        elif self.state == 3:
            self.state = 7  # Left idle

        pressed_keys = pygame.key.get_pressed()
        moved = False

        # Movement with bounds checking
        if self.y > 0:
            if pressed_keys[K_UP]:
                self.y -= self.speed
                self.state = 0
                moved = True

        if self.y < screen_height - self.display_height:
            if pressed_keys[K_DOWN]:
                self.y += self.speed
                self.state = 1
                moved = True

        if self.x < screen_width - self.display_width:
            if pressed_keys[K_RIGHT]:
                self.x += self.speed
                self.state = 2
                moved = True

        if self.x > 0:
            if pressed_keys[K_LEFT]:
                self.x -= self.speed
                self.state = 3
                moved = True

        return moved

    def draw(self, screen):
        """Draw the animated character at current position"""
        self.draw_at_screen_position(screen, self.x, self.y)

    def draw_at_screen_position(self, screen, screen_x, screen_y):
        """Draw the animated character at specified screen position"""
        # Animate frames
        self.frame += 1
        if self.frame >= 8:
            self.frame = 0

        # Get current sprite from sheet
        sprite_rect = Rect(
            self.frame * self.width + self.buffer,
            self.state * self.height + self.buffer,
            self.width - self.buffer,
            self.height - self.buffer
        )

        try:
            current_sprite = self.spriteSheet.subsurface(sprite_rect)
            # Scale down the sprite
            scaled_sprite = pygame.transform.scale(current_sprite,
                                                   (self.display_width, self.display_height))
            screen.blit(scaled_sprite, (screen_x, screen_y))
        except:
            # Fallback drawing - draw a simple character representation (larger)
            # Body
            pygame.draw.circle(screen, (220, 180, 140),
                             (int(screen_x + self.display_width//2), int(screen_y + self.display_height//3)),
                             self.display_width//3)  # Increased from //4 to //3
            # Head
            pygame.draw.circle(screen, (255, 220, 177),
                             (int(screen_x + self.display_width//2), int(screen_y + self.display_height//6)),
                             self.display_width//4)  # Increased from //6 to //4
            # Body rectangle
            pygame.draw.rect(screen, (100, 50, 200),
                             (screen_x + self.display_width//4, screen_y + self.display_height//3,
                              self.display_width//2, self.display_height//2))
            # Legs
            pygame.draw.rect(screen, (50, 50, 50),
                             (screen_x + self.display_width//3, screen_y + 4*self.display_height//5,
                              self.display_width//6, self.display_height//5))
            pygame.draw.rect(screen, (50, 50, 50),
                             (screen_x + self.display_width//2, screen_y + 4*self.display_height//5,
                              self.display_width//6, self.display_height//5))

    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(self.x, self.y, self.display_width, self.display_height)

    def set_position(self, x, y):
        """Set player position directly"""
        self.x = x
        self.y = y