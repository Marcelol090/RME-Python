from __future__ import annotations

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

    def _toggle_actions_history_dock(self, checked: bool) -> None:
        editor = cast("QtMapEditor", self)
        if editor.dock_actions_history is None:
            return
        if bool(checked):
            editor.dock_actions_history.show()
            editor.dock_actions_history.raise_()
            try:
                editor.actions_history.refresh()
            except Exception:
                pass
        else:
            editor.dock_actions_history.hide()
