from __future__ import annotations


def undo(editor) -> None:
    editor._undo()


def redo(editor) -> None:
    editor._redo()


def cancel(editor) -> None:
    editor._cancel_current()


def copy(editor) -> None:
    editor._copy_selection()


def cut(editor) -> None:
    editor._cut_selection()


def arm_paste(editor) -> None:
    editor._arm_paste()


def delete_selection(editor) -> None:
    editor._delete_selection()


def copy_position(editor) -> None:
    editor._copy_position_to_clipboard()


def jump_to_brush(editor) -> None:
    editor._jump_to_brush()


def jump_to_item(editor) -> None:
    editor._jump_to_item()


def duplicate_selection(editor) -> None:
    editor._duplicate_selection()


def escape_pressed(editor) -> None:
    editor._escape_pressed()


def move_selection_z(editor, dz: int) -> None:
    editor._move_selection_z(int(dz))


def toggle_automagic(editor, enabled: bool) -> None:
    editor._toggle_automagic(bool(enabled))


def borderize_selection(editor) -> None:
    editor._borderize_selection()


def open_border_builder(editor) -> None:
    editor._open_border_builder()


def arm_fill(editor) -> None:
    editor._arm_fill()


def apply_ui_state_to_session(editor) -> None:
    editor.apply_ui_state_to_session()


def goto_previous_position(editor) -> None:
    editor._goto_previous_position()


def goto_position(editor) -> None:
    editor._goto_position_from_fields()


def create_additional_palette(editor) -> None:
    editor._create_additional_palette()


def select_palette(editor, key: str) -> None:
    editor._select_palette(str(key))


def toggle_symmetry_vertical(editor, enabled: bool) -> None:
    editor._toggle_symmetry_vertical(bool(enabled))


def toggle_symmetry_horizontal(editor, enabled: bool) -> None:
    editor._toggle_symmetry_horizontal(bool(enabled))


def replace_items(editor) -> None:
    """Open Replace Items dialog."""
    editor._replace_items()


def check_uid(editor) -> None:
    """Open UID Report dialog."""
    editor._check_uid()


def toggle_lasso(editor, enabled: bool) -> None:
    """Toggle lasso selection tool."""
    editor._toggle_lasso(bool(enabled))
