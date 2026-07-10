"""Rendering-backend switch — single source of truth.

Gameplay modules select their `pygame` name from here:

    from Code.backend import pygame

As of v2.2.5 (final pygame-migration step) the Arcade-native `Code.gfx` shim is
the DEFAULT and only required backend — `pygame` is no longer a declared
dependency (removed from requirements.txt). The legacy real-pygame drawing path
survives only as an explicit, best-effort opt-in for anyone who still has
pygame installed:

  * MEGITECH_BACKEND unset / empty / "arcade"  -> Code.gfx shim  (default)
  * MEGITECH_BACKEND=pygame                     -> real pygame    (opt-in;
        requires pygame to be installed, otherwise ImportError)

arcade_app.py sets the env var before importing the game, so a single import
line per module flips that module between backends with zero code changes.
"""

import os

if os.environ.get("MEGITECH_BACKEND", "").strip().lower() == "pygame":
    import pygame  # noqa: F401  (re-exported; opt-in legacy backend)
else:
    from Code import gfx as pygame  # noqa: F401  (re-exported; default)
