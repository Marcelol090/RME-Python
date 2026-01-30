"""Tests for selection operations."""

from __future__ import annotations

from py_rme_canary.core.data.creature import Monster, Npc
from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.operations.selection_operations import (
    count_monsters_in_selection,
    remove_duplicates_in_selection,
    search_items_in_selection,
)


def test_search_items_in_selection_finds_ground():
    """Test searching for ground item in selection."""
    header = MapHeader(width=100, height=100, otbm_version=2)
    game_map = GameMap(header=header)

    # Create tiles with specific ground
    tile1 = Tile(x=100, y=100, z=7, ground=Item(id=4526))
    tile2 = Tile(x=101, y=100, z=7, ground=Item(id=4527))
    tile3 = Tile(x=102, y=100, z=7, ground=Item(id=4526))

    game_map.set_tile(tile1)
    game_map.set_tile(tile2)
    game_map.set_tile(tile3)

    selection = {(100, 100, 7), (101, 100, 7), (102, 100, 7)}

    result = search_items_in_selection(game_map, item_id=4526, selection_tiles=selection)

    assert result.item_id == 4526
    assert result.count == 2
    assert (100, 100, 7) in result.positions
    assert (102, 100, 7) in result.positions


def test_count_monsters_in_selection():
    """Test counting monsters and NPCs in selection."""
    header = MapHeader(width=100, height=100, otbm_version=2)
    game_map = GameMap(header=header)

    # Create tiles with monsters and NPCs
    monster1 = Monster(name="Rat", direction=2)
    monster2 = Monster(name="Rat", direction=2)
    monster3 = Monster(name="Cat", direction=2)
    npc1 = Npc(name="Tom", direction=2)

    tile1 = Tile(x=100, y=100, z=7, monsters=[monster1])
    tile2 = Tile(x=101, y=100, z=7, monsters=[monster2, monster3])
    tile3 = Tile(x=102, y=100, z=7, npc=npc1)

    game_map.set_tile(tile1)
    game_map.set_tile(tile2)
    game_map.set_tile(tile3)

    selection = {(100, 100, 7), (101, 100, 7), (102, 100, 7)}

    result = count_monsters_in_selection(game_map, selection_tiles=selection)

    assert result.total_monsters == 3
    assert result.total_npcs == 1
    assert result.unique_monsters["Rat"] == 2
    assert result.unique_monsters["Cat"] == 1
    assert result.unique_npcs["Tom"] == 1


def test_remove_duplicates_in_selection():
    """Test removing duplicate items in selection."""
    header = MapHeader(width=100, height=100, otbm_version=2)
    game_map = GameMap(header=header)

    # Create tile with duplicate items
    tile1 = Tile(
        x=100,
        y=100,
        z=7,
        items=[
            Item(id=1234),
            Item(id=1234),  # duplicate
            Item(id=5678),
            Item(id=1234),  # another duplicate
        ],
    )

    game_map.set_tile(tile1)

    selection = {(100, 100, 7)}

    changed_tiles, result = remove_duplicates_in_selection(game_map, selection_tiles=selection)

    assert result.removed_count == 2
    assert result.tiles_modified == 1
    assert (100, 100, 7) in changed_tiles

    new_tile = changed_tiles[(100, 100, 7)]
    assert len(new_tile.items) == 2  # Only unique items remain
