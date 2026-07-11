"""Tests for the special victory-message banner (roadmap P5 #29).

Covers `build_victory_messages` in `Code.enhanced_combat_integration`: the
trophy banner for boss defeats vs. the compact banner for normal wins, the
level-up line, reward formatting, colour coding, and — importantly — that every
decorative glyph is in the Basic Multilingual Plane so it survives the
`Code.gfx` renderer (which strips astral-plane emoji). Pure/deterministic, no
GPU or combat state needed.
"""

import unittest

from Code.enhanced_combat_integration import (
    build_victory_messages,
    VICTORY_STAR,
    VICTORY_SPARK,
)
from Code.ui_components import GOLD, GREEN, YELLOW


class VictoryMessageTests(unittest.TestCase):
    def test_boss_banner_shape(self):
        lines = build_victory_messages(True, 120, 300, leveled_up=False)
        # Five-line trophy banner: border, title, "Level Complete!", reward, border.
        self.assertEqual(len(lines), 5)
        texts = [t for t, _ in lines]
        self.assertEqual(texts[0], texts[4])  # matching top/bottom borders
        self.assertIn("BOSS DEFEATED!", texts[1])
        self.assertEqual(texts[2], "Level Complete!")

    def test_normal_banner_shape(self):
        lines = build_victory_messages(False, 40, 80, leveled_up=False)
        # Compact two-line banner for a non-boss win.
        self.assertEqual(len(lines), 2)
        self.assertIn("Victory!", lines[0][0])
        self.assertNotIn("BOSS", lines[0][0])

    def test_reward_text_present(self):
        for is_boss in (True, False):
            lines = build_victory_messages(is_boss, 77, 210, leveled_up=False)
            joined = " ".join(t for t, _ in lines)
            self.assertIn("+77 XP", joined)
            self.assertIn("+210 Credits", joined)

    def test_level_up_line_appended(self):
        without = build_victory_messages(False, 10, 20, leveled_up=False)
        with_lu = build_victory_messages(False, 10, 20, leveled_up=True)
        self.assertEqual(len(with_lu), len(without) + 1)
        self.assertIn("LEVEL UP!", with_lu[-1][0])

    def test_boss_level_up_line_appended(self):
        lines = build_victory_messages(True, 10, 20, leveled_up=True)
        self.assertEqual(len(lines), 6)
        self.assertIn("LEVEL UP!", lines[-1][0])

    def test_colors_are_rgb_tuples(self):
        lines = build_victory_messages(True, 10, 20, leveled_up=True)
        for _, color in lines:
            self.assertIn(color, (GOLD, GREEN, YELLOW))

    def test_all_glyphs_are_bmp(self):
        # Every character must be <= U+FFFF so the gfx shim's emoji-stripping
        # renderer keeps the decorations visible on-screen. The 🏆 emoji is the
        # deliberate exception (kept for the real-pygame backend / logs), so we
        # strip it before asserting.
        lines = build_victory_messages(True, 10, 20, leveled_up=True)
        for text, _ in lines:
            visible = text.replace("\U0001F3C6", "")
            for ch in visible:
                self.assertLessEqual(
                    ord(ch), 0xFFFF, f"non-BMP glyph {ch!r} would be stripped on-screen"
                )

    def test_decoration_glyphs_are_bmp_constants(self):
        self.assertLessEqual(ord(VICTORY_STAR), 0xFFFF)
        self.assertLessEqual(ord(VICTORY_SPARK), 0xFFFF)

    def test_deterministic(self):
        a = build_victory_messages(True, 55, 99, leveled_up=True)
        b = build_victory_messages(True, 55, 99, leveled_up=True)
        self.assertEqual(a, b)

    def test_line_length_within_log_width(self):
        # The combat log truncates each message to 60 chars (combat_system.py);
        # keep the banner within that so nothing is clipped mid-word.
        lines = build_victory_messages(True, 999, 9999, leveled_up=True)
        for text, _ in lines:
            self.assertLessEqual(len(text), 60)


if __name__ == "__main__":
    unittest.main()
