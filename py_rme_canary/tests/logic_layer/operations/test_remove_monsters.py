from __future__ import annotations

# ruff: noqa: E501
import unittest

from py_rme_canary.core.data.creature import Monster, Npc
from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.spawns import MonsterSpawnArea
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.remove_items import remove_monsters_in_map


class TestRemoveMonsters(unittest.TestCase):
    def setUp(self):
        # Create a basic map header
        self.header = MapHeader(width=100, height=100, otbm_version=2)
        self.gamemap = GameMap(header=self.header)

    def _create_tile(self, x, y, z, monsters=None, npc=None, spawn_monster=None, spawn_npc=None, items=None):
        return Tile(
            x=x,
            y=y,
            z=z,
            monsters=monsters or [],
            npc=npc,
            spawn_monster=spawn_monster,
            spawn_npc=spawn_npc,
            items=items or [],
        )

    def test_remove_multiple_monsters(self):
        """Test Case 1: Multiple monsters on a single tile are all removed."""
        m1 = Monster(name="Rat", direction=2)
        m2 = Monster(name="Dragon", direction=2)
        tile = self._create_tile(100, 100, 7, monsters=[m1, m2])
        self.gamemap.set_tile(tile)

        # Action: Remove monsters from map
        changed, result = remove_monsters_in_map(self.gamemap, selection_only=False)

        # Assertions
        self.assertEqual(result.removed, 2)
        new_tile = changed.get((100, 100, 7))
        self.assertIsNotNone(new_tile)
        self.assertEqual(len(new_tile.monsters), 0)

    def test_preservation(self):
        """Test Case 2: Preservation of NPC, Spawn Markers, and Items."""
        m1 = Monster(name="Rat", direction=2)
        npc1 = Npc(name="Guide", direction=2)
        # Dummy spawn objects (center/radius don't matter for this test)
        spawn_m = MonsterSpawnArea(center=(100, 100, 7), radius=5)
        item1 = Item(id=1234)

        tile = self._create_tile(100, 100, 7, monsters=[m1], npc=npc1, spawn_monster=spawn_m, items=[item1])
        self.gamemap.set_tile(tile)

        # Action: Remove monsters
        changed, result = remove_monsters_in_map(self.gamemap, selection_only=False)

        # Assertions
        self.assertEqual(result.removed, 1)
        new_tile = changed.get((100, 100, 7))

        # Check preservation
        self.assertEqual(len(new_tile.monsters), 0)  # Monsters gone
        self.assertEqual(new_tile.npc, npc1)  # NPC preserved
        self.assertEqual(new_tile.spawn_monster, spawn_m)  # Spawn preserved
        self.assertEqual(len(new_tile.items), 1)
        self.assertEqual(new_tile.items[0], item1)  # Items preserved

    def test_selection_only(self):
        """Test Case 3: Only monsters on selected tiles are removed."""
        # Tile 1: Inside Selection (has monster)
        m1 = Monster(name="Rat", direction=2)
        t1 = self._create_tile(10, 10, 7, monsters=[m1])

        # Tile 2: Outside Selection (has monster)
        m2 = Monster(name="Dragon", direction=2)
        t2 = self._create_tile(20, 20, 7, monsters=[m2])

        self.gamemap.set_tile(t1)
        self.gamemap.set_tile(t2)

        # Define selection
        selection = {(10, 10, 7)}

        # Action: Remove with selection
        changed, result = remove_monsters_in_map(self.gamemap, selection_only=True, selection_tiles=selection)

        # Assertions
        self.assertEqual(result.removed, 1)  # Only 1 removed
        self.assertIn((10, 10, 7), changed)  # T1 changed
        self.assertNotIn((20, 20, 7), changed)  # T2 NOT changed

        # Verify T1 is empty
        self.assertEqual(len(changed[(10, 10, 7)].monsters), 0)

        # Verify T2 still has monster (in game map, since it wasn't returned in changed)
        # remove_monsters_in_map returns changed dict, doesn't mutate map in-place (conceptually, though logic layer reads map)
        # Actually logic layer reads map tiles. Let's check logic implies we return diff.
        # But we didn't mutate map, logic function returns `changed` dict.
        # So we trust T2 in `self.gamemap.tiles` is untouched.
        # BUT wait: logic layer iterates `game_map.tiles`. Does it mutate?
        # remove_monsters_in_map implementation:
        # `changed[key] = new_tile`
        # It does NOT set `game_map.tiles[key] = new_tile`.
        # So the map itself is untouched by the function, it returns a diff.
        # So checking self.gamemap.tiles for T2 is just checking initial state.

        tile2_after = self.gamemap.get_tile(20, 20, 7)
        self.assertEqual(len(tile2_after.monsters), 1)


if __name__ == "__main__":
    unittest.main()
