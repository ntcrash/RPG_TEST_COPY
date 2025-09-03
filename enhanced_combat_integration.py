"""
Enhanced Combat Integration Module
Integrates the enhanced combat system with sound and animation support
"""

import pygame
import random
import os
from enhanced_combat_system import EnhancedCombatManager, SoundManager
from game_data import CharacterManager
from ui_components import *


class GameState:
    """Game state constants - duplicate from game_states.py for integration"""
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


class EnhancedCombatIntegration:
    """Handles integration between main game and enhanced combat system"""

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.combat_manager = EnhancedCombatManager(game_manager.character_manager)
        self.sound_manager = SoundManager()  # Separate sound manager for world sounds
        self.in_combat = False
        self.combat_result = None

        # Combat entry/exit cooldowns
        self.combat_entry_cooldown = 0
        self.post_combat_invulnerability = 0

        # World sound effects
        self.footstep_timer = 0

    def start_combat(self, enemy_data):
        """Start combat with enhanced entry effects"""
        if self.combat_entry_cooldown > 0:
            return False

        # Play dramatic combat entry sound
        self.sound_manager.play_sound("menu_select")

        # Start the enhanced combat system
        self.combat_manager.start_combat(enemy_data)
        self.in_combat = True
        self.combat_result = None

        # Set cooldown to prevent immediate re-entry
        self.combat_entry_cooldown = 60  # 4 seconds at 15 FPS

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
        """Handle combat victory with enhanced rewards"""
        if not self.game_manager.character_manager.character_data:
            return

        enemy_level = self.combat_manager.current_enemy.get("Level", 1)
        enemy_name = self.combat_manager.current_enemy.get("Name", "Enemy")

        # Calculate rewards based on enemy level and type
        base_xp = 50
        base_credits = 75

        # Bonus for elite/boss enemies
        if "Elite" in enemy_name:
            base_xp *= 1.5
            base_credits *= 1.5
        elif "Ancient" in enemy_name or "BOSS" in enemy_name:
            base_xp *= 2.0
            base_credits *= 2.0

        xp_gained = int(base_xp + (enemy_level * 25) + random.randint(-10, 20))
        credits_gained = int(base_credits + (enemy_level * 30) + random.randint(-20, 30))

        # Apply rewards
        char_data = self.game_manager.character_manager.character_data
        char_data["Experience_Points"] = char_data.get("Experience_Points", 0) + xp_gained
        char_data["Credits"] = char_data.get("Credits", 0) + credits_gained

        # Enhanced item reward system
        item_chance = 25 + (enemy_level * 5)  # Higher level = better item chance
        if "Elite" in enemy_name:
            item_chance += 15
        elif "Ancient" in enemy_name or "BOSS" in enemy_name:
            item_chance += 25

        if random.randint(1, 100) <= item_chance:
            self.give_random_item(enemy_level, enemy_name)

        # Check for level up
        leveled_up = self.game_manager.character_manager.level_up_check()

        # Enhanced victory message with sound
        victory_msg = f"🎉 Victory! Gained {xp_gained} XP and {credits_gained} credits!"
        if leveled_up:
            victory_msg += " ⭐ LEVEL UP! ⭐"
            # Play level up sound
            self.sound_manager.play_sound("victory")

        self.combat_manager.add_combat_log(victory_msg, GOLD)

        # Save character progress
        self.game_manager.character_manager.save_character()

        # Set post-combat invulnerability
        self.post_combat_invulnerability = 120  # 8 seconds

    def handle_defeat(self):
        """Handle combat defeat with enhanced consequences"""
        if not self.game_manager.character_manager.character_data:
            return

        char_data = self.game_manager.character_manager.character_data
        level = char_data.get("Level", 1)
        max_hp = self.game_manager.character_manager.get_max_hp_for_level(level)

        # Respawn with reduced stats - scale with level
        respawn_hp_percent = max(0.15, 0.35 - (level * 0.02))  # Less HP penalty at higher levels
        char_data["Hit_Points"] = max(1, int(max_hp * respawn_hp_percent))

        # Lose credits based on level and current wealth
        current_credits = char_data.get("Credits", 0)
        credit_loss_percent = random.uniform(0.05, 0.15)  # 5-15% loss
        credits_lost = int(current_credits * credit_loss_percent)
        char_data["Credits"] = max(0, current_credits - credits_lost)

        # Small XP penalty for higher level characters
        if level > 3:
            current_xp = char_data.get("Experience_Points", 0)
            xp_loss = min(50, current_xp // 20)  # Lose up to 50 XP, based on current XP
            char_data["Experience_Points"] = max(0, current_xp - xp_loss)

        defeat_msg = f"💀 Defeat! Lost {credits_lost} credits. You wake up wounded..."
        self.combat_manager.add_combat_log(defeat_msg, RED)

        # Save character
        self.game_manager.character_manager.save_character()

        # Set longer invulnerability after defeat
        self.post_combat_invulnerability = 180  # 12 seconds

    def give_random_item(self, enemy_level, enemy_name):
        """Give player a random item reward based on enemy difficulty"""
        if not self.game_manager.character_manager.character_data:
            return

        # Tier items by enemy level and type
        basic_items = ["Health Potion", "Mana Potion"]
        good_items = ["Greater Health Potion", "Greater Mana Potion"]
        rare_items = ["Full Restore"]

        # Equipment rewards for higher level enemies
        equipment_items = []
        if enemy_level >= 3:
            equipment_items = ["Enhanced Spell Blade", "Mystic Staff", "Leather Armor"]
        if enemy_level >= 5:
            equipment_items.extend(["Warrior's Sword", "Mystic Armor", "Ring of Strength"])

        # Determine item pool
        possible_items = basic_items.copy()

        if enemy_level >= 2:
            possible_items.extend(good_items)
        if enemy_level >= 4:
            possible_items.extend(rare_items)
        if enemy_level >= 3 and random.randint(1, 100) <= 20:  # 20% chance for equipment
            possible_items.extend(equipment_items)

        # Boss/Elite enemies have better rewards
        if "Elite" in enemy_name:
            possible_items.extend(good_items)
            if equipment_items:
                possible_items.extend(equipment_items[:2])  # Better equipment chance
        elif "Ancient" in enemy_name or "BOSS" in enemy_name:
            possible_items = good_items + rare_items + equipment_items

        if not possible_items:
            possible_items = basic_items

        item_name = random.choice(possible_items)

        # Add to inventory
        char_data = self.game_manager.character_manager.character_data
        inventory = char_data.get("Inventory", {})
        inventory[item_name] = inventory.get(item_name, 0) + 1
        char_data["Inventory"] = inventory

        # Play item reward sound
        if item_name in equipment_items:
            self.sound_manager.play_sound("victory")  # Special sound for equipment
            reward_msg = f"Found rare {item_name}!"
        else:
            self.sound_manager.play_sound("item_pickup")
            reward_msg = f"Found {item_name}!"

        self.combat_manager.add_combat_log(reward_msg, LIGHT_BLUE)

    def end_combat(self, result):
        """End combat and return to world"""
        self.in_combat = False
        self.combat_result = result

        # Stop combat music and return to world sounds
        self.combat_manager.sound_manager.stop_music()

        # If victory, deactivate the enemy in the world
        if result == "victory" and hasattr(self.game_manager, 'current_enemy_obj'):
            self.game_manager.current_enemy_obj.active = False

        # Play world music if available
        try:
            if os.path.exists("Sounds/world_music.ogg"):
                self.sound_manager.play_music("Sounds/world_music.ogg")
        except Exception as e:
            print(f"Could not load world music: {e}")

    def update_world_sounds(self):
        """Update world sound effects"""
        # Update cooldowns
        if self.combat_entry_cooldown > 0:
            self.combat_entry_cooldown -= 1

        if self.post_combat_invulnerability > 0:
            self.post_combat_invulnerability -= 1

        # Footstep sounds when player moves
        if hasattr(self.game_manager, 'animated_player'):
            # Check if player is moving (simple detection based on animation state)
            if hasattr(self.game_manager.animated_player, 'state'):
                player_state = self.game_manager.animated_player.state
                if player_state in [0, 1, 2, 3]:  # Moving states
                    self.footstep_timer -= 1
                    if self.footstep_timer <= 0:
                        self.sound_manager.play_sound("footstep", 0.3)  # Quiet footsteps
                        self.footstep_timer = 20  # Reset timer

    def can_enter_combat(self):
        """Check if player can enter combat (not in cooldown)"""
        return (self.combat_entry_cooldown <= 0 and
                self.post_combat_invulnerability <= 0 and
                not self.in_combat)

    def play_world_sound(self, sound_name, volume=1.0):
        """Play a world sound effect"""
        self.sound_manager.play_sound(sound_name, volume)

    def draw_combat(self, screen):
        """Draw combat interface"""
        try:
            if self.in_combat:
                # print("Drawing combat manager")
                self.combat_manager.draw(screen)

                # Add combat status indicators
                self.draw_combat_hud(screen)
                # print("Combat drawing completed")
        except Exception as e:
            print(f"Error in draw_combat: {e}")
            import traceback
            traceback.print_exc()

            # Fallback drawing
            try:
                screen.fill((50, 0, 0))
                font = pygame.font.Font(None, 36)
                error_text = font.render("Combat Display Error", True, (255, 255, 255))
                text_rect = error_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
                screen.blit(error_text, text_rect)
            except:
                screen.fill((50, 0, 0))  # Ultimate fallback

    def draw_combat_hud(self, screen):
        """Draw additional HUD elements during combat"""
        # Draw escape instruction
        font = pygame.font.Font(None, 18)
        escape_text = font.render("ESC: Forfeit and flee combat", True, WHITE)

        # Add semi-transparent background
        text_rect = escape_text.get_rect()
        bg_rect = text_rect.inflate(10, 4)
        bg_rect.topleft = (5, 5)
        pygame.draw.rect(screen, (0, 0, 0, 128), bg_rect)

        screen.blit(escape_text, (10, 7))

        # Show current combat round or turn counter if desired
        if hasattr(self.combat_manager, 'combat_round'):
            round_text = font.render(f"Round: {self.combat_manager.combat_round}", True, WHITE)
            screen.blit(round_text, (10, 25))

        # Show post-combat invulnerability status on world screen
        if not self.in_combat and self.post_combat_invulnerability > 0:
            invuln_seconds = self.post_combat_invulnerability // 15  # Convert frames to seconds
            if invuln_seconds > 0:
                invuln_text = font.render(f"Combat Immunity: {invuln_seconds}s", True, GREEN)
                screen.blit(invuln_text, (10, screen.get_height() - 40))

    def draw_world_hud_additions(self, screen):
        """Draw additional HUD elements for the world screen"""
        font = pygame.font.Font(None, 18)

        # Show combat cooldown if active
        if self.combat_entry_cooldown > 0:
            cooldown_seconds = self.combat_entry_cooldown // 15
            cooldown_text = font.render(f"Combat Cooldown: {cooldown_seconds}s", True, YELLOW)
            screen.blit(cooldown_text, (10, screen.get_height() - 60))

        # Show post-combat immunity
        if self.post_combat_invulnerability > 0:
            immunity_seconds = self.post_combat_invulnerability // 15
            immunity_text = font.render(f"Combat Immunity: {immunity_seconds}s", True, GREEN)
            screen.blit(immunity_text, (10, screen.get_height() - 40))


def create_sound_directories():
    """Create sound directories and placeholder files"""
    sound_dir = "Sounds"
    if not os.path.exists(sound_dir):
        os.makedirs(sound_dir)
        print(f"Created {sound_dir} directory")

    # Create placeholder sound files (empty files for now)
    placeholder_sounds = [
        "sword_hit.wav", "sword_miss.wav", "spell_cast.wav", "fireball.wav",
        "heal.wav", "enemy_hit.wav", "enemy_death.wav", "player_hurt.wav",
        "critical_hit.wav", "magic_missile.wav", "potion_drink.wav",
        "run_away.wav", "victory.wav", "defeat.wav", "menu_select.wav",
        "menu_move.wav", "item_pickup.wav", "coin_pickup.wav",
        "footstep.wav", "door_open.wav", "battle_music.ogg", "world_music.ogg"
    ]

    for sound_file in placeholder_sounds:
        sound_path = os.path.join(sound_dir, sound_file)
        if not os.path.exists(sound_path):
            # Create empty placeholder file
            with open(sound_path, 'w') as f:
                f.write("")
            print(f"Created placeholder: {sound_path}")


def integrate_enhanced_combat_with_game_states(game_manager):
    """
    Enhanced integration function to modify existing game states for combat with sound/animation
    Call this from your main game initialization
    """

    # Create sound directories
    create_sound_directories()

    # Create enhanced combat integration
    combat_integration = EnhancedCombatIntegration(game_manager)
    game_manager.combat_integration = combat_integration

    # Store original methods for modification
    original_check_collisions = game_manager.check_collisions
    original_draw_fight_screen = game_manager.draw_fight_screen
    original_handle_keypress = game_manager.handle_keypress
    original_update = game_manager.update
    original_draw_game_board = game_manager.draw_game_board

    def enhanced_check_collisions():
        """Enhanced collision detection with combat integration and cooldowns"""
        collision_type, collision_obj = original_check_collisions()

        if collision_type == "enemy" and collision_obj:
            # Check if we can enter combat (cooldowns, etc.)
            if combat_integration.can_enter_combat():
                collision_obj.active = False  # Remove from world temporarily
                game_manager.current_enemy_obj = collision_obj

                # Start enhanced combat
                if combat_integration.start_combat(collision_obj.enemy_data):
                    game_manager.current_state = GameState.FIGHT
                    return None, None  # No standard collision handling
            else:
                # Play sound to indicate cooldown
                combat_integration.play_world_sound("menu_select", 0.5)
                return None, None

        # Handle treasure pickup with sound
        elif collision_type == "treasure" and collision_obj:
            combat_integration.play_world_sound("coin_pickup", 0.8)
            return collision_type, collision_obj

        # Handle shop entry with sound
        elif collision_type == "shop" and collision_obj:
            combat_integration.play_world_sound("door_open", 0.6)
            return collision_type, collision_obj

        return collision_type, collision_obj

    def enhanced_draw_fight_screen():
        """Enhanced fight screen with advanced combat"""
        if (hasattr(game_manager, 'combat_integration') and
                game_manager.combat_integration.in_combat):
            game_manager.combat_integration.draw_combat(game_manager.screen)
        else:
            original_draw_fight_screen()

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

        # Add sound effects to menu navigation
        elif game_manager.current_state in [GameState.MAIN_MENU, GameState.CHARACTER_SELECT,
                                            GameState.STORE, GameState.INVENTORY]:
            if key in [pygame.K_UP, pygame.K_DOWN]:
                game_manager.combat_integration.play_world_sound("menu_move", 0.4)
            elif key == pygame.K_RETURN:
                game_manager.combat_integration.play_world_sound("menu_select", 0.6)

        # Call original handler for other states
        return original_handle_keypress(key)

    def enhanced_update():
        """Enhanced update with combat integration and world sounds"""
        # Call original update
        original_update()

        # Update combat if active
        if (hasattr(game_manager, 'combat_integration') and
                game_manager.combat_integration.in_combat):

            result = game_manager.combat_integration.update_combat()
            if result in ["victory", "defeat", "escaped"]:
                game_manager.current_state = GameState.GAME_BOARD

        # Update world sounds and cooldowns
        if hasattr(game_manager, 'combat_integration'):
            game_manager.combat_integration.update_world_sounds()

    def enhanced_draw_game_board():
        """Enhanced game board drawing with combat HUD additions"""
        # Call original draw method
        original_draw_game_board()

        # Add combat-related HUD elements
        if hasattr(game_manager, 'combat_integration'):
            game_manager.combat_integration.draw_world_hud_additions(game_manager.screen)

    # Replace methods with enhanced versions
    game_manager.check_collisions = enhanced_check_collisions
    game_manager.draw_fight_screen = enhanced_draw_fight_screen
    game_manager.handle_keypress = enhanced_handle_keypress
    game_manager.update = enhanced_update
    game_manager.draw_game_board = enhanced_draw_game_board

    return combat_integration


def setup_enhanced_audio_system(game_manager):
    """
    Setup enhanced audio system with background music and ambient sounds
    """
    if not hasattr(game_manager, 'combat_integration'):
        return

    sound_manager = game_manager.combat_integration.sound_manager

    # Set up context-sensitive music
    def play_contextual_music():
        if game_manager.current_state == GameState.MAIN_MENU:
            try:
                if os.path.exists("Sounds/menu_music.ogg"):
                    sound_manager.play_music("Sounds/menu_music.ogg")
            except:
                pass
        elif game_manager.current_state == GameState.GAME_BOARD:
            try:
                if os.path.exists("Sounds/world_music.ogg"):
                    sound_manager.play_music("Sounds/world_music.ogg")
            except:
                pass
        elif game_manager.current_state == GameState.STORE:
            try:
                if os.path.exists("Sounds/shop_music.ogg"):
                    sound_manager.play_music("Sounds/shop_music.ogg")
            except:
                pass

    # Store original state change logic to add music transitions
    original_set_state = getattr(game_manager, 'set_current_state', None)

    def enhanced_set_state(new_state):
        if original_set_state:
            original_set_state(new_state)
        else:
            game_manager.current_state = new_state

        # Play appropriate music for new state
        play_contextual_music()

    game_manager.set_current_state = enhanced_set_state

    # Play initial music
    play_contextual_music()
