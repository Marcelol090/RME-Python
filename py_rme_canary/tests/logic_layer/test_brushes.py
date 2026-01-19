"""Tests for specialized brushes: Monster, NPC, Eraser, Flag."""
from __future__ import annotations

import unittest

from py_rme_canary.core.data.creature import Monster, Npc
from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.eraser_brush import EraserBrush, EraserMode
from py_rme_canary.logic_layer.flag_brush import FlagBrush, TileFlag
from py_rme_canary.logic_layer.monster_brush import MonsterBrush
from py_rme_canary.logic_layer.npc_brush import NpcBrush


class TestMonsterBrush(unittest.TestCase):
    """Test MonsterBrush functionality."""

    def setUp(self) -> None:
        self.header = MapHeader(width=100, height=100, otbm_version=2)
        self.game_map = GameMap(header=self.header)
        self.brush = MonsterBrush(monster_name="Rat")

    def _create_tile_with_ground(self, x: int, y: int, z: int) -> Tile:
        return Tile(x=x, y=y, z=z, ground=Item(id=100))

    def test_can_draw_no_ground(self) -> None:
        """Cannot place monster on tile without ground."""
        tile = Tile(x=50, y=50, z=7)
        self.game_map.set_tile(tile)
        self.assertFalse(self.brush.can_draw(self.game_map, Position(50, 50, 7)))

    def test_can_draw_with_ground(self) -> None:
        """Can place monster on tile with ground."""
        tile = self._create_tile_with_ground(50, 50, 7)
        self.game_map.set_tile(tile)
        self.assertTrue(self.brush.can_draw(self.game_map, Position(50, 50, 7)))

    def test_draw_places_monster(self) -> None:
        """draw() adds monster to tile."""
        tile = self._create_tile_with_ground(50, 50, 7)
        self.game_map.set_tile(tile)
        pos = Position(50, 50, 7)

        changes = self.brush.draw(self.game_map, pos)

        self.assertEqual(len(changes), 1)
        _, new_tile = changes[0]
        self.assertEqual(len(new_tile.monsters), 1)
        self.assertEqual(new_tile.monsters[0].name, "Rat")

    def test_draw_no_duplicate(self) -> None:
        """draw() doesn't add duplicate monster."""
        tile = Tile(
            x=50, y=50, z=7,
            ground=Item(id=100),
            monsters=[Monster(name="Rat", direction=2)],
        )
        self.game_map.set_tile(tile)
        pos = Position(50, 50, 7)

        changes = self.brush.draw(self.game_map, pos)

        self.assertEqual(len(changes), 0)


class TestNpcBrush(unittest.TestCase):
    """Test NpcBrush functionality."""

    def setUp(self) -> None:
        self.header = MapHeader(width=100, height=100, otbm_version=2)
        self.game_map = GameMap(header=self.header)
        self.brush = NpcBrush(npc_name="Sam")

    def test_can_draw_with_ground(self) -> None:
        """Can place NPC on tile with ground."""
        tile = Tile(x=50, y=50, z=7, ground=Item(id=100))
        self.game_map.set_tile(tile)
        self.assertTrue(self.brush.can_draw(self.game_map, Position(50, 50, 7)))

    def test_cannot_draw_existing_npc(self) -> None:
        """Cannot place NPC if one already exists."""
        tile = Tile(x=50, y=50, z=7, ground=Item(id=100), npc=Npc("Bob", 2))
        self.game_map.set_tile(tile)
        self.assertFalse(self.brush.can_draw(self.game_map, Position(50, 50, 7)))


class TestEraserBrush(unittest.TestCase):
    """Test EraserBrush functionality."""

    def setUp(self) -> None:
        self.header = MapHeader(width=100, height=100, otbm_version=2)
        self.game_map = GameMap(header=self.header)

    def test_erase_monsters_only(self) -> None:
        """Erase only monsters, keep items."""
        tile = Tile(
            x=50, y=50, z=7,
            ground=Item(id=100),
            items=[Item(id=200)],
            monsters=[Monster(name="Rat", direction=2)],
        )
        self.game_map.set_tile(tile)
        eraser = EraserBrush(mode=EraserMode.MONSTERS)
        pos = Position(50, 50, 7)

        changes = eraser.draw(self.game_map, pos)

        self.assertEqual(len(changes), 1)
        _, new_tile = changes[0]
        self.assertEqual(len(new_tile.monsters), 0)
        self.assertEqual(len(new_tile.items), 1)  # Items preserved

    def test_erase_all(self) -> None:
        """Erase everything."""
        tile = Tile(
            x=50, y=50, z=7,
            ground=Item(id=100),
            items=[Item(id=200)],
            monsters=[Monster(name="Rat", direction=2)],
            npc=Npc("Sam", 2),
        )
        self.game_map.set_tile(tile)
        eraser = EraserBrush(mode=EraserMode.ALL)
        pos = Position(50, 50, 7)

        changes = eraser.draw(self.game_map, pos)

        _, new_tile = changes[0]
        self.assertIsNone(new_tile.ground)
        self.assertEqual(len(new_tile.items), 0)
        self.assertEqual(len(new_tile.monsters), 0)
        self.assertIsNone(new_tile.npc)


class TestFlagBrush(unittest.TestCase):
    """Test FlagBrush functionality."""

    def setUp(self) -> None:
        self.header = MapHeader(width=100, height=100, otbm_version=2)
        self.game_map = GameMap(header=self.header)

    def test_set_pz_flag(self) -> None:
        """FlagBrush sets Protection Zone flag."""
        tile = Tile(x=50, y=50, z=7, ground=Item(id=100), map_flags=0)
        self.game_map.set_tile(tile)
        brush = FlagBrush(flag=TileFlag.PROTECTION_ZONE)
        pos = Position(50, 50, 7)

        changes = brush.draw(self.game_map, pos)

        _, new_tile = changes[0]
        self.assertTrue(new_tile.map_flags & TileFlag.PROTECTION_ZONE)

    def test_clear_flag(self) -> None:
        """FlagBrush with set_flag=False clears flag."""
        tile = Tile(
            x=50, y=50, z=7,
            ground=Item(id=100),
            map_flags=TileFlag.PROTECTION_ZONE,
        )
        self.game_map.set_tile(tile)
        brush = FlagBrush(flag=TileFlag.PROTECTION_ZONE, set_flag=False)
        pos = Position(50, 50, 7)

        changes = brush.draw(self.game_map, pos)

        _, new_tile = changes[0]
        self.assertFalse(new_tile.map_flags & TileFlag.PROTECTION_ZONE)


if __name__ == "__main__":
    unittest.main()
