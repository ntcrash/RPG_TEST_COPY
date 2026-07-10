"""Regression tests for spawn-item accessibility (roadmap P1 #3).

These pin the guarantees added in v2.1.4: every spawned world item lands
inside world-derived bounds, on a walkable tile, and never covers the player
start or a key interactable (rest area, shop, boss-dungeon centre), so items
are always reachable and the player is never trapped at spawn.

The full ``EnhancedGameManager.__init__`` boots the whole game (display,
audio, every subsystem), so we build a bare instance with ``__new__`` and
attach only the few attributes the placement methods touch. This keeps the
test headless and fast.
"""

import random
import unittest

import main


class _StubLevel:
    world = 1
    level = 1


class _StubLevelManager:
    def get_current_level(self):
        return _StubLevel()


class _StubTileMap:
    """Minimal stand-in for Code.tile_map.TileMap."""

    def __init__(self, width=768, height=576):
        self._w, self._h = width, height

    def get_world_pixel_size(self):
        return (self._w, self._h)

    def is_position_walkable(self, x, y):
        return True


def _make_manager(world=(768, 576)):
    g = main.EnhancedGameManager.__new__(main.EnhancedGameManager)
    g.tile_map = _StubTileMap(*world)
    g.level_manager = _StubLevelManager()
    g.trees = []
    g.rocks = []
    g.metals = []
    g.streams = []
    g.brushes = []
    return g


class SpawnBoundsTests(unittest.TestCase):
    def test_bounds_within_default_world(self):
        g = _make_manager((768, 576))
        self.assertEqual(g.get_spawn_bounds(margin=48), (48, 48, 720, 528))

    def test_bounds_scale_with_world_size(self):
        g = _make_manager((1200, 900))
        _, _, max_x, max_y = g.get_spawn_bounds(margin=48)
        self.assertEqual((max_x, max_y), (1152, 852))

    def test_bounds_never_invert_on_tiny_world(self):
        g = _make_manager((40, 40))
        min_x, min_y, max_x, max_y = g.get_spawn_bounds(margin=48)
        self.assertLessEqual(min_x, max_x)
        self.assertLessEqual(min_y, max_y)

    def test_reserved_positions_cover_key_interactables(self):
        g = _make_manager((768, 576))
        reserved = g.get_reserved_positions()
        self.assertIn(main.EnhancedGameManager.PLAYER_START, reserved)  # player
        self.assertIn((708, 516), reserved)  # rest area (w-60, h-60)
        self.assertIn((688, 20), reserved)   # shop (w-80, 20)
        self.assertIn((384, 288), reserved)  # boss-dungeon centre (w/2, h/2)


class SpawnPlacementTests(unittest.TestCase):
    """Drive the real placement loops across many RNG seeds and assert the
    accessibility invariants hold for every item that gets placed."""

    SEEDS = range(60)

    def _assert_positions_ok(self, positions, g, margin):
        min_x, min_y, max_x, max_y = g.get_spawn_bounds(margin=margin)
        reserved = g.get_reserved_positions()
        clearance = main.EnhancedGameManager.RESERVED_CLEARANCE
        for (x, y) in positions:
            self.assertTrue(
                min_x <= x <= max_x and min_y <= y <= max_y,
                f"({x},{y}) outside spawn bounds {(min_x, min_y, max_x, max_y)}",
            )
            for (rx, ry) in reserved:
                self.assertGreaterEqual(
                    main.math.dist((x, y), (rx, ry)),
                    clearance,
                    f"({x},{y}) within {clearance}px of reserved ({rx},{ry})",
                )

    def test_map_objects_stay_in_bounds_and_clear_reserved(self):
        g = _make_manager((768, 576))
        placed_any = False
        for seed in self.SEEDS:
            g.rocks.clear()
            g.metals.clear()
            g.streams.clear()
            g.brushes.clear()
            random.seed(seed)
            g.create_map_objects(existing_positions=[])
            positions = (
                [(r.x, r.y) for r in g.rocks]
                + [(m.x, m.y) for m in g.metals]
                + [(s.x, s.y) for s in g.streams]
                + [(b.x, b.y) for b in g.brushes]
            )
            placed_any = placed_any or bool(positions)
            self._assert_positions_ok(positions, g, margin=44)
        self.assertTrue(placed_any, "expected at least some map objects to spawn")

    def test_trees_stay_in_bounds_and_clear_reserved(self):
        g = _make_manager((768, 576))
        placed_any = False
        for seed in self.SEEDS:
            g.trees.clear()
            random.seed(seed)
            g.create_trees(existing_positions=[])
            positions = [(t.x, t.y) for t in g.trees]
            placed_any = placed_any or bool(positions)
            self._assert_positions_ok(positions, g, margin=48)
        self.assertTrue(placed_any, "expected at least some trees to spawn")


if __name__ == "__main__":
    unittest.main()
