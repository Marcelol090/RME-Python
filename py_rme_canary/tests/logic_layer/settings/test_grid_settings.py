"""Tests for grid settings."""
from __future__ import annotations

import pytest

from py_rme_canary.logic_layer.settings.grid_settings import (
    GRID_COLORS,
    GridColor,
    GridSettings,
    GridType,
)


def test_grid_color_creation() -> None:
    """Test creating grid color."""
    color = GridColor(255, 128, 64, 200)

    assert color.r == 255
    assert color.g == 128
    assert color.b == 64
    assert color.a == 200


def test_grid_color_validation() -> None:
    """Test color component validation."""
    with pytest.raises(ValueError, match="must be 0-255"):
        GridColor(256, 0, 0, 255)

    with pytest.raises(ValueError, match="must be 0-255"):
        GridColor(0, -1, 0, 255)


def test_grid_color_to_rgba_tuple() -> None:
    """Test conversion to RGBA tuple."""
    color = GridColor(255, 128, 64, 200)

    assert color.to_rgba_tuple() == (255, 128, 64, 200)


def test_grid_color_to_hex() -> None:
    """Test conversion to hex string."""
    color = GridColor(255, 0, 128, 255)

    assert color.to_hex() == "#ff0080"


def test_grid_color_with_alpha() -> None:
    """Test creating color with new alpha."""
    color = GridColor(255, 128, 64, 200)
    new_color = color.with_alpha(100)

    assert new_color.r == 255
    assert new_color.g == 128
    assert new_color.b == 64
    assert new_color.a == 100


def test_grid_color_from_hex() -> None:
    """Test creating color from hex string."""
    color = GridColor.from_hex("#FF8040", 200)

    assert color.r == 255
    assert color.g == 128
    assert color.b == 64
    assert color.a == 200


def test_grid_color_from_hex_without_hash() -> None:
    """Test hex parsing without # prefix."""
    color = GridColor.from_hex("FF8040", 200)

    assert color.r == 255
    assert color.g == 128
    assert color.b == 64


def test_grid_color_from_hex_invalid() -> None:
    """Test invalid hex string."""
    with pytest.raises(ValueError, match="must be 6 characters"):
        GridColor.from_hex("#FFF", 255)


def test_grid_settings_defaults() -> None:
    """Test default grid settings."""
    settings = GridSettings()

    assert settings.enabled is True
    assert settings.grid_type == GridType.SOLID
    assert settings.thickness == 1
    assert settings.show_coordinates is False


def test_grid_settings_with_enabled() -> None:
    """Test toggling grid enabled state."""
    settings = GridSettings()
    disabled = settings.with_enabled(False)

    assert disabled.enabled is False
    assert disabled.grid_type == settings.grid_type  # Other fields unchanged


def test_grid_settings_with_color() -> None:
    """Test changing grid color."""
    settings = GridSettings()
    new_color = GridColor(255, 0, 0, 255)
    red_settings = settings.with_color(new_color)

    assert red_settings.color == new_color
    assert red_settings.enabled == settings.enabled


def test_grid_settings_with_transparency() -> None:
    """Test changing transparency."""
    settings = GridSettings()
    transparent = settings.with_transparency(50)

    assert transparent.color.a == 50
    assert transparent.color.r == settings.color.r  # RGB unchanged


def test_grid_settings_with_type() -> None:
    """Test changing grid type."""
    settings = GridSettings()
    dotted = settings.with_type(GridType.DOTTED)

    assert dotted.grid_type == GridType.DOTTED


def test_grid_settings_with_thickness() -> None:
    """Test changing grid thickness."""
    settings = GridSettings()
    thick = settings.with_thickness(3)

    assert thick.thickness == 3


def test_grid_settings_thickness_validation() -> None:
    """Test grid thickness validation."""
    with pytest.raises(ValueError, match="must be 1-5"):
        GridSettings(thickness=0)

    with pytest.raises(ValueError, match="must be 1-5"):
        GridSettings(thickness=10)


def test_grid_settings_immutability() -> None:
    """Test that GridSettings is immutable."""
    settings = GridSettings()

    with pytest.raises(AttributeError):
        settings.enabled = False  # type: ignore[misc]


def test_grid_type_enum() -> None:
    """Test GridType enum values."""
    assert GridType.SOLID.value == "solid"
    assert GridType.DOTTED.value == "dotted"
    assert GridType.DASHED.value == "dashed"
    assert GridType.NONE.value == "none"


def test_predefined_colors() -> None:
    """Test predefined color schemes."""
    assert "default" in GRID_COLORS
    assert "white" in GRID_COLORS
    assert "black" in GRID_COLORS

    default_color = GRID_COLORS["default"]
    assert isinstance(default_color, GridColor)


def test_grid_color_immutability() -> None:
    """Test that GridColor is immutable."""
    color = GridColor(255, 0, 0, 255)

    with pytest.raises(AttributeError):
        color.r = 128  # type: ignore[misc]
