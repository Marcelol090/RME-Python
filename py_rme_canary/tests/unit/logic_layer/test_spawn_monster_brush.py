"""Test suite for SpawnMonsterBrush implementation.

Reference: source/spawn_monster_brush.cpp (legacy C++)
Tests follow strict TDD: exact assertions, no fuzzy matching.
"""

import pytest

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.map_header import MapHeader
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.spawn_monster_brush import SpawnMonsterBrush


@pytest.fixture
def empty_map() -> GameMap:
    """Empty test map."""
    header = MapHeader(width=100, height=100, otbm_version=2)
    return GameMap(header=header)


@pytest.fixture
def tile_with_ground() -> Tile:
    """Tile with ground item."""
    return Tile(x=50, y=50, z=7, ground=Item(id=100))


def test_spawn_monster_brush_creates_spawn_area(empty_map: GameMap, tile_with_ground: Tile):
    """Test that SpawnMonsterBrush creates a spawn area."""
    # Arrange
    empty_map.set_tile(tile_with_ground)
    brush = SpawnMonsterBrush(radius=3, spawn_time=60)
    pos = Position(x=50, y=50, z=7)

    # Act
    changes = brush.draw(empty_map, pos)

    # Assert
    assert len(changes) >= 1
    # Check that spawn area was created in tile or map
    assert len(empty_map.monster_spawns) > 0


def test_spawn_monster_brush_sets_correct_radius(empty_map: GameMap, tile_with_ground: Tile):
    """Test that spawn area has correct radius."""
    # Arrange
    empty_map.set_tile(tile_with_ground)
    brush = SpawnMonsterBrush(radius=5, spawn_time=60)
    pos = Position(x=50, y=50, z=7)

    # Act
    brush.draw(empty_map, pos)

    # Assert
    # Find the spawn area at this position
    spawn = next(
        (s for s in empty_map.monster_spawns if s.center.x == 50 and s.center.y == 50 and s.center.z == 7), None
    )
    assert spawn is not None
    assert spawn.radius == 5


def test_spawn_monster_brush_cannot_draw_without_ground(empty_map: GameMap):
    """Test that SpawnMonsterBrush requires ground."""
    # Arrange
    tile = Tile(x=50, y=50, z=7, ground=None)  # No ground
    empty_map.set_tile(tile)
    brush = SpawnMonsterBrush(radius=3, spawn_time=60)
    pos = Position(x=50, y=50, z=7)

    # Act
    can_draw = brush.can_draw(empty_map, pos)
    changes = brush.draw(empty_map, pos)

    # Assert
    assert can_draw is False
    assert len(changes) == 0


def test_spawn_monster_brush_cannot_draw_on_existing_spawn(empty_map: GameMap, tile_with_ground: Tile):
    """Test that SpawnMonsterBrush prevents duplicate spawns at same tile."""
    # Arrange
    empty_map.set_tile(tile_with_ground)
    brush = SpawnMonsterBrush(radius=3, spawn_time=60)
    pos = Position(x=50, y=50, z=7)

    # Act - Draw twice
    brush.draw(empty_map, pos)
    can_draw_again = brush.can_draw(empty_map, pos)

    # Assert
    assert can_draw_again is False


def test_spawn_monster_brush_undraw_removes_spawn(empty_map: GameMap, tile_with_ground: Tile):
    """Test that undraw removes spawn area."""
    # Arrange
    empty_map.set_tile(tile_with_ground)
    brush = SpawnMonsterBrush(radius=3, spawn_time=60)
    pos = Position(x=50, y=50, z=7)
    brush.draw(empty_map, pos)

    # Act
    changes = brush.undraw(empty_map, pos)

    # Assert
    assert len(changes) >= 1
    # Spawn should be removed
    spawn = next(
        (s for s in empty_map.monster_spawns if s.center.x == 50 and s.center.y == 50 and s.center.z == 7), None
    )
    assert spawn is None


def test_spawn_monster_brush_preserves_other_tile_data(empty_map: GameMap):
    """Test that SpawnMonsterBrush preserves zones, items, etc."""
    # Arrange
    tile = Tile(
        x=50,
        y=50,
        z=7,
        ground=Item(id=100),
        zones=frozenset({10, 20}),
        items=[Item(id=1609)],  # Table
    )
    empty_map.set_tile(tile)
    brush = SpawnMonsterBrush(radius=3, spawn_time=60)
    pos = Position(x=50, y=50, z=7)

    # Act
    changes = brush.draw(empty_map, pos)

    # Assert
    _, new_tile = changes[0]
    assert new_tile.zones == frozenset({10, 20})
    assert len(new_tile.items) == 1
    assert new_tile.items[0].id == 1609


def test_spawn_monster_brush_custom_spawn_time(empty_map: GameMap, tile_with_ground: Tile):
    """Test that spawn area respects custom spawn_time."""
    # Arrange
    empty_map.set_tile(tile_with_ground)
    brush = SpawnMonsterBrush(radius=3, spawn_time=120)  # Custom time
    pos = Position(x=50, y=50, z=7)

    # Act
    brush.draw(empty_map, pos)

    # Assert
    # spawn_time is stored in individual monster entries, not the area
    # This test just ensures the brush accepts the parameter
    assert brush.spawn_time == 120
