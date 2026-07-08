"""Central version metadata for Magitech RPG.

Single source of truth for the game version. Import from here instead of
hardcoding version strings throughout the codebase.

    from Code.version import __version__, CAPTION
"""

__version__ = "2.0.6"

# Human-facing title used for the window caption / title bar.
TITLE = "Magitech RPG - Multi-Level Edition"
CAPTION = f"{TITLE} (v{__version__})"

# Default rendering backend. The ACTUAL live backend is chosen at runtime by
# the MEGITECH_BACKEND env var, read in Code/ui_components.py:
#   unset            -> real pygame   (legacy `python main.py`)
#   MEGITECH_BACKEND=arcade -> Code.gfx shim (set by arcade_app.py)
BACKEND = "pygame"
