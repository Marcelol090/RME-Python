from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QCheckBox, QSpinBox

from py_rme_canary.vis_layer.ui.helpers import iter_brush_border_offsets, iter_brush_offsets

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorBrushesMixin:
    # ---------- brush controls ----------
    def _refresh_brush_offset_cache(self: QtMapEditor) -> None:
        size = max(1, int(getattr(self, "brush_size", 1) or 1))
        shape = str(getattr(self, "brush_shape", "square") or "square")
        self._brush_offsets_cache = tuple(iter_brush_offsets(size, shape))
        self._brush_border_offsets_cache = tuple(iter_brush_border_offsets(size, shape))

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
        self.brush_size = max(0, int(size))
        with contextlib.suppress(Exception):
            self.session.brush_size = int(self.brush_size)

        if hasattr(self, "size_spin") and isinstance(self.size_spin, QSpinBox):
            self.size_spin.blockSignals(True)
            self.size_spin.setValue(self.brush_size)
            self.size_spin.blockSignals(False)

        if hasattr(self, "brush_toolbar") and hasattr(self.brush_toolbar, "set_size"):
            self.brush_toolbar.set_size(self.brush_size)

        # Keep menu actions aligned with backend state source-of-truth.
        with contextlib.suppress(Exception):
            if hasattr(self, "act_brush_size_decrease"):
                self.act_brush_size_decrease.setEnabled(int(self.brush_size) > 1)
            if hasattr(self, "act_brush_size_increase"):
                self.act_brush_size_increase.setEnabled(int(self.brush_size) < 11)
        self._refresh_brush_offset_cache()

    def _set_brush_variation(self: QtMapEditor, variation: int) -> None:
        self.brush_variation = int(variation)
        with contextlib.suppress(Exception):
            self.session.set_brush_variation(int(self.brush_variation))
        if hasattr(self, "variation_spin") and isinstance(self.variation_spin, QSpinBox):
            self.variation_spin.blockSignals(True)
            self.variation_spin.setValue(int(self.brush_variation))
            self.variation_spin.blockSignals(False)

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

        if hasattr(self, "shape_square") and isinstance(self.shape_square, QCheckBox):
            self.shape_square.blockSignals(True)
            self.shape_square.setChecked(shape == "square")
            self.shape_square.blockSignals(False)

        if hasattr(self, "shape_circle") and isinstance(self.shape_circle, QCheckBox):
            self.shape_circle.blockSignals(True)
            self.shape_circle.setChecked(shape == "circle")
            self.shape_circle.blockSignals(False)

        if hasattr(self, "brush_toolbar") and hasattr(self.brush_toolbar, "set_shape"):
            self.brush_toolbar.set_shape(shape)

        with contextlib.suppress(Exception):
            if hasattr(self, "act_brush_shape_square"):
                self.act_brush_shape_square.blockSignals(True)
                self.act_brush_shape_square.setChecked(shape == "square")
                self.act_brush_shape_square.blockSignals(False)
            if hasattr(self, "act_brush_shape_circle"):
                self.act_brush_shape_circle.blockSignals(True)
                self.act_brush_shape_circle.setChecked(shape == "circle")
                self.act_brush_shape_circle.blockSignals(False)
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
