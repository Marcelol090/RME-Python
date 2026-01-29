from __future__ import annotations


def toggle_mirror_drawing(editor) -> None:
    editor._toggle_mirror_drawing_at_cursor()


def set_axis(editor, axis: str) -> None:
    editor._set_mirror_axis(str(axis))


def set_axis_from_cursor(editor) -> None:
    editor._set_mirror_axis_from_cursor()
