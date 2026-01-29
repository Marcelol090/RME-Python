"""Tests for doodad erase-like behavior in TransactionalBrushStroke."""

from __future__ import annotations

import unittest

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.brush_definitions import (
    VIRTUAL_DOODAD_BASE,
    BrushManager,
    DoodadAlternative,
    DoodadBrushSpec,
    DoodadItemChoice,
)
from py_rme_canary.logic_layer.transactional_brush import HistoryManager, TransactionalBrushStroke


class TestDoodadEraseLike(unittest.TestCase):
    """Validate doodad erasing respects erase-like and unique-item rules."""

    def setUp(self) -> None:
        header = MapHeader(width=32, height=32, otbm_version=2)
        self.game_map = GameMap(header=header)
        self.brush_manager = BrushManager()

        spec_a = DoodadBrushSpec(
            name="Brush A",
            server_id=1,
            alternatives=(DoodadAlternative(items=(DoodadItemChoice(id=100, chance=10),)),),
        )
        spec_b = DoodadBrushSpec(
            name="Brush B",
            server_id=2,
            alternatives=(DoodadAlternative(items=(DoodadItemChoice(id=200, chance=10),)),),
        )

        self.brush_manager._doodads = {1: spec_a, 2: spec_b}
        self.brush_manager._doodads_loaded = True
        self.brush_manager._doodad_owned_ids_cache = None

    def _apply_erase(self, *, erase_like: bool, leave_unique: bool) -> Tile | None:
        tile = Tile(
            x=1,
            y=1,
            z=7,
            ground=Item(id=100),
            items=[
                Item(id=100),
                Item(id=100, unique_id=42),
                Item(id=200),
                Item(id=999),
            ],
        )
        self.game_map.set_tile(tile)

        stroke = TransactionalBrushStroke(
            game_map=self.game_map,
            brush_manager=self.brush_manager,
            history=HistoryManager(),
            auto_border_enabled=False,
        )
        stroke.doodad_erase_like = bool(erase_like)
        stroke.eraser_leave_unique = bool(leave_unique)

        brush_id = int(VIRTUAL_DOODAD_BASE + 1)
        stroke.begin(x=1, y=1, z=7, selected_server_id=brush_id, alt=True)
        stroke.end()

        return self.game_map.get_tile(1, 1, 7)

    def test_erase_like_only_removes_owned_items(self) -> None:
        tile = self._apply_erase(erase_like=True, leave_unique=True)
        assert tile is not None
        self.assertIsNone(tile.ground)
        self.assertEqual([int(it.id) for it in tile.items], [100, 200, 999])
        self.assertEqual(tile.items[0].unique_id, 42)

    def test_erase_like_false_removes_all_doodad_items(self) -> None:
        tile = self._apply_erase(erase_like=False, leave_unique=True)
        assert tile is not None
        self.assertIsNone(tile.ground)
        self.assertEqual([int(it.id) for it in tile.items], [100, 999])
        self.assertEqual(tile.items[0].unique_id, 42)

    def test_eraser_can_remove_unique_items_when_disabled(self) -> None:
        tile = self._apply_erase(erase_like=False, leave_unique=False)
        assert tile is not None
        self.assertIsNone(tile.ground)
        self.assertEqual([int(it.id) for it in tile.items], [999])


if __name__ == "__main__":
    unittest.main()
