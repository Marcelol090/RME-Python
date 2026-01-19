"""Tests for DoorBrush functionality."""
from __future__ import annotations

import unittest

from py_rme_canary.core.data.door import DoorType
from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.door_brush import DoorBrush


class TestDoorType(unittest.TestCase):
    """Test DoorType enum."""

    def test_door_types_exist(self) -> None:
        """All 6 door types are defined."""
        self.assertEqual(DoorType.NORMAL, 1)
        self.assertEqual(DoorType.LOCKED, 2)
        self.assertEqual(DoorType.MAGIC, 3)
        self.assertEqual(DoorType.QUEST, 4)
        self.assertEqual(DoorType.HATCH, 5)
        self.assertEqual(DoorType.WINDOW, 6)

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

    def _create_tile_with_wall(self, x: int, y: int, z: int) -> Tile:
        """Create a tile with a wall item."""
        wall_item = Item(id=1220)  # Wall in valid range
        return Tile(
            x=x,
            y=y,
            z=z,
            items=[wall_item],
        )

    def test_can_draw_no_tile(self) -> None:
        """can_draw returns False if no tile exists."""
        pos = Position(x=50, y=50, z=7)
        self.assertFalse(self.brush.can_draw(self.game_map, pos))

    def test_can_draw_no_wall(self) -> None:
        """can_draw returns False if tile has no wall."""
        tile = Tile(x=50, y=50, z=7, items=[Item(id=100)])  # Non-wall item
        self.game_map.set_tile(tile)
        pos = Position(x=50, y=50, z=7)
        self.assertFalse(self.brush.can_draw(self.game_map, pos))

    def test_can_draw_with_wall(self) -> None:
        """can_draw returns True if tile has wall."""
        tile = self._create_tile_with_wall(50, 50, 7)
        self.game_map.set_tile(tile)
        pos = Position(x=50, y=50, z=7)
        self.assertTrue(self.brush.can_draw(self.game_map, pos))

    def test_draw_converts_wall(self) -> None:
        """draw replaces wall with door item."""
        tile = self._create_tile_with_wall(50, 50, 7)
        self.game_map.set_tile(tile)
        pos = Position(x=50, y=50, z=7)

        changes = self.brush.draw(self.game_map, pos)

        self.assertEqual(len(changes), 1)
        new_pos, new_tile = changes[0]
        self.assertEqual(new_pos, pos)
        # Door should be different from original wall
        self.assertEqual(len(new_tile.items), 1)
        self.assertNotEqual(new_tile.items[0].id, 1220)

    def test_switch_door(self) -> None:
        """switch_door toggles door state."""
        closed_door = Item(id=1210)
        open_door = DoorBrush.switch_door(closed_door)
        self.assertNotEqual(open_door.id, closed_door.id)

    def test_get_name(self) -> None:
        """Brush has human-readable name."""
        self.assertEqual(self.brush.get_name(), "Normal door brush")


if __name__ == "__main__":
    unittest.main()
