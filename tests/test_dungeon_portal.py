"""Unit tests for the mystical dungeon-entrance visuals (roadmap P5 #27).

Pins the animated-portal helpers added to ``Dungeon`` in v2.6.0 — the themed
colour palette that distinguishes a boss dungeon from a level portal, the
breathing ``glow_pulse``, the rotating vortex ``swirl_point``, the rising
``particle_state`` motes, and the ``_lerp_color`` blend — plus a headless draw
pass proving both entrance modes render crash-free.

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

from Code.ui_components import Dungeon  # noqa: E402


class _StubCamera:
    """Minimal camera: identity world->screen, everything visible."""

    def world_to_screen(self, x, y):
        return int(x), int(y)

    def is_visible(self, x, y, w, h):
        return True


class _InvisibleCamera(_StubCamera):
    def is_visible(self, x, y, w, h):
        return False


class ThemeTests(unittest.TestCase):
    def test_boss_and_portal_themes_differ(self):
        boss = Dungeon.portal_theme(False)
        portal = Dungeon.portal_theme(True)
        self.assertEqual(boss["label"], "BOSS DUNGEON")
        self.assertEqual(portal["label"], "LEVEL PORTAL")
        # Distinct core colours so the two entrances read differently.
        self.assertNotEqual(boss["core"], portal["core"])
        self.assertNotEqual(boss["label_color"], portal["label_color"])

    def test_theme_has_required_keys(self):
        for is_portal in (True, False):
            theme = Dungeon.portal_theme(is_portal)
            for key in ("core", "glow", "swirl", "particle",
                        "label", "label_color", "label_glow"):
                self.assertIn(key, theme)


class LerpColorTests(unittest.TestCase):
    def test_endpoints(self):
        a, b = (0, 0, 0), (200, 100, 50)
        self.assertEqual(Dungeon._lerp_color(a, b, 0.0), (0, 0, 0))
        self.assertEqual(Dungeon._lerp_color(a, b, 1.0), (200, 100, 50))

    def test_midpoint(self):
        self.assertEqual(
            Dungeon._lerp_color((0, 0, 0), (100, 100, 100), 0.5),
            (50, 50, 50),
        )

    def test_clamps_out_of_range_t(self):
        a, b = (10, 20, 30), (40, 50, 60)
        self.assertEqual(Dungeon._lerp_color(a, b, -5), a)
        self.assertEqual(Dungeon._lerp_color(a, b, 5), b)


class GlowPulseTests(unittest.TestCase):
    def test_range_stays_0_1(self):
        for t in range(0, 400, 7):
            p = Dungeon.glow_pulse(t)
            self.assertGreaterEqual(p, 0.0)
            self.assertLessEqual(p, 1.0)

    def test_oscillates(self):
        vals = {round(Dungeon.glow_pulse(t), 4) for t in range(0, 80)}
        self.assertGreater(len(vals), 5)

    def test_deterministic(self):
        self.assertEqual(Dungeon.glow_pulse(42), Dungeon.glow_pulse(42))


class SwirlPointTests(unittest.TestCase):
    def test_returns_int_pair(self):
        x, y = Dungeon.swirl_point(100, 100, 0, arm=0, step=0)
        self.assertIsInstance(x, int)
        self.assertIsInstance(y, int)

    def test_outer_steps_are_farther_from_center(self):
        cx, cy = 100, 100
        inner = Dungeon.swirl_point(cx, cy, 0, arm=0, step=0)
        outer = Dungeon.swirl_point(cx, cy, 0, arm=0, step=5)
        d_inner = math.hypot(inner[0] - cx, inner[1] - cy)
        d_outer = math.hypot(outer[0] - cx, outer[1] - cy)
        self.assertGreater(d_outer, d_inner)

    def test_arms_are_offset(self):
        p0 = Dungeon.swirl_point(100, 100, 0, arm=0, step=3)
        p1 = Dungeon.swirl_point(100, 100, 0, arm=1, step=3)
        self.assertNotEqual(p0, p1)

    def test_rotates_over_time(self):
        p_a = Dungeon.swirl_point(100, 100, 0, arm=0, step=4)
        p_b = Dungeon.swirl_point(100, 100, 30, arm=0, step=4)
        self.assertNotEqual(p_a, p_b)


class ParticleStateTests(unittest.TestCase):
    def test_returns_triplet(self):
        dx, dy, size = Dungeon.particle_state(0, 0)
        self.assertIsInstance(dx, int)
        self.assertIsInstance(dy, int)
        self.assertGreaterEqual(size, 1)

    def test_particles_rise_within_span(self):
        # dy should never exceed the configured half-span in either direction.
        for t in range(0, 200, 3):
            for i in range(6):
                _, dy, _ = Dungeon.particle_state(t, i, rise_span=46)
                self.assertLessEqual(abs(dy), 46)

    def test_distinct_particles_spread_out(self):
        ys = {Dungeon.particle_state(10, i)[1] for i in range(6)}
        self.assertGreater(len(ys), 1)


class DrawSmokeTests(unittest.TestCase):
    def _draw(self, is_portal, camera):
        surface = pygame.Surface((200, 200))
        dungeon = Dungeon(20, 20, is_portal=is_portal)
        # Multiple frames to exercise the animated branches.
        for t in (0, 17, 88, 250):
            dungeon.draw(surface, camera, animation_timer=t)
        return surface

    def test_boss_entrance_draws(self):
        self._draw(False, _StubCamera())  # must not raise

    def test_level_portal_draws(self):
        self._draw(True, _StubCamera())  # must not raise

    def test_offscreen_is_noop(self):
        # Not visible -> draw returns early, no crash.
        self._draw(False, _InvisibleCamera())

    def test_inactive_is_noop(self):
        surface = pygame.Surface((200, 200))
        dungeon = Dungeon(20, 20)
        dungeon.active = False
        dungeon.draw(surface, _StubCamera(), animation_timer=5)


if __name__ == "__main__":
    unittest.main()
