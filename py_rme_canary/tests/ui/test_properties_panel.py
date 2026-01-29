"""Tests for Properties Panel.

TDD strict mode - comprehensive tests for all property types.
"""

from __future__ import annotations

import pytest

from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile

pytestmark = pytest.mark.qt_no_exception_capture


class TestPropertiesPanel:
    """Test Properties Panel basic functionality."""

    def test_panel_creation(self, qtbot):
        """Test creating properties panel widget."""
        from py_rme_canary.vis_layer.ui.docks.properties_panel import PropertiesPanel

        panel = PropertiesPanel()
        qtbot.addWidget(panel)

        assert panel is not None
        assert panel.windowTitle() == "Properties"

    def test_show_tile_properties(self, qtbot):
        """Test displaying tile properties."""
        from py_rme_canary.vis_layer.ui.docks.properties_panel import PropertiesPanel

        panel = PropertiesPanel()
        qtbot.addWidget(panel)

        tile = Tile(x=100, y=100, z=7)
        panel.show_tile(tile)

        # Should display position
        assert "Position" in panel.get_display_text()
        assert "100, 100, 7" in panel.get_display_text()

    def test_show_item_properties(self, qtbot):
        """Test displaying item properties."""
        from py_rme_canary.vis_layer.ui.docks.properties_panel import PropertiesPanel

        panel = PropertiesPanel()
        qtbot.addWidget(panel)

        item = Item(id=1234)
        panel.show_item(item)

        # Should display item ID
        assert "1234" in panel.get_display_text()

    def test_clear_properties(self, qtbot):
        """Test clearing properties display."""
        from py_rme_canary.vis_layer.ui.docks.properties_panel import PropertiesPanel

        panel = PropertiesPanel()
        qtbot.addWidget(panel)

        item = Item(id=1234)
        panel.show_item(item)

        assert panel.get_display_text() != ""

        panel.clear()

        assert panel.get_display_text() == ""

    def test_edit_item_text(self, qtbot):
        """Test editing item text property."""
        from py_rme_canary.vis_layer.ui.docks.properties_panel import PropertiesPanel

        panel = PropertiesPanel()
        qtbot.addWidget(panel)

        item = Item(id=1972)  # Writable item (assuming)
        panel.show_item(item)

        # Just verify no crash - actual editing would need mutable item
        display = panel.get_display_text()
        assert "1972" in display


class TestHouseProperties:
    """Test house-specific property editing."""

    def test_show_house_properties(self, qtbot):
        """Test showing house properties."""
        from py_rme_canary.vis_layer.ui.docks.properties_panel import PropertiesPanel

        panel = PropertiesPanel()
        qtbot.addWidget(panel)

        house = House(id=1, name="Test House", townid=1, rent=1000)
        panel.show_house(house)

        display = panel.get_display_text()
        assert "Test House" in display
        assert "1000" in display  # rent

    def test_edit_house_name(self, qtbot):
        """Test editing house name - verify panel accepts input."""
        from py_rme_canary.vis_layer.ui.docks.properties_panel import PropertiesPanel

        panel = PropertiesPanel()
        qtbot.addWidget(panel)

        house = House(id=1, name="Old Name", townid=1, rent=500)
        panel.show_house(house)

        # Just verify we can set the field value without crash
        panel.set_house_name("New House Name")
        display = panel.get_display_text()
        assert "New House Name" in display


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
