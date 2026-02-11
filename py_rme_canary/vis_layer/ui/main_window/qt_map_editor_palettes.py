from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorPalettesMixin:
    # ---------- Palette docks (legacy Window palettes, modernized UI) ----------

    def _sync_palette_selection_actions(self: QtMapEditor, palette_key: str | None = None) -> None:
        key = str(palette_key or getattr(self.palettes, "current_palette_name", "")).strip().lower()
        action_by_key = {
            "terrain": "act_palette_terrain",
            "doodad": "act_palette_doodad",
            "item": "act_palette_item",
            "collection": "act_palette_collection",
            "house": "act_palette_house",
            "creature": "act_palette_creature",
            "npc": "act_palette_npc",
            "waypoint": "act_palette_waypoint",
            "zones": "act_palette_zones",
            "raw": "act_palette_raw",
        }
        for current_key, action_name in action_by_key.items():
            action = getattr(self, action_name, None)
            if action is None or not hasattr(action, "setChecked"):
                continue
            try:
                action.blockSignals(True)
                action.setChecked(str(current_key) == str(key))
            except Exception:
                pass
            finally:
                action.blockSignals(False)

    def _create_additional_palette(self: QtMapEditor, _checked: bool = False) -> None:
        self.palettes.create_additional(_checked)

    def _select_palette(self: QtMapEditor, palette_key: str) -> None:
        self.palettes.select_palette(palette_key)
        self._sync_palette_selection_actions(palette_key)

    def _toggle_palette_large_icons(self: QtMapEditor, enabled: bool) -> None:
        self.palette_large_icons = bool(enabled)
        size = 48 if bool(enabled) else 24
        with contextlib.suppress(Exception):
            self.palettes.set_icon_size(int(size))
        with contextlib.suppress(Exception):
            self.status.showMessage("Palette icons: large" if bool(enabled) else "Palette icons: normal")
