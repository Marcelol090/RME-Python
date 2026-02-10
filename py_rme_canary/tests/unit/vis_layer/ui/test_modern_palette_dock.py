from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QMainWindow, QSpinBox

from py_rme_canary.vis_layer.ui.docks.modern_palette_dock import ModernPaletteDock


@pytest.fixture
def app():
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


class _DummyBrushManager:
    def __init__(self) -> None:
        self._brushes = {
            100: SimpleNamespace(server_id=100, name="Stone Ground", brush_type="ground"),
            200: SimpleNamespace(server_id=200, name="Blue Carpet", brush_type="carpet"),
            201: SimpleNamespace(server_id=201, name="Dining Table", brush_type="table"),
            300: SimpleNamespace(server_id=300, name="Stone Wall", brush_type="wall"),
        }

    def get_brush(self, sid: int):
        return self._brushes.get(int(sid))

    def iter_doodad_brushes(self):
        return []


class _DummyEditor(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.brush_mgr = _DummyBrushManager()
        self.session = SimpleNamespace(
            game_map=SimpleNamespace(houses={}, zones={}, waypoints={}),
            recent_brushes=[100, 201],
        )
        self.brush_id_entry = QSpinBox(self)
        self.selected_brush = None
        self.brush_size_value = 0
        self.brush_shape_value = "square"
        self.brush_variation_value = 0
        self.doodad_thickness_enabled = False
        self.doodad_thickness_level = 0

    def set_brush_size(self, size: int) -> None:
        self.brush_size_value = int(size)

    def set_brush_shape(self, shape: str) -> None:
        self.brush_shape_value = str(shape)

    def _set_selected_brush_id(self, brush_id: int) -> None:
        self.selected_brush = int(brush_id)

    def _set_brush_variation(self, value: int) -> None:
        self.brush_variation_value = int(value)

    def _set_doodad_thickness_enabled(self, enabled: bool) -> None:
        self.doodad_thickness_enabled = bool(enabled)

    def _set_doodad_thickness_level(self, level: int) -> None:
        self.doodad_thickness_level = int(level)


def test_modern_palette_dock_exposes_legacy_bindings(app) -> None:
    editor = _DummyEditor()
    dock = ModernPaletteDock(editor, editor)

    assert dock.primary is dock
    assert dock.current_palette_name == "terrain"
    assert editor.brush_filter is dock.brush_filter
    assert editor.brush_list is dock.brush_list


def test_modern_palette_dock_select_palette_and_filter(app) -> None:
    editor = _DummyEditor()
    dock = ModernPaletteDock(editor, editor)

    dock.select_palette("item")
    assert dock.current_palette_name == "item"
    assert dock.brush_list.count() == 2

    dock.brush_filter.setText("table")
    assert dock.brush_list.count() == 1
    assert "Table" in dock.brush_list.item(0).text()


def test_modern_palette_dock_icon_size_and_create_additional(app) -> None:
    editor = _DummyEditor()
    dock = ModernPaletteDock(editor, editor)

    dock.set_icon_size(48)
    assert dock.brush_list.iconSize().width() == 48
    assert dock.create_additional() is dock


def test_modern_palette_dock_collection_and_variation_backend_binding(app) -> None:
    editor = _DummyEditor()
    dock = ModernPaletteDock(editor, editor)

    dock.select_palette("collection")
    assert dock.current_palette_name == "collection"
    assert dock.brush_list.count() >= 4

    dock.tool_options.var_slider.setValue(80)
    assert editor.doodad_thickness_enabled is True
    assert editor.doodad_thickness_level == 8

    dock.select_palette("terrain")
    dock.tool_options.var_slider.setValue(37)
    assert editor.brush_variation_value == 37
