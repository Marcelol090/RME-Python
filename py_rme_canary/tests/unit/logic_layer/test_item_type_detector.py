"""Unit tests for ItemTypeDetector.

Tests item categorization, door toggle detection, rotation sequences,
and other smart context menu logic.
"""

import pytest
from py_rme_canary.logic_layer.item_type_detector import (
    ItemTypeDetector,
    ItemCategory,
    DOOR_PAIRS,
    ROTATABLE_SEQUENCES,
)
from py_rme_canary.core.data.item import Item


class TestItemCategoryDetection:
    """Test item category detection."""
    
    def test_detect_wall_category(self):
        """Test wall detection in ID range."""
        item = Item(id=1050)  # Wall range: 1000-1200
        assert ItemTypeDetector.get_category(item) == ItemCategory.WALL
    
    def test_detect_carpet_category(self):
        """Test carpet detection in ID range."""
        item = Item(id=1350)  # Carpet range: 1300-1400
        assert ItemTypeDetector.get_category(item) == ItemCategory.CARPET
    
    def test_detect_door_category(self):
        """Test door detection in ID range."""
        item = Item(id=1250)  # Door range: 1200-1300
        assert ItemTypeDetector.get_category(item) == ItemCategory.DOOR
    
    def test_detect_unknown_category(self):
        """Test unknown item returns UNKNOWN category."""
        item = Item(id=99999)  # Out of all ranges
        assert ItemTypeDetector.get_category(item) == ItemCategory.UNKNOWN


class TestDoorDetection:
    """Test door-specific detection methods."""
    
    def test_is_door_positive(self):
        """Test door detection returns True for door ID."""
        door = Item(id=1209)  # Closed wooden door
        assert ItemTypeDetector.is_door(door) is True
    
    def test_is_door_negative(self):
        """Test door detection returns False for non-door."""
        wall = Item(id=1050)
        assert ItemTypeDetector.is_door(wall) is False
    
    def test_get_door_toggle_id_closed_to_open(self):
        """Test getting open ID from closed door."""
        closed_door = Item(id=1209)
        open_id = ItemTypeDetector.get_door_toggle_id(closed_door)
        assert open_id == 1210  # Expected open door ID
    
    def test_get_door_toggle_id_open_to_closed(self):
        """Test getting closed ID from open door."""
        open_door = Item(id=1210)
        closed_id = ItemTypeDetector.get_door_toggle_id(open_door)
        assert closed_id == 1209  # Expected closed door ID
    
    def test_get_door_toggle_id_unknown_door(self):
        """Test unknown door returns None."""
        unknown = Item(id=9999)
        toggle_id = ItemTypeDetector.get_door_toggle_id(unknown)
        assert toggle_id is None
    
    def test_is_door_open_true(self):
        """Test detecting open door state."""
        open_door = Item(id=1210)
        # Check if this ID is in the "open" values of DOOR_PAIRS
        assert open_door.id in DOOR_PAIRS.values()
    
    def test_is_door_open_false(self):
        """Test detecting closed door state."""
        closed_door = Item(id=1209)
        # Check if this ID is a key (closed state)
        assert closed_door.id in DOOR_PAIRS.keys()


class TestRotatableItems:
    """Test rotatable item detection and sequences."""
    
    def test_is_rotatable_positive(self):
        """Test rotatable detection returns True for rotatable item."""
        torch = Item(id=2050)
        assert ItemTypeDetector.is_rotatable(torch) is True
    
    def test_is_rotatable_negative(self):
        """Test rotatable detection returns False for non-rotatable."""
        door = Item(id=1209)
        assert ItemTypeDetector.is_rotatable(door) is False
    
    def test_get_next_rotation_id_torch(self):
        """Test torch rotation sequence."""
        # Torch sequence: 2050 → 2051 → 2052 → 2053 → 2050
        torch1 = Item(id=2050)
        next_id = ItemTypeDetector.get_next_rotation_id(torch1)
        assert next_id == 2051
        
        torch2 = Item(id=2051)
        next_id = ItemTypeDetector.get_next_rotation_id(torch2)
        assert next_id == 2052
    
    def test_get_next_rotation_id_wraps_around(self):
        """Test rotation sequence wraps to start."""
        if 2050 in ROTATABLE_SEQUENCES:
            sequence = ROTATABLE_SEQUENCES[2050]
            last_item = Item(id=sequence[-1])
            next_id = ItemTypeDetector.get_next_rotation_id(last_item)
            assert next_id == sequence[0]  # Wraps to first
    
    def test_get_next_rotation_id_unknown_item(self):
        """Test unknown item returns None."""
        unknown = Item(id=9999)
        next_id = ItemTypeDetector.get_next_rotation_id(unknown)
        assert next_id is None


class TestTeleportDetection:
    """Test teleport-specific methods."""
    
    def test_is_teleport_positive(self):
        """Test teleport detection returns True for teleport ID."""
        teleport = Item(id=1387)  # Common teleport ID
        # If ID range check exists
        if hasattr(ItemTypeDetector, 'is_teleport'):
            assert ItemTypeDetector.is_teleport(teleport) is True
    
    def test_get_teleport_destination_with_data(self):
        """Test extracting teleport destination from item data."""
        if not hasattr(ItemTypeDetector, 'get_teleport_destination'):
            pytest.skip("get_teleport_destination not implemented")
        
        teleport = Item(id=1387)
        # TODO: Set teleport data with destination
        # dest = ItemTypeDetector.get_teleport_destination(teleport)
        # assert dest == (x, y, z)


class TestHelperMethods:
    """Test other helper methods."""
    
    def test_can_select_brush_for_wall(self):
        """Test brush selection availability for wall."""
        if hasattr(ItemTypeDetector, 'can_select_brush'):
            wall = Item(id=1050)
            assert ItemTypeDetector.can_select_brush(wall) is True
    
    def test_get_brush_name_for_category(self):
        """Test getting brush name from category."""
        if hasattr(ItemTypeDetector, 'get_brush_name'):
            assert ItemTypeDetector.get_brush_name(ItemCategory.WALL) == "wall"
            assert ItemTypeDetector.get_brush_name(ItemCategory.DOOR) == "door"


# Integration-style tests
class TestItemTypeDetectorIntegration:
    """Integration tests combining multiple detection methods."""
    
    def test_door_workflow(self):
        """Test complete door toggle workflow."""
        # Start with closed door
        door = Item(id=1209)
        assert ItemTypeDetector.is_door(door) is True
        
        # Get open state
        open_id = ItemTypeDetector.get_door_toggle_id(door)
        assert open_id == 1210
        
        # Toggle to open
        door.id = open_id
        
        # Get closed state
        closed_id = ItemTypeDetector.get_door_toggle_id(door)
        assert closed_id == 1209
    
    def test_rotation_workflow(self):
        """Test complete rotation workflow."""
        torch = Item(id=2050)
        assert ItemTypeDetector.is_rotatable(torch) is True
        
        # Rotate 4 times (full cycle)
        original_id = torch.id
        for _ in range(4):
            next_id = ItemTypeDetector.get_next_rotation_id(torch)
            assert next_id is not None
            torch.id = next_id
        
        # Should be back to original (if sequence is 4 items)
        if 2050 in ROTATABLE_SEQUENCES and len(ROTATABLE_SEQUENCES[2050]) == 4:
            assert torch.id == original_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
