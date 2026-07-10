"""Unit tests for Code/gfx.py — the pygame -> Arcade rendering shim (roadmap P1 #1).

The shim is the linchpin of the Pygame->Arcade migration: every draw call in the
game routes through it, and its two easiest-to-break jobs are (1) flipping
pygame's top-left/y-down coordinates into Arcade's bottom-left/y-up space and
(2) recording draws onto off-screen surfaces so they can be replayed later.
Neither of those needs a GPU, so this suite pins the shim's *arcade-independent*
logic and runs headlessly in CI.

Anything that would actually hand geometry to Arcade's GL layer (real draws,
text layout, texture uploads) is forced through the `_arcade is None` path by
patching `gfx._arcade = None`, so the tests never require a display or an
installed `arcade`, yet still exercise the coordinate/area/record/replay math
right up to the draw boundary.
"""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from Code import gfx  # noqa: E402


class NoArcadeMixin:
    """Force the deterministic, GPU-free path for the duration of a test.

    With `_arcade` set to None every `_draw_*` primitive early-returns, so
    replay/draw calls are safe no-ops we can smoke-test, while all the coordinate
    and op-recording logic still runs. Screen size is pinned so `_flip_y` math is
    predictable regardless of test ordering.
    """

    def setUp(self):
        self._saved_arcade = gfx._arcade
        self._saved_dims = (gfx.SCREEN_WIDTH, gfx.SCREEN_HEIGHT)
        gfx._arcade = None
        gfx.configure(800, 600)

    def tearDown(self):
        gfx._arcade = self._saved_arcade
        gfx.configure(*self._saved_dims)


class HelperFunctionTests(NoArcadeMixin, unittest.TestCase):
    def test_flip_y_inverts_about_screen_height(self):
        self.assertEqual(gfx._flip_y(0), 600)
        self.assertEqual(gfx._flip_y(600), 0)
        self.assertEqual(gfx._flip_y(150), 450)

    def test_configure_updates_flip_reference(self):
        gfx.configure(1024, 768)
        self.assertEqual(gfx._flip_y(0), 768)

    def test_norm_color_clamps_and_defaults(self):
        self.assertEqual(gfx._norm_color(None), (0, 0, 0, 255))
        self.assertEqual(gfx._norm_color((300, -5, 128)), (255, 0, 128))
        self.assertEqual(gfx._norm_color((10.7, 20.2, 30.9)), (10, 20, 30))

    def test_apply_alpha_passthrough_when_opaque(self):
        # None or >=255 surface alpha must not touch the color.
        self.assertEqual(gfx._apply_alpha((10, 20, 30), None), (10, 20, 30))
        self.assertEqual(gfx._apply_alpha((10, 20, 30), 255), (10, 20, 30))
        self.assertEqual(gfx._apply_alpha((10, 20, 30, 255), 300), (10, 20, 30, 255))

    def test_apply_alpha_modulates_alpha_channel(self):
        # RGB source is treated as alpha=255; half surface alpha -> ~127.
        self.assertEqual(gfx._apply_alpha((0, 0, 0), 128), (0, 0, 0, 128))
        # The crafting/store overlay case: BLACK filled, set_alpha(180).
        self.assertEqual(gfx._apply_alpha((0, 0, 0), 180), (0, 0, 0, 180))
        # An already-translucent source color composes multiplicatively.
        self.assertEqual(gfx._apply_alpha((255, 0, 0, 200), 128), (255, 0, 0, 100))
        # Fully transparent surface alpha zeroes it out.
        self.assertEqual(gfx._apply_alpha((255, 255, 255), 0), (255, 255, 255, 0))

    def test_rect_xywh_accepts_rect_and_tuple(self):
        self.assertEqual(gfx._rect_xywh(gfx.Rect(3, 4, 5, 6)), (3, 4, 5, 6))
        self.assertEqual(gfx._rect_xywh((1, 2, 3, 4)), (1, 2, 3, 4))

    def test_finite_rejects_nan_and_inf(self):
        self.assertTrue(gfx._finite(1, 2, 3.5))
        self.assertFalse(gfx._finite(float("nan")))
        self.assertFalse(gfx._finite(1, float("inf")))
        self.assertFalse(gfx._finite(float("-inf"), 2))


class SafeTextTests(NoArcadeMixin, unittest.TestCase):
    """`_safe_text` strips the codepoints that SIGSEGV pyglet's CoreText path."""

    def test_plain_ascii_untouched(self):
        self.assertEqual(gfx._safe_text("Level 3 - Boss"), "Level 3 - Boss")

    def test_strips_variation_selector_and_zwj(self):
        self.assertEqual(gfx._safe_text("HP️"), "HP")
        self.assertEqual(gfx._safe_text("a‍b"), "ab")
        self.assertEqual(gfx._safe_text("5⃣"), "5")

    def test_strips_astral_plane_emoji(self):
        # U+1F600 grinning face is above the BMP -> dropped.
        self.assertEqual(gfx._safe_text("win \U0001F600!"), "win !")

    def test_keeps_bmp_symbols(self):
        # Arrows / box-drawing are in the BMP and safe to render.
        self.assertEqual(gfx._safe_text("↑↓ move"), "↑↓ move")


class RectTests(NoArcadeMixin, unittest.TestCase):
    def test_edges_and_size_aliases(self):
        r = gfx.Rect(10, 20, 30, 40)
        self.assertEqual((r.left, r.top, r.right, r.bottom), (10, 20, 40, 60))
        self.assertEqual((r.w, r.h, r.size), (30, 40, (30, 40)))

    def test_center_get_and_set(self):
        r = gfx.Rect(0, 0, 20, 10)
        self.assertEqual(r.center, (10, 5))
        r.center = (100, 50)
        self.assertEqual(r.topleft, (90, 45))

    def test_anchor_setters_move_box(self):
        r = gfx.Rect(0, 0, 20, 10)
        r.topright = (100, 5)
        self.assertEqual(r.topleft, (80, 5))
        r2 = gfx.Rect(0, 0, 20, 10)
        r2.midbottom = (50, 200)
        self.assertEqual((r2.centerx, r2.bottom), (50, 200))
        r3 = gfx.Rect(0, 0, 20, 10)
        r3.bottomright = (60, 60)
        self.assertEqual((r3.right, r3.bottom), (60, 60))

    def test_get_rect_via_surface_kwargs(self):
        surf = gfx.Surface((40, 20))
        rect = surf.get_rect(center=(100, 100))
        self.assertEqual(rect.center, (100, 100))
        self.assertEqual((rect.width, rect.height), (40, 20))

    def test_collidepoint(self):
        r = gfx.Rect(0, 0, 10, 10)
        self.assertTrue(r.collidepoint(5, 5))
        self.assertTrue(r.collidepoint((0, 0)))
        self.assertFalse(r.collidepoint(11, 5))

    def test_colliderect(self):
        a = gfx.Rect(0, 0, 10, 10)
        self.assertTrue(a.colliderect(gfx.Rect(5, 5, 10, 10)))
        self.assertFalse(a.colliderect(gfx.Rect(20, 20, 5, 5)))

    def test_move_copy_inflate(self):
        r = gfx.Rect(10, 10, 20, 20)
        self.assertEqual(r.move(5, -5).topleft, (15, 5))
        self.assertEqual(r.topleft, (10, 10))  # move is non-mutating
        r.move_ip(5, 5)
        self.assertEqual(r.topleft, (15, 15))
        infl = gfx.Rect(0, 0, 10, 10).inflate(4, 4)  # keeps center
        self.assertEqual((infl.x, infl.y, infl.width, infl.height), (-2, -2, 14, 14))

    def test_clamp_union_contains(self):
        bounds = gfx.Rect(0, 0, 100, 100)
        clamped = gfx.Rect(90, 90, 30, 30).clamp(bounds)
        self.assertEqual(clamped.topleft, (70, 70))
        u = gfx.Rect(0, 0, 10, 10).union(gfx.Rect(20, 20, 10, 10))
        self.assertEqual((u.left, u.top, u.right, u.bottom), (0, 0, 30, 30))
        self.assertTrue(gfx.Rect(0, 0, 100, 100).contains(gfx.Rect(10, 10, 5, 5)))
        self.assertFalse(gfx.Rect(0, 0, 5, 5).contains(gfx.Rect(10, 10, 5, 5)))

    def test_iter_unpacks_as_xywh(self):
        x, y, w, h = gfx.Rect(1, 2, 3, 4)
        self.assertEqual((x, y, w, h), (1, 2, 3, 4))


class SurfaceTests(NoArcadeMixin, unittest.TestCase):
    def test_size_queries(self):
        s = gfx.Surface((64, 48))
        self.assertEqual(s.get_width(), 64)
        self.assertEqual(s.get_height(), 48)
        self.assertEqual(s.get_size(), (64, 48))

    def test_alpha_clamped(self):
        s = gfx.Surface((10, 10))
        s.set_alpha(None)
        self.assertEqual(s.get_alpha(), 255)
        s.set_alpha(999)
        self.assertEqual(s.get_alpha(), 255)
        s.set_alpha(-5)
        self.assertEqual(s.get_alpha(), 0)

    def test_sized_surface_is_offscreen_zero_is_not(self):
        self.assertTrue(gfx.Surface((10, 10))._offscreen)
        self.assertFalse(gfx.Surface((0, 0))._offscreen)

    def test_fill_records_op_on_offscreen(self):
        s = gfx.Surface((10, 10))
        s.fill((1, 2, 3))
        self.assertEqual(s._ops, [("fill", ((1, 2, 3),))])

    def test_blit_records_op_with_dest(self):
        dst = gfx.Surface((100, 100))
        src = gfx.Surface((10, 10))
        dst.blit(src, (5, 7))
        self.assertEqual(len(dst._ops), 1)
        op, args = dst._ops[0]
        self.assertEqual(op, "blit")
        self.assertIs(args[0], src)
        self.assertEqual((args[1], args[2]), (5, 7))

    def test_blit_accepts_rect_dest(self):
        dst = gfx.Surface((100, 100))
        src = gfx.Surface((10, 10))
        dst.blit(src, gfx.Rect(3, 4, 10, 10))
        _, args = dst._ops[0]
        self.assertEqual((args[1], args[2]), (3, 4))

    def test_replay_is_safe_without_arcade(self):
        # Exercises the translation + area-clip paths; draws no-op under _arcade=None.
        dst = gfx.Surface((100, 100))
        dst.fill((0, 0, 0))
        gfx.draw.rect(dst, (255, 0, 0), (10, 10, 5, 5))
        gfx.draw.circle(dst, (0, 255, 0), (20, 20), 4)
        gfx.draw.line(dst, (0, 0, 255), (0, 0), (30, 30))
        dst._replay(0, 0)                       # full replay
        dst._replay(50, 50, area=(10, 10, 5, 5))  # sub-rect replay


class DrawModuleRecordingTests(NoArcadeMixin, unittest.TestCase):
    """pygame.draw.* against an off-screen surface must record, not draw."""

    def setUp(self):
        super().setUp()
        self.s = gfx.Surface((50, 50))

    def test_rect_records(self):
        gfx.draw.rect(self.s, (10, 20, 30), (1, 2, 3, 4), 2)
        self.assertEqual(self.s._ops[-1], ("rect", ((10, 20, 30), (1, 2, 3, 4), 2)))

    def test_circle_records(self):
        gfx.draw.circle(self.s, (1, 2, 3), (5, 6), 7, 1)
        self.assertEqual(self.s._ops[-1], ("circle", ((1, 2, 3), (5, 6), 7, 1)))

    def test_polygon_records_points(self):
        gfx.draw.polygon(self.s, (9, 9, 9), [(0, 0), (1, 0), (1, 1)])
        op, args = self.s._ops[-1]
        self.assertEqual(op, "polygon")
        self.assertEqual(args[1], [(0, 0), (1, 0), (1, 1)])

    def test_lines_records(self):
        gfx.draw.lines(self.s, (1, 1, 1), True, [(0, 0), (5, 5)], 2)
        op, args = self.s._ops[-1]
        self.assertEqual(op, "lines")
        self.assertEqual((args[1], args[3]), (True, 2))


class FontTests(NoArcadeMixin, unittest.TestCase):
    """Under _arcade=None, Font.render falls back to approximate metrics so the
    game's layout math (centering, wrapping) still produces sane numbers."""

    def test_render_returns_sized_surface(self):
        f = gfx.Font(None, 24)
        surf = f.render("Hello", True, (255, 255, 255))
        self.assertIsInstance(surf, gfx.Surface)
        self.assertGreater(surf.get_width(), 0)
        self.assertEqual(surf.get_height(), 24)

    def test_wider_text_is_wider(self):
        f = gfx.Font(None, 24)
        short = f.render("Hi", True, (0, 0, 0)).get_width()
        long = f.render("Hello world foo", True, (0, 0, 0)).get_width()
        self.assertGreater(long, short)

    def test_sysfont_and_init(self):
        f = gfx.font.SysFont("arial", 18)
        self.assertIsInstance(f, gfx.Font)
        self.assertIsNone(gfx.font.init())
        self.assertTrue(gfx.font.get_init())

    def test_size_method_is_callable_not_shadowed(self):
        # pygame.font.Font.size(text) -> (w, h) is a METHOD. The stored point
        # size must NOT be named self.size or it shadows this method with an int
        # ("int is not callable"). Guards the drop-in API contract.
        f = gfx.Font(None, 24)
        self.assertTrue(callable(f.size))
        w, h = f.size("Hello")
        self.assertIsInstance(w, int)
        self.assertGreater(w, 0)
        self.assertEqual(h, 24)

    def test_font_size_stored_as_font_size_attr(self):
        f = gfx.Font("arial", 30)
        self.assertEqual(f.font_size, 30)
        # render must honor the stored size in the no-arcade metric fallback.
        self.assertEqual(f.render("x", True, (0, 0, 0)).get_height(), 30)


class ConstantsTests(NoArcadeMixin, unittest.TestCase):
    def test_key_constants_match_pygame_values(self):
        # These MUST match pygame so handle_keypress(key) comparisons are
        # unchanged when arcade_app translates arcade key codes into them.
        self.assertEqual(gfx.K_ESCAPE, 27)
        self.assertEqual(gfx.K_RETURN, 13)
        self.assertEqual(gfx.K_SPACE, 32)
        self.assertEqual(gfx.K_a, 97)
        self.assertEqual(gfx.K_0, 48)
        self.assertEqual(gfx.K_UP, 1073741906)

    def test_event_type_constants(self):
        self.assertEqual(gfx.QUIT, 256)
        self.assertEqual(gfx.KEYDOWN, 768)
        self.assertEqual(gfx.KEYUP, 769)

    def test_event_object_holds_attrs(self):
        e = gfx.Event(gfx.KEYDOWN, key=gfx.K_SPACE, unicode=" ")
        self.assertEqual(e.type, gfx.KEYDOWN)
        self.assertEqual(e.key, 32)
        self.assertEqual(e.unicode, " ")

    def test_held_key_state_roundtrip(self):
        gfx.set_key(gfx.K_w, True)
        pressed = gfx.key.get_pressed()
        self.assertTrue(pressed[gfx.K_w])
        gfx.set_key(gfx.K_w, False)
        self.assertFalse(gfx.key.get_pressed()[gfx.K_w])


if __name__ == "__main__":
    unittest.main()
