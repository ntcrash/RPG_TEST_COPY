class EnemyManager:
    """Enhanced enemy manager with level-based scaling"""

    def __init__(self):
        self.current_book_level = 1
        self.world_theme = "grassland"  # Current world theme
        self.enemy_templates = self._create_enhanced_enemy_templates()

    def _create_enhanced_enemy_templates(self):
        """Create enhanced enemy templates organized by world themes"""
        return {
            "grassland": {
                "basic": [
                    {"name": "Wild Goblin", "hp_base": 60, "aspect": "earth_level_1"},
                    {"name": "Forest Wolf", "hp_base": 70, "aspect": "life_level_1"},
                    {"name": "Bandit Scout", "hp_base": 65, "aspect": "fire_level_1"},
                    {"name": "Wild Boar", "hp_base": 80, "aspect": "earth_level_1"},
                ],
                "elite": [
                    {"name": "Goblin Chieftain", "hp_base": 120, "aspect": "earth_level_2"},
                    {"name": "Alpha Wolf", "hp_base": 130, "aspect": "life_level_2"},
                    {"name": "Bandit Leader", "hp_base": 125, "aspect": "fire_level_2"},
                    {"name": "Giant Boar", "hp_base": 140, "aspect": "earth_level_2"},
                ],
                "champion": [
                    {"name": "Orc Warlord", "hp_base": 180, "aspect": "fire_level_3"},
                    {"name": "Dire Wolf Pack Leader", "hp_base": 170, "aspect": "life_level_3"},
                    {"name": "Forest Guardian", "hp_base": 190, "aspect": "life_level_3"},
                ],
                "ancient": [
                    {"name": "Ancient Treant", "hp_base": 250, "aspect": "life_level_4"},
                    {"name": "Elder Dragon Wyrmling", "hp_base": 280, "aspect": "fire_level_4"},
                ],
                "boss": [
                    {"name": "🐉 FOREST DRAGON KING 🐉", "hp_base": 400, "aspect": "fire_level_5"},
                ]
            },
            "ice": {
                "basic": [
                    {"name": "Ice Goblin", "hp_base": 70, "aspect": "water_level_1"},
                    {"name": "Frost Wolf", "hp_base": 75, "aspect": "water_level_1"},
                    {"name": "Snow Troll", "hp_base": 85, "aspect": "water_level_1"},
                    {"name": "Ice Sprite", "hp_base": 60, "aspect": "water_level_1"},
                ],
                "elite": [
                    {"name": "Frost Giant", "hp_base": 140, "aspect": "water_level_2"},
                    {"name": "Ice Wraith", "hp_base": 120, "aspect": "water_level_2"},
                    {"name": "Yeti Warrior", "hp_base": 160, "aspect": "water_level_2"},
                ],
                "champion": [
                    {"name": "Glacier Colossus", "hp_base": 220, "aspect": "water_level_3"},
                    {"name": "Frost Lich", "hp_base": 200, "aspect": "void_level_3"},
                ],
                "ancient": [
                    {"name": "Ancient Ice Dragon", "hp_base": 300, "aspect": "water_level_4"},
                    {"name": "Eternal Frost Guardian", "hp_base": 280, "aspect": "water_level_4"},
                ],
                "boss": [
                    {"name": "❄️ ICE EMPEROR ❄️", "hp_base": 450, "aspect": "water_level_5"},
                ]
            },
            "shadow": {
                "basic": [
                    {"name": "Shadow Imp", "hp_base": 65, "aspect": "void_level_1"},
                    {"name": "Nightmare Hound", "hp_base": 75, "aspect": "void_level_1"},
                    {"name": "Dark Wraith", "hp_base": 70, "aspect": "void_level_1"},
                    {"name": "Void Stalker", "hp_base": 80, "aspect": "void_level_1"},
                ],
                "elite": [
                    {"name": "Shadow Knight", "hp_base": 130, "aspect": "void_level_2"},
                    {"name": "Nightmare Lord", "hp_base": 140, "aspect": "void_level_2"},
                    {"name": "Void Assassin", "hp_base": 110, "aspect": "void_level_2"},
                ],
                "champion": [
                    {"name": "Dark Paladin", "hp_base": 200, "aspect": "void_level_3"},
                    {"name": "Nightmare Dragon", "hp_base": 230, "aspect": "void_level_3"},
                ],
                "ancient": [
                    {"name": "Ancient Shadow Lord", "hp_base": 320, "aspect": "void_level_4"},
                    {"name": "Void Leviathan", "hp_base": 300, "aspect": "void_level_4"},
                ],
                "boss": [
                    {"name": "🌑 SHADOW EMPEROR 🌑", "hp_base": 500, "aspect": "void_level_5"},
                ]
            },
            "elemental": {
                "basic": [
                    {"name": "Fire Elemental", "hp_base": 75, "aspect": "fire_level_1"},
                    {"name": "Lightning Sprite", "hp_base": 60, "aspect": "dream_level_1"},
                    {"name": "Earth Golem", "hp_base": 90, "aspect": "earth_level_1"},
                    {"name": "Storm Wisp", "hp_base": 65, "aspect": "dream_level_1"},
                ],
                "elite": [
                    {"name": "Greater Fire Elemental", "hp_base": 140, "aspect": "fire_level_2"},
                    {"name": "Storm Lord", "hp_base": 130, "aspect": "dream_level_2"},
                    {"name": "Stone Titan", "hp_base": 170, "aspect": "earth_level_2"},
                ],
                "champion": [
                    {"name": "Elemental Chaos Spawn", "hp_base": 210, "aspect": "fire_level_3"},
                    {"name": "Thunder King", "hp_base": 200, "aspect": "dream_level_3"},
                ],
                "ancient": [
                    {"name": "Primordial Fire", "hp_base": 330, "aspect": "fire_level_4"},
                    {"name": "Ancient Storm Dragon", "hp_base": 310, "aspect": "dream_level_4"},
                ],
                "boss": [
                    {"name": "⚡ ELEMENTAL OVERLORD ⚡", "hp_base": 550, "aspect": "fire_level_5"},
                ]
            },
            "cosmic": {
                "basic": [
                    {"name": "Astral Wanderer", "hp_base": 80, "aspect": "dream_level_2"},
                    {"name": "Void Walker", "hp_base": 85, "aspect": "void_level_2"},
                    {"name": "Star Fragment", "hp_base": 75, "aspect": "life_level_2"},
                ],
                "elite": [
                    {"name": "Cosmic Horror", "hp_base": 160, "aspect": "void_level_3"},
                    {"name": "Stellar Guardian", "hp_base": 150, "aspect": "life_level_3"},
                    {"name": "Dimension Ripper", "hp_base": 140, "aspect": "dream_level_3"},
                ],
                "champion": [
                    {"name": "Galactic Destroyer", "hp_base": 240, "aspect": "void_level_4"},
                    {"name": "Starborn Titan", "hp_base": 250, "aspect": "life_level_4"},
                ],
                "ancient": [
                    {"name": "Ancient Cosmic Entity", "hp_base": 400, "aspect": "void_level_5"},
                    {"name": "Universe Devourer", "hp_base": 420, "aspect": "dream_level_5"},
                ],
                "boss": [
                    {"name": "✨ THE NEXUS GUARDIAN ✨", "hp_base": 666, "aspect": "life_level_5"},
                ]
            }
        }

    def set_world_theme(self, theme):
        """Set the current world theme"""
        valid_themes = ["grassland", "ice", "shadow", "elemental", "cosmic"]
        if theme in valid_themes:
            self.world_theme = theme
        else:
            self.world_theme = "grassland"

    def create_scaled_enemy(self):
        """Create an enemy scaled to current difficulty and world theme"""
        # Determine enemy tier based on book level
        if self.current_book_level <= 3:
            tier = "basic"
        elif self.current_book_level <= 6:
            tier = "elite"
        elif self.current_book_level <= 10:
            tier = "champion"
        elif self.current_book_level <= 15:
            tier = "ancient"
        else:
            tier = "boss"

        # Get enemies for current world theme
        theme_enemies = self.enemy_templates.get(self.world_theme, self.enemy_templates["grassland"])
        tier_enemies = theme_enemies.get(tier, theme_enemies["basic"])

        # Select random enemy from tier
        enemy_template = random.choice(tier_enemies)

        # Scale HP based on current book level
        base_hp = enemy_template["hp_base"]
        level_scaling = (self.current_book_level - 1) * 12
        scaled_hp = base_hp + level_scaling + random.randint(-10, 15)

        # Create enemy data
        enemy_data = {
            "Name": enemy_template["name"],
            "Hit_Points": max(1, scaled_hp),
            "Aspect1": enemy_template["aspect"],
            "Level": max(1, self.current_book_level),
            "Experience_Points": 0,
            "Tier": tier,
            "Theme": self.world_theme
        }

        return enemy_data

    def create_scaled_boss(self):
        """Create a boss scaled to current difficulty"""
        theme_enemies = self.enemy_templates.get(self.world_theme, self.enemy_templates["grassland"])
        boss_template = random.choice(theme_enemies["boss"])

        base_hp = boss_template["hp_base"]
        level_scaling = (self.current_book_level - 1) * 30
        scaled_hp = base_hp + level_scaling + random.randint(-30, 50)

        boss_data = {
            "Name": boss_template["name"],
            "Hit_Points": max(1, scaled_hp),
            "Aspect1": boss_template["aspect"],
            "Level": max(1, self.current_book_level + 3),
            "Experience_Points": 0,
            "Tier": "boss",
            "Theme": self.world_theme
        }

        return boss_data

    def create_specific_enemy(self, enemy_type, level_override=None):
        """Create a specific type of enemy"""
        level = level_override or self.current_book_level

        # Search through all themes and tiers for the enemy type
        for theme_name, theme_data in self.enemy_templates.items():
            for tier, enemies in theme_data.items():
                for enemy in enemies:
                    if enemy_type.lower() in enemy["name"].lower():
                        base_hp = enemy["hp_base"]
                        level_scaling = (level - 1) * 15
                        scaled_hp = base_hp + level_scaling

                        return {
                            "Name": enemy["name"],
                            "Hit_Points": max(1, scaled_hp),
                            "Aspect1": enemy["aspect"],
                            "Level": level,
                            "Experience_Points": 0,
                            "Tier": tier,
                            "Theme": theme_name
                        }

        # Fallback to basic enemy
        return self.create_scaled_enemy()

    def set_difficulty_level(self, level):
        """Set the current difficulty level and automatically determine theme"""
        self.current_book_level = max(1, min(25, level))

        # Auto-set theme based on level range
        if level <= 4:
            self.set_world_theme("grassland")
        elif level <= 8:
            self.set_world_theme("ice")
        elif level <= 12:
            self.set_world_theme("shadow")
        elif level <= 16:
            self.set_world_theme("elemental")
        else:
            self.set_world_theme("cosmic")

    def get_enemy_reward_multiplier(self, enemy_data):
        """Get reward multiplier based on enemy tier"""
        tier = enemy_data.get("Tier", "basic")
        multipliers = {
            "basic": 1.0,
            "elite": 1.4,
            "champion": 1.8,
            "ancient": 2.5,
            "boss": 4.0
        }
        return multipliers.get(tier, 1.0)

    def get_theme_description(self, theme):
        """Get description of world theme"""
        descriptions = {
            "grassland": "Peaceful forests and meadows with natural creatures",
            "ice": "Frozen wasteland filled with ice-based enemies",
            "shadow": "Dark realm where nightmares come to life",
            "elemental": "Chaotic realm where elements collide",
            "cosmic": "Astral plane with beings beyond comprehension"
        }
        return descriptions.get(theme, "Unknown realm")