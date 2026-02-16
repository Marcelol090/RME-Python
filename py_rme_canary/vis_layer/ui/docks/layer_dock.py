"""Dock wrapper for Layer Manager."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QDockWidget, QWidget

from py_rme_canary.vis_layer.ui.widgets.layer_manager import LayerManager

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class ModernLayerDock(QDockWidget):
    """Dock widget containing the LayerManager."""

    def __init__(self, editor: QtMapEditor, parent: QWidget | None = None) -> None:
        super().__init__("Layers", parent)
        self.editor = editor

        self.layer_manager = LayerManager()
        self.layer_manager.layer_visibility_changed.connect(self._on_visibility_changed)
        self.layer_manager.layer_opacity_changed.connect(self._on_opacity_changed)

        self.setWidget(self.layer_manager)

    def _on_visibility_changed(self, layer_id: str, visible: bool) -> None:
        # Map layer_id to DrawingOptions attributes
        # Ground -> show_ground? (Assuming DrawingOptions has these, if not, we might need to add them or map to existing)
        # Existing toggles: show_all_floors, show_loose_items, etc.
        # We might need to extend DrawingOptions if "Ground" toggle doesn't exist.

        # For now, let's map what we can and log the rest
        if hasattr(self.editor, "drawing_options"):
            opts = self.editor.drawing_options
            if layer_id == "grid":
                opts.show_grid = visible
            elif layer_id == "creatures":
                opts.show_creatures = visible
            elif layer_id == "spawns":
                opts.show_spawns = visible
            elif layer_id == "houses":
                opts.show_houses = visible
            elif layer_id == "zones":
                opts.show_zones = visible

            # Trigger redraw
            if hasattr(self.editor, "canvas"):
                self.editor.canvas.update()

    def _on_opacity_changed(self, layer_id: str, opacity: float) -> None:
        # Opacity might require shader support or painter opacity
        # For now, just logging or storing in options if supported
        if hasattr(self.editor, "drawing_options"):
            # opts.set_layer_opacity(layer_id, opacity)
            pass
        if hasattr(self.editor, "canvas"):
            self.editor.canvas.update()
