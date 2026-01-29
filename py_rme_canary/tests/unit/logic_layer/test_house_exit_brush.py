"""Test suite for HouseExitBrush implementation.

Reference: source/house_exit_brush.cpp (legacy C++)
Tests follow strict TDD: exact assertions, no fuzzy matching.
"""

import pytest

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.map_header import MapHeader
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.house_exit_brush import HouseExitBrush


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
    return Tile(x=50, y=50, z=7, ground=Item(id=100))


def test_house_exit_brush_sets_exit_position(empty_map: GameMap, sample_house: House, tile_with_ground: Tile):
    """Test that HouseExitBrush sets house entry position."""
    # Arrange
    empty_map.set_tile(tile_with_ground)
    empty_map.houses[sample_house.id] = sample_house

    brush = HouseExitBrush(house_id=sample_house.id, house_name=sample_house.name)
    pos = Position(x=50, y=50, z=7)

    # Act
    changes = brush.draw(empty_map, pos)

    # Assert
    assert len(changes) == 1
    # Verify house entry was updated in map
    updated_house = empty_map.houses[sample_house.id]
    assert updated_house.entry is not None
    assert updated_house.entry.x == 50
    assert updated_house.entry.y == 50
    assert updated_house.entry.z == 7


def test_house_exit_brush_requires_house_tile(empty_map: GameMap, sample_house: House):
    """Test that HouseExitBrush requires tile to be part of house."""
    # Arrange
    tile = Tile(x=50, y=50, z=7, ground=Item(id=100), house_id=None)  # Not a house tile
    empty_map.set_tile(tile)
    empty_map.houses[sample_house.id] = sample_house

    brush = HouseExitBrush(house_id=sample_house.id, house_name=sample_house.name)
    pos = Position(x=50, y=50, z=7)

    # Act
    can_draw = brush.can_draw(empty_map, pos)

    # Assert
    assert can_draw is False


def test_house_exit_brush_can_draw_on_house_tile(empty_map: GameMap, sample_house: House):
    """Test that HouseExitBrush can draw on house tiles."""
    # Arrange
    tile = Tile(x=50, y=50, z=7, ground=Item(id=100), house_id=sample_house.id)
    empty_map.set_tile(tile)
    empty_map.houses[sample_house.id] = sample_house

    brush = HouseExitBrush(house_id=sample_house.id, house_name=sample_house.name)
    pos = Position(x=50, y=50, z=7)

    # Act
    can_draw = brush.can_draw(empty_map, pos)

    # Assert
    assert can_draw is True


def test_house_exit_brush_updates_existing_entry(empty_map: GameMap):
    """Test that HouseExitBrush updates existing entry position."""
    # Arrange
    old_entry = Position(x=10, y=10, z=7)
    house = House(id=1001, name="Test House", entry=old_entry)

    tile = Tile(x=50, y=50, z=7, ground=Item(id=100), house_id=house.id)
    empty_map.set_tile(tile)
    empty_map.houses[house.id] = house

    brush = HouseExitBrush(house_id=house.id, house_name=house.name)
    pos = Position(x=50, y=50, z=7)

    # Act
    brush.draw(empty_map, pos)

    # Assert
    updated_house = empty_map.houses[house.id]
    assert updated_house.entry.x == 50  # New position
    assert updated_house.entry.y == 50
    assert updated_house.entry.z == 7


def test_house_exit_brush_undraw_clears_entry(empty_map: GameMap):
    """Test that undraw clears house entry if position matches."""
    # Arrange
    entry = Position(x=50, y=50, z=7)
    house = House(id=1001, name="Test House", entry=entry)

    tile = Tile(x=50, y=50, z=7, ground=Item(id=100), house_id=house.id)
    empty_map.set_tile(tile)
    empty_map.houses[house.id] = house

    brush = HouseExitBrush(house_id=house.id, house_name=house.name)
    pos = Position(x=50, y=50, z=7)

    # Act
    brush.undraw(empty_map, pos)

    # Assert
    updated_house = empty_map.houses[house.id]
    assert updated_house.entry is None  # Entry cleared


def test_house_exit_brush_preserves_other_house_data(empty_map: GameMap):
    """Test that HouseExitBrush preserves rent, guildhall, etc."""
    # Arrange
    house = House(id=1001, name="Test House", rent=5000, guildhall=True, townid=1)

    tile = Tile(x=50, y=50, z=7, ground=Item(id=100), house_id=house.id)
    empty_map.set_tile(tile)
    empty_map.houses[house.id] = house

    brush = HouseExitBrush(house_id=house.id, house_name=house.name)
    pos = Position(x=50, y=50, z=7)

    # Act
    brush.draw(empty_map, pos)

    # Assert
    updated_house = empty_map.houses[house.id]
    assert updated_house.rent == 5000
    assert updated_house.guildhall is True
    assert updated_house.townid == 1
