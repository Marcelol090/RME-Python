from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

try:
    from PyQt6.QtWidgets import QApplication, QWidget
    from PyQt6.QtGui import QColor, QIcon
    from py_rme_canary.vis_layer.ui.widgets.modern_progress_dialog import ModernProgressDialog, CircularProgressBar
except ImportError:
    QApplication = None
    QWidget = object
    QColor = None
    QIcon = None
    ModernProgressDialog = None
    CircularProgressBar = None

pytest.importorskip("PyQt6")

@pytest.fixture
def app():
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance

def test_circular_progress_bar_api(app):
    if CircularProgressBar is None:
        pytest.skip("PyQt6 missing")
    bar = CircularProgressBar()
    bar.setMaximum(200)
    bar.setValue(100)
    assert bar._maximum == 200
    assert bar._value == 100

    bar.setColors("#FF0000", "#00FF00", "#0000FF")
    assert bar._color_primary == QColor("#FF0000")
    assert bar._color_secondary == QColor("#00FF00")
    assert bar._text_color == QColor("#0000FF")

@patch("py_rme_canary.vis_layer.ui.widgets.modern_progress_dialog.get_theme_manager")
@patch("py_rme_canary.vis_layer.ui.widgets.modern_progress_dialog.load_icon")
def test_modern_progress_dialog_initialization(mock_load_icon, mock_get_theme_manager, app):
    if ModernProgressDialog is None:
        pytest.skip("PyQt6 missing")

    # Setup mocks
    mock_theme = MagicMock()
    mock_theme.tokens = {
        "color": {
            "surface": {"primary": "#000", "secondary": "#111", "tertiary": "#222"},
            "border": {"default": "#333", "strong": "#444"},
            "text": {"primary": "#FFF", "secondary": "#AAA"},
            "brand": {"primary": "#F00", "secondary": "#0F0"},
            "state": {"hover": "#555"},
        },
        "radius": {"xl": 20, "md": 10},
    }
    mock_theme.profile = {"logo": "test_logo", "app_name": "Test App"}
    mock_get_theme_manager.return_value = mock_theme

    mock_load_icon.return_value = QIcon()

    dialog = ModernProgressDialog("Test Title", "Initial Status", 0, 100)

    # Verify UI elements
    assert dialog.title_lbl.text() == "TEST TITLE"
    assert dialog.status_lbl.text() == "INITIAL STATUS"
    assert dialog.bar._value == 0
    assert dialog.bar._maximum == 100
    assert not dialog.wasCanceled()

    # Verify Theme usage
    mock_get_theme_manager.assert_called_once()
    mock_load_icon.assert_called_with("logo_test_logo")

def test_modern_progress_dialog_updates(app):
    if ModernProgressDialog is None:
        pytest.skip("PyQt6 missing")

    with patch("py_rme_canary.vis_layer.ui.widgets.modern_progress_dialog.get_theme_manager") as mock_tm:
        mock_tm.return_value.tokens = {
            "color": {
                "surface": {"primary": "#000", "secondary": "#111", "tertiary": "#222"},
                "border": {"default": "#333", "strong": "#444"},
                "text": {"primary": "#FFF", "secondary": "#AAA"},
                "brand": {"primary": "#F00", "secondary": "#0F0"},
                "state": {"hover": "#555"},
            },
            "radius": {"xl": 20, "md": 10},
        }
        mock_tm.return_value.profile = {}

        dialog = ModernProgressDialog()

        dialog.setLabelText("New Status")
        assert dialog.status_lbl.text() == "NEW STATUS"

        dialog.setValue(50)
        assert dialog.bar._value == 50

        dialog.setMaximum(200)
        assert dialog.bar._maximum == 200

def test_modern_progress_dialog_cancel(app):
    if ModernProgressDialog is None:
        pytest.skip("PyQt6 missing")

    with patch("py_rme_canary.vis_layer.ui.widgets.modern_progress_dialog.get_theme_manager"):
        dialog = ModernProgressDialog()
        dialog.show()

        assert not dialog.wasCanceled()
        dialog.cancel()
        assert dialog.wasCanceled()
        assert dialog.status_lbl.text() == "CANCELING..."
        assert not dialog.isVisible() # Should close on cancel
