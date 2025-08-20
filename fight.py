"""
Combat Functions for Magitech RPG
Enhanced combat mechanics with proper stat calculations
"""

import random
import pygame
from typing import Dict, List, Tuple, Optional, Any


def roll_dice(num: int, sides: int) -> List[int]:
    """Roll dice and return list of results"""
    return [random.randint(1, sides) for _ in range(num)]


def calculate_modifier(stat_value: int) -> int:
    """Calculate D&D style ability modifier"""
    return (stat_value - 10) // 2


def gui_fight(player_name: str, player_aspect1: str, roll: List[int], demon_name: str,
              demon_hit_points: int, demon_aspect1: str, player_hit_points: int,
              mana_level: int, weapon_level: int, player_level: int,
              player_stats: Optional[Dict] = None) -> Tuple[int, int, str, int, int, str, str, str, str]:
    """
    Enhanced combat function with proper stat calculations
    Returns: (xp, new_enemy_hp, damage_type, new_player_hp, new_mana,
              action_message, damage_message, enemy_status, xp_message)
    """
    # Get player stats for combat calculations
    stats = player_stats or {}
    strength = stats.get('strength', 10)
    dexterity = stats.get('dexterity', 10)
    constitution = stats.get('constitution', 10)
    intelligence = stats.get('intelligence', 10)
    wisdom = stats.get('wisdom', 10)
    charisma = stats.get('charisma', 10)
    armor_class = stats.get('armor_class', 10)

    # Calculate stat modifiers
    str_mod = calculate_modifier(strength)
    dex_mod = calculate_modifier(dexterity)
    con_mod = calculate_modifier(constitution)
    int_mod = calculate_modifier(intelligence)
    wis_mod = calculate_modifier(wisdom)
    cha_mod = calculate_modifier(charisma)

    # Enhanced damage calculation with stats
    base_damage = random.randint(8, 20)

    # Weapon level bonus
    weapon_bonus = weapon_level * 3

    # Stat bonuses for combat
    strength_bonus = max(0, str_mod * 2)  # Strength increases physical damage
    magic_bonus = max(0, int_mod * 1.5)  # Intelligence increases magical damage
    level_bonus = player_level * 2  # Level scaling

    # Calculate total damage
    total_damage = int(base_damage + weapon_bonus + strength_bonus + magic_bonus + level_bonus)

    # Apply damage
    new_enemy_hp = max(0, demon_hit_points - total_damage)
    new_player_hp = player_hit_points

    # Mana cost with wisdom modifier (wisdom reduces mana cost)
    base_mana_cost = max(1, player_level // 2)
    mana_cost = max(1, base_mana_cost - max(0, wis_mod))
    new_mana = max(0, mana_level - mana_cost)

    # XP calculation with enhanced factors
    if new_enemy_hp <= 0:
        xp_dice = roll_dice(2, 6)  # Roll 2d6 for XP
        level_multiplier = max(1, demon_hit_points // 25)  # Higher HP enemies give more XP
        intelligence_bonus = max(0, int_mod)  # Intelligence gives XP bonus
        xp = (sum(xp_dice) * 5 * level_multiplier) + (intelligence_bonus * 5)
    else:
        xp = 0

    # Combat messages with stat information
    damage_breakdown = f"Base: {base_damage}, Weapon: {weapon_bonus}, Str: {strength_bonus}, Magic: {int(magic_bonus)}, Level: {level_bonus}"

    return (xp, new_enemy_hp, "fire", new_player_hp, new_mana,
            f"{player_name} attacks with enhanced power!",
            f"Deals {total_damage} damage! ({damage_breakdown})",
            f"Enemy has {new_enemy_hp} HP left",
            f"Gained {xp} XP! (Rolled {xp_dice if new_enemy_hp <= 0 else 'N/A'})")


def gui_enemy_fight(player_hit_points: int, roll: List[int], player_aspect1: str,
                    player_name: str, magic_type: str, demon_name: str,
                    demon_hit_points: int, demon_aspect1: str, mana_level: int,
                    player_stats: Optional[Dict] = None) -> Tuple[int, int, str]:
    """
    Enhanced enemy combat function that considers player's armor class
    Returns: (new_player_hp, new_mana, combat_message)
    """
    # Get player defensive stats
    stats = player_stats or {}
    armor_class = stats.get('armor_class', 10)
    constitution = stats.get('constitution', 10)
    dexterity = stats.get('dexterity', 10)

    # Calculate defensive modifiers
    con_mod = calculate_modifier(constitution)
    dex_mod = calculate_modifier(dexterity)

    # Enemy attack roll vs player AC
    enemy_attack_roll = random.randint(1, 20) + (demon_hit_points // 25)  # Enemy level bonus

    if enemy_attack_roll >= armor_class:
        # Hit! Calculate damage
        base_damage = random.randint(5, 15)
        enemy_level = max(1, demon_hit_points // 25)
        level_bonus = enemy_level * 2
        total_damage = base_damage + level_bonus

        # Constitution reduces damage taken
        damage_reduction = max(0, con_mod)
        final_damage = max(1, total_damage - damage_reduction)  # Minimum 1 damage

        new_player_hp = max(0, player_hit_points - final_damage)
        message = f"{demon_name} hits for {final_damage} damage! (AC: {armor_class}, Reduced by {damage_reduction})"
    else:
        # Miss!
        new_player_hp = player_hit_points
        final_damage = 0
        message = f"{demon_name} attacks but misses! (Rolled {enemy_attack_roll} vs AC {armor_class})"

    return (new_player_hp, mana_level, message)


def calculate_spell_damage(spell_name: str, caster_level: int, intelligence: int) -> Dict[str, Any]:
    """Calculate spell damage and effects"""
    int_mod = calculate_modifier(intelligence)

    spell_data = {
        'fireball': {
            'damage_dice': (3, 6),  # 3d6
            'damage_type': 'fire',
            'int_scaling': True,
            'level_scaling': True
        },
        'magic_missile': {
            'damage_dice': (1, 4),  # 1d4+1 per missile
            'damage_bonus': 1,
            'damage_type': 'force',
            'missiles': min(5, 1 + (caster_level // 2)),
            'int_scaling': False,
            'level_scaling': False
        },
        'lightning_bolt': {
            'damage_dice': (6, 6),  # 6d6
            'damage_type': 'lightning',
            'int_scaling': True,
            'level_scaling': True
        },
        'ice_shard': {
            'damage_dice': (2, 8),  # 2d8
            'damage_type': 'cold',
            'int_scaling': True,
            'level_scaling': True,
            'special': 'slow'
        }
    }

    if spell_name not in spell_data:
        return {'damage': 0, 'type': 'none', 'message': 'Unknown spell'}

    spell = spell_data[spell_name]
    dice_count, dice_sides = spell['damage_dice']

    # Roll base damage
    damage_rolls = roll_dice(dice_count, dice_sides)
    base_damage = sum(damage_rolls)

    # Add bonuses
    total_damage = base_damage

    if spell.get('damage_bonus'):
        total_damage += spell['damage_bonus']

    if spell.get('int_scaling'):
        total_damage += int_mod

    if spell.get('level_scaling'):
        total_damage += caster_level // 2

    # Handle special cases
    if spell_name == 'magic_missile':
        missiles = spell['missiles']
        total_damage *= missiles
        damage_message = f"Fires {missiles} missiles for {total_damage} total force damage!"
    else:
        damage_message = f"Deals {total_damage} {spell['damage_type']} damage!"

    return {
        'damage': total_damage,
        'type': spell['damage_type'],
        'message': damage_message,
        'rolls': damage_rolls,
        'special': spell.get('special'),
        'missiles': spell.get('missiles', 1)
    }


def calculate_healing(spell_name: str, caster_level: int, wisdom: int) -> Dict[str, Any]:
    """Calculate healing spell effects"""
    wis_mod = calculate_modifier(wisdom)

    healing_spells = {
        'cure_light_wounds': {
            'healing_dice': (1, 8),  # 1d8
            'wis_scaling': True,
            'level_scaling': False
        },
        'cure_moderate_wounds': {
            'healing_dice': (2, 8),  # 2d8
            'wis_scaling': True,
            'level_scaling': True
        },
        'heal': {
            'healing_dice': (6, 8),  # 6d8
            'wis_scaling': True,
            'level_scaling': True
        },
        'regeneration': {
            'healing_dice': (3, 8),  # 3d8
            'wis_scaling': True,
            'level_scaling': True,
            'special': 'regen'
        }
    }

    if spell_name not in healing_spells:
        return {'healing': 0, 'message': 'Unknown healing spell'}

    spell = healing_spells[spell_name]
    dice_count, dice_sides = spell['healing_dice']

    # Roll base healing
    healing_rolls = roll_dice(dice_count, dice_sides)
    base_healing = sum(healing_rolls)

    # Add bonuses
    total_healing = base_healing

    if spell.get('wis_scaling'):
        total_healing += wis_mod

    if spell.get('level_scaling'):
        total_healing += caster_level // 3

    healing_message = f"Heals {total_healing} hit points!"

    return {
        'healing': total_healing,
        'message': healing_message,
        'rolls': healing_rolls,
        'special': spell.get('special')
    }


def calculate_critical_hit(attack_roll: int, damage: int, weapon_type: str = 'sword') -> Tuple[bool, int]:
    """Calculate if attack is critical hit and apply multiplier"""
    # Critical hit thresholds by weapon type
    crit_thresholds = {
        'sword': 20,
        'dagger': 19,  # 19-20 crit range
        'axe': 20,
        'bow': 20,
        'crossbow': 19,
        'staff': 20
    }

    # Critical multipliers by weapon type
    crit_multipliers = {
        'sword': 2,
        'dagger': 2,
        'axe': 3,  # Higher multiplier for axes
        'bow': 3,
        'crossbow': 2,
        'staff': 2
    }

    threshold = crit_thresholds.get(weapon_type, 20)
    multiplier = crit_multipliers.get(weapon_type, 2)

    if attack_roll >= threshold:
        return True, damage * multiplier

    return False, damage


def apply_status_effects(target: Dict, effects: List[str], duration: int = 3) -> Dict:
    """Apply status effects to target"""
    if 'status_effects' not in target:
        target['status_effects'] = {}

    for effect in effects:
        target['status_effects'][effect] = duration

    return target


def process_status_effects(character: Dict) -> Dict:
    """Process ongoing status effects"""
    if 'status_effects' not in character:
        return character

    effects_to_remove = []
    messages = []

    for effect, duration in character['status_effects'].items():
        if duration <= 0:
            effects_to_remove.append(effect)
            continue

        # Apply effect
        if effect == 'poison':
            damage = random.randint(1, 4)
            character['hit_points'] = max(0, character.get('hit_points', 100) - damage)
            messages.append(f"Poison deals {damage} damage!")
        elif effect == 'regen':
            healing = random.randint(1, 6)
            max_hp = character.get('max_hit_points', 100)
            character['hit_points'] = min(max_hp, character.get('hit_points', 100) + healing)
            messages.append(f"Regeneration heals {healing} hit points!")
        elif effect == 'slow':
            messages.append("Movement is slowed!")
        elif effect == 'haste':
            messages.append("Movement is hastened!")

        # Reduce duration
        character['status_effects'][effect] = duration - 1

    # Remove expired effects
    for effect in effects_to_remove:
        del character['status_effects'][effect]
        messages.append(f"{effect.capitalize()} effect has ended.")

    return character


def calculate_armor_class(character: Dict) -> int:
    """Calculate character's armor class"""
    base_ac = 10

    # Dexterity modifier
    dex = character.get('stats', {}).get('dexterity', 10)
    dex_mod = calculate_modifier(dex)

    # Armor bonus
    armor_bonus = character.get('armor_bonus', 0)

    # Shield bonus
    shield_bonus = character.get('shield_bonus', 0)

    # Natural armor
    natural_armor = character.get('natural_armor', 0)

    # Magical bonuses
    magic_bonus = character.get('ac_magic_bonus', 0)

    total_ac = base_ac + dex_mod + armor_bonus + shield_bonus + natural_armor + magic_bonus

    return max(1, total_ac)  # Minimum AC of 1


def calculate_attack_bonus(character: Dict, weapon_type: str = 'melee') -> int:
    """Calculate character's attack bonus"""
    base_attack = character.get('level', 1) // 2  # Base attack progression

    # Ability modifier
    if weapon_type in ['bow', 'crossbow', 'thrown']:
        # Ranged weapons use dexterity
        ability = character.get('stats', {}).get('dexterity', 10)
    else:
        # Melee weapons use strength
        ability = character.get('stats', {}).get('strength', 10)

    ability_mod = calculate_modifier(ability)

    # Weapon enhancement bonus
    weapon_bonus = character.get('weapon_enhancement', 0)

    # Proficiency bonus (if proficient with weapon)
    proficiency_bonus = 2 if character.get('weapon_proficiencies', {}).get(weapon_type, False) else 0

    total_bonus = base_attack + ability_mod + weapon_bonus + proficiency_bonus

    return total_bonus


def get_spell_list(character_class: str, level: int) -> List[Dict]:
    """Get available spells for character class and level"""
    spell_lists = {
        'wizard': {
            1: ['magic_missile', 'shield', 'burning_hands'],
            2: ['scorching_ray', 'mirror_image', 'web'],
            3: ['fireball', 'lightning_bolt', 'haste'],
            4: ['ice_storm', 'wall_of_fire', 'polymorph'],
            5: ['cone_of_cold', 'cloudkill', 'teleport']
        },
        'cleric': {
            1: ['cure_light_wounds', 'bless', 'command'],
            2: ['cure_moderate_wounds', 'hold_person', 'spiritual_weapon'],
            3: ['cure_serious_wounds', 'dispel_magic', 'prayer'],
            4: ['cure_critical_wounds', 'freedom_of_movement', 'divine_power'],
            5: ['heal', 'flame_strike', 'raise_dead']
        },
        'sorcerer': {
            1: ['magic_missile', 'shield', 'color_spray'],
            2: ['scorching_ray', 'blur', 'invisibility'],
            3: ['fireball', 'haste', 'fly'],
            4: ['ice_storm', 'greater_invisibility', 'stoneskin'],
            5: ['cone_of_cold', 'teleport', 'wall_of_force']
        }
    }

    available_spells = []
    class_spells = spell_lists.get(character_class.lower(), {})

    for spell_level in range(1, min(level // 2 + 1, 6)):
        if spell_level in class_spells:
            for spell_name in class_spells[spell_level]:
                available_spells.append({
                    'name': spell_name,
                    'level': spell_level,
                    'school': get_spell_school(spell_name)
                })

    return available_spells


def get_spell_school(spell_name: str) -> str:
    """Get the school of magic for a spell"""
    schools = {
        'magic_missile': 'evocation',
        'fireball': 'evocation',
        'lightning_bolt': 'evocation',
        'ice_storm': 'evocation',
        'cone_of_cold': 'evocation',
        'cure_light_wounds': 'conjuration',
        'cure_moderate_wounds': 'conjuration',
        'heal': 'conjuration',
        'shield': 'abjuration',
        'haste': 'transmutation',
        'polymorph': 'transmutation',
        'invisibility': 'illusion',
        'mirror_image': 'illusion',
        'web': 'conjuration',
        'teleport': 'conjuration'
    }

    return schools.get(spell_name, 'universal')


def calculate_saving_throw(character: Dict, save_type: str, dc: int) -> Tuple[bool, int, str]:
    """
    Calculate saving throw
    save_type: 'fortitude', 'reflex', 'will'
    Returns: (success, roll_result, message)
    """
    # Base save progression (simplified)
    level = character.get('level', 1)
    base_save = level // 3

    # Ability modifier based on save type
    if save_type == 'fortitude':
        ability = character.get('stats', {}).get('constitution', 10)
    elif save_type == 'reflex':
        ability = character.get('stats', {}).get('dexterity', 10)
    elif save_type == 'will':
        ability = character.get('stats', {}).get('wisdom', 10)
    else:
        ability = 10

    ability_mod = calculate_modifier(ability)

    # Roll d20
    roll = random.randint(1, 20)

    # Calculate total
    total = roll + base_save + ability_mod

    # Check for success
    success = total >= dc

    message = f"{save_type.capitalize()} save: {roll} + {base_save + ability_mod} = {total} vs DC {dc}"
    if success:
        message += " (Success!)"
    else:
        message += " (Failed!)"

    return success, total, message


class CombatManager:
    """Manages combat encounters and turn order"""

    def __init__(self):
        self.participants = []
        self.turn_order = []
        self.current_turn = 0
        self.round_number = 1
        self.combat_active = False

    def start_combat(self, players: List[Dict], enemies: List[Dict]):
        """Start combat with initiative rolls"""
        self.participants = []
        self.turn_order = []
        self.current_turn = 0
        self.round_number = 1
        self.combat_active = True

        # Add players
        for player in players:
            initiative = self.roll_initiative(player)
            self.participants.append({
                'type': 'player',
                'data': player,
                'initiative': initiative,
                'name': player.get('Name', 'Player')
            })

        # Add enemies
        for enemy in enemies:
            initiative = self.roll_initiative(enemy)
            self.participants.append({
                'type': 'enemy',
                'data': enemy,
                'initiative': initiative,
                'name': enemy.get('name', 'Enemy')
            })

        # Sort by initiative (highest first)
        self.participants.sort(key=lambda x: x['initiative'], reverse=True)
        self.turn_order = [p['name'] for p in self.participants]

    def roll_initiative(self, character: Dict) -> int:
        """Roll initiative for character"""
        dex = character.get('stats', {}).get('dexterity', 10)
        dex_mod = calculate_modifier(dex)
        roll = random.randint(1, 20)
        return roll + dex_mod

    def get_current_participant(self) -> Optional[Dict]:
        """Get current turn participant"""
        if not self.combat_active or not self.participants:
            return None
        return self.participants[self.current_turn]

    def advance_turn(self):
        """Advance to next turn"""
        if not self.combat_active:
            return

        self.current_turn = (self.current_turn + 1) % len(self.participants)

        # New round if we've cycled through all participants
        if self.current_turn == 0:
            self.round_number += 1

    def remove_participant(self, name: str):
        """Remove participant from combat (death, flee, etc.)"""
        for i, participant in enumerate(self.participants):
            if participant['name'] == name:
                # Adjust current turn if necessary
                if i < self.current_turn:
                    self.current_turn -= 1
                elif i == self.current_turn and self.current_turn >= len(self.participants) - 1:
                    self.current_turn = 0

                self.participants.pop(i)
                self.turn_order.remove(name)
                break

        # Check if combat should end
        if self.should_end_combat():
            self.end_combat()

    def should_end_combat(self) -> bool:
        """Check if combat should end"""
        player_count = sum(1 for p in self.participants if p['type'] == 'player')
        enemy_count = sum(1 for p in self.participants if p['type'] == 'enemy')

        return player_count == 0 or enemy_count == 0

    def end_combat(self):
        """End combat"""
        self.combat_active = False
        self.participants = []
        self.turn_order = []
        self.current_turn = 0
        self.round_number = 1

    def get_combat_status(self) -> Dict:
        """Get current combat status"""
        return {
            'active': self.combat_active,
            'round': self.round_number,
            'current_turn': self.current_turn,
            'turn_order': self.turn_order,
            'current_participant': self.get_current_participant()
        }
