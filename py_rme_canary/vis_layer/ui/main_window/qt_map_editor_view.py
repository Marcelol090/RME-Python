from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, cast

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QMessageBox

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorViewMixin:
    def _sync_drawing_options(self) -> None:
        editor = cast("QtMapEditor", self)
        coordinator = getattr(editor, "drawing_options_coordinator", None)
        if coordinator is None:
            return
        coordinator.sync_from_editor()

    def _visible_floors_for_selection(self) -> list[int]:
        editor = cast("QtMapEditor", self)
        floor = int(editor.viewport.z)
        show_all = bool(getattr(editor, "show_all_floors", False))
        start_z = (7 if floor < 8 else min(15, floor + 2)) if show_all else floor
        end_z = floor
        if start_z >= end_z:
            return list(range(start_z, end_z - 1, -1))
        return list(range(start_z, end_z + 1))

    def _set_view_flag(self, name: str, value: bool) -> None:
        editor = cast("QtMapEditor", self)
        try:
            setattr(editor, name, bool(value))
        except Exception:
            return
        editor._sync_drawing_options()
        with contextlib.suppress(Exception):
            editor.canvas.update()

    def _toggle_indicators_simple(self, checked: bool) -> None:
        editor = cast("QtMapEditor", self)
        editor.show_indicators = bool(checked)
        # Reuse existing indicator drawing implementation by mapping to per-type toggles.
        editor.show_wall_hooks = bool(checked)
        editor.show_pickupables = bool(checked)
        editor.show_moveables = bool(checked)
        editor.show_avoidables = bool(checked)
        editor._sync_drawing_options()
        with contextlib.suppress(Exception):
            editor.canvas.update()

    def _toggle_fullscreen(self) -> None:
        editor = cast("QtMapEditor", self)
        if editor.isFullScreen():
            editor.showNormal()
        else:
            editor.showFullScreen()

    def _take_screenshot(self) -> None:
        editor = cast("QtMapEditor", self)
        # Capture the visible canvas (fast and predictable).
        path, _ = QFileDialog.getSaveFileName(editor, "Save Screenshot", "screenshot.png", "PNG (*.png)")
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        try:
            pm = editor.canvas.grab()
            pm.save(path, "PNG")
            editor.status.showMessage(f"Saved screenshot: {path}")
        except Exception as e:
            QMessageBox.critical(editor, "Screenshot", str(e))

    def _toggle_sprite_preview(self, checked: bool) -> None:
        editor = cast("QtMapEditor", self)
        editor.show_preview = bool(checked)
        editor._sync_drawing_options()
        dock = getattr(editor, "dock_sprite_preview", None)
        if dock is None:
            return
        try:
            dock.setVisible(bool(checked))
            if bool(checked):
                dock.raise_()
        except Exception:
            pass

    def _toggle_ingame_preview(self, checked: bool) -> None:
        editor = cast("QtMapEditor", self)
        if not hasattr(editor, "ingame_preview_enabled"):
            editor.ingame_preview_enabled = False
        if checked:
            try:
                from py_rme_canary.vis_layer.preview.preview_controller import PreviewController
            except Exception as exc:
                QMessageBox.warning(editor, "In-Game Preview", f"Failed to import preview window: {exc}")
                return
            controller = getattr(editor, "ingame_preview_controller", None)
            if controller is None:
                controller = PreviewController(editor)
                editor.ingame_preview_controller = controller
            controller.start()
            editor.ingame_preview_enabled = True
        else:
            controller = getattr(editor, "ingame_preview_controller", None)
            if controller is not None:
                controller.stop()
            editor.ingame_preview_enabled = False

    def _sync_dock_action(self, act: QAction, visible: bool) -> None:
        try:
            act.blockSignals(True)
            act.setChecked(bool(visible))
            act.blockSignals(False)
        except Exception:
            pass

    def _set_zoom(self, tile_px: int) -> None:
        editor = cast("QtMapEditor", self)
        editor.viewport.tile_px = int(max(6, min(64, tile_px)))
        editor.canvas.update()

    def _toggle_grid(self, enabled: bool) -> None:
        editor = cast("QtMapEditor", self)
        editor.show_grid = bool(enabled)
        editor._sync_drawing_options()
        editor.canvas.update()

    def _toggle_wall_hooks(self, enabled: bool) -> None:
        editor = cast("QtMapEditor", self)
        editor.show_wall_hooks = bool(enabled)
        editor._sync_indicator_actions()
        editor._sync_drawing_options()
        editor.canvas.update()

    def _toggle_pickupables(self, enabled: bool) -> None:
        editor = cast("QtMapEditor", self)
        editor.show_pickupables = bool(enabled)
        editor._sync_indicator_actions()
        editor._sync_drawing_options()
        editor.canvas.update()

    def _toggle_moveables(self, enabled: bool) -> None:
        editor = cast("QtMapEditor", self)
        editor.show_moveables = bool(enabled)
        editor._sync_indicator_actions()
        editor._sync_drawing_options()
        editor.canvas.update()

    def _toggle_avoidables(self, enabled: bool) -> None:
        editor = cast("QtMapEditor", self)
        editor.show_avoidables = bool(enabled)
        editor._sync_indicator_actions()
        editor._sync_drawing_options()
        editor.canvas.update()

    def _sync_indicator_actions(self) -> None:
        editor = cast("QtMapEditor", self)
        # Menu actions
        if hasattr(editor, "act_show_grid"):
            editor.act_show_grid.blockSignals(True)
            editor.act_show_grid.setChecked(bool(editor.show_grid))
            editor.act_show_grid.blockSignals(False)

        for attr, value in (
            ("act_show_wall_hooks", editor.show_wall_hooks),
            ("act_show_pickupables", editor.show_pickupables),
            ("act_show_moveables", editor.show_moveables),
            ("act_show_avoidables", editor.show_avoidables),
        ):
            if hasattr(editor, attr):
                act = getattr(editor, attr)
                act.blockSignals(True)
                act.setChecked(bool(value))
                act.blockSignals(False)

        # Toolbar actions (best-effort)
        for attr, value in (
            ("act_tb_hooks", editor.show_wall_hooks),
            ("act_tb_pickupables", editor.show_pickupables),
            ("act_tb_moveables", editor.show_moveables),
            ("act_tb_avoidables", editor.show_avoidables),
        ):
            if hasattr(editor, attr):
                act = getattr(editor, attr)
                act.blockSignals(True)
                act.setChecked(bool(value))
                act.blockSignals(False)
