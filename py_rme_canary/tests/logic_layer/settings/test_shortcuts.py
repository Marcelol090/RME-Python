"""Tests for shortcuts configuration."""
from __future__ import annotations

from pathlib import Path

import pytest

from py_rme_canary.logic_layer.settings.shortcuts import (
    DEFAULT_SHORTCUTS,
    ShortcutAction,
    ShortcutSettings,
)


def test_default_settings() -> None:
    """Test default settings creation."""
    settings = ShortcutSettings.default()

    assert settings.enabled is True
    assert settings.allow_custom is True
    assert len(settings.shortcuts) > 0


def test_get_shortcut() -> None:
    """Test getting shortcuts."""
    settings = ShortcutSettings.default()

    assert settings.get_shortcut(ShortcutAction.UNDO) == "Ctrl+Z"
    assert settings.get_shortcut(ShortcutAction.SAVE_MAP) == "Ctrl+S"


def test_with_shortcut() -> None:
    """Test updating a shortcut."""
    settings = ShortcutSettings.default()

    new_settings = settings.with_shortcut(ShortcutAction.CUSTOM_1, "Ctrl+K")

    # Original unchanged
    assert settings.get_shortcut(ShortcutAction.CUSTOM_1) == ""
    # New settings updated
    assert new_settings.get_shortcut(ShortcutAction.CUSTOM_1) == "Ctrl+K"


def test_with_enabled() -> None:
    """Test enabling/disabling shortcuts."""
    settings = ShortcutSettings.default()

    disabled = settings.with_enabled(False)
    assert disabled.enabled is False

    re_enabled = disabled.with_enabled(True)
    assert re_enabled.enabled is True


def test_with_custom_allowed() -> None:
    """Test allowing/disallowing custom shortcuts."""
    settings = ShortcutSettings.default()

    no_custom = settings.with_custom_allowed(False)
    assert no_custom.allow_custom is False

    # Should raise when trying to set custom shortcut
    with pytest.raises(ValueError, match="Custom shortcuts are disabled"):
        no_custom.with_shortcut(ShortcutAction.CUSTOM_1, "Ctrl+K")


def test_reset_to_defaults() -> None:
    """Test resetting all shortcuts to defaults."""
    settings = ShortcutSettings.default()

    # Modify some shortcuts
    modified = settings.with_shortcut(ShortcutAction.UNDO, "Ctrl+U")
    modified = modified.with_shortcut(ShortcutAction.CUSTOM_1, "Ctrl+K")

    # Reset
    reset = modified.reset_to_defaults()

    assert reset.get_shortcut(ShortcutAction.UNDO) == "Ctrl+Z"
    assert reset.get_shortcut(ShortcutAction.CUSTOM_1) == ""


def test_reset_action() -> None:
    """Test resetting a single action."""
    settings = ShortcutSettings.default()

    # Modify UNDO
    modified = settings.with_shortcut(ShortcutAction.UNDO, "Ctrl+U")
    assert modified.get_shortcut(ShortcutAction.UNDO) == "Ctrl+U"

    # Reset only UNDO
    reset = modified.reset_action(ShortcutAction.UNDO)
    assert reset.get_shortcut(ShortcutAction.UNDO) == "Ctrl+Z"


def test_get_all_shortcuts() -> None:
    """Test getting all shortcuts."""
    settings = ShortcutSettings.default()

    all_shortcuts = settings.get_all_shortcuts()

    assert ShortcutAction.UNDO in all_shortcuts
    assert all_shortcuts[ShortcutAction.UNDO] == "Ctrl+Z"


def test_get_custom_shortcuts() -> None:
    """Test getting only custom shortcuts."""
    settings = ShortcutSettings.default()

    # No custom shortcuts initially
    assert len(settings.get_custom_shortcuts()) == 0

    # Add some custom shortcuts
    settings = settings.with_shortcut(ShortcutAction.CUSTOM_1, "Ctrl+K")
    settings = settings.with_shortcut(ShortcutAction.CUSTOM_2, "Ctrl+L")

    custom = settings.get_custom_shortcuts()
    assert len(custom) == 2
    assert ShortcutAction.CUSTOM_1 in custom
    assert ShortcutAction.CUSTOM_2 in custom


def test_invalid_shortcut_format() -> None:
    """Test validation of invalid shortcut formats."""
    settings = ShortcutSettings.default()

    # Invalid modifier
    with pytest.raises(ValueError, match="Invalid shortcut format"):
        settings.with_shortcut(ShortcutAction.CUSTOM_1, "Invalid+K")


def test_shortcut_conflict() -> None:
    """Test detecting shortcut conflicts."""
    settings = ShortcutSettings.default()

    # Try to bind CUSTOM_1 to an already used shortcut
    with pytest.raises(ValueError, match="already bound"):
        settings.with_shortcut(ShortcutAction.CUSTOM_1, "Ctrl+Z")


def test_unbind_shortcut() -> None:
    """Test unbinding a shortcut (setting to empty)."""
    settings = ShortcutSettings.default()

    # Unbind UNDO
    unbound = settings.with_shortcut(ShortcutAction.UNDO, "")
    assert unbound.get_shortcut(ShortcutAction.UNDO) == ""


def test_export_import(tmp_path: Path) -> None:
    """Test exporting and importing shortcuts."""
    config_file = tmp_path / "shortcuts.json"

    # Create custom settings
    settings = ShortcutSettings.default()
    settings = settings.with_shortcut(ShortcutAction.CUSTOM_1, "Ctrl+K")
    settings = settings.with_enabled(False)

    # Export
    settings.export_to_file(config_file)
    assert config_file.exists()

    # Import
    loaded = ShortcutSettings.import_from_file(config_file)

    assert loaded.enabled is False
    assert loaded.get_shortcut(ShortcutAction.CUSTOM_1) == "Ctrl+K"
    assert loaded.get_shortcut(ShortcutAction.UNDO) == "Ctrl+Z"


def test_immutability() -> None:
    """Test that settings are truly immutable."""
    settings = ShortcutSettings.default()

    # Modify shortcuts dict should not affect original
    shortcuts = settings.get_all_shortcuts()
    shortcuts[ShortcutAction.UNDO] = "Invalid"

    assert settings.get_shortcut(ShortcutAction.UNDO) == "Ctrl+Z"


def test_position_hotkeys() -> None:
    """Test position save/goto hotkeys."""
    settings = ShortcutSettings.default()

    assert settings.get_shortcut(ShortcutAction.SAVE_POSITION_1) == "Ctrl+Shift+1"
    assert settings.get_shortcut(ShortcutAction.GOTO_POSITION_1) == "Ctrl+1"
    assert settings.get_shortcut(ShortcutAction.SAVE_POSITION_5) == "Ctrl+Shift+5"


def test_tool_shortcuts() -> None:
    """Test tool shortcuts."""
    settings = ShortcutSettings.default()

    assert settings.get_shortcut(ShortcutAction.SELECT_TOOL) == "S"
    assert settings.get_shortcut(ShortcutAction.DRAW_TOOL) == "D"
    assert settings.get_shortcut(ShortcutAction.ERASE_TOOL) == "E"


def test_view_shortcuts() -> None:
    """Test view shortcuts."""
    settings = ShortcutSettings.default()

    assert settings.get_shortcut(ShortcutAction.TOGGLE_GRID) == "G"
    assert settings.get_shortcut(ShortcutAction.TOGGLE_PREVIEW) == "F5"
    assert settings.get_shortcut(ShortcutAction.ZOOM_IN) == "Ctrl++"


def test_default_shortcuts_constant() -> None:
    """Test DEFAULT_SHORTCUTS constant is complete."""
    # Should have entries for all actions
    assert ShortcutAction.UNDO in DEFAULT_SHORTCUTS
    assert ShortcutAction.CUSTOM_1 in DEFAULT_SHORTCUTS
    assert ShortcutAction.SAVE_POSITION_1 in DEFAULT_SHORTCUTS


def test_custom_shortcuts_count() -> None:
    """Test that there are exactly 10 custom shortcuts."""
    custom_actions = [action for action in ShortcutAction if action.name.startswith("CUSTOM_")]

    assert len(custom_actions) == 10


def test_position_hotkeys_count() -> None:
    """Test that there are 5 save and 5 goto position hotkeys."""
    save_positions = [action for action in ShortcutAction if action.name.startswith("SAVE_POSITION_")]
    goto_positions = [action for action in ShortcutAction if action.name.startswith("GOTO_POSITION_")]

    assert len(save_positions) == 5
    assert len(goto_positions) == 5


def test_chained_modifications() -> None:
    """Test chaining multiple modifications."""
    settings = (
        ShortcutSettings.default()
        .with_shortcut(ShortcutAction.CUSTOM_1, "Ctrl+K")
        .with_shortcut(ShortcutAction.CUSTOM_2, "Ctrl+L")
        .with_enabled(False)
        .with_custom_allowed(True)
    )

    assert settings.get_shortcut(ShortcutAction.CUSTOM_1) == "Ctrl+K"
    assert settings.get_shortcut(ShortcutAction.CUSTOM_2) == "Ctrl+L"
    assert settings.enabled is False
    assert settings.allow_custom is True


def test_complex_shortcuts() -> None:
    """Test complex multi-modifier shortcuts."""
    settings = ShortcutSettings.default()

    # Triple modifier
    modified = settings.with_shortcut(
        ShortcutAction.CUSTOM_1,
        "Ctrl+Shift+Alt+K",
    )
    assert modified.get_shortcut(ShortcutAction.CUSTOM_1) == "Ctrl+Shift+Alt+K"
