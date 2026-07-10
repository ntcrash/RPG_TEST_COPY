"""Test suite for Magitech RPG (roadmap P2 #8).

Importing this package configures a headless environment so the game modules
can be imported and exercised on a machine with no display or audio device
(CI, containers).

As of v2.2.5 the suite runs on the Arcade-native ``Code.gfx`` shim by default —
``pygame`` is no longer a required dependency (it was dropped from
requirements.txt at the end of the Arcade migration). The shim provides its own
headless font/draw/audio stand-ins, so no real display, audio card, or pygame
install is needed. To exercise the legacy real-pygame backend instead (only if
pygame is installed), run with ``MEGITECH_BACKEND=pygame``.
"""

import os

# Default the whole suite onto the Arcade-native gfx shim. `setdefault` lets a
# caller opt into the legacy real-pygame backend with MEGITECH_BACKEND=pygame.
os.environ.setdefault("MEGITECH_BACKEND", "arcade")

# Force dummy SDL drivers as well, so the legacy pygame backend (if explicitly
# selected and installed) still imports headlessly. Harmless under the shim.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

# Initialize whichever backend is active (idempotent). Under the default shim
# this is Code.gfx.init(); under MEGITECH_BACKEND=pygame it is pygame.init(),
# which brings up the font subsystem CombatManager needs.
from Code.backend import pygame  # noqa: E402  (import after env setup)

pygame.init()
