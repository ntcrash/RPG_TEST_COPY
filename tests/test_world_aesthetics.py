"""Unit tests for cleaner grass terrain / flower declutter (roadmap P5 #30).

Pins the World Aesthetics change added in v2.9.0: legacy maps sprinkled
decorative flower tiles ('F'/'f'/'R'/'r') across the grass, producing a busy,
cluttered field. ``EnhancedTileMap.declutter_flowers`` now swaps each flower
marker for a deterministic grass variant so the terrain reads as clean, natural
grass. These tests exercise the pure declutter helper and confirm it is wired
into ``load_map_from_data`` (no flower tiles survive to the rendered tile map).

Everything runs headlessly through the ``Code.gfx`` shim (see ``tests/__init__``)
so it needs no display, GPU, or map assets.
"""

import os
import unittest

os.environ.setdefault("MEGITECH_BACKEND", "arcade")

from Code.backend import pygame  # noqa: E402  (default: Code.gfx shim)

pygame.init()

from Code.tile_map import EnhancedTileMap  # noqa: E402

FLOWER_CHARS = set("FfRr")
GRASS_CHARS = set("Ggd")


class DeclutterFlowersTests(unittest.TestCase):
    """The pure ``declutter_flowers`` classmethod."""

    def test_flowers_replaced_with_grass(self):
        cleaned = EnhancedTileMap.declutter_flowers("GGFfFGG", row=0)
        # No flower characters survive; every replacement is a grass variant.
        self.assertFalse(set(cleaned) & FLOWER_CHARS)
        for src, dst in zip("GGFfFGG", cleaned):
            if src in FLOWER_CHARS:
                self.assertIn(dst, GRASS_CHARS)

    def test_non_flower_chars_untouched(self):
        line = "GtTtGGGpGG+ppW"  # trees, path, water, intersection — no flowers
        self.assertEqual(EnhancedTileMap.declutter_flowers(line, row=3), line)

    def test_length_preserved(self):
        line = "FfRrGGtTtWwXY"
        self.assertEqual(len(EnhancedTileMap.declutter_flowers(line, row=7)), len(line))

    def test_all_flower_variants_covered(self):
        # Every declared flower char must be treated as clutter.
        for ch in "FfRr":
            self.assertNotIn(ch, EnhancedTileMap.declutter_flowers(ch * 5, row=0))

    def test_deterministic(self):
        line = "GGFfFGGRrGG"
        self.assertEqual(
            EnhancedTileMap.declutter_flowers(line, row=2),
            EnhancedTileMap.declutter_flowers(line, row=2),
        )

    def test_position_varies_replacement(self):
        # The three grass variants should all appear across a long flower run,
        # so the terrain isn't one flat monotone block.
        cleaned = EnhancedTileMap.declutter_flowers("F" * 9, row=0)
        self.assertEqual(set(cleaned), GRASS_CHARS)

    def test_empty_line(self):
        self.assertEqual(EnhancedTileMap.declutter_flowers("", row=0), "")


class LoadMapDeclutterTests(unittest.TestCase):
    """Flower clutter is stripped end-to-end when a map is loaded."""

    def setUp(self):
        self.tm = EnhancedTileMap()

    def test_flower_tiles_map_to_grass(self):
        # A flower tile and a grass tile must resolve to the SAME tile rect,
        # proving the flower was decluttered to grass before mapping.
        grass_rect = self.tm.load_map_from_data(["G"])[0][0]
        for flower in "FfRr":
            tile = self.tm.load_map_from_data([flower])[0][0]
            self.assertEqual(tile, grass_rect)

    def test_no_flower_distinct_tile_in_grid(self):
        # Every cell of a flower-laden line must resolve to one of the grass
        # tile rects (G / g / d) — no non-grass tile sneaks in via a flower.
        grass_rects = {
            self.tm.load_map_from_data([ch])[0][0] for ch in "Ggd"
        }
        line = "GGFfFGGRrGG"
        grid = self.tm.load_map_from_data([line])
        for cell in grid[0][: len(line)]:
            self.assertIn(cell, grass_rects)


if __name__ == "__main__":
    unittest.main()
