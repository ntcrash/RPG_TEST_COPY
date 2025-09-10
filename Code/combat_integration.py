"""
Combat Integration Module
Integrates the advanced combat system with the main game
"""

import pygame
import random
from Code.combat_system import CombatManager
from game_data import CharacterManager
from Code.ui_components import *


class GameState:
    """Game state constants - duplicate from main.py for integration"""
    OPENING = 0
    MAIN_MENU = 1
    CHARACTER_SELECT = 2
    CREATE_CHARACTER = 3
    GAME_BOARD = 4
    FIGHT = 5
    STORE = 6
    INVENTORY = 7
    CHARACTER_SHEET = 8
    HELP = 9


class CombatIntegration:
    """Handles integration between main game and combat system"""

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.combat_manager = CombatManager(game_manager.character_manager)
        self.in_combat = False
        self.combat_result = None

    def start_combat(self, enemy_data):
        """Start combat with given enemy"""
        self.combat_manager.start_combat(enemy_data)
        self.in_combat = True
        self.combat_result = None
        return True

    def handle_combat_input(self, key):
        """Handle input during combat"""
        if not self.in_combat:
            return None

        result = self.combat_manager.handle_keypress(key)

        if result == "run_success":
            self.end_combat("escaped")
            return "escaped"
        elif result in ["victory", "defeat"]:
            self.end_combat(result)
            return result

        return "continue"

    def update_combat(self):
        """Update combat system"""
        if not self.in_combat:
            return None

        result = self.combat_manager.update()

        if result == "victory":
            self.handle_victory()
            self.end_combat("victory")
            return "victory"
        elif result == "defeat":
            self.handle_defeat()
            self.end_combat("defeat")
            return "defeat"

        return "continue"

    def handle_victory(self):
        """Handle combat victory"""
        if not self.game_manager.character_manager.character_data:
            return

        enemy_level = self.combat_manager.current_enemy.get("Level", 1)

        # Calculate rewards based on enemy level
        base_xp = 50
        base_credits = 75

        xp_gained = base_xp + (enemy_level * 25) + random.randint(-10, 20)
        credits_gained = base_credits + (enemy_level * 30) + random.randint(-20, 30)

        # Apply rewards
        char_data = self.game_manager.character_manager.character_data
        char_data["Experience_Points"] = char_data.get("Experience_Points", 0) + xp_gained
        char_data["Credits"] = char_data.get("Credits", 0) + credits_gained

        # Chance for item reward
        if random.randint(1, 100) <= 25:  # 25% chance
            self.give_random_item()

        # Check for level up
        leveled_up = self.game_manager.character_manager.level_up_check()

        # Add victory message
        victory_msg = f"Victory! Gained {xp_gained} XP and {credits_gained} credits!"
        if leveled_up:
            victory_msg += " LEVEL UP!"

        self.combat_manager.add_combat_log(victory_msg, GOLD)

        # Save character progress
        self.game_manager.character_manager.save_character()

    def handle_defeat(self):
        """Handle combat defeat"""
        if not self.game_manager.character_manager.character_data:
            return

        # Respawn with reduced stats
        char_data = self.game_manager.character_manager.character_data
        level = char_data.get("Level", 1)
        max_hp = self.game_manager.character_manager.get_max_hp_for_level(level)

        # Restore to 25% health
        char_data["Hit_Points"] = max(1, max_hp // 4)

        # Lose some credits (10-20%)
        current_credits = char_data.get("Credits", 0)
        credits_lost = random.randint(int(current_credits * 0.1), int(current_credits * 0.2))
        char_data["Credits"] = max(0, current_credits - credits_lost)

        defeat_msg = f"Defeat! Lost {credits_lost} credits. You wake up wounded..."
        self.combat_manager.add_combat_log(defeat_msg, RED)

        # Save character
        self.game_manager.character_manager.save_character()

    def give_random_item(self):
        """Give player a random item reward"""
        if not self.game_manager.character_manager.character_data:
            return

        # Possible item rewards
        possible_items = [
            "Health Potion",
            "Mana Potion",
            "Greater Health Potion",
            "Greater Mana Potion"
        ]

        # Higher level enemies give better items
        enemy_level = self.combat_manager.current_enemy.get("Level", 1)
        if enemy_level >= 3:
            possible_items.extend(["Greater Health Potion", "Greater Mana Potion"])
        if enemy_level >= 5:
            possible_items.extend(["Full Restore"])

        item_name = random.choice(possible_items)

        # Add to inventory
        char_data = self.game_manager.character_manager.character_data
        inventory = char_data.get("Inventory", {})
        inventory[item_name] = inventory.get(item_name, 0) + 1
        char_data["Inventory"] = inventory

        reward_msg = f"Found {item_name}!"
        self.combat_manager.add_combat_log(reward_msg, LIGHT_BLUE)

    def end_combat(self, result):
        """End combat and return to world"""
        self.in_combat = False
        self.combat_result = result

        # If victory, deactivate the enemy in the world
        if result == "victory" and hasattr(self.game_manager, 'current_enemy_obj'):
            self.game_manager.current_enemy_obj.active = False

    def draw_combat(self, screen):
        """Draw combat interface"""
        if self.in_combat:
            self.combat_manager.draw(screen)

            # Add any additional UI elements specific to integration
            self.draw_combat_hud(screen)

    def draw_combat_hud(self, screen):
        """Draw additional HUD elements during combat"""
        # Draw escape instruction
        font = pygame.font.Font(None, 20)
        escape_text = font.render("ESC: Forfeit and flee combat", True, WHITE)
        screen.blit(escape_text, (10, 10))

        # Show current world time or other contextual info
        if hasattr(self.game_manager, 'animation_timer'):
            # Could add day/night cycle or other world state info
            pass


def integrate_combat_with_game_states(game_manager):
    """
    Integration function to modify existing game states for combat
    Call this from your main game initialization
    """

    # Create combat integration
    combat_integration = CombatIntegration(game_manager)
    game_manager.combat_integration = combat_integration

    # Store original enemy collision handler
    original_check_collisions = game_manager.check_collisions

    def enhanced_check_collisions():
        """Enhanced collision detection with combat integration"""
        collision_type, collision_obj = original_check_collisions()

        if collision_type == "enemy" and collision_obj:
            # Start combat instead of simple collision
            collision_obj.active = False  # Remove from world temporarily
            game_manager.current_enemy_obj = collision_obj

            # Start advanced combat
            if combat_integration.start_combat(collision_obj.enemy_data):
                game_manager.current_state = GameState.FIGHT
                return None, None  # No standard collision handling

        return collision_type, collision_obj

    # Replace collision detection
    game_manager.check_collisions = enhanced_check_collisions

    # Store original fight screen drawing
    original_draw_fight_screen = game_manager.draw_fight_screen

    def enhanced_draw_fight_screen():
        """Enhanced fight screen with advanced combat"""
        if hasattr(game_manager, 'combat_integration') and game_manager.combat_integration.in_combat:
            game_manager.combat_integration.draw_combat(game_manager.screen)
        else:
            original_draw_fight_screen()

    # Replace fight screen drawing
    game_manager.draw_fight_screen = enhanced_draw_fight_screen

    # Store original handle keypress for fight state
    original_handle_keypress = game_manager.handle_keypress

    def enhanced_handle_keypress(key):
        """Enhanced keypress handling with combat integration"""
        if (game_manager.current_state == GameState.FIGHT and
                hasattr(game_manager, 'combat_integration')):

            # Handle combat input
            result = game_manager.combat_integration.handle_combat_input(key)

            if result == "escaped":
                game_manager.current_state = GameState.GAME_BOARD
                return True
            elif result in ["victory", "defeat"]:
                game_manager.current_state = GameState.GAME_BOARD
                return True
            elif result == "continue":
                return True

            # Handle ESC to forfeit
            if key == pygame.K_ESCAPE:
                game_manager.combat_integration.end_combat("forfeited")
                game_manager.current_state = GameState.GAME_BOARD
                return True

        # Call original handler for other states
        return original_handle_keypress(key)

    # Replace keypress handling
    game_manager.handle_keypress = enhanced_handle_keypress

    # Store original update method
    original_update = game_manager.update

    def enhanced_update():
        """Enhanced update with combat integration"""
        # Call original update
        original_update()

        # Update combat if active
        if (hasattr(game_manager, 'combat_integration') and
                game_manager.combat_integration.in_combat):

            result = game_manager.combat_integration.update_combat()
            if result in ["victory", "defeat", "escaped"]:
                game_manager.current_state = GameState.GAME_BOARD

    # Replace update method
    game_manager.update = enhanced_update

    return combat_integration


# Usage instructions for integrating with existing game:
"""
To integrate this combat system with your existing game:

1. Import the integration at the top of main.py:
   from combat_integration import integrate_combat_with_game_states

2. In EnhancedGameManager.__init__(), after all other initialization, add:
   integrate_combat_with_game_states(self)

3. The integration will automatically:
   - Replace simple enemy collisions with advanced combat
   - Handle combat input and state management  
   - Provide victory/defeat rewards and consequences
   - Integrate floating combat text with the world

4. No other changes to existing code are needed!
"""