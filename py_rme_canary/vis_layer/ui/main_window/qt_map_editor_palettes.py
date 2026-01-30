from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorPalettesMixin:
    # ---------- Palette docks (legacy Window palettes, modernized UI) ----------

    def _create_additional_palette(self: QtMapEditor, _checked: bool = False) -> None:
        self.palettes.create_additional(_checked)

    def _select_palette(self: QtMapEditor, palette_key: str) -> None:
        self.palettes.select_palette(palette_key)

    def _toggle_palette_large_icons(self: QtMapEditor, enabled: bool) -> None:
        self.palette_large_icons = bool(enabled)
        size = 48 if bool(enabled) else 24
        try:
            self.palettes.set_icon_size(int(size))
        except Exception:
            pass
        try:
            self.status.showMessage("Palette icons: large" if bool(enabled) else "Palette icons: normal")
        except Exception:
            pass
