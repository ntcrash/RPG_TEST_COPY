"""Rendering-backend switch — single source of truth.

Gameplay modules select their `pygame` name from here:

    from Code.backend import pygame

Behavior mirrors the switch documented in Code/ui_components.py:
  * MEGITECH_BACKEND unset/empty  -> real pygame  (legacy `python main.py`)
  * MEGITECH_BACKEND=arcade       -> Code.gfx shim (drawing routed to
    arcade_app's arcade.Window; non-render calls delegate back to real pygame)

arcade_app.py sets the env var before importing the game, so a single import
line per module flips that module between backends with zero code changes.
"""

import os

if os.environ.get("MEGITECH_BACKEND", "").strip().lower() == "arcade":
    from Code import gfx as pygame  # noqa: F401  (re-exported)
else:
    import pygame  # noqa: F401  (re-exported)
