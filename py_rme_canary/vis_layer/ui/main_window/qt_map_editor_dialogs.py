from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PyQt6.QtWidgets import QMessageBox

from py_rme_canary.vis_layer.ui.main_window.dialogs import FindItemDialog, MapStatisticsDialog, ReplaceItemsDialog
from py_rme_canary.vis_layer.ui.main_window.find_item import open_find_item

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorDialogsMixin:
    def _open_find_item_dialog(self) -> None:
        editor = cast("QtMapEditor", self)
        open_find_item(editor)

    def _open_replace_items_dialog(self) -> None:
        editor = cast("QtMapEditor", self)
        dlg = ReplaceItemsDialog(editor)
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        from_id, to_id = dlg.values()

        replaced, exceeded, _action = editor.session.replace_items(from_id=int(from_id), to_id=int(to_id))
        if replaced <= 0:
            QMessageBox.information(editor, "Replace Items", "No matching items found.")
            return

        msg = f"Replaced {replaced} item(s)."
        if exceeded:
            msg += "\nStopped early due to safety limit."
        QMessageBox.information(editor, "Replace Items", msg)

    def _open_replace_items_on_selection_dialog(self) -> None:
        editor = cast("QtMapEditor", self)
        if not editor.session.has_selection():
            QMessageBox.information(editor, "Replace Items", "No selection.")
            return

        dlg = ReplaceItemsDialog(editor)
        dlg.setWindowTitle("Replace Items on Selection")
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        from_id, to_id = dlg.values()
        replaced, exceeded, _action = editor.session.replace_items(
            from_id=int(from_id),
            to_id=int(to_id),
            selection_only=True,
        )
        if replaced <= 0:
            QMessageBox.information(editor, "Replace Items", "No matching items found in selection.")
            return

        msg = f"Replaced {replaced} item(s) in selection."
        if exceeded:
            msg += "\nStopped early due to safety limit."
        QMessageBox.information(editor, "Replace Items", msg)

    def _open_remove_item_on_selection_dialog(self) -> None:
        editor = cast("QtMapEditor", self)
        if not editor.session.has_selection():
            QMessageBox.information(editor, "Remove Item", "No selection.")
            return

        dlg = FindItemDialog(editor, title="Remove Item on Selection")
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        server_id = int(dlg.result_value().server_id)
        removed, _action = editor.session.remove_items(server_id=server_id, selection_only=True)
        QMessageBox.information(editor, "Remove Item", f"{removed} items removed.")

    def _show_map_statistics(self) -> None:
        editor = cast("QtMapEditor", self)
        dlg = MapStatisticsDialog(editor, game_map=editor.map)
        dlg.exec()
