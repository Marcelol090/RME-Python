from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorMirrorMixin:
    # ---------- mirror drawing ----------

    def _sync_mirror_actions(self: QtMapEditor) -> None:
        self.act_toggle_mirror.blockSignals(True)
        self.act_mirror_axis_x.blockSignals(True)
        self.act_mirror_axis_y.blockSignals(True)
        self.act_toggle_mirror.setChecked(bool(self.mirror_enabled))
        self.act_mirror_axis_x.setChecked(self.mirror_axis == "x")
        self.act_mirror_axis_y.setChecked(self.mirror_axis == "y")
        self.act_toggle_mirror.blockSignals(False)
        self.act_mirror_axis_x.blockSignals(False)
        self.act_mirror_axis_y.blockSignals(False)

    def has_mirror_axis(self: QtMapEditor) -> bool:
        return self.mirror_axis_value is not None

    def get_mirror_axis_value(self: QtMapEditor) -> int:
        if self.mirror_axis_value is None:
            raise RuntimeError("Mirror axis not set")
        return int(self.mirror_axis_value)

    def _set_mirror_axis(self: QtMapEditor, axis: str) -> None:
        axis = (axis or "x").strip().lower()
        if axis not in ("x", "y"):
            axis = "x"
        self.mirror_axis = axis
        self._sync_mirror_actions()
        self.status.showMessage(
            f"Mirror axis set to {axis.upper()} (value {'unset' if self.mirror_axis_value is None else self.mirror_axis_value})"
        )

    def _set_mirror_axis_from_cursor(self: QtMapEditor) -> None:
        x, y = self._last_hover_tile
        if self.mirror_axis == "x":
            self.mirror_axis_value = int(x)
        else:
            self.mirror_axis_value = int(y)
        self._sync_mirror_actions()
        self.status.showMessage(f"Mirror axis {self.mirror_axis.upper()} set to {self.mirror_axis_value}")

    def _toggle_mirror_drawing_at_cursor(self: QtMapEditor) -> None:
        self.mirror_enabled = not bool(self.mirror_enabled)
        if self.mirror_enabled and self.mirror_axis_value is None:
            # Legacy toggle is "at cursor"; default to setting the axis value
            # from the last hover position so it works immediately.
            self._set_mirror_axis_from_cursor()
        self._sync_mirror_actions()
        self.status.showMessage(f"Mirror drawing {'enabled' if self.mirror_enabled else 'disabled'}")
