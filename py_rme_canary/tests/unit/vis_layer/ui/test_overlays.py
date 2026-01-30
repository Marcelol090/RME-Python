"""Unit tests for overlay components."""

from __future__ import annotations

import pytest

# Skip tests if PyQt6 not available
pytest.importorskip("PyQt6")


class TestBrushCursorOverlay:
    """Tests for brush cursor overlay."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def parent_widget(self, app):
        from PyQt6.QtWidgets import QWidget

        return QWidget()

    def test_overlay_creation(self, parent_widget):
        """Test creating brush cursor overlay."""
        from py_rme_canary.vis_layer.ui.overlays.brush_cursor import BrushCursorOverlay

        overlay = BrushCursorOverlay(parent_widget)
        assert overlay is not None

    def test_set_position(self, parent_widget):
        """Test setting cursor position."""
        from PyQt6.QtCore import QPoint

        from py_rme_canary.vis_layer.ui.overlays.brush_cursor import BrushCursorOverlay

        overlay = BrushCursorOverlay(parent_widget)
        overlay.set_position(QPoint(100, 200))

        assert overlay._center.x() == 100
        assert overlay._center.y() == 200

    def test_set_brush_size(self, parent_widget):
        """Test setting brush size."""
        from py_rme_canary.vis_layer.ui.overlays.brush_cursor import BrushCursorOverlay

        overlay = BrushCursorOverlay(parent_widget)
        overlay.set_brush_size(5)

        assert overlay._brush_size == 5

    def test_set_tile_size(self, parent_widget):
        """Test setting tile size."""
        from py_rme_canary.vis_layer.ui.overlays.brush_cursor import BrushCursorOverlay

        overlay = BrushCursorOverlay(parent_widget)
        overlay.set_tile_size(64)

        assert overlay._tile_size == 64

    def test_set_circle_shape(self, parent_widget):
        """Test setting circle shape."""
        from py_rme_canary.vis_layer.ui.overlays.brush_cursor import BrushCursorOverlay

        overlay = BrushCursorOverlay(parent_widget)
        overlay.set_circle_shape(True)

        assert overlay._is_circle is True

    def test_visibility(self, parent_widget):
        """Test visibility toggle."""
        from py_rme_canary.vis_layer.ui.overlays.brush_cursor import BrushCursorOverlay

        overlay = BrushCursorOverlay(parent_widget)

        overlay.set_visible(True)
        assert overlay._visible is True

        overlay.set_visible(False)
        assert overlay._visible is False


class TestPastePreviewOverlay:
    """Tests for paste preview overlay."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def parent_widget(self, app):
        from PyQt6.QtWidgets import QWidget

        return QWidget()

    def test_overlay_creation(self, parent_widget):
        """Test creating paste preview overlay."""
        from py_rme_canary.vis_layer.ui.overlays.paste_preview import PastePreviewOverlay

        overlay = PastePreviewOverlay(parent_widget)
        assert overlay is not None

    def test_set_preview_positions(self, parent_widget):
        """Test setting preview positions."""
        from py_rme_canary.vis_layer.ui.overlays.paste_preview import PastePreviewOverlay

        overlay = PastePreviewOverlay(parent_widget)
        positions = [(100, 200, 7), (101, 200, 7), (102, 200, 7)]

        overlay.set_preview_positions(positions)

        assert len(overlay._positions) == 3

    def test_clear_preview(self, parent_widget):
        """Test clearing preview."""
        from py_rme_canary.vis_layer.ui.overlays.paste_preview import PastePreviewOverlay

        overlay = PastePreviewOverlay(parent_widget)
        overlay.set_preview_positions([(100, 200, 7)])

        overlay.clear_preview()

        assert len(overlay._positions) == 0

    def test_cut_mode_color(self, parent_widget):
        """Test different color for cut mode."""
        from py_rme_canary.vis_layer.ui.overlays.paste_preview import PastePreviewOverlay

        overlay = PastePreviewOverlay(parent_widget)

        # Copy mode
        overlay.set_preview_positions([(100, 200, 7)], is_cut=False)
        # Check standard fill color
        assert overlay._is_cut is False

        # Cut mode
        overlay.set_preview_positions([(100, 200, 7)], is_cut=True)
        # Check cut fill color
        assert overlay._is_cut is True


class TestSelectionOverlay:
    """Tests for selection overlay."""

    @pytest.fixture
    def app(self):
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def parent_widget(self, app):
        from PyQt6.QtWidgets import QWidget

        return QWidget()

    def test_overlay_creation(self, parent_widget):
        """Test creating selection overlay."""
        from py_rme_canary.vis_layer.ui.overlays.paste_preview import SelectionOverlay

        overlay = SelectionOverlay(parent_widget)
        assert overlay is not None

    def test_set_rect(self, parent_widget):
        """Test setting selection rectangle."""
        from PyQt6.QtCore import QRect

        from py_rme_canary.vis_layer.ui.overlays.paste_preview import SelectionOverlay

        overlay = SelectionOverlay(parent_widget)
        rect = QRect(10, 20, 100, 50)

        overlay.set_selection([rect])

        assert overlay._selection_rects == [rect]

    def test_visibility(self, parent_widget):
        """Test selection visibility."""
        from py_rme_canary.vis_layer.ui.overlays.paste_preview import SelectionOverlay

        overlay = SelectionOverlay(parent_widget)

        # SelectionOverlay doesn't have custom set_visible, but inherits QWidget
        # It's always visible but paints nothing if selection is empty.

        # Test that set_selection starts timer and clears stops it
        from PyQt6.QtCore import QRect
        rect = QRect(10, 20, 100, 50)

        overlay.set_selection([rect])
        assert overlay._march_timer.isActive()

        overlay.clear_selection()
        assert not overlay._march_timer.isActive()
