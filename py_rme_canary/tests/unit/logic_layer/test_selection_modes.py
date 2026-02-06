"""Test suite for selection depth modes.

Tests COMPENSATE, CURRENT, LOWER, VISIBLE modes.
"""

from py_rme_canary.logic_layer.session.selection_modes import (
    SelectionDepthMode,
    apply_compensation_offset,
    get_floors_for_selection,
)


def test_selection_mode_current_single_floor() -> None:
    """Test CURRENT mode selects only one floor."""
    result = get_floors_for_selection(
        start_z=7,
        end_z=10,
        mode=SelectionDepthMode.CURRENT,
    )
    assert result == [7]


def test_selection_mode_lower_multiple_floors() -> None:
    """Test LOWER mode selects start floor + all below."""
    result = get_floors_for_selection(
        start_z=7,
        end_z=10,
        mode=SelectionDepthMode.LOWER,
    )
    assert result == [7, 8, 9, 10]


def test_selection_mode_lower_single_floor() -> None:
    """Test LOWER mode with same start and end."""
    result = get_floors_for_selection(
        start_z=7,
        end_z=7,
        mode=SelectionDepthMode.LOWER,
    )
    assert result == [7]


def test_selection_mode_visible_filters_floors() -> None:
    """Test VISIBLE mode only includes visible floors."""
    result = get_floors_for_selection(
        start_z=5,
        end_z=10,
        mode=SelectionDepthMode.VISIBLE,
        visible_floors=[5, 7, 9],
    )
    assert result == [5, 7, 9]


def test_selection_mode_visible_empty_when_none_visible() -> None:
    """Test VISIBLE mode returns empty when no floors visible."""
    result = get_floors_for_selection(
        start_z=7,
        end_z=10,
        mode=SelectionDepthMode.VISIBLE,
        visible_floors=[1, 2, 3],  # None in range
    )
    assert result == []


def test_selection_mode_visible_defaults_to_start_floor() -> None:
    """Test VISIBLE mode defaults to start floor when visible_floors=None."""
    result = get_floors_for_selection(
        start_z=7,
        end_z=10,
        mode=SelectionDepthMode.VISIBLE,
        visible_floors=None,
    )
    assert result == [7]


def test_selection_mode_compensate_same_as_lower() -> None:
    """Test COMPENSATE mode returns same floors as LOWER (base behavior)."""
    result = get_floors_for_selection(
        start_z=7,
        end_z=10,
        mode=SelectionDepthMode.COMPENSATE,
    )
    assert result == [7, 8, 9, 10]


def test_compensation_offset_at_ground_level() -> None:
    """Test that compensation is not applied at ground level (z=7)."""
    x, y = apply_compensation_offset(x=100, y=100, z=7, base_z=7)
    assert x == 100
    assert y == 100


def test_compensation_offset_above_ground() -> None:
    """Test that compensation is not applied above ground (z<7)."""
    x, y = apply_compensation_offset(x=100, y=100, z=5, base_z=5)
    assert x == 100
    assert y == 100


def test_compensation_offset_below_ground() -> None:
    """Test compensation applied below ground level."""
    # At z=9 (2 floors below ground), offset by 2
    x, y = apply_compensation_offset(x=100, y=100, z=9, base_z=7)
    assert x == 102
    assert y == 102


def test_compensation_offset_deep_underground() -> None:
    """Test compensation for deep underground levels."""
    # At z=12 (5 floors below ground z=7), offset by 5
    x, y = apply_compensation_offset(x=100, y=100, z=12, base_z=7)
    assert x == 105
    assert y == 105


def test_compensation_offset_with_different_base() -> None:
    """Test compensation with different base floor."""
    # Base at z=8, current at z=10, offset by 2
    x, y = apply_compensation_offset(x=50, y=60, z=10, base_z=8)
    assert x == 52
    assert y == 62


def test_compensation_offset_no_change_when_base_above_ground() -> None:
    """Test no compensation when base floor is above ground."""
    x, y = apply_compensation_offset(x=100, y=100, z=5, base_z=3)
    assert x == 100
    assert y == 100
