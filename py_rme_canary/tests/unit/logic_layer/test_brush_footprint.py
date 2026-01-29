"""Unit tests for brush footprint/border offset functions.

Validates parity between Python implementation and C++ legacy (source/map_display.cpp).
Tests cover:
- Square and circle footprints
- Size edge cases (0, 1, 3, 5)
- Border ring calculation
- Edge symmetry verification

C++ Reference (map_display.cpp::getTilesToDraw):
    Square draw: x >= -size && x <= size && y >= -size && y <= size
    Square border: abs(x) - size < 2 && abs(y) - size < 2
    Circle draw: distance < size + 0.005
    Circle border: abs(distance - size) < 1.5
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pytest

from py_rme_canary.logic_layer.geometry import iter_brush_border_offsets, iter_brush_offsets

if TYPE_CHECKING:
    from collections.abc import Sequence


# ============================================================================
# C++ Legacy Algorithm Reference Implementation
# ============================================================================


def _cpp_legacy_draw_offsets(size: int, shape: str) -> list[tuple[int, int]]:
    """Replicates C++ MapCanvas::getTilesToDraw tilestodraw logic.

    From source/map_display.cpp lines 2780-2800.
    """
    size = max(0, int(size))
    shape = (shape or "square").strip().lower()
    result: list[tuple[int, int]] = []

    for y in range(-size - 1, size + 2):
        for x in range(-size - 1, size + 2):
            if shape == "circle":
                # C++: double distance = sqrt(double(x * x) + double(y * y));
                # C++: if (distance < g_gui.GetBrushSize() + 0.005)
                distance = math.sqrt(float(x * x + y * y))
                if distance < float(size) + 0.005:
                    result.append((x, y))
            # C++: if (x >= -size && x <= size && y >= -size && y <= size)
            elif x >= -size and x <= size and y >= -size and y <= size:
                result.append((x, y))

    return result


def _cpp_legacy_border_offsets(size: int, shape: str) -> list[tuple[int, int]]:
    """Replicates C++ MapCanvas::getTilesToDraw tilestoborder logic.

    From source/map_display.cpp lines 2780-2800.
    """
    size = max(0, int(size))
    shape = (shape or "square").strip().lower()
    result: list[tuple[int, int]] = []

    for y in range(-size - 1, size + 2):
        for x in range(-size - 1, size + 2):
            if shape == "circle":
                # C++: if (std::abs(distance - g_gui.GetBrushSize()) < 1.5)
                distance = math.sqrt(float(x * x + y * y))
                if abs(distance - float(size)) < 1.5:
                    result.append((x, y))
            # C++: if (std::abs(x) - size < 2 && std::abs(y) - size < 2)
            elif abs(x) - size < 2 and abs(y) - size < 2:
                result.append((x, y))

    return result


# ============================================================================
# Square Footprint Tests
# ============================================================================


class TestSquareFootprintDraw:
    """Tests for square-shaped brush footprint (draw tiles)."""

    @pytest.mark.parametrize("size", [0, 1, 3, 5])
    def test_matches_cpp_legacy(self, size: int) -> None:
        """Verify Python output matches C++ legacy for various sizes."""
        expected = _cpp_legacy_draw_offsets(size, "square")
        actual = list(iter_brush_offsets(size, "square"))
        assert actual == expected

    def test_size_0_returns_single_tile(self) -> None:
        """Size 0 should return only the center tile (0, 0)."""
        offsets = list(iter_brush_offsets(0, "square"))
        assert offsets == [(0, 0)]

    def test_size_1_returns_3x3_grid(self) -> None:
        """Size 1 should return 3x3 = 9 tiles."""
        offsets = list(iter_brush_offsets(1, "square"))
        assert len(offsets) == 9
        # Verify all tiles in [-1, 1] x [-1, 1] are present
        for y in range(-1, 2):
            for x in range(-1, 2):
                assert (x, y) in offsets

    def test_size_3_returns_7x7_grid(self) -> None:
        """Size 3 should return 7x7 = 49 tiles."""
        offsets = list(iter_brush_offsets(3, "square"))
        assert len(offsets) == 49

    def test_size_5_returns_11x11_grid(self) -> None:
        """Size 5 should return 11x11 = 121 tiles."""
        offsets = list(iter_brush_offsets(5, "square"))
        assert len(offsets) == 121

    def test_formula_2splus1_squared(self) -> None:
        """For size s, square footprint should be (2s+1)^2 tiles."""
        for size in range(0, 10):
            offsets = list(iter_brush_offsets(size, "square"))
            expected_count = (2 * size + 1) ** 2
            assert len(offsets) == expected_count


class TestSquareFootprintBorder:
    """Tests for square-shaped brush border (autoborder tiles)."""

    @pytest.mark.parametrize("size", [0, 1, 3, 5])
    def test_matches_cpp_legacy(self, size: int) -> None:
        """Verify Python output matches C++ legacy for various sizes."""
        expected = _cpp_legacy_border_offsets(size, "square")
        actual = list(iter_brush_border_offsets(size, "square"))
        assert actual == expected

    def test_size_0_returns_3x3_grid(self) -> None:
        """Size 0 border should be 3x3 = 9 tiles."""
        offsets = list(iter_brush_border_offsets(0, "square"))
        assert len(offsets) == 9

    def test_size_1_returns_5x5_grid(self) -> None:
        """Size 1 border should be 5x5 = 25 tiles."""
        offsets = list(iter_brush_border_offsets(1, "square"))
        assert len(offsets) == 25

    def test_size_3_returns_9x9_grid(self) -> None:
        """Size 3 border should be 9x9 = 81 tiles."""
        offsets = list(iter_brush_border_offsets(3, "square"))
        assert len(offsets) == 81

    def test_formula_2splus3_squared(self) -> None:
        """For size s, square border should be (2s+3)^2 tiles."""
        for size in range(0, 10):
            offsets = list(iter_brush_border_offsets(size, "square"))
            expected_count = (2 * size + 3) ** 2
            assert len(offsets) == expected_count

    def test_border_contains_draw_tiles(self) -> None:
        """Border tiles should always include all draw tiles."""
        for size in range(0, 6):
            draw = set(iter_brush_offsets(size, "square"))
            border = set(iter_brush_border_offsets(size, "square"))
            assert draw.issubset(border)


# ============================================================================
# Circle Footprint Tests
# ============================================================================


class TestCircleFootprintDraw:
    """Tests for circle-shaped brush footprint (draw tiles)."""

    @pytest.mark.parametrize("size", [0, 1, 3, 5])
    def test_matches_cpp_legacy(self, size: int) -> None:
        """Verify Python output matches C++ legacy for various sizes."""
        expected = _cpp_legacy_draw_offsets(size, "circle")
        actual = list(iter_brush_offsets(size, "circle"))
        assert actual == expected

    def test_size_0_returns_single_tile(self) -> None:
        """Size 0 circle should return only (0, 0)."""
        offsets = list(iter_brush_offsets(0, "circle"))
        assert offsets == [(0, 0)]

    def test_size_1_returns_cross_pattern(self) -> None:
        """Size 1 circle should return 5 tiles (cross pattern)."""
        offsets = list(iter_brush_offsets(1, "circle"))
        # Distance from center must be < 1.005
        # (0,0)=0, (±1,0)=1, (0,±1)=1, (±1,±1)=√2≈1.41 > 1.005
        assert len(offsets) == 5
        assert (0, 0) in offsets
        assert (1, 0) in offsets
        assert (-1, 0) in offsets
        assert (0, 1) in offsets
        assert (0, -1) in offsets
        # Corners should NOT be included
        assert (1, 1) not in offsets
        assert (-1, -1) not in offsets

    def test_size_3_count(self) -> None:
        """Size 3 circle should return 29 tiles."""
        offsets = list(iter_brush_offsets(3, "circle"))
        assert len(offsets) == 29

    def test_size_5_count(self) -> None:
        """Size 5 circle should return 81 tiles."""
        offsets = list(iter_brush_offsets(5, "circle"))
        assert len(offsets) == 81


class TestCircleFootprintBorder:
    """Tests for circle-shaped brush border (autoborder tiles)."""

    @pytest.mark.parametrize("size", [0, 1, 3, 5])
    def test_matches_cpp_legacy(self, size: int) -> None:
        """Verify Python output matches C++ legacy for various sizes."""
        expected = _cpp_legacy_border_offsets(size, "circle")
        actual = list(iter_brush_border_offsets(size, "circle"))
        assert actual == expected

    def test_size_0_count(self) -> None:
        """Size 0 circle border should be 9 tiles (distance from 0 < 1.5)."""
        offsets = list(iter_brush_border_offsets(0, "circle"))
        assert len(offsets) == 9

    def test_size_1_count(self) -> None:
        """Size 1 circle border should return 21 tiles."""
        offsets = list(iter_brush_border_offsets(1, "circle"))
        assert len(offsets) == 21

    def test_size_3_count(self) -> None:
        """Size 3 circle border should return 60 tiles."""
        offsets = list(iter_brush_border_offsets(3, "circle"))
        assert len(offsets) == 60

    def test_size_5_count(self) -> None:
        """Size 5 circle border should return 100 tiles."""
        offsets = list(iter_brush_border_offsets(5, "circle"))
        assert len(offsets) == 100


# ============================================================================
# Edge Symmetry Verification
# ============================================================================


class TestSymmetry:
    """Verify footprints have proper symmetry around origin."""

    def _check_4way_symmetry(self, offsets: Sequence[tuple[int, int]]) -> None:
        """Check 4-way rotational symmetry: (x,y) ↔ (-x,y) ↔ (x,-y) ↔ (-x,-y)."""
        offset_set = set(offsets)
        for x, y in offsets:
            # All 4 quadrant reflections should exist
            assert (x, y) in offset_set
            assert (-x, y) in offset_set
            assert (x, -y) in offset_set
            assert (-x, -y) in offset_set

    def _check_8way_symmetry(self, offsets: Sequence[tuple[int, int]]) -> None:
        """Check 8-way symmetry (includes diagonal reflections)."""
        offset_set = set(offsets)
        for x, y in offsets:
            # 4-way rotational
            assert (x, y) in offset_set
            assert (-x, y) in offset_set
            assert (x, -y) in offset_set
            assert (-x, -y) in offset_set
            # Diagonal swap
            assert (y, x) in offset_set
            assert (-y, x) in offset_set
            assert (y, -x) in offset_set
            assert (-y, -x) in offset_set

    @pytest.mark.parametrize("size", [0, 1, 2, 3, 5])
    def test_square_draw_4way_symmetry(self, size: int) -> None:
        """Square draw tiles should have 4-way symmetry."""
        offsets = list(iter_brush_offsets(size, "square"))
        self._check_4way_symmetry(offsets)

    @pytest.mark.parametrize("size", [0, 1, 2, 3, 5])
    def test_square_border_4way_symmetry(self, size: int) -> None:
        """Square border tiles should have 4-way symmetry."""
        offsets = list(iter_brush_border_offsets(size, "square"))
        self._check_4way_symmetry(offsets)

    @pytest.mark.parametrize("size", [0, 1, 2, 3, 5])
    def test_circle_draw_8way_symmetry(self, size: int) -> None:
        """Circle draw tiles should have 8-way symmetry."""
        offsets = list(iter_brush_offsets(size, "circle"))
        self._check_8way_symmetry(offsets)

    @pytest.mark.parametrize("size", [0, 1, 2, 3, 5])
    def test_circle_border_8way_symmetry(self, size: int) -> None:
        """Circle border tiles should have 8-way symmetry."""
        offsets = list(iter_brush_border_offsets(size, "circle"))
        self._check_8way_symmetry(offsets)


# ============================================================================
# Input Handling Tests
# ============================================================================


class TestInputHandling:
    """Tests for edge cases in input handling."""

    def test_negative_size_treated_as_zero(self) -> None:
        """Negative sizes should be treated as size 0."""
        neg_offsets = list(iter_brush_offsets(-5, "square"))
        zero_offsets = list(iter_brush_offsets(0, "square"))
        assert neg_offsets == zero_offsets

    def test_shape_case_insensitive(self) -> None:
        """Shape parameter should be case insensitive."""
        lower = list(iter_brush_offsets(2, "circle"))
        upper = list(iter_brush_offsets(2, "CIRCLE"))
        mixed = list(iter_brush_offsets(2, "CiRcLe"))
        assert lower == upper == mixed

    def test_shape_whitespace_handling(self) -> None:
        """Shape parameter should handle leading/trailing whitespace."""
        clean = list(iter_brush_offsets(2, "square"))
        padded = list(iter_brush_offsets(2, "  square  "))
        assert clean == padded

    def test_default_shape_is_square(self) -> None:
        """Empty or None shape should default to square."""
        default = list(iter_brush_offsets(2, ""))
        square = list(iter_brush_offsets(2, "square"))
        assert default == square

    def test_unknown_shape_treated_as_square(self) -> None:
        """Unknown shape names should be treated as square."""
        unknown = list(iter_brush_offsets(2, "triangle"))
        square = list(iter_brush_offsets(2, "square"))
        assert unknown == square
