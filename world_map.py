"""
World Map System for Magitech RPG
Creates a Zelda-inspired tile-based world map
"""

import pygame
import random
import json
from typing import Dict, List, Tuple, Optional
from assets.world_tiles import WorldTiles


class WorldMap:
    def __init__(self, width: int = 50, height: int = 40):
        self.width = width
        self.height = height
        self.tile_size = 32

        # Map data
        self.tiles = [[0 for _ in range(width)] for _ in range(height)]
        self.collision_map = [[False for _ in range(width)] for _ in range(height)]
        self.entity_map = {}  # Position -> Entity data

        # Tile system
        self.world_tiles = WorldTiles()

        # Generated structures
        self.dungeons = []
        self.towns = []
        self.forests = []
        self.lakes = []

        # Camera system
        self.camera_x = 0
        self.camera_y = 0

        # Generate initial world
        self.generate_world()

    def generate_world(self):
        """Generate a Zelda-inspired world map"""
        # Start with grass base
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x] = self.world_tiles.GRASS

        # Generate terrain features
        self.generate_forests()
        self.generate_lakes()
        self.generate_mountains()
        self.generate_paths()
        self.generate_structures()

        # Set collision data
        self.update_collision_map()

    def generate_forests(self):
        """Generate forest areas"""
        num_forests = random.randint(3, 6)

        for _ in range(num_forests):
            # Random forest center
            center_x = random.randint(5, self.width - 5)
            center_y = random.randint(5, self.height - 5)

            forest_size = random.randint(3, 8)

            forest_area = []
            for dy in range(-forest_size, forest_size + 1):
                for dx in range(-forest_size, forest_size + 1):
                    x, y = center_x + dx, center_y + dy

                    if (0 <= x < self.width and 0 <= y < self.height and
                            dx * dx + dy * dy <= forest_size * forest_size):

                        # Vary tree density
                        if random.random() < 0.7:
                            if random.random() < 0.1:
                                self.tiles[y][x] = self.world_tiles.TREE_DARK
                            else:
                                self.tiles[y][x] = self.world_tiles.TREE
                        forest_area.append((x, y))

            self.forests.append({
                'center': (center_x, center_y),
                'size': forest_size,
                'tiles': forest_area
            })

    def generate_lakes(self):
        """Generate lake areas"""
        num_lakes = random.randint(2, 4)

        for _ in range(num_lakes):
            center_x = random.randint(8, self.width - 8)
            center_y = random.randint(8, self.height - 8)

            lake_size = random.randint(2, 5)

            lake_area = []
            for dy in range(-lake_size, lake_size + 1):
                for dx in range(-lake_size, lake_size + 1):
                    x, y = center_x + dx, center_y + dy

                    if (0 <= x < self.width and 0 <= y < self.height and
                            dx * dx + dy * dy <= lake_size * lake_size):

                        distance = (dx * dx + dy * dy) ** 0.5
                        if distance <= lake_size * 0.6:
                            self.tiles[y][x] = self.world_tiles.WATER_DEEP
                        elif distance <= lake_size * 0.8:
                            self.tiles[y][x] = self.world_tiles.WATER
                        else:
                            self.tiles[y][x] = self.world_tiles.SAND

                        lake_area.append((x, y))

            self.lakes.append({
                'center': (center_x, center_y),
                'size': lake_size,
                'tiles': lake_area
            })

    def generate_mountains(self):
        """Generate mountain ranges"""
        num_ranges = random.randint(1, 3)

        for _ in range(num_ranges):
            # Create mountain range
            start_x = random.randint(0, self.width - 1)
            start_y = random.randint(0, self.height - 1)

            # Random direction for range
            direction = random.choice(['horizontal', 'vertical', 'diagonal'])
            length = random.randint(8, 15)

            for i in range(length):
                if direction == 'horizontal':
                    x = start_x + i
                    y = start_y + random.randint(-2, 2)
                elif direction == 'vertical':
                    x = start_x + random.randint(-2, 2)
                    y = start_y + i
                else:  # diagonal
                    x = start_x + i
                    y = start_y + i + random.randint(-1, 1)

                if 0 <= x < self.width and 0 <= y < self.height:
                    if random.random() < 0.8:
                        if random.random() < 0.3:
                            self.tiles[y][x] = self.world_tiles.MOUNTAIN_PEAK
                        else:
                            self.tiles[y][x] = self.world_tiles.MOUNTAIN
                    else:
                        self.tiles[y][x] = self.world_tiles.STONE

    def generate_paths(self):
        """Generate paths connecting important areas"""
        # Create main roads
        main_paths = [
            # Horizontal path through middle
            [(x, self.height // 2) for x in range(0, self.width, 2)],
            # Vertical path through middle
            [(self.width // 2, y) for y in range(0, self.height, 2)]
        ]

        for path in main_paths:
            for x, y in path:
                if 0 <= x < self.width and 0 <= y < self.height:
                    # Don't overwrite water or mountains
                    current_tile = self.tiles[y][x]
                    if current_tile not in [self.world_tiles.WATER, self.world_tiles.WATER_DEEP,
                                            self.world_tiles.MOUNTAIN, self.world_tiles.MOUNTAIN_PEAK]:
                        self.tiles[y][x] = self.world_tiles.PATH

    def generate_structures(self):
        """Generate towns, dungeons, and other structures"""
        # Generate towns
        num_towns = random.randint(2, 4)
        for _ in range(num_towns):
            self.place_town()

        # Generate dungeons
        num_dungeons = random.randint(3, 6)
        for _ in range(num_dungeons):
            self.place_dungeon()

        # Generate smaller structures
        self.place_misc_structures()

    def place_town(self):
        """Place a town on the map"""
        attempts = 0
        while attempts < 20:
            x = random.randint(3, self.width - 4)
            y = random.randint(3, self.height - 4)

            # Check if area is suitable (mostly grass/path)
            suitable = True
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    tx, ty = x + dx, y + dy
                    if 0 <= tx < self.width and 0 <= ty < self.height:
                        tile = self.tiles[ty][tx]
                        if tile in [self.world_tiles.WATER, self.world_tiles.WATER_DEEP,
                                    self.world_tiles.MOUNTAIN, self.world_tiles.MOUNTAIN_PEAK]:
                            suitable = False
                            break
                if not suitable:
                    break

            if suitable:
                # Create town layout
                town_tiles = []

                # Central building (inn/shop)
                self.tiles[y][x] = self.world_tiles.BUILDING
                town_tiles.append((x, y))

                # Houses around center
                for dy in [-2, -1, 1, 2]:
                    for dx in [-2, -1, 1, 2]:
                        tx, ty = x + dx, y + dy
                        if (0 <= tx < self.width and 0 <= ty < self.height and
                                random.random() < 0.6):
                            self.tiles[ty][tx] = self.world_tiles.HOUSE
                            town_tiles.append((tx, ty))

                # Add some paths within town
                for dy in range(-1, 2):
                    if 0 <= x < self.width and 0 <= y + dy < self.height:
                        if self.tiles[y + dy][x] not in [self.world_tiles.BUILDING, self.world_tiles.HOUSE]:
                            self.tiles[y + dy][x] = self.world_tiles.PATH

                for dx in range(-1, 2):
                    if 0 <= x + dx < self.width and 0 <= y < self.height:
                        if self.tiles[y][x + dx] not in [self.world_tiles.BUILDING, self.world_tiles.HOUSE]:
                            self.tiles[y][x + dx] = self.world_tiles.PATH

                self.towns.append({
                    'center': (x, y),
                    'tiles': town_tiles,
                    'name': f"Town_{len(self.towns) + 1}"
                })
                break

            attempts += 1

    def place_dungeon(self):
        """Place a dungeon entrance"""
        attempts = 0
        while attempts < 20:
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)

            # Prefer to place near mountains or in forests
            nearby_terrain = []
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    tx, ty = x + dx, y + dy
                    if 0 <= tx < self.width and 0 <= ty < self.height:
                        nearby_terrain.append(self.tiles[ty][tx])

            mountain_count = nearby_terrain.count(self.world_tiles.MOUNTAIN)
            mountain_peak_count = nearby_terrain.count(self.world_tiles.MOUNTAIN_PEAK)
            tree_count = nearby_terrain.count(self.world_tiles.TREE)

            # Good location if near mountains or trees
            if mountain_count + mountain_peak_count + tree_count > 3:
                self.tiles[y][x] = self.world_tiles.DUNGEON_ENTRANCE

                self.dungeons.append({
                    'entrance': (x, y),
                    'type': random.choice(['cave', 'ruins', 'tower']),
                    'level': random.randint(1, 5)
                })
                break

            attempts += 1

    def place_misc_structures(self):
        """Place miscellaneous structures"""
        num_structures = random.randint(5, 10)

        for _ in range(num_structures):
            x = random.randint(1, self.width - 2)
            y = random.randint(1, self.height - 2)

            # Don't place on water or existing structures
            if (self.tiles[y][x] not in [self.world_tiles.WATER, self.world_tiles.WATER_DEEP,
                                         self.world_tiles.BUILDING, self.world_tiles.HOUSE,
                                         self.world_tiles.DUNGEON_ENTRANCE]):

                structure_type = random.choice(['chest', 'shrine', 'ruins', 'statue'])

                if structure_type == 'chest':
                    self.tiles[y][x] = self.world_tiles.CHEST
                    self.entity_map[(x, y)] = {
                        'type': 'chest',
                        'loot': self.generate_chest_loot(),
                        'opened': False
                    }
                elif structure_type == 'shrine':
                    self.tiles[y][x] = self.world_tiles.SHRINE
                    self.entity_map[(x, y)] = {
                        'type': 'shrine',
                        'blessing': random.choice(['health', 'mana', 'strength', 'wisdom'])
                    }
                elif structure_type == 'ruins':
                    self.tiles[y][x] = self.world_tiles.RUINS
                elif structure_type == 'statue':
                    self.tiles[y][x] = self.world_tiles.STATUE

    def generate_chest_loot(self) -> List[Dict]:
        """Generate loot for treasure chests"""
        loot = []

        # Gold
        gold_amount = random.randint(10, 100)
        loot.append({'type': 'gold', 'amount': gold_amount})

        # Random item chance
        if random.random() < 0.7:
            items = [
                {'name': 'Health Potion', 'type': 'consumable', 'effect': 'heal', 'value': 25},
                {'name': 'Mana Potion', 'type': 'consumable', 'effect': 'mana', 'value': 20},
                {'name': 'Iron Sword', 'type': 'weapon', 'damage': 8, 'level': 2},
                {'name': 'Steel Shield', 'type': 'armor', 'defense': 3, 'level': 2},
                {'name': 'Magic Ring', 'type': 'accessory', 'effect': 'intelligence', 'value': 2}
            ]
            loot.append(random.choice(items))

        return loot

    def update_collision_map(self):
        """Update collision detection map"""
        for y in range(self.height):
            for x in range(self.width):
                tile = self.tiles[y][x]

                # Set collision for impassable tiles
                self.collision_map[y][x] = tile in [
                    self.world_tiles.WATER_DEEP,
                    self.world_tiles.MOUNTAIN,
                    self.world_tiles.MOUNTAIN_PEAK,
                    self.world_tiles.TREE,
                    self.world_tiles.TREE_DARK,
                    self.world_tiles.BUILDING,
                    self.world_tiles.HOUSE
                ]

    def is_passable(self, x: int, y: int) -> bool:
        """Check if a tile position is passable"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False

        return not self.collision_map[y][x]

    def get_tile_at(self, x: int, y: int) -> int:
        """Get tile type at position"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return 0

    def get_entity_at(self, x: int, y: int) -> Optional[Dict]:
        """Get entity at position"""
        return self.entity_map.get((x, y))

    def interact_with_tile(self, x: int, y: int, player_data: Dict) -> Optional[Dict]:
        """Handle interaction with a tile"""
        tile = self.get_tile_at(x, y)
        entity = self.get_entity_at(x, y)

        result = None

        if entity and entity['type'] == 'chest' and not entity.get('opened', False):
            # Open chest
            entity['opened'] = True
            result = {
                'type': 'loot',
                'items': entity['loot'],
                'message': "You found treasure!"
            }

        elif entity and entity['type'] == 'shrine':
            # Blessing from shrine
            blessing = entity['blessing']
            result = {
                'type': 'blessing',
                'blessing': blessing,
                'message': f"You receive a blessing of {blessing}!"
            }

        elif tile == self.world_tiles.DUNGEON_ENTRANCE:
            # Enter dungeon
            dungeon = next((d for d in self.dungeons if d['entrance'] == (x, y)), None)
            if dungeon:
                result = {
                    'type': 'dungeon',
                    'dungeon_data': dungeon,
                    'message': f"You enter a {dungeon['type']}..."
                }

        elif tile in [self.world_tiles.BUILDING, self.world_tiles.HOUSE]:
            # Enter building
            result = {
                'type': 'building',
                'building_type': 'shop' if tile == self.world_tiles.BUILDING else 'house',
                'message': "You enter the building..."
            }

        return result

    def update_camera(self, target_x: float, target_y: float, screen_width: int, screen_height: int):
        """Update camera position to follow target"""
        # Convert world coordinates to tile coordinates
        tile_x = int(target_x // self.tile_size)
        tile_y = int(target_y // self.tile_size)

        # Calculate camera position to center on target
        self.camera_x = target_x - screen_width // 2
        self.camera_y = target_y - screen_height // 2

        # Clamp camera to world bounds
        max_camera_x = (self.width * self.tile_size) - screen_width
        max_camera_y = (self.height * self.tile_size) - screen_height

        self.camera_x = max(0, min(self.camera_x, max_camera_x))
        self.camera_y = max(0, min(self.camera_y, max_camera_y))

    def render(self, screen: pygame.Surface, screen_width: int, screen_height: int):
        """Render the visible portion of the world map"""
        # Calculate visible tile range
        start_tile_x = max(0, int(self.camera_x // self.tile_size) - 1)
        end_tile_x = min(self.width, int((self.camera_x + screen_width) // self.tile_size) + 2)
        start_tile_y = max(0, int(self.camera_y // self.tile_size) - 1)
        end_tile_y = min(self.height, int((self.camera_y + screen_height) // self.tile_size) + 2)

        # Render tiles
        for y in range(start_tile_y, end_tile_y):
            for x in range(start_tile_x, end_tile_x):
                tile_type = self.tiles[y][x]

                # Calculate screen position
                screen_x = (x * self.tile_size) - self.camera_x
                screen_y = (y * self.tile_size) - self.camera_y

                # Get tile color/surface
                tile_surface = self.world_tiles.get_tile_surface(tile_type, self.tile_size)
                screen.blit(tile_surface, (screen_x, screen_y))

                # Render entity overlays
                entity = self.get_entity_at(x, y)
                if entity:
                    overlay_surface = self.world_tiles.get_entity_overlay(entity, self.tile_size)
                    if overlay_surface:
                        screen.blit(overlay_surface, (screen_x, screen_y))

    def world_to_screen(self, world_x: float, world_y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates"""
        screen_x = int(world_x - self.camera_x)
        screen_y = int(world_y - self.camera_y)
        return screen_x, screen_y

    def screen_to_world(self, screen_x: int, screen_y: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        world_x = screen_x + self.camera_x
        world_y = screen_y + self.camera_y
        return world_x, world_y

    def get_spawn_position(self) -> Tuple[int, int]:
        """Get a safe spawn position for new players"""
        # Try to find a good spawn near the center
        center_x, center_y = self.width // 2, self.height // 2

        for radius in range(1, 10):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    x, y = center_x + dx, center_y + dy

                    if (0 <= x < self.width and 0 <= y < self.height and
                            self.is_passable(x, y)):
                        return x * self.tile_size + self.tile_size // 2, y * self.tile_size + self.tile_size // 2

        # Fallback to exact center
        return center_x * self.tile_size, center_y * self.tile_size

    def save_to_file(self, filename: str):
        """Save world map to file"""
        world_data = {
            'width': self.width,
            'height': self.height,
            'tiles': self.tiles,
            'dungeons': self.dungeons,
            'towns': self.towns,
            'forests': self.forests,
            'lakes': self.lakes,
            'entity_map': {f"{k[0]},{k[1]}": v for k, v in self.entity_map.items()}
        }

        with open(filename, 'w') as f:
            json.dump(world_data, f)

    def load_from_file(self, filename: str):
        """Load world map from file"""
        try:
            with open(filename, 'r') as f:
                world_data = json.load(f)

            self.width = world_data['width']
            self.height = world_data['height']
            self.tiles = world_data['tiles']
            self.dungeons = world_data['dungeons']
            self.towns = world_data['towns']
            self.forests = world_data['forests']
            self.lakes = world_data['lakes']

            # Convert entity map keys back to tuples
            self.entity_map = {}
            for key_str, value in world_data.get('entity_map', {}).items():
                x, y = map(int, key_str.split(','))
                self.entity_map[(x, y)] = value

            self.update_collision_map()
            return True

        except Exception as e:
            print(f"Failed to load world map: {e}")
            return False
