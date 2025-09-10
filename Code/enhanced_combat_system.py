from pathlib import Path

import pygame
import random
import math
import os
from Code.ui_components import *

# Get the directory where your script is located
script_dir = Path(__file__).parent

# Build paths
sounds_dir = script_dir.parent / 'Sounds'
# demon_file = enemies_dir / 'demon_level_1.json'
# f"{sounds_dir}/sword_hit.wav"


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


class CombatText:
    """Base combat text class for compatibility"""

    def __init__(self, x, y, text, text_type="damage", world_pos=None):
        self.x = x
        self.y = y
        self.text = str(text)
        self.text_type = text_type
        self.timer = 60
        self.font = pygame.font.Font(None, 28)
        self.world_pos = world_pos

        # Set color based on text type
        self.colors = {
            "damage": (255, 100, 100),
            "player_damage": (255, 255, 100),
            "heal": (100, 255, 100),
            "mana": (100, 150, 255),
            "miss": (200, 200, 200),
            "critical": (255, 255, 255),
            "spell": (255, 100, 255),
            "status": (255, 200, 100)
        }

        self.color = self.colors.get(text_type, (255, 255, 255))
        self.alpha = 255

        # Movement
        self.velocity_y = -2
        self.velocity_x = random.uniform(-1, 1)

    def update(self):
        """Update combat text animation"""
        self.timer -= 1
        self.y += self.velocity_y
        self.x += self.velocity_x

        # Fade out
        fade_ratio = self.timer / 60
        self.alpha = max(0, int(255 * fade_ratio))

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

        text_surface = self.font.render(self.text, True, self.color)
        text_surface.set_alpha(self.alpha)
        screen.blit(text_surface, (draw_x, draw_y))


class SoundManager:
    """Manages game sound effects and music"""

    def __init__(self):
        self.sounds = {}
        self.music_enabled = True
        self.sfx_enabled = True
        self.master_volume = 0.7

        # Initialize pygame mixer
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sound_available = True
            self.load_sounds()
        except pygame.error:
            print("Sound system unavailable - continuing without audio")
            self.sound_available = False

    def load_sounds(self):
        """Load sound effects - with fallback for missing files"""
        if not self.sound_available:
            return

        sound_files = {
            # Combat sounds
            "sword_hit": f"{sounds_dir}/sword_hit.wav",
            "sword_miss": f"{sounds_dir}/sword_miss.wav",
            "spell_cast": f"{sounds_dir}/spell_cast.wav",
            "fireball": f"{sounds_dir}/fireball.wav",
            "heal": f"{sounds_dir}/heal.wav",
            "enemy_hit": f"{sounds_dir}/enemy_hit.wav",
            "enemy_death": f"{sounds_dir}/enemy_death.wav",
            "player_hurt": f"{sounds_dir}/player_hurt.wav",
            "critical_hit": f"{sounds_dir}/critical_hit.wav",
            "magic_missile": f"{sounds_dir}/magic_missile.wav",
            "potion_drink": f"{sounds_dir}/potion_drink.wav",
            "run_away": f"{sounds_dir}/run_away.wav",
            "victory": f"{sounds_dir}/victory.wav",
            "defeat": f"{sounds_dir}/defeat.wav",

            # UI sounds
            "menu_select": f"{sounds_dir}/menu_select.wav",
            "menu_move": f"{sounds_dir}/menu_move.wav",
            "item_pickup": f"{sounds_dir}/item_pickup.wav",
            "coin_pickup": f"{sounds_dir}/coin_pickup.wav",

            # Environmental sounds
            "footstep": f"{sounds_dir}/footstep.wav",
            "door_open": f"{sounds_dir}/door_open.wav",
        }

        for sound_name, file_path in sound_files.items():
            try:
                sound = pygame.mixer.Sound(file_path)
                sound.set_volume(self.master_volume)
                self.sounds[sound_name] = sound
            except (pygame.error, FileNotFoundError):
                # Create a simple fallback sound or skip
                print(f"Could not load {file_path} - using fallback or skipping")
                self.sounds[sound_name] = None

    def play_sound(self, sound_name, volume=1.0):
        """Play a sound effect"""
        if not self.sound_available or not self.sfx_enabled:
            return

        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                sound = self.sounds[sound_name]
                sound.set_volume(self.master_volume * volume)
                sound.play()
            except pygame.error:
                pass

    def play_music(self, music_file, loops=-1):
        """Play background music"""
        if not self.sound_available or not self.music_enabled:
            return

        try:
            # Check if file exists first
            if not os.path.exists(music_file):
                print(f"Music file not found: {music_file}")
                return

            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(self.master_volume * 0.6)
            pygame.mixer.music.play(loops)
        except (pygame.error, FileNotFoundError):
            print(f"Could not load music: {music_file}")

    def stop_music(self):
        """Stop background music"""
        if self.sound_available:
            pygame.mixer.music.stop()

    def set_master_volume(self, volume):
        """Set master volume (0.0 to 1.0)"""
        self.master_volume = max(0.0, min(1.0, volume))

        # Update all loaded sounds
        for sound in self.sounds.values():
            if sound:
                sound.set_volume(self.master_volume)


class CombatAnimation:
    """Enhanced combat animations and visual effects"""

    def __init__(self, x, y, animation_type, duration=60):
        self.x = x
        self.y = y
        self.animation_type = animation_type
        self.duration = duration
        self.timer = duration
        self.original_duration = duration

        # Animation parameters
        self.offset_x = 0
        self.offset_y = 0
        self.scale = 1.0
        self.rotation = 0
        self.alpha = 255
        self.particles = []

        # Initialize based on type
        self.setup_animation()

    def setup_animation(self):
        """Setup animation parameters based on type"""
        if self.animation_type == "sword_slash":
            self.rotation_speed = 15
            self.scale_change = 0.05

        elif self.animation_type == "spell_circle":
            self.rotation_speed = 8
            # Create magic particles
            for _ in range(12):
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(20, 40)
                self.particles.append({
                    'x': math.cos(angle) * distance,
                    'y': math.sin(angle) * distance,
                    'angle': angle,
                    'speed': random.uniform(1, 3),
                    'color': random.choice([(255, 100, 255), (100, 100, 255), (255, 255, 100)])
                })

        elif self.animation_type == "impact_flash":
            self.duration = 20
            self.timer = 20

        elif self.animation_type == "heal_sparkle":
            # Create healing sparkles
            for _ in range(8):
                self.particles.append({
                    'x': random.uniform(-30, 30),
                    'y': random.uniform(-30, 30),
                    'vx': random.uniform(-2, 2),
                    'vy': random.uniform(-4, -1),
                    'life': random.uniform(30, 60),
                    'color': (100, 255, 100)
                })

    def update(self):
        """Update animation"""
        self.timer -= 1
        progress = 1.0 - (self.timer / self.original_duration)

        if self.animation_type == "sword_slash":
            self.rotation += self.rotation_speed
            self.scale = 1.0 + math.sin(progress * math.pi) * 0.3
            self.offset_x = math.sin(progress * math.pi * 2) * 15

        elif self.animation_type == "spell_circle":
            self.rotation += self.rotation_speed
            self.scale = 0.5 + progress * 1.5

            # Update particles
            for particle in self.particles:
                particle['angle'] += particle['speed'] * 0.1
                particle['x'] = math.cos(particle['angle']) * (20 + progress * 30)
                particle['y'] = math.sin(particle['angle']) * (20 + progress * 30)

        elif self.animation_type == "impact_flash":
            self.alpha = int(255 * (1.0 - progress))
            self.scale = 1.0 + progress * 2.0

        elif self.animation_type == "heal_sparkle":
            # Update healing particles
            for particle in self.particles[:]:
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']
                particle['life'] -= 1
                if particle['life'] <= 0:
                    self.particles.remove(particle)

        # Fade out near end
        if self.timer < 15:
            self.alpha = int(255 * (self.timer / 15))

        return self.timer > 0

    def draw(self, screen):
        """Draw the animation"""
        draw_x = int(self.x + self.offset_x)
        draw_y = int(self.y + self.offset_y)

        if self.animation_type == "sword_slash":
            # Draw sword slash arc
            points = []
            for i in range(8):
                angle = math.radians(self.rotation + i * 15)
                radius = 30 * self.scale
                px = draw_x + math.cos(angle) * radius
                py = draw_y + math.sin(angle) * radius
                points.append((px, py))

            if len(points) >= 3:
                color = (*WHITE, max(50, self.alpha))
                try:
                    # Draw slash trail
                    for i in range(len(points) - 1):
                        pygame.draw.line(screen, (255, 255, 200), points[i], points[i + 1], 3)
                except:
                    pass

        elif self.animation_type == "spell_circle":
            # Draw magic circle
            radius = int(25 * self.scale)
            color = (255, 100, 255)

            # Draw circle outline
            if radius > 0:
                pygame.draw.circle(screen, color, (draw_x, draw_y), radius, 3)

                # Draw rotating runes/symbols
                for i in range(6):
                    angle = math.radians(self.rotation + i * 60)
                    symbol_x = draw_x + math.cos(angle) * radius * 0.7
                    symbol_y = draw_y + math.sin(angle) * radius * 0.7
                    pygame.draw.circle(screen, (255, 255, 100),
                                       (int(symbol_x), int(symbol_y)), 3)

            # Draw particles
            for particle in self.particles:
                px = draw_x + particle['x']
                py = draw_y + particle['y']
                pygame.draw.circle(screen, particle['color'], (int(px), int(py)), 2)

        elif self.animation_type == "impact_flash":
            # Draw impact flash
            color = (*WHITE, max(0, min(255, self.alpha)))
            radius = int(20 * self.scale)
            if radius > 0:
                # Create flash effect
                for i in range(3):
                    flash_radius = radius - i * 5
                    if flash_radius > 0:
                        alpha = max(0, self.alpha - i * 50)
                        flash_color = (255, 255 - i * 80, 100 - i * 30)
                        pygame.draw.circle(screen, flash_color, (draw_x, draw_y), flash_radius)

        elif self.animation_type == "heal_sparkle":
            # Draw healing sparkles
            for particle in self.particles:
                px = draw_x + particle['x']
                py = draw_y + particle['y']
                sparkle_alpha = max(0, min(255, int(particle['life'] * 4)))
                pygame.draw.circle(screen, particle['color'], (int(px), int(py)), 2)

                # Add sparkle effect
                if random.randint(1, 10) == 1:
                    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                        pygame.draw.circle(screen, (255, 255, 255),
                                           (int(px + dx), int(py + dy)), 1)


class EnhancedCombatText(CombatText):
    """Enhanced combat text with more visual effects"""

    def __init__(self, x, y, text, text_type="damage", world_pos=None):
        super().__init__(x, y, text, text_type, world_pos)

        # Enhanced visual properties
        self.bounce = 0
        self.shake = 0
        self.outline = text_type in ["critical", "spell"]
        self.scale = 1.0

        # Enhanced movement based on type
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

        # Screen shake for big hits
        if text_type == "critical" and isinstance(text, (int, str)):
            try:
                damage_value = int(str(text).replace("-", "").replace("+", ""))
                if damage_value > 25:
                    self.shake = 8
            except:
                pass

    def update(self):
        """Enhanced update with bounce and shake effects"""
        result = super().update()

        # Add bounce effect for crits
        if self.text_type == "critical":
            self.bounce = math.sin(self.timer * 0.3) * 3

        # Reduce shake over time
        self.shake *= 0.9

        return result

    def draw(self, screen, camera=None):
        """Enhanced drawing with effects"""
        if camera and self.world_pos:
            screen_x, screen_y = camera.world_to_screen(self.world_pos[0], self.world_pos[1])
            draw_x = screen_x + (self.x - self.world_pos[0])
            draw_y = screen_y + (self.y - self.world_pos[1])
        else:
            draw_x = self.x
            draw_y = self.y

        # Apply effects
        draw_x += random.uniform(-self.shake, self.shake) if self.shake > 0 else 0
        draw_y += random.uniform(-self.shake, self.shake) + self.bounce if self.shake > 0 else draw_y + self.bounce

        # Scale font based on text type
        font_size = int(28 * self.scale)
        if font_size != 28:
            try:
                font = pygame.font.Font(None, font_size)
            except:
                font = self.font
        else:
            font = self.font

        # Draw outline for special effects
        if self.outline:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx != 0 or dy != 0:
                        try:
                            outline_surface = font.render(self.text, True, BLACK)
                            outline_surface.set_alpha(self.alpha)
                            screen.blit(outline_surface, (int(draw_x + dx), int(draw_y + dy)))
                        except:
                            pass

        # Draw main text
        try:
            text_surface = font.render(self.text, True, self.color)
            text_surface.set_alpha(self.alpha)
            screen.blit(text_surface, (int(draw_x), int(draw_y)))
        except:
            # Fallback if there are any rendering issues
            fallback_surface = self.font.render(str(self.text), True, self.color)
            fallback_surface.set_alpha(self.alpha)
            screen.blit(fallback_surface, (int(draw_x), int(draw_y)))


class EnhancedCombatManager:
    """Enhanced combat manager with sound and animation support"""

    def __init__(self, character_manager):
        self.character_manager = character_manager
        self.spell_manager = SpellManager()
        self.sound_manager = SoundManager()

        self.combat_texts = []
        self.combat_animations = []
        self.combat_log = []

        # Combat state
        self.current_enemy = None
        self.player_turn = True
        self.combat_phase = "select_action"
        self.selected_action = 0
        self.selected_spell = 0
        self.selected_item = 0

        # Combat options
        self.actions = ["Attack", "Cast Spell", "Use Item", "Run Away"]

        # Status effects
        self.player_status = {}
        self.enemy_status = {}

        # Animation and timing
        self.animation_timer = 0
        self.action_delay = 0
        self.screen_shake = 0
        self.combat_music_playing = False

        # UI fonts
        self.font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 20)

    def add_combat_log(self, message, color=WHITE):
        """Add message to combat log"""
        self.combat_log.append((message, color))
        if len(self.combat_log) > 8:
            self.combat_log.pop(0)

    def start_combat(self, enemy_data):
        """Initialize combat with enhanced audio-visual effects"""
        self.current_enemy = enemy_data.copy()
        self.combat_texts.clear()
        self.combat_animations.clear()
        self.combat_log.clear()
        self.player_status.clear()
        self.enemy_status.clear()
        self.player_turn = True
        self.combat_phase = "select_action"
        self.selected_action = 0
        self.animation_timer = 0

        # Play combat music if available
        if not self.combat_music_playing:
            self.sound_manager.play_music(f"{sounds_dir}/battle_music.ogg")
            self.combat_music_playing = True

        # Play combat start sound
        self.sound_manager.play_sound("menu_select")

        # Add combat start message
        enemy_name = self.current_enemy.get("Name", "Enemy")
        self.add_combat_log(f"Combat begins with {enemy_name}!", WHITE)

        # Add dramatic entry animation
        self.add_combat_animation(400, 300, "spell_circle", 120)

    def get_player_stats(self):
        """Get player stats for combat calculations"""
        if not self.character_manager or not self.character_manager.character_data:
            return {"strength": 10, "dexterity": 10, "constitution": 10,
                    "intelligence": 10, "wisdom": 10, "charisma": 10}

        return {
            "strength": self.character_manager.get_total_stat("strength"),
            "dexterity": self.character_manager.get_total_stat("dexterity"),
            "constitution": self.character_manager.get_total_stat("constitution"),
            "intelligence": self.character_manager.get_total_stat("intelligence"),
            "wisdom": self.character_manager.get_total_stat("wisdom"),
            "charisma": self.character_manager.get_total_stat("charisma"),
            "armor_class": self.character_manager.get_armor_class()
        }

    def get_enemy_stats(self):
        """Get enemy stats (simplified)"""
        level = self.current_enemy.get("Level", 1) if self.current_enemy else 1
        return {
            "strength": 10 + level,
            "dexterity": 10 + level,
            "constitution": 12 + level,
            "intelligence": 8 + level,
            "wisdom": 8 + level,
            "charisma": 6
        }

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

    def calculate_spell_damage(self, spell, caster_stats):
        """Calculate spell damage with intelligence/wisdom modifiers"""
        base_damage = random.randint(spell.damage_min, spell.damage_max)

        # Intelligence modifier for damage spells
        int_bonus = max(0, (caster_stats.get("intelligence", 10) - 10) // 2)

        # Wisdom modifier for healing spells
        wis_bonus = max(0, (caster_stats.get("wisdom", 10) - 10) // 2)

        if spell.spell_type == "heal":
            return base_damage + wis_bonus, False
        elif spell.spell_type == "drain":
            return base_damage + int_bonus, False
        else:
            # Critical hit chance for spells
            crit_chance = max(3, int_bonus)
            is_critical = random.randint(1, 100) <= crit_chance

            if is_critical:
                return int((base_damage + int_bonus) * 1.5), True
            else:
                return base_damage + int_bonus, False

    def calculate_hit_chance(self, attacker_stats, defender_stats):
        """Calculate if attack hits based on stats"""
        # Base hit chance
        base_hit = 75

        # Attacker dexterity bonus
        att_dex = attacker_stats.get("dexterity", 10)
        hit_bonus = (att_dex - 10) // 2

        # Defender AC
        if "armor_class" in defender_stats:
            ac_penalty = (defender_stats["armor_class"] - 10) * 2
        else:
            def_dex = defender_stats.get("dexterity", 10)
            ac_penalty = (def_dex - 10)

        final_hit_chance = max(5, base_hit + hit_bonus - ac_penalty)
        return random.randint(1, 100) <= final_hit_chance

    def process_status_effects(self):
        """Process ongoing status effects"""
        # Process enemy status effects
        for effect, duration in list(self.enemy_status.items()):
            if effect == "burn":
                burn_damage = random.randint(3, 8)
                self.current_enemy["Hit_Points"] -= burn_damage
                self.add_combat_text(400, 280, f"-{burn_damage}", "damage")
                self.add_combat_log(f"Enemy burns for {burn_damage} damage!", ORANGE)
            elif effect == "freeze":
                self.add_combat_log(f"Enemy is frozen!", LIGHT_BLUE)
            elif effect == "stun":
                self.add_combat_log(f"Enemy is stunned!", YELLOW)

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

    def add_combat_animation(self, x, y, animation_type, duration=60):
        """Add a combat animation"""
        animation = CombatAnimation(x, y, animation_type, duration)
        self.combat_animations.append(animation)

    def add_combat_text(self, x, y, text, text_type="damage", world_pos=None):
        """Add enhanced floating combat text"""
        try:
            # Ensure coordinates are valid numbers
            x = float(x) if x is not None else 400
            y = float(y) if y is not None else 300

            combat_text = EnhancedCombatText(x, y, text, text_type, world_pos)
            self.combat_texts.append(combat_text)

            # Add screen shake for big numbers
            if text_type == "critical" and isinstance(text, (int, str)):
                try:
                    damage_value = int(str(text).replace("-", "").replace("+", ""))
                    if damage_value > 20:
                        self.screen_shake = min(15, damage_value // 3)
                except:
                    pass
        except Exception as e:
            print(f"Error adding combat text: {e}")
            # Minimal fallback
            try:
                simple_text = CombatText(400, 300, str(text), text_type, world_pos)
                self.combat_texts.append(simple_text)
            except:
                pass

    def player_attack(self):
        """Enhanced player attack with audio and visual effects"""
        player_stats = self.get_player_stats()
        enemy_stats = self.get_enemy_stats()

        # Play attack sound
        self.sound_manager.play_sound("sword_hit" if random.choice([True, False]) else "sword_miss")

        # Add sword slash animation
        self.add_combat_animation(400, 250, "sword_slash", 45)

        if self.calculate_hit_chance(player_stats, enemy_stats):
            damage, is_critical = self.calculate_damage(10, 20, player_stats, enemy_stats)

            # Play appropriate hit sound
            if is_critical:
                self.sound_manager.play_sound("critical_hit")
            else:
                self.sound_manager.play_sound("enemy_hit")

            # Apply damage
            self.current_enemy["Hit_Points"] -= damage

            # Enhanced visual effects
            text_type = "critical" if is_critical else "damage"
            crit_text = "CRITICAL! " if is_critical else ""

            self.add_combat_text(400, 250, f"-{damage}", text_type)
            self.add_combat_log(f"{crit_text}You deal {damage} damage!", GREEN)

            # Add impact animation
            self.add_combat_animation(420, 270, "impact_flash", 30)

            # Check if enemy dies
            if self.current_enemy["Hit_Points"] <= 0:
                self.sound_manager.play_sound("enemy_death")

            return damage
        else:
            self.sound_manager.play_sound("sword_miss")
            self.add_combat_text(400, 250, "MISS", "miss")
            self.add_combat_log("Your attack misses!", GRAY)
            return 0

    def player_cast_spell(self, spell):
        """Enhanced spell casting with effects"""
        if not self.character_manager.character_data:
            return False

        current_mana = self.character_manager.character_data.get("Aspect1_Mana", 0)
        if current_mana < spell.mana_cost:
            self.add_combat_log("Not enough mana!", RED)
            self.sound_manager.play_sound("menu_select")  # Error sound
            return False

        # Consume mana
        self.character_manager.character_data["Aspect1_Mana"] -= spell.mana_cost

        # Play spell casting sound
        if "Fire" in spell.name or "flame" in spell.name.lower():
            self.sound_manager.play_sound("fireball")
        elif "heal" in spell.name.lower():
            self.sound_manager.play_sound("heal")
        else:
            self.sound_manager.play_sound("spell_cast")

        # Add spell circle animation
        self.add_combat_animation(200 if spell.spell_type == "heal" else 400, 250, "spell_circle", 75)

        player_stats = self.get_player_stats()
        damage, is_critical = self.calculate_spell_damage(spell, player_stats)

        if spell.spell_type == "heal":
            # Healing spell effects
            current_hp = self.character_manager.character_data.get("Hit_Points", 100)
            level = self.character_manager.character_data.get("Level", 1)
            max_hp = self.character_manager.get_max_hp_for_level(level)

            healed = min(damage, max_hp - current_hp)
            self.character_manager.character_data["Hit_Points"] += healed

            self.add_combat_text(200, 250, f"+{healed}", "heal")
            self.add_combat_log(f"You heal for {healed} HP!", GREEN)

            # Add healing sparkle animation
            self.add_combat_animation(200, 250, "heal_sparkle", 90)

        elif spell.spell_type == "drain":
            # Drain life effects
            self.current_enemy["Hit_Points"] -= damage

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

            # Add impact and heal effects
            self.add_combat_animation(420, 270, "impact_flash", 30)
            if healed > 0:
                self.add_combat_animation(200, 250, "heal_sparkle", 60)

        else:
            # Damage spell effects
            self.current_enemy["Hit_Points"] -= damage

            text_type = "critical" if is_critical else "spell"
            crit_text = "CRITICAL! " if is_critical else ""

            self.add_combat_text(400, 250, f"-{damage}", text_type)
            self.add_combat_log(f"{crit_text}{spell.name} deals {damage} damage!", PURPLE)

            # Add impact animation
            self.add_combat_animation(420, 270, "impact_flash", 45)

            # Apply status effect if applicable
            if spell.effect_chance > 0 and random.randint(1, 100) <= spell.effect_chance:
                self.enemy_status[spell.effect_type] = spell.effect_value
                self.add_combat_log(f"Enemy is affected by {spell.effect_type}!", ORANGE)

        return True

    def player_use_item(self, item_name):
        """Enhanced item usage with sound effects"""
        success, message = self.character_manager.use_item_from_inventory(item_name)

        if success:
            # Play potion drinking sound
            self.sound_manager.play_sound("potion_drink")

            if "HP" in message:
                self.add_combat_text(200, 250, message.split()[1], "heal")
                self.add_combat_animation(200, 250, "heal_sparkle", 60)
            elif "MP" in message:
                self.add_combat_text(200, 250, message.split()[1], "mana")

            self.add_combat_log(message, GREEN)
            return True
        else:
            self.sound_manager.play_sound("menu_select")  # Error sound
            self.add_combat_log(message, RED)
            return False

    def enemy_turn(self):
        """Enhanced enemy turn with effects"""
        if not self.current_enemy or self.current_enemy.get("Hit_Points", 0) <= 0:
            return

        enemy_stats = self.get_enemy_stats()
        player_stats = self.get_player_stats()

        # Enemy attack with sound and visual effects
        if self.calculate_hit_chance(enemy_stats, player_stats):
            damage, is_critical = self.calculate_damage(8, 18, enemy_stats, player_stats)

            # Play enemy attack sounds
            if is_critical:
                self.sound_manager.play_sound("critical_hit")
            else:
                enemy_sounds = ["enemy_hit", "sword_hit"]
                self.sound_manager.play_sound(random.choice(enemy_sounds))

            # Apply damage to player
            self.character_manager.character_data["Hit_Points"] -= damage

            # Play player hurt sound
            self.sound_manager.play_sound("player_hurt")

            text_type = "critical" if is_critical else "player_damage"
            crit_text = "CRITICAL! " if is_critical else ""

            self.add_combat_text(200, 250, f"-{damage}", text_type)
            enemy_name = self.current_enemy.get("Name", "Enemy")
            self.add_combat_log(f"{crit_text}{enemy_name} deals {damage} damage!", RED)

            # Add impact animation on player
            self.add_combat_animation(180, 270, "impact_flash", 30)

        else:
            self.sound_manager.play_sound("sword_miss")
            self.add_combat_text(200, 250, "MISS", "miss")
            enemy_name = self.current_enemy.get("Name", "Enemy")
            self.add_combat_log(f"{enemy_name}'s attack misses!", GRAY)

    def attempt_run(self):
        """Enhanced run away with sound effect"""
        player_stats = self.get_player_stats()
        enemy_stats = self.get_enemy_stats()

        run_chance = 60 + (player_stats.get("dexterity", 10) - 10) * 3
        run_chance = max(25, min(90, run_chance))

        if random.randint(1, 100) <= run_chance:
            self.sound_manager.play_sound("run_away")
            self.add_combat_log("You successfully escape!", GREEN)
            return True
        else:
            self.sound_manager.play_sound("menu_select")  # Failure sound
            self.add_combat_log("You couldn't escape!", RED)
            return False

    def update(self):
        """Enhanced update with animations and screen effects"""
        self.animation_timer += 1

        # Update combat texts
        for text in self.combat_texts[:]:
            if not text.update():
                self.combat_texts.remove(text)

        # Update combat animations
        for animation in self.combat_animations[:]:
            if not animation.update():
                self.combat_animations.remove(animation)

        # Update screen shake
        if self.screen_shake > 0:
            self.screen_shake *= 0.9
            if self.screen_shake < 0.5:
                self.screen_shake = 0

        # Handle action delay
        if self.action_delay > 0:
            self.action_delay -= 1
            return "continue"

        # Check for combat end conditions
        if not self.current_enemy or self.current_enemy.get("Hit_Points", 0) <= 0:
            self.sound_manager.play_sound("victory")
            self.sound_manager.stop_music()
            self.combat_music_playing = False
            return "victory"

        if not self.character_manager.character_data or self.character_manager.character_data.get("Hit_Points", 0) <= 0:
            self.sound_manager.play_sound("defeat")
            self.sound_manager.stop_music()
            self.combat_music_playing = False
            return "defeat"

        # Handle enemy turn
        if not self.player_turn:
            self.enemy_turn()
            self.process_status_effects()
            self.player_turn = True
            self.action_delay = 30

        return "continue"

    def handle_keypress(self, key):
        """Enhanced keypress handling with menu sounds"""
        if self.action_delay > 0:
            return "continue"

        if self.combat_phase == "select_action":
            if key == pygame.K_UP:
                self.sound_manager.play_sound("menu_move")
                self.selected_action = (self.selected_action - 1) % len(self.actions)
            elif key == pygame.K_DOWN:
                self.sound_manager.play_sound("menu_move")
                self.selected_action = (self.selected_action + 1) % len(self.actions)
            elif key == pygame.K_RETURN:
                self.sound_manager.play_sound("menu_select")

                if self.selected_action == 0:  # Attack
                    self.player_attack()
                    self.player_turn = False
                    self.action_delay = 30
                elif self.selected_action == 1:  # Cast Spell
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
                self.sound_manager.play_sound("menu_move")
                self.selected_spell = (self.selected_spell - 1) % len(spells)
            elif key == pygame.K_DOWN:
                self.sound_manager.play_sound("menu_move")
                self.selected_spell = (self.selected_spell + 1) % len(spells)
            elif key == pygame.K_RETURN:
                spell = spells[self.selected_spell]
                if self.player_cast_spell(spell):
                    self.player_turn = False
                    self.action_delay = 30
                self.combat_phase = "select_action"
            elif key == pygame.K_ESCAPE:
                self.sound_manager.play_sound("menu_move")
                self.combat_phase = "select_action"

        elif self.combat_phase == "select_item":
            inventory = self.character_manager.character_data.get("Inventory", {})
            usable_items = [item for item in inventory.keys() if "Potion" in item or "Restore" in item]

            if key == pygame.K_UP:
                self.sound_manager.play_sound("menu_move")
                self.selected_item = (self.selected_item - 1) % len(usable_items)
            elif key == pygame.K_DOWN:
                self.sound_manager.play_sound("menu_move")
                self.selected_item = (self.selected_item + 1) % len(usable_items)
            elif key == pygame.K_RETURN:
                item_name = usable_items[self.selected_item]
                if self.player_use_item(item_name):
                    self.player_turn = False
                    self.action_delay = 30
                self.combat_phase = "select_action"
            elif key == pygame.K_ESCAPE:
                self.sound_manager.play_sound("menu_move")
                self.combat_phase = "select_action"

        return "continue"

    def draw(self, screen):
        """Enhanced draw with screen shake and animations"""
        # Apply screen shake
        shake_x = random.uniform(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        shake_y = random.uniform(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0

        # Create a surface for the shaken content
        if self.screen_shake > 0:
            combat_surface = pygame.Surface((screen.get_width(), screen.get_height()))
            combat_surface.fill((40, 20, 20))
            draw_target = combat_surface
        else:
            screen.fill((40, 20, 20))
            draw_target = screen

        # Draw title with pulsing effect
        pulse = math.sin(self.animation_timer * 0.1) * 0.2 + 1.0
        title_color = tuple(int(c * pulse) for c in WHITE)
        title = self.large_font.render("️ COMBAT ", True, DARK_BLUE)
        title_rect = title.get_rect(center=(400, 50))
        draw_target.blit(title, title_rect)

        if not self.character_manager.character_data or not self.current_enemy:
            if self.screen_shake > 0:
                screen.blit(combat_surface, (shake_x, shake_y))
            return

        # Draw combatant info with enhanced visuals
        player_name = self.character_manager.character_data.get("Name", "Player")
        player_hp = self.character_manager.character_data.get("Hit_Points", 100)
        player_mana = self.character_manager.character_data.get("Aspect1_Mana", 50)

        enemy_name = self.current_enemy.get("Name", "Enemy")
        enemy_hp = self.current_enemy.get("Hit_Points", 75)

        # Player info (left side) with health bar
        player_info = [
            f"{player_name}",
            f"HP: {player_hp}",
            f"MP: {player_mana}"
        ]

        for i, info in enumerate(player_info):
            color = GREEN if i == 0 else WHITE
            # Add glow effect for low health
            if "HP:" in info and player_hp < 25:
                color = (255, 100, 100)
                # Add warning pulse
                warning_pulse = math.sin(self.animation_timer * 0.3) * 0.3 + 0.7
                color = tuple(int(c * warning_pulse) for c in color)

            text = self.font.render(info, True, color)
            draw_target.blit(text, (50, 120 + i * 25))

        # Enemy info (right side) with damage indicators
        enemy_info = [
            f"{enemy_name}",
            f"HP: {enemy_hp}"
        ]

        for i, info in enumerate(enemy_info):
            color = RED if i == 0 else WHITE
            # Add damage flash effect
            if hasattr(self, 'enemy_damage_flash') and self.enemy_damage_flash > 0:
                flash_intensity = self.enemy_damage_flash / 30.0
                color = tuple(min(255, int(c + 100 * flash_intensity)) for c in color)

            text = self.font.render(info, True, color)
            text_rect = text.get_rect(topright=(750, 120 + i * 25))
            draw_target.blit(text, text_rect)

        # Draw enhanced status effects with icons
        y_offset = 0
        for effect, duration in self.enemy_status.items():
            # Choose color and icon based on effect type
            if effect == "burn":
                effect_color = (255, 100, 0)
                icon = "🔥"
            elif effect == "freeze":
                effect_color = (100, 200, 255)
                icon = "❄️"
            elif effect == "poison":
                effect_color = (100, 255, 100)
                icon = "☠️"
            else:
                effect_color = ORANGE
                icon = "✨"

            status_text = f"{icon} {effect.title()}: {duration}"
            status_surface = self.small_font.render(status_text, True, effect_color)
            status_rect = status_surface.get_rect(topright=(750, 170 + y_offset))
            draw_target.blit(status_surface, status_rect)
            y_offset += 20

        # Draw action interface with enhanced visuals
        self.draw_enhanced_action_interface(draw_target)

        # Draw enhanced combat log with background
        log_bg = pygame.Rect(40, 390, 720, 130)
        pygame.draw.rect(draw_target, (20, 10, 10, 180), log_bg)
        pygame.draw.rect(draw_target, (100, 50, 50), log_bg, 2)

        log_y = 400
        for i, (message, color) in enumerate(self.combat_log[-6:]):
            # Add fade effect for older messages
            fade = 1.0 - (5 - i) * 0.15 if i < 5 else 1.0
            faded_color = tuple(int(c * fade) for c in color)

            text = self.small_font.render(message[:60], True, faded_color)
            draw_target.blit(text, (50, log_y + i * 20))

        # Draw combat animations
        for animation in self.combat_animations:
            animation.draw(draw_target)

        # Draw combat texts
        for text in self.combat_texts:
            text.draw(draw_target)

        # Draw turn indicator with enhanced styling
        turn_text = "YOUR TURN" if self.player_turn else "ENEMY TURN"
        turn_color = GREEN if self.player_turn else RED

        # Add pulsing effect
        turn_pulse = math.sin(self.animation_timer * 0.2) * 0.3 + 0.7
        turn_color = tuple(max(0, min(255, int(c * turn_pulse))) for c in turn_color)

        turn_surface = self.font.render(turn_text, True, turn_color)
        turn_rect = turn_surface.get_rect(center=(400, 100))

        # Add background for turn indicator
        bg_rect = turn_rect.inflate(20, 10)
        pygame.draw.rect(draw_target, (0, 0, 0, 128), bg_rect)
        pygame.draw.rect(draw_target, turn_color, bg_rect, 2)

        draw_target.blit(turn_surface, turn_rect)

        # Apply screen shake by blitting the shaken surface
        if self.screen_shake > 0:
            screen.blit(combat_surface, (shake_x, shake_y))

    def draw_enhanced_action_interface(self, screen):
        """Draw enhanced action selection interface"""
        if self.combat_phase == "select_action":
            # Draw action menu with background
            menu_bg = pygame.Rect(40, 210, 300, 150)
            pygame.draw.rect(screen, (30, 15, 15, 200), menu_bg)
            pygame.draw.rect(screen, (150, 100, 100), menu_bg, 2)

            action_y = 220
            action_title = self.font.render("Choose Action:", True, WHITE)
            screen.blit(action_title, (50, action_y))
            action_y += 30

            # Action icons
            action_icons = ["⚔️", "🔮", "🧪", "🏃"]

            for i, (action, icon) in enumerate(zip(self.actions, action_icons)):
                color = MENU_SELECTED if i == self.selected_action else WHITE

                # Add selection highlight
                if i == self.selected_action:
                    highlight_rect = pygame.Rect(65, action_y + i * 25 - 2, 250, 20)
                    pygame.draw.rect(screen, (50, 30, 30), highlight_rect)
                    pygame.draw.rect(screen, color, highlight_rect, 1)

                action_text = f"{icon} {action}"
                text_surface = self.font.render(action_text, True, color)
                screen.blit(text_surface, (70, action_y + i * 25))

        elif self.combat_phase == "select_spell":
            # Draw spell selection menu with mana costs
            if self.character_manager.character_data:
                aspect = self.character_manager.character_data.get("Aspect1", "fire_level_1")
                level = self.character_manager.character_data.get("Level", 1)
                spells = self.spell_manager.get_spells_for_aspect(aspect, level)
                current_mana = self.character_manager.character_data.get("Aspect1_Mana", 0)

                # Enhanced spell menu background
                menu_height = len(spells) * 45 + 80
                menu_bg = pygame.Rect(40, 210, 400, menu_height)
                pygame.draw.rect(screen, (20, 10, 30, 220), menu_bg)
                pygame.draw.rect(screen, (100, 50, 150), menu_bg, 2)

                spell_y = 220
                spell_title = self.font.render("Choose Spell:", True, PURPLE)
                screen.blit(spell_title, (50, spell_y))
                spell_y += 30

                for i, spell in enumerate(spells):
                    can_cast = current_mana >= spell.mana_cost

                    # Selection highlight
                    if i == self.selected_spell:
                        highlight_rect = pygame.Rect(65, spell_y + i * 45 - 2, 350, 40)
                        highlight_color = GREEN if can_cast else RED
                        pygame.draw.rect(screen, (30, 20, 30), highlight_rect)
                        pygame.draw.rect(screen, highlight_color, highlight_rect, 2)
                        color = highlight_color
                    else:
                        color = WHITE if can_cast else GRAY

                    # Spell icon based on type
                    if "fire" in spell.name.lower() or "flame" in spell.name.lower():
                        spell_icon = "🔥"
                    elif "heal" in spell.name.lower():
                        spell_icon = "💚"
                    elif "ice" in spell.name.lower() or "frost" in spell.name.lower():
                        spell_icon = "❄️"
                    elif "lightning" in spell.name.lower():
                        spell_icon = "⚡"
                    else:
                        spell_icon = "✨"

                    spell_text = f"{spell_icon} {spell.name} ({spell.mana_cost} MP)"
                    text_surface = self.font.render(spell_text, True, color)
                    screen.blit(text_surface, (70, spell_y + i * 45))

                    # Show damage range
                    if spell.spell_type == "heal":
                        damage_text = f"Heals {spell.damage_min}-{spell.damage_max}"
                    else:
                        damage_text = f"Damage: {spell.damage_min}-{spell.damage_max}"

                    damage_surface = self.small_font.render(damage_text, True, MENU_TEXT)
                    screen.blit(damage_surface, (90, spell_y + i * 45 + 18))

                    # Show spell description for selected spell
                    if i == self.selected_spell:
                        desc_surface = self.small_font.render(spell.description, True, color)
                        screen.blit(desc_surface, (90, spell_y + i * 45 + 32))

                # Instructions with enhanced styling
                instruction_bg = pygame.Rect(40, spell_y + len(spells) * 45 + 10, 400, 25)
                pygame.draw.rect(screen, (40, 20, 40), instruction_bg)
                instruction = self.small_font.render("ENTER: Cast  ESC: Back  ↑↓: Navigate", True, WHITE)
                screen.blit(instruction, (50, spell_y + len(spells) * 45 + 15))

        elif self.combat_phase == "select_item":
            # Draw item selection menu
            if self.character_manager.character_data:
                inventory = self.character_manager.character_data.get("Inventory", {})
                usable_items = [item for item in inventory.keys() if "Potion" in item or "Restore" in item]

                # Enhanced item menu
                menu_height = len(usable_items) * 35 + 60
                menu_bg = pygame.Rect(40, 210, 350, menu_height)
                pygame.draw.rect(screen, (10, 20, 10, 220), menu_bg)
                pygame.draw.rect(screen, (50, 150, 50), menu_bg, 2)

                item_y = 220
                item_title = self.font.render("Choose Item:", True, GREEN)
                screen.blit(item_title, (50, item_y))
                item_y += 30

                for i, item_name in enumerate(usable_items):
                    quantity = inventory[item_name]

                    # Selection highlight
                    if i == self.selected_item:
                        highlight_rect = pygame.Rect(65, item_y + i * 35 - 2, 300, 30)
                        pygame.draw.rect(screen, (20, 40, 20), highlight_rect)
                        pygame.draw.rect(screen, MENU_SELECTED, highlight_rect, 2)
                        color = MENU_SELECTED
                    else:
                        color = WHITE

                    # Item icon
                    if "Health" in item_name:
                        item_icon = "❤️"
                    elif "Mana" in item_name:
                        item_icon = "💙"
                    elif "Restore" in item_name:
                        item_icon = "⭐"
                    else:
                        item_icon = "🧪"

                    item_text = f"{item_icon} {item_name} x{quantity}"
                    text_surface = self.font.render(item_text, True, color)
                    screen.blit(text_surface, (70, item_y + i * 35))

                # Instructions
                instruction_bg = pygame.Rect(40, item_y + len(usable_items) * 35 + 5, 350, 25)
                pygame.draw.rect(screen, (20, 40, 20), instruction_bg)

    def draw_combatant_info(self, draw_target):
        """Draw player and enemy information"""
        player_name = self.character_manager.character_data.get("Name", "Player")
        player_hp = self.character_manager.character_data.get("Hit_Points", 100)
        player_mana = self.character_manager.character_data.get("Aspect1_Mana", 50)

        enemy_name = self.current_enemy.get("Name", "Enemy")
        enemy_hp = self.current_enemy.get("Hit_Points", 75)

        # Player info (left side) with health bar
        player_info = [
            f"{player_name}",
            f"HP: {player_hp}",
            f"MP: {player_mana}"
        ]

        for i, info in enumerate(player_info):
            color = (0, 255, 0) if i == 0 else (255, 255, 255)  # GREEN if i == 0 else WHITE
            # Add glow effect for low health
            if "HP:" in info and player_hp < 25:
                color = (255, 100, 100)
                # Add warning pulse
                warning_pulse = math.sin(self.animation_timer * 0.3) * 0.3 + 0.7
                color = tuple(max(0, min(255, int(c * warning_pulse))) for c in color)

            text = self.font.render(info, True, color)
            draw_target.blit(text, (50, 120 + i * 25))

        # Enemy info (right side) with damage indicators
        enemy_info = [
            f"{enemy_name}",
            f"HP: {enemy_hp}"
        ]

        for i, info in enumerate(enemy_info):
            color = (255, 0, 0) if i == 0 else (255, 255, 255)  # RED if i == 0 else WHITE
            # Add damage flash effect
            if hasattr(self, 'enemy_damage_flash') and self.enemy_damage_flash > 0:
                flash_intensity = self.enemy_damage_flash / 30.0
                color = tuple(max(0, min(255, int(c + 100 * flash_intensity))) for c in color)

            text = self.font.render(info, True, color)
            text_rect = text.get_rect(topright=(750, 120 + i * 25))
            draw_target.blit(text, text_rect)

        # Draw enhanced status effects with icons
        y_offset = 0
        for effect, duration in self.enemy_status.items():
            # Choose color and icon based on effect type
            if effect == "burn":
                effect_color = (255, 100, 0)
                icon = "BURN"
            elif effect == "freeze":
                effect_color = (100, 200, 255)
                icon = "FREEZE"
            elif effect == "poison":
                effect_color = (100, 255, 100)
                icon = "POISON"
            else:
                effect_color = (255, 165, 0)  # ORANGE
                icon = "STATUS"

            status_text = f"{icon}: {duration}"
            status_surface = self.small_font.render(status_text, True, effect_color)
            status_rect = status_surface.get_rect(topright=(750, 170 + y_offset))
            draw_target.blit(status_surface, status_rect)
            y_offset += 20

    def draw_combat_log(self, draw_target):
        """Draw the combat log with background"""
        log_bg = pygame.Rect(40, 390, 720, 130)
        pygame.draw.rect(draw_target, (20, 10, 10), log_bg)
        pygame.draw.rect(draw_target, (100, 50, 50), log_bg, 2)

        log_y = 400
        for i, (message, color) in enumerate(self.combat_log[-6:]):
            # Add fade effect for older messages
            fade = 1.0 - (5 - i) * 0.15 if i < 5 else 1.0
            faded_color = tuple(max(0, min(255, int(c * fade))) for c in color)

            text = self.small_font.render(message[:60], True, faded_color)
            draw_target.blit(text, (50, log_y + i * 20))

    def draw_turn_indicator(self, draw_target):
        """Draw the turn indicator with enhanced styling"""
        turn_text = "YOUR TURN" if self.player_turn else "ENEMY TURN"
        turn_color = (0, 255, 0) if self.player_turn else (255, 0, 0)  # GREEN if self.player_turn else RED

        # Add pulsing effect
        turn_pulse = math.sin(self.animation_timer * 0.2) * 0.3 + 0.7
        turn_color = tuple(max(0, min(255, int(c * turn_pulse))) for c in turn_color)

        turn_surface = self.font.render(turn_text, True, turn_color)
        turn_rect = turn_surface.get_rect(center=(400, 100))

        # Add background for turn indicator
        bg_rect = turn_rect.inflate(20, 10)
        pygame.draw.rect(draw_target, (0, 0, 0), bg_rect)
        pygame.draw.rect(draw_target, turn_color, bg_rect, 2)

        draw_target.blit(turn_surface, turn_rect)