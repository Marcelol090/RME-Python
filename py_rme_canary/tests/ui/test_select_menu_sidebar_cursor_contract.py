from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

import pytest

pytest.importorskip("PyQt6.QtWidgets")

from PyQt6.QtCore import QEvent, QPoint, QPointF, QRect, Qt
from PyQt6.QtGui import QImage, QMouseEvent, QPainter
from PyQt6.QtWidgets import QApplication

from py_rme_canary.core.assets.asset_profile import detect_asset_profile
from py_rme_canary.tests.ui._editor_test_utils import show_editor_window, stabilize_editor_for_headless_tests
from py_rme_canary.vis_layer.renderer.qpainter_backend import QPainterRenderBackend
from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


@dataclass(slots=True)
class _FixedMapper:
    source_server_id: int
    client_id: int

    def get_client_id(self, server_id: int) -> int | None:
        if int(server_id) == int(self.source_server_id):
            return int(self.client_id)
        return None


def _write_minimal_legacy_assets_full_red(root: Path) -> tuple[Path, Path]:
    dat_path = root / "Tibia.dat"
    spr_path = root / "Tibia.spr"
    dat_path.write_bytes(struct.pack("<IHHHH", 0, 1, 0, 0, 0))

    # Single 32x32 sprite: fully opaque red (legacy SPR RLE format).
    sprite_data = struct.pack("<HH", 0, 1024) + (bytes([255, 0, 0]) * 1024)
    payload = bytes([0, 0, 0]) + struct.pack("<H", len(sprite_data)) + sprite_data
    sig = struct.pack("<I", 0x01020304)
    count = struct.pack("<H", 1)
    offset = struct.pack("<I", 10)
    spr_path.write_bytes(sig + count + offset + payload)
    return dat_path, spr_path


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


@pytest.fixture
def editor(app, qtbot):
    window = QtMapEditor()
    stabilize_editor_for_headless_tests(window)
    qtbot.addWidget(window)
    show_editor_window(qtbot, window)
    try:
        yield window
    finally:
        window.close()
        window.deleteLater()


def test_selection_menu_tools_dispatch_to_expected_handlers(editor, monkeypatch, qtbot):
    import py_rme_canary.vis_layer.ui.main_window.find_item as find_item

    menu_actions = [action.text() for action in editor.menu_selection.actions() if action.text()]
    assert any(text.startswith("Replace Items on Selection") for text in menu_actions)
    assert "Find Item on Selection" in menu_actions
    assert any(text.startswith("Remove Item on Selection") for text in menu_actions)

    called: dict[str, object] = {
        "replace": 0,
        "remove": 0,
        "borderize": 0,
        "randomize_selection_only": None,
        "find_dialog": [],
        "find_everything": [],
        "find_unique": [],
        "find_action": [],
        "find_container": [],
        "find_writeable": [],
    }

    def _mark_replace() -> None:
        called["replace"] = int(called["replace"]) + 1

    def _mark_remove() -> None:
        called["remove"] = int(called["remove"]) + 1

    def _mark_borderize() -> None:
        called["borderize"] = int(called["borderize"]) + 1

    editor_cls = type(editor)
    monkeypatch.setattr(editor_cls, "_replace_items_on_selection", lambda self: _mark_replace())
    monkeypatch.setattr(editor_cls, "_remove_item_on_selection", lambda self: _mark_remove())
    monkeypatch.setattr(editor_cls, "_borderize_selection", lambda self: _mark_borderize())
    monkeypatch.setattr(
        editor_cls,
        "_randomize",
        lambda self, *, selection_only=False: called.__setitem__("randomize_selection_only", bool(selection_only)),
    )

    monkeypatch.setattr(
        find_item,
        "open_find_dialog",
        lambda _editor, mode, selection_only=False: called["find_dialog"].append((str(mode), bool(selection_only))),
    )
    monkeypatch.setattr(
        find_item,
        "open_find_everything",
        lambda _editor, selection_only=False: called["find_everything"].append(bool(selection_only)),
    )
    monkeypatch.setattr(
        find_item,
        "open_find_unique",
        lambda _editor, selection_only=False: called["find_unique"].append(bool(selection_only)),
    )
    monkeypatch.setattr(
        find_item,
        "open_find_action",
        lambda _editor, selection_only=False: called["find_action"].append(bool(selection_only)),
    )
    monkeypatch.setattr(
        find_item,
        "open_find_container",
        lambda _editor, selection_only=False: called["find_container"].append(bool(selection_only)),
    )
    monkeypatch.setattr(
        find_item,
        "open_find_writeable",
        lambda _editor, selection_only=False: called["find_writeable"].append(bool(selection_only)),
    )

    editor.act_replace_items_on_selection.trigger()
    editor.act_find_item_selection.trigger()
    editor.act_remove_item_on_selection.trigger()
    editor.act_find_everything_selection.trigger()
    editor.act_find_unique_selection.trigger()
    editor.act_find_action_selection.trigger()
    editor.act_find_container_selection.trigger()
    editor.act_find_writeable_selection.trigger()
    editor.act_borderize_selection.trigger()
    editor.act_randomize_selection.trigger()
    qtbot.wait(10)

    assert int(called["replace"]) == 1
    assert int(called["remove"]) == 1
    assert int(called["borderize"]) == 1
    assert called["randomize_selection_only"] is True
    assert ("item", True) in called["find_dialog"]
    assert called["find_everything"] == [True]
    assert called["find_unique"] == [True]
    assert called["find_action"] == [True]
    assert called["find_container"] == [True]
    assert called["find_writeable"] == [True]

    editor.act_selection_depth_compensate.trigger()
    qtbot.wait(5)
    assert str(editor.session.get_selection_depth_mode()) == "compensate"
    editor.act_selection_depth_current.trigger()
    qtbot.wait(5)
    assert str(editor.session.get_selection_depth_mode()) == "current"
    editor.act_selection_depth_lower.trigger()
    qtbot.wait(5)
    assert str(editor.session.get_selection_depth_mode()) == "lower"
    editor.act_selection_depth_visible.trigger()
    qtbot.wait(5)
    assert str(editor.session.get_selection_depth_mode()) == "visible"


def test_sidebar_palette_selects_brush_and_syncs_backend(editor, qtbot):
    palette_actions = (
        ("raw", editor.act_palette_raw),
        ("terrain", editor.act_palette_terrain),
        ("item", editor.act_palette_item),
        ("doodad", editor.act_palette_doodad),
        ("collection", editor.act_palette_collection),
    )

    list_widget = editor.palettes.brush_list
    target_item = None
    target_brush_id = None

    for expected_key, action in palette_actions:
        action.trigger()
        qtbot.wait(20)
        assert editor.palettes.current_palette_name == expected_key
        if list_widget.count() <= 0:
            continue
        for idx in range(list_widget.count()):
            item = list_widget.item(idx)
            value = item.data(Qt.ItemDataRole.UserRole)
            if value is None:
                continue
            brush_id = int(value)
            if brush_id <= 0:
                continue
            target_item = item
            target_brush_id = brush_id
            break
        if target_item is not None:
            break

    assert target_item is not None, "No selectable brush entry found in sidebar palettes"
    assert target_brush_id is not None
    list_widget.itemClicked.emit(target_item)
    qtbot.wait(10)

    assert int(editor.brush_id_entry.value()) == int(target_brush_id)
    assert int(editor.session._gestures.active_brush_id) == int(target_brush_id)

    # Sidebar filter must impact visible list entries (without breaking selection model).
    before_count = list_widget.count()
    editor.palettes.filter_edit.setText("zzzz__no_match__")
    qtbot.wait(10)
    assert list_widget.count() <= before_count
    editor.palettes.filter_edit.clear()
    qtbot.wait(10)
    assert list_widget.count() > 0


def test_cursor_preview_uses_selected_asset_sprite_and_canvas_draw_matches(editor, tmp_path: Path):
    _write_minimal_legacy_assets_full_red(tmp_path)
    profile = detect_asset_profile(tmp_path, prefer_kind="legacy")
    loaded = editor._apply_asset_profile(profile)
    assert loaded is not None

    selected_server_id = 391
    editor.id_mapper = _FixedMapper(source_server_id=selected_server_id, client_id=1)
    editor._set_selected_brush_id(int(selected_server_id))
    editor.show_preview = True
    editor.selection_mode = False
    editor.fill_armed = False
    editor.paste_armed = False
    editor._set_brush_size(1)
    editor.canvas._sync_animation_timer()

    hover = QPoint(int(editor.viewport.tile_px // 2), int(editor.viewport.tile_px // 2))
    editor.canvas._update_brush_preview(hover)

    overlay = editor.canvas._brush_preview_overlay
    preview_px = getattr(overlay, "_preview_pixmap", None)
    assert preview_px is not None
    assert preview_px.isNull() is False

    preview_img = preview_px.toImage()
    found_red = False
    for y in range(preview_img.height()):
        for x in range(preview_img.width()):
            c = preview_img.pixelColor(x, y)
            if c.red() >= 200 and c.green() <= 40 and c.blue() <= 40 and c.alpha() > 0:
                found_red = True
                break
        if found_red:
            break
    assert found_red

    click_x = int(editor.viewport.tile_px // 2)
    click_y = int(editor.viewport.tile_px // 2)
    tx, ty = editor.canvas._tile_at(click_x, click_y)
    z = int(editor.viewport.z)

    press = QMouseEvent(
        QEvent.Type.MouseButtonPress,
        QPointF(float(click_x), float(click_y)),
        QPointF(float(click_x), float(click_y)),
        QPointF(float(click_x), float(click_y)),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    release = QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        QPointF(float(click_x), float(click_y)),
        QPointF(float(click_x), float(click_y)),
        QPointF(float(click_x), float(click_y)),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    editor.canvas.mousePressEvent(press)
    editor.canvas.mouseReleaseEvent(release)

    tile = editor.map.get_tile(int(tx), int(ty), int(z))
    assert tile is not None
    assert any(int(item.id) == int(selected_server_id) for item in (tile.items or []))

    frame = QImage(32, 32, QImage.Format.Format_ARGB32)
    frame.fill(0)
    painter = QPainter(frame)
    try:
        backend = QPainterRenderBackend(
            painter,
            target_rect=QRect(0, 0, 32, 32),
            sprite_lookup=lambda sid, size: editor._sprite_pixmap_for_server_id(int(sid), tile_px=int(size)),
        )
        backend.draw_tile_sprite(0, 0, 32, int(selected_server_id))
    finally:
        painter.end()

    rendered_red = False
    for y in range(frame.height()):
        for x in range(frame.width()):
            c = frame.pixelColor(x, y)
            if c.red() >= 200 and c.green() <= 40 and c.blue() <= 40 and c.alpha() > 0:
                rendered_red = True
                break
        if rendered_red:
            break
    assert rendered_red
