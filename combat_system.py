"""
Enhanced Combat System for Magitech RPG
Handles turn-based combat mechanics
"""

import random
import time
import pygame
from typing import Dict, List, Optional, Tuple, Any


class CombatSystem:
    def __init__(self, network_manager):
        self.network_manager = network_manager
        self.current_combat = None
        self.combat_ui_visible = False
        self.selected_action = None
        self.action_target = None

        # Combat state
        self.player_stats = {}
        self.enemy_stats = {}
        self.turn_timer = 0
        self.turn_timeout = 30  # 30 seconds per turn

        # UI elements
        self.action_buttons = []
        self.combat_log = []
        self.max_log_entries = 10

        # Animation system
        self.animations = []
        self.damage_numbers = []

    def start_combat(self, enemy_data: Dict) -> bool:
        """Start a new combat encounter"""
        if not self.network_manager.is_in_session():
            return False

        # Prepare enemy data
        prepared_enemy = self.prepare_enemy_data(enemy_data)

        success, data = self.network_manager.start_combat(prepared_enemy)
        if success:
            self.current_combat = data.get('combat_data', {})
            self.combat_ui_visible = True
            self.turn_timer = time.time()

            self.add_combat_log(f"Combat started against {prepared_enemy.get('name', 'Enemy')}!")
            return True

        return False

    def prepare_enemy_data(self, enemy_data: Dict) -> Dict:
        """Prepare enemy data for combat"""
        # Ensure enemy has all necessary stats
        default_enemy = {
            'name': 'Goblin',
            'level': 1,
            'hit_points': 25,
            'max_hit_points': 25,
            'armor_class': 12,
            'attack_bonus': 2,
            'damage_dice': '1d6',
            'damage_bonus': 1,
            'abilities': {
                'strength': 10,
                'dexterity': 12,
                'constitution': 10,
                'intelligence': 8,
                'wisdom': 10,
                'charisma': 8
            }
        }

        # Merge provided data with defaults
        for key, value in default_enemy.items():
            if key not in enemy_data:
                enemy_data[key] = value

        return enemy_data

    def process_turn(self, action: str, action_data: Dict = None) -> bool:
        """Process player's turn action"""
        if not self.network_manager.is_in_combat():
            return False

        if not self.network_manager.get_my_turn():
            self.add_combat_log("It's not your turn!")
            return False

        # Send action to server
        success, data = self.network_manager.combat_action(action, action_data)
        if success:
            self.add_combat_log(f"You used {action}!")
            self.selected_action = None
            self.action_target = None
            self.turn_timer = time.time()
            return True

        return False

    def process_attack(self, target_data: Dict = None) -> bool:
        """Process attack action"""
        # Get player's character data
        character = self.network_manager.character_data
        if not character:
            return False

        # Calculate attack damage
        damage_data = self.calculate_attack_damage(character)

        action_data = {
            'target': 'enemy',
            'damage': damage_data['total_damage'],
            'damage_type': damage_data['damage_type'],
            'hit_roll': damage_data['hit_roll'],
            'damage_breakdown': damage_data['breakdown']
        }

        return self.process_turn('attack', action_data)

    def calculate_attack_damage(self, character: Dict) -> Dict:
        """Calculate attack damage based on character stats"""
        # Get character stats
        stats = character.get('stats', {})
        strength = stats.get('strength', 10)
        weapon_level = character.get('weapon_level', 1)
        player_level = character.get('level', 1)

        # Calculate modifiers
        str_mod = (strength - 10) // 2

        # Roll for hit
        hit_roll = random.randint(1, 20)

        # Calculate damage
        base_damage = random.randint(1, 8)  # 1d8
        weapon_bonus = weapon_level * 2
        strength_bonus = max(0, str_mod)
        level_bonus = player_level

        total_damage = base_damage + weapon_bonus + strength_bonus + level_bonus

        return {
            'hit_roll': hit_roll,
            'total_damage': total_damage,
            'damage_type': 'physical',
            'breakdown': {
                'base': base_damage,
                'weapon': weapon_bonus,
                'strength': strength_bonus,
                'level': level_bonus
            }
        }

    def process_spell(self, spell_name: str) -> bool:
        """Process spell casting"""
        character = self.network_manager.character_data
        if not character:
            return False

        # Check mana
        current_mana = character.get('mana_level', 0)
        spell_cost = self.get_spell_cost(spell_name)

        if current_mana < spell_cost:
            self.add_combat_log("Not enough mana!")
            return False

        # Calculate spell effects
        spell_data = self.calculate_spell_effects(character, spell_name)

        action_data = {
            'spell_name': spell_name,
            'mana_cost': spell_cost,
            'effects': spell_data
        }

        return self.process_turn('spell', action_data)

    def get_spell_cost(self, spell_name: str) -> int:
        """Get mana cost for spell"""
        spell_costs = {
            'fireball': 8,
            'healing_light': 6,
            'magic_missile': 4,
            'shield': 3,
            'heal': 5
        }
        return spell_costs.get(spell_name, 3)

    def calculate_spell_effects(self, character: Dict, spell_name: str) -> Dict:
        """Calculate spell effects"""
        stats = character.get('stats', {})
        intelligence = stats.get('intelligence', 10)
        player_level = character.get('level', 1)

        int_mod = (intelligence - 10) // 2

        effects = {}

        if spell_name == 'fireball':
            damage = random.randint(6, 18) + int_mod + player_level  # 3d6 + mods
            effects = {'damage': damage, 'damage_type': 'fire', 'target': 'enemy'}
        elif spell_name == 'healing_light':
            healing = random.randint(8, 24) + int_mod  # 3d8 + int mod
            effects = {'healing': healing, 'target': 'self'}
        elif spell_name == 'magic_missile':
            missiles = min(3, (player_level // 2) + 1)
            damage_per_missile = random.randint(1, 4) + 1  # 1d4+1
            total_damage = missiles * damage_per_missile
            effects = {'damage': total_damage, 'damage_type': 'force', 'target': 'enemy', 'missiles': missiles}

        return effects

    def process_item_use(self, item_name: str) -> bool:
        """Process item usage"""
        character = self.network_manager.character_data
        if not character:
            return False

        # Check if item is available in inventory
        inventory = character.get('inventory', [])
        if not any(item['name'] == item_name for item in inventory):
            self.add_combat_log(f"You don't have {item_name}!")
            return False

        # Calculate item effects
        item_effects = self.calculate_item_effects(item_name)

        action_data = {
            'item_name': item_name,
            'effects': item_effects
        }

        return self.process_turn('item', action_data)

    def calculate_item_effects(self, item_name: str) -> Dict:
        """Calculate item effects"""
        item_effects = {
            'health_potion': {'healing': random.randint(15, 25), 'target': 'self'},
            'mana_potion': {'mana_restore': random.randint(10, 20), 'target': 'self'},
            'bomb': {'damage': random.randint(12, 20), 'damage_type': 'explosive', 'target': 'enemy'},
            'smoke_bomb': {'effect': 'blind', 'duration': 2, 'target': 'enemy'}
        }
        return item_effects.get(item_name, {})

    def end_combat(self, result: str = 'victory') -> bool:
        """End the current combat"""
        if not self.network_manager.is_in_combat():
            return False

        success, data = self.network_manager.end_combat(result)
        if success:
            self.current_combat = None
            self.combat_ui_visible = False
            self.selected_action = None
            self.action_target = None
            self.combat_log.clear()
            self.animations.clear()
            self.damage_numbers.clear()

            self.add_combat_log(f"Combat ended: {result}")
            return True

        return False

    def update(self, dt: float):
        """Update combat system"""
        if not self.combat_ui_visible:
            return

        # Update animations
        self.update_animations(dt)

        # Update damage numbers
        self.update_damage_numbers(dt)

        # Check for new activities
        self.process_combat_activities()

        # Check turn timeout
        if self.network_manager.get_my_turn():
            time_left = self.turn_timeout - (time.time() - self.turn_timer)
            if time_left <= 0:
                # Auto-skip turn or take default action
                self.process_turn('defend')

    def process_combat_activities(self):
        """Process recent combat activities"""
        activities = self.network_manager.get_recent_activities('combat_action', 5)
        activities.extend(self.network_manager.get_recent_activities('combat_started', 5))
        activities.extend(self.network_manager.get_recent_activities('combat_ended', 5))
        activities.extend(self.network_manager.get_recent_activities('enemy_action', 5))
        activities.extend(self.network_manager.get_recent_activities('turn_changed', 5))

        for activity in activities:
            self.process_activity(activity)

    def process_activity(self, activity: Dict):
        """Process a single combat activity"""
        activity_type = activity.get('type')
        data = activity.get('data', {})
        username = activity.get('username', 'Unknown')

        if activity_type == 'combat_action':
            action = data.get('action', 'unknown')
            self.add_combat_log(f"{username} used {action}")

            if 'damage' in data:
                self.add_damage_number(data['damage'], 'damage')
            if 'healing' in data:
                self.add_damage_number(data['healing'], 'healing')

        elif activity_type == 'enemy_action':
            enemy_name = data.get('enemy_name', 'Enemy')
            target_name = data.get('target_player_name', 'Someone')
            damage = data.get('damage_dealt', 0)

            self.add_combat_log(f"{enemy_name} attacks {target_name} for {damage} damage!")
            if target_name == self.network_manager.username:
                self.add_damage_number(damage, 'damage_taken')

        elif activity_type == 'turn_changed':
            new_turn_name = data.get('new_turn_name', 'Unknown')
            if data.get('new_turn_player') == self.network_manager.user_id:
                self.add_combat_log("It's your turn!")
                self.turn_timer = time.time()
            else:
                self.add_combat_log(f"It's {new_turn_name}'s turn")

        elif activity_type == 'combat_ended':
            result = data.get('result', 'unknown')
            self.add_combat_log(f"Combat ended: {result}")

    def add_combat_log(self, message: str):
        """Add message to combat log"""
        self.combat_log.append({
            'message': message,
            'timestamp': time.time()
        })

        # Keep only recent entries
        if len(self.combat_log) > self.max_log_entries:
            self.combat_log.pop(0)

    def add_damage_number(self, amount: int, damage_type: str):
        """Add floating damage number"""
        self.damage_numbers.append({
            'amount': amount,
            'type': damage_type,
            'x': 400,  # Center of screen
            'y': 200,
            'life': 2.0,
            'max_life': 2.0
        })

    def update_animations(self, dt: float):
        """Update combat animations"""
        # Update existing animations
        for animation in self.animations[:]:
            animation['life'] -= dt
            if animation['life'] <= 0:
                self.animations.remove(animation)

    def update_damage_numbers(self, dt: float):
        """Update floating damage numbers"""
        for number in self.damage_numbers[:]:
            number['life'] -= dt
            number['y'] -= 50 * dt  # Float upward

            if number['life'] <= 0:
                self.damage_numbers.remove(number)

    def render_combat_ui(self, screen: pygame.Surface, font: pygame.font.Font):
        """Render combat UI"""
        if not self.combat_ui_visible:
            return

        # Combat panel background
        combat_rect = pygame.Rect(50, 400, 700, 150)
        pygame.draw.rect(screen, (30, 30, 30), combat_rect)
        pygame.draw.rect(screen, (100, 100, 100), combat_rect, 2)

        # Turn indicator
        turn_info = self.network_manager.get_combat_turn_info()
        if turn_info.get('is_my_turn', False):
            turn_text = "YOUR TURN"
            turn_color = (0, 255, 0)
        else:
            current_turn = turn_info.get('current_turn', 'Unknown')
            if current_turn == 'ENEMY':
                turn_text = "ENEMY TURN"
                turn_color = (255, 0, 0)
            else:
                # Find username for current turn
                other_players = self.network_manager.other_players
                turn_player = other_players.get(current_turn, {})
                turn_username = turn_player.get('username', 'Player')
                turn_text = f"{turn_username.upper()}'S TURN"
                turn_color = (255, 255, 0)

        turn_surface = font.render(turn_text, True, turn_color)
        screen.blit(turn_surface, (60, 410))

        # Action buttons (only show on player's turn)
        if turn_info.get('is_my_turn', False):
            self.render_action_buttons(screen, font)

        # Combat log
        self.render_combat_log(screen, font)

        # Damage numbers
        self.render_damage_numbers(screen, font)

    def render_action_buttons(self, screen: pygame.Surface, font: pygame.font.Font):
        """Render combat action buttons"""
        buttons = [
            {'name': 'Attack', 'action': 'attack', 'color': (255, 100, 100)},
            {'name': 'Magic', 'action': 'magic', 'color': (100, 100, 255)},
            {'name': 'Item', 'action': 'item', 'color': (100, 255, 100)},
            {'name': 'Defend', 'action': 'defend', 'color': (200, 200, 200)}
        ]

        button_width = 120
        button_height = 30
        start_x = 60
        start_y = 450

        self.action_buttons.clear()

        for i, button in enumerate(buttons):
            x = start_x + i * (button_width + 10)
            y = start_y

            button_rect = pygame.Rect(x, y, button_width, button_height)
            self.action_buttons.append({
                'rect': button_rect,
                'action': button['action'],
                'name': button['name']
            })

            # Highlight selected action
            color = button['color']
            if self.selected_action == button['action']:
                color = tuple(min(255, c + 50) for c in color)

            pygame.draw.rect(screen, color, button_rect)
            pygame.draw.rect(screen, (255, 255, 255), button_rect, 2)

            text_surface = font.render(button['name'], True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=button_rect.center)
            screen.blit(text_surface, text_rect)

    def render_combat_log(self, screen: pygame.Surface, font: pygame.font.Font):
        """Render combat log"""
        log_start_y = 500
        for i, log_entry in enumerate(self.combat_log[-5:]):  # Show last 5 entries
            y = log_start_y + i * 20
            text_surface = font.render(log_entry['message'], True, (200, 200, 200))
            screen.blit(text_surface, (60, y))

    def render_damage_numbers(self, screen: pygame.Surface, font: pygame.font.Font):
        """Render floating damage numbers"""
        for number in self.damage_numbers:
            alpha = int(255 * (number['life'] / number['max_life']))

            if number['type'] == 'damage':
                color = (255, 100, 100)
                text = f"-{number['amount']}"
            elif number['type'] == 'damage_taken':
                color = (255, 50, 50)
                text = f"-{number['amount']}"
            elif number['type'] == 'healing':
                color = (100, 255, 100)
                text = f"+{number['amount']}"
            else:
                color = (255, 255, 255)
                text = str(number['amount'])

            # Create surface with alpha
            text_surface = font.render(text, True, color)
            text_surface.set_alpha(alpha)

            screen.blit(text_surface, (number['x'], number['y']))

    def handle_click(self, pos: Tuple[int, int]) -> bool:
        """Handle mouse click on combat UI"""
        if not self.combat_ui_visible or not self.network_manager.get_my_turn():
            return False

        # Check action button clicks
        for button in self.action_buttons:
            if button['rect'].collidepoint(pos):
                action = button['action']

                if action == 'attack':
                    self.process_attack()
                elif action == 'defend':
                    self.process_turn('defend')
                elif action == 'magic':
                    # For now, cast fireball - could expand to spell selection
                    self.process_spell('fireball')
                elif action == 'item':
                    # For now, use health potion - could expand to item selection
                    self.process_item_use('health_potion')

                return True

        return False

    def get_combat_status(self) -> Dict:
        """Get current combat status"""
        if not self.network_manager.is_in_combat():
            return {'in_combat': False}

        turn_info = self.network_manager.get_combat_turn_info()

        return {
            'in_combat': True,
            'is_my_turn': turn_info.get('is_my_turn', False),
            'current_turn': turn_info.get('current_turn'),
            'turn_order': turn_info.get('turn_order', []),
            'combat_session': self.network_manager.combat_session
        }
