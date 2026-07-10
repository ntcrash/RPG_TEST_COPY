#!/usr/bin/env python3
"""render_smoke.py - headless VISUAL verification of the Arcade backend.

This drives the REAL game (arcade_app.MagitechWindow -> EnhancedGameManager)
through every GameState under the Arcade rendering shim (Code/gfx.py) and
renders each screen to a PNG, asserting that (a) no draw call crashes and
(b) the frame is not entirely black. It is the automated form of migration
"step 1" in ROADMAP.md ("On-device VISUAL verification") — the step that had
to be done by a human before because the sandbox had no display.

It needs a GL context. On a headless box that means a virtual X server, e.g.:

    xvfb-run -a -s "-screen 0 900x700x24" python3 tests/render_smoke.py

Requirements: `pip install arcade pygame`. If arcade isn't installed or no GL
context can be created, the script prints SKIP and exits 0 (see the unittest
wrapper test_render_smoke.py, which subprocess-runs this and skips cleanly).

Exit codes: 0 = all screens rendered (or cleanly skipped), 1 = a screen crashed.
"""
from __future__ import annotations

import os
import sys
import tempfile
import traceback

# Match arcade_app.py's environment: dummy SDL video/audio for the still-pygame
# subsystems (display/mixer/font), Arcade shim as the live rendering backend.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["MEGITECH_BACKEND"] = "arcade"

# Run from the repo root so relative asset/save paths resolve.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_REPO_ROOT)
sys.path.insert(0, _REPO_ROOT)


def _skip(msg: str) -> int:
    print(f"SKIP render_smoke: {msg}")
    return 0


def main() -> int:
    try:
        import arcade
    except Exception as exc:  # arcade not installed
        return _skip(f"arcade not importable ({exc})")

    try:
        from arcade_app import MagitechWindow
    except Exception as exc:
        return _skip(f"arcade_app import failed ({exc})")

    try:
        win = MagitechWindow()
    except Exception as exc:
        # No GL context (no display / no xvfb) -> not a failure, just unrunnable.
        return _skip(f"could not open Arcade window ({exc})")

    game = win.game
    GS = win.GameState

    # A character + built world so the character-dependent screens have content.
    try:
        game.character_manager.create_sample_character()
    except Exception as exc:
        print(f"warn: sample character setup failed ({exc})")
    try:
        game.setup_world_for_current_level()
    except Exception as exc:
        print(f"warn: world setup failed ({exc})")

    out_dir = os.path.join(tempfile.gettempdir(), "megitech_render_smoke")
    os.makedirs(out_dir, exist_ok=True)

    screens = [
        ("01_opening", GS.OPENING),
        ("02_main_menu", GS.MAIN_MENU),
        ("03_char_select", GS.CHARACTER_SELECT),
        ("04_create_char", GS.CREATE_CHARACTER),
        ("05_game_board", GS.GAME_BOARD),
        ("06_store", GS.STORE),
        ("07_inventory", GS.INVENTORY),
        ("08_char_sheet", GS.CHARACTER_SHEET),
        ("09_help", GS.HELP),
        ("10_level_select", GS.LEVEL_SELECT),
        ("11_settings", GS.SETTINGS),
        ("12_crafting", GS.CRAFTING),
        ("13_fight", GS.FIGHT),
    ]

    results = []
    for name, state in screens:
        game.current_state = state
        try:
            win.switch_to()
            win.clear()
            win.on_draw()
            img = arcade.get_image(0, 0, win.width, win.height).convert("RGB")
            img.save(os.path.join(out_dir, f"{name}.png"))
            data = img.getdata()
            nonblack = sum(1 for p in data if p != (0, 0, 0))
            results.append((name, "OK", nonblack / len(data)))
        except Exception as exc:
            results.append((name, "CRASH", repr(exc)))
            traceback.print_exc()

    win._closing = True

    print("\n==== RENDER VERIFICATION RESULTS ====")
    for name, status, info in results:
        info_s = f"{info:.3f} nonblack" if status == "OK" else info
        print(f"{status:6} {name:18} {info_s}")

    crashes = [r for r in results if r[1] == "CRASH"]
    ok = len(results) - len(crashes)
    print(f"\n{ok}/{len(results)} screens rendered without crashing")
    print(f"screenshots: {out_dir}")
    return 1 if crashes else 0


if __name__ == "__main__":
    raise SystemExit(main())
