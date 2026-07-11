"""Unit tests for resource-node harvest/depleted visual feedback (roadmap P5 #26).

Pins the shared ``HarvestableNode`` behaviour added in v2.5.0 that gives Rock,
Metal, Stream, and Brush consistent, legible feedback about whether they can be
gathered: the 0..1 ``regrow_fraction`` mapping over the respawn timer, the
colour interpolation between a depleted and a ready appearance, the
``harvest_pulse`` used for the "ready" sparkle, and that ``draw`` runs
crash-free in BOTH the ready and depleted states while the pulsing ready-marker
is drawn only when a node is harvestable.

Rendering runs through the headless ``Code.gfx`` shim (see ``tests/__init__``)
so it needs no display or GPU — we draw onto an off-screen Surface and only
assert the shim recorded draw ops without crashing.
"""

import math
import os
import unittest

os.environ.setdefault("MEGITECH_BACKEND", "arcade")

from Code.backend import pygame  # noqa: E402  (default: Code.gfx shim)

pygame.init()

from Code.ui_components import (  # noqa: E402
    Brush,
    HarvestableNode,
    Metal,
    Rock,
    Stream,
)


class _StubCamera:
    """Minimal camera: identity world->screen, everything visible."""

    def world_to_screen(self, x, y):
        return int(x), int(y)

    def is_visible(self, x, y, w, h):
        return True


NODE_FACTORIES = (
    lambda: Rock(100, 100, "iron"),
    lambda: Metal(100, 100, "mithril"),
    lambda: Stream(100, 100),
    lambda: Brush(100, 100),
)


class RegrowFractionTests(unittest.TestCase):
    def test_harvestable_node_is_fully_ready(self):
        for make in NODE_FACTORIES:
            node = make()
            self.assertTrue(node.harvestable)
            self.assertEqual(node.regrow_fraction(), 1.0)

    def test_just_harvested_is_zero(self):
        for make in NODE_FACTORIES:
            node = make()
            node.harvest()
            self.assertFalse(node.harvestable)
            self.assertAlmostEqual(node.regrow_fraction(), 0.0, places=6)

    def test_halfway_regrown(self):
        for make in NODE_FACTORIES:
            node = make()
            node.harvest()
            node.respawn_timer = node.max_respawn_time // 2
            self.assertAlmostEqual(node.regrow_fraction(), 0.5, places=2)

    def test_fraction_always_clamped(self):
        for make in NODE_FACTORIES:
            node = make()
            node.harvest()
            node.respawn_timer = node.max_respawn_time * 10  # absurd
            self.assertGreaterEqual(node.regrow_fraction(), 0.0)
            node.respawn_timer = -5
            self.assertLessEqual(node.regrow_fraction(), 1.0)


class ColorAndPulseTests(unittest.TestCase):
    def test_lerp_endpoints(self):
        self.assertEqual(HarvestableNode._lerp_color((0, 0, 0), (100, 200, 50), 0.0), (0, 0, 0))
        self.assertEqual(HarvestableNode._lerp_color((0, 0, 0), (100, 200, 50), 1.0), (100, 200, 50))

    def test_lerp_midpoint(self):
        self.assertEqual(HarvestableNode._lerp_color((0, 0, 0), (100, 200, 40), 0.5), (50, 100, 20))

    def test_lerp_clamped(self):
        # t outside 0..1 is clamped, never extrapolated.
        self.assertEqual(HarvestableNode._lerp_color((10, 10, 10), (20, 20, 20), 5.0), (20, 20, 20))
        self.assertEqual(HarvestableNode._lerp_color((10, 10, 10), (20, 20, 20), -5.0), (10, 10, 10))

    def test_harvest_pulse_range(self):
        for t in range(0, 200, 7):
            p = HarvestableNode.harvest_pulse(t)
            self.assertGreaterEqual(p, 0.0)
            self.assertLessEqual(p, 1.0)

    def test_harvest_pulse_oscillates(self):
        # Over a full period the pulse must reach both a low and a high point.
        values = [HarvestableNode.harvest_pulse(t) for t in range(0, 200)]
        self.assertLess(min(values), 0.1)
        self.assertGreater(max(values), 0.9)


class DrawFeedbackTests(unittest.TestCase):
    """draw() must not crash in either state, on the headless shim."""

    def setUp(self):
        self.camera = _StubCamera()
        self.screen = pygame.Surface((400, 400))

    def test_draw_ready_state_crash_free(self):
        for make in NODE_FACTORIES:
            node = make()
            self.assertTrue(node.harvestable)
            node.draw(self.screen, self.camera, animation_timer=20)

    def test_draw_depleted_state_crash_free(self):
        for make in NODE_FACTORIES:
            node = make()
            node.harvest()  # now depleted / regrowing
            node.respawn_timer = node.max_respawn_time // 3
            node.draw(self.screen, self.camera, animation_timer=20)

    def test_ready_marker_only_when_harvestable(self):
        node = Rock(100, 100, "iron")
        # Harvestable -> marker draws (two circles) without error.
        node.draw_ready_marker(self.screen, 120, 100, animation_timer=10)
        # Depleted -> early return, no crash, nothing drawn.
        node.harvestable = False
        node.draw_ready_marker(self.screen, 120, 100, animation_timer=10)

    def test_all_nodes_subclass_mixin(self):
        for make in NODE_FACTORIES:
            self.assertIsInstance(make(), HarvestableNode)


if __name__ == "__main__":
    unittest.main()
