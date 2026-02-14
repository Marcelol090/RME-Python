"""Unit tests for widget components."""

from __future__ import annotations

import pytest

# Skip tests if PyQt6 not available
pytest.importorskip("PyQt6")


class TestStatusBarIndicators:
    """Tests for status bar indicator widgets."""

    @pytest.fixture
    def app(self):
        """Create QApplication for tests."""
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_position_indicator_creation(self, app):
        """Test creating position indicator."""
        from py_rme_canary.vis_layer.ui.widgets.status_bar import PositionIndicator

        indicator = PositionIndicator()
        assert indicator is not None

    def test_position_indicator_update(self, app):
        """Test updating position display."""
        from py_rme_canary.vis_layer.ui.widgets.status_bar import PositionIndicator

        indicator = PositionIndicator()
        indicator.set_position(100, 200, 7)

        assert "100" in indicator.text_label.text()
        assert "200" in indicator.text_label.text()

    def test_zoom_indicator(self, app):
        """Test zoom indicator."""
        from py_rme_canary.vis_layer.ui.widgets.status_bar import ZoomIndicator

        indicator = ZoomIndicator()
        indicator.set_zoom(1.5)

        assert "150%" in indicator.text_label.text()

    def test_selection_indicator_no_selection(self, app):
        """Test selection indicator with no selection."""
        from py_rme_canary.vis_layer.ui.widgets.status_bar import SelectionIndicator

        indicator = SelectionIndicator()
        indicator.set_selection(0)

        assert "No selection" in indicator.text_label.text()

    def test_selection_indicator_with_selection(self, app):
        """Test selection indicator with tiles selected."""
        from py_rme_canary.vis_layer.ui.widgets.status_bar import SelectionIndicator

        indicator = SelectionIndicator()
        indicator.set_selection(25, 5, 5)

        assert "25" in indicator.text_label.text()

    def test_brush_indicator(self, app):
        """Test brush indicator."""
        from py_rme_canary.vis_layer.ui.widgets.status_bar import BrushIndicator

        indicator = BrushIndicator()
        indicator.set_brush("Grass", 3)

        assert "Grass" in indicator.text_label.text()


class TestFloorIndicator:
    """Tests for floor indicator widget."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_floor_indicator_creation(self, app):
        """Test creating floor indicator."""
        from py_rme_canary.vis_layer.ui.widgets.minimap import FloorIndicator

        indicator = FloorIndicator()
        assert indicator.get_floor() == 7  # Ground level

    def test_floor_up(self, app):
        """Test floor up."""
        from py_rme_canary.vis_layer.ui.widgets.minimap import FloorIndicator

        indicator = FloorIndicator()
        indicator.set_floor(7)
        indicator._floor_up()

        assert indicator.get_floor() == 6

    def test_floor_down(self, app):
        """Test floor down."""
        from py_rme_canary.vis_layer.ui.widgets.minimap import FloorIndicator

        indicator = FloorIndicator()
        indicator.set_floor(7)
        indicator._floor_down()

        assert indicator.get_floor() == 8

    def test_floor_limits(self, app):
        """Test floor limits."""
        from py_rme_canary.vis_layer.ui.widgets.minimap import FloorIndicator

        indicator = FloorIndicator()

        # Can't go below 0
        indicator.set_floor(0)
        indicator._floor_up()
        assert indicator.get_floor() == 0

        # Can't go above 15
        indicator.set_floor(15)
        indicator._floor_down()
        assert indicator.get_floor() == 15


class TestLayerManager:
    """Tests for layer manager widget."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_layer_manager_creation(self, app):
        """Test creating layer manager."""
        from py_rme_canary.vis_layer.ui.widgets.layer_manager import LayerManager

        manager = LayerManager()
        assert manager is not None

    def test_layer_visibility(self, app):
        """Test layer visibility toggle."""
        from py_rme_canary.vis_layer.ui.widgets.layer_manager import LayerManager

        manager = LayerManager()

        # Toggle ground layer
        manager.set_layer_visible("ground", False)
        assert manager.get_layer_visibility("ground") is False

        manager.set_layer_visible("ground", True)
        assert manager.get_layer_visibility("ground") is True

    def test_layer_opacity(self, app):
        """Test layer opacity."""
        from py_rme_canary.vis_layer.ui.widgets.layer_manager import LayerManager

        manager = LayerManager()

        manager.set_layer_opacity("grid", 0.5)
        assert abs(manager.get_layer_opacity("grid") - 0.5) < 0.01


class TestBrushToolbar:
    """Tests for brush toolbar widget."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_brush_toolbar_creation(self, app):
        """Test creating brush toolbar."""
        from py_rme_canary.vis_layer.ui.widgets.brush_toolbar import BrushToolbar

        toolbar = BrushToolbar()
        assert toolbar is not None

    def test_brush_size_change(self, app):
        """Test changing brush size."""
        from PyQt6.QtTest import QSignalSpy

        from py_rme_canary.vis_layer.ui.widgets.brush_toolbar import BrushToolbar

        toolbar = BrushToolbar()
        QSignalSpy(toolbar.size_changed)

        toolbar.set_size(5)
        # Verify signal would be emitted on actual click

    def test_shape_toggle(self, app):
        """Test shape toggle."""
        from py_rme_canary.vis_layer.ui.widgets.brush_toolbar import BrushToolbar

        toolbar = BrushToolbar()

        toolbar.set_shape("circle")
        assert toolbar.btn_circle.isChecked()
        assert not toolbar.btn_square.isChecked()

        toolbar.set_shape("square")
        assert toolbar.btn_square.isChecked()
        assert not toolbar.btn_circle.isChecked()

    def test_brush_toolbar_uses_theme_tokens_in_stylesheet(self, app, monkeypatch):
        """Toolbar style should read color tokens from ThemeManager."""
        from types import SimpleNamespace

        from py_rme_canary.vis_layer.ui.widgets import brush_toolbar as brush_toolbar_module
        from py_rme_canary.vis_layer.ui.widgets.brush_toolbar import BrushToolbar

        fake_tokens = {
            "color": {
                "surface": {
                    "primary": "rgba(1, 2, 3, 0.8)",
                    "secondary": "rgba(4, 5, 6, 0.6)",
                },
                "text": {
                    "primary": "#FAFAFA",
                    "secondary": "#ABABAB",
                },
                "border": {
                    "default": "rgba(7, 8, 9, 0.5)",
                    "interactive": "rgba(10, 11, 12, 0.4)",
                },
                "state": {
                    "hover": "rgba(13, 14, 15, 0.3)",
                    "active": "rgba(16, 17, 18, 0.2)",
                },
            },
            "radius": {"md": 5, "lg": 9},
        }
        monkeypatch.setattr(
            brush_toolbar_module,
            "get_theme_manager",
            lambda: SimpleNamespace(tokens=fake_tokens),
        )

        toolbar = BrushToolbar()
        style = toolbar.styleSheet()
        assert "rgba(1, 2, 3, 0.8)" in style
        assert "rgba(4, 5, 6, 0.6)" in style
        assert "rgba(7, 8, 9, 0.5)" in style
        assert "rgba(10, 11, 12, 0.4)" in style


class TestUndoRedoPanel:
    """Tests for undo/redo panel."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    def test_panel_creation(self, app):
        """Test creating undo/redo panel."""
        from py_rme_canary.vis_layer.ui.widgets.undo_redo import UndoRedoPanel

        panel = UndoRedoPanel()
        assert panel is not None

    def test_add_entry(self, app):
        """Test adding history entry."""
        from py_rme_canary.vis_layer.ui.widgets.undo_redo import HistoryEntry, UndoRedoPanel

        panel = UndoRedoPanel()
        panel.clear_history()

        entry = HistoryEntry("Draw", "✏️", "5 tiles")
        panel.add_entry(entry)

        assert panel.history_list.count() == 1

    def test_undo_redo_buttons(self, app):
        """Test undo/redo button states."""
        from py_rme_canary.vis_layer.ui.widgets.undo_redo import HistoryEntry, UndoRedoPanel

        panel = UndoRedoPanel()
        panel.clear_history()

        # Initially disabled
        assert not panel.btn_undo.isEnabled()
        assert not panel.btn_redo.isEnabled()

        # Add entry
        panel.add_entry(HistoryEntry("Action 1", "✏️"))

        # Undo should be enabled, redo still disabled
        assert panel.btn_undo.isEnabled()
        assert not panel.btn_redo.isEnabled()
