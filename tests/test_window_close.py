"""test_window_close.py - regression tests for the app-shutdown path (P5 #24).

Pins the fix that made the window "X" button, the Quit menu item, and Escape all
end the WHOLE program via one idempotent shutdown routine in arcade_app.py:

  * on_close() delegates to _shutdown() (and does NOT double-close via super()).
  * _shutdown() is idempotent (re-entry is a no-op) so a stray second on_close
    from pyglet during teardown can't crash or save progression twice.
  * _shutdown() saves progression once, closes the window, and calls
    arcade.exit() so arcade.run() returns and main() can end the process.

GPU-free: we bypass arcade.Window.__init__ with object.__new__ so no display /
GL context is ever created; the arcade module itself only needs to be importable.
The test SKIPS (never fails) when arcade isn't installed, mirroring
tests/test_render_smoke.py, so the headless sandbox suite stays green while CI
(which installs arcade) exercises it for real.
"""
import unittest
from unittest import mock


def _has_arcade() -> bool:
    try:
        import arcade  # noqa: F401
        return True
    except Exception:
        return False


@unittest.skipUnless(_has_arcade(), "arcade not installed")
class WindowShutdownTests(unittest.TestCase):
    def _make_window(self):
        """A MagitechWindow with __init__ bypassed (no real window opened)."""
        import arcade_app
        win = object.__new__(arcade_app.MagitechWindow)
        # Minimal attributes _shutdown / on_close touch.
        win.game = mock.Mock()
        win.game.level_manager = mock.Mock()
        win.close = mock.Mock()  # stand in for arcade.Window.close
        return win, arcade_app

    def test_shutdown_saves_closes_and_exits(self):
        win, arcade_app = self._make_window()
        with mock.patch.object(arcade_app.arcade, "exit") as exit_mock:
            win._shutdown()
        self.assertTrue(win._closing)
        win.game.level_manager.save_progression.assert_called_once()
        win.close.assert_called_once()
        exit_mock.assert_called_once()

    def test_shutdown_is_idempotent(self):
        win, arcade_app = self._make_window()
        with mock.patch.object(arcade_app.arcade, "exit") as exit_mock:
            win._shutdown()
            win._shutdown()
            win._shutdown()
        # Second and third calls must be no-ops: save/close/exit happen once.
        win.game.level_manager.save_progression.assert_called_once()
        win.close.assert_called_once()
        exit_mock.assert_called_once()

    def test_on_close_routes_through_shutdown(self):
        win, _ = self._make_window()
        with mock.patch.object(win, "_shutdown") as shutdown_mock:
            win.on_close()
        shutdown_mock.assert_called_once()

    def test_shutdown_survives_save_failure(self):
        win, arcade_app = self._make_window()
        win.game.level_manager.save_progression.side_effect = RuntimeError("disk full")
        with mock.patch.object(arcade_app.arcade, "exit") as exit_mock:
            win._shutdown()  # must not raise
        # Even if the save blows up, the app still closes and exits.
        win.close.assert_called_once()
        exit_mock.assert_called_once()

    def test_shutdown_without_level_manager(self):
        win, arcade_app = self._make_window()
        del win.game.level_manager
        win.game = mock.Mock(spec=[])  # no level_manager attribute
        with mock.patch.object(arcade_app.arcade, "exit") as exit_mock:
            win._shutdown()  # must not raise
        win.close.assert_called_once()
        exit_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
