"""
World Tiles System for Magitech RPG
Defines tile types and provides tile rendering
"""

import pygame
from typing import Dict, Optional


class WorldTiles:
    # Tile type constants
    GRASS = 0
    WATER = 1
    WATER_DEEP = 2
    SAND = 3
    STONE = 4
    PATH = 5
    TREE = 6
    TREE_DARK = 7
    MOUNTAIN = 8
    MOUNTAIN_PEAK = 9
    BUILDING = 10
    HOUSE = 11
    DUNGEON_ENTRANCE = 12
    CHEST = 13
    SHRINE = 14
    RUINS = 15
    STATUE = 16

    def __init__(self):
        self.tile_surfaces = {}
        self.tile_colors = {
            self.GRASS: (34, 139, 34),  # Forest green
            self.WATER: (0, 100, 200),  # Blue
            self.WATER_DEEP: (0, 50, 150),  # Dark blue
            self.SAND: (238, 203, 173),  # Sandy brown
            self.STONE: (128, 128, 128),  # Gray
            self.PATH: (139, 115, 85),  # Brown path
            self.TREE: (0, 100, 0),  # Dark green
            self.TREE_DARK: (0, 80, 0),  # Darker green
            self.MOUNTAIN: (105, 105, 105),  # Dark gray
            self.MOUNTAIN_PEAK: (169, 169, 169),  # Light gray
            self.BUILDING: (160, 82, 45),  # Brown building
            self.HOUSE: (210, 180, 140),  # Tan house
            self.DUNGEON_ENTRANCE: (64, 64, 64),  # Very dark gray
            self.CHEST: (255, 215, 0),  # Gold
            self.SHRINE: (255, 255, 255),  # White
            self.RUINS: (112, 128, 144),  # Slate gray
            self.STATUE: (192, 192, 192)  # Silver
        }

    def get_tile_surface(self, tile_type: int, size: int) -> pygame.Surface:
        """Get or create a surface for the given tile type"""
        cache_key = f"{tile_type}_{size}"

        if cache_key not in self.tile_surfaces:
            self.tile_surfaces[cache_key] = self._create_tile_surface(tile_type, size)

        return self.tile_surfaces[cache_key]

    def _create_tile_surface(self, tile_type: int, size: int) -> pygame.Surface:
        """Create a surface for a specific tile type"""
        surface = pygame.Surface((size, size))
        base_color = self.tile_colors.get(tile_type, (100, 100, 100))

        if tile_type == self.GRASS:
            # Grass with some texture
            surface.fill(base_color)
            # Add some darker grass blades
            for i in range(8):
                x = (i * size // 8) + (size // 16)
                y = size // 2
                darker_green = (max(0, base_color[0] - 20), max(0, base_color[1] - 20), base_color[2])
                pygame.draw.line(surface, darker_green, (x, y - 3), (x, y + 3), 1)

        elif tile_type == self.WATER:
            # Water with simple wave effect
            surface.fill(base_color)
            wave_color = (min(255, base_color[0] + 30), min(255, base_color[1] + 30), min(255, base_color[2] + 30))
            for i in range(0, size, 4):
                pygame.draw.line(surface, wave_color, (i, size // 4), (i + 2, size // 4), 1)
                pygame.draw.line(surface, wave_color, (i + 2, 3 * size // 4), (i + 4, 3 * size // 4), 1)

        elif tile_type == self.WATER_DEEP:
            # Deeper water
            surface.fill(base_color)
            # Darker waves
            darker_blue = (max(0, base_color[0] - 20), max(0, base_color[1] - 20), base_color[2])
            for i in range(0, size, 6):
                pygame.draw.line(surface, darker_blue, (i, size // 3), (i + 3, size // 3), 2)

        elif tile_type == self.SAND:
            # Sand with speckled texture
            surface.fill(base_color)
            for i in range(20):
                x = i * size // 20
                y = (i * 7) % size  # Pseudo-random pattern
                lighter_sand = (
                min(255, base_color[0] + 15), min(255, base_color[1] + 15), min(255, base_color[2] + 15))
                pygame.draw.circle(surface, lighter_sand, (x, y), 1)

        elif tile_type == self.STONE:
            # Stone with cracks
            surface.fill(base_color)
            crack_color = (max(0, base_color[0] - 30), max(0, base_color[1] - 30), max(0, base_color[2] - 30))
            pygame.draw.line(surface, crack_color, (size // 4, 0), (size // 2, size // 2), 1)
            pygame.draw.line(surface, crack_color, (3 * size // 4, size // 4), (size // 2, size), 1)

        elif tile_type == self.PATH:
            # Path with edge definition
            surface.fill(base_color)
            edge_color = (max(0, base_color[0] - 20), max(0, base_color[1] - 20), max(0, base_color[2] - 20))
            pygame.draw.rect(surface, edge_color, (0, 0, size, 2))
            pygame.draw.rect(surface, edge_color, (0, size - 2, size, 2))

        elif tile_type in [self.TREE, self.TREE_DARK]:
            # Tree with trunk and leaves
            surface.fill((34, 139, 34))  # Grass background
            trunk_color = (101, 67, 33)  # Brown
            leaves_color = base_color

            # Draw trunk
            trunk_width = size // 6
            trunk_x = size // 2 - trunk_width // 2
            pygame.draw.rect(surface, trunk_color, (trunk_x, 2 * size // 3, trunk_width, size // 3))

            # Draw leaves (circle)
            pygame.draw.circle(surface, leaves_color, (size // 2, size // 3), size // 3)

        elif tile_type in [self.MOUNTAIN, self.MOUNTAIN_PEAK]:
            # Mountain triangle
            surface.fill((34, 139, 34))  # Grass background
            peak_color = base_color
            if tile_type == self.MOUNTAIN_PEAK:
                # Add snow cap
                snow_color = (255, 255, 255)
                points = [(size // 2, size // 6), (size // 4, size // 2), (3 * size // 4, size // 2)]
                pygame.draw.polygon(surface, peak_color, points)
                # Snow cap
                snow_points = [(size // 2, size // 6), (size // 2 - size // 8, size // 3),
                               (size // 2 + size // 8, size // 3)]
                pygame.draw.polygon(surface, snow_color, snow_points)
            else:
                points = [(size // 2, size // 4), (size // 6, 3 * size // 4), (5 * size // 6, 3 * size // 4)]
                pygame.draw.polygon(surface, peak_color, points)

        elif tile_type == self.BUILDING:
            # Building with roof
            surface.fill((34, 139, 34))  # Grass background
            # Building base
            building_rect = pygame.Rect(size // 8, size // 3, 3 * size // 4, 2 * size // 3)
            pygame.draw.rect(surface, base_color, building_rect)
            # Roof
            roof_color = (139, 69, 19)  # Darker brown
            roof_points = [(0, size // 3), (size // 2, size // 8), (size, size // 3)]
            pygame.draw.polygon(surface, roof_color, roof_points)
            # Door
            door_color = (101, 67, 33)
            door_rect = pygame.Rect(size // 2 - size // 12, 2 * size // 3, size // 6, size // 3)
            pygame.draw.rect(surface, door_color, door_rect)

        elif tile_type == self.HOUSE:
            # Smaller house
            surface.fill((34, 139, 34))  # Grass background
            # House base
            house_rect = pygame.Rect(size // 6, size // 2, 2 * size // 3, size // 2)
            pygame.draw.rect(surface, base_color, house_rect)
            # Roof
            roof_color = (160, 82, 45)  # Brown roof
            roof_points = [(size // 6, size // 2), (size // 2, size // 4), (5 * size // 6, size // 2)]
            pygame.draw.polygon(surface, roof_color, roof_points)
            # Window
            window_color = (135, 206, 250)  # Light blue
            window_rect = pygame.Rect(size // 2 + size // 12, 2 * size // 3, size // 8, size // 8)
            pygame.draw.rect(surface, window_color, window_rect)

        elif tile_type == self.DUNGEON_ENTRANCE:
            # Cave entrance
            surface.fill((105, 105, 105))  # Mountain/stone background
            # Cave opening (black oval)
            cave_color = (0, 0, 0)
            pygame.draw.ellipse(surface, cave_color, (size // 4, size // 3, size // 2, size // 2))
            # Add some rocky texture
            rock_color = (169, 169, 169)
            for i in range(5):
                x = (i * size // 5) + size // 10
                y = size // 6
                pygame.draw.circle(surface, rock_color, (x, y), 2)

        elif tile_type == self.CHEST:
            # Treasure chest
            surface.fill((34, 139, 34))  # Grass background
            # Chest body
            chest_body = pygame.Rect(size // 4, size // 2, size // 2, size // 3)
            pygame.draw.rect(surface, base_color, chest_body)
            # Chest lid
            lid_color = (255, 223, 0)  # Lighter gold
            chest_lid = pygame.Rect(size // 4, size // 2 - size // 8, size // 2, size // 4)
            pygame.draw.rect(surface, lid_color, chest_lid)
            # Lock
            lock_color = (139, 115, 85)
            pygame.draw.circle(surface, lock_color, (size // 2, 2 * size // 3), 2)

        elif tile_type == self.SHRINE:
            # Shrine with pillar
            surface.fill((34, 139, 34))  # Grass background
            # Base
            base_rect = pygame.Rect(size // 3, 2 * size // 3, size // 3, size // 6)
            pygame.draw.rect(surface, (192, 192, 192), base_rect)
            # Pillar
            pillar_rect = pygame.Rect(size // 2 - size // 12, size // 4, size // 6, size // 2)
            pygame.draw.rect(surface, base_color, pillar_rect)
            # Top ornament
            pygame.draw.circle(surface, (255, 215, 0), (size // 2, size // 4), size // 12)

        elif tile_type == self.RUINS:
            # Ancient ruins
            surface.fill((34, 139, 34))  # Grass background
            # Broken pillars
            pillar_color = base_color
            pygame.draw.rect(surface, pillar_color, (size // 6, size // 2, size // 8, size // 2))
            pygame.draw.rect(surface, pillar_color, (2 * size // 3, size // 3, size // 8, 2 * size // 3))
            # Rubble
            rubble_color = (105, 105, 105)
            for i in range(3):
                x = size // 4 + i * size // 8
                y = 3 * size // 4
                pygame.draw.circle(surface, rubble_color, (x, y), 3)

        elif tile_type == self.STATUE:
            # Statue
            surface.fill((34, 139, 34))  # Grass background
            # Base
            base_rect = pygame.Rect(size // 4, 3 * size // 4, size // 2, size // 8)
            pygame.draw.rect(surface, (128, 128, 128), base_rect)
            # Statue body
            statue_rect = pygame.Rect(size // 2 - size // 8, size // 3, size // 4, size // 2)
            pygame.draw.rect(surface, base_color, statue_rect)
            # Statue head
            pygame.draw.circle(surface, base_color, (size // 2, size // 3), size // 8)

        else:
            # Unknown tile - use base color
            surface.fill(base_color)

        return surface

    def get_entity_overlay(self, entity: Dict, size: int) -> Optional[pygame.Surface]:
        """Get overlay surface for entities (like opened chests)"""
        entity_type = entity.get('type')

        if entity_type == 'chest' and entity.get('opened', False):
            # Show opened chest
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            surface.fill((0, 0, 0, 0))  # Transparent

            # Draw opened chest with sparkles
            sparkle_color = (255, 255, 0, 180)
            for i in range(4):
                x = size // 4 + (i % 2) * size // 2
                y = size // 3 + (i // 2) * size // 3
                pygame.draw.circle(surface, sparkle_color, (x, y), 2)

            return surface

        return None

    def get_tile_name(self, tile_type: int) -> str:
        """Get human-readable name for tile type"""
        names = {
            self.GRASS: "Grass",
            self.WATER: "Water",
            self.WATER_DEEP: "Deep Water",
            self.SAND: "Sand",
            self.STONE: "Stone",
            self.PATH: "Path",
            self.TREE: "Tree",
            self.TREE_DARK: "Dark Tree",
            self.MOUNTAIN: "Mountain",
            self.MOUNTAIN_PEAK: "Mountain Peak",
            self.BUILDING: "Building",
            self.HOUSE: "House",
            self.DUNGEON_ENTRANCE: "Dungeon Entrance",
            self.CHEST: "Treasure Chest",
            self.SHRINE: "Shrine",
            self.RUINS: "Ancient Ruins",
            self.STATUE: "Statue"
        }
        return names.get(tile_type, "Unknown")

    def is_passable(self, tile_type: int) -> bool:
        """Check if a tile type is passable"""
        impassable_tiles = [
            self.WATER_DEEP,
            self.MOUNTAIN,
            self.MOUNTAIN_PEAK,
            self.TREE,
            self.TREE_DARK,
            self.BUILDING,
            self.HOUSE
        ]
        return tile_type not in impassable_tiles

    def is_interactable(self, tile_type: int) -> bool:
        """Check if a tile type can be interacted with"""
        interactable_tiles = [
            self.CHEST,
            self.SHRINE,
            self.DUNGEON_ENTRANCE,
            self.BUILDING,
            self.HOUSE,
            self.STATUE
        ]
        return tile_type in interactable_tiles
