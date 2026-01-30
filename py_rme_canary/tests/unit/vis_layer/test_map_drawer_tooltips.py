from __future__ import annotations

from dataclasses import dataclass

from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.spawns import MonsterSpawnArea
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.drawing_options import DrawingOptions
from py_rme_canary.vis_layer.renderer.map_drawer import MapDrawer, RenderBackend


@dataclass
class _DummyMap:
    tile: Tile

    def get_tile(self, x: int, y: int, z: int) -> Tile | None:
        if int(x) == int(self.tile.x) and int(y) == int(self.tile.y) and int(z) == int(self.tile.z):
            return self.tile
        return None


class _FakeBackend(RenderBackend):
    def __init__(self) -> None:
        self.selection_calls: list[tuple[int, int, int, int, tuple[int, ...]]] = []
        self.text_calls: list[tuple[int, int, str]] = []

    def clear(self, r: int, g: int, b: int, a: int = 255) -> None:  # pragma: no cover - unused
        pass

    def draw_tile_color(self, x: int, y: int, size: int, r: int, g: int, b: int, a: int = 255) -> None:
        pass

    def draw_tile_sprite(self, x: int, y: int, size: int, sprite_id: int) -> None:
        pass

    def draw_grid_line(self, x0: int, y0: int, x1: int, y1: int, r: int, g: int, b: int, a: int = 255) -> None:
        pass

    def draw_grid_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        pass

    def draw_selection_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        self.selection_calls.append((x, y, w, h, (r, g, b, a)))

    def draw_indicator_icon(self, x: int, y: int, indicator_type: str, size: int) -> None:
        pass

    def draw_text(self, x: int, y: int, text: str, r: int, g: int, b: int, a: int = 255) -> None:
        self.text_calls.append((x, y, text))

    def draw_shade_overlay(self, x: int, y: int, w: int, h: int, alpha: int) -> None:
        pass


def test_draw_tooltips_renders_hover_info():
    opts = DrawingOptions()
    opts.show_tooltips = True

    tile = Tile(
        x=0,
        y=0,
        z=7,
        ground=Item(id=101),
        items=[Item(id=202)],
        spawn_monster=MonsterSpawnArea(center=Position(0, 0, 7), radius=1),  # center not used by renderer
    )

    drawer = MapDrawer(options=opts, game_map=_DummyMap(tile=tile))
    drawer.viewport.origin_x = 0
    drawer.viewport.origin_y = 0
    drawer.viewport.z = 7
    drawer.viewport.tile_px = 32
    drawer.viewport.width_px = 64
    drawer.viewport.height_px = 64

    # Inject hover info (as MapCanvasWidget does).
    drawer.set_hover_tile(0, 0, 7, [101, 202])

    backend = _FakeBackend()
    drawer.draw(backend)

    assert backend.selection_calls, "Tooltip should highlight hover tile"
    assert backend.text_calls, "Tooltip should render text for hover tile"
    assert "top:202" in backend.text_calls[-1][2]
