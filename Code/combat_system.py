import pygame
import random
import math
from Code.ui_components import *


class CombatText:
    """Enhanced floating combat text with different types"""

    def __init__(self, x, y, text, text_type="damage", world_pos=None):
        self.x = x
        self.y = y
        self.text = str(text)
        self.text_type = text_type
        self.timer = 90  # Longer duration
        self.max_timer = 90
        self.font = pygame.font.Font(None, 32)
        self.world_pos = world_pos

        # Set color and movement based on text type
        self.colors = {
            "damage": (255, 100, 100),  # Red for damage dealt
            "player_damage": (255, 255, 100),  # Yellow for player taking damage
            "heal": (100, 255, 100),  # Green for healing
            "mana": (100, 150, 255),  # Blue for mana
            "miss": (200, 200, 200),  # Gray for misses
            "critical": (255, 255, 255),  # White for crits
            "spell": (255, 100, 255),  # Purple for spells
            "status": (255, 200, 100)  # Orange for status effects
        }

        self.color = self.colors.get(text_type, (255, 255, 255))
        self.alpha = 255

        # Different movement patterns
        if text_type == "critical":
            self.velocity_y = -4
            self.velocity_x = random.uniform(-2, 2)
            self.scale = 1.5
        elif text_type == "heal":
            self.velocity_y = -2
            self.velocity_x = 0
            self.scale = 1.2
        elif text_type == "miss":
            self.velocity_y = -1
            self.velocity_x = random.uniform(-3, 3)
            self.scale = 0.8
        else:
            self.velocity_y = -3
            self.velocity_x = random.uniform(-1, 1)
            self.scale = 1.0

    def update(self):
        """Update combat text animation"""
        self.timer -= 1
        self.y += self.velocity_y
        self.x += self.velocity_x

        # Fade out over time
        fade_ratio = self.timer / self.max_timer
        self.alpha = max(0, int(255 * fade_ratio))

        # Slow down vertical movement over time
        self.velocity_y *= 0.98
        self.velocity_x *= 0.95

        return self.timer > 0

    def draw(self, screen, camera=None):
        """Draw the combat text"""
        if camera and self.world_pos:
            screen_x, screen_y = camera.world_to_screen(self.world_pos[0], self.world_pos[1])
            draw_x = screen_x + (self.x - self.world_pos[0])
            draw_y = screen_y + (self.y - self.world_pos[1])
        else:
            draw_x = self.x
            draw_y = self.y

        # Scale font based on text type
        font_size = int(32 * self.scale)
        if font_size != 32:
            font = pygame.font.Font(None, font_size)
        else:
            font = self.font

        # Create text surface with outline for critical hits
        if self.text_type == "critical":
            # Draw outline
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        outline_surface = font.render(self.text, True, BLACK)
                        outline_surface.set_alpha(self.alpha)
                        screen.blit(outline_surface, (draw_x + dx, draw_y + dy))

        # Draw main text
        text_surface = font.render(self.text, True, self.color)
        text_surface.set_alpha(self.alpha)
        screen.blit(text_surface, (draw_x, draw_y))


class Spell:
    """Spell data structure"""

    def __init__(self, name, mana_cost, damage_min, damage_max, spell_type="damage",
                 description="", effect_chance=0, effect_type="", effect_value=0):
        self.name = name
        self.mana_cost = mana_cost
        self.damage_min = damage_min
        self.damage_max = damage_max
        self.spell_type = spell_type
        self.description = description
        self.effect_chance = effect_chance
        self.effect_type = effect_type
        self.effect_value = effect_value


class SpellManager:
    """Manages available spells based on character aspect"""

    def __init__(self):
        self.spell_library = {
            "fire": [
                Spell("Flame Bolt", 5, 8, 15, "damage", "Basic fire projectile"),
                Spell("Fireball", 12, 15, 25, "damage", "Explosive fire magic", 20, "burn", 3),
                Spell("Inferno", 25, 30, 45, "damage", "Devastating fire spell", 30, "burn", 5)
            ],
            "water": [
                Spell("Ice Shard", 4, 6, 12, "damage", "Sharp ice projectile"),
                Spell("Frost Blast", 10, 12, 20, "damage", "Freezing attack", 25, "freeze", 1),
                Spell("Blizzard", 22, 25, 40, "damage", "Overwhelming ice storm", 35, "freeze", 2)
            ],
            "dream": [
                Spell("Lightning Bolt", 6, 10, 18, "damage", "Electric shock"),
                Spell("Chain Lightning", 15, 18, 28, "damage", "Multi-target lightning", 15, "stun", 1),
                Spell("Thunder Storm", 28, 35, 50, "damage", "Massive electrical assault", 25, "stun", 2)
            ],
            "earth": [
                Spell("Stone Throw", 3, 5, 10, "damage", "Hurled rock"),
                Spell("Earth Spike", 8, 12, 18, "damage", "Piercing stone spear"),
                Spell("Earthquake", 20, 20, 35, "damage", "Ground-shaking force", 20, "knockdown", 1)
            ],
            "life": [
                Spell("Heal", 8, 15, 25, "heal", "Restore health"),
                Spell("Greater Heal", 15, 25, 40, "heal", "Major healing"),
                Spell("Holy Light", 10, 8, 15, "damage", "Damages undead, heals living", 30, "blind", 2)
            ],
            "void": [
                Spell("Shadow Bolt", 7, 12, 20, "damage", "Dark energy projectile"),
                Spell("Drain Life", 12, 10, 18, "drain", "Damage enemy, heal self", 0, "", 0),
                Spell("Soul Burn", 20, 25, 35, "damage", "Corrupting darkness", 25, "curse", 3)
            ]
        }

    def get_spells_for_aspect(self, aspect, level=1):
        """Get available spells for character aspect and level"""
        aspect_name = aspect.split('_')[0].lower() if aspect else "fire"
        spells = self.spell_library.get(aspect_name, self.spell_library["fire"])

        # Return spells based on level
        available_spells = []
        if level >= 1:
            available_spells.append(spells[0])  # Basic spell
        if level >= 3:
            available_spells.append(spells[1])  # Intermediate spell
        if level >= 5:
            available_spells.append(spells[2])  # Advanced spell

        return available_spells if available_spells else [spells[0]]


class CombatManager:
    """Advanced turn-based combat system"""

    def __init__(self, character_manager):
        self.character_manager = character_manager
        self.spell_manager = SpellManager()
        self.combat_texts = []
        self.combat_log = []

        # Combat state
        self.current_enemy = None
        self.player_turn = True
        self.combat_phase = "select_action"  # select_action, select_target, animating, enemy_turn
        self.selected_action = 0
        self.selected_spell = 0
        self.selected_item = 0

        # Combat options
        self.actions = ["Attack", "Cast Spell", "Use Item", "Run Away"]

        # Status effects
        self.player_status = {}
        self.enemy_status = {}

        # Animation timer
        self.animation_timer = 0
        self.action_delay = 0

        # UI fonts
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 20)

    def start_combat(self, enemy_data):
        """Initialize combat with an enemy"""
        self.current_enemy = enemy_data.copy()
        self.combat_texts.clear()
        self.combat_log.clear()
        self.player_status.clear()
        self.enemy_status.clear()
        self.player_turn = True
        self.combat_phase = "select_action"
        self.selected_action = 0
        self.animation_timer = 0

        # Add combat start message
        enemy_name = self.current_enemy.get("Name", "Enemy")
        self.add_combat_log(f"Combat begins with {enemy_name}!", WHITE)

    def add_combat_log(self, message, color=WHITE):
        """Add message to combat log"""
        self.combat_log.append((message, color))
        if len(self.combat_log) > 8:
            self.combat_log.pop(0)

    def add_combat_text(self, x, y, text, text_type="damage", world_pos=None):
        """Add floating combat text"""
        combat_text = CombatText(x, y, text, text_type, world_pos)
        self.combat_texts.append(combat_text)

    def calculate_damage(self, base_min, base_max, attacker_stats, defender_stats=None):
        """Calculate damage with stat modifiers"""
        # Base damage roll
        base_damage = random.randint(base_min, base_max)

        # Strength modifier for physical attacks
        str_bonus = max(0, (attacker_stats.get("strength", 10) - 10) // 2)

        # Critical hit chance based on dexterity
        dex = attacker_stats.get("dexterity", 10)
        crit_chance = max(5, (dex - 10) // 2 + 5)  # 5% base + dex modifier

        is_critical = random.randint(1, 100) <= crit_chance

        if is_critical:
            final_damage = int((base_damage + str_bonus) * 1.5)
            return final_damage, True
        else:
            return base_damage + str_bonus, False

    def calculate_spell_damage(self, spell, caster_stats, caster_level=1):
        """Calculate spell damage with intelligence/wisdom modifiers and level scaling - ENHANCED VERSION"""
        base_damage = random.randint(spell.damage_min, spell.damage_max)

        # Intelligence modifier for damage spells
        int_bonus = max(0, (caster_stats.get("intelligence", 10) - 10) // 2)

        # Wisdom modifier for healing spells
        wis_bonus = max(0, (caster_stats.get("wisdom", 10) - 10) // 2)

        # Level bonus - scales magic damage with character level
        level_bonus = max(0, (caster_level - 1) // 2)  # +1 damage every 2 levels

        print(
            f"DEBUG: Spell base damage: {base_damage}, INT bonus: {int_bonus}, WIS bonus: {wis_bonus}, Level bonus: {level_bonus}")

        if spell.spell_type == "heal":
            final_damage = base_damage + wis_bonus + level_bonus
            print(f"DEBUG: Heal spell final: {final_damage}")
            return final_damage, False
        elif spell.spell_type == "drain":
            final_damage = base_damage + int_bonus + level_bonus
            print(f"DEBUG: Drain spell final: {final_damage}")
            return final_damage, False
        else:
            # Critical hit chance for spells based on intelligence and level
            crit_chance = max(3, int_bonus + (caster_level // 5))  # Slight crit chance increase with level
            is_critical = random.randint(1, 100) <= crit_chance

            if is_critical:
                final_damage = int((base_damage + int_bonus + level_bonus) * 1.5)
                print(f"DEBUG: CRITICAL SPELL! Final damage: {final_damage}")
                return final_damage, True
            else:
                final_damage = base_damage + int_bonus + level_bonus
                print(f"DEBUG: Normal spell damage: {final_damage}")
                return final_damage, False

    def calculate_hit_chance(self, attacker_stats, defender_stats):
        """Calculate if attack hits based on stats - ENHANCED VERSION"""
        # Base hit chance
        base_hit = 75

        # Attacker dexterity bonus
        att_dex = attacker_stats.get("dexterity", 10)
        hit_bonus = (att_dex - 10) // 2

        # Defender AC penalty
        defender_ac = defender_stats.get("armor_class", 10)
        ac_penalty = (defender_ac - 10) * 2

        final_hit_chance = max(5, base_hit + hit_bonus - ac_penalty)

        roll = random.randint(1, 100)
        hit = roll <= final_hit_chance

        print(f"DEBUG: Hit calculation - Base: {base_hit}, DEX bonus: {hit_bonus}, AC penalty: {ac_penalty}")
        print(f"DEBUG: Final hit chance: {final_hit_chance}%, Roll: {roll}, Hit: {hit}")

        return hit

    def get_player_stats(self):
        """Get player stats for combat calculations - FIXED VERSION"""
        # First check if we have character manager and data
        if not self.character_manager:
            print("WARNING: No character manager available, using default stats")
            return {"strength": 10, "dexterity": 10, "constitution": 10,
                    "intelligence": 10, "wisdom": 10, "charisma": 10, "armor_class": 10}

        if not self.character_manager.character_data:
            print("WARNING: No character data available, using default stats")
            return {"strength": 10, "dexterity": 10, "constitution": 10,
                    "intelligence": 10, "wisdom": 10, "charisma": 10, "armor_class": 10}

        try:
            # Get stats using character manager methods
            stats = {
                "strength": self.character_manager.get_total_stat("strength"),
                "dexterity": self.character_manager.get_total_stat("dexterity"),
                "constitution": self.character_manager.get_total_stat("constitution"),
                "intelligence": self.character_manager.get_total_stat("intelligence"),
                "wisdom": self.character_manager.get_total_stat("wisdom"),
                "charisma": self.character_manager.get_total_stat("charisma"),
                "armor_class": self.character_manager.get_armor_class()
            }

            # Verify we got valid stats
            for stat_name, value in stats.items():
                if value is None or value < 1:
                    print(f"WARNING: Invalid {stat_name} value: {value}, using default 10")
                    stats[stat_name] = 10

            print(f"DEBUG: Player stats loaded: {stats}")
            return stats

        except Exception as e:
            print(f"ERROR getting player stats: {e}")
            # Fallback to reading directly from character data
            return self.get_stats_from_character_data()

    def get_stats_from_character_data(self):
        """Fallback method to get stats directly from character data"""
        char_data = self.character_manager.character_data

        # Base stats from character data
        base_stats = {
            "strength": char_data.get("Strength", 10),
            "dexterity": char_data.get("Dexterity", 10),
            "constitution": char_data.get("Constitution", 10),
            "intelligence": char_data.get("Intelligence", 10),
            "wisdom": char_data.get("Wisdom", 10),
            "charisma": char_data.get("Charisma", 10)
        }

        # Calculate AC from dexterity + equipment
        dex_bonus = max(0, (base_stats["dexterity"] - 10) // 2)
        base_ac = 10 + dex_bonus

        # Add equipment AC bonus if available
        equipment_ac = 0
        inventory = char_data.get("Inventory", {})
        for item_name, item_data in inventory.items():
            if isinstance(item_data, dict) and item_data.get("equipped", False):
                if "Armor_Class" in item_data:
                    equipment_ac += item_data["Armor_Class"]

        base_stats["armor_class"] = base_ac + equipment_ac

        print(f"DEBUG: Stats from character data: {base_stats}")
        return base_stats

    def get_enemy_stats(self):
        """Get enemy stats with difficulty scaling"""
        if not self.current_enemy:
            return {"strength": 10, "dexterity": 10, "constitution": 12,
                    "intelligence": 8, "wisdom": 8, "charisma": 6, "armor_class": 10}

        # Use the new enemy stats method if available
        if hasattr(self.character_manager, 'enemy_manager'):
            try:
                enemy_stats = self.character_manager.enemy_manager.get_enemy_stats_for_combat(self.current_enemy)
                print(f"DEBUG: Enemy stats with difficulty: {enemy_stats}")
                return enemy_stats
            except:
                pass

        # Fallback to basic enemy stats with scaling
        level = self.current_enemy.get("Level", 1)
        difficulty_mult = self.current_enemy.get("difficulty_multiplier", 1.0)

        # Apply difficulty multiplier to enemy stats
        base_bonus = int((level - 1) * difficulty_mult)

        enemy_stats = {
            "strength": 10 + base_bonus,
            "dexterity": 10 + base_bonus,
            "constitution": 12 + base_bonus,
            "intelligence": 8 + base_bonus,
            "wisdom": 8 + base_bonus,
            "charisma": 6,
            "armor_class": 10 + int(base_bonus * 0.5)
        }

        print(f"DEBUG: Enemy stats (fallback): {enemy_stats}")
        return enemy_stats

    def calculate_damage(self, base_min, base_max, attacker_stats, defender_stats=None):
        """Calculate damage with stat modifiers - ENHANCED VERSION"""
        # Base damage roll
        base_damage = random.randint(base_min, base_max)

        # Strength modifier for physical attacks
        str_bonus = max(0, (attacker_stats.get("strength", 10) - 10) // 2)

        print(f"DEBUG: Base damage: {base_damage}, STR bonus: {str_bonus} (STR: {attacker_stats.get('strength', 10)})")

        # Critical hit chance based on dexterity
        dex = attacker_stats.get("dexterity", 10)
        crit_chance = max(5, (dex - 10) // 2 + 5)  # 5% base + dex modifier

        print(f"DEBUG: Crit chance: {crit_chance}% (DEX: {dex})")

        is_critical = random.randint(1, 100) <= crit_chance

        if is_critical:
            final_damage = int((base_damage + str_bonus) * 1.5)
            print(f"DEBUG: CRITICAL HIT! Final damage: {final_damage}")
            return final_damage, True
        else:
            final_damage = base_damage + str_bonus
            print(f"DEBUG: Normal hit. Final damage: {final_damage}")
            return final_damage, False

    def player_attack(self):
        """Execute player's basic attack"""
        player_stats = self.get_player_stats()
        enemy_stats = self.get_enemy_stats()

        if self.calculate_hit_chance(player_stats, enemy_stats):
            damage, is_critical = self.calculate_damage(25, 45, player_stats, enemy_stats)  # Increased damage

            # Apply damage
            self.current_enemy["Hit_Points"] -= damage

            # Add combat text and log
            text_type = "critical" if is_critical else "damage"
            crit_text = "CRITICAL! " if is_critical else ""

            self.add_combat_text(400, 250, f"-{damage}", text_type)
            self.add_combat_log(f"{crit_text}You deal {damage} damage!", GREEN)

            return damage
        else:
            self.add_combat_text(400, 250, "MISS", "miss")
            self.add_combat_log("Your attack misses!", GRAY)
            return 0

    def player_cast_spell(self, spell):
        """Execute player's spell cast"""
        if not self.character_manager.character_data:
            return False

        current_mana = self.character_manager.character_data.get("Aspect1_Mana", 0)
        if current_mana < spell.mana_cost:
            self.add_combat_log("Not enough mana!", RED)
            return False

        # Consume mana
        self.character_manager.character_data["Aspect1_Mana"] -= spell.mana_cost

        player_stats = self.get_player_stats()
        damage, is_critical = self.calculate_spell_damage(spell, player_stats)

        if spell.spell_type == "heal":
            # Healing spell
            current_hp = self.character_manager.character_data.get("Hit_Points", 100)
            level = self.character_manager.character_data.get("Level", 1)
            max_hp = self.character_manager.get_max_hp_for_level(level)

            healed = min(damage, max_hp - current_hp)
            self.character_manager.character_data["Hit_Points"] += healed

            self.add_combat_text(200, 250, f"+{healed}", "heal")
            self.add_combat_log(f"You heal for {healed} HP!", GREEN)

        elif spell.spell_type == "drain":
            # Drain life spell
            self.current_enemy["Hit_Points"] -= damage

            # Heal player for half damage dealt
            current_hp = self.character_manager.character_data.get("Hit_Points", 100)
            level = self.character_manager.character_data.get("Level", 1)
            max_hp = self.character_manager.get_max_hp_for_level(level)

            healed = min(damage // 2, max_hp - current_hp)
            self.character_manager.character_data["Hit_Points"] += healed

            text_type = "critical" if is_critical else "spell"
            self.add_combat_text(400, 250, f"-{damage}", text_type)
            if healed > 0:
                self.add_combat_text(200, 250, f"+{healed}", "heal")

            crit_text = "CRITICAL! " if is_critical else ""
            self.add_combat_log(f"{crit_text}{spell.name} deals {damage} damage and heals {healed}!", PURPLE)

        else:
            # Damage spell
            self.current_enemy["Hit_Points"] -= damage

            text_type = "critical" if is_critical else "spell"
            crit_text = "CRITICAL! " if is_critical else ""

            self.add_combat_text(400, 250, f"-{damage}", text_type)
            self.add_combat_log(f"{crit_text}{spell.name} deals {damage} damage!", PURPLE)

            # Apply status effect if applicable
            if spell.effect_chance > 0 and random.randint(1, 100) <= spell.effect_chance:
                self.enemy_status[spell.effect_type] = spell.effect_value
                self.add_combat_log(f"Enemy is affected by {spell.effect_type}!", ORANGE)

        return True

    def player_use_item(self, item_name):
        """Use an item from inventory"""
        success, message = self.character_manager.use_item_from_inventory(item_name)

        if success:
            if "HP" in message:
                self.add_combat_text(200, 250, message.split()[1], "heal")
            elif "MP" in message:
                self.add_combat_text(200, 250, message.split()[1], "mana")

            self.add_combat_log(message, GREEN)
            return True
        else:
            self.add_combat_log(message, RED)
            return False

    def enemy_turn(self):
        """Execute enemy's turn"""
        if not self.current_enemy or self.current_enemy.get("Hit_Points", 0) <= 0:
            return

        enemy_stats = self.get_enemy_stats()
        player_stats = self.get_player_stats()

        # Simple AI - enemy always attacks
        if self.calculate_hit_chance(enemy_stats, player_stats):
            damage, is_critical = self.calculate_damage(8, 18, enemy_stats, player_stats)

            # Apply damage to player
            self.character_manager.character_data["Hit_Points"] -= damage

            text_type = "critical" if is_critical else "player_damage"
            crit_text = "CRITICAL! " if is_critical else ""

            self.add_combat_text(200, 250, f"-{damage}", text_type)
            enemy_name = self.current_enemy.get("Name", "Enemy")
            self.add_combat_log(f"{crit_text}{enemy_name} deals {damage} damage!", RED)
        else:
            self.add_combat_text(200, 250, "MISS", "miss")
            enemy_name = self.current_enemy.get("Name", "Enemy")
            self.add_combat_log(f"{enemy_name}'s attack misses!", GRAY)

    def process_status_effects(self):
        """Process ongoing status effects"""
        # Process enemy status effects
        for effect, duration in list(self.enemy_status.items()):
            if effect == "burn":
                burn_damage = random.randint(3, 8)
                self.current_enemy["Hit_Points"] -= burn_damage
                self.add_combat_text(400, 280, f"-{burn_damage}", "damage")
                self.add_combat_log(f"Enemy burns for {burn_damage} damage!", ORANGE)

            # Reduce duration
            self.enemy_status[effect] -= 1
            if self.enemy_status[effect] <= 0:
                del self.enemy_status[effect]
                self.add_combat_log(f"Enemy recovers from {effect}!", WHITE)

        # Process player status effects (if any)
        for effect, duration in list(self.player_status.items()):
            self.player_status[effect] -= 1
            if self.player_status[effect] <= 0:
                del self.player_status[effect]

    def attempt_run(self):
        """Attempt to run from combat"""
        player_stats = self.get_player_stats()
        enemy_stats = self.get_enemy_stats()

        # Base run chance of 60% + dexterity modifier
        run_chance = 60 + (player_stats.get("dexterity", 10) - 10) * 3
        run_chance = max(25, min(90, run_chance))  # Clamp between 25-90%

        if random.randint(1, 100) <= run_chance:
            self.add_combat_log("You successfully escape!", GREEN)
            return True
        else:
            self.add_combat_log("You couldn't escape!", RED)
            return False

    def handle_keypress(self, key):
        """Handle input during combat"""
        if self.action_delay > 0:
            return "continue"

        if self.combat_phase == "select_action":
            if key == pygame.K_UP:
                self.selected_action = (self.selected_action - 1) % len(self.actions)
            elif key == pygame.K_DOWN:
                self.selected_action = (self.selected_action + 1) % len(self.actions)
            elif key == pygame.K_RETURN:
                if self.selected_action == 0:  # Attack
                    self.player_attack()
                    self.player_turn = False
                    self.action_delay = 30
                elif self.selected_action == 1:  # Cast Spell
                    # Get available spells
                    if self.character_manager.character_data:
                        aspect = self.character_manager.character_data.get("Aspect1", "fire_level_1")
                        level = self.character_manager.character_data.get("Level", 1)
                        spells = self.spell_manager.get_spells_for_aspect(aspect, level)
                        if spells:
                            self.combat_phase = "select_spell"
                        else:
                            self.add_combat_log("No spells available!", RED)
                elif self.selected_action == 2:  # Use Item
                    if self.character_manager.character_data:
                        inventory = self.character_manager.character_data.get("Inventory", {})
                        usable_items = [item for item in inventory.keys() if "Potion" in item or "Restore" in item]
                        if usable_items:
                            self.combat_phase = "select_item"
                        else:
                            self.add_combat_log("No usable items!", RED)
                elif self.selected_action == 3:  # Run Away
                    if self.attempt_run():
                        return "run_success"
                    else:
                        self.player_turn = False
                        self.action_delay = 30

        elif self.combat_phase == "select_spell":
            aspect = self.character_manager.character_data.get("Aspect1", "fire_level_1")
            level = self.character_manager.character_data.get("Level", 1)
            spells = self.spell_manager.get_spells_for_aspect(aspect, level)

            if key == pygame.K_UP:
                self.selected_spell = (self.selected_spell - 1) % len(spells)
            elif key == pygame.K_DOWN:
                self.selected_spell = (self.selected_spell + 1) % len(spells)
            elif key == pygame.K_RETURN:
                spell = spells[self.selected_spell]
                if self.player_cast_spell(spell):
                    self.player_turn = False
                    self.action_delay = 30
                self.combat_phase = "select_action"
            elif key == pygame.K_ESCAPE:
                self.combat_phase = "select_action"

        elif self.combat_phase == "select_item":
            inventory = self.character_manager.character_data.get("Inventory", {})
            usable_items = [item for item in inventory.keys() if "Potion" in item or "Restore" in item]

            if key == pygame.K_UP:
                self.selected_item = (self.selected_item - 1) % len(usable_items)
            elif key == pygame.K_DOWN:
                self.selected_item = (self.selected_item + 1) % len(usable_items)
            elif key == pygame.K_RETURN:
                item_name = usable_items[self.selected_item]
                if self.player_use_item(item_name):
                    self.player_turn = False
                    self.action_delay = 30
                self.combat_phase = "select_action"
            elif key == pygame.K_ESCAPE:
                self.combat_phase = "select_action"

        return "continue"

    def update(self):
        """Update combat system"""
        self.animation_timer += 1

        # Update combat texts
        for text in self.combat_texts[:]:
            if not text.update():
                self.combat_texts.remove(text)

        # Handle action delay
        if self.action_delay > 0:
            self.action_delay -= 1
            return "continue"

        # Check for combat end conditions
        if not self.current_enemy or self.current_enemy.get("Hit_Points", 0) <= 0:
            return "victory"

        if not self.character_manager.character_data or self.character_manager.character_data.get("Hit_Points", 0) <= 0:
            return "defeat"

        # Handle enemy turn
        if not self.player_turn:
            self.enemy_turn()
            self.process_status_effects()
            self.player_turn = True
            self.action_delay = 30

        return "continue"

    def draw(self, screen):
        """Draw combat interface"""
        screen.fill((40, 20, 20))  # Dark red background

        # Draw title
        title = self.large_font.render("⚔️ COMBAT ⚔️", True, WHITE)
        title_rect = title.get_rect(center=(400, 50))
        screen.blit(title, title_rect)

        if not self.character_manager.character_data or not self.current_enemy:
            return

        # Draw combatant info
        player_name = self.character_manager.character_data.get("Name", "Player")
        player_hp = self.character_manager.character_data.get("Hit_Points", 100)
        player_mana = self.character_manager.character_data.get("Aspect1_Mana", 50)

        enemy_name = self.current_enemy.get("Name", "Enemy")
        enemy_hp = self.current_enemy.get("Hit_Points", 75)

        # Player info (left side)
        player_info = [
            f"{player_name}",
            f"HP: {player_hp}",
            f"MP: {player_mana}"
        ]

        for i, info in enumerate(player_info):
            color = GREEN if i == 0 else WHITE
            text = self.font.render(info, True, color)
            screen.blit(text, (50, 120 + i * 25))

        # Enemy info (right side)
        enemy_info = [
            f"{enemy_name}",
            f"HP: {enemy_hp}"
        ]

        for i, info in enumerate(enemy_info):
            color = RED if i == 0 else WHITE
            text = self.font.render(info, True, color)
            text_rect = text.get_rect(topright=(750, 120 + i * 25))
            screen.blit(text, text_rect)

        # Draw status effects
        y_offset = 0
        for effect, duration in self.enemy_status.items():
            status_text = self.small_font.render(f"{effect.title()}: {duration}", True, ORANGE)
            status_rect = status_text.get_rect(topright=(750, 170 + y_offset))
            screen.blit(status_text, status_rect)
            y_offset += 20

        # Draw action menu or spell/item selection
        self.draw_action_interface(screen)

        # Draw combat log
        log_y = 400
        for i, (message, color) in enumerate(self.combat_log[-6:]):
            text = self.small_font.render(message[:60], True, color)
            screen.blit(text, (50, log_y + i * 20))

        # Draw combat texts
        for text in self.combat_texts:
            text.draw(screen)

        # Draw turn indicator
        turn_text = "YOUR TURN" if self.player_turn else "ENEMY TURN"
        turn_color = GREEN if self.player_turn else RED
        turn_surface = self.font.render(turn_text, True, turn_color)
        turn_rect = turn_surface.get_rect(center=(400, 100))
        screen.blit(turn_surface, turn_rect)

    def draw_action_interface(self, screen):
        """Draw the action selection interface"""
        if self.combat_phase == "select_action":
            # Draw action menu
            action_y = 220
            action_title = self.font.render("Choose Action:", True, WHITE)
            screen.blit(action_title, (50, action_y))
            action_y += 30

            for i, action in enumerate(self.actions):
                color = MENU_SELECTED if i == self.selected_action else WHITE
                action_text = self.font.render(f"> {action}", True, color)
                screen.blit(action_text, (70, action_y + i * 25))

        elif self.combat_phase == "select_spell":
            # Draw spell selection menu
            if self.character_manager.character_data:
                aspect = self.character_manager.character_data.get("Aspect1", "fire_level_1")
                level = self.character_manager.character_data.get("Level", 1)
                spells = self.spell_manager.get_spells_for_aspect(aspect, level)
                current_mana = self.character_manager.character_data.get("Aspect1_Mana", 0)

                spell_y = 220
                spell_title = self.font.render("Choose Spell:", True, WHITE)
                screen.blit(spell_title, (50, spell_y))
                spell_y += 30

                for i, spell in enumerate(spells):
                    can_cast = current_mana >= spell.mana_cost
                    if i == self.selected_spell:
                        color = GREEN if can_cast else RED
                    else:
                        color = WHITE if can_cast else GRAY

                    spell_text = f"> {spell.name} ({spell.mana_cost} MP)"
                    text_surface = self.font.render(spell_text, True, color)
                    screen.blit(text_surface, (70, spell_y + i * 25))

                    # Show spell description for selected spell
                    if i == self.selected_spell:
                        desc_text = self.small_font.render(spell.description, True, MENU_TEXT)
                        screen.blit(desc_text, (90, spell_y + i * 25 + 20))

                # Instructions
                instruction = self.small_font.render("ENTER: Cast  ESC: Back", True, WHITE)
                screen.blit(instruction, (50, spell_y + len(spells) * 25 + 20))

        elif self.combat_phase == "select_item":
            # Draw item selection menu
            if self.character_manager.character_data:
                inventory = self.character_manager.character_data.get("Inventory", {})
                usable_items = [item for item in inventory.keys() if "Potion" in item or "Restore" in item]

                item_y = 220
                item_title = self.font.render("Choose Item:", True, WHITE)
                screen.blit(item_title, (50, item_y))
                item_y += 30

                for i, item_name in enumerate(usable_items):
                    quantity = inventory[item_name]
                    color = MENU_SELECTED if i == self.selected_item else WHITE

                    item_text = f"> {item_name} x{quantity}"
                    text_surface = self.font.render(item_text, True, color)
                    screen.blit(text_surface, (70, item_y + i * 25))

                # Instructions
                instruction = self.small_font.render("ENTER: Use  ESC: Back", True, WHITE)
                screen.blit(instruction, (50, item_y + len(usable_items) * 25 + 20))