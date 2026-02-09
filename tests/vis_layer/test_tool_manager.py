"""Tests for Tool Manager and Canvas Interaction."""

import pytest
from unittest.mock import MagicMock, patch

from PyQt6.QtCore import Qt, QPoint, QPointF
from PyQt6.QtGui import QMouseEvent

from py_rme_canary.vis_layer.ui.canvas.tools.manager import ToolManager
from py_rme_canary.vis_layer.ui.canvas.tools.brush_tool import BrushTool
from py_rme_canary.vis_layer.ui.canvas.widget import MapCanvasWidget

class MockEditor:
    def __init__(self):
        self.session = MagicMock()
        self.viewport = MagicMock()
        self.viewport.z = 7
        self.viewport.origin_x = 0
        self.viewport.origin_y = 0
        self.viewport.tile_px = 32
        self.map = MagicMock()
        self.map.header.width = 100
        self.map.header.height = 100
        self.show_preview = False
        self.drawing_options_coordinator = MagicMock()

        # Flags
        self.paste_armed = False
        self.selection_mode = False
        self.fill_armed = False
        self.lasso_enabled = False

    def apply_ui_state_to_session(self):
        pass

    def _update_action_enabled_states(self):
        pass

    def update_status_from_mouse(self, x, y):
        pass

    def _client_id_for_server_id(self, sid):
        return sid

    def _sprite_pixmap_for_server_id(self, sid, tile_px):
        return None

@pytest.fixture
def mock_editor():
    return MockEditor()

@pytest.fixture
def canvas(qtbot, mock_editor):
    with patch('py_rme_canary.vis_layer.ui.canvas.widget.QElapsedTimer'), \
         patch('py_rme_canary.vis_layer.ui.canvas.widget.QTimer'):
        widget = MapCanvasWidget(None, mock_editor)
        qtbot.addWidget(widget)
        # Mock _tile_at to return predictable coordinates
        widget._tile_at = MagicMock(return_value=(10, 10))
        # Mock _paint_footprint_at to avoid side effects
        widget._paint_footprint_at = MagicMock()
        return widget

def test_tool_manager_initialization(canvas, mock_editor):
    manager = ToolManager(canvas, mock_editor)
    assert isinstance(manager.active_tool, BrushTool)
    assert manager.get_tool("brush") is not None
    assert manager.get_tool("selection") is not None
    assert manager.get_tool("pan") is not None

def test_tool_switching(canvas, mock_editor):
    manager = ToolManager(canvas, mock_editor)

    manager.set_tool("selection")
    assert manager._active_tool_name == "selection"
    assert manager.active_tool == manager.get_tool("selection")

    manager.set_tool("pan")
    assert manager._active_tool_name == "pan"
    assert manager.active_tool == manager.get_tool("pan")

def test_canvas_delegates_to_tool(canvas, mock_editor):
    # Setup
    tool_mock = MagicMock()
    tool_mock.mouse_press.return_value = True
    tool_mock.mouse_move.return_value = True
    tool_mock.mouse_release.return_value = True

    canvas.tool_manager._active_tool = tool_mock

    # Simulate Press
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(100, 100),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    canvas.mousePressEvent(event)
    tool_mock.mouse_press.assert_called_once()
    assert not canvas._mouse_down  # Should not set legacy flag if handled

    # Simulate Move
    event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(110, 110),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier
    )
    canvas.mouseMoveEvent(event)
    tool_mock.mouse_move.assert_called_once()
    canvas._paint_footprint_at.assert_not_called()

    # Simulate Release
    event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        QPointF(110, 110),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier
    )
    canvas.mouseReleaseEvent(event)
    tool_mock.mouse_release.assert_called_once()
    mock_editor.session.mouse_up.assert_not_called() # Because tool handled it
