from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, cast

from py_rme_canary.vis_layer.ui.main_window.build_docks import build_docks

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorDocksMixin:
    def _build_docks(self) -> None:
        editor = cast("QtMapEditor", self)
        build_docks(editor)

    def _toggle_minimap_dock(self, checked: bool) -> None:
        editor = cast("QtMapEditor", self)
        if editor.dock_minimap is None:
            return
        if bool(checked):
            editor.dock_minimap.show()
            editor.dock_minimap.raise_()
            if editor.minimap_widget is not None:
                editor.minimap_widget.update()
        else:
            editor.dock_minimap.hide()

    def _show_tool_options_panel(self) -> None:
        """Show modern palette dock and focus tool options panel (legacy Window>Tool Options parity)."""
        editor = cast("QtMapEditor", self)
        dock_palette = getattr(editor, "dock_palette", None)
        if dock_palette is None:
            return
        dock_palette.show()
        dock_palette.raise_()
        tool_options = getattr(dock_palette, "tool_options", None)
        if tool_options is not None and hasattr(tool_options, "setFocus"):
            with contextlib.suppress(Exception):
                tool_options.setFocus()

    def _toggle_actions_history_dock(self, checked: bool) -> None:
        editor = cast("QtMapEditor", self)
        if editor.dock_actions_history is None:
            return
        if bool(checked):
            editor.dock_actions_history.show()
            editor.dock_actions_history.raise_()
            with contextlib.suppress(Exception):
                editor.actions_history.refresh()
        else:
            editor.dock_actions_history.hide()

    def _toggle_live_log_dock(self, checked: bool) -> None:
        editor = cast("QtMapEditor", self)
        if editor.dock_live_log is None:
            return
        if bool(checked):
            editor.dock_live_log.show()
            editor.dock_live_log.raise_()
        else:
            editor.dock_live_log.hide()

    def _toggle_friends_dock(self, checked: bool) -> None:
        editor = cast("QtMapEditor", self)
        if editor.dock_friends is None:
            return
        if bool(checked):
            editor.dock_friends.show()
            editor.dock_friends.raise_()
            with contextlib.suppress(Exception):
                editor._refresh_friends_sidebar()
        else:
            editor.dock_friends.hide()
