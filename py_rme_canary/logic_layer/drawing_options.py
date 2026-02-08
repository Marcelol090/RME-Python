"""Drawing options configuration.

This module provides a Qt-free dataclass that stores all rendering-layer toggles.
The class mirrors the legacy C++ DrawingOptions struct from map_drawer.h.

Architecture Notes:
-------------------
- This lives in logic_layer because it contains no Qt imports
- vis_layer components observe and mutate this via a shared instance
- The MapCanvas reads these flags to decide what to render
- Menu/toolbar actions in vis_layer modify these flags and trigger repaints
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto

from py_rme_canary.logic_layer.settings import LIGHT_PRESETS, LightSettings


class TransparencyMode(Enum):
    """Transparency rendering mode for floors/items."""

    NONE = auto()
    FLOORS = auto()
    ITEMS = auto()
    BOTH = auto()


@dataclass(slots=True)
class DrawingOptions:
    """Configuration state for map rendering toggles.

    This mirrors the C++ DrawingOptions struct from source/map_drawer.h.
    All fields default to sensible values matching the legacy editor's defaults.

    Attributes
    ----------
    Grid & Basic Display
    --------------------
    show_grid : int
        Grid visibility level (0=off, 1=visible, 2=dense). Legacy uses int for modes.
    show_all_floors : bool
        Whether to render all floors (underground stacking).
    show_shade : bool
        Whether to render shade overlay for current floor.

    Transparency
    ------------
    transparent_floors : bool
        Render floors below with transparency.
    transparent_items : bool
        Render items with transparency.

    Creatures & Spawns
    ------------------
    show_monsters : bool
        Render monster graphics on map.
    show_spawns_monster : bool
        Show monster spawn areas/indicators.
    show_npcs : bool
        Render NPC graphics on map.
    show_spawns_npc : bool
        Show NPC spawn areas/indicators.

    Map Elements
    ------------
    show_houses : bool
        Highlight house boundaries and IDs.
    show_special_tiles : bool
        Show special tile markers (PZ, PVP, etc.).
    show_items : bool
        Render items on tiles.

    Indicators & Overlays
    ---------------------
    show_hooks : bool
        Show wall hook indicators.
    show_pickupables : bool
        Show pickupable item indicators.
    show_moveables : bool
        Show moveable item indicators.
    show_avoidables : bool
        Show avoidable/blocking indicators.
    show_blocking : bool
        Show pathfinding blocking overlay.
    show_pathing : bool
        Show pathing/walkability overlay.
    highlight_items : bool
        Highlight items with special border.
    show_tooltips : bool
        Show item tooltips on hover.

    Visualization Modes
    -------------------
    show_as_minimap : bool
        Render as minimap colors only (no sprites).
    show_only_colors : bool
        Show only tile flag colors.
    show_only_modified : bool
        Only render tiles marked as modified.

    Lights
    ------
    show_lights : bool
        Render in-game light effects.
    show_light_strength : bool
        Show light strength values.

    Client View
    -----------
    show_ingame_box : bool
        Show client viewport box indicator.
    show_preview : bool
        Enable preview rendering (animated sprites, etc.).

    Internal State
    --------------
    ingame : bool
        Whether we're in "ingame" rendering mode (screenshot capture).
    dragging : bool
        Whether a drag operation is in progress.
    hide_items_when_zoomed : bool
        Hide items when zoomed out beyond threshold.
    """

    # Grid & Basic Display
    show_grid: int = 1
    show_all_floors: bool = True
    show_shade: bool = True

    # Transparency
    transparent_floors: bool = False
    transparent_items: bool = False

    # Creatures & Spawns
    show_monsters: bool = True
    show_spawns_monster: bool = True
    show_npcs: bool = True
    show_spawns_npc: bool = True

    # Map Elements
    show_houses: bool = True
    show_special_tiles: bool = True
    show_items: bool = True

    # Indicators & Overlays
    show_hooks: bool = False
    show_pickupables: bool = False
    show_moveables: bool = False
    show_avoidables: bool = False
    show_blocking: bool = False
    show_pathing: bool = False
    highlight_items: bool = False
    show_tooltips: bool = False

    # Visualization Modes
    show_as_minimap: bool = False
    show_only_colors: bool = False
    show_only_modified: bool = False
    show_client_ids: bool = False

    # Lights
    show_lights: bool = False
    show_light_strength: bool = True
    light_settings: LightSettings = field(default_factory=lambda: LIGHT_PRESETS["editor_default"])

    # Client View
    show_ingame_box: bool = False
    show_preview: bool = False

    # Internal State
    ingame: bool = False
    dragging: bool = False
    hide_items_when_zoomed: bool = True

    # Change notification callback (set by vis_layer coordinator)
    _on_change: Callable[[], None] | None = field(default=None, repr=False, compare=False)

    def set_default(self) -> None:
        """Reset all options to their default values.

        Mirrors C++ DrawingOptions::SetDefault().
        """
        self.transparent_floors = False
        self.transparent_items = False
        self.show_ingame_box = False
        self.show_lights = False
        self.show_light_strength = True
        self.light_settings = LIGHT_PRESETS["editor_default"]
        self.ingame = False
        self.dragging = False

        self.show_grid = 1
        self.show_all_floors = True
        self.show_monsters = True
        self.show_spawns_monster = True
        self.show_npcs = True
        self.show_spawns_npc = True
        self.show_houses = True
        self.show_shade = True
        self.show_special_tiles = True
        self.show_items = True

        self.highlight_items = False
        self.show_blocking = False
        self.show_tooltips = False
        self.show_as_minimap = False
        self.show_only_colors = False
        self.show_only_modified = False
        self.show_client_ids = False
        self.show_preview = False
        self.show_hooks = False
        self.show_pickupables = False
        self.show_moveables = False
        self.show_avoidables = False
        self.hide_items_when_zoomed = True

        self._notify_change()

    def set_ingame(self) -> None:
        """Set options for in-game screenshot mode.

        Mirrors C++ DrawingOptions::SetIngame().
        """
        self.transparent_floors = False
        self.transparent_items = False
        self.show_ingame_box = False
        self.show_lights = False
        self.show_light_strength = False
        self.light_settings = LIGHT_PRESETS["editor_default"]
        self.ingame = True
        self.dragging = False

        self.show_grid = 0
        self.show_all_floors = True
        self.show_monsters = True
        self.show_spawns_monster = False
        self.show_npcs = True
        self.show_spawns_npc = False
        self.show_houses = False
        self.show_shade = False
        self.show_special_tiles = False
        self.show_items = True

        self.highlight_items = False
        self.show_blocking = False
        self.show_tooltips = False
        self.show_as_minimap = False
        self.show_only_colors = False
        self.show_only_modified = False
        self.show_client_ids = False
        self.show_preview = False
        self.show_hooks = False
        self.show_pickupables = False
        self.show_moveables = False
        self.show_avoidables = False
        self.hide_items_when_zoomed = False

        self._notify_change()

    def is_only_colors(self) -> bool:
        """Check if we're in colors-only rendering mode.

        Mirrors C++ DrawingOptions::isOnlyColors().
        """
        return self.show_as_minimap or self.show_only_colors

    def is_tile_indicators(self) -> bool:
        """Check if any tile indicator overlays are enabled.

        Mirrors C++ DrawingOptions::isTileIndicators().
        """
        if self.is_only_colors():
            return False
        return (
            self.show_pickupables
            or self.show_moveables
            or self.show_houses
            or self.show_spawns_monster
            or self.show_spawns_npc
        )

    def is_tooltips(self) -> bool:
        """Check if tooltips should be rendered.

        Mirrors C++ DrawingOptions::isTooltips().
        """
        return self.show_tooltips and not self.is_only_colors()

    def _notify_change(self) -> None:
        """Notify listeners that options have changed."""
        if self._on_change is not None:
            self._on_change()

    # Convenience setters that trigger change notification
    def set_show_grid(self, value: int) -> None:
        self.show_grid = int(value)
        self._notify_change()

    def toggle_grid(self) -> None:
        """Cycle grid visibility: 0 -> 1 -> 0."""
        self.show_grid = 0 if self.show_grid else 1
        self._notify_change()

    def set_show_shade(self, value: bool) -> None:
        self.show_shade = bool(value)
        self._notify_change()

    def set_show_all_floors(self, value: bool) -> None:
        self.show_all_floors = bool(value)
        self._notify_change()

    def set_show_monsters(self, value: bool) -> None:
        self.show_monsters = bool(value)
        self._notify_change()

    def set_show_spawns_monster(self, value: bool) -> None:
        self.show_spawns_monster = bool(value)
        self._notify_change()

    def set_show_npcs(self, value: bool) -> None:
        self.show_npcs = bool(value)
        self._notify_change()

    def set_show_spawns_npc(self, value: bool) -> None:
        self.show_spawns_npc = bool(value)
        self._notify_change()

    def set_show_houses(self, value: bool) -> None:
        self.show_houses = bool(value)
        self._notify_change()

    def set_show_items(self, value: bool) -> None:
        self.show_items = bool(value)
        self._notify_change()

    def set_show_hooks(self, value: bool) -> None:
        self.show_hooks = bool(value)
        self._notify_change()

    def set_show_pickupables(self, value: bool) -> None:
        self.show_pickupables = bool(value)
        self._notify_change()

    def set_show_moveables(self, value: bool) -> None:
        self.show_moveables = bool(value)
        self._notify_change()

    def set_show_avoidables(self, value: bool) -> None:
        self.show_avoidables = bool(value)
        self._notify_change()

    def set_show_lights(self, value: bool) -> None:
        self.show_lights = bool(value)
        if self.show_lights:
            if not self.light_settings.enabled:
                self.light_settings = LIGHT_PRESETS["twilight"]
        else:
            self.light_settings = LIGHT_PRESETS["editor_default"]
        self._notify_change()

    def set_light_settings(self, settings: LightSettings, *, notify: bool = True) -> None:
        """Set the current light rendering configuration."""

        self.light_settings = settings
        if notify:
            self._notify_change()

    def set_show_as_minimap(self, value: bool) -> None:
        self.show_as_minimap = bool(value)
        self._notify_change()

    def set_show_only_modified(self, value: bool) -> None:
        self.show_only_modified = bool(value)
        self._notify_change()

    def set_show_tooltips(self, value: bool) -> None:
        self.show_tooltips = bool(value)
        self._notify_change()

    def set_show_preview(self, value: bool) -> None:
        self.show_preview = bool(value)
        self._notify_change()

    def set_transparent_floors(self, value: bool) -> None:
        self.transparent_floors = bool(value)
        self._notify_change()

    def set_transparent_items(self, value: bool) -> None:
        self.transparent_items = bool(value)
        self._notify_change()
