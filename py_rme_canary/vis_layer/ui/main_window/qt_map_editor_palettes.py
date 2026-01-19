from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor

class QtMapEditorPalettesMixin:
    # ---------- Palette docks (legacy Window palettes, modernized UI) ----------

    def _create_additional_palette(self: "QtMapEditor", _checked: bool = False) -> None:
        self.palettes.create_additional(_checked)

    def _select_palette(self: "QtMapEditor", palette_key: str) -> None:
        self.palettes.select_palette(palette_key)
