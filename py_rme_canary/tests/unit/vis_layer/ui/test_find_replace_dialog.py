from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

try:
    from PyQt6.QtWidgets import QApplication, QWidget, QDialog
    from py_rme_canary.vis_layer.ui.dialogs.find_replace_dialog import ItemFindReplaceDialog
except ImportError:
    QApplication = None
    QWidget = object
    QDialog = object
    ItemFindReplaceDialog = None

pytest.importorskip("PyQt6")

@pytest.fixture
def app():
    instance = QApplication.instance()
    if instance is None:
        # Use offscreen platform for headless environment
        import sys
        if "-platform" not in sys.argv:
            sys.argv.append("-platform")
            sys.argv.append("offscreen")
        instance = QApplication(sys.argv)
    return instance

@patch("py_rme_canary.vis_layer.ui.dialogs.find_replace_dialog.get_theme_manager")
def test_find_replace_dialog_initialization(mock_get_theme_manager, app):
    if ItemFindReplaceDialog is None:
        pytest.skip("PyQt6 missing")

    # Setup mocks
    mock_theme = MagicMock()
    mock_theme.tokens = {
        "color": {
            "surface": {"primary": "#000", "secondary": "#111", "tertiary": "#222"},
            "border": {"default": "#333", "strong": "#444"},
            "text": {"primary": "#FFF", "secondary": "#AAA", "tertiary": "#BBB"},
            "brand": {"primary": "#F00", "secondary": "#0F0"},
            "state": {"hover": "#555"},
        },
        "radius": {"xl": 20, "lg": 15, "md": 10, "sm": 5},
    }
    mock_get_theme_manager.return_value = mock_theme

    # Mock GameMap
    mock_map = MagicMock()

    dialog = ItemFindReplaceDialog(game_map=mock_map)

    # Verify UI elements
    assert dialog.windowTitle() == "Find & Replace Items"
    assert dialog.isModal()

    # Check if widgets exist
    assert dialog.find_id is not None
    assert dialog.find_name is not None
    assert dialog.replace_id is not None
    assert dialog.delete_mode is not None

    # Check initial state
    assert dialog.find_id.value() == 0
    assert not dialog.delete_mode.isChecked()
    assert dialog.scope_all.isChecked()

    # Verify Theme usage
    mock_get_theme_manager.assert_called()

def test_delete_mode_toggle(app):
    if ItemFindReplaceDialog is None:
        pytest.skip("PyQt6 missing")

    with patch("py_rme_canary.vis_layer.ui.dialogs.find_replace_dialog.get_theme_manager") as mock_tm:
        mock_tm.return_value.tokens = {
            "color": {
                "surface": {"primary": "#000", "secondary": "#111", "tertiary": "#222"},
                "border": {"default": "#333", "strong": "#444"},
                "text": {"primary": "#FFF", "secondary": "#AAA", "tertiary": "#BBB"},
                "brand": {"primary": "#F00", "secondary": "#0F0"},
                "state": {"hover": "#555"},
            },
            "radius": {"xl": 20, "lg": 15, "md": 10, "sm": 5},
        }

        dialog = ItemFindReplaceDialog(game_map=MagicMock())

        # Initial state: replace_id enabled
        assert dialog.replace_id.isEnabled()

        # Enable delete mode
        dialog.delete_mode.setChecked(True)
        assert not dialog.replace_id.isEnabled()

        # Disable delete mode
        dialog.delete_mode.setChecked(False)
        assert dialog.replace_id.isEnabled()
