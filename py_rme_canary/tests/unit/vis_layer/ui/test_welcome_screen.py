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

    class MockSignal:
        def connect(self, slot): pass
        def emit(self, *args): pass

    class QPushButton(QWidget):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.clicked = MockSignal()
        def setIcon(self, i): pass
        def setIconSize(self, s): pass

    class QListWidget(QWidget):
        class ScrollMode:
            ScrollPerPixel = 0
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.itemClicked = MockSignal()
            self.addItem = MagicMock()
            self.setItemWidget = MagicMock()
            self.clear = MagicMock()
        def setFrameShape(self, s): pass
        def setVerticalScrollMode(self, m): pass
        def count(self): return 0

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
    mock_qt.Qt.AlignmentFlag.AlignRight = 0
    mock_qt.Qt.AlignmentFlag.AlignVCenter = 0
    mock_qt.Qt.ItemDataRole.UserRole = 0
    mock_qt.Qt.CursorShape.PointingHandCursor = 0
    mock_qt.Qt.ItemFlag.NoItemFlags = 0

import pytest
from py_rme_canary.vis_layer.ui.dialogs.welcome_dialog import WelcomeDialog, RecentFileWidget


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
            "radius": {"xl": 20, "md": 10, "sm": 8, "round": 99},
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
    set_item_widget = dialog.recent_list.setItemWidget
    if hasattr(set_item_widget, "call_count"):
        assert set_item_widget.call_count == 2

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

@patch("os.path.exists")
@patch("os.path.getmtime")
@patch("time.time")
def test_recent_file_widget_time_ago(mock_time, mock_mtime, mock_exists, mock_theme_manager):
    mock_exists.return_value = True

    # Current time = 10000
    mock_time.return_value = 10000.0

    # Case 1: Just now (< 60s)
    mock_mtime.return_value = 9950.0 # 50s ago
    w = RecentFileWidget("/tmp/test")
    assert w._get_time_ago("/tmp/test") == "Just now"

    # Case 2: Minutes (< 1h)
    mock_mtime.return_value = 9000.0 # 1000s ago = 16 mins
    assert w._get_time_ago("/tmp/test") == "16m ago"

    # Case 3: Hours (< 24h)
    mock_mtime.return_value = 10000.0 - (3600 * 5) # 5 hours ago
    assert w._get_time_ago("/tmp/test") == "5h ago"

    # Case 4: Days (< 7d)
    mock_mtime.return_value = 10000.0 - (86400 * 3) # 3 days ago
    assert w._get_time_ago("/tmp/test") == "3d ago"

@patch("py_rme_canary.vis_layer.ui.dialogs.welcome_dialog.RecentFilesManager")
@patch("py_rme_canary.vis_layer.ui.dialogs.welcome_dialog.load_icon")
def test_welcome_dialog_clear(mock_load_icon, mock_rfm_cls, mock_theme_manager):
    # Setup RecentFilesManager mock
    mock_instance = MagicMock()
    mock_rfm_cls.instance.return_value = mock_instance

    try:
        from PyQt6.QtGui import QIcon
        mock_load_icon.return_value = QIcon()
    except Exception:
        pass

    dialog = WelcomeDialog(["/tmp/1"])

    # Trigger clear
    dialog._on_clear_recent()

    # Verify manager clear called
    mock_instance.clear.assert_called_once()

    # Verify list is empty
    assert len(dialog.recent_files) == 0

    # Check if empty list item added
    assert dialog.recent_list.addItem.called
