"""Tests for DoorBrush functionality."""

from __future__ import annotations

import unittest

from py_rme_canary.core.data.door import DoorType
from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.brush_definitions import (
    BrushDefinition,
    BrushManager,
    DoorBrushSpec,
    DoorItemSpec,
)
from py_rme_canary.logic_layer.door_brush import DoorBrush


def _make_brush_manager() -> tuple[BrushManager, DoorBrushSpec]:
    door_spec = DoorBrushSpec(
        name="test wall",
        server_id=1000,
        items_by_alignment={
            "HORIZONTAL": (
                DoorItemSpec(id=2000, door_type=DoorType.NORMAL, is_open=False),
                DoorItemSpec(id=2001, door_type=DoorType.NORMAL, is_open=True),
            ),
            "VERTICAL": (
                DoorItemSpec(id=2010, door_type=DoorType.NORMAL, is_open=False),
                DoorItemSpec(id=2011, door_type=DoorType.NORMAL, is_open=True),
            ),
        },
    )

    brush_def = BrushDefinition(
        name="test wall",
        server_id=1000,
        brush_type="wall",
        borders={"HORIZONTAL": 1000, "VERTICAL": 1001},
        transition_borders={},
        door_spec=door_spec,
    )

    mgr = BrushManager()
    mgr._brushes[int(brush_def.server_id)] = brush_def
    for fid in brush_def.family_ids:
        mgr._family_index[int(fid)] = int(brush_def.server_id)

    return mgr, door_spec


class TestDoorType(unittest.TestCase):
    """Test DoorType enum."""

    def test_door_types_exist(self) -> None:
        """Legacy door type values are preserved."""
        self.assertEqual(DoorType.UNDEFINED, 0)
        self.assertEqual(DoorType.ARCHWAY, 1)
        self.assertEqual(DoorType.NORMAL, 2)
        self.assertEqual(DoorType.LOCKED, 3)
        self.assertEqual(DoorType.QUEST, 4)
        self.assertEqual(DoorType.MAGIC, 5)
        self.assertEqual(DoorType.WINDOW, 6)
        self.assertEqual(DoorType.HATCH, 7)

    def test_get_name(self) -> None:
        """Door types have human-readable names."""
        self.assertEqual(DoorType.NORMAL.get_name(), "Normal door")
        self.assertEqual(DoorType.LOCKED.get_name(), "Locked door")


class TestDoorBrush(unittest.TestCase):
    """Test DoorBrush functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.header = MapHeader(width=100, height=100, otbm_version=2)
        self.game_map = GameMap(header=self.header)
        self.brush = DoorBrush(door_type=DoorType.NORMAL)
        self.brush_manager, self.door_spec = _make_brush_manager()

    def _create_tile_with_wall(self, x: int, y: int, z: int) -> Tile:
        """Create a tile with a wall item."""
        wall_item = Item(id=1000)  # Horizontal wall id
        return Tile(
            x=x,
            y=y,
            z=z,
            items=[wall_item],
        )

    def test_can_draw_no_tile(self) -> None:
        """can_draw returns False if no tile exists."""
        pos = Position(x=50, y=50, z=7)
        self.assertFalse(self.brush.can_draw(self.game_map, pos, brush_manager=self.brush_manager))

    def test_can_draw_with_wall(self) -> None:
        """can_draw returns True if tile has wall with door spec."""
        tile = self._create_tile_with_wall(50, 50, 7)
        self.game_map.set_tile(tile)
        pos = Position(x=50, y=50, z=7)
        self.assertTrue(self.brush.can_draw(self.game_map, pos, brush_manager=self.brush_manager))

    def test_draw_converts_wall(self) -> None:
        """draw replaces wall with door item based on alignment."""
        tile = self._create_tile_with_wall(50, 50, 7)
        self.game_map.set_tile(tile)
        pos = Position(x=50, y=50, z=7)

        changes = self.brush.draw(self.game_map, pos, brush_manager=self.brush_manager)

        self.assertEqual(len(changes), 1)
        new_pos, new_tile = changes[0]
        self.assertEqual(new_pos, pos)
        self.assertEqual(len(new_tile.items), 1)
        self.assertEqual(new_tile.items[0].id, 2000)

    def test_draw_preserves_open_state(self) -> None:
        """draw preserves open state when painting over an open door."""
        open_door = Item(id=2001)
        tile = Tile(x=50, y=50, z=7, items=[open_door])
        self.game_map.set_tile(tile)
        pos = Position(x=50, y=50, z=7)

        changes = self.brush.draw(self.game_map, pos, brush_manager=self.brush_manager)

        self.assertEqual(len(changes), 1)
        _, new_tile = changes[0]
        self.assertEqual(new_tile.items[0].id, 2001)

    def test_switch_door(self) -> None:
        """switch_door toggles door state using door specs."""
        closed_door = Item(id=2000)
        open_door = DoorBrush.switch_door(closed_door, door_spec=self.door_spec)
        self.assertEqual(open_door.id, 2001)


if __name__ == "__main__":
    unittest.main()
