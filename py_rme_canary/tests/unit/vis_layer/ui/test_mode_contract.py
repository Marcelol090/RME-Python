from __future__ import annotations

from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_navigation import QtMapEditorNavigationMixin


class _Action:
    def __init__(self, checked: bool = False) -> None:
        self._checked = bool(checked)
        self._signals_blocked = False

    def isChecked(self) -> bool:  # noqa: N802
        return bool(self._checked)

    def setChecked(self, value: bool) -> None:  # noqa: N802
        self._checked = bool(value)

    def blockSignals(self, value: bool) -> None:  # noqa: N802
        self._signals_blocked = bool(value)


class _Session:
    def __init__(self) -> None:
        self.cancel_gesture_calls = 0
        self.cancel_box_selection_calls = 0

    def cancel_gesture(self) -> None:
        self.cancel_gesture_calls += 1

    def cancel_box_selection(self) -> None:
        self.cancel_box_selection_calls += 1

    def set_selection_depth_mode(self, _mode: object) -> None:
        return


class _Canvas:
    def __init__(self) -> None:
        self.update_calls = 0
        self.cancel_lasso_calls = 0
        self.cancel_interaction_calls = 0

    def update(self) -> None:
        self.update_calls += 1

    def cancel_lasso(self) -> None:
        self.cancel_lasso_calls += 1

    def cancel_interaction(self) -> None:
        self.cancel_interaction_calls += 1


class _Editor(QtMapEditorNavigationMixin):
    def __init__(self) -> None:
        self.act_selection_mode = _Action(False)
        self.act_lasso_select = _Action(False)
        self.selection_mode = False
        self.lasso_enabled = False
        self.session = _Session()
        self.canvas = _Canvas()
        self.update_action_enabled_states_calls = 0

    def _update_action_enabled_states(self) -> None:
        self.update_action_enabled_states_calls += 1

    def _sync_selection_depth_actions(self) -> None:
        return


def test_toggle_selection_mode_enables_selection_and_cancels_gesture() -> None:
    editor = _Editor()
    editor.act_selection_mode.setChecked(True)

    editor._toggle_selection_mode()

    assert editor.selection_mode is True
    assert editor.canvas.cancel_interaction_calls >= 1
    assert editor.session.cancel_gesture_calls == 1
    assert editor.session.cancel_box_selection_calls == 1
    assert editor.canvas.update_calls == 1
    assert editor.update_action_enabled_states_calls == 1


def test_toggle_selection_mode_off_clears_lasso_state() -> None:
    editor = _Editor()
    editor.lasso_enabled = True
    editor.act_lasso_select.setChecked(True)
    editor.act_selection_mode.setChecked(False)

    editor._toggle_selection_mode()

    assert editor.selection_mode is False
    assert editor.lasso_enabled is False
    assert editor.act_lasso_select.isChecked() is False
    assert editor.canvas.cancel_lasso_calls == 1
    assert editor.session.cancel_gesture_calls == 0
    assert editor.session.cancel_box_selection_calls == 1


def test_toggle_lasso_enables_selection_mode_and_syncs_action() -> None:
    editor = _Editor()

    editor._toggle_lasso(True)

    assert editor.lasso_enabled is True
    assert editor.selection_mode is True
    assert editor.act_selection_mode.isChecked() is True
    assert editor.canvas.cancel_interaction_calls == 1
    assert editor.session.cancel_gesture_calls == 1
    assert editor.canvas.update_calls == 1

    editor._toggle_lasso(False)
    assert editor.lasso_enabled is False
    assert editor.canvas.cancel_lasso_calls == 1
    assert editor.canvas.update_calls == 2
