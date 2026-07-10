"""test_render_smoke.py - unittest wrapper around tests/render_smoke.py.

Runs the headless Arcade render verification in a SUBPROCESS so that:
  * setting MEGITECH_BACKEND=arcade cannot leak into the other (pygame-backed)
    tests running in the same interpreter, and
  * a native GL/pyglet SIGSEGV can't take down the whole unittest process.

The test SKIPS (never fails) when arcade isn't installed or no GL context can
be created (e.g. CI with no display and no xvfb). When a display IS available
it asserts every game screen renders through Code/gfx.py without crashing.
This is the automated form of ROADMAP migration step 1.
"""
import os
import subprocess
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_HARNESS = os.path.join(_HERE, "render_smoke.py")


def _has_arcade() -> bool:
    try:
        import arcade  # noqa: F401
        return True
    except Exception:
        return False


class RenderSmokeTest(unittest.TestCase):
    @unittest.skipUnless(_has_arcade(), "arcade not installed")
    def test_all_screens_render_through_shim(self):
        # Prefer a virtual X server if one is available and we have no display.
        cmd = [sys.executable, _HARNESS]
        if not os.environ.get("DISPLAY"):
            from shutil import which
            if which("xvfb-run"):
                cmd = ["xvfb-run", "-a", "-s", "-screen 0 900x700x24"] + cmd

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        out = proc.stdout + proc.stderr

        if "SKIP render_smoke" in out:
            self.skipTest(out.strip().splitlines()[-1])

        self.assertEqual(
            proc.returncode, 0,
            msg=f"render_smoke reported a crashing screen:\n{out}",
        )
        self.assertIn("screens rendered without crashing", out)


if __name__ == "__main__":
    unittest.main()
