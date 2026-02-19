from __future__ import annotations

import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QSpinBox

from py_rme_canary.vis_layer.ui.helpers import get_brush_border_offsets, get_brush_offsets

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorBrushesMixin:
    # ---------- brush controls ----------
    def _refresh_brush_offset_cache(self: QtMapEditor) -> None:
        size = max(1, int(getattr(self, "brush_size", 1) or 1))
        shape = str(getattr(self, "brush_shape", "square") or "square")
        draw_offsets = tuple(get_brush_offsets(size, shape))
        border_offsets = tuple(get_brush_border_offsets(size, shape))
        self._brush_offsets_cache = draw_offsets
        self._brush_border_offsets_cache = border_offsets
        # Hot cache consumed directly by canvas render loop.
        self._brush_draw_offsets = draw_offsets
        self._brush_border_offsets = border_offsets

    def _brush_offsets(self: QtMapEditor) -> tuple[tuple[int, int], ...]:
        cached = getattr(self, "_brush_offsets_cache", None)
        if not cached:
            self._refresh_brush_offset_cache()
            cached = getattr(self, "_brush_offsets_cache", ())
        return cached

    def _brush_border_offsets(self: QtMapEditor) -> tuple[tuple[int, int], ...]:
        cached = getattr(self, "_brush_border_offsets_cache", None)
        if not cached:
            self._refresh_brush_offset_cache()
            cached = getattr(self, "_brush_border_offsets_cache", ())
        return cached

    def _set_selected_brush_id(self: QtMapEditor, sid: int) -> None:
        sid = int(sid)
        self.session.set_selected_brush(sid)
        self.brush_id_entry.blockSignals(True)
        self.brush_id_entry.setValue(sid)
        self.brush_id_entry.blockSignals(False)
        self._update_brush_label()

    def _set_brush_size(self: QtMapEditor, size: int) -> None:
        val = max(0, int(size))
        self.brush_size = val
        with contextlib.suppress(Exception):
            if hasattr(self, "session") and self.session.brush_size != val:
                self.session.brush_size = int(val)

        if hasattr(self, "size_spin") and isinstance(self.size_spin, QSpinBox):
            self.size_spin.blockSignals(True)
            self.size_spin.setValue(self.brush_size)
            self.size_spin.blockSignals(False)

        if hasattr(self, "brush_toolbar") and hasattr(self.brush_toolbar, "set_size"):
            self.brush_toolbar.set_size(self.brush_size)

        if hasattr(self, "act_brush_size_actions"):
            for act in getattr(self, "act_brush_size_actions", ()):
                if not hasattr(act, "setChecked"):
                    continue
                if hasattr(act, "blockSignals"):
                    act.blockSignals(True)
                act_size = int(act.data()) if hasattr(act, "data") and act.data() is not None else None
                act.setChecked(act_size == int(self.brush_size))
                if hasattr(act, "blockSignals"):
                    act.blockSignals(False)

        # Keep legacy +/- action enabled state in sync with current size.
        with contextlib.suppress(Exception):
            if hasattr(self, "act_brush_size_decrease"):
                self.act_brush_size_decrease.setEnabled(int(self.brush_size) > 1)
            if hasattr(self, "act_brush_size_increase"):
                self.act_brush_size_increase.setEnabled(int(self.brush_size) < 15)

        self._warm_brush_offsets_cache()

    def _set_brush_variation(self: QtMapEditor, variation: int) -> None:
        self.brush_variation = int(variation)
        with contextlib.suppress(Exception):
            self.session.set_brush_variation(int(self.brush_variation))
        if hasattr(self, "variation_spin") and isinstance(self.variation_spin, QSpinBox):
            self.variation_spin.blockSignals(True)
            self.variation_spin.setValue(int(self.brush_variation))
            self.variation_spin.blockSignals(False)

    def _cycle_brush_size(self: QtMapEditor, delta: int) -> None:
        """Cycle brush size by delta (e.g. +1 or -1), clamped to 0..15."""
        delta = int(delta)
        cur = int(getattr(self, "brush_size", 0) or 0)
        # Assuming max size 15 for now (legacy limit often higher but UI spinbox checks needed)
        # BrushToolbar buttons are 1, 3, 5, 7, 9.
        # Let's allow step 1.
        nxt = max(0, min(15, cur + delta))
        self._set_brush_size(nxt)

    def _cycle_brush_variation(self: QtMapEditor, delta: int) -> None:
        delta = int(delta)
        cur = int(getattr(self, "brush_variation", 0) or 0)
        if hasattr(self, "variation_spin") and isinstance(self.variation_spin, QSpinBox):
            with contextlib.suppress(Exception):
                cur = int(self.variation_spin.value())
            lo, hi = int(self.variation_spin.minimum()), int(self.variation_spin.maximum())
        else:
            lo, hi = 0, 100

        nxt = max(int(lo), min(int(hi), int(cur + delta)))
        self._set_brush_variation(int(nxt))

    def _set_doodad_thickness_enabled(self: QtMapEditor, enabled: bool) -> None:
        self.doodad_thickness_enabled = bool(enabled)
        level = int(getattr(self, "doodad_thickness_level", 5) or 5)
        level = max(1, min(10, int(level)))
        lookup_table = (1, 2, 3, 5, 8, 13, 23, 35, 50, 80)
        low = int(lookup_table[level - 1])
        with contextlib.suppress(Exception):
            self.session.set_doodad_custom_thickness(
                enabled=bool(self.doodad_thickness_enabled), low=int(low), ceil=100
            )
        if hasattr(self, "thickness_cb") and isinstance(self.thickness_cb, QCheckBox):
            self.thickness_cb.blockSignals(True)
            self.thickness_cb.setChecked(bool(self.doodad_thickness_enabled))
            self.thickness_cb.blockSignals(False)

    def _set_doodad_thickness_level(self: QtMapEditor, level: int) -> None:
        level = max(1, min(10, int(level)))
        self.doodad_thickness_level = int(level)
        if hasattr(self, "thickness_spin") and isinstance(self.thickness_spin, QSpinBox):
            self.thickness_spin.blockSignals(True)
            self.thickness_spin.setValue(int(level))
            self.thickness_spin.blockSignals(False)
        # Legacy behavior: changing the slider enables custom thickness.
        self._set_doodad_thickness_enabled(True)

    def _set_brush_shape(self: QtMapEditor, shape: str) -> None:
        shape = (shape or "square").strip().lower()
        if shape not in ("square", "circle"):
            shape = "square"
        self.brush_shape = shape
        self._warm_brush_offsets_cache()

        if hasattr(self, "shape_square") and hasattr(self.shape_square, "setChecked"):
            if hasattr(self.shape_square, "blockSignals"):
                self.shape_square.blockSignals(True)
            self.shape_square.setChecked(shape == "square")
            if hasattr(self.shape_square, "blockSignals"):
                self.shape_square.blockSignals(False)

        if hasattr(self, "shape_circle") and hasattr(self.shape_circle, "setChecked"):
            if hasattr(self.shape_circle, "blockSignals"):
                self.shape_circle.blockSignals(True)
            self.shape_circle.setChecked(shape == "circle")
            if hasattr(self.shape_circle, "blockSignals"):
                self.shape_circle.blockSignals(False)

        if hasattr(self, "brush_toolbar") and hasattr(self.brush_toolbar, "set_shape"):
            self.brush_toolbar.set_shape(shape)

        if hasattr(self, "act_brush_shape_square") and hasattr(self.act_brush_shape_square, "setChecked"):
            if hasattr(self.act_brush_shape_square, "blockSignals"):
                self.act_brush_shape_square.blockSignals(True)
            self.act_brush_shape_square.setChecked(shape == "square")
            if hasattr(self.act_brush_shape_square, "blockSignals"):
                self.act_brush_shape_square.blockSignals(False)

        if hasattr(self, "act_brush_shape_circle") and hasattr(self.act_brush_shape_circle, "setChecked"):
            if hasattr(self.act_brush_shape_circle, "blockSignals"):
                self.act_brush_shape_circle.blockSignals(True)
            self.act_brush_shape_circle.setChecked(shape == "circle")
            if hasattr(self.act_brush_shape_circle, "blockSignals"):
                self.act_brush_shape_circle.blockSignals(False)

    def _warm_brush_offsets_cache(self: QtMapEditor) -> None:
        self._refresh_brush_offset_cache()

    def _set_z(self: QtMapEditor, z: int) -> None:
        self.viewport.z = int(z)
        if hasattr(self, "z_spin") and isinstance(self.z_spin, QSpinBox):
            self.z_spin.blockSignals(True)
            self.z_spin.setValue(int(z))
            self.z_spin.blockSignals(False)
        self.canvas.update()

    def _update_brush_label(self: QtMapEditor) -> None:
        b = self.brush_mgr.get_brush(int(self.brush_id_entry.value()))
        if b is None:
            self.brush_label.setText("(unknown brush)")
        else:
            self.brush_label.setText(f"{b.brush_type}: {b.name}")

    def _refresh_brush_list(self: QtMapEditor) -> None:
        self.palettes.refresh_primary_list()

    def _on_brush_selected(self: QtMapEditor) -> None:
        if not hasattr(self, "brush_list"):
            return
        items = self.brush_list.selectedItems()
        if not items:
            return
        sid = items[0].data(Qt.ItemDataRole.UserRole)
        if sid is None:
            return
        self._set_selected_brush_id(int(sid))

    def _on_session_brush_size_changed(self: QtMapEditor, size: int) -> None:
        """Callback from EditorSession when brush size changes externally."""
        if int(self.brush_size) != int(size):
            self._set_brush_size(int(size))

    @staticmethod
    def _hotkey_key_label(slot: int) -> str:
        idx = int(slot) % 10
        return "0" if idx == 0 else str(idx)

    def _ensure_hotkey_manager(self: QtMapEditor) -> object | None:
        hkm = getattr(self, "hotkey_manager", None)
        if hkm is not None:
            return hkm
        try:
            from py_rme_canary.logic_layer.hotkey_manager import HotkeyManager

            cfg_dir = Path.home() / ".py_rme_canary"
            self.hotkey_manager = HotkeyManager(config_dir=cfg_dir)
            with contextlib.suppress(Exception):
                self.hotkey_manager.load()
            return self.hotkey_manager
        except Exception:
            return None

    def _set_selection_mode_checked(self: QtMapEditor, enabled: bool) -> None:
        enabled = bool(enabled)
        action = getattr(self, "act_selection_mode", None)
        if action is None:
            self.selection_mode = enabled
            return
        with contextlib.suppress(Exception):
            if bool(action.isChecked()) != enabled:
                action.trigger()

    def _resolve_brush_id_from_name(self: QtMapEditor, brush_name: str) -> int | None:
        target = str(brush_name or "").strip().lower()
        if not target:
            return None
        brushes = getattr(getattr(self, "brush_mgr", None), "_brushes", {})
        if not isinstance(brushes, dict):
            return None
        for sid, brush in brushes.items():
            name = str(getattr(brush, "name", "")).strip().lower()
            if name == target:
                return int(sid)
        return None

    def _view_center_tile(self: QtMapEditor) -> tuple[int, int, int]:
        tile_px = max(1, int(getattr(self.viewport, "tile_px", 32) or 32))
        cols = max(1, int(self.canvas.width()) // tile_px)
        rows = max(1, int(self.canvas.height()) // tile_px)
        x = int(getattr(self.viewport, "origin_x", 0)) + (cols // 2)
        y = int(getattr(self.viewport, "origin_y", 0)) + (rows // 2)
        z = int(getattr(self.viewport, "z", 7))
        game_map = getattr(self, "map", None)
        header = getattr(game_map, "header", None) if game_map is not None else None
        if header is not None:
            max_x = max(0, int(getattr(header, "width", 1)) - 1)
            max_y = max(0, int(getattr(header, "height", 1)) - 1)
            x = max(0, min(max_x, int(x)))
            y = max(0, min(max_y, int(y)))
        return int(x), int(y), int(z)

    def _assign_hotkey(self: QtMapEditor, slot: int) -> None:
        """Assign a hotkey slot using legacy semantics.

        Selection mode: store viewport-center position.
        Drawing mode: store current brush name.
        """
        key = self._hotkey_key_label(int(slot))
        hkm = self._ensure_hotkey_manager()
        if hkm is None:
            return
        from py_rme_canary.logic_layer.hotkey_manager import Hotkey

        if bool(getattr(self, "selection_mode", False)):
            x, y, z = self._view_center_tile()
            hkm.set_hotkey(int(slot), Hotkey.from_position(int(x), int(y), int(z)))
            with contextlib.suppress(Exception):
                hkm.save()
            self.status.showMessage(f"Set hotkey {key}: position ({x}, {y}, {z})")
            return

        sid = int(getattr(self.brush_id_entry, "value", lambda: 0)())
        brush = None
        with contextlib.suppress(Exception):
            brush = self.brush_mgr.get_brush_any(int(sid))
        if brush is None:
            with contextlib.suppress(Exception):
                brush = self.brush_mgr.get_brush(int(sid))
        if brush is None:
            self.status.showMessage(f"Set hotkey {key}: no active brush")
            return

        brush_name = str(getattr(brush, "name", "")).strip()
        if not brush_name:
            self.status.showMessage(f"Set hotkey {key}: brush without name")
            return

        hkm.set_hotkey(int(slot), Hotkey.from_brush(brush_name))
        with contextlib.suppress(Exception):
            hkm.save()
        self.status.showMessage(f"Set hotkey {key}: brush \"{brush_name}\"")

    def _activate_hotkey(self: QtMapEditor, slot: int) -> None:
        """Activate a hotkey slot (legacy 0-9 semantics).

        Position slot: switches to Selection Mode and jumps to stored tile.
        Brush slot: switches to Drawing Mode and selects stored brush name.
        """
        key = self._hotkey_key_label(int(slot))
        hkm = self._ensure_hotkey_manager()
        if hkm is None:
            return
        if not bool(getattr(hkm, "enabled", True)):
            return

        hotkey = hkm.get_hotkey(int(slot))
        if hotkey is None or bool(getattr(hotkey, "is_empty", True)):
            self.status.showMessage(f"Unassigned hotkey {key}")
            return

        if bool(getattr(hotkey, "is_position", False)):
            pos = getattr(hotkey, "position", None)
            if pos is None:
                self.status.showMessage(f"Unassigned hotkey {key}")
                return
            x = int(getattr(pos, "x", 0))
            y = int(getattr(pos, "y", 0))
            z = int(getattr(pos, "z", 7))
            self._set_selection_mode_checked(True)
            if hasattr(self, "center_view_on"):
                self.center_view_on(int(x), int(y), int(z), push_history=True)
            else:
                self.viewport.origin_x = int(x)
                self.viewport.origin_y = int(y)
                self._set_z(int(z))
                self.canvas.update()
            self.status.showMessage(f"Used hotkey {key}")
            return

        if not bool(getattr(hotkey, "is_brush", False)):
            self.status.showMessage(f"Unassigned hotkey {key}")
            return

        brush_name = str(getattr(hotkey, "brush_name", "")).strip()
        sid = self._resolve_brush_id_from_name(brush_name)
        if sid is None:
            self.status.showMessage(f"Brush \"{brush_name}\" not found")
            return

        self._set_selection_mode_checked(False)
        self._set_selected_brush_id(int(sid))
        self.status.showMessage(f"Used hotkey {key}")
