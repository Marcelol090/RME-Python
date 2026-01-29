"""Tests for BrushSettings functionality."""

from __future__ import annotations

import unittest

from py_rme_canary.core.data.item import Position
from py_rme_canary.logic_layer.brush_settings import (
    BrushSettings,
    BrushShape,
)


class TestBrushShape(unittest.TestCase):
    """Test BrushShape enum."""

    def test_shapes_exist(self) -> None:
        """Both shapes are defined."""
        self.assertEqual(BrushShape.CIRCLE, 0)
        self.assertEqual(BrushShape.SQUARE, 1)


class TestBrushSettings(unittest.TestCase):
    """Test BrushSettings functionality."""

    def test_default_settings(self) -> None:
        """Default is 1x1 square."""
        settings = BrushSettings()
        self.assertEqual(settings.size, 0)
        self.assertEqual(settings.shape, BrushShape.SQUARE)
        self.assertEqual(settings.get_radius(), 0)

    def test_radius_calculation(self) -> None:
        """Radius matches size dimensions."""
        # Size 0 = 1x1 = radius 0
        self.assertEqual(BrushSettings(size=0).get_radius(), 0)
        # Size 1 = 3x3 = radius 1
        self.assertEqual(BrushSettings(size=1).get_radius(), 1)
        # Size 2 = 5x5 = radius 2
        self.assertEqual(BrushSettings(size=2).get_radius(), 2)

    def test_affected_positions_1x1(self) -> None:
        """Size 0 affects only center tile."""
        settings = BrushSettings(size=0)
        center = Position(x=10, y=10, z=7)
        positions = list(settings.get_affected_positions(center))
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0], center)

    def test_affected_positions_3x3_square(self) -> None:
        """Size 1 square affects 9 tiles."""
        settings = BrushSettings(size=1, shape=BrushShape.SQUARE)
        center = Position(x=10, y=10, z=7)
        positions = list(settings.get_affected_positions(center))
        self.assertEqual(len(positions), 9)

        # Check corners exist
        pos_tuples = {(p.x, p.y) for p in positions}
        self.assertIn((9, 9), pos_tuples)  # NW
        self.assertIn((11, 9), pos_tuples)  # NE
        self.assertIn((9, 11), pos_tuples)  # SW
        self.assertIn((11, 11), pos_tuples)  # SE

    def test_affected_positions_3x3_circle(self) -> None:
        """Size 1 circle affects fewer tiles than square."""
        settings = BrushSettings(size=1, shape=BrushShape.CIRCLE)
        center = Position(x=10, y=10, z=7)
        positions = list(settings.get_affected_positions(center))

        # Circle excludes corners (distance > 1)
        # Center + 4 cardinals = 5 tiles for radius 1
        self.assertEqual(len(positions), 5)

        pos_tuples = {(p.x, p.y) for p in positions}
        self.assertIn((10, 10), pos_tuples)  # Center
        self.assertIn((9, 10), pos_tuples)  # W
        self.assertIn((11, 10), pos_tuples)  # E
        self.assertIn((10, 9), pos_tuples)  # N
        self.assertIn((10, 11), pos_tuples)  # S
        # Corners should NOT be included
        self.assertNotIn((9, 9), pos_tuples)

    def test_preview_offsets(self) -> None:
        """Preview returns dx, dy pairs."""
        settings = BrushSettings(size=0)
        offsets = settings.get_preview_positions(Position(0, 0, 0))
        self.assertEqual(offsets, [(0, 0)])


if __name__ == "__main__":
    unittest.main()
