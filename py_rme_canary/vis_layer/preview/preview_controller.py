from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtWidgets import QMessageBox

from py_rme_canary.core.assets.legacy_dat_spr import LegacySpriteArchive
from py_rme_canary.logic_layer.sprite_system import LegacyDatError, LegacyItemSpriteInfo, load_legacy_item_sprites
from py_rme_canary.vis_layer.preview.preview_renderer import PreviewItem, PreviewSnapshot, PreviewViewport, TileSnapshot
from py_rme_canary.vis_layer.preview.preview_thread import PreviewThread

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class PreviewController(QObject):
    def __init__(self, editor: QtMapEditor) -> None:
        super().__init__(editor)
        self._editor = editor
        self._timer = QTimer(self)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._sync)
        self._thread: PreviewThread | None = None
        self._legacy_items: dict[int, LegacyItemSpriteInfo] | None = None
        self._items_xml = None

    def start(self) -> None:
        if self._thread is not None:
            return
        if self._editor.sprite_assets is None:
            QMessageBox.warning(self._editor, "In-Game Preview", "Load client assets before opening preview.")
            return

        self._items_xml = self._editor.session._ensure_items_xml_loaded()
        self._legacy_items = self._load_legacy_items()

        initial_size = self._initial_window_size()
        self._thread = PreviewThread(
            sprite_provider=self._editor.sprite_assets,
            appearance_index=self._editor.appearance_assets,
            legacy_items=self._legacy_items or {},
            items_xml=self._items_xml,
            initial_size=initial_size,
        )
        self._thread.start()
        self._timer.start()
        self._sync()

    def stop(self) -> None:
        if self._thread is None:
            return
        self._timer.stop()
        self._thread.stop()
        self._thread.join(timeout=1.5)
        self._thread = None

    def _initial_window_size(self) -> tuple[int, int]:
        tiles_wide, tiles_high = self._tiles_from_editor()
        return (max(1, tiles_wide * 32), max(1, tiles_high * 32))

    def _tiles_from_editor(self) -> tuple[int, int]:
        canvas = self._editor.canvas
        width_px = max(1, int(canvas.width()))
        height_px = max(1, int(canvas.height()))
        tile_px = max(1, int(self._editor.viewport.tile_px))
        tiles_wide = max(1, width_px // tile_px) + 1
        tiles_high = max(1, height_px // tile_px) + 1
        return tiles_wide, tiles_high

    def _sync(self) -> None:
        if self._thread is None:
            return
        snapshot = self._build_snapshot()
        self._thread.submit_snapshot(snapshot)

    def _build_snapshot(self) -> PreviewSnapshot:
        editor = self._editor
        tiles_wide, tiles_high = self._tiles_from_editor()
        viewport = PreviewViewport(
            origin_x=int(editor.viewport.origin_x),
            origin_y=int(editor.viewport.origin_y),
            z=int(editor.viewport.z),
            tile_px=32,
            tiles_wide=int(tiles_wide),
            tiles_high=int(tiles_high),
        )

        tiles: list[TileSnapshot] = []
        for y in range(viewport.origin_y, viewport.origin_y + viewport.tiles_high):
            for x in range(viewport.origin_x, viewport.origin_x + viewport.tiles_wide):
                tile = editor.map.get_tile(x, y, viewport.z)
                if tile is None:
                    continue
                ground = self._snapshot_item(tile.ground)
                items = tuple(self._snapshot_item(it) for it in tile.items if it is not None)
                tiles.append(
                    TileSnapshot(
                        x=int(x),
                        y=int(y),
                        z=int(viewport.z),
                        ground=ground,
                        items=items,
                    )
                )

        time_ms = int(editor.animation_time_ms() if hasattr(editor, "animation_time_ms") else 0)
        return PreviewSnapshot(viewport=viewport, tiles=tuple(tiles), time_ms=time_ms)

    def _snapshot_item(self, item) -> PreviewItem | None:
        if item is None:
            return None
        server_id = int(item.id)
        client_id = item.client_id
        if client_id is None and self._editor.id_mapper is not None:
            client_id = self._editor.id_mapper.get_client_id(server_id)
        if client_id is None:
            client_id = server_id
        count = item.count if item.count is not None else item.subtype

        stackable = False
        if self._items_xml is not None:
            meta = self._items_xml.get(server_id)
            if meta is not None:
                stackable = bool(meta.stackable)

        return PreviewItem(
            server_id=int(server_id),
            client_id=int(client_id),
            count=int(count) if count is not None else None,
            stackable=bool(stackable),
        )

    def _load_legacy_items(self) -> dict[int, LegacyItemSpriteInfo] | None:
        profile = getattr(self._editor, "asset_profile", None)
        if profile is None or getattr(profile, "kind", None) != "legacy":
            return None
        sprite_assets = self._editor.sprite_assets
        if not isinstance(sprite_assets, LegacySpriteArchive):
            return None
        dat_path = profile.dat_path or profile.root
        try:
            parsed = load_legacy_item_sprites(
                dat_path,
                sprite_count=sprite_assets.sprite_count,
                is_extended=sprite_assets.is_extended,
                has_frame_durations=None,
            )
        except LegacyDatError:
            return None
        return dict(parsed.items)
