"""gfx.py - pygame -> Arcade compatibility / rendering shim.

WHY THIS EXISTS
---------------
The v1.x codebase draws with pygame's immediate-mode API:

    screen.fill(color)
    pygame.draw.rect(screen, color, (x, y, w, h))
    surf = font.render("text", True, color); screen.blit(surf, (x, y))

Arcade 3.x draws differently (callback-based Window, sprites, y-up coords).
Rewriting all ~390 pygame call sites by hand at once is how you introduce 390
new bugs, monkey. Instead this module emulates the *small* slice of the pygame
surface/draw/font API the game actually uses, backed by Arcade draw calls.

MIGRATION PATTERN (per module)
------------------------------
    # old:
    import pygame
    # new:
    from Code import gfx as pygame     # drop-in, then delete leftovers

Every draw call in that module now routes through Arcade with the Y-axis
handled for you. Migrate one file, run it, commit. Repeat.

KEY DIFFERENCE HANDLED FOR YOU
------------------------------
pygame origin = top-left, +y DOWN.   Arcade origin = bottom-left, +y UP.
All coordinates you pass in stay in *pygame* (top-left) space; this shim flips
them to Arcade space at draw time. Do NOT pre-flip.

STATUS: foundation. Covers the primitives inventoried from the codebase
(rect, circle, polygon, line/lines, ellipse, blit, fill, font render,
image load, transform.scale, key constants). Needs on-Mac verification with
`pip install arcade` — this sandbox has no display + no arcade installed.
"""

from __future__ import annotations

# Arcade is imported lazily so that merely importing this module never hard
# crashes the still-pygame build during the transition.
try:
    import arcade as _arcade
except Exception:  # pragma: no cover - arcade not installed yet
    _arcade = None

# ---------------------------------------------------------------------------
# Screen dimensions. arcade_app sets these once the Window is created so the
# Y-flip math knows the surface height. Defaults match the v1.x window.
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600


def configure(width: int, height: int) -> None:
    """Called by arcade_app once the Window size is known."""
    global SCREEN_WIDTH, SCREEN_HEIGHT
    SCREEN_WIDTH, SCREEN_HEIGHT = width, height


def _flip_y(y: float) -> float:
    """pygame top-left y  ->  arcade bottom-left y (for a single point)."""
    return SCREEN_HEIGHT - y


def _norm_color(color):
    """Accept pygame-style RGB/RGBA tuples; pass through to Arcade."""
    if color is None:
        return (0, 0, 0, 255)
    c = tuple(int(max(0, min(255, v))) for v in color)
    return c


# ===========================================================================
# Rect  (mirrors the handful of pygame.Rect features the game relies on)
# ===========================================================================
class Rect:
    """Minimal pygame.Rect stand-in in *pygame* (top-left, y-down) space."""

    __slots__ = ("x", "y", "width", "height")

    def __init__(self, x=0, y=0, width=0, height=0):
        self.x, self.y, self.width, self.height = x, y, width, height

    # --- edges ---
    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.width

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.height

    # --- center (get/set, used for text centering all over the UI) ---
    @property
    def center(self):
        return (self.x + self.width / 2, self.y + self.height / 2)

    @center.setter
    def center(self, value):
        cx, cy = value
        self.x = cx - self.width / 2
        self.y = cy - self.height / 2

    @property
    def centerx(self):
        return self.x + self.width / 2

    @centerx.setter
    def centerx(self, v):
        self.x = v - self.width / 2

    @property
    def centery(self):
        return self.y + self.height / 2

    @centery.setter
    def centery(self, v):
        self.y = v - self.height / 2

    @property
    def topleft(self):
        return (self.x, self.y)

    @topleft.setter
    def topleft(self, value):
        self.x, self.y = value

    def collidepoint(self, px, py):
        return self.left <= px <= self.right and self.top <= py <= self.bottom

    def move(self, dx, dy):
        return Rect(self.x + dx, self.y + dy, self.width, self.height)

    def __iter__(self):
        yield from (self.x, self.y, self.width, self.height)


# ===========================================================================
# Surface  (framebuffer + off-screen surfaces + rendered text)
# ===========================================================================
class Surface:
    """Emulates a pygame.Surface.

    Two flavors:
      * The main window surface (`screen`) -> draws land on the Arcade window.
      * Text/image surfaces -> hold an Arcade drawable + size, blitted later.
    """

    def __init__(self, size=(0, 0), *, text=None, texture=None):
        self._w, self._h = size
        self._alpha = 255
        self._arcade_text = text        # arcade.Text (for font.render results)
        self._texture = texture         # arcade.Texture (for images)

    # ---- size queries ----
    def get_width(self):
        return self._w

    def get_height(self):
        return self._h

    def get_size(self):
        return (self._w, self._h)

    def get_rect(self, **kwargs):
        r = Rect(0, 0, self._w, self._h)
        for key, val in kwargs.items():
            setattr(r, key, val)   # supports center=..., topleft=..., etc.
        return r

    def set_alpha(self, alpha):
        self._alpha = 255 if alpha is None else int(max(0, min(255, alpha)))

    def get_alpha(self):
        return self._alpha

    # ---- clearing ----
    def fill(self, color):
        """Clear the whole surface to a solid color (main-screen use)."""
        if _arcade is None:
            return
        c = _norm_color(color)
        _arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, c)

    # ---- compositing ----
    def blit(self, source: "Surface", dest, area=None):
        """Draw `source` onto this surface at pygame-space top-left `dest`."""
        if _arcade is None or source is None:
            return
        if isinstance(dest, Rect):
            x, y = dest.x, dest.y
        else:
            x, y = dest[0], dest[1]
        source._draw_at(x, y, self._alpha_mult(source))

    def _alpha_mult(self, source):
        return min(self._alpha, source._alpha)

    # ---- internal: render self (text/texture) at pygame top-left (x, y) ----
    def _draw_at(self, x, y, alpha=255):
        if _arcade is None:
            return
        if self._arcade_text is not None:
            t = self._arcade_text
            # arcade.Text anchored top-left; convert y to arcade space.
            t.x = x
            t.y = _flip_y(y)
            try:
                t.color = (t.color[0], t.color[1], t.color[2], alpha)
            except Exception:
                pass
            t.draw()
        elif self._texture is not None:
            # Texture drawn top-left at pygame (x, y) -> arcade rect.
            rect = _arcade.LBWH(x, _flip_y(y + self._h), self._w, self._h)
            _arcade.draw_texture_rect(self._texture, rect)

    # ---- transform.scale support ----
    def _scaled(self, size):
        return Surface(size, texture=self._texture)


# ===========================================================================
# Font  (pygame.font.Font / SysFont -> arcade.Text)
# ===========================================================================
class Font:
    """Emulates pygame.font.Font. `render()` returns a text Surface."""

    def __init__(self, name=None, size=24):
        self.name = name
        self.size = size

    def render(self, text, antialias, color, background=None) -> Surface:
        if _arcade is None:
            # Approximate metrics so layout code still works without arcade.
            w = int(len(str(text)) * self.size * 0.55)
            return Surface((w, self.size))
        c = _norm_color(color)
        atext = _arcade.Text(
            str(text),
            0, 0,
            color=c,
            font_size=self.size * 0.75,   # px font-size ~ pygame point size
            font_name=self.name or ("Kenney Pixel", "arial", "calibri"),
            anchor_x="left",
            anchor_y="top",
        )
        surf = Surface((int(atext.content_width), int(atext.content_height)),
                       text=atext)
        return surf

    def size(self, text):  # pygame Font.size(text) -> (w, h)
        s = self.render(text, True, (255, 255, 255))
        return (s.get_width(), s.get_height())


class _FontModule:
    """Namespace mirroring pygame.font."""

    Font = Font

    @staticmethod
    def SysFont(name, size, bold=False, italic=False):
        return Font(name, size)

    @staticmethod
    def init():
        return None

    @staticmethod
    def get_init():
        return True


font = _FontModule()


# ===========================================================================
# draw  (pygame.draw.* -> arcade.draw_*)
# ===========================================================================
class _DrawModule:
    @staticmethod
    def rect(surface, color, rect, width=0, border_radius=0):
        if _arcade is None:
            return
        x, y, w, h = tuple(rect)
        c = _norm_color(color)
        bottom = _flip_y(y + h)
        if width == 0:
            _arcade.draw_lbwh_rectangle_filled(x, bottom, w, h, c)
        else:
            _arcade.draw_lbwh_rectangle_outline(x, bottom, w, h, c, width)

    @staticmethod
    def circle(surface, color, center, radius, width=0):
        if _arcade is None:
            return
        cx, cy = center
        c = _norm_color(color)
        if width == 0:
            _arcade.draw_circle_filled(cx, _flip_y(cy), radius, c)
        else:
            _arcade.draw_circle_outline(cx, _flip_y(cy), radius, c, width)

    @staticmethod
    def ellipse(surface, color, rect, width=0):
        if _arcade is None:
            return
        x, y, w, h = tuple(rect)
        c = _norm_color(color)
        cx, cy = x + w / 2, y + h / 2
        if width == 0:
            _arcade.draw_ellipse_filled(cx, _flip_y(cy), w, h, c)
        else:
            _arcade.draw_ellipse_outline(cx, _flip_y(cy), w, h, c, width)

    @staticmethod
    def line(surface, color, start, end, width=1):
        if _arcade is None:
            return
        c = _norm_color(color)
        _arcade.draw_line(start[0], _flip_y(start[1]),
                          end[0], _flip_y(end[1]), c, width)

    @staticmethod
    def lines(surface, color, closed, points, width=1):
        if _arcade is None or len(points) < 2:
            return
        c = _norm_color(color)
        pts = [(p[0], _flip_y(p[1])) for p in points]
        seq = pts + [pts[0]] if closed else pts
        for i in range(len(seq) - 1):
            _arcade.draw_line(seq[i][0], seq[i][1],
                              seq[i + 1][0], seq[i + 1][1], c, width)

    @staticmethod
    def polygon(surface, color, points, width=0):
        if _arcade is None:
            return
        c = _norm_color(color)
        pts = [(p[0], _flip_y(p[1])) for p in points]
        if width == 0:
            _arcade.draw_polygon_filled(pts, c)
        else:
            _arcade.draw_polygon_outline(pts, c, width)


draw = _DrawModule()


# ===========================================================================
# image / transform  (asset loading)
# ===========================================================================
class _ImageModule:
    @staticmethod
    def load(path):
        if _arcade is None:
            return Surface((0, 0))
        tex = _arcade.load_texture(path)
        return Surface((tex.width, tex.height), texture=tex)


image = _ImageModule()


class _TransformModule:
    @staticmethod
    def scale(surface, size):
        return surface._scaled(size)

    @staticmethod
    def flip(surface, flip_x, flip_y):
        return surface  # texture-level flip handled at draw time if needed


transform = _TransformModule()


# ===========================================================================
# Key constants + event type constants.
# Values mirror pygame's so existing `handle_keypress(key)` comparisons work
# unchanged; arcade_app maps arcade key codes to these on the way in.
# ===========================================================================
# Event types
QUIT = 256
KEYDOWN = 768
KEYUP = 769
TEXTINPUT = 771
SRCALPHA = 0x00010000

# Keys (subset actually referenced in the codebase)
K_ESCAPE = 27
K_RETURN = 13
K_SPACE = 32
K_TAB = 9
K_BACKSPACE = 8
K_UP = 1073741906
K_DOWN = 1073741905
K_LEFT = 1073741904
K_RIGHT = 1073741903
K_PAGEUP = 1073741899
K_PAGEDOWN = 1073741902
# Letters
K_a = 97; K_b = 98; K_c = 99; K_d = 100; K_e = 101; K_f = 102
K_g = 103; K_h = 104; K_i = 105; K_j = 106; K_k = 107; K_l = 108
K_m = 109; K_n = 110; K_o = 111; K_p = 112; K_q = 113; K_r = 114
K_s = 115; K_t = 116; K_u = 117; K_v = 118; K_w = 119; K_x = 120
K_y = 121; K_z = 122
# Digits
K_0 = 48; K_1 = 49; K_2 = 50; K_3 = 51; K_4 = 52
K_5 = 53; K_6 = 54; K_7 = 55; K_8 = 56; K_9 = 57


class Event:
    """pygame.event.Event stand-in (type + attributes)."""

    def __init__(self, type, **attrs):
        self.type = type
        self.__dict__.update(attrs)


def init():
    """pygame.init() no-op; Arcade window handles real init."""
    return (0, 0)


def quit():  # noqa: A001 - mirror pygame API name
    return None
