"""Tests for drag shadow overlay."""
from __future__ import annotations

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QWidget


@pytest.fixture
def parent_widget(qtbot: object) -> QWidget:
    """Create a parent widget for overlay testing."""
    widget = QWidget()
    widget.resize(800, 600)
    return widget


def test_drag_shadow_initialization(qtbot: object, parent_widget: QWidget) -> None:
    """Test DragShadowOverlay can be instantiated."""
    from py_rme_canary.vis_layer.ui.overlays.drag_shadow import DragShadowOverlay

    overlay = DragShadowOverlay(parent_widget)

    assert not overlay.is_dragging()
    assert not overlay.isVisible()


def test_start_drag(qtbot: object, parent_widget: QWidget) -> None:
    """Test starting drag operation."""
    from py_rme_canary.vis_layer.ui.overlays.drag_shadow import DragShadowOverlay

    overlay = DragShadowOverlay(parent_widget)
    positions = [(10, 10, 7), (11, 10, 7), (10, 11, 7)]

    overlay.start_drag(positions)

    assert overlay.is_dragging()
    # Widget visibility depends on parent, check drag state instead


def test_update_drag_offset(qtbot: object, parent_widget: QWidget) -> None:
    """Test updating drag offset."""
    from py_rme_canary.vis_layer.ui.overlays.drag_shadow import DragShadowOverlay

    overlay = DragShadowOverlay(parent_widget)
    positions = [(10, 10, 7)]

    overlay.start_drag(positions)
    overlay.update_drag_offset(5, 3)

    # Should trigger repaint without error
    assert overlay.is_dragging()


def test_end_drag(qtbot: object, parent_widget: QWidget) -> None:
    """Test ending drag operation."""
    from py_rme_canary.vis_layer.ui.overlays.drag_shadow import DragShadowOverlay

    overlay = DragShadowOverlay(parent_widget)
    positions = [(10, 10, 7)]

    overlay.start_drag(positions)
    overlay.update_drag_offset(2, 2)
    overlay.end_drag()

    assert not overlay.is_dragging()
    assert not overlay.isVisible()


def test_set_origin_and_tile_size(qtbot: object, parent_widget: QWidget) -> None:
    """Test setting rendering parameters."""
    from py_rme_canary.vis_layer.ui.overlays.drag_shadow import DragShadowOverlay

    overlay = DragShadowOverlay(parent_widget)

    overlay.set_origin(QPoint(100, 100))
    overlay.set_tile_size(64)

    # Should not crash
    assert not overlay.is_dragging()


def test_paint_without_drag(qtbot: object, parent_widget: QWidget) -> None:
    """Test painting when not dragging (should be safe)."""
    from py_rme_canary.vis_layer.ui.overlays.drag_shadow import DragShadowOverlay

    overlay = DragShadowOverlay(parent_widget)

    # Should not crash
    overlay.update()


def test_paint_with_drag(qtbot: object, parent_widget: QWidget) -> None:
    """Test painting during drag."""
    from py_rme_canary.vis_layer.ui.overlays.drag_shadow import DragShadowOverlay

    overlay = DragShadowOverlay(parent_widget)
    overlay.show()

    positions = [(10, 10, 7), (11, 10, 7)]
    overlay.start_drag(positions)
    overlay.set_origin(QPoint(100, 100))
    overlay.set_tile_size(32)
    overlay.update_drag_offset(3, 3)

    # Force paint event
    overlay.update()

    # Should complete without crashes
    assert overlay.is_dragging()


def test_update_offset_without_drag_is_safe(qtbot: object, parent_widget: QWidget) -> None:
    """Test that updating offset without starting drag is safe."""
    from py_rme_canary.vis_layer.ui.overlays.drag_shadow import DragShadowOverlay

    overlay = DragShadowOverlay(parent_widget)

    # Should not crash
    overlay.update_drag_offset(5, 5)

    assert not overlay.is_dragging()


def test_multiple_drag_cycles(qtbot: object, parent_widget: QWidget) -> None:
    """Test multiple drag start/end cycles."""
    from py_rme_canary.vis_layer.ui.overlays.drag_shadow import DragShadowOverlay

    overlay = DragShadowOverlay(parent_widget)

    # First drag
    overlay.start_drag([(10, 10, 7)])
    overlay.update_drag_offset(2, 2)
    overlay.end_drag()

    # Second drag
    overlay.start_drag([(20, 20, 7)])
    overlay.update_drag_offset(5, 5)

    assert overlay.is_dragging()

    overlay.end_drag()
    assert not overlay.is_dragging()
