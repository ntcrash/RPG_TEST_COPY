"""arcade_app.py - Arcade 3.x entry point for Magitech RPG (v2.x).

This is the NEW front door for the game, replacing pygame's hand-rolled
`while running:` loop in main.py with an event-driven arcade.Window.

WHAT THIS DOES TODAY (foundation)
---------------------------------
  * Opens a real Arcade window at 800x600 and runs the game loop via
    on_update / on_draw callbacks.
  * Translates Arcade (pyglet) keyboard + text events into the exact
    pygame-shaped events the existing EnhancedGameManager.handle_event /
    handle_keypress already consume -- so the game's state machine runs
    UNCHANGED on the Arcade loop.
  * Ticks game logic at the original 15 Hz (main.py used clock.tick(15)).
  * Draws an on-screen "Arcade backend online" overlay so you can confirm
    the window + input + loop foundation works before any module's draw()
    is ported.

WHAT'S NEXT (incremental, per project gitflow rules)
----------------------------------------------------
  Each render module (ui_components, tile_map, combat, ...) gets migrated
  from `import pygame` to `from Code import gfx as pygame`. As each one
  lands, its visuals start appearing in this window. pygame stays runnable
  via `python main.py` until the last module is ported.

RUN IT (on the Mac, not the sandbox):
    pip install arcade
    python arcade_app.py
"""

import os

# CRITICAL: run pygame's display under SDL's headless "dummy" video driver.
# The un-migrated modules still call pygame.display.set_mode(), pygame image
# .convert_alpha(), pygame.font, etc. On a real driver that creates a second
# OpenGL context which steals the current context from Arcade/pyglet, causing
# "No GL context; create a Window first" the moment Arcade draws. The dummy
# driver gives pygame a valid off-screen video mode (so surface/convert/font
# ops work) WITHOUT any real GL context. Must be set before pygame.display
# initializes. Audio (SDL_AUDIODRIVER) is untouched, so game sound still works.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import arcade

from Code import gfx
from Code.version import CAPTION, __version__

WIDTH, HEIGHT = 800, 600
LOGIC_HZ = 15                       # matches v1.x clock.tick(15)
LOGIC_DT = 1.0 / LOGIC_HZ


# ---------------------------------------------------------------------------
# Arcade (pyglet) key code  ->  pygame/SDL key code.
# The game compares against pygame.K_* (== SDL codes == Code.gfx.K_* values),
# so we translate incoming Arcade events to those integers.
# ---------------------------------------------------------------------------
_A = arcade.key
ARCADE_TO_PYGAME_KEY = {
    _A.ESCAPE: gfx.K_ESCAPE,
    _A.RETURN: gfx.K_RETURN,
    _A.ENTER: gfx.K_RETURN,
    _A.SPACE: gfx.K_SPACE,
    _A.TAB: gfx.K_TAB,
    _A.BACKSPACE: gfx.K_BACKSPACE,
    _A.UP: gfx.K_UP,
    _A.DOWN: gfx.K_DOWN,
    _A.LEFT: gfx.K_LEFT,
    _A.RIGHT: gfx.K_RIGHT,
    _A.PAGEUP: gfx.K_PAGEUP,
    _A.PAGEDOWN: gfx.K_PAGEDOWN,
}
# Letters a-z and digits 0-9 map to identical integer codes in both systems.
for _c in range(ord("a"), ord("z") + 1):
    ARCADE_TO_PYGAME_KEY.setdefault(_c, _c)
for _c in range(ord("0"), ord("9") + 1):
    ARCADE_TO_PYGAME_KEY.setdefault(_c, _c)


class MagitechWindow(arcade.Window):
    """Hosts the existing game manager on the Arcade event loop."""

    def __init__(self):
        super().__init__(WIDTH, HEIGHT, CAPTION)
        arcade.set_background_color(arcade.color.BLACK)

        # Tell the render shim how tall the surface is (for Y-flip math).
        gfx.configure(WIDTH, HEIGHT)

        # The game draws to this shim; blits/fills/draws land on this window.
        # NB: don't name this `self.screen` -- arcade.Window already defines a
        # read-only `screen` property (the pyglet display), which collides.
        self._surface = gfx.Surface((WIDTH, HEIGHT))

        # Import lazily so importing this module never triggers pygame init
        # before the Arcade window exists.
        from main import EnhancedGameManager, GameState
        self.GameState = GameState
        self.game = EnhancedGameManager()
        # Redirect the manager's render target from its pygame surface to ours.
        self.game.screen = self._surface

        # pygame.display.init (dummy driver) may have made an SDL context current
        # during construction; reclaim pyglet's GL context so Arcade can draw.
        self.switch_to()

        self._accum = 0.0

        # Overlay text confirming the foundation is live.
        self._banner = arcade.Text(
            f"Arcade backend online  -  v{__version__}",
            10, HEIGHT - 10, arcade.color.LIGHT_GREEN, 14,
            anchor_x="left", anchor_y="top",
        )
        self._hint = arcade.Text(
            "Foundation running on arcade.Window. Modules light up as they migrate. "
            "Press keys to drive the state machine.",
            10, 22, arcade.color.GRAY, 11, anchor_x="left", anchor_y="bottom",
        )
        self._state_text = arcade.Text(
            "", 10, HEIGHT - 30, arcade.color.WHITE, 12,
            anchor_x="left", anchor_y="top",
        )

    # ---- game loop ----
    def on_update(self, delta_time: float):
        """Throttle to the original 15 Hz logic tick."""
        self._accum += delta_time
        while self._accum >= LOGIC_DT:
            self._accum -= LOGIC_DT
            try:
                self.game.update()
            except Exception as exc:  # keep window alive during migration
                print(f"[arcade_app] update() error: {exc}")

    def on_draw(self):
        self.clear()
        # Run the game's own draw pipeline (routes through gfx for migrated
        # modules; pygame-only modules simply draw nothing yet).
        try:
            self.game.draw()
        except Exception as exc:
            print(f"[arcade_app] draw() error: {exc}")

        # Foundation overlay so the window is never blank during migration.
        self._banner.draw()
        state_name = self._state_name(self.game.current_state)
        self._state_text.text = f"state: {state_name}"
        self._state_text.draw()
        self._hint.draw()

    def _state_name(self, value):
        for name in dir(self.GameState):
            if not name.startswith("_") and getattr(self.GameState, name) == value:
                return name
        return str(value)

    # ---- input translation ----
    def on_key_press(self, symbol, modifiers):
        key = ARCADE_TO_PYGAME_KEY.get(symbol)
        if key is None:
            return
        event = gfx.Event(gfx.KEYDOWN, key=key, mod=modifiers, unicode="")
        result = self.game.handle_event(event)
        if result is False:
            self._shutdown()

    def on_text(self, text):
        """Character-creation name entry uses pygame TEXTINPUT events."""
        if self.game.current_state == self.GameState.CREATE_CHARACTER:
            event = gfx.Event(gfx.TEXTINPUT, text=text)
            self.game.handle_event(event)

    def on_close(self):
        self._shutdown()
        super().on_close()

    def _shutdown(self):
        if hasattr(self.game, "level_manager"):
            try:
                self.game.level_manager.save_progression()
            except Exception:
                pass
        arcade.close_window()


def main():
    MagitechWindow()
    arcade.run()


if __name__ == "__main__":
    main()
