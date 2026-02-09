"""Tests for DrawingOptions dataclass."""

from __future__ import annotations

from py_rme_canary.logic_layer.drawing_options import DrawingOptions, TransparencyMode
from py_rme_canary.logic_layer.settings import LIGHT_PRESETS


class TestDrawingOptions:
    """Tests for the DrawingOptions dataclass."""

    def test_default_values(self):
        """Test that default values match C++ DrawingOptions::SetDefault()."""
        opts = DrawingOptions()

        # Grid & Display
        assert opts.show_grid == 1
        assert opts.show_all_floors is True
        assert opts.show_shade is True

        # Creatures & Spawns
        assert opts.show_monsters is True
        assert opts.show_spawns_monster is True
        assert opts.show_npcs is True
        assert opts.show_spawns_npc is True

        # Map Elements
        assert opts.show_houses is True
        assert opts.show_special_tiles is True
        assert opts.show_items is True

        # Indicators
        assert opts.show_hooks is False
        assert opts.show_pickupables is False
        assert opts.show_moveables is False
        assert opts.show_avoidables is False
        assert opts.show_blocking is False

        # Modes
        assert opts.show_as_minimap is False
        assert opts.show_only_colors is False
        assert opts.show_only_modified is False
        assert opts.show_client_ids is False

        # Transparency
        assert opts.transparent_floors is False
        assert opts.transparent_items is False

    def test_set_default(self):
        """Test set_default() resets all values."""
        opts = DrawingOptions()

        # Modify some values
        opts.show_grid = 0
        opts.show_monsters = False
        opts.show_pickupables = True
        opts.show_client_ids = True

        # Reset
        opts.set_default()

        # Verify reset
        assert opts.show_grid == 1
        assert opts.show_monsters is True
        assert opts.show_pickupables is False
        assert opts.show_client_ids is False

    def test_set_ingame(self):
        """Test set_ingame() sets screenshot mode values."""
        opts = DrawingOptions()
        opts.set_ingame()

        # Core ingame flags
        assert opts.ingame is True
        assert opts.show_grid == 0
        assert opts.show_shade is False
        assert opts.show_spawns_monster is False
        assert opts.show_spawns_npc is False
        assert opts.show_houses is False
        assert opts.hide_items_when_zoomed is False
        assert opts.show_client_ids is False

        # Items still shown
        assert opts.show_items is True
        assert opts.show_monsters is True
        assert opts.show_npcs is True

    def test_show_lights_toggles_presets(self):
        """Show lights should enable/disable the default presets."""
        opts = DrawingOptions()

        opts.set_show_lights(True)
        assert opts.light_settings == LIGHT_PRESETS["twilight"]
        assert opts.show_lights is True

        opts.set_show_lights(False)
        assert opts.light_settings == LIGHT_PRESETS["editor_default"]
        assert opts.show_lights is False

    def test_set_light_settings_notify_flag(self):
        """set_light_settings should respect the notify flag."""
        opts = DrawingOptions()
        notifications: list[None] = []

        def on_change() -> None:
            notifications.append(None)

        opts._on_change = on_change
        opts.set_light_settings(LIGHT_PRESETS["night"], notify=False)
        assert len(notifications) == 0

        opts.set_light_settings(LIGHT_PRESETS["night"], notify=True)
        assert len(notifications) == 1

    def test_is_only_colors(self):
        """Test is_only_colors() helper method."""
        opts = DrawingOptions()

        # Default: not colors-only
        assert opts.is_only_colors() is False

        # Minimap mode
        opts.show_as_minimap = True
        assert opts.is_only_colors() is True

        opts.show_as_minimap = False
        assert opts.is_only_colors() is False

        # Show only colors mode
        opts.show_only_colors = True
        assert opts.is_only_colors() is True

    def test_is_tile_indicators(self):
        """Test is_tile_indicators() helper method."""
        opts = DrawingOptions()

        # Default has show_houses=True and show_spawns_monster=True, show_spawns_npc=True
        # which makes is_tile_indicators() return True by default
        # Let's disable all to test properly
        opts.show_houses = False
        opts.show_spawns_monster = False
        opts.show_spawns_npc = False
        assert opts.is_tile_indicators() is False

        # Enable pickupables
        opts.show_pickupables = True
        assert opts.is_tile_indicators() is True

        # In colors-only mode, no indicators
        opts.show_as_minimap = True
        assert opts.is_tile_indicators() is False

        opts.show_as_minimap = False

        # Enable moveables
        opts.show_pickupables = False
        opts.show_moveables = True
        assert opts.is_tile_indicators() is True

        # Houses also counts
        opts.show_moveables = False
        opts.show_houses = True
        assert opts.is_tile_indicators() is True

    def test_is_tooltips(self):
        """Test is_tooltips() helper method."""
        opts = DrawingOptions()

        # Default: no tooltips
        assert opts.is_tooltips() is False

        # Enable tooltips
        opts.show_tooltips = True
        assert opts.is_tooltips() is True

        # In colors-only mode, no tooltips
        opts.show_as_minimap = True
        assert opts.is_tooltips() is False

    def test_setter_methods(self):
        """Test convenience setter methods."""
        opts = DrawingOptions()

        opts.set_show_grid(0)
        assert opts.show_grid == 0

        opts.set_show_grid(1)
        assert opts.show_grid == 1

        opts.set_show_monsters(False)
        assert opts.show_monsters is False

        opts.set_show_pickupables(True)
        assert opts.show_pickupables is True

    def test_toggle_grid(self):
        """Test toggle_grid() cycles between 0 and 1."""
        opts = DrawingOptions()
        assert opts.show_grid == 1

        opts.toggle_grid()
        assert opts.show_grid == 0

        opts.toggle_grid()
        assert opts.show_grid == 1

    def test_change_notification(self):
        """Test that setters trigger change notification."""
        opts = DrawingOptions()
        changes = []

        def on_change():
            changes.append(True)

        opts._on_change = on_change

        # Setter should trigger notification
        opts.set_show_grid(0)
        assert len(changes) == 1

        opts.set_show_monsters(False)
        assert len(changes) == 2

        opts.toggle_grid()
        assert len(changes) == 3

        opts.set_default()
        assert len(changes) == 4

        opts.set_ingame()
        assert len(changes) == 5


class TestTransparencyMode:
    """Tests for the TransparencyMode enum."""

    def test_enum_values(self):
        """Test enum has expected values."""
        assert TransparencyMode.NONE is not None
        assert TransparencyMode.FLOORS is not None
        assert TransparencyMode.ITEMS is not None
        assert TransparencyMode.BOTH is not None

    def test_enum_distinct(self):
        """Test enum values are distinct."""
        assert TransparencyMode.NONE != TransparencyMode.FLOORS
        assert TransparencyMode.FLOORS != TransparencyMode.ITEMS
        assert TransparencyMode.ITEMS != TransparencyMode.BOTH
