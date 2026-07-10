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

# Real pygame is imported lazily too. This shim is a HYBRID: it implements the
# *rendering* slice (draw/font/Rect/Surface/image/transform + key constants)
# on top of Arcade, and DELEGATES everything else (mixer, time, display, event,
# key, mouse, sprite, locals, error, Color, ...) straight through to real
# pygame via the module-level __getattr__ at the bottom of this file. That lets
# a single `from Code import gfx as pygame` swap route drawing to Arcade while
# audio/timing/input keep working exactly as before. See __getattr__ below.
try:
    import pygame as _pygame
except Exception:  # pragma: no cover - pygame not installed in this env
    _pygame = None

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


def _rect_xywh(rect):
    """Unpack a pygame.Rect / gfx.Rect / (x, y, w, h) tuple into ints."""
    if hasattr(rect, "x") and hasattr(rect, "width"):
        return int(rect.x), int(rect.y), int(rect.width), int(rect.height)
    return int(rect[0]), int(rect[1]), int(rect[2]), int(rect[3])


_crop_cache = {}


def _crop_texture(texture, x, y, w, h):
    """Return a sub-region of an Arcade texture (sprite-sheet cell / subsurface).

    CACHED: tile-sheet / sprite-frame blits ask for the same cell every frame.
    Creating a fresh GPU texture each time thrashes (and eventually overflows)
    the texture atlas -> lag then SIGSEGV. Key on the source texture identity +
    region so each distinct cell is uploaded exactly once.
    """
    if _arcade is None:
        return texture
    key = (id(texture), x, y, w, h)
    cropped = _crop_cache.get(key)
    if cropped is not None:
        return cropped
    try:
        cropped = texture.crop(x, y, w, h)
    except Exception:
        try:
            img = texture.image.crop((x, y, x + w, y + h))
            cropped = _arcade.Texture(img)
        except Exception:
            cropped = texture  # last resort: draw the whole sheet
    _crop_cache[key] = cropped
    return cropped


# ---------------------------------------------------------------------------
# Immediate-mode draw primitives (pygame top-left coords -> Arcade, Y flipped).
# These are the single source of truth for "draw to the current Arcade window".
# Both the on-screen draw module AND the off-screen surface replay call these,
# so translated/replayed geometry lands identically to freshly-drawn geometry.
# ---------------------------------------------------------------------------
def _draw_rect(color, rect, width=0):
    if _arcade is None:
        return
    x, y, w, h = tuple(rect)
    c = _norm_color(color)
    bottom = _flip_y(y + h)
    if width == 0:
        _arcade.draw_lbwh_rectangle_filled(x, bottom, w, h, c)
    else:
        _arcade.draw_lbwh_rectangle_outline(x, bottom, w, h, c, width)


def _draw_circle(color, center, radius, width=0):
    if _arcade is None:
        return
    cx, cy = center
    c = _norm_color(color)
    if width == 0:
        _arcade.draw_circle_filled(cx, _flip_y(cy), radius, c)
    else:
        _arcade.draw_circle_outline(cx, _flip_y(cy), radius, c, width)


def _draw_ellipse(color, rect, width=0):
    if _arcade is None:
        return
    x, y, w, h = tuple(rect)
    c = _norm_color(color)
    cx, cy = x + w / 2, y + h / 2
    if width == 0:
        _arcade.draw_ellipse_filled(cx, _flip_y(cy), w, h, c)
    else:
        _arcade.draw_ellipse_outline(cx, _flip_y(cy), w, h, c, width)


def _draw_line(color, start, end, width=1):
    if _arcade is None:
        return
    c = _norm_color(color)
    _arcade.draw_line(start[0], _flip_y(start[1]),
                      end[0], _flip_y(end[1]), c, width)


def _draw_lines(color, closed, points, width=1):
    if _arcade is None or len(points) < 2:
        return
    c = _norm_color(color)
    pts = [(p[0], _flip_y(p[1])) for p in points]
    seq = pts + [pts[0]] if closed else pts
    for i in range(len(seq) - 1):
        _arcade.draw_line(seq[i][0], seq[i][1],
                          seq[i + 1][0], seq[i + 1][1], c, width)


def _draw_polygon(color, points, width=0):
    if _arcade is None:
        return
    c = _norm_color(color)
    pts = [(p[0], _flip_y(p[1])) for p in points]
    if width == 0:
        _arcade.draw_polygon_filled(pts, c)
    else:
        _arcade.draw_polygon_outline(pts, c, width)


# ===========================================================================
# Rect  (mirrors the handful of pygame.Rect features the game relies on)
# ===========================================================================
class Rect:
    """Minimal pygame.Rect stand-in in *pygame* (top-left, y-down) space."""

    __slots__ = ("x", "y", "width", "height")

    def __init__(self, x=0, y=0, width=0, height=0):
        self.x, self.y, self.width, self.height = x, y, width, height

    # --- edges (settable, like pygame.Rect) ---
    @property
    def left(self):
        return self.x

    @left.setter
    def left(self, v):
        self.x = v

    @property
    def right(self):
        return self.x + self.width

    @right.setter
    def right(self, v):
        self.x = v - self.width

    @property
    def top(self):
        return self.y

    @top.setter
    def top(self, v):
        self.y = v

    @property
    def bottom(self):
        return self.y + self.height

    @bottom.setter
    def bottom(self, v):
        self.y = v - self.height

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

    # --- width/height/size aliases ---
    @property
    def w(self):
        return self.width

    @w.setter
    def w(self, v):
        self.width = v

    @property
    def h(self):
        return self.height

    @h.setter
    def h(self, v):
        self.height = v

    @property
    def size(self):
        return (self.width, self.height)

    @size.setter
    def size(self, value):
        self.width, self.height = value

    # --- corner / edge-midpoint anchors (get + set) ---
    @property
    def topright(self):
        return (self.right, self.top)

    @topright.setter
    def topright(self, value):
        self.x = value[0] - self.width
        self.y = value[1]

    @property
    def bottomleft(self):
        return (self.left, self.bottom)

    @bottomleft.setter
    def bottomleft(self, value):
        self.x = value[0]
        self.y = value[1] - self.height

    @property
    def bottomright(self):
        return (self.right, self.bottom)

    @bottomright.setter
    def bottomright(self, value):
        self.x = value[0] - self.width
        self.y = value[1] - self.height

    @property
    def midtop(self):
        return (self.centerx, self.top)

    @midtop.setter
    def midtop(self, value):
        self.centerx = value[0]
        self.y = value[1]

    @property
    def midbottom(self):
        return (self.centerx, self.bottom)

    @midbottom.setter
    def midbottom(self, value):
        self.centerx = value[0]
        self.y = value[1] - self.height

    @property
    def midleft(self):
        return (self.left, self.centery)

    @midleft.setter
    def midleft(self, value):
        self.x = value[0]
        self.centery = value[1]

    @property
    def midright(self):
        return (self.right, self.centery)

    @midright.setter
    def midright(self, value):
        self.x = value[0] - self.width
        self.centery = value[1]

    # --- geometry helpers (mirror pygame.Rect) ---
    def collidepoint(self, px, py=None):
        if py is None:            # allow collidepoint((x, y))
            px, py = px
        return self.left <= px <= self.right and self.top <= py <= self.bottom

    def colliderect(self, other):
        ox, oy, ow, oh = _rect_xywh(other)
        return (self.left < ox + ow and self.right > ox and
                self.top < oy + oh and self.bottom > oy)

    def copy(self):
        return Rect(self.x, self.y, self.width, self.height)

    def move(self, dx, dy):
        return Rect(self.x + dx, self.y + dy, self.width, self.height)

    def move_ip(self, dx, dy):
        self.x += dx
        self.y += dy

    def inflate(self, dx, dy):
        # Grow/shrink keeping the center fixed (pygame semantics).
        return Rect(self.x - dx / 2, self.y - dy / 2,
                    self.width + dx, self.height + dy)

    def inflate_ip(self, dx, dy):
        self.x -= dx / 2
        self.y -= dy / 2
        self.width += dx
        self.height += dy

    def clamp(self, other):
        ox, oy, ow, oh = _rect_xywh(other)
        r = self.copy()
        r.x = max(ox, min(r.x, ox + ow - r.width))
        r.y = max(oy, min(r.y, oy + oh - r.height))
        return r

    def union(self, other):
        ox, oy, ow, oh = _rect_xywh(other)
        left = min(self.left, ox)
        top = min(self.top, oy)
        right = max(self.right, ox + ow)
        bottom = max(self.bottom, oy + oh)
        return Rect(left, top, right - left, bottom - top)

    def contains(self, other):
        ox, oy, ow, oh = _rect_xywh(other)
        return (self.left <= ox and self.top <= oy and
                self.right >= ox + ow and self.bottom >= oy + oh)

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

    def __init__(self, size=(0, 0), flags=0, *, text=None, texture=None,
                 is_screen=False):
        # `flags` is pygame's second positional arg (e.g. SRCALPHA). We accept
        # and ignore it -- the shim always has an alpha channel available.
        self._w, self._h = size
        self._alpha = 255
        self._arcade_text = text        # arcade.Text (for font.render results)
        self._texture = texture         # arcade.Texture (for images)
        self._is_screen = is_screen     # the one real window framebuffer
        # An off-screen draw target: a plain sized Surface that is neither the
        # window nor a text/image surface. pygame code draws onto it and later
        # blits it to the screen. Arcade is immediate-mode with no spare
        # framebuffers, so we RECORD draw ops here and REPLAY them (translated,
        # optionally sub-rect clipped) when this surface is blitted onto the
        # screen. Covers the HUD-overlay and tile-sheet patterns in the game.
        self._offscreen = (not is_screen and text is None and texture is None
                           and (self._w > 0 or self._h > 0))
        self._ops = [] if self._offscreen else None

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
        """Clear the surface to a solid color.

        On the window this clears the whole framebuffer; on an off-screen
        surface it records a fill covering the surface bounds.
        """
        if self._offscreen:
            self._ops.append(("fill", (_norm_color(color),)))
            return
        if _arcade is None:
            return
        c = _norm_color(color)
        _arcade.draw_lbwh_rectangle_filled(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, c)

    # ---- compositing ----
    def blit(self, source: "Surface", dest, area=None):
        """Draw `source` onto this surface at pygame-space top-left `dest`.

        `area` (a sub-rect of `source`) selects a region -- used for tile-sheet
        blitting. If THIS surface is off-screen, the blit is recorded for later
        replay; otherwise it renders straight to the window now.
        """
        if source is None:
            return
        if isinstance(dest, Rect):
            x, y = dest.x, dest.y
        else:
            x, y = dest[0], dest[1]
        if self._offscreen:
            self._ops.append(("blit", (source, x, y, area)))
            return
        self._render_source(source, x, y, area, self._alpha)

    def _alpha_mult(self, source):
        return min(self._alpha, source._alpha)

    # ---- render a source surface straight onto the window at (x, y) ----
    def _render_source(self, source, x, y, area, alpha=255):
        if getattr(source, "_offscreen", False) and source._ops is not None:
            source._replay(x, y, area, min(alpha, source._alpha))
        else:
            source._draw_at(x, y, min(alpha, source._alpha), area)

    # ---- replay this off-screen surface's ops onto the window ----
    def _replay(self, ox, oy, area=None, alpha=255):
        """Draw every recorded op, translated so this surface's local top-left
        lands at window (ox, oy). If `area` is given, only the ops inside that
        sub-rect are drawn (and offset so the sub-rect's top-left maps to
        (ox, oy)) -- this is how tile sheets blit a single 24x24 cell."""
        if isinstance(area, Rect):
            ax, ay, aw, ah = area.x, area.y, area.width, area.height
        elif area is not None:
            ax, ay, aw, ah = area[0], area[1], area[2], area[3]
        else:
            ax = ay = 0
            aw, ah = self._w, self._h
        dx, dy = ox - ax, oy - ay

        def in_area(px, py):
            return (area is None) or (ax <= px < ax + aw and ay <= py < ay + ah)

        for op, args in self._ops:
            if op == "fill":
                (color,) = args
                _draw_rect(color, (ax + dx, ay + dy, aw, ah), 0)
            elif op == "rect":
                color, rect, width = args
                if in_area(rect[0], rect[1]):
                    _draw_rect(color, (rect[0] + dx, rect[1] + dy,
                                       rect[2], rect[3]), width)
            elif op == "circle":
                color, center, radius, width = args
                if in_area(center[0], center[1]):
                    _draw_circle(color, (center[0] + dx, center[1] + dy),
                                 radius, width)
            elif op == "ellipse":
                color, rect, width = args
                if in_area(rect[0], rect[1]):
                    _draw_ellipse(color, (rect[0] + dx, rect[1] + dy,
                                          rect[2], rect[3]), width)
            elif op == "line":
                color, start, end, width = args
                if in_area(start[0], start[1]):
                    _draw_line(color, (start[0] + dx, start[1] + dy),
                               (end[0] + dx, end[1] + dy), width)
            elif op == "lines":
                color, closed, points, width = args
                _draw_lines(color, closed,
                            [(p[0] + dx, p[1] + dy) for p in points], width)
            elif op == "polygon":
                color, points, width = args
                _draw_polygon(color, [(p[0] + dx, p[1] + dy) for p in points],
                              width)
            elif op == "blit":
                src, sx, sy, sub = args
                if in_area(sx, sy):
                    self._render_source(src, sx + dx, sy + dy, sub, alpha)

    # ---- internal: render self (text/texture) at pygame top-left (x, y) ----
    def _draw_at(self, x, y, alpha=255, area=None):
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
            # Texture drawn top-left at pygame (x, y) -> arcade rect. If `area`
            # (a sub-rect of the sheet) is given, crop to it first -- this is
            # how tile sheets blit a single cell via screen.blit(sheet, pos, area).
            tex, w, h = self._texture, self._w, self._h
            if area is not None:
                ax, ay, aw, ah = _rect_xywh(area)
                tex = _crop_texture(self._texture, ax, ay, aw, ah)
                w, h = aw, ah
            rect = _arcade.LBWH(x, _flip_y(y + h), w, h)
            _arcade.draw_texture_rect(tex, rect)

    # ---- pygame.Surface.subsurface: a view of a sub-rect of a sheet ----
    def subsurface(self, rect):
        """Return a Surface for a sub-region (used for sprite-sheet frame
        extraction, e.g. AnimatedPlayer). Texture-backed -> cropped texture."""
        x, y, w, h = _rect_xywh(rect)
        if self._texture is not None and _arcade is not None:
            return Surface((w, h), texture=_crop_texture(self._texture, x, y, w, h))
        # off-screen/plain fallback: hand back a blank sub-sized surface.
        return Surface((w, h))

    # ---- transform.scale support ----
    def _scaled(self, size):
        return Surface(size, texture=self._texture)


# ===========================================================================
# Font  (pygame.font.Font / SysFont -> arcade.Text)
# ===========================================================================
_text_cache = {}


def _get_cached_text(text, size, name, color):
    """Build-or-reuse an arcade.Text. Constructing a Text lays out glyphs and
    is expensive; the game re-renders the same strings every frame, so caching
    creation (not just draw) is the difference between smooth and slideshow.
    Position/alpha are set per-draw in Surface._draw_at, so sharing is safe."""
    key = (text, round(float(size), 1),
           name if isinstance(name, str) else None, tuple(color))
    t = _text_cache.get(key)
    if t is None:
        if len(_text_cache) > 4000:
            _text_cache.clear()  # crude bound: HP/damage strings churn endlessly
        t = _arcade.Text(
            text, 0, 0, color=color,
            font_size=size * 0.75,          # px font-size ~ pygame point size
            font_name=name or ("Kenney Pixel", "arial", "calibri"),
            anchor_x="left", anchor_y="top",
        )
        _text_cache[key] = t
    return t


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
        atext = _get_cached_text(str(text), self.size, self.name, c)
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
def _is_offscreen(surface):
    return getattr(surface, "_offscreen", False)


class _DrawModule:
    """pygame.draw.* -> Arcade. If the target surface is an off-screen buffer
    the op is recorded on it (for later replay); otherwise it draws now."""

    @staticmethod
    def rect(surface, color, rect, width=0, border_radius=0):
        if _is_offscreen(surface):
            surface._ops.append(("rect", (_norm_color(color), tuple(rect), width)))
            return
        _draw_rect(color, rect, width)

    @staticmethod
    def circle(surface, color, center, radius, width=0):
        if _is_offscreen(surface):
            surface._ops.append(("circle", (_norm_color(color), tuple(center),
                                            radius, width)))
            return
        _draw_circle(color, center, radius, width)

    @staticmethod
    def ellipse(surface, color, rect, width=0):
        if _is_offscreen(surface):
            surface._ops.append(("ellipse", (_norm_color(color), tuple(rect), width)))
            return
        _draw_ellipse(color, rect, width)

    @staticmethod
    def line(surface, color, start, end, width=1):
        if _is_offscreen(surface):
            surface._ops.append(("line", (_norm_color(color), tuple(start),
                                          tuple(end), width)))
            return
        _draw_line(color, start, end, width)

    @staticmethod
    def lines(surface, color, closed, points, width=1):
        if _is_offscreen(surface):
            surface._ops.append(("lines", (_norm_color(color), closed,
                                           [tuple(p) for p in points], width)))
            return
        _draw_lines(color, closed, points, width)

    @staticmethod
    def polygon(surface, color, points, width=0):
        if _is_offscreen(surface):
            surface._ops.append(("polygon", (_norm_color(color),
                                             [tuple(p) for p in points], width)))
            return
        _draw_polygon(color, points, width)


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
    """pygame.init(). Delegates to real pygame so mixer/font/display
    subsystems the un-migrated game logic relies on still initialize
    (under the SDL 'dummy' video driver arcade_app sets up)."""
    if _pygame is not None:
        return _pygame.init()
    return (0, 0)


def quit():  # noqa: A001 - mirror pygame API name
    if _pygame is not None:
        return _pygame.quit()
    return None


# ===========================================================================
# Keyboard state. Under the Arcade backend the real pygame window receives NO
# input (arcade owns the window), so real pygame.key.get_pressed() is always
# all-False -> continuous movement (AnimatedPlayer, main.py) would never fire.
# arcade_app translates its on_key_press/on_key_release callbacks into
# set_key(...) here, and we expose a pygame-shaped get_pressed() over that set.
# ===========================================================================
_pressed_keys = set()


def set_key(keyint, down):
    """Called by arcade_app on key press/release so get_pressed() is truthful."""
    if down:
        _pressed_keys.add(keyint)
    else:
        _pressed_keys.discard(keyint)


class _PressedKeys:
    """Indexable held-key state, mirroring pygame.key.get_pressed()'s result."""
    __slots__ = ()

    def __getitem__(self, k):
        return k in _pressed_keys

    def __len__(self):
        return 1 << 16  # pygame returns a fixed-length sequence


class _KeyModule:
    """pygame.key stand-in: get_pressed() reads arcade's held-key set; any
    other attribute (name, get_mods, set_repeat, ...) delegates to real pygame."""

    @staticmethod
    def get_pressed():
        return _PressedKeys()

    @staticmethod
    def get_mods():
        return 0

    def __getattr__(self, name):
        if _pygame is not None:
            return getattr(_pygame.key, name)
        raise AttributeError(name)


key = _KeyModule()


# ===========================================================================
# Hybrid delegation. Any attribute this shim does NOT define itself (mixer,
# time, display, event, key, mouse, sprite, locals, error, Color, Vector2,
# ...) is forwarded to real pygame. Module-level __getattr__ (PEP 562) only
# fires for names missing from this module's namespace, so everything defined
# above (draw, font, Rect, Surface, image, transform, key constants, init,
# quit, ...) keeps the Arcade-backed behavior and takes precedence.
# ===========================================================================
def __getattr__(name):
    if _pygame is not None:
        try:
            return getattr(_pygame, name)
        except AttributeError:
            pass
    raise AttributeError(
        f"module 'Code.gfx' has no attribute {name!r} and real pygame is "
        f"{'not installed' if _pygame is None else 'missing that attribute'}"
    )
