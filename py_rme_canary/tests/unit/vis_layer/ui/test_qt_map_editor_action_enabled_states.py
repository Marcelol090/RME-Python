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
    def __init__(
        self,
        *,
        has_selection: bool,
        can_paste: bool,
        live_active: bool = False,
        live_client: bool = False,
        live_server: bool = False,
    ) -> None:
        self._has_selection = bool(has_selection)
        self._can_paste = bool(can_paste)
        self._live_active = bool(live_active)
        self._live_client = bool(live_client)
        self._live_server = bool(live_server)
        self.game_map = object()

    def has_selection(self) -> bool:
        return bool(self._has_selection)

    def can_paste(self) -> bool:
        return bool(self._can_paste)

    def is_live_active(self) -> bool:
        return bool(self._live_active)

    def is_live_client(self) -> bool:
        return bool(self._live_client)

    def is_live_server(self) -> bool:
        return bool(self._live_server)


class _EditorState(QtMapEditorSessionMixin):
    def __init__(
        self,
        *,
        has_selection: bool,
        can_paste: bool,
        live_active: bool = False,
        live_client: bool = False,
        live_server: bool = False,
    ) -> None:
        self.session = _Session(
            has_selection=has_selection,
            can_paste=can_paste,
            live_active=live_active,
            live_client=live_client,
            live_server=live_server,
        )
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

        # legacy role-gated actions
        self.act_save = _Action()
        self.act_save_as = _Action()
        self.act_close_map = _Action()
        self.act_import_map = _Action()
        self.act_import_monsters_npcs = _Action()
        self.act_replace_items = _Action()
        self.act_borderize_map = _Action()
        self.act_randomize_map = _Action()
        self.act_remove_item_map = _Action()
        self.act_remove_corpses_map = _Action()
        self.act_remove_unreachable_map = _Action()
        self.act_clear_invalid_house_tiles_map = _Action()
        self.act_clear_modified_state = _Action()
        self.act_edit_towns = _Action()
        self.act_map_cleanup = _Action()
        self.act_map_properties = _Action()
        self.act_map_statistics_legacy = _Action()
        self.act_find_item = _Action()
        self.act_find_everything_map = _Action()
        self.act_find_unique_map = _Action()
        self.act_find_action_map = _Action()
        self.act_find_container_map = _Action()
        self.act_find_writeable_map = _Action()
        self.act_new_view = _Action()
        self.act_zoom_in = _Action()
        self.act_zoom_out = _Action()
        self.act_zoom_normal = _Action()
        self.act_goto_previous_position = _Action()
        self.act_goto_position = _Action()

        # live actions
        self.act_live_host = _Action()
        self.act_live_stop = _Action()
        self.act_src_connect = _Action()
        self.act_src_disconnect = _Action()
        self.act_live_kick = _Action()
        self.act_live_ban = _Action()
        self.act_live_banlist = _Action()


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


def test_live_client_role_gates_host_and_local_actions() -> None:
    editor = _EditorState(
        has_selection=True,
        can_paste=True,
        live_active=True,
        live_client=True,
        live_server=False,
    )

    editor._update_action_enabled_states()

    assert editor.act_save.enabled is False
    assert editor.act_save_as.enabled is False
    assert editor.act_close_map.enabled is False
    assert editor.act_map_cleanup.enabled is False
    assert editor.act_map_properties.enabled is False
    assert editor.act_map_statistics_legacy.enabled is False
    assert editor.act_find_item.enabled is False
    assert editor.act_find_everything_map.enabled is False
    assert editor.act_find_item_selection.enabled is False
    assert editor.act_replace_items_on_selection.enabled is False
    assert editor.act_live_host.enabled is False
    assert editor.act_live_stop.enabled is False
    assert editor.act_src_connect.enabled is False
    assert editor.act_src_disconnect.enabled is True
    assert editor.act_live_kick.enabled is False
    assert editor.act_live_ban.enabled is False
    assert editor.act_live_banlist.enabled is False


def test_live_server_role_enables_host_actions_and_server_controls() -> None:
    editor = _EditorState(
        has_selection=True,
        can_paste=True,
        live_active=True,
        live_client=False,
        live_server=True,
    )

    editor._update_action_enabled_states()

    assert editor.act_save.enabled is True
    assert editor.act_save_as.enabled is True
    assert editor.act_close_map.enabled is False
    assert editor.act_map_cleanup.enabled is False
    assert editor.act_find_item.enabled is True
    assert editor.act_find_everything_map.enabled is True
    assert editor.act_find_item_selection.enabled is True
    assert editor.act_replace_items_on_selection.enabled is True
    assert editor.act_live_host.enabled is False
    assert editor.act_live_stop.enabled is True
    assert editor.act_src_connect.enabled is False
    assert editor.act_src_disconnect.enabled is True
    assert editor.act_live_kick.enabled is True
    assert editor.act_live_ban.enabled is True
    assert editor.act_live_banlist.enabled is True


def test_local_role_enables_local_host_and_connect_actions() -> None:
    editor = _EditorState(has_selection=True, can_paste=False)

    editor._update_action_enabled_states()

    assert editor.act_save.enabled is True
    assert editor.act_save_as.enabled is True
    assert editor.act_close_map.enabled is True
    assert editor.act_map_cleanup.enabled is True
    assert editor.act_map_properties.enabled is True
    assert editor.act_map_statistics_legacy.enabled is True
    assert editor.act_find_item.enabled is True
    assert editor.act_find_everything_map.enabled is True
    assert editor.act_find_item_selection.enabled is True
    assert editor.act_replace_items_on_selection.enabled is True
    assert editor.act_live_host.enabled is True
    assert editor.act_live_stop.enabled is False
    assert editor.act_src_connect.enabled is True
    assert editor.act_src_disconnect.enabled is False
    assert editor.act_live_kick.enabled is False
    assert editor.act_live_ban.enabled is False
    assert editor.act_live_banlist.enabled is False
