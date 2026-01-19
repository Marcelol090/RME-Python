from __future__ import annotations


def set_zoom(editor, tile_px: int) -> None:
    editor._set_zoom(int(tile_px))


def toggle_grid(editor, enabled: bool) -> None:
    editor._toggle_grid(bool(enabled))
