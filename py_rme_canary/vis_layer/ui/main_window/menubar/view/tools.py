from __future__ import annotations


def set_zoom(editor, tile_px: int) -> None:
    editor._set_zoom(int(tile_px))


def toggle_grid(editor, enabled: bool) -> None:
    editor._toggle_grid(bool(enabled))


def toggle_ingame_preview(editor, enabled: bool) -> None:
    editor._toggle_ingame_preview(bool(enabled))


def goto_floor(editor, floor: int) -> None:
    """Navigate directly to a specific floor level (0-15)."""
    editor._goto_floor(int(floor))
