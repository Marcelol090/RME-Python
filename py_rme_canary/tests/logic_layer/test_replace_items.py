"""Tests for replace_items and find_items functions."""

from __future__ import annotations

import unittest

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.remove_items import (
    find_items_in_map,
    replace_items_in_map,
    replace_items_in_tile,
)


class TestReplaceItemsInTile(unittest.TestCase):
    """Test replace_items_in_tile function."""

    def test_replace_in_ground(self) -> None:
        """Replace ground item."""
        tile = Tile(x=10, y=10, z=7, ground=Item(id=100))
        new_tile, count = replace_items_in_tile(tile=tile, source_id=100, target_id=200)
        self.assertEqual(count, 1)
        self.assertIsNotNone(new_tile.ground)
        self.assertEqual(new_tile.ground.id, 200)

    def test_replace_in_items(self) -> None:
        """Replace items in stack."""
        tile = Tile(
            x=10,
            y=10,
            z=7,
            ground=Item(id=50),
            items=[Item(id=100), Item(id=101), Item(id=100)],
        )
        new_tile, count = replace_items_in_tile(tile=tile, source_id=100, target_id=200)
        self.assertEqual(count, 2)
        self.assertEqual(len(new_tile.items), 3)
        self.assertEqual(new_tile.items[0].id, 200)
        self.assertEqual(new_tile.items[1].id, 101)
        self.assertEqual(new_tile.items[2].id, 200)

    def test_no_match(self) -> None:
        """No replacement when ID not found."""
        tile = Tile(x=10, y=10, z=7, ground=Item(id=50), items=[Item(id=60)])
        new_tile, count = replace_items_in_tile(tile=tile, source_id=100, target_id=200)
        self.assertEqual(count, 0)
        self.assertIs(new_tile, tile)  # Same object returned


class TestReplaceItemsInMap(unittest.TestCase):
    """Test replace_items_in_map function."""

    def setUp(self) -> None:
        self.header = MapHeader(width=100, height=100, otbm_version=2)
        self.game_map = GameMap(header=self.header)

    def test_replace_across_tiles(self) -> None:
        """Replace items across multiple tiles."""
        tile1 = Tile(x=10, y=10, z=7, ground=Item(id=100))
        tile2 = Tile(x=20, y=20, z=7, ground=Item(id=100), items=[Item(id=100)])
        tile3 = Tile(x=30, y=30, z=7, ground=Item(id=50))

        self.game_map.set_tile(tile1)
        self.game_map.set_tile(tile2)
        self.game_map.set_tile(tile3)

        changed, result = replace_items_in_map(self.game_map, source_id=100, target_id=200)

        self.assertEqual(result.replaced, 3)  # 1 + 2 = 3 replacements
        self.assertEqual(len(changed), 2)

    def test_selection_only(self) -> None:
        """Replace only in selection."""
        tile1 = Tile(x=10, y=10, z=7, ground=Item(id=100))
        tile2 = Tile(x=20, y=20, z=7, ground=Item(id=100))

        self.game_map.set_tile(tile1)
        self.game_map.set_tile(tile2)

        changed, result = replace_items_in_map(
            self.game_map,
            source_id=100,
            target_id=200,
            selection_only=True,
            selection_tiles={(10, 10, 7)},
        )

        self.assertEqual(result.replaced, 1)
        self.assertEqual(len(changed), 1)
        self.assertIn((10, 10, 7), changed)


class TestFindItemsInMap(unittest.TestCase):
    """Test find_items_in_map function."""

    def setUp(self) -> None:
        self.header = MapHeader(width=100, height=100, otbm_version=2)
        self.game_map = GameMap(header=self.header)

    def test_find_item(self) -> None:
        """Find item positions."""
        tile1 = Tile(x=10, y=10, z=7, ground=Item(id=100))
        tile2 = Tile(x=20, y=20, z=7, items=[Item(id=100)])
        tile3 = Tile(x=30, y=30, z=7, ground=Item(id=50))

        self.game_map.set_tile(tile1)
        self.game_map.set_tile(tile2)
        self.game_map.set_tile(tile3)

        results = find_items_in_map(self.game_map, server_id=100)

        self.assertEqual(len(results), 2)
        self.assertIn((10, 10, 7), results)
        self.assertIn((20, 20, 7), results)

    def test_find_empty(self) -> None:
        """Returns empty when not found."""
        tile = Tile(x=10, y=10, z=7, ground=Item(id=50))
        self.game_map.set_tile(tile)

        results = find_items_in_map(self.game_map, server_id=999)
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
