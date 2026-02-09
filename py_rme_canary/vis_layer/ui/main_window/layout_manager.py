"""Layout Manager for saving and restoring window states."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMainWindow, QMessageBox

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class LayoutManager:
    """Manages window layouts (dock positions, toolbars, geometry)."""

    def __init__(self, editor: QtMapEditor) -> None:
        self.editor = editor
        self.settings = QSettings("Canary", "MapEditor")

    def save_layout(self, name: str = "default") -> None:
        """Save current layout to settings."""
        if not name:
            return

        self.settings.beginGroup(f"layouts/{name}")
        self.settings.setValue("geometry", self.editor.saveGeometry())
        self.settings.setValue("state", self.editor.saveState())
        self.settings.endGroup()

    def load_layout(self, name: str = "default") -> None:
        """Load layout from settings."""
        if not name:
            return

        self.settings.beginGroup(f"layouts/{name}")
        geometry = self.settings.value("geometry")
        state = self.settings.value("state")
        self.settings.endGroup()

        if geometry:
            self.editor.restoreGeometry(geometry)
        if state:
            self.editor.restoreState(state)

    def list_layouts(self) -> list[str]:
        """Return list of saved layouts."""
        self.settings.beginGroup("layouts")
        keys = self.settings.childGroups()
        self.settings.endGroup()
        return keys

    def restore_last_session(self) -> None:
        """Restore the layout from the last session."""
        self.load_layout("last_session")

    def save_current_session(self) -> None:
        """Save current state as last session."""
        self.save_layout("last_session")
