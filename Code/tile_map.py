from pathlib import Path
from Code.backend import pygame  # backend switch (real pygame or Arcade gfx shim)

# Get the directory where your script is located
script_dir = Path(__file__).parent

# Build paths
assets_dir = script_dir.parent / 'assets'
map_file = assets_dir / 'map.txt'


class EnhancedTileMap(pygame.sprite.Sprite):
    """Enhanced TileMap class from RPG2 demo with Zelda-style world"""

    # Legacy maps sprinkled decorative flower tiles ('F'/'f' = flower patches,
    # 'R'/'r' = single blooms) across the grass, producing a cluttered, busy
    # field. World Aesthetics (roadmap P5 #30) replaces that clutter with clean,
    # natural grass so paths and landmarks read clearly.
    FLOWER_CHARS = frozenset("FfRr")
    # Grass tile variants used to backfill decluttered flower tiles. Mixing the
    # three keeps the terrain from looking like one flat monotone block while
    # still being plain grass (no flowers).
    GRASS_VARIANTS = ("G", "g", "d")

    # --- Structured Paths (roadmap P5 #31) -------------------------------
    # The overworld's key interactables (boss dungeon, shop, rest area) sit at
    # fixed spots but nothing on the ground led the player toward them, so the
    # world read as a trackless field. ``carve_landmark_paths`` lays clear dirt
    # routes from the central hub out to each important area so the player
    # always has an obvious walking route to follow.
    TILE_PX = 24
    # Player spawn tile, mirrors EnhancedGameManager.PLAYER_START (480, 480).
    PLAYER_START_PX = (480, 480)
    # Characters already treated as walkable path/road tiles; painting over one
    # of these turns it into an intersection ('+') instead of a plain segment.
    PATH_CHARS = frozenset("p=|+ro")

    @classmethod
    def landmark_tiles(cls, cols, rows):
        """Return the (col, row) tile of each important area for a cols×rows map.

        Positions mirror where ``EnhancedGameManager`` actually places things:
        the boss dungeon at world centre (the hub), the shop in the top-right,
        the rest area in the bottom-right, and the player spawn. Derived from
        the grid size in the same pixel terms as the game so the routes always
        land on the real landmarks. Pure/deterministic — safe to unit-test.
        """
        world_w, world_h = cols * cls.TILE_PX, rows * cls.TILE_PX

        def to_tile(px, py):
            col = min(max(px // cls.TILE_PX, 0), max(cols - 1, 0))
            row = min(max(py // cls.TILE_PX, 0), max(rows - 1, 0))
            return col, row

        return {
            "hub": to_tile(world_w // 2, world_h // 2),      # boss dungeon centre
            "spawn": to_tile(*cls.PLAYER_START_PX),          # player spawn
            "shop": to_tile(world_w - 80, 20),               # top-right shop
            "rest": to_tile(world_w - 60, world_h - 60),     # bottom-right rest area
        }

    @classmethod
    def carve_landmark_paths(cls, lines):
        """Carve clear dirt routes from the central hub to each important area.

        Draws an L-shaped (Manhattan) path of dirt-path tiles from the world
        centre out to the player spawn, the shop, and the rest area, so every
        key destination has an obvious walking route. Where a route crosses an
        existing path (or another route) the cell becomes an intersection
        ('+'). Non-path terrain (grass, trees, water) is overwritten by the
        route only along its line. Pure/deterministic and length-preserving, so
        it is safe to unit-test without a display.
        """
        if not lines:
            return lines

        grid = [list(line) for line in lines]
        rows = len(grid)
        cols = max(len(r) for r in grid)
        # Normalise to a rectangular grid so column math is always in-bounds.
        for r in grid:
            if len(r) < cols:
                r.extend([cls.GRASS_VARIANTS[0]] * (cols - len(r)))

        # Only route on a full-size overworld: if the map is too small to even
        # contain the player spawn point, the landmarks all collapse onto one
        # tile and there is no meaningful route to draw, so leave it untouched
        # (this also keeps tiny probe/test maps from sprouting spurious paths).
        world_w, world_h = cols * cls.TILE_PX, rows * cls.TILE_PX
        spawn_px, spawn_py = cls.PLAYER_START_PX
        if spawn_px < world_w and spawn_py < world_h:
            marks = cls.landmark_tiles(cols, rows)

            def paint(col, row):
                ch = grid[row][col]
                grid[row][col] = "+" if ch in cls.PATH_CHARS else "p"

            def carve_l(a, b):
                (c0, r0), (c1, r1) = a, b
                # Horizontal leg along the hub's row, then vertical leg to target.
                for col in range(min(c0, c1), max(c0, c1) + 1):
                    paint(col, r0)
                for row in range(min(r0, r1), max(r0, r1) + 1):
                    paint(c1, row)

            hub = marks["hub"]
            for key in ("spawn", "shop", "rest"):
                carve_l(hub, marks[key])

        return ["".join(r) for r in grid]

    @classmethod
    def declutter_flowers(cls, line, row=0):
        """Replace decorative flower markers in a map line with grass variants.

        Each flower character (see ``FLOWER_CHARS``) is swapped for a grass tile
        chosen deterministically from ``GRASS_VARIANTS`` by its (row, column)
        position, so the terrain reads as clean, varied grass instead of a field
        of scattered flowers. Non-flower characters are left untouched. Pure and
        deterministic, so it is safe to unit-test without a display.
        """
        variants = cls.GRASS_VARIANTS
        out = []
        for col, ch in enumerate(line):
            if ch in cls.FLOWER_CHARS:
                out.append(variants[(row + col) % len(variants)])
            else:
                out.append(ch)
        return "".join(out)

    def __init__(self, sprite_sheet_path="overworldSmall2.png", map_data=None):
        super().__init__()
        self.map_data = map_data

        # Load tileset
        try:
            self.tiles = pygame.image.load(sprite_sheet_path)
        except:
            # Create fallback tileset with Zelda-inspired colors
            self.tiles = pygame.Surface((144, 144))
            # Create basic tiles with different colors (6x6 grid of 24x24 tiles)
            tile_colors = [
                # Row 1 - Grass variations
                (34, 139, 34),  # Forest green (grass)
                (50, 205, 50),  # Lime green (light grass)
                (0, 100, 0),  # Dark green (dark grass)
                (85, 107, 47),  # Dark olive (dirt)
                (160, 82, 45),  # Saddle brown (path)
                (205, 133, 63),  # Peru (sand)

                # Row 2 - Path and terrain
                (139, 69, 19),  # Saddle brown (dirt path)
                (160, 82, 45),  # Light brown (path)
                (34, 139, 34),  # Grass
                (0, 100, 0),  # Dark grass
                (50, 205, 50),  # Light grass
                (85, 107, 47),  # Olive (bush)

                # Row 3 - Grass variations (flowers removed for cleaner terrain)
                (46, 160, 46),  # Grass variant
                (40, 120, 40),  # Grass variant
                (34, 139, 34),  # Grass base
                (0, 100, 0),  # Dark grass
                (139, 69, 19),  # Tree trunk
                (0, 128, 0),  # Tree leaves

                # Row 4 - More variations
                (50, 205, 50),  # Light grass
                (34, 139, 34),  # Medium grass
                (0, 100, 0),  # Dark grass
                (85, 107, 47),  # Bush color
                (160, 82, 45),  # Path
                (139, 69, 19),  # Dirt

                # Row 5 - Special tiles
                (0, 191, 255),  # Deep sky blue (water)
                (100, 149, 237),  # Cornflower blue (water edge)
                (34, 139, 34),  # Grass
                (255, 255, 0),  # Yellow (special)
                (128, 0, 128),  # Purple (magic)
                (255, 0, 0),  # Red (danger)

                # Row 6 - Border tiles
                (139, 69, 19),  # Brown (border)
                (85, 107, 47),  # Dark olive
                (160, 82, 45),  # Light brown
                (34, 139, 34),  # Grass
                (0, 100, 0),  # Dark grass
                (50, 205, 50)  # Light grass
            ]

            for i, color in enumerate(tile_colors):
                x = (i % 6) * 24
                y = (i // 6) * 24
                pygame.draw.rect(self.tiles, color, (x, y, 24, 24))
                # Add some texture/detail
                if i == 16 or i == 17:  # Tree tiles
                    pygame.draw.circle(self.tiles, (0, 128, 0), (x + 12, y + 8), 8)
                    pygame.draw.rect(self.tiles, (139, 69, 19), (x + 10, y + 16, 4, 8))
                # Add border to all tiles
                pygame.draw.rect(self.tiles, (0, 0, 0), (x, y, 24, 24), 1)

        self.tile_size = 24
        self.map_width = 32  # Increased map size
        self.map_height = 24

    def load_map_from_data(self, map_lines):
        """Load map from string data - Zelda-style mapping system"""
        # Strip decorative flower clutter to clean grass before mapping tiles
        # (World Aesthetics, roadmap P5 #30).
        map_lines = [self.declutter_flowers(line, row) for row, line in enumerate(map_lines)]
        # Lay clear dirt routes from the central hub to the key interactables
        # (Structured Paths, roadmap P5 #31) so the player always has an obvious
        # walking route toward the boss dungeon, shop, and rest area.
        map_lines = self.carve_landmark_paths(map_lines)

        tile_map = []

        # Tile coordinate mappings for Zelda-style world
        tile_coords = {
            # Basic terrain
            'G': (0, 0, 24, 24),  # Grass
            'g': (24, 0, 24, 24),  # Light grass
            'd': (48, 0, 24, 24),  # Dark grass
            'D': (72, 0, 24, 24),  # Dirt
            'P': (96, 0, 24, 24),  # Path
            'S': (120, 0, 24, 24),  # Sand

            # Paths and roads
            'p': (0, 24, 24, 24),  # Dirt path
            'r': (24, 24, 24, 24),  # Road
            '=': (48, 24, 24, 24),  # Horizontal path
            '|': (72, 24, 24, 24),  # Vertical path
            '+': (96, 24, 24, 24),  # Path intersection
            'o': (120, 24, 24, 24),  # Round path

            # Decorative elements
            'T': (72, 48, 24, 24),  # Tree trunk
            't': (96, 48, 24, 24),  # Tree leaves
            'B': (120, 48, 24, 24),  # Bush

            # Water and special
            'W': (0, 96, 24, 24),  # Water
            'w': (24, 96, 24, 24),  # Water edge
            'Y': (72, 96, 24, 24),  # Special yellow
            'M': (96, 96, 24, 24),  # Magic purple
            'X': (120, 96, 24, 24),  # Danger red

            # Default fallback
            ' ': (0, 0, 24, 24),  # Default to grass
            '0': (0, 0, 24, 24),  # Grass
            '1': (24, 0, 24, 24),  # Light grass
            '2': (48, 0, 24, 24),  # Dark grass
            '3': (96, 0, 24, 24),  # Path
        }

        # Initialize empty map
        for row in range(self.map_height):
            tile_map.append([])
            for _column in range(self.map_width):
                tile_map[row].append((0, 0, 24, 24))  # Default grass

        # Process each line of map data
        for x in range(min(len(map_lines), self.map_height)):
            line = map_lines[x]
            for y in range(min(len(line), self.map_width)):
                char = line[y]

                # Get tile coordinates from mapping, default to grass
                tile_map[x][y] = tile_coords.get(char, (0, 0, 24, 24))

        return tile_map

    def load_map_from_file(self, map_file_path):
        """Load map from file"""
        try:
            with open(map_file_path, 'r') as f:
                map_lines = [line.rstrip('\n') for line in f.readlines()]
            return self.load_map_from_data(map_lines)
        except FileNotFoundError:
            print(f"Map file {map_file_path} not found, creating Zelda-style map")
            return self.create_zelda_style_map()

    def create_zelda_style_map(self):
        """Create a Zelda-style map similar to the reference image"""
        zelda_map_data = [
            # Row 0-5: Top area with trees
            "GGGGtTtGGGGGGGGtTtGGGGGGGGGGtTt",
            "GGtTtGGGGGGGGGGGGGtTtGGGPpPGGG",
            "GtTtGGGpGGGGGGGGtTtGGGGGGGGGGt",
            "GGGGGGGGGGGGGGGGGGGGtTtGGGGGGG",
            "GGGGGGGGGpppppppppppppGGGGGGGG",
            "GGGGGGGGGpGGGGGGGGGGpGGGGGGGGG",

            # Row 6-11: Middle area with main path
            "GGGGGGGGGpGGtTtGGGGGpGGGGGGGGG",
            "GtTtGGGGGpGGGGGGGGGGpGGGtTtGGG",
            "GGGGGGGGGppppppp+pppppGGGGGGGG",
            "GGGGGGGGGGGGGGGGpGGGGGGGGGGPGG",
            "GGGGGGGGGGGtTtGGpGGtTtGGGGGGGG",
            "GGtTtGGGGGGGGGGGpGGGGGGGGtTtGG",

            # Row 12-17: Lower middle with diagonal paths to bottom-right
            "GGGGGGGGGGGGGGGGpGGGGGGGGGGGGG",
            "GGGGGGGGGGGGGGGGpGGGGGGGGpGGGG",
            "GGGGGGGGGpppppppppppppGGGGGGGG",
            "GGtTtGGGGpGGGGGGGGGGpGGGGtTtGG",
            "GGGGGGGGGpGGGGGpppppppGGGGGGGG",
            "GGGGGGGGGpGGGGGGGGGGpGGGGGGGGG",

            # Row 18-23: Bottom area with clear path to rest/shop area
            "GGGGGGGGGpGGtTtGGGGGpGGtTtGGGG",
            "GGGGGGGGGpGGGGGGGGGGpGGGGGGGGG",
            "GGGGGGGGGpppppppppppppppppppGG",
            "GGtTtGGGGGGGGGGGGGGGGGGGGtTtGG",
            "GGGGGGGGGGGGGPppppppppppppppGG",
            "GGGGGGGGGGGGGGGGGGGGGGGGGGGGpG"
        ]

        # Ensure all lines have the same length
        normalized_lines = []
        for line in zelda_map_data:
            # Pad or truncate to map_width
            if len(line) < self.map_width:
                line += 'G' * (self.map_width - len(line))
            elif len(line) > self.map_width:
                line = line[:self.map_width]
            normalized_lines.append(line)

        # Add more lines if needed
        while len(normalized_lines) < self.map_height:
            normalized_lines.append('G' * self.map_width)

        # Save the map
        with open(f"{map_file}", 'w') as f:
            for line in normalized_lines:
                f.write(line + '\n')

        return self.load_map_from_data(normalized_lines)

    def create_default_map(self):
        """Create a default map if no map file exists"""
        return self.create_zelda_style_map()

    def draw(self, tile_map, screen, offset_x=0, offset_y=0):
        """Draw the tile map with optional camera offset"""
        for x in range(self.map_height):
            for y in range(self.map_width):
                if x < len(tile_map) and y < len(tile_map[x]):
                    screen_x = y * self.tile_size + offset_x
                    screen_y = x * self.tile_size + offset_y

                    # Only draw tiles that are visible on screen
                    if (-self.tile_size < screen_x < screen.get_width() and
                            -self.tile_size < screen_y < screen.get_height()):
                        try:
                            screen.blit(self.tiles, (screen_x, screen_y), tile_map[x][y])
                        except:
                            # Fallback if tile coordinates are invalid
                            pygame.draw.rect(screen, (34, 139, 34),
                                             (screen_x, screen_y, self.tile_size, self.tile_size))

    def get_tile_at_position(self, world_x, world_y):
        """Get the tile type at a specific world position"""
        tile_x = world_x // self.tile_size
        tile_y = world_y // self.tile_size

        if 0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height:
            return tile_x, tile_y
        return None, None

    def is_position_walkable(self, world_x, world_y):
        """Check if a position is walkable (for collision detection)"""
        tile_x, tile_y = self.get_tile_at_position(world_x, world_y)

        if tile_x is None or tile_y is None:
            return False

        # All tiles are walkable in this version
        return True

    def get_world_pixel_size(self):
        """Get the total pixel size of the world"""
        return (self.map_width * self.tile_size, self.map_height * self.tile_size)

    def parse_map_for_objects(self, map_file_path="map.txt"):
        """Parse map file to extract object positions"""
        objects = {
            'enemies': [],  # X positions or enemy markers
            'treasures': [],  # F positions (flowers as treasures)
            'shops': [],  # Y positions or special markers
            'special': []  # Other special markers
        }

        try:
            with open(map_file_path, 'r') as f:
                map_lines = [line.strip() for line in f.readlines()]

            for row, line in enumerate(map_lines):
                for col, char in enumerate(line):
                    world_x = col * self.tile_size
                    world_y = row * self.tile_size

                    # Map special characters to objects
                    if char == 'X':
                        objects['enemies'].append((world_x, world_y))
                    elif char == 'R' or char == 'r':  # Flowers as treasures
                        objects['treasures'].append((world_x, world_y))
                    elif char == 'Y' or char == 'M':  # Special markers as shops
                        objects['shops'].append((world_x, world_y))
                    elif char == 'T':  # Trees as special markers
                        objects['special'].append((world_x, world_y))

            # If no objects found in map, add some manually
            if not any(objects.values()):
                # Add some default enemy positions
                objects['enemies'] = [
                    (200, 150), (400, 300), (600, 200), (300, 450)
                ]
                # Add some treasure positions
                objects['treasures'] = [
                    (150, 100), (350, 250), (550, 150), (450, 400)
                ]
                # Add shop positions
                objects['shops'] = [
                    (250, 200), (500, 350)
                ]

        except FileNotFoundError:
            print(f"Map file {map_file_path} not found")
            # Default object positions
            objects['enemies'] = [(200, 150), (400, 300), (600, 200)]
            objects['treasures'] = [(150, 100), (350, 250), (550, 150)]
            objects['shops'] = [(250, 200), (500, 350)]

        return objects