"""Test suite for Magitech RPG (roadmap P2 #8).

Importing this package configures a headless SDL environment so the
Pygame-coupled game modules can be imported and exercised on a machine with
no display or audio device (CI, containers). Set BEFORE any ``import pygame``
happens in a test module, which is why it lives in the package ``__init__``.
"""

import os

# Force Pygame/SDL to use dummy drivers — no window, no audio card required.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
# Keep the game on the legacy pygame backend for tests (not the Arcade shim).
os.environ.setdefault("MEGITECH_BACKEND", "pygame")

import pygame  # noqa: E402  (import after env setup, intentionally)

# pygame.init() brings up the font subsystem that CombatManager needs. It is
# idempotent, so calling it once here covers every test module.
pygame.init()
