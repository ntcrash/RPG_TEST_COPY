"""Unit tests for Structured Paths (roadmap P5 #31).

Pins the Structured Paths change added in v2.10.0: the overworld's key
interactables (boss dungeon hub, shop, rest area) had no ground routes leading
to them, so the world read as a trackless field. ``EnhancedTileMap`` now carves
clear dirt-path routes from the central hub out to each important area via the
pure ``carve_landmark_paths`` helper, wired into ``load_map_from_data``.

Everything runs headlessly through the ``Code.gfx`` shim (see ``tests/__init__``)
so it needs no display, GPU, or map assets.
"""

import os
import unittest

os.environ.setdefault("MEGITECH_BACKEND", "arcade")

from Code.backend import pygame  # noqa: E402  (default: Code.gfx shim)

pygame.init()

from Code.tile_map import EnhancedTileMap  # noqa: E402

PATH_CHARS = set("p=|+ro")


def blank_grid(cols=32, rows=24):
    return ["G" * cols for _ in range(rows)]


def is_path(grid, col, row):
    return grid[row][col] in PATH_CHARS


class LandmarkTilesTests(unittest.TestCase):
    """The pure ``landmark_tiles`` locator."""

    def test_default_grid_positions(self):
        marks = EnhancedTileMap.landmark_tiles(32, 24)
        self.assertEqual(marks["hub"], (16, 12))     # world centre
        self.assertEqual(marks["spawn"], (20, 20))   # PLAYER_START (480, 480)
        self.assertEqual(marks["shop"], (28, 0))     # top-right
        self.assertEqual(marks["rest"], (29, 21))    # bottom-right

    def test_all_tiles_in_bounds(self):
        for cols, rows in [(32, 24), (10, 10), (5, 5), (1, 1)]:
            for col, row in EnhancedTileMap.landmark_tiles(cols, rows).values():
                self.assertTrue(0 <= col < cols, (cols, rows, col))
                self.assertTrue(0 <= row < rows, (cols, rows, row))

    def test_deterministic(self):
        self.assertEqual(
            EnhancedTileMap.landmark_tiles(32, 24),
            EnhancedTileMap.landmark_tiles(32, 24),
        )


class CarveLandmarkPathsTests(unittest.TestCase):
    """The pure ``carve_landmark_paths`` classmethod."""

    def setUp(self):
        self.grid = blank_grid()
        self.carved = EnhancedTileMap.carve_landmark_paths(self.grid)
        self.marks = EnhancedTileMap.landmark_tiles(32, 24)

    def test_shape_preserved(self):
        self.assertEqual(len(self.carved), len(self.grid))
        for src, dst in zip(self.grid, self.carved):
            self.assertEqual(len(dst), len(src))

    def test_each_landmark_reached_by_path(self):
        # A path tile must sit on (or immediately adjacent to) every landmark
        # so the route actually arrives at the important area.
        for key in ("spawn", "shop", "rest", "hub"):
            col, row = self.marks[key]
            near = any(
                0 <= row + dr < 24 and 0 <= col + dc < 32 and is_path(self.carved, col + dc, row + dr)
                for dr in (-1, 0, 1)
                for dc in (-1, 0, 1)
            )
            self.assertTrue(near, f"no path near landmark {key} at {(col, row)}")

    def test_hub_is_intersection_of_routes(self):
        # Three routes emanate from the hub, so the hub cell is a path.
        col, row = self.marks["hub"]
        self.assertTrue(is_path(self.carved, col, row))

    def test_routes_are_connected_hub_to_spawn(self):
        # Walk the L-route from hub to spawn: horizontal along hub row, then
        # vertical along spawn column — every cell must be a path.
        hc, hr = self.marks["hub"]
        sc, sr = self.marks["spawn"]
        for col in range(min(hc, sc), max(hc, sc) + 1):
            self.assertTrue(is_path(self.carved, col, hr), (col, hr))
        for row in range(min(hr, sr), max(hr, sr) + 1):
            self.assertTrue(is_path(self.carved, sc, row), (sc, row))

    def test_intersections_marked(self):
        # Painting a route over an existing path yields '+' (an intersection),
        # not a plain 'p'. The spawn and rest routes share the hub row, so the
        # overlapping horizontal segment must contain intersections.
        joined = "".join(self.carved)
        self.assertIn("+", joined)

    def test_grass_off_route_untouched(self):
        # A far corner with no route through it stays grass.
        self.assertEqual(self.carved[23][0], "G")

    def test_deterministic(self):
        self.assertEqual(
            EnhancedTileMap.carve_landmark_paths(blank_grid()),
            EnhancedTileMap.carve_landmark_paths(blank_grid()),
        )

    def test_empty_input(self):
        self.assertEqual(EnhancedTileMap.carve_landmark_paths([]), [])

    def test_ragged_lines_normalised(self):
        # Short lines are padded so column math never goes out of bounds.
        carved = EnhancedTileMap.carve_landmark_paths(["G", "GGGG", ""])
        self.assertEqual(len({len(line) for line in carved}), 1)


class LoadMapStructuredPathsTests(unittest.TestCase):
    """Routes are carved end-to-end when a map is loaded."""

    def setUp(self):
        self.tm = EnhancedTileMap()

    def test_routes_present_in_rendered_grid(self):
        # Load an all-grass map; the rendered tile grid must contain the dirt
        # path tile rect, proving carve_landmark_paths ran during load.
        grass_rect = self.tm.load_map_from_data(["G"])[0][0]
        path_rect = (0, 24, 24, 24)  # 'p' dirt path tile coords
        grid = self.tm.load_map_from_data(["G" * 32 for _ in range(24)])
        flat = [cell for col in grid for cell in col]
        self.assertIn(path_rect, flat)
        self.assertNotEqual(path_rect, grass_rect)

    def test_spawn_tile_on_a_route(self):
        # The player spawn tile must render as a path/intersection so the
        # player starts on a clear route, not buried in blank grass.
        grid = self.tm.load_map_from_data(["G" * 32 for _ in range(24)])
        col, row = EnhancedTileMap.landmark_tiles(32, 24)["spawn"]
        path_rects = {(0, 24, 24, 24), (96, 24, 24, 24)}  # 'p' and '+'
        # grid is indexed [row][col]
        self.assertIn(grid[row][col], path_rects)


if __name__ == "__main__":
    unittest.main()
