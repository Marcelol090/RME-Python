from __future__ import annotations

from dataclasses import dataclass

from py_rme_canary.logic_layer.drawing_options import DrawingOptions
from py_rme_canary.vis_layer.renderer.map_drawer import MapDrawer, RenderBackend


@dataclass
class _Header:
    width: int
    height: int


@dataclass
class _CountingMap:
    header: _Header
    calls: int = 0

    def get_tile(self, x: int, y: int, z: int):  # noqa: ANN201
        self.calls += 1
        return None


class _NoopBackend(RenderBackend):
    def clear(self, r: int, g: int, b: int, a: int = 255) -> None:
        return

    def draw_tile_color(self, x: int, y: int, size: int, r: int, g: int, b: int, a: int = 255) -> None:
        return

    def draw_tile_sprite(self, x: int, y: int, size: int, sprite_id: int) -> None:
        return

    def draw_grid_line(self, x0: int, y0: int, x1: int, y1: int, r: int, g: int, b: int, a: int = 255) -> None:
        return

    def draw_grid_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        return

    def draw_selection_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        return

    def draw_indicator_icon(self, x: int, y: int, indicator_type: str, size: int) -> None:
        return

    def draw_text(self, x: int, y: int, text: str, r: int, g: int, b: int, a: int = 255) -> None:
        return

    def draw_shade_overlay(self, x: int, y: int, w: int, h: int, alpha: int) -> None:
        return


def _configure_viewport(drawer: MapDrawer, *, origin_x: int, origin_y: int, width_px: int, height_px: int) -> None:
    drawer.viewport.origin_x = origin_x
    drawer.viewport.origin_y = origin_y
    drawer.viewport.z = 7
    drawer.viewport.tile_px = 32
    drawer.viewport.width_px = width_px
    drawer.viewport.height_px = height_px


def test_map_drawer_culls_to_map_bounds() -> None:
    opts = DrawingOptions()
    opts.show_grid = 0
    opts.show_shade = False
    game_map = _CountingMap(header=_Header(width=3, height=2))
    drawer = MapDrawer(options=opts, game_map=game_map)
    _configure_viewport(drawer, origin_x=0, origin_y=0, width_px=320, height_px=320)

    drawer.draw(_NoopBackend())

    assert game_map.calls == 6


def test_map_drawer_skips_when_viewport_outside_map() -> None:
    opts = DrawingOptions()
    opts.show_grid = 0
    opts.show_shade = False
    game_map = _CountingMap(header=_Header(width=4, height=4))
    drawer = MapDrawer(options=opts, game_map=game_map)
    _configure_viewport(drawer, origin_x=200, origin_y=200, width_px=320, height_px=320)

    drawer.draw(_NoopBackend())

    assert game_map.calls == 0


def test_map_drawer_clamps_negative_origin_to_zero() -> None:
    opts = DrawingOptions()
    opts.show_grid = 0
    opts.show_shade = False
    game_map = _CountingMap(header=_Header(width=2, height=2))
    drawer = MapDrawer(options=opts, game_map=game_map)
    _configure_viewport(drawer, origin_x=-1, origin_y=-1, width_px=96, height_px=96)

    drawer.draw(_NoopBackend())

    assert game_map.calls == 4
