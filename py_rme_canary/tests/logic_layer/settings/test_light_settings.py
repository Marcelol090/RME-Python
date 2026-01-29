"""Tests for light settings."""
from __future__ import annotations

import pytest

from py_rme_canary.logic_layer.settings.light_settings import (
    LIGHT_PRESETS,
    LightColor,
    LightMode,
    LightSettings,
)


def test_light_color_creation() -> None:
    """Test creating light color."""
    color = LightColor(255, 200, 150)

    assert color.r == 255
    assert color.g == 200
    assert color.b == 150


def test_light_color_validation() -> None:
    """Test color component validation."""
    with pytest.raises(ValueError, match="must be 0-255"):
        LightColor(256, 0, 0)

    with pytest.raises(ValueError, match="must be 0-255"):
        LightColor(0, -1, 0)


def test_light_color_to_rgb_tuple() -> None:
    """Test conversion to RGB tuple."""
    color = LightColor(255, 128, 64)

    assert color.to_rgb_tuple() == (255, 128, 64)


def test_light_color_to_hex() -> None:
    """Test conversion to hex string."""
    color = LightColor(255, 0, 128)

    assert color.to_hex() == "#ff0080"


def test_light_color_from_hex() -> None:
    """Test creating color from hex string."""
    color = LightColor.from_hex("#FF8040")

    assert color.r == 255
    assert color.g == 128
    assert color.b == 64


def test_light_color_from_hex_without_hash() -> None:
    """Test hex parsing without # prefix."""
    color = LightColor.from_hex("FF8040")

    assert color.r == 255
    assert color.g == 128
    assert color.b == 64


def test_light_color_from_hex_invalid() -> None:
    """Test invalid hex string."""
    with pytest.raises(ValueError, match="must be 6 characters"):
        LightColor.from_hex("#FFF")


def test_light_settings_defaults() -> None:
    """Test default light settings."""
    settings = LightSettings()

    assert settings.enabled is True
    assert settings.mode == LightMode.SIMPLE
    assert settings.ambient_level == 255
    assert settings.show_light_sources is False
    assert settings.dynamic_updates is True


def test_light_settings_with_enabled() -> None:
    """Test toggling light enabled state."""
    settings = LightSettings()
    disabled = settings.with_enabled(False)

    assert disabled.enabled is False
    assert disabled.mode == settings.mode  # Other fields unchanged


def test_light_settings_with_mode() -> None:
    """Test changing light mode."""
    settings = LightSettings()
    full = settings.with_mode(LightMode.FULL)

    assert full.mode == LightMode.FULL
    assert full.enabled == settings.enabled


def test_light_settings_with_ambient_level() -> None:
    """Test changing ambient light level."""
    settings = LightSettings()
    dark = settings.with_ambient_level(50)

    assert dark.ambient_level == 50


def test_light_settings_ambient_level_validation() -> None:
    """Test ambient level validation."""
    with pytest.raises(ValueError, match="must be 0-255"):
        LightSettings(ambient_level=-1)

    with pytest.raises(ValueError, match="must be 0-255"):
        LightSettings(ambient_level=256)


def test_light_settings_with_ambient_color() -> None:
    """Test changing ambient color."""
    settings = LightSettings()
    warm_color = LightColor(255, 200, 150)
    warm = settings.with_ambient_color(warm_color)

    assert warm.ambient_color == warm_color


def test_light_settings_with_show_light_sources() -> None:
    """Test toggling light source visibility."""
    settings = LightSettings()
    show = settings.with_show_light_sources(True)

    assert show.show_light_sources is True


def test_light_settings_is_dark_mode() -> None:
    """Test dark mode detection."""
    bright = LightSettings(ambient_level=255)
    dark = LightSettings(ambient_level=50)
    medium = LightSettings(ambient_level=128)

    assert not bright.is_dark_mode()
    assert dark.is_dark_mode()
    assert not medium.is_dark_mode()  # Exactly 128 is not dark


def test_light_settings_get_brightness_percentage() -> None:
    """Test brightness percentage calculation."""
    full = LightSettings(ambient_level=255)
    half = LightSettings(ambient_level=128)
    dark = LightSettings(ambient_level=0)

    assert full.get_brightness_percentage() == 1.0
    assert abs(half.get_brightness_percentage() - 0.502) < 0.01  # ~0.502
    assert dark.get_brightness_percentage() == 0.0


def test_light_settings_immutability() -> None:
    """Test that LightSettings is immutable."""
    settings = LightSettings()

    with pytest.raises(AttributeError):
        settings.enabled = False  # type: ignore[misc]


def test_light_mode_enum() -> None:
    """Test LightMode enum values."""
    assert LightMode.FULL.value == "full"
    assert LightMode.SIMPLE.value == "simple"
    assert LightMode.AMBIENT_ONLY.value == "ambient_only"
    assert LightMode.OFF.value == "off"


def test_predefined_presets() -> None:
    """Test predefined light presets."""
    assert "daylight" in LIGHT_PRESETS
    assert "night" in LIGHT_PRESETS
    assert "cave" in LIGHT_PRESETS

    daylight = LIGHT_PRESETS["daylight"]
    assert daylight.ambient_level == 255
    assert daylight.mode == LightMode.SIMPLE

    night = LIGHT_PRESETS["night"]
    assert night.is_dark_mode()
    assert night.mode == LightMode.FULL


def test_preset_twilight() -> None:
    """Test twilight preset."""
    twilight = LIGHT_PRESETS["twilight"]

    assert twilight.ambient_level == 180
    assert twilight.ambient_color.r == 255  # Warm tint
    assert twilight.mode == LightMode.FULL


def test_preset_cave() -> None:
    """Test cave preset."""
    cave = LIGHT_PRESETS["cave"]

    assert cave.is_dark_mode()
    assert cave.show_light_sources is True  # Show torches etc
    assert cave.ambient_level == 30


def test_preset_editor_default() -> None:
    """Test editor default preset."""
    editor = LIGHT_PRESETS["editor_default"]

    assert editor.enabled is False  # No lights by default
    assert editor.mode == LightMode.OFF


def test_light_color_immutability() -> None:
    """Test that LightColor is immutable."""
    color = LightColor(255, 0, 0)

    with pytest.raises(AttributeError):
        color.r = 128  # type: ignore[misc]
