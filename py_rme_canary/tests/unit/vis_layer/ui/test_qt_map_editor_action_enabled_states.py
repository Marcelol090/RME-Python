from __future__ import annotations

import pytest

pytest.importorskip("PyQt6.QtWidgets", exc_type=ImportError)

from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_session import QtMapEditorSessionMixin


class _Action:
    def __init__(self) -> None:
        self.enabled = True

    def setEnabled(self, value: bool) -> None:  # noqa: N802
        self.enabled = bool(value)


class _Session:
    def __init__(self, *, has_selection: bool, can_paste: bool) -> None:
        self._has_selection = bool(has_selection)
        self._can_paste = bool(can_paste)

    def has_selection(self) -> bool:
        return bool(self._has_selection)

    def can_paste(self) -> bool:
        return bool(self._can_paste)


class _EditorState(QtMapEditorSessionMixin):
    def __init__(self, *, has_selection: bool, can_paste: bool) -> None:
        self.session = _Session(has_selection=has_selection, can_paste=can_paste)
        self.paste_armed = False
        self.fill_armed = False

        # baseline edit actions
        self.act_copy = _Action()
        self.act_cut = _Action()
        self.act_delete_selection = _Action()
        self.act_duplicate_selection = _Action()
        self.act_move_selection_up = _Action()
        self.act_move_selection_down = _Action()
        self.act_borderize_selection = _Action()
        self.act_clear_invalid_tiles_selection = _Action()
        self.act_randomize_selection = _Action()
        self.act_house_set_id_on_selection = _Action()
        self.act_house_clear_id_on_selection = _Action()
        self.act_switch_door_here = _Action()
        self.act_paste = _Action()
        self.act_clear_selection = _Action()

        # selection menu actions
        self.act_replace_items_on_selection = _Action()
        self.act_find_item_selection = _Action()
        self.act_remove_item_on_selection = _Action()
        self.act_find_everything_selection = _Action()
        self.act_find_unique_selection = _Action()
        self.act_find_action_selection = _Action()
        self.act_find_container_selection = _Action()
        self.act_find_writeable_selection = _Action()


def test_selection_scoped_actions_disabled_without_selection() -> None:
    editor = _EditorState(has_selection=False, can_paste=True)

    editor._update_action_enabled_states()

    assert editor.act_replace_items_on_selection.enabled is False
    assert editor.act_find_item_selection.enabled is False
    assert editor.act_remove_item_on_selection.enabled is False
    assert editor.act_find_everything_selection.enabled is False
    assert editor.act_find_unique_selection.enabled is False
    assert editor.act_find_action_selection.enabled is False
    assert editor.act_find_container_selection.enabled is False
    assert editor.act_find_writeable_selection.enabled is False


def test_selection_scoped_actions_enabled_with_selection() -> None:
    editor = _EditorState(has_selection=True, can_paste=False)

    editor._update_action_enabled_states()

    assert editor.act_replace_items_on_selection.enabled is True
    assert editor.act_find_item_selection.enabled is True
    assert editor.act_remove_item_on_selection.enabled is True
    assert editor.act_find_everything_selection.enabled is True
    assert editor.act_find_unique_selection.enabled is True
    assert editor.act_find_action_selection.enabled is True
    assert editor.act_find_container_selection.enabled is True
    assert editor.act_find_writeable_selection.enabled is True
