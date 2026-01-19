from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorEditMixin:
    def _undo(self: "QtMapEditor") -> None:
        self.session.undo()
        self.canvas.update()

    def _redo(self: "QtMapEditor") -> None:
        self.session.redo()
        self.canvas.update()

    def _arm_fill(self: "QtMapEditor") -> None:
        self.fill_armed = True
        self.status.showMessage("Fill armed: click a ground tile to flood-fill (64x64)")

    def _cancel_current(self: "QtMapEditor") -> None:
        # Legacy-ish: Esc cancels armed tools and in-progress interactions.
        self.paste_armed = False
        self.fill_armed = False
        self.session.cancel_box_selection()
        self.session.cancel_gesture()
        self.canvas.cancel_interaction()
        self.status.showMessage("Canceled")

    def _copy_selection(self: "QtMapEditor") -> None:
        if not self.session.copy_selection():
            self.status.showMessage("Copy: nothing selected")
            self._update_action_enabled_states()
            return
        self.status.showMessage("Copied selection")
        self._update_action_enabled_states()

    def _cut_selection(self: "QtMapEditor") -> None:
        action = self.session.cut_selection()
        if action is None:
            self.status.showMessage("Cut: nothing selected")
            self._update_action_enabled_states()
            return
        self.canvas.update()
        self.status.showMessage("Cut selection")
        self._update_action_enabled_states()

    def _delete_selection(self: "QtMapEditor") -> None:
        action = self.session.delete_selection(borderize=bool(self.automagic_cb.isChecked()))
        if action is None:
            self.status.showMessage("Delete: nothing selected")
            self._update_action_enabled_states()
            return
        self.canvas.update()
        self.status.showMessage("Deleted selection")
        self._update_action_enabled_states()

    def _arm_paste(self: "QtMapEditor") -> None:
        if not self.session.can_paste():
            self.status.showMessage("Paste: buffer empty")
            self._update_action_enabled_states()
            return
        self.paste_armed = True
        self.status.showMessage("Paste armed: click to paste")
        self._update_action_enabled_states()

    def _duplicate_selection(self: "QtMapEditor", _checked: bool = False) -> None:
        # Legacy behavior: duplicate arms placement (copy selection -> paste click).
        if not self.session.copy_selection():
            self.status.showMessage("Duplicate: nothing selected")
            self._update_action_enabled_states()
            return
        self.paste_armed = True
        self.status.showMessage("Duplicate armed: click to place")
        self._update_action_enabled_states()

    def _escape_pressed(self: "QtMapEditor", _checked: bool = False) -> None:
        # Legacy-ish: Esc clears selection first; otherwise cancels armed tools.
        if self.session.has_selection():
            self.session.clear_selection()
            self.canvas.update()
            self.status.showMessage("Selection cleared")
            self._update_action_enabled_states()
            return
        self._cancel_current()
        self._update_action_enabled_states()

    def _move_selection_z(self: "QtMapEditor", direction: int) -> None:
        # EditorSession uses dst = src - move_z.
        # Up (towards z-1) => move_z = +1
        # Down (towards z+1) => move_z = -1
        if not self.session.has_selection():
            self.status.showMessage("Move selection: nothing selected")
            self._update_action_enabled_states()
            return

        move_z = 1 if int(direction) < 0 else -1
        action = self.session.move_selection(move_x=0, move_y=0, move_z=int(move_z))
        if action is None:
            self.status.showMessage("Move selection: no changes")
        else:
            self.canvas.update()
            self.status.showMessage("Moved selection")
        self._update_action_enabled_states()

    def _copy_position_to_clipboard(self: "QtMapEditor", _checked: bool = False) -> None:
        x, y = self._last_hover_tile
        z = int(self.viewport.z)
        try:
            QApplication.clipboard().setText(f"{int(x)} {int(y)} {int(z)}")
            self.status.showMessage(f"Copied position: {int(x)},{int(y)},{int(z)}")
        except Exception:
            self.status.showMessage("Copy position: failed")
