from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, QTimer
from PyQt6.QtWidgets import QMessageBox

from py_rme_canary.core.assets.legacy_dat_spr import LegacySpriteArchive
from py_rme_canary.logic_layer.settings.light_settings import LightMode
from py_rme_canary.logic_layer.sprite_system import LegacyDatError, LegacyItemSpriteInfo, load_legacy_item_sprites
from py_rme_canary.vis_layer.preview.preview_renderer import (
    PreviewCreature,
    PreviewItem,
    PreviewLighting,
    PreviewSnapshot,
    PreviewSpawn,
    PreviewViewport,
    TileSnapshot,
)
from py_rme_canary.vis_layer.preview.preview_thread import PreviewThread

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor

log = logging.getLogger(__name__)


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
        self._light_drawer = None
        self._health_check_counter: int = 0

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
        self._thread.join(timeout=2.0)
        if self._thread.is_alive():
            log.warning("Preview thread did not stop within timeout")
        error = self._thread.last_error
        if error:
            log.warning("Preview thread reported error: %s", error)
        self._thread = None

    @property
    def is_running(self) -> bool:
        """Return True if the preview thread is alive."""
        return self._thread is not None and self._thread.is_alive()

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

        # Health check: detect if thread has died unexpectedly
        self._health_check_counter += 1
        if self._health_check_counter % 10 == 0 and not self._thread.is_alive():
            error = self._thread.last_error or "Unknown error"
            log.error("Preview thread died: %s", error)
            self._timer.stop()
            self._thread = None
            QMessageBox.warning(
                self._editor,
                "In-Game Preview",
                f"Preview window closed unexpectedly:\n{error}",
            )
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
        lighting = self._build_lighting()
        show_light_strength = bool(getattr(lighting, "show_strength", False))
        show_lights = bool(getattr(lighting, "enabled", False))
        for y in range(viewport.origin_y, viewport.origin_y + viewport.tiles_high):
            for x in range(viewport.origin_x, viewport.origin_x + viewport.tiles_wide):
                tile = editor.map.get_tile(x, y, viewport.z)
                if tile is None:
                    continue
                ground = self._snapshot_item(tile.ground)
                items = tuple(self._snapshot_item(it) for it in tile.items if it is not None)
                light_strength = 0
                if show_lights or show_light_strength:
                    light_strength = self._light_strength_for_tile(tile)

                creatures = self._snapshot_creatures(tile)
                spawns = self._snapshot_spawns(tile)

                tiles.append(
                    TileSnapshot(
                        x=int(x),
                        y=int(y),
                        z=int(viewport.z),
                        ground=ground,
                        items=items,
                        light_strength=int(light_strength),
                        creatures=creatures,
                        spawns=spawns,
                    )
                )

        time_ms = int(editor.animation_time_ms() if hasattr(editor, "animation_time_ms") else 0)
        show_grid = bool(getattr(editor, "show_grid", False))
        return PreviewSnapshot(
            viewport=viewport,
            tiles=tuple(tiles),
            time_ms=time_ms,
            show_grid=bool(show_grid),
            lighting=lighting,
        )

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

        # Elevation from appearances.dat or legacy dat
        elevation = 0
        if self._editor.appearance_assets is not None:
            obj_info = getattr(self._editor.appearance_assets, "object_info", None)
            if obj_info is not None:
                app = obj_info.get(int(client_id))
                if app is not None:
                    elevation = int(getattr(app, "elevation", 0))

        return PreviewItem(
            server_id=int(server_id),
            client_id=int(client_id),
            count=int(count) if count is not None else None,
            stackable=bool(stackable),
            elevation=int(elevation),
        )

    @staticmethod
    def _snapshot_creatures(tile: object) -> tuple[PreviewCreature, ...]:
        """Extract creature snapshots from a tile."""
        result: list[PreviewCreature] = []
        monsters = getattr(tile, "monsters", None)
        if monsters:
            for m in monsters:
                name = str(getattr(m, "name", ""))
                outfit = getattr(m, "outfit", None)
                lookitem = int(getattr(outfit, "lookitem", 0) or 0) if outfit else 0
                result.append(PreviewCreature(
                    name=name,
                    kind="monster",
                    lookitem=lookitem if lookitem > 0 else None,
                ))
        npc = getattr(tile, "npc", None)
        if npc is not None:
            name = str(getattr(npc, "name", ""))
            outfit = getattr(npc, "outfit", None)
            lookitem = int(getattr(outfit, "lookitem", 0) or 0) if outfit else 0
            result.append(PreviewCreature(
                name=name,
                kind="npc",
                lookitem=lookitem if lookitem > 0 else None,
            ))
        return tuple(result)

    @staticmethod
    def _snapshot_spawns(tile: object) -> tuple[PreviewSpawn, ...]:
        """Extract spawn marker snapshots from a tile."""
        result: list[PreviewSpawn] = []
        sm = getattr(tile, "spawn_monster", None)
        if sm is not None:
            result.append(PreviewSpawn(
                kind="monster",
                radius=int(getattr(sm, "radius", 0)),
            ))
        sn = getattr(tile, "spawn_npc", None)
        if sn is not None:
            result.append(PreviewSpawn(
                kind="npc",
                radius=int(getattr(sn, "radius", 0)),
            ))
        return tuple(result)

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

    def _build_lighting(self) -> PreviewLighting:
        opts = getattr(self._editor, "drawing_options", None)
        if opts is None:
            return PreviewLighting()
        settings = getattr(opts, "light_settings", None)
        if settings is None:
            return PreviewLighting()

        mode_obj = getattr(settings, "mode", LightMode.OFF)
        mode = str(getattr(mode_obj, "value", mode_obj))
        enabled = bool(getattr(opts, "show_lights", False)) and bool(getattr(settings, "enabled", False))
        if mode in ("off", str(LightMode.OFF)):
            enabled = False

        ambient_level = int(getattr(settings, "ambient_level", 255))
        ambient_color = (255, 255, 255)
        try:
            ambient_color = tuple(int(c) for c in settings.ambient_color.to_rgb_tuple())
        except Exception:
            ambient_color = (255, 255, 255)

        outdoor_time = float(getattr(settings, "outdoor_time", 12.0))

        return PreviewLighting(
            enabled=bool(enabled),
            mode=str(mode),
            ambient_level=int(ambient_level),
            ambient_color=ambient_color,
            show_strength=bool(getattr(opts, "show_light_strength", False)),
            outdoor_time=float(outdoor_time),
        )

    def _light_strength_for_tile(self, tile) -> int:
        if self._light_drawer is None:
            try:
                from py_rme_canary.vis_layer.renderer.drawers.light_drawer import LightDrawer

                self._light_drawer = LightDrawer()
            except Exception:
                self._light_drawer = False
        if self._light_drawer is False:
            return 0
        try:
            return int(self._light_drawer._tile_light_strength(tile))
        except Exception:
            return 0
