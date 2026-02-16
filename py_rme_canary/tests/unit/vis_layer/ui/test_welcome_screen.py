"""Tests for Modern Welcome Screen."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

# Mock PyQt6
try:
    import PyQt6
except ImportError:
    mock_qt = MagicMock()
    sys.modules["PyQt6"] = mock_qt
    sys.modules["PyQt6.QtWidgets"] = mock_qt
    sys.modules["PyQt6.QtCore"] = mock_qt
    sys.modules["PyQt6.QtGui"] = mock_qt

    # Define dummy base classes with mock caching
    class MockableWidget:
        def __init__(self, parent=None):
            self._mocks = {}
        def __getattr__(self, name):
            if name not in self._mocks:
                self._mocks[name] = MagicMock()
            return self._mocks[name]

    class QWidget(MockableWidget):
        def setStyleSheet(self, s): pass
        def setAttribute(self, a): pass
        def setWindowFlags(self, f): pass
        def setFixedSize(self, w, h): pass
        def setModal(self, m): pass
        def show(self): pass
        def close(self): pass
        def setCursor(self, c): pass
        def setGraphicsEffect(self, e): pass
        def setObjectName(self, n): pass

    class QDialog(QWidget):
        def exec(self): return 1
        def accept(self): pass
        def reject(self): pass

    class QFrame(QWidget):
        class Shape:
            NoFrame = 0
        def setFrameShape(self, s): pass

    class QLabel(QWidget):
        def setText(self, t): pass
        def setPixmap(self, p): pass
        def setAlignment(self, a): pass
        def setWordWrap(self, w): pass

    class QPushButton(QWidget):
        def setIcon(self, i): pass
        def setIconSize(self, s): pass

    class QListWidget(QWidget):
        class ScrollMode:
            ScrollPerPixel = 0
        def setFrameShape(self, s): pass
        def setVerticalScrollMode(self, m): pass

    class QListWidgetItem:
        def __init__(self, parent=None): pass
        def setData(self, r, d): pass
        def setFlags(self, f): pass
        def setTextAlignment(self, a): pass
        def setSizeHint(self, s): pass

    class QVBoxLayout(QWidget):
        def setContentsMargins(self, *a): pass
        def setSpacing(self, s): pass
        def addWidget(self, w, *args): pass
        def addLayout(self, l): pass
        def addStretch(self): pass
        def addSpacing(self, s): pass

    class QHBoxLayout(QVBoxLayout): pass

    class QGraphicsDropShadowEffect(QWidget):
        def setBlurRadius(self, r): pass
        def setColor(self, c): pass
        def setOffset(self, *a): pass

    mock_qt.QWidget = QWidget
    mock_qt.QDialog = QDialog
    mock_qt.QFrame = QFrame
    mock_qt.QLabel = QLabel
    mock_qt.QPushButton = QPushButton
    mock_qt.QListWidget = QListWidget
    mock_qt.QListWidgetItem = QListWidgetItem
    mock_qt.QVBoxLayout = QVBoxLayout
    mock_qt.QHBoxLayout = QHBoxLayout
    mock_qt.QGraphicsDropShadowEffect = QGraphicsDropShadowEffect

    mock_qt.Qt.WindowType.FramelessWindowHint = 0
    mock_qt.Qt.WindowType.Dialog = 0
    mock_qt.Qt.WidgetAttribute.WA_TranslucentBackground = 0
    mock_qt.Qt.AlignmentFlag.AlignLeft = 0
    mock_qt.Qt.AlignmentFlag.AlignCenter = 0
    mock_qt.Qt.ItemDataRole.UserRole = 0
    mock_qt.Qt.CursorShape.PointingHandCursor = 0
    mock_qt.Qt.ItemFlag.NoItemFlags = 0

import pytest
from py_rme_canary.vis_layer.ui.dialogs.welcome_dialog import WelcomeDialog


@pytest.fixture
def app():
    """Ensure QApplication exists when real PyQt6 is available."""
    try:
        from PyQt6.QtWidgets import QApplication
    except Exception:
        return None

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def mock_theme_manager():
    with patch("py_rme_canary.vis_layer.ui.dialogs.welcome_dialog.get_theme_manager") as mock:
        mock.return_value.tokens = {
            "color": {
                "surface": {"primary": "#000", "secondary": "#111", "elevated": "#222"},
                "text": {"primary": "#FFF", "secondary": "#AAA", "tertiary": "#888", "disabled": "#555"},
                "brand": {"primary": "#F00", "secondary": "#0F0", "active": "#00F"},
                "border": {"default": "#333", "strong": "#444"},
                "state": {"hover": "#444", "active": "#555", "error": "#F00"},
            },
            "radius": {"xl": 20, "md": 10, "round": 99},
        }
        mock.return_value.profile = {"logo": "test_logo", "component_style": "glass"}
        yield mock

@patch("py_rme_canary.vis_layer.ui.dialogs.welcome_dialog.load_icon")
@patch("py_rme_canary.vis_layer.ui.dialogs.welcome_dialog.icon_logo_axolotl")
def test_welcome_dialog_init(mock_logo_gen, mock_load_icon, mock_theme_manager, app):
    """Verify dialog initialization and population."""
    recent_files = ["/path/to/map1.otbm", "/path/to/map2.otbm"]
    try:
        from PyQt6.QtGui import QIcon

        mock_load_icon.return_value = QIcon()
        mock_logo_gen.return_value = QIcon()
    except Exception:
        pass

    dialog = WelcomeDialog(recent_files)

    # Check if list populated
    add_item = dialog.recent_list.addItem
    if hasattr(add_item, "call_count"):
        assert add_item.call_count == 2
    else:
        assert dialog.recent_list.count() == 2

    # Check if logo logic called
    mock_logo_gen.assert_called_once()

    # Check signals exist
    assert hasattr(dialog, "new_map_requested")
    assert hasattr(dialog, "open_map_requested")

@patch("py_rme_canary.vis_layer.ui.dialogs.welcome_dialog.load_icon")
def test_welcome_dialog_empty_recent(mock_load_icon, mock_theme_manager, app):
    """Verify empty state."""
    try:
        from PyQt6.QtGui import QIcon

        mock_load_icon.return_value = QIcon()
    except Exception:
        pass

    dialog = WelcomeDialog([])

    # Should add 1 item (fallback message)
    add_item = dialog.recent_list.addItem
    if hasattr(add_item, "call_count"):
        assert add_item.call_count == 1
    else:
        assert dialog.recent_list.count() == 1
