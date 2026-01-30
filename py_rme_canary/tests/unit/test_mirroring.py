from __future__ import annotations

from py_rme_canary.logic_layer.mirroring import mirrored_position, union_with_mirrored


def test_mirrored_position_x_axis() -> None:
    assert mirrored_position(5, 3, axis="x", axis_value=4) == (3, 3)


def test_mirrored_position_y_axis() -> None:
    assert mirrored_position(5, 3, axis="y", axis_value=2) == (5, 1)


def test_mirrored_position_same_returns_none() -> None:
    assert mirrored_position(4, 3, axis="x", axis_value=4) is None


def test_mirrored_position_bounds() -> None:
    assert mirrored_position(0, 0, axis="x", axis_value=5, width=5, height=5) is None


def test_union_with_mirrored_stable_dedupe() -> None:
    positions = [(1, 1, 7), (1, 1, 7), (2, 1, 7)]
    result = union_with_mirrored(positions, axis="x", axis_value=1, width=10, height=10)
    assert result == [(1, 1, 7), (2, 1, 7), (0, 1, 7)]


def test_union_with_mirrored_skips_invalid_z() -> None:
    positions = [(1, 1, 16), (2, 2, 7)]
    result = union_with_mirrored(positions, axis="y", axis_value=5, width=10, height=10)
    assert result == [(2, 2, 7), (2, 8, 7)]
