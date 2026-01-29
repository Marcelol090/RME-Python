from __future__ import annotations

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.borders.border_groups import BorderGroupRegistry
from py_rme_canary.logic_layer.borders.ground_equivalents import GroundEquivalentRegistry
from py_rme_canary.logic_layer.borders.processor import AutoBorderProcessor
from py_rme_canary.logic_layer.brush_definitions import BrushDefinition


class _DummyBrushManager:
    def __init__(
        self,
        brushes: list[BrushDefinition],
        *,
        border_groups: BorderGroupRegistry | None = None,
        ground_equivalents: GroundEquivalentRegistry | None = None,
    ) -> None:
        self._brushes = {int(b.server_id): b for b in brushes}
        self._border_groups = border_groups or BorderGroupRegistry()
        self._ground_equivalents = ground_equivalents or GroundEquivalentRegistry()

    def get_brush(self, server_id: int) -> BrushDefinition | None:
        return self._brushes.get(int(server_id))

    def get_brush_any(self, server_id: int) -> BrushDefinition | None:
        return self._brushes.get(int(server_id))

    def border_groups(self) -> BorderGroupRegistry:
        return self._border_groups

    def ground_equivalents(self) -> GroundEquivalentRegistry:
        return self._ground_equivalents


def _make_map() -> GameMap:
    return GameMap(header=MapHeader(otbm_version=2, width=5, height=5))


def _seed_tile(game_map: GameMap, x: int, y: int, z: int, *, ground: int | None, items: list[int]) -> None:
    game_map.set_tile(
        Tile(
            x=int(x),
            y=int(y),
            z=int(z),
            ground=None if ground is None else Item(id=int(ground)),
            items=[Item(id=int(i)) for i in items],
        )
    )


def test_ground_equivalent_neighbor_counts_as_same() -> None:
    brush = BrushDefinition(
        name="grass",
        server_id=100,
        brush_type="ground",
        borders={"NORTH": 101},
    )
    ground_eq = GroundEquivalentRegistry()
    ground_eq.register(101, 100)
    mgr = _DummyBrushManager([brush], ground_equivalents=ground_eq)

    game_map = _make_map()
    _seed_tile(game_map, 2, 2, 7, ground=100, items=[])
    _seed_tile(game_map, 2, 1, 7, ground=None, items=[101])

    AutoBorderProcessor(game_map, mgr).update_tile(2, 2, 7, 100)

    center = game_map.get_tile(2, 2, 7)
    assert center is not None
    assert [int(it.id) for it in center.items] == []


def test_ground_friend_neighbor_counts_as_same() -> None:
    brush_a = BrushDefinition(
        name="grass",
        server_id=100,
        brush_type="ground",
        borders={"NORTH": 101},
        friends=(200,),
    )
    brush_b = BrushDefinition(
        name="dirt",
        server_id=200,
        brush_type="ground",
        borders={"NORTH": 201},
    )
    mgr = _DummyBrushManager([brush_a, brush_b])

    game_map = _make_map()
    _seed_tile(game_map, 2, 2, 7, ground=100, items=[])
    _seed_tile(game_map, 2, 1, 7, ground=200, items=[])

    AutoBorderProcessor(game_map, mgr).update_tile(2, 2, 7, 100)

    center = game_map.get_tile(2, 2, 7)
    assert center is not None
    assert [int(it.id) for it in center.items] == []


def test_border_group_removes_existing_group_items() -> None:
    brush = BrushDefinition(
        name="grass",
        server_id=100,
        brush_type="ground",
        borders={"NORTH": 101},
        border_group=7,
    )
    groups = BorderGroupRegistry()
    groups.register_group(7, [101, 202])
    mgr = _DummyBrushManager([brush], border_groups=groups)

    game_map = _make_map()
    _seed_tile(game_map, 2, 2, 7, ground=100, items=[202])

    AutoBorderProcessor(game_map, mgr).update_tile(2, 2, 7, 100)

    center = game_map.get_tile(2, 2, 7)
    assert center is not None
    assert [int(it.id) for it in center.items] == [101]
