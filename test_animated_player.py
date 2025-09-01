#!/usr/bin/env python3
"""
Test script for the animated player system
This will help verify that the animation is working correctly
"""

import pygame
import sys
import os
from animated_player import AnimatedPlayer


def create_fallback_sprite_sheet():
    """Create a simple colored sprite sheet for testing if the actual file is missing"""
    sprite_sheet = pygame.Surface((640, 640))
    sprite_sheet.fill((50, 50, 50))  # Dark gray background

    # Create 8 frames for each of 8 states (8 directions x 8 frames)
    colors = [
        (255, 0, 0),  # Red - Up
        (0, 255, 0),  # Green - Down
        (0, 0, 255),  # Blue - Right
        (255, 255, 0),  # Yellow - Left
        (128, 0, 128),  # Purple - Up Idle
        (0, 128, 128),  # Teal - Down Idle
        (128, 128, 0),  # Olive - Right Idle
        (255, 128, 0),  # Orange - Left Idle
    ]

    for state in range(8):
        for frame in range(8):
            x = frame * 80 + 15
            y = state * 80 + 15
            color = colors[state]

            # Draw a simple character shape
            pygame.draw.circle(sprite_sheet, color, (x + 25, y + 20), 15)  # Head
            pygame.draw.rect(sprite_sheet, color, (x + 15, y + 30, 20, 25))  # Body
            pygame.draw.rect(sprite_sheet, color, (x + 10, y + 35, 8, 15))  # Left arm
            pygame.draw.rect(sprite_sheet, color, (x + 32, y + 35, 8, 15))  # Right arm
            pygame.draw.rect(sprite_sheet, color, (x + 18, y + 50, 6, 15))  # Left leg
            pygame.draw.rect(sprite_sheet, color, (x + 26, y + 50, 6, 15))  # Right leg

            # Add frame number for debugging
            font = pygame.font.Font(None, 16)
            frame_text = font.render(str(frame), True, (255, 255, 255))
            sprite_sheet.blit(frame_text, (x + 2, y + 2))

    return sprite_sheet


def main():
    """Main test function"""
    pygame.init()

    # Screen settings
    WIDTH, HEIGHT = 800, 600
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Animated Player Test")

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (128, 128, 128)

    # Check if sprite file exists
    sprite_file = "80SpriteSheetNEW.png"
    if not os.path.exists(sprite_file):
        print(f"⚠️  Sprite file '{sprite_file}' not found!")
        print("Creating a test sprite sheet...")

        # Create and save a test sprite sheet
        test_sprite = create_fallback_sprite_sheet()
        pygame.image.save(test_sprite, sprite_file)
        print(f"✅ Created test sprite sheet: {sprite_file}")

    # Initialize animated player
    try:
        player = AnimatedPlayer(sprite_file)
        player.x = WIDTH // 2
        player.y = HEIGHT // 2
        print(f"✅ Animated player initialized successfully!")
        print(f"   Sprite size: {player.width}x{player.height}")
        print(f"   Display size: {player.display_width}x{player.display_height}")
        print(f"   Speed: {player.speed}")
    except Exception as e:
        print(f"❌ Failed to initialize animated player: {e}")
        return

    # Load font for info display
    try:
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)
    except:
        font = pygame.font.Font(None, 24)
        small_font = pygame.font.Font(None, 18)

    # Game loop
    clock = pygame.time.Clock()
    running = True

    print("\n🎮 Test Controls:")
    print("   Arrow Keys - Move and animate character")
    print("   ESC - Exit test")
    print("   Watch the character animate as you move!")
    print("\n🔍 Debug Info:")

    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Update player (using screen dimensions for this test)
        moved = player.update_position(WIDTH - player.display_width, HEIGHT - player.display_height)

        # Clear screen
        screen.fill(GRAY)

        # Draw grid background for reference
        grid_size = 50
        for x in range(0, WIDTH, grid_size):
            pygame.draw.line(screen, WHITE, (x, 0), (x, HEIGHT), 1)
        for y in range(0, HEIGHT, grid_size):
            pygame.draw.line(screen, WHITE, (0, y), (WIDTH, y), 1)

        # Draw player
        player.draw(screen)

        # Draw debug info
        debug_info = [
            f"Position: ({player.x}, {player.y})",
            f"State: {player.state} ({'Moving' if player.state < 4 else 'Idle'})",
            f"Frame: {int(player.frame)}/7",
            f"Moving: {'Yes' if moved else 'No'}",
            "",
            "State Legend:",
            "0=Up, 1=Down, 2=Right, 3=Left",
            "4=Up Idle, 5=Down Idle",
            "6=Right Idle, 7=Left Idle"
        ]

        y_offset = 10
        for i, info in enumerate(debug_info):
            if info == "":
                y_offset += 10
                continue

            color = WHITE if i < 4 else (200, 200, 200)
            font_to_use = font if i < 4 else small_font

            text = font_to_use.render(info, True, color)
            screen.blit(text, (10, y_offset))
            y_offset += 20 if i < 4 else 15

        # Draw instructions
        instructions = [
            "Arrow Keys: Move character",
            "ESC: Exit test",
            "Watch animation states change!"
        ]

        instruction_y = HEIGHT - 80
        for instruction in instructions:
            text = small_font.render(instruction, True, WHITE)
            screen.blit(text, (10, instruction_y))
            instruction_y += 20

        # Update display
        pygame.display.flip()
        clock.tick(60)  # 60 FPS

        # Print debug info every second (for console output)
        if pygame.time.get_ticks() % 1000 < 17:  # Approximately every second
            state_names = ["Up", "Down", "Right", "Left", "Up Idle", "Down Idle", "Right Idle", "Left Idle"]
            current_state = state_names[player.state] if player.state < 8 else f"Unknown({player.state})"
            print(f"   State: {current_state}, Frame: {int(player.frame)}, Pos: ({player.x}, {player.y})")

    print("\n✅ Animation test completed!")
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()