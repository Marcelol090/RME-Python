"""Test suite for HouseBrush implementation.

Reference: source/house_brush.cpp (legacy C++)
Tests follow strict TDD: exact assertions, no fuzzy matching.
"""

import pytest

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.map_header import MapHeader
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.house_brush import HouseBrush


@pytest.fixture
def empty_map() -> GameMap:
    """Empty test map."""
    header = MapHeader(width=100, height=100, otbm_version=2)
    return GameMap(header=header)


@pytest.fixture
def sample_house() -> House:
    """Sample house for testing."""
    return House(id=1001, name="Test House", rent=1000)


@pytest.fixture
def tile_with_ground() -> Tile:
    """Tile with ground item."""
    return Tile(
        x=50,
        y=50,
        z=7,
        ground=Item(id=100),  # Grass
    )


def test_house_brush_sets_house_id(empty_map: GameMap, sample_house: House, tile_with_ground: Tile):
    """Test that HouseBrush sets house_id on tile."""
    # Arrange
    empty_map.set_tile(tile_with_ground)
    brush = HouseBrush(house_id=sample_house.id, house_name=sample_house.name)
    pos = Position(x=50, y=50, z=7)

    # Act
    changes = brush.draw(empty_map, pos)

    # Assert
    assert len(changes) == 1
    _, new_tile = changes[0]
    assert new_tile.house_id == 1001  # Exact value


def test_house_brush_sets_pz_flag(empty_map: GameMap, sample_house: House, tile_with_ground: Tile):
    """Test that HouseBrush sets Protection Zone flag."""
    # Arrange
    empty_map.set_tile(tile_with_ground)
    brush = HouseBrush(house_id=sample_house.id, house_name=sample_house.name)
    pos = Position(x=50, y=50, z=7)

    # Act
    changes = brush.draw(empty_map, pos)

    # Assert
    assert len(changes) == 1
    _, new_tile = changes[0]
    assert (new_tile.map_flags & 0x01) == 0x01  # PZ flag is bit 0


def test_house_brush_clears_old_house(empty_map: GameMap, tile_with_ground: Tile):
    """Test that HouseBrush switches house IDs correctly."""
    # Arrange
    old_tile = Tile(
        x=50,
        y=50,
        z=7,
        ground=Item(id=100),
        house_id=999,  # Old house
        map_flags=0x01,  # PZ already set
    )
    empty_map.set_tile(old_tile)
    brush = HouseBrush(house_id=1001, house_name="New House")
    pos = Position(x=50, y=50, z=7)

    # Act
    changes = brush.draw(empty_map, pos)

    # Assert
    assert len(changes) == 1
    _, new_tile = changes[0]
    assert new_tile.house_id == 1001  # New house ID
    assert (new_tile.map_flags & 0x01) == 0x01  # PZ still set


def test_house_brush_auto_assigns_door_id(empty_map: GameMap, sample_house: House):
    """Test that HouseBrush auto-assigns door IDs."""
    # Arrange
    door_item = Item(id=1209, house_door_id=0)  # Door without ID
    tile = Tile(
        x=50,
        y=50,
        z=7,
        ground=Item(id=100),
        items=[door_item],
    )
    empty_map.set_tile(tile)
    brush = HouseBrush(house_id=1001, house_name="Test House", auto_assign_door_id=True)
    pos = Position(x=50, y=50, z=7)

    # Act
    changes = brush.draw(empty_map, pos)

    # Assert
    assert len(changes) == 1
    _, new_tile = changes[0]
    assert len(new_tile.items) == 1
    assert new_tile.items[0].house_door_id != 0  # Door ID assigned


def test_house_brush_removes_loose_items(empty_map: GameMap, sample_house: House):
    """Test that HouseBrush removes loose (moveable) items."""
    # Arrange
    loose_item = Item(id=2148)  # Gold coin (moveable)
    fixed_item = Item(id=1609)  # Table (not moveable)
    tile = Tile(
        x=50,
        y=50,
        z=7,
        ground=Item(id=100),
        items=[loose_item, fixed_item],
    )
    empty_map.set_tile(tile)
    brush = HouseBrush(house_id=1001, house_name="Test House", remove_loose_items=True)
    pos = Position(x=50, y=50, z=7)

    # Act
    changes = brush.draw(empty_map, pos)

    # Assert
    assert len(changes) == 1
    _, new_tile = changes[0]
    # Only fixed item should remain
    assert len(new_tile.items) == 1
    assert new_tile.items[0].id == 1609


def test_house_brush_undraw_clears_house(empty_map: GameMap):
    """Test that undraw clears all house data."""
    # Arrange
    door_item = Item(id=1209, house_door_id=123)
    tile = Tile(
        x=50,
        y=50,
        z=7,
        ground=Item(id=100),
        house_id=1001,
        map_flags=0x01,  # PZ flag
        items=[door_item],
    )
    empty_map.set_tile(tile)
    brush = HouseBrush(house_id=1001, house_name="Test House")
    pos = Position(x=50, y=50, z=7)

    # Act
    changes = brush.undraw(empty_map, pos)

    # Assert
    assert len(changes) == 1
    _, new_tile = changes[0]
    assert new_tile.house_id is None  # House cleared
    assert (new_tile.map_flags & 0x01) == 0  # PZ flag cleared
    assert new_tile.items[0].house_door_id == 0  # Door ID cleared


def test_house_brush_cannot_draw_without_ground(empty_map: GameMap, sample_house: House):
    """Test that HouseBrush requires ground."""
    # Arrange
    tile = Tile(x=50, y=50, z=7, ground=None)  # No ground
    empty_map.set_tile(tile)
    brush = HouseBrush(house_id=sample_house.id, house_name=sample_house.name)
    pos = Position(x=50, y=50, z=7)

    # Act
    can_draw = brush.can_draw(empty_map, pos)
    changes = brush.draw(empty_map, pos)

    # Assert
    assert can_draw is False
    assert len(changes) == 0


def test_house_brush_can_draw_returns_true_with_ground(empty_map: GameMap, sample_house: House, tile_with_ground: Tile):
    """Test that can_draw returns True when ground exists."""
    # Arrange
    empty_map.set_tile(tile_with_ground)
    brush = HouseBrush(house_id=sample_house.id, house_name=sample_house.name)
    pos = Position(x=50, y=50, z=7)

    # Act
    can_draw = brush.can_draw(empty_map, pos)

    # Assert
    assert can_draw is True


def test_house_brush_preserves_other_tile_data(empty_map: GameMap, sample_house: House):
    """Test that HouseBrush preserves zones, monsters, etc."""
    # Arrange
    from py_rme_canary.core.data.creature import Monster

    tile = Tile(
        x=50,
        y=50,
        z=7,
        ground=Item(id=100),
        zones=frozenset({10, 20}),
        monsters=[Monster(name="Rat", direction=2)],
    )
    empty_map.set_tile(tile)
    brush = HouseBrush(house_id=sample_house.id, house_name=sample_house.name)
    pos = Position(x=50, y=50, z=7)

    # Act
    changes = brush.draw(empty_map, pos)

    # Assert
    _, new_tile = changes[0]
    assert new_tile.zones == frozenset({10, 20})
    assert len(new_tile.monsters) == 1
    assert new_tile.monsters[0].name == "Rat"
