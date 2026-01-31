"""Unit tests for EditorActions in tile_actions.py.

Tests undo/redo functionality for ModifyTileItemsAction, ToggleDoorAction,
and RotateItemAction.
"""

import pytest
from py_rme_canary.logic_layer.history.tile_actions import (
    ModifyTileItemsAction,
    Mod

ifyItemAction,
    ToggleDoorAction,
    RotateItemAction,
)
from py_rme_canary.logic_layer.game_map import GameMap
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.data.item import Item


@pytest.fixture
def game_map():
    """Create test game map."""
    gmap = GameMap(width=100, height=100, name="Test Map")
    return gmap


@pytest.fixture
def sample_tile():
    """Create sample tile with ground and items."""
    tile = Tile()
    tile.ground = Item(id=4526)  # Grass
    tile.items = [
        Item(id=2050),  # Torch
        Item(id=1234),  # Container
    ]
    return tile


class TestModifyTileItemsAction:
    """Test ModifyTileItemsAction for Browse Tile dialog."""

    def test_has_changes_when_different(self):
        """Test has_changes returns True when items differ."""
        action = ModifyTileItemsAction(
            position=(10, 10, 7),
            old_ground=Item(id=100),
            old_items=[Item(id=200)],
            new_ground=Item(id=101),  # Different
            new_items=[Item(id=201)],  # Different
        )
        assert action.has_changes() is True

    def test_has_changes_when_same(self):
        """Test has_changes returns False when items same."""
        ground = Item(id=100)
        items = [Item(id=200)]
        action = ModifyTileItemsAction(
            position=(10, 10, 7),
            old_ground=ground,
            old_items=items,
            new_ground=ground,
            new_items=items,
        )
        assert action.has_changes() is False

    def test_redo_applies_changes(self, game_map):
        """Test redo applies new state to tile."""
        # Create tile with old state
        tile = Tile()
        tile.ground = Item(id=100)
        tile.items = [Item(id=200)]
        game_map.set_tile(10, 10, 7, tile)

        # Create action
        new_ground = Item(id=101)
        new_items = [Item(id=201), Item(id=202)]
        action = ModifyTileItemsAction(
            position=(10, 10, 7),
            old_ground=tile.ground,
            old_items=list(tile.items),
            new_ground=new_ground,
            new_items=new_items,
        )

        # Apply redo
        action.redo(game_map)

        # Verify changes
        updated_tile = game_map.get_tile(10, 10, 7)
        assert updated_tile.ground.id == 101
        assert len(updated_tile.items) == 2
        assert updated_tile.items[0].id == 201
        assert updated_tile.items[1].id == 202

    def test_undo_reverts_changes(self, game_map):
        """Test undo reverts to old state."""
        # Setup
        tile = Tile()
        old_ground = Item(id=100)
        old_items = [Item(id=200)]
        tile.ground = old_ground
        tile.items = list(old_items)
        game_map.set_tile(10, 10, 7, tile)

        action = ModifyTileItemsAction(
            position=(10, 10, 7),
            old_ground=old_ground,
            old_items=old_items,
            new_ground=Item(id=101),
            new_items=[Item(id=201)],
        )

        # Apply redo then undo
        action.redo(game_map)
        action.undo(game_map)

        # Verify reverted
        reverted_tile = game_map.get_tile(10, 10, 7)
        assert reverted_tile.ground.id == 100
        assert len(reverted_tile.items) == 1
        assert reverted_tile.items[0].id == 200

    def test_describe_returns_label(self):
        """Test describe returns human-readable label."""
        action = ModifyTileItemsAction(
            position=(50, 75, 7),
            old_ground=None,
            old_items=[],
            new_ground=Item(id=100),
            new_items=[],
        )
        description = action.describe()
        assert "50" in description
        assert "75" in description
        assert "7" in description


class TestToggleDoorAction:
    """Test ToggleDoorAction for door open/close with undo."""

    def test_redo_changes_door_id(self, game_map):
        """Test redo changes item ID to new state."""
        # Create tile with closed door
        tile = Tile()
        tile.items = [Item(id=1209)]  # Closed door
        game_map.set_tile(10, 10, 7, tile)

        action = ToggleDoorAction(
            position=(10, 10, 7),
            item_index=0,
            old_id=1209,
            new_id=1210,  # Open door
        )

        action.redo(game_map)

        updated_tile = game_map.get_tile(10, 10, 7)
        assert updated_tile.items[0].id == 1210

    def test_undo_reverts_door_id(self, game_map):
        """Test undo reverts door to original ID."""
        tile = Tile()
        tile.items = [Item(id=1209)]
        game_map.set_tile(10, 10, 7, tile)

        action = ToggleDoorAction(
            position=(10, 10, 7),
            item_index=0,
            old_id=1209,
            new_id=1210,
        )

        action.redo(game_map)
        action.undo(game_map)

        reverted_tile = game_map.get_tile(10, 10, 7)
        assert reverted_tile.items[0].id == 1209

    def test_toggle_ground_item(self, game_map):
        """Test toggling door when it's the ground item."""
        tile = Tile()
        tile.ground = Item(id=1209)
        game_map.set_tile(10, 10, 7, tile)

        action = ToggleDoorAction(
            position=(10, 10, 7),
            item_index=-1,  # Ground item
            old_id=1209,
            new_id=1210,
        )

        action.redo(game_map)

        updated_tile = game_map.get_tile(10, 10, 7)
        assert updated_tile.ground.id == 1210

    def test_describe_labels_door_action(self):
        """Test describe returns descriptive label."""
        action = ToggleDoorAction(
            position=(10, 10, 7),
            item_index=0,
            old_id=1209,
            new_id=1210,
        )
        description = action.describe()
        # Should mention "door" and position
        assert "door" in description.lower() or "10" in description


class TestRotateItemAction:
    """Test RotateItemAction for item rotation with undo."""

    def test_redo_rotates_item(self, game_map):
        """Test redo changes item to next rotation."""
        tile = Tile()
        tile.items = [Item(id=2050)]  # Torch
        game_map.set_tile(10, 10, 7, tile)

        action = RotateItemAction(
            position=(10, 10, 7),
            item_index=0,
            old_id=2050,
            new_id=2051,  # Next orientation
        )

        action.redo(game_map)

        updated_tile = game_map.get_tile(10, 10, 7)
        assert updated_tile.items[0].id == 2051

    def test_undo_reverts_rotation(self, game_map):
        """Test undo reverts item to original orientation."""
        tile = Tile()
        tile.items = [Item(id=2050)]
        game_map.set_tile(10, 10, 7, tile)

        action = RotateItemAction(
            position=(10, 10, 7),
            item_index=0,
            old_id=2050,
            new_id=2051,
        )

        action.redo(game_map)
        action.undo(game_map)

        reverted_tile = game_map.get_tile(10, 10, 7)
        assert reverted_tile.items[0].id == 2050

    def test_multiple_rotations_in_sequence(self, game_map):
        """Test rotating item multiple times."""
        tile = Tile()
        tile.items = [Item(id=2050)]
        game_map.set_tile(10, 10, 7, tile)

        # Rotate 4 times
        actions = [
            RotateItemAction((10, 10, 7), 0, 2050, 2051),
            RotateItemAction((10, 10, 7), 0, 2051, 2052),
            RotateItemAction((10, 10, 7), 0, 2052, 2053),
            RotateItemAction((10, 10, 7), 0, 2053, 2050),  # Back to start
        ]

        for action in actions:
            action.redo(game_map)

        # Should be back to original
        final_tile = game_map.get_tile(10, 10, 7)
        assert final_tile.items[0].id == 2050

    def test_has_changes_detection(self):
        """Test has_changes correctly detects ID change."""
        action = RotateItemAction(
            position=(10, 10, 7),
            item_index=0,
            old_id=2050,
            new_id=2051,
        )
        assert action.has_changes() is True

        action_no_change = RotateItemAction(
            position=(10, 10, 7),
            item_index=0,
            old_id=2050,
            new_id=2050,  # Same ID
        )
        assert action_no_change.has_changes() is False


class TestModifyItemAction:
    """Test ModifyItemAction for single item property changes."""

    def test_modify_action_id(self, game_map):
        """Test modifying item's action_id property."""
        tile = Tile()
        item = Item(id=1234)
        item.action_id = 0
        tile.items = [item]
        game_map.set_tile(10, 10, 7, tile)

        action = ModifyItemAction(
            position=(10, 10, 7),
            item_index=0,
            property_name="action_id",
            old_value=0,
            new_value=100,
        )

        action.redo(game_map)

        updated_tile = game_map.get_tile(10, 10, 7)
        assert updated_tile.items[0].action_id == 100

    def test_undo_restores_property(self, game_map):
        """Test undo restores original property value."""
        tile = Tile()
        item = Item(id=1234)
        item.unique_id = 0
        tile.items = [item]
        game_map.set_tile(10, 10, 7, tile)

        action = ModifyItemAction(
            position=(10, 10, 7),
            item_index=0,
            property_name="unique_id",
            old_value=0,
            new_value=999,
        )

        action.redo(game_map)
        action.undo(game_map)

        reverted_tile = game_map.get_tile(10, 10, 7)
        assert reverted_tile.items[0].unique_id == 0


# Integration test
class TestEditorActions Integration:
    """Integration tests combining multiple actions."""

    def test_multiple_actions_with_undo_stack(self, game_map):
        """Test multiple actions with undo in sequence."""
        # Create tile
        tile = Tile()
        tile.ground = Item(id=100)
        tile.items = [Item(id=1209)]  # Closed door
        game_map.set_tile(10, 10, 7, tile)

        # Action 1: Toggle door
        action1 = ToggleDoorAction((10, 10, 7), 0, 1209, 1210)
        action1.redo(game_map)
        assert game_map.get_tile(10, 10, 7).items[0].id == 1210

        # Action 2: Add item
        action2 = ModifyTileItemsAction(
            (10, 10, 7),
            old_ground=Item(id=100),
            old_items=[Item(id=1210)],
            new_ground=Item(id=100),
            new_items=[Item(id=1210), Item(id=2050)],  # Add torch
        )
        action2.redo(game_map)
        assert len(game_map.get_tile(10, 10, 7).items) == 2

        # Undo action 2
        action2.undo(game_map)
        assert len(game_map.get_tile(10, 10, 7).items) == 1

        # Undo action 1
        action1.undo(game_map)
        assert game_map.get_tile(10, 10, 7).items[0].id == 1209


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
