from __future__ import annotations

from py_rme_canary.vis_layer.ui.main_window.menubar.file import tools as file_tools


class _Editor:
    def __init__(self, confirm_result: bool) -> None:
        self.confirm_result = bool(confirm_result)
        self.confirm_calls: list[bool] = []
        self.close_calls = 0
        self._live_close_confirmed_for_exit = False

    def _confirm_live_session_close(self, *, for_app_exit: bool = False) -> bool:
        self.confirm_calls.append(bool(for_app_exit))
        return bool(self.confirm_result)

    def close(self) -> None:
        self.close_calls += 1


def test_exit_app_aborts_when_live_confirmation_fails() -> None:
    editor = _Editor(confirm_result=False)

    file_tools.exit_app(editor)

    assert editor.confirm_calls == [True]
    assert editor.close_calls == 0
    assert editor._live_close_confirmed_for_exit is False


def test_exit_app_sets_skip_flag_and_closes_when_live_confirmation_passes() -> None:
    editor = _Editor(confirm_result=True)

    file_tools.exit_app(editor)

    assert editor.confirm_calls == [True]
    assert editor.close_calls == 1
    assert editor._live_close_confirmed_for_exit is True
