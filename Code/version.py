"""Central version metadata for Magitech RPG.

Single source of truth for the game version. Import from here instead of
hardcoding version strings throughout the codebase.

    from Code.version import __version__, CAPTION
"""

__version__ = "2.2.3"

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
# NOTE: pygame remains a runtime dependency, but the migration keeps chipping
# away at what routes through it. As of v2.2.2 audio (pygame.mixer ->
# arcade.Sound) and timing (pygame.time) are Arcade-native in Code/gfx.py; as of
# v2.2.3 sprite (gfx.sprite.Sprite) and input constants (pygame.locals) are too,
# so Code/tile_map.py and Code/animated_player.py no longer import real pygame.
# Real pygame is still imported for the remaining delegations (display/event)
# until migration step 6 finishes and the dep is dropped.
BACKEND = "arcade"
