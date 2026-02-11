from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QApplication

from py_rme_canary.core.config.user_settings import get_user_settings

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


def format_position_for_copy(x: int, y: int, z: int, *, copy_format: int) -> str:
    """Render position in one of the user-configured clipboard formats."""
    px = int(x)
    py = int(y)
    pz = int(z)
    fmt = int(copy_format)

    if fmt == 1:
        return f'{{"x":{px},"y":{py},"z":{pz}}}'
    if fmt == 2:
        return f"{px}, {py}, {pz}"
    if fmt == 3:
        return f"({px}, {py}, {pz})"
    if fmt == 4:
        return f"Position({px}, {py}, {pz})"
    # Legacy default.
    return f"{{x = {px}, y = {py}, z = {pz}}}"


class QtMapEditorEditMixin:
    def _undo(self: QtMapEditor) -> None:
        self.session.undo()
        self.canvas.update()

    def _redo(self: QtMapEditor) -> None:
        self.session.redo()
        self.canvas.update()

    def _arm_fill(self: QtMapEditor) -> None:
        self.fill_armed = True
        self.status.showMessage("Fill armed: click a ground tile to flood-fill (64x64)")

    def _cancel_current(self: QtMapEditor) -> None:
        # Legacy-ish: Esc cancels armed tools and in-progress interactions.
        self.paste_armed = False
        self.fill_armed = False
        self.session.cancel_box_selection()
        self.session.cancel_gesture()
        # Defensive: Some canvas implementations may not have cancel_interaction
        if hasattr(self.canvas, "cancel_interaction"):
            self.canvas.cancel_interaction()
        self.status.showMessage("Canceled")

    def _copy_selection(self: QtMapEditor) -> None:
        if not self.session.copy_selection(
            client_version=str(self.client_version),
            sprite_hash_lookup=self._sprite_hash_for_server_id,
        ):
            self.status.showMessage("Copy: nothing selected")
            self._update_action_enabled_states()
            return
        self.status.showMessage("Copied selection")
        self._update_action_enabled_states()

    def _cut_selection(self: QtMapEditor) -> None:
        action = self.session.cut_selection(
            client_version=str(self.client_version),
            sprite_hash_lookup=self._sprite_hash_for_server_id,
        )
        if action is None:
            self.status.showMessage("Cut: nothing selected")
            self._update_action_enabled_states()
            return
        self.canvas.update()
        self.status.showMessage("Cut selection")
        self._update_action_enabled_states()

    def _delete_selection(self: QtMapEditor) -> None:
        action = self.session.delete_selection(borderize=bool(self.automagic_cb.isChecked()))
        if action is None:
            self.status.showMessage("Delete: nothing selected")
            self._update_action_enabled_states()
            return
        self.canvas.update()
        self.status.showMessage("Deleted selection")
        self._update_action_enabled_states()

    def _arm_paste(self: QtMapEditor) -> None:
        # Try importing from system clipboard first (handling any version conversion)
        sprite_match_enabled = bool(get_user_settings().get_sprite_match_on_paste())
        self.session.import_from_system_clipboard(
            target_version=str(self.client_version),
            hash_resolver=self._resolve_server_id_from_sprite_hash,
            enable_sprite_match=sprite_match_enabled,
        )

        if not self.session.can_paste():
            self.status.showMessage("Paste: buffer empty")
            self._update_action_enabled_states()
            return
        self.paste_armed = True
        self.status.showMessage("Paste armed: click to paste")
        self._update_action_enabled_states()

    def _duplicate_selection(self: QtMapEditor, _checked: bool = False) -> None:
        # Legacy behavior: duplicate arms placement (copy selection -> paste click).
        if not self.session.copy_selection():
            self.status.showMessage("Duplicate: nothing selected")
            self._update_action_enabled_states()
            return
        self.paste_armed = True
        self.status.showMessage("Duplicate armed: click to place")
        self._update_action_enabled_states()

    def _escape_pressed(self: QtMapEditor, _checked: bool = False) -> None:
        # Legacy-ish: Esc clears selection first; otherwise cancels armed tools.
        if self.session.has_selection():
            self.session.clear_selection()
            self.canvas.update()
            self.status.showMessage("Selection cleared")
            self._update_action_enabled_states()
            return
        self._cancel_current()
        self._update_action_enabled_states()

    def _move_selection_z(self: QtMapEditor, direction: int) -> None:
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

    def _copy_position_to_clipboard(self: QtMapEditor, _checked: bool = False) -> None:
        x, y = self._last_hover_tile
        z = int(self.viewport.z)
        try:
            settings = get_user_settings()
            copy_format = int(settings.get_copy_position_format())
            text = format_position_for_copy(int(x), int(y), int(z), copy_format=copy_format)
            QApplication.clipboard().setText(text)
            self.status.showMessage(f"Copied position: {text}")
        except Exception:
            self.status.showMessage("Copy position: failed")
