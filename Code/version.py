"""Central version metadata for Magitech RPG.

Single source of truth for the game version. Import from here instead of
hardcoding version strings throughout the codebase.

    from Code.version import __version__, CAPTION
"""

__version__ = "2.2.0"

# Human-facing title used for the window caption / title bar.
TITLE = "Magitech RPG - Multi-Level Edition"
CAPTION = f"{TITLE} (v{__version__})"

# Default rendering backend. As of v2.2.0 the game LAUNCHES on Arcade by
# default: `python main.py` sets MEGITECH_BACKEND=arcade before importing the
# Code.* package (unless already set) and opens the Arcade window. The ACTUAL
# live backend is still chosen at runtime by the MEGITECH_BACKEND env var, read
# in Code/ui_components.py and Code/backend.py:
#   MEGITECH_BACKEND=arcade (default) -> Code.gfx shim + arcade.Window
#   MEGITECH_BACKEND=pygame           -> real pygame + legacy run() loop
BACKEND = "arcade"
