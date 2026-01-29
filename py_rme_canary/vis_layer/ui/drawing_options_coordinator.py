"""Drawing options coordinator for Qt integration.

This module bridges the Qt-free DrawingOptions (logic_layer) with the Qt
editor state. It provides methods to:
- Sync DrawingOptions to editor attributes
- Sync editor attributes to DrawingOptions
- Connect menu action signals to DrawingOptions
- Trigger canvas repaints when options change
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.logic_layer.drawing_options import DrawingOptions
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class DrawingOptionsCoordinator:
    """Coordinates DrawingOptions state with Qt editor.

    This class acts as a bridge between the Qt-free DrawingOptions dataclass
    and the Qt-based editor. It handles:

    1. State synchronization (editor attrs <-> DrawingOptions)
    2. Change notification (options change -> canvas update)
    3. Menu action wiring (Qt actions <-> DrawingOptions setters)
    """

    def __init__(self, editor: "QtMapEditor", options: "DrawingOptions") -> None:
        """Initialize the coordinator.

        Parameters
        ----------
        editor : QtMapEditor
            The Qt editor instance.
        options : DrawingOptions
            The drawing options instance to coordinate.
        """
        self._editor = editor
        self._options = options

        # Set up change notification
        self._options._on_change = self._on_options_changed

    @property
    def options(self) -> "DrawingOptions":
        """Return the DrawingOptions instance."""
        return self._options

    def _on_options_changed(self) -> None:
        """Called when DrawingOptions fields change.

        Updates canvas to reflect new options.
        """
        try:
            self._editor.canvas.update()
        except Exception:
            pass

    def sync_from_editor(self) -> None:
        """Sync DrawingOptions from editor attributes.

        Reads the editor's view toggle attributes and updates DrawingOptions.
        """
        editor = self._editor
        opts = self._options

        # Grid
        opts.show_grid = 1 if getattr(editor, "show_grid", True) else 0

        # Transparency
        # (editor doesn't have separate attrs yet, use defaults)

        # Creatures & Spawns
        opts.show_monsters = bool(getattr(editor, "show_monsters", True))
        opts.show_spawns_monster = bool(getattr(editor, "show_monsters_spawns", True))
        opts.show_npcs = bool(getattr(editor, "show_npcs", True))
        opts.show_spawns_npc = bool(getattr(editor, "show_npcs_spawns", False))

        # Map Elements
        opts.show_houses = bool(getattr(editor, "show_houses_overlay", True))
        opts.show_special_tiles = bool(getattr(editor, "show_special", False))
        opts.show_items = True  # Always show items (controlled by minimap mode)

        # Indicators & Overlays
        opts.show_hooks = bool(getattr(editor, "show_wall_hooks", False))
        opts.show_pickupables = bool(getattr(editor, "show_pickupables", False))
        opts.show_moveables = bool(getattr(editor, "show_moveables", False))
        opts.show_avoidables = bool(getattr(editor, "show_avoidables", False))
        opts.show_pathing = bool(getattr(editor, "show_pathing", False))
        opts.highlight_items = bool(getattr(editor, "highlight_items", False))
        opts.show_tooltips = bool(getattr(editor, "show_tooltips", True))

        # Visualization Modes
        opts.show_as_minimap = bool(getattr(editor, "show_as_minimap", False))
        opts.show_only_colors = bool(getattr(editor, "only_show_colors", False))
        opts.show_only_modified = bool(getattr(editor, "only_show_modified", False))

        # View
        opts.show_shade = bool(getattr(editor, "show_shade", False))
        opts.show_all_floors = bool(getattr(editor, "show_all_floors", True))
        opts.show_lights = bool(getattr(editor, "show_lights", False))
        opts.show_ingame_box = bool(getattr(editor, "show_client_box", False))
        opts.show_preview = bool(getattr(editor, "show_preview", True))

    def sync_to_editor(self) -> None:
        """Sync editor attributes from DrawingOptions.

        Writes DrawingOptions values to editor attributes.
        """
        editor = self._editor
        opts = self._options

        # Grid
        editor.show_grid = bool(opts.show_grid)

        # Creatures & Spawns
        editor.show_monsters = opts.show_monsters
        editor.show_monsters_spawns = opts.show_spawns_monster
        editor.show_npcs = opts.show_npcs
        editor.show_npcs_spawns = opts.show_spawns_npc

        # Map Elements
        editor.show_houses_overlay = opts.show_houses
        editor.show_special = opts.show_special_tiles

        # Indicators & Overlays
        editor.show_wall_hooks = opts.show_hooks
        editor.show_pickupables = opts.show_pickupables
        editor.show_moveables = opts.show_moveables
        editor.show_avoidables = opts.show_avoidables
        editor.show_pathing = opts.show_pathing
        editor.highlight_items = opts.highlight_items
        editor.show_tooltips = opts.show_tooltips

        # Visualization Modes
        editor.show_as_minimap = opts.show_as_minimap
        editor.only_show_colors = opts.show_only_colors
        editor.only_show_modified = opts.show_only_modified

        # View
        editor.show_shade = opts.show_shade
        editor.show_all_floors = opts.show_all_floors
        editor.show_lights = opts.show_lights
        editor.show_client_box = opts.show_ingame_box
        editor.show_preview = opts.show_preview

    def sync_actions_to_options(self) -> None:
        """Sync Qt action checked states to DrawingOptions.

        Reads action states and updates options accordingly.
        """
        editor = self._editor

        # Grid
        if hasattr(editor, "act_show_grid"):
            self._options.show_grid = 1 if editor.act_show_grid.isChecked() else 0

        # Indicators
        if hasattr(editor, "act_show_wall_hooks"):
            self._options.show_hooks = editor.act_show_wall_hooks.isChecked()
        if hasattr(editor, "act_show_pickupables"):
            self._options.show_pickupables = editor.act_show_pickupables.isChecked()
        if hasattr(editor, "act_show_moveables"):
            self._options.show_moveables = editor.act_show_moveables.isChecked()
        if hasattr(editor, "act_show_avoidables"):
            self._options.show_avoidables = editor.act_show_avoidables.isChecked()

        # View toggles
        if hasattr(editor, "act_show_shade"):
            self._options.show_shade = editor.act_show_shade.isChecked()
        if hasattr(editor, "act_show_all_floors"):
            self._options.show_all_floors = editor.act_show_all_floors.isChecked()
        if hasattr(editor, "act_show_houses"):
            self._options.show_houses = editor.act_show_houses.isChecked()
        if hasattr(editor, "act_show_monsters"):
            self._options.show_monsters = editor.act_show_monsters.isChecked()
        if hasattr(editor, "act_show_monsters_spawns"):
            self._options.show_spawns_monster = editor.act_show_monsters_spawns.isChecked()
        if hasattr(editor, "act_show_npcs"):
            self._options.show_npcs = editor.act_show_npcs.isChecked()
        if hasattr(editor, "act_show_npcs_spawns"):
            self._options.show_spawns_npc = editor.act_show_npcs_spawns.isChecked()
        if hasattr(editor, "act_show_as_minimap"):
            self._options.show_as_minimap = editor.act_show_as_minimap.isChecked()
        if hasattr(editor, "act_only_show_modified"):
            self._options.show_only_modified = editor.act_only_show_modified.isChecked()
        if hasattr(editor, "act_show_lights"):
            self._options.show_lights = editor.act_show_lights.isChecked()
        if hasattr(editor, "act_show_tooltips"):
            self._options.show_tooltips = editor.act_show_tooltips.isChecked()

    def sync_options_to_actions(self) -> None:
        """Sync Qt action checked states from DrawingOptions.

        Updates action states to reflect current options.
        """
        editor = self._editor
        opts = self._options

        def _set_checked(attr: str, value: bool) -> None:
            if hasattr(editor, attr):
                act = getattr(editor, attr)
                act.blockSignals(True)
                act.setChecked(bool(value))
                act.blockSignals(False)

        # Grid
        _set_checked("act_show_grid", bool(opts.show_grid))

        # Indicators
        _set_checked("act_show_wall_hooks", opts.show_hooks)
        _set_checked("act_show_pickupables", opts.show_pickupables)
        _set_checked("act_show_moveables", opts.show_moveables)
        _set_checked("act_show_avoidables", opts.show_avoidables)

        # View toggles
        _set_checked("act_show_shade", opts.show_shade)
        _set_checked("act_show_all_floors", opts.show_all_floors)
        _set_checked("act_show_houses", opts.show_houses)
        _set_checked("act_show_monsters", opts.show_monsters)
        _set_checked("act_show_monsters_spawns", opts.show_spawns_monster)
        _set_checked("act_show_npcs", opts.show_npcs)
        _set_checked("act_show_npcs_spawns", opts.show_spawns_npc)
        _set_checked("act_show_as_minimap", opts.show_as_minimap)
        _set_checked("act_only_show_modified", opts.show_only_modified)
        _set_checked("act_show_lights", opts.show_lights)
        _set_checked("act_show_tooltips", opts.show_tooltips)
        _set_checked("act_highlight_items", opts.highlight_items)
        _set_checked("act_show_special", opts.show_special_tiles)
        _set_checked("act_show_pathing", opts.show_pathing)
        _set_checked("act_show_client_box", opts.show_ingame_box)
        _set_checked("act_show_preview", opts.show_preview)


def create_coordinator(
    editor: "QtMapEditor",
    options: "DrawingOptions | None" = None,
) -> DrawingOptionsCoordinator:
    """Create a DrawingOptionsCoordinator for the given editor.

    Parameters
    ----------
    editor : QtMapEditor
        The Qt editor instance.
    options : DrawingOptions, optional
        The drawing options to use. If None, creates a new instance.

    Returns
    -------
    DrawingOptionsCoordinator
        The coordinator instance.
    """
    from py_rme_canary.logic_layer.drawing_options import DrawingOptions

    if options is None:
        options = DrawingOptions()

    return DrawingOptionsCoordinator(editor, options)
