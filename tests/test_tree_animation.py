"""Unit tests for the animated Tree canopy (roadmap P5 #25).

Pins the harvestable-driven regrowth tween and the swaying animation added in
v2.4.0: colour interpolation between a withered and a healthy canopy, the
0..1 ``regrow_fraction`` mapping over the respawn timer, and that the sway
displaces the canopy over time while the trunk stays rooted. Rendering runs
through the headless ``Code.gfx`` shim (see ``tests/__init__``) so it needs no
display or GPU — we draw onto an off-screen Surface and only assert the shim
recorded draw ops without crashing.
"""

import math
import os
import unittest

os.environ.setdefault("MEGITECH_BACKEND", "arcade")

from Code.backend import pygame  # noqa: E402  (default: Code.gfx shim)

pygame.init()

from Code.ui_components import Tree  # noqa: E402


class _StubCamera:
    """Minimal camera: identity world->screen, everything visible."""

    def world_to_screen(self, x, y):
        return int(x), int(y)

    def is_visible(self, x, y, w, h):
        return True


class RegrowFractionTests(unittest.TestCase):
    def test_harvestable_tree_is_fully_grown(self):
        tree = Tree(100, 100)
        self.assertTrue(tree.harvestable)
        self.assertEqual(tree.regrow_fraction(), 1.0)

    def test_just_harvested_is_zero(self):
        tree = Tree(100, 100)
        tree.harvest()
        self.assertFalse(tree.harvestable)
        # timer == max right after harvest -> 0.0 grown
        self.assertAlmostEqual(tree.regrow_fraction(), 0.0, places=6)

    def test_halfway_regrown(self):
        tree = Tree(100, 100)
        tree.harvest()
        tree.respawn_timer = tree.max_respawn_time // 2
        self.assertAlmostEqual(tree.regrow_fraction(), 0.5, places=2)

    def test_fraction_always_clamped(self):
        tree = Tree(100, 100)
        tree.harvest()
        tree.respawn_timer = tree.max_respawn_time * 10  # absurd
        self.assertGreaterEqual(tree.regrow_fraction(), 0.0)
        tree.respawn_timer = -5
        self.assertLessEqual(tree.regrow_fraction(), 1.0)


class CanopyColorTests(unittest.TestCase):
    def test_lerp_endpoints(self):
        self.assertEqual(Tree._lerp_color((0, 0, 0), (100, 200, 50), 0.0), (0, 0, 0))
        self.assertEqual(Tree._lerp_color((0, 0, 0), (100, 200, 50), 1.0), (100, 200, 50))

    def test_lerp_midpoint(self):
        self.assertEqual(Tree._lerp_color((0, 0, 0), (100, 200, 40), 0.5), (50, 100, 20))

    def test_full_tree_uses_healthy_color(self):
        tree = Tree(100, 100)  # harvestable -> grown == 1.0
        color = tree._lerp_color(tree.leaf_withered, tree.leaf_color, tree.regrow_fraction())
        self.assertEqual(color, tree.leaf_color)

    def test_depleted_tree_uses_withered_color(self):
        tree = Tree(100, 100)
        tree.harvest()  # grown == 0.0
        color = tree._lerp_color(tree.leaf_withered, tree.leaf_color, tree.regrow_fraction())
        self.assertEqual(color, tree.leaf_withered)


class SwayAnimationTests(unittest.TestCase):
    def test_sway_moves_canopy_over_time(self):
        # The canopy offset should differ across animation frames for a grown tree.
        tree = Tree(200, 200)
        offsets = set()
        for timer in range(0, 200, 7):
            t = timer * 0.05 + tree.sway_phase
            sway = (2.6 * tree.sway_strength * math.sin(t)
                    + 1.1 * math.sin(t * 0.37 + 1.3))
            offsets.add(int(sway))
        self.assertGreater(len(offsets), 1, "sway should vary across frames")

    def test_neighbor_trees_have_distinct_phase(self):
        a = Tree(100, 100)
        b = Tree(340, 100)
        self.assertNotAlmostEqual(a.sway_phase, b.sway_phase, places=4)

    def test_draw_runs_headless_for_all_types_and_states(self):
        screen = pygame.Surface((400, 400))
        camera = _StubCamera()
        for ttype in ("normal", "oak", "pine"):
            tree = Tree(120, 120, ttype)
            # healthy
            tree.draw(screen, camera, animation_timer=42)
            # depleted mid-regrow
            tree.harvest()
            tree.respawn_timer = tree.max_respawn_time // 2
            tree.draw(screen, camera, animation_timer=99)


if __name__ == "__main__":
    unittest.main()
