"""Tests for Phase 5 Advanced Preview Features."""
from __future__ import annotations

import math
from unittest.mock import MagicMock

import pytest

from py_rme_canary.vis_layer.preview.preview_renderer import (
    PreviewCreature,
    PreviewItem,
    PreviewLighting,
    PreviewSpawn,
    TileSnapshot,
)


class TestPreviewCreature:
    def test_defaults(self) -> None:
        c = PreviewCreature(name="Rat", kind="monster")
        assert c.name == "Rat"
        assert c.kind == "monster"
        assert c.lookitem is None

    def test_with_lookitem(self) -> None:
        c = PreviewCreature(name="Bear", kind="monster", lookitem=1234)
        assert c.lookitem == 1234

    def test_npc_kind(self) -> None:
        c = PreviewCreature(name="King", kind="npc")
        assert c.kind == "npc"

    def test_frozen(self) -> None:
        c = PreviewCreature(name="Rat", kind="monster")
        with pytest.raises(AttributeError):
            c.name = "Wolf"  # type: ignore[misc]


class TestPreviewSpawn:
    def test_defaults(self) -> None:
        s = PreviewSpawn(kind="monster")
        assert s.radius == 0

    def test_with_radius(self) -> None:
        s = PreviewSpawn(kind="npc", radius=5)
        assert s.radius == 5


class TestPreviewItemElevation:
    def test_default_zero(self) -> None:
        item = PreviewItem(server_id=1, client_id=1, count=1, stackable=False)
        assert item.elevation == 0

    def test_custom(self) -> None:
        item = PreviewItem(server_id=1, client_id=1, count=1, stackable=False, elevation=16)
        assert item.elevation == 16


class TestTileSnapshotCreatures:
    def test_empty_default(self) -> None:
        t = TileSnapshot(x=0, y=0, z=7, ground=None, items=())
        assert t.creatures == ()
        assert t.spawns == ()

    def test_with_creatures(self) -> None:
        c = (PreviewCreature(name="Rat", kind="monster"),)
        t = TileSnapshot(x=0, y=0, z=7, ground=None, items=(), creatures=c)
        assert len(t.creatures) == 1

    def test_with_spawns(self) -> None:
        s = (PreviewSpawn(kind="monster", radius=3),)
        t = TileSnapshot(x=0, y=0, z=7, ground=None, items=(), spawns=s)
        assert t.spawns[0].radius == 3


class TestPreviewLightingOutdoorTime:
    def test_default_noon(self) -> None:
        assert PreviewLighting().outdoor_time == 12.0

    def test_custom_time(self) -> None:
        assert PreviewLighting(outdoor_time=0.0).outdoor_time == 0.0


class TestDayNightCycle:
    @staticmethod
    def _time_factor(hour: float) -> float:
        normalized = (hour % 24) / 24.0
        angle = (normalized - 0.5) * 2 * math.pi
        return 0.3 + ((math.cos(angle) + 1) / 2) * 0.7

    def test_noon_brightest(self) -> None:
        assert self._time_factor(12.0) == pytest.approx(1.0, abs=0.01)

    def test_midnight_darkest(self) -> None:
        assert self._time_factor(0.0) == pytest.approx(0.3, abs=0.01)

    def test_midnight_24(self) -> None:
        assert self._time_factor(24.0) == pytest.approx(0.3, abs=0.01)

    def test_6am_moderate(self) -> None:
        assert 0.5 < self._time_factor(6.0) < 0.8

    def test_18pm_moderate(self) -> None:
        assert 0.5 < self._time_factor(18.0) < 0.8

    def test_symmetry(self) -> None:
        assert self._time_factor(6.0) == pytest.approx(self._time_factor(18.0), abs=0.01)


class TestUndergroundDarkness:
    @staticmethod
    def _factor(z: int) -> float:
        if z >= 7:
            return 1.0
        return max(0.1, 0.7 ** (7 - z))

    def test_surface(self) -> None:
        assert self._factor(7) == 1.0

    def test_deeper_darker(self) -> None:
        assert self._factor(6) > self._factor(3)

    def test_floor0_very_dark(self) -> None:
        assert self._factor(0) < 0.15

    def test_never_pitch_black(self) -> None:
        for z in range(8):
            assert self._factor(z) >= 0.1


class TestControllerSnapshotCreatures:
    def test_empty(self) -> None:
        from py_rme_canary.vis_layer.preview.preview_controller import PreviewController
        tile = MagicMock(monsters=[], npc=None)
        assert PreviewController._snapshot_creatures(tile) == ()

    def test_monster(self) -> None:
        from py_rme_canary.vis_layer.preview.preview_controller import PreviewController
        m = MagicMock(name="Rat", outfit=None)
        tile = MagicMock(monsters=[m], npc=None)
        result = PreviewController._snapshot_creatures(tile)
        assert len(result) == 1
        assert result[0].kind == "monster"

    def test_npc_with_lookitem(self) -> None:
        from py_rme_canary.vis_layer.preview.preview_controller import PreviewController
        outfit = MagicMock(lookitem=456)
        npc = MagicMock(name="King", outfit=outfit)
        tile = MagicMock(monsters=[], npc=npc)
        result = PreviewController._snapshot_creatures(tile)
        assert len(result) == 1
        assert result[0].lookitem == 456

    def test_spawns_none(self) -> None:
        from py_rme_canary.vis_layer.preview.preview_controller import PreviewController
        tile = MagicMock(spawn_monster=None, spawn_npc=None)
        assert PreviewController._snapshot_spawns(tile) == ()

    def test_spawns_both(self) -> None:
        from py_rme_canary.vis_layer.preview.preview_controller import PreviewController
        tile = MagicMock(spawn_monster=MagicMock(radius=3), spawn_npc=MagicMock(radius=5))
        result = PreviewController._snapshot_spawns(tile)
        assert len(result) == 2
        assert result[0].radius == 3
        assert result[1].radius == 5


class TestMinimapExporterAutomapColors:
    def test_resolve_from_appearance(self) -> None:
        from py_rme_canary.logic_layer.minimap_exporter import MinimapExporter
        info = MagicMock(has_minimap_color=True, minimap_color=42)
        idx = MagicMock(object_info={100: info})
        exporter = MinimapExporter(appearance_index=idx)
        assert exporter._resolve_automap_color(100) == 42

    def test_resolve_no_appearance(self) -> None:
        from py_rme_canary.logic_layer.minimap_exporter import MinimapExporter
        assert MinimapExporter()._resolve_automap_color(100) is None

    def test_resolve_no_minimap_flag(self) -> None:
        from py_rme_canary.logic_layer.minimap_exporter import MinimapExporter
        info = MagicMock(has_minimap_color=False)
        idx = MagicMock(object_info={100: info})
        assert MinimapExporter(appearance_index=idx)._resolve_automap_color(100) is None

    def test_fallback_grass(self) -> None:
        from py_rme_canary.logic_layer.minimap_exporter import MinimapExporter
        assert MinimapExporter._fallback_color(MagicMock(server_id=4526)) == 24

    def test_fallback_water(self) -> None:
        from py_rme_canary.logic_layer.minimap_exporter import MinimapExporter
        assert MinimapExporter._fallback_color(MagicMock(server_id=4664)) == 20

    def test_fallback_default(self) -> None:
        from py_rme_canary.logic_layer.minimap_exporter import MinimapExporter
        assert MinimapExporter._fallback_color(MagicMock(server_id=9999)) == 200

    def test_color_cache(self) -> None:
        from py_rme_canary.logic_layer.minimap_exporter import MinimapExporter
        info = MagicMock(has_minimap_color=True, minimap_color=77)
        idx = MagicMock(object_info={100: info})
        exporter = MinimapExporter(appearance_index=idx)
        tile = MagicMock()
        tile.ground = MagicMock(client_id=100, server_id=100, id=100)
        assert exporter._get_tile_minimap_color(tile) == 77
        assert 100 in exporter._color_cache


class TestNanoVGText:
    def test_glyph_map_has_ascii(self) -> None:
        from py_rme_canary.core.nanovg.nanovg_opengl_adapter import NanoVGContext
        gmap = NanoVGContext._build_glyph_map()
        for ch in "ABCDabcd0123 ":
            assert ch in gmap

    def test_glyph_5_columns(self) -> None:
        from py_rme_canary.core.nanovg.nanovg_opengl_adapter import NanoVGContext
        for ch, cols in NanoVGContext._build_glyph_map().items():
            assert len(cols) == 5

    def test_space_zeros(self) -> None:
        from py_rme_canary.core.nanovg.nanovg_opengl_adapter import NanoVGContext
        assert NanoVGContext._build_glyph_map()[" "] == (0, 0, 0, 0, 0)

    def test_glyph_cached(self) -> None:
        from py_rme_canary.core.nanovg.nanovg_opengl_adapter import NanoVGContext
        assert NanoVGContext._build_glyph_map() is NanoVGContext._build_glyph_map()
