"""Central version metadata for Magitech RPG.

Single source of truth for the game version. Import from here instead of
hardcoding version strings throughout the codebase.

    from Code.version import __version__, CAPTION
"""

__version__ = "2.0.4"

# Human-facing title used for the window caption / title bar.
TITLE = "Magitech RPG - Multi-Level Edition"
CAPTION = f"{TITLE} (v{__version__})"

# Which rendering backend is active. Flips to "arcade" as modules migrate.
# Kept here so code can branch on the backend during the transition period.
BACKEND = "pygame"  # -> "arcade" once the migration lands
