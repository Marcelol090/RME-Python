"""Tests for Layer Manager integration."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

# Mock PyQt6
try:
    import PyQt6  # noqa: F401
    mock_qt = MagicMock(name="pyqt6_runtime")
except ImportError:
    mock_qt = MagicMock()
    sys.modules["PyQt6"] = mock_qt
    sys.modules["PyQt6.QtWidgets"] = mock_qt
    sys.modules["PyQt6.QtCore"] = mock_qt
    sys.modules["PyQt6.QtGui"] = mock_qt

    # Define dummy base classes with mock caching
    class MockableWidget:
        def __init__(self, *args, **kwargs):
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
        def hide(self): pass
        def close(self): pass
        def setCursor(self, c): pass
        def setGraphicsEffect(self, e): pass
        def setObjectName(self, n): pass
        def update(self): pass

    class QDockWidget(QWidget):
        def __init__(self, title, parent=None): super().__init__(parent)
        def setWidget(self, w): pass
        def setAllowedAreas(self, a): pass

    class QFrame(QWidget):
        class Shape:
            NoFrame = 0
            HLine = 1
        def setFrameShape(self, s): pass
        def setFixedHeight(self, h): pass

    class QLabel(QWidget):
        def setText(self, t): pass
        def setPixmap(self, p): pass
        def setAlignment(self, a): pass
        def setWordWrap(self, w): pass
        def setToolTip(self, t): pass

    class QPushButton(QWidget):
        def setIcon(self, i): pass
        def setIconSize(self, s): pass

    class QScrollArea(QWidget):
        def setWidgetResizable(self, b): pass
        def setWidget(self, w): pass

    class QSpinBox(QWidget):
        def setRange(self, mn, mx): pass
        def setValue(self, v): pass
        def setPrefix(self, p): pass

    class QVBoxLayout(QWidget):
        def setContentsMargins(self, *a): pass
        def setSpacing(self, s): pass
        def addWidget(self, w, *args): pass
        def addLayout(self, l): pass
        def addStretch(self): pass
        def addSpacing(self, s): pass
        def setAlignment(self, a): pass

    class QHBoxLayout(QVBoxLayout): pass

    class QCheckBox(QWidget):
        def setChecked(self, b): pass
        def isChecked(self): return True

    class QSlider(QWidget):
        def setRange(self, mn, mx): pass
        def setValue(self, v): pass
        def value(self): return 100
        def setFixedWidth(self, w): pass

    mock_qt.QWidget = QWidget
    mock_qt.QDockWidget = QDockWidget
    mock_qt.QFrame = QFrame
    mock_qt.QLabel = QLabel
    mock_qt.QPushButton = QPushButton
    mock_qt.QScrollArea = QScrollArea
    mock_qt.QSpinBox = QSpinBox
    mock_qt.QVBoxLayout = QVBoxLayout
    mock_qt.QHBoxLayout = QHBoxLayout
    mock_qt.QCheckBox = QCheckBox
    mock_qt.QSlider = QSlider

    mock_qt.Qt.AlignmentFlag.AlignLeft = 0
    mock_qt.Qt.AlignmentFlag.AlignCenter = 0
    mock_qt.Qt.AlignmentFlag.AlignRight = 0
    mock_qt.Qt.PenStyle.NoPen = 0
    mock_qt.Qt.Orientation.Horizontal = 0
    mock_qt.Qt.DockWidgetArea.LeftDockWidgetArea = 1
    mock_qt.Qt.DockWidgetArea.RightDockWidgetArea = 2
    mock_qt.Qt.CheckState.Checked = 2

import pytest
from py_rme_canary.vis_layer.ui.docks.layer_dock import ModernLayerDock

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
def mock_qt_fixture():
    """Just ensuring mocks are in place."""
    return mock_qt

def test_layer_dock_visibility_updates(mock_qt_fixture, app):
    """Verify that toggling layers updates editor options."""
    editor = MagicMock()
    editor.drawing_options = MagicMock()
    editor.canvas = MagicMock()

    dock = ModernLayerDock(editor)

    # Simulate toggling grid
    dock._on_visibility_changed("grid", False)

    assert editor.drawing_options.show_grid is False
    editor.canvas.update.assert_called()

def test_layer_dock_opacity_updates(mock_qt_fixture, app):
    """Verify opacity change triggers update."""
    editor = MagicMock()
    editor.canvas = MagicMock()

    dock = ModernLayerDock(editor)

    dock._on_opacity_changed("grid", 0.5)
    editor.canvas.update.assert_called()
