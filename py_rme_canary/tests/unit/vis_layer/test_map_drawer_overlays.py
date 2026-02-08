from __future__ import annotations

from dataclasses import dataclass

from py_rme_canary.core.data.creature import Monster, Npc
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.spawns import MonsterSpawnArea
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.drawing_options import DrawingOptions
from py_rme_canary.logic_layer.settings import LIGHT_PRESETS
from py_rme_canary.vis_layer.renderer.map_drawer import MapDrawer, RenderBackend


@dataclass
class _DummyMap:
    tile: Tile

    def get_tile(self, x: int, y: int, z: int) -> Tile | None:
        if int(x) == int(self.tile.x) and int(y) == int(self.tile.y) and int(z) == int(self.tile.z):
            return self.tile
        return None


class _OverlayBackend(RenderBackend):
    def __init__(self) -> None:
        self.grid_rects: list[tuple[int, int, int, int]] = []
        self.shade_calls: list[tuple[int, int, int, int, int]] = []
        self.selection_calls: list[tuple[int, int, int, int, tuple[int, ...]]] = []
        self.indicator_calls: list[tuple[int, int, str, int]] = []
        self.text_calls: list[tuple[int, int, str]] = []
        self.tile_colors: list[tuple[int, int, int, int, int, int, int, int]] = []

    def clear(self, r: int, g: int, b: int, a: int = 255) -> None:
        pass

    def draw_tile_color(self, x: int, y: int, size: int, r: int, g: int, b: int, a: int = 255) -> None:
        self.tile_colors.append((x, y, size, size, r, g, b, a))

    def draw_tile_sprite(self, x: int, y: int, size: int, sprite_id: int) -> None:
        pass

    def draw_grid_line(self, x0: int, y0: int, x1: int, y1: int, r: int, g: int, b: int, a: int = 255) -> None:
        pass

    def draw_grid_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        self.grid_rects.append((x, y, w, h))

    def draw_selection_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        self.selection_calls.append((x, y, w, h, (r, g, b, a)))

    def draw_indicator_icon(self, x: int, y: int, indicator_type: str, size: int) -> None:
        self.indicator_calls.append((x, y, indicator_type, size))

    def draw_text(self, x: int, y: int, text: str, r: int, g: int, b: int, a: int = 255) -> None:
        self.text_calls.append((x, y, text))

    def draw_shade_overlay(self, x: int, y: int, w: int, h: int, alpha: int) -> None:
        self.shade_calls.append((x, y, w, h, alpha))


def _setup_viewport(drawer: MapDrawer, *, width: int = 32, height: int = 32, z: int = 7, tile_px: int = 32) -> None:
    drawer.viewport.origin_x = 0
    drawer.viewport.origin_y = 0
    drawer.viewport.z = z
    drawer.viewport.tile_px = tile_px
    drawer.viewport.width_px = width
    drawer.viewport.height_px = height


def test_draw_grid_and_shade_when_enabled() -> None:
    opts = DrawingOptions()
    opts.show_grid = 1
    opts.show_shade = True
    opts.show_all_floors = True
    drawer = MapDrawer(options=opts, game_map=None)
    _setup_viewport(drawer, width=32, height=32, z=8, tile_px=32)
    backend = _OverlayBackend()
    drawer.draw(backend)
    assert len(backend.grid_rects) == 9
    assert backend.shade_calls == [(0, 0, 32, 32, 128)]


def test_spawn_indicator_and_ingame_box_emit_selection_rects() -> None:
    opts = DrawingOptions()
    opts.show_spawns_monster = True
    opts.show_monsters = False
    opts.show_ingame_box = True
    opts.show_grid = 0
    opts.show_shade = False
    tile = Tile(
        x=0,
        y=0,
        z=7,
        ground=Item(id=101),
        spawn_monster=MonsterSpawnArea(center=Position(0, 0, 7), radius=1),
    )
    drawer = MapDrawer(options=opts, game_map=_DummyMap(tile=tile))
    _setup_viewport(drawer, width=32, height=32, z=7, tile_px=32)
    backend = _OverlayBackend()
    drawer.draw(backend)
    assert backend.indicator_calls
    assert backend.selection_calls
    sizes = {(w, h) for _, _, w, h, _ in backend.selection_calls}
    assert (32, 32) in sizes
    assert (15 * 32, 11 * 32) in sizes


def test_creature_names_drawn_when_enabled() -> None:
    opts = DrawingOptions()
    opts.show_monsters = True
    opts.show_npcs = True
    opts.show_grid = 0
    opts.show_shade = False
    tile = Tile(
        x=0,
        y=0,
        z=7,
        ground=Item(id=101),
        monsters=[Monster(name="Rat")],
        npc=Npc(name="Tom"),
    )
    drawer = MapDrawer(options=opts, game_map=_DummyMap(tile=tile))
    _setup_viewport(drawer, width=32, height=32, z=7, tile_px=32)
    backend = _OverlayBackend()
    drawer.draw(backend)
    texts = [t[2] for t in backend.text_calls]
    assert any("Rat" in t for t in texts)
    assert any("Tom" in t for t in texts)


def test_client_id_overlay_uses_item_client_id_when_enabled() -> None:
    opts = DrawingOptions()
    opts.show_grid = 0
    opts.show_shade = False
    opts.show_client_ids = True
    tile = Tile(
        x=0,
        y=0,
        z=7,
        ground=Item(id=101, client_id=301),
        items=[Item(id=202, client_id=4040)],
    )
    drawer = MapDrawer(options=opts, game_map=_DummyMap(tile=tile))
    _setup_viewport(drawer, width=32, height=32, z=7, tile_px=32)
    backend = _OverlayBackend()
    drawer.draw(backend)
    texts = [t[2] for t in backend.text_calls]
    assert "4040" in texts


def test_client_id_overlay_uses_resolver_when_item_lacks_client_id() -> None:
    opts = DrawingOptions()
    opts.show_grid = 0
    opts.show_shade = False
    opts.show_client_ids = True
    tile = Tile(
        x=0,
        y=0,
        z=7,
        ground=Item(id=101),
        items=[Item(id=5000)],
    )
    drawer = MapDrawer(options=opts, game_map=_DummyMap(tile=tile))
    drawer.client_id_resolver = lambda server_id: {5000: 35023}.get(int(server_id))
    _setup_viewport(drawer, width=32, height=32, z=7, tile_px=32)
    backend = _OverlayBackend()
    drawer.draw(backend)
    texts = [t[2] for t in backend.text_calls]
    assert "35023" in texts


def test_highlight_tile_draws_selection_rect() -> None:
    opts = DrawingOptions()
    opts.show_grid = 0
    opts.show_shade = False
    tile = Tile(
        x=5,
        y=6,
        z=7,
        ground=Item(id=101),
    )
    drawer = MapDrawer(options=opts, game_map=_DummyMap(tile=tile))
    _setup_viewport(drawer, width=64, height=64, z=7, tile_px=32)
    drawer.set_highlight_tile(5, 6, 7, duration_ms=2000)
    backend = _OverlayBackend()
    drawer.draw(backend)
    assert backend.selection_calls
    coords = {(x, y) for x, y, _w, _h, _c in backend.selection_calls}
    assert (5 * 32, 6 * 32) in coords


def test_light_rendering_glows_and_strength_labels() -> None:
    opts = DrawingOptions()
    opts.set_show_lights(True)
    opts.set_light_settings(LIGHT_PRESETS["night"])
    opts.show_light_strength = True
    opts.show_grid = 0
    opts.show_shade = False

    tile = Tile(
        x=0,
        y=0,
        z=7,
        ground=Item(id=101),
        items=[Item(id=202)],
        spawn_monster=MonsterSpawnArea(center=Position(0, 0, 7), radius=1),
    )
    drawer = MapDrawer(options=opts, game_map=_DummyMap(tile=tile))
    _setup_viewport(drawer, width=96, height=96, z=7, tile_px=32)
    backend = _OverlayBackend()
    drawer.draw(backend)

    assert backend.tile_colors, "Expected ambient overlay/glow draws"
    assert any(size >= drawer.viewport.width_px for _, _, size, _, _, _, _, _ in backend.tile_colors)
    assert any(call[7] >= 60 for call in backend.tile_colors)
    assert any(text.strip().isdigit() and int(text.strip()) > 0 for _, _, text in backend.text_calls)
