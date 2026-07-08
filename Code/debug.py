"""Central debug utilities for Megitech.

Gate verbose developer output behind a single DEBUG flag so it never spams
players' consoles in normal play. Set DEBUG = True (or the MEGITECH_DEBUG
environment variable to a truthy value) to re-enable the detailed combat and
settings diagnostics.
"""

import os

# Master switch. Off by default for release builds.
DEBUG = os.environ.get("MEGITECH_DEBUG", "").lower() in ("1", "true", "yes", "on")


def debug_print(*args, **kwargs):
    """print() that only fires when DEBUG is enabled.

    Automatically prefixes output with 'DEBUG:' to match the prior log format.
    """
    if DEBUG:
        print("DEBUG:", *args, **kwargs)
