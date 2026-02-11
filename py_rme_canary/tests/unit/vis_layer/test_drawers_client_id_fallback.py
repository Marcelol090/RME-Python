from __future__ import annotations

from types import SimpleNamespace

from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.vis_layer.renderer.drawers.floor_drawer import FloorDrawer
from py_rme_canary.vis_layer.renderer.drawers.item_drawer import ItemDrawer


class _Backend:
    def __init__(self) -> None:
        self.calls: list[int] = []

    def draw_tile_sprite(self, _x: int, _y: int, _size: int, sprite_id: int) -> None:
        self.calls.append(int(sprite_id))


def test_item_drawer_uses_raw_client_id_when_server_id_missing() -> None:
    drawer = ItemDrawer()
    backend = _Backend()
    map_drawer = SimpleNamespace(should_draw_items=lambda: True)
    tile = Tile(x=1, y=2, z=7, items=[Item(id=0, client_id=4500)])

    drawer.draw(map_drawer, backend, tile, 0, 0, 32)

    assert backend.calls == [-4500]


def test_floor_drawer_uses_raw_client_id_when_server_id_missing() -> None:
    drawer = FloorDrawer()
    backend = _Backend()
    map_drawer = SimpleNamespace(options=SimpleNamespace(show_items=True))
    tile = Tile(x=1, y=2, z=7, ground=Item(id=0, client_id=3001))

    drawer.draw(map_drawer, backend, tile, 0, 0, 32)

    assert backend.calls == [-3001]


def test_item_drawer_prefers_server_id_when_available() -> None:
    drawer = ItemDrawer()
    backend = _Backend()
    map_drawer = SimpleNamespace(should_draw_items=lambda: True)
    tile = Tile(x=1, y=2, z=7, items=[Item(id=2160, client_id=3043)])

    drawer.draw(map_drawer, backend, tile, 0, 0, 32)

    assert backend.calls == [2160]
