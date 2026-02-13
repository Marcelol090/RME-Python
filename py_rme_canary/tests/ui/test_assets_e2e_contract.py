from __future__ import annotations

import json
import struct
from pathlib import Path

import pytest

pytest.importorskip("PyQt6.QtWidgets")

from PyQt6.QtCore import QEvent, QPointF, QRect, Qt
from PyQt6.QtGui import QColor, QImage, QMouseEvent, QPainter
from PyQt6.QtWidgets import QApplication

from py_rme_canary.core.assets.asset_profile import detect_asset_profile
from py_rme_canary.tests.ui._editor_test_utils import stabilize_editor_for_headless_tests
from py_rme_canary.vis_layer.renderer.qpainter_backend import QPainterRenderBackend
from py_rme_canary.vis_layer.ui.main_window.dialogs import FindEntityDialog
from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


def _varint(value: int) -> bytes:
    out = bytearray()
    current = int(value)
    while True:
        chunk = current & 0x7F
        current >>= 7
        if current:
            out.append(chunk | 0x80)
        else:
            out.append(chunk)
            return bytes(out)


def _key(field_number: int, wire_type: int) -> bytes:
    return _varint((int(field_number) << 3) | int(wire_type))


def _minimal_appearances_payload(appearance_id: int, sprite_id: int) -> bytes:
    sprite_info = _key(5, 0) + _varint(int(sprite_id))
    frame_group = _key(3, 2) + _varint(len(sprite_info)) + sprite_info
    appearance = _key(1, 0) + _varint(int(appearance_id)) + _key(2, 2) + _varint(len(frame_group)) + frame_group
    return _key(1, 2) + _varint(len(appearance)) + appearance


def _write_minimal_legacy_assets(root: Path) -> tuple[Path, Path]:
    dat_path = root / "Tibia.dat"
    spr_path = root / "Tibia.spr"
    dat_path.write_bytes(struct.pack("<IHHHH", 0, 1, 0, 0, 0))

    # Minimal sprite file with one sprite. Pixel (0,0) is red, rest transparent.
    sig = struct.pack("<I", 0x01020304)
    count = struct.pack("<H", 1)
    offset = struct.pack("<I", 10)
    sprite_data = struct.pack("<HH", 0, 1) + bytes([255, 0, 0]) + struct.pack("<HH", 1023, 0)
    payload = bytes([0, 0, 0]) + struct.pack("<H", len(sprite_data)) + sprite_data
    spr_path.write_bytes(sig + count + offset + payload)
    return dat_path, spr_path


class _Mapper:
    def __init__(self, mapping: dict[int, int]) -> None:
        self._mapping = dict(mapping)

    def get_client_id(self, server_id: int) -> int | None:
        return self._mapping.get(int(server_id))


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


@pytest.fixture
def editor(app):
    window = QtMapEditor()
    stabilize_editor_for_headless_tests(window)
    try:
        yield window
    finally:
        window.close()
        window.deleteLater()


def test_modern_assets_load_appearances_index(editor, tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "dummy_sprites.dat").write_bytes(b"")
    (assets_dir / "appearances.dat").write_bytes(_minimal_appearances_payload(appearance_id=391, sprite_id=1))
    (assets_dir / "catalog-content.json").write_text(
        json.dumps(
            [
                {
                    "type": "sprite",
                    "firstspriteid": 1,
                    "lastspriteid": 1,
                    "spritetype": 0,
                    "file": "dummy_sprites.dat",
                },
                {"type": "appearances", "file": "appearances.dat"},
            ]
        ),
        encoding="utf-8",
    )

    profile = detect_asset_profile(assets_dir)
    loaded = editor._apply_asset_profile(profile)

    assert loaded is not None
    assert editor.appearance_assets is not None
    assert editor.appearance_assets.get_sprite_id(391, kind="object") == 1


def test_legacy_dat_spr_load_resolves_sprite_pixmap(editor, tmp_path: Path) -> None:
    _write_minimal_legacy_assets(tmp_path)
    profile = detect_asset_profile(tmp_path, prefer_kind="legacy")
    loaded = editor._apply_asset_profile(profile)

    assert loaded is not None
    editor.id_mapper = _Mapper({391: 1})
    sprite = editor._sprite_pixmap_for_server_id(391, tile_px=32)
    assert sprite is not None
    assert sprite.isNull() is False

    # Cache contract: repeated lookup should return the cached pixmap object.
    cached = editor._sprite_pixmap_for_server_id(391, tile_px=32)
    assert cached is sprite


def test_canvas_click_paints_tile_and_sprite_lookup_renders(editor, tmp_path: Path) -> None:
    _write_minimal_legacy_assets(tmp_path)
    profile = detect_asset_profile(tmp_path, prefer_kind="legacy")
    loaded = editor._apply_asset_profile(profile)
    assert loaded is not None

    editor.id_mapper = _Mapper({391: 1})
    editor.selection_mode = False
    editor.fill_armed = False
    editor.paste_armed = False
    editor._set_brush_size(1)
    editor.session.set_selected_brush(391)

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
    assert any(int(item.id) == 391 for item in (tile.items or []))

    frame = QImage(32, 32, QImage.Format.Format_ARGB32)
    frame.fill(QColor(0, 0, 0, 255))
    painter = QPainter(frame)
    try:
        backend = QPainterRenderBackend(
            painter,
            target_rect=QRect(0, 0, 32, 32),
            sprite_lookup=lambda sid, size: editor._sprite_pixmap_for_server_id(int(sid), tile_px=int(size)),
        )
        backend.draw_tile_sprite(0, 0, 32, 391)
    finally:
        painter.end()

    top_left = frame.pixelColor(0, 0)
    assert top_left.red() >= 200
    assert top_left.alpha() > 0


def test_find_entity_item_select_menu_updates_query_mode(app) -> None:
    dialog = FindEntityDialog()

    dialog.set_mode("item")
    dialog._item_id_spin.setValue(321)
    dialog._item_mode_combo.setCurrentIndex(1)  # Client ID
    result = dialog.result_value()

    assert result.mode == "item"
    assert result.query_mode == "client_id"
    assert result.query_id == 321
    dialog.close()
