"""Central version metadata for Magitech RPG.

Single source of truth for the game version. Import from here instead of
hardcoding version strings throughout the codebase.

    from Code.version import __version__, CAPTION
"""

__version__ = "2.2.1"

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
# NOTE: pygame remains a runtime dependency — Code/gfx.py delegates audio
# (pygame.mixer), timing, and input constants to real pygame under either value.
BACKEND = "arcade"
