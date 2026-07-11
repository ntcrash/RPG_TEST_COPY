"""Central version metadata for Magitech RPG.

Single source of truth for the game version. Import from here instead of
hardcoding version strings throughout the codebase.

    from Code.version import __version__, CAPTION
"""

__version__ = "2.11.0"

# Human-facing title used for the window caption / title bar.
TITLE = "Magitech RPG - Multi-Level Edition"
CAPTION = f"{TITLE} (v{__version__})"

# Default rendering backend. As of v2.2.1 Arcade is the ONLY entry point:
# `python main.py` sets MEGITECH_BACKEND=arcade before importing the Code.*
# package (unless already set) and opens the Arcade window. The deprecated
# pygame run() loop and its MEGITECH_BACKEND=pygame launch fallback were removed
# in v2.2.1 (migration step 5). MEGITECH_BACKEND still selects the *drawing*
# binding star-exported by Code/ui_components.py and Code/backend.py:
#   MEGITECH_BACKEND=arcade (default) -> Code.gfx shim + arcade.Window
#   MEGITECH_BACKEND=pygame           -> real pygame drawing (headless test imports only)
# As of v2.2.5 the migration is COMPLETE: `pygame` has been dropped as a
# dependency (removed from requirements.txt). Every gameplay module now takes its
# drawing name from Code/backend.py, which defaults to the Arcade-native
# Code.gfx shim; the shim implements audio (arcade.Sound), timing, sprite,
# display, event, init, and the draw/font/Rect/Surface API on top of Arcade with
# no `import pygame` required. The legacy real-pygame backend survives only as an
# explicit opt-in (MEGITECH_BACKEND=pygame) for anyone who installs pygame
# themselves; unset/empty/"arcade" all resolve to the shim.
BACKEND = "arcade"
