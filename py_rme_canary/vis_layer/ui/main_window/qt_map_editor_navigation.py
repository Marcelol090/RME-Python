from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QSpinBox

from py_rme_canary.logic_layer.editor_session import EditorSession
from py_rme_canary.logic_layer.session.selection_modes import SelectionDepthMode

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorNavigationMixin:
    def center_view_on(self: QtMapEditor, x: int, y: int, z: int, *, push_history: bool = True) -> None:
        """Center viewport on a given tile (used by GoTo and Minimap)."""

        if bool(push_history):
            self._position_history.append(
                (int(self.viewport.origin_x), int(self.viewport.origin_y), int(self.viewport.z))
            )

        cols = max(1, self.canvas.width() // max(1, int(self.viewport.tile_px)))
        rows = max(1, self.canvas.height() // max(1, int(self.viewport.tile_px)))
        new_origin_x = int(int(x) - (cols // 2))
        new_origin_y = int(int(y) - (rows // 2))
        new_origin_x = max(0, min(int(self.map.header.width) - 1, new_origin_x))
        new_origin_y = max(0, min(int(self.map.header.height) - 1, new_origin_y))

        self.viewport.origin_x = int(new_origin_x)
        self.viewport.origin_y = int(new_origin_y)
        self._set_z(int(z))
        try:
            if hasattr(self, "map_drawer") and self.map_drawer is not None:
                self.map_drawer.set_highlight_tile(int(x), int(y), int(z))
        except Exception:
            pass
        self.canvas.update()
        if self.minimap_widget is not None:
            self.minimap_widget.update()

    def _goto_position_from_fields(self: QtMapEditor) -> None:
        if not hasattr(self, "goto_x_spin") or not hasattr(self, "goto_y_spin"):
            return
        x = int(self.goto_x_spin.value())
        y = int(self.goto_y_spin.value())
        z = int(self.viewport.z)

        if hasattr(self, "z_spin") and isinstance(self.z_spin, QSpinBox):
            z = int(self.z_spin.value())

        self.center_view_on(int(x), int(y), int(z), push_history=True)

    def _goto_previous_position(self: QtMapEditor) -> None:
        if not self._position_history:
            self.status.showMessage("No previous position")
            return
        ox, oy, oz = self._position_history.pop()
        self.viewport.origin_x = int(max(0, ox))
        self.viewport.origin_y = int(max(0, oy))
        self._set_z(int(oz))
        self.canvas.update()

    def update_status_from_mouse(self: QtMapEditor, px: int, py: int) -> None:
        x, y = self.canvas._tile_at(px, py)
        self._last_hover_tile = (int(x), int(y))
        z = self.viewport.z
        sid = self.canvas._server_id_for_tile(x, y, z)
        if hasattr(self, "cursor_pos_label"):
            self.cursor_pos_label.setText(f"Cursor: {x},{y},{z}")
        if hasattr(self, "goto_x_spin") and isinstance(self.goto_x_spin, QSpinBox) and not self.goto_x_spin.hasFocus():
            self.goto_x_spin.blockSignals(True)
            self.goto_x_spin.setValue(int(x))
            self.goto_x_spin.blockSignals(False)
        if hasattr(self, "goto_y_spin") and isinstance(self.goto_y_spin, QSpinBox) and not self.goto_y_spin.hasFocus():
            self.goto_y_spin.blockSignals(True)
            self.goto_y_spin.setValue(int(y))
            self.goto_y_spin.blockSignals(False)
        if not getattr(self, "show_tooltips", True):
            try:
                self.canvas.setToolTip("")
            except Exception:
                pass
            self.status.showMessage(f"x={x} y={y} z={z} | origin=({self.viewport.origin_x},{self.viewport.origin_y})")
            return

        # Tooltip uses the tile stack (topmost last)
        try:
            stack = self.canvas._server_ids_for_tile_stack(x, y, z)
        except Exception:
            stack = []

        if stack:
            top = int(stack[-1])
            tooltip = f"{x},{y},{z}\nTop: {top}\nStack: {len(stack)}"
        else:
            tooltip = f"{x},{y},{z}\n(empty)"

        try:
            self.canvas.setToolTip(tooltip)
        except Exception:
            pass

        self.status.showMessage(
            f"x={x} y={y} z={z} | tile_id={sid if sid is not None else '-'} | origin=({self.viewport.origin_x},{self.viewport.origin_y})"
        )
        try:
            self.session.send_live_cursor_update(x=int(x), y=int(y), z=int(z))
        except Exception:
            pass

    def _jump_to_brush(self: QtMapEditor, _checked: bool = False) -> None:
        try:
            if hasattr(self, "dock_brushes") and self.dock_brushes is not None:
                self.dock_brushes.raise_()
                self.dock_brushes.show()
            self.brush_filter.setFocus()
            self.brush_filter.selectAll()
        except Exception:
            pass

    def _jump_to_item(self: QtMapEditor, _checked: bool = False) -> None:
        try:
            self.brush_id_entry.setFocus()
            le = self.brush_id_entry.lineEdit()
            if le is not None:
                le.selectAll()
        except Exception:
            pass

    def _new_view(self: QtMapEditor) -> None:
        w = type(self)()
        # Best-effort: mirror current view state.
        try:
            w.current_path = getattr(self, "current_path", None)
            w.map = self.map
            w.session = EditorSession(w.map, w.brush_mgr, on_tiles_changed=w._on_tiles_changed)
            w.viewport.origin_x = int(self.viewport.origin_x)
            w.viewport.origin_y = int(self.viewport.origin_y)
            w._set_z(int(self.viewport.z))
        except Exception:
            pass
        w.show()
        self._extra_views.append(w)

    def _new_instance(self: QtMapEditor) -> None:
        """Open a new independent editor instance.

        The new window starts with a fresh map and independent assets/session.
        """
        w = type(self)()
        w.show()
        self._extra_views.append(w)

    def _toggle_selection_mode(self: QtMapEditor) -> None:
        self.selection_mode = bool(self.act_selection_mode.isChecked())
        # Cancel any active paint gesture if user toggles modes mid-drag.
        if self.selection_mode:
            self.session.cancel_gesture()
        elif bool(getattr(self, "lasso_enabled", False)) and hasattr(self, "act_lasso_select"):
            try:
                self.act_lasso_select.blockSignals(True)
                self.act_lasso_select.setChecked(False)
                self.act_lasso_select.blockSignals(False)
            except Exception:
                pass
            self.lasso_enabled = False
            if hasattr(self, "canvas"):
                try:
                    self.canvas.cancel_lasso()
                except Exception:
                    pass
        self.session.cancel_box_selection()
        self.canvas.update()
        self._update_action_enabled_states()

    def _toggle_lasso(self: QtMapEditor, enabled: bool) -> None:
        self.lasso_enabled = bool(enabled)
        if self.lasso_enabled and not bool(self.selection_mode):
            if hasattr(self, "act_selection_mode"):
                try:
                    self.act_selection_mode.blockSignals(True)
                    self.act_selection_mode.setChecked(True)
                    self.act_selection_mode.blockSignals(False)
                except Exception:
                    pass
            self.selection_mode = True
            self.session.cancel_gesture()
        if not self.lasso_enabled and hasattr(self, "canvas"):
            try:
                self.canvas.cancel_lasso()
            except Exception:
                pass
        self.canvas.update()
        self._update_action_enabled_states()

    def _set_selection_depth_mode(self: QtMapEditor, mode: SelectionDepthMode | str) -> None:
        self.session.set_selection_depth_mode(mode)
        current = self.session.get_selection_depth_mode()
        mapping = {
            SelectionDepthMode.COMPENSATE: "act_selection_depth_compensate",
            SelectionDepthMode.CURRENT: "act_selection_depth_current",
            SelectionDepthMode.LOWER: "act_selection_depth_lower",
            SelectionDepthMode.VISIBLE: "act_selection_depth_visible",
        }
        for depth_mode, attr in mapping.items():
            if hasattr(self, attr):
                act = getattr(self, attr)
                try:
                    act.blockSignals(True)
                    act.setChecked(current == depth_mode)
                    act.blockSignals(False)
                except Exception:
                    pass
