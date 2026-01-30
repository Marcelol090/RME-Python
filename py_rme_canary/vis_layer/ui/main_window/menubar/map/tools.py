"""Map tools for py_rme_canary editor.

Provides menu actions for map-wide operations like removing monsters.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from py_rme_canary.logic_layer.remove_items import remove_monsters_in_map

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


def remove_monsters(editor: "QtMapEditor", selection_only: bool = True) -> None:
    """Action: Remove monsters from the map (or selection)."""
    game_map = editor.map
    if game_map is None:
        return

    selection_tiles = _get_selection_tiles(editor) if selection_only else None

    changed_tiles, result = remove_monsters_in_map(
        game_map,
        selection_only=selection_only and (selection_tiles is not None),
        selection_tiles=selection_tiles,
    )

    if not changed_tiles:
        _show_status(editor, "No monsters removed.")
        return

    # Apply changes to map
    for pos, new_tile in changed_tiles.items():
        game_map.set_tile(new_tile)

    # Request viewport refresh
    if hasattr(editor, "viewport") and hasattr(editor.viewport, "update"):
        editor.viewport.update()

    # Signal map modification
    if hasattr(editor, "map_modified"):
        editor.map_modified.emit()

    _show_status(editor, f"Removed {result.removed} monsters.")


def _get_selection_tiles(editor: "QtMapEditor") -> set[tuple[int, int, int]] | None:
    """Extract tile coordinates from editor selection."""
    if not editor.selection or editor.selection.is_empty():
        return None

    # Try get_tiles() method first
    if hasattr(editor.selection, "get_tiles"):
        tiles = editor.selection.get_tiles()
        if tiles:
            return tiles

    # Fallback: iterate selection ranges
    if hasattr(editor.selection, "ranges"):
        selection_tiles: set[tuple[int, int, int]] = set()
        for r in editor.selection.ranges:
            for x in range(r.x, r.x + r.width):
                for y in range(r.y, r.y + r.height):
                    selection_tiles.add((x, y, r.z))
        return selection_tiles if selection_tiles else None

    return None


def _show_status(editor: "QtMapEditor", message: str) -> None:
    """Safely show a status bar message."""
    status_bar = editor.statusBar()
    if status_bar is not None:
        status_bar.showMessage(message)
