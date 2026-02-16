from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

pytest.importorskip("PyQt6.QtWidgets")

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QApplication

from py_rme_canary.core.assets.asset_profile import detect_asset_profile
from py_rme_canary.core.assets.loader import load_assets_from_profile
from py_rme_canary.core.database.id_mapper import IdMapper
from py_rme_canary.core.database.items_otb import ItemsOTB
from py_rme_canary.core.database.items_xml import ItemsXML
from py_rme_canary.vis_layer.renderer.qpainter_backend import QPainterRenderBackend
from py_rme_canary.vis_layer.ui.main_window.dialogs import FindEntityDialog
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_assets import QtMapEditorAssetsMixin

SHADOWBORN_CLIENT = Path(
    "/mnt/c/Users/Marcelo Henrique/Desktop/PROJETOS TIBIA/shadowborn/15.11 Shadowborn/15.11 localhost"
)
ARCANA_CLIENT = Path(
    "/mnt/c/Users/Marcelo Henrique/Desktop/PROJETOS TIBIA/PROJETOS TIBIA/Arcana/clienterme"
)
REDUX_ITEMS_OTB = Path(
    "/mnt/c/Users/Marcelo Henrique/Desktop/projec_rme/remeres-map-editor-redux/data/1330/items.otb"
)
REDUX_ITEMS_XML = Path(
    "/mnt/c/Users/Marcelo Henrique/Desktop/projec_rme/remeres-map-editor-redux/data/1330/items.xml"
)
RME_LINUX_ITEMS_XML = Path(
    "/mnt/c/Users/Marcelo Henrique/Desktop/projec_rme/Remeres-map-editor-linux-4.0.0/data/items/items.xml"
)


@dataclass(slots=True)
class _FixedMapper:
    source_server_id: int
    client_id: int

    def get_client_id(self, server_id: int) -> int | None:
        if int(server_id) == int(self.source_server_id):
            return int(self.client_id)
        return None


def _require_dir(path: Path) -> Path:
    if not path.is_dir():
        pytest.skip(f"Real client directory not available: {path}")
    return path


def _require_file(path: Path) -> Path:
    if not path.is_file():
        pytest.skip(f"Real definition file not available: {path}")
    return path


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


def test_real_shadowborn_modern_profile_loads_appearances_and_sprite() -> None:
    base = _require_dir(SHADOWBORN_CLIENT)
    profile = detect_asset_profile(base)
    assert profile.kind == "modern"
    assert profile.appearances_path is not None
    assert profile.appearances_path.exists()

    loaded = load_assets_from_profile(profile)
    assert loaded.appearance_assets is not None
    assert len(loaded.sprite_assets.sheets) > 0

    object_to_sprite = dict(loaded.appearance_assets.object_sprites)
    assert object_to_sprite
    _, sprite_id = next(iter(object_to_sprite.items()))
    width, height, bgra = loaded.sprite_assets.get_sprite_rgba(int(sprite_id))
    assert width > 0
    assert height > 0
    assert len(bgra) == int(width) * int(height) * 4


def test_real_arcana_legacy_profile_renders_sprite_in_grid_backend(app) -> None:
    base = _require_dir(ARCANA_CLIENT)
    profile = detect_asset_profile(base, prefer_kind="legacy")
    assert profile.kind == "legacy"
    loaded = load_assets_from_profile(profile)
    assert loaded.sprite_assets is not None
    assert int(getattr(loaded.sprite_assets, "sprite_count", 0)) > 0

    server_id = 50001
    mapper = _FixedMapper(source_server_id=server_id, client_id=1)

    def sprite_lookup(server_id_value: int, tile_size: int) -> QPixmap | None:
        client_id = mapper.get_client_id(int(server_id_value))
        if client_id is None:
            return None
        width, height, bgra = loaded.sprite_assets.get_sprite_rgba(int(client_id))
        image = QImage(bgra, int(width), int(height), int(width) * 4, QImage.Format.Format_ARGB32).copy()
        pixmap = QPixmap.fromImage(image)
        if pixmap.isNull():
            return None
        if int(tile_size) > 0 and (pixmap.width() != int(tile_size) or pixmap.height() != int(tile_size)):
            pixmap = pixmap.scaled(
                int(tile_size),
                int(tile_size),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.FastTransformation,
            )
        return pixmap

    frame = QImage(32, 32, QImage.Format.Format_ARGB32)
    frame.fill(0)
    painter = QPainter(frame)
    try:
        backend = QPainterRenderBackend(
            painter,
            target_rect=QRect(0, 0, 32, 32),
            sprite_lookup=sprite_lookup,
        )
        backend.draw_tile_sprite(0, 0, 32, server_id)
    finally:
        painter.end()

    # At least one pixel should be non-transparent after drawing.
    non_transparent_found = False
    for y in range(32):
        for x in range(32):
            if frame.pixelColor(x, y).alpha() > 0:
                non_transparent_found = True
                break
        if non_transparent_found:
            break
    assert non_transparent_found


def test_real_items_otb_items_xml_and_select_menu_contract(app) -> None:
    otb_path = _require_file(REDUX_ITEMS_OTB)
    xml_path = _require_file(REDUX_ITEMS_XML)
    xml_only_path = _require_file(RME_LINUX_ITEMS_XML)

    otb = ItemsOTB.load(otb_path)
    xml = ItemsXML.load(xml_path, strict_mapping=False)
    primary_mapper = IdMapper.from_items_otb(otb)
    xml_mapper = IdMapper.from_items_xml(xml)
    merged_mapper, merged_count = QtMapEditorAssetsMixin._merge_id_mappers(
        primary=primary_mapper,
        secondary=xml_mapper,
    )
    assert merged_mapper is not None
    assert int(merged_count) >= 0
    assert primary_mapper.server_to_client
    assert primary_mapper.client_to_server
    assert xml.items_by_server_id
    assert isinstance(xml_mapper.server_to_client, dict)

    xml_only = ItemsXML.load(xml_only_path, strict_mapping=False)
    xml_only_mapper = IdMapper.from_items_xml(xml_only)
    assert xml_only.items_by_server_id
    assert isinstance(xml_only_mapper.server_to_client, dict)

    dialog = FindEntityDialog()
    try:
        dialog.set_mode("item")
        assert dialog._item_mode_combo.count() >= 2
        dialog._item_mode_combo.setCurrentIndex(1)  # Client ID
        dialog._item_id_spin.setValue(100)
        result = dialog.result_value()
        assert result.mode == "item"
        assert result.query_mode == "client_id"
        assert result.query_id == 100
    finally:
        dialog.close()
