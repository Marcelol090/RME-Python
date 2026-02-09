"""Assets Dock for managing loaded client resources."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QDockWidget,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class AssetsDock(QDockWidget):
    """Dock widget to display and manage loaded assets."""

    def __init__(self, editor: QtMapEditor, parent: QWidget | None = None) -> None:
        super().__init__("Assets", parent)
        self.editor = editor
        self._setup_ui()

        # Initial update
        self.update_info()

    def _setup_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Status Group
        status_group = QGroupBox("Current Profile")
        status_layout = QFormLayout(status_group)

        self.lbl_client_version = QLabel("Unknown")
        status_layout.addRow("Client:", self.lbl_client_version)

        self.lbl_engine = QLabel("Unknown")
        status_layout.addRow("Engine:", self.lbl_engine)

        self.lbl_assets_path = QLabel("Not set")
        self.lbl_assets_path.setWordWrap(True)
        status_layout.addRow("Path:", self.lbl_assets_path)

        layout.addWidget(status_group)

        # Loaded Files Group
        files_group = QGroupBox("Loaded Resources")
        files_layout = QFormLayout(files_group)

        self.lbl_dat = QLabel("Not loaded")
        files_layout.addRow("DAT:", self.lbl_dat)

        self.lbl_spr = QLabel("Not loaded")
        files_layout.addRow("SPR:", self.lbl_spr)

        self.lbl_otb = QLabel("Not loaded")
        files_layout.addRow("OTB:", self.lbl_otb)

        self.lbl_xml = QLabel("Not loaded")
        files_layout.addRow("XML:", self.lbl_xml)

        layout.addWidget(files_group)

        # Actions
        actions_layout = QHBoxLayout()

        self.btn_reload = QPushButton("Reload")
        self.btn_reload.clicked.connect(self._on_reload)
        actions_layout.addWidget(self.btn_reload)

        self.btn_change = QPushButton("Change...")
        self.btn_change.clicked.connect(self._on_change)
        actions_layout.addWidget(self.btn_change)

        layout.addLayout(actions_layout)
        layout.addStretch()

        self.setWidget(container)

    def update_info(self) -> None:
        """Update display from editor state."""
        # Profile
        self.lbl_client_version.setText(str(self.editor.client_version or "Unknown"))
        self.lbl_engine.setText(str(self.editor.engine or "Unknown"))
        self.lbl_assets_path.setText(str(self.editor.assets_dir or "Not set"))

        # Resources
        has_assets = self.editor.sprite_assets is not None
        self.lbl_dat.setText("Loaded" if has_assets else "Missing")
        self.lbl_spr.setText("Loaded" if has_assets else "Missing")

        # Definitions
        # We can check id_mapper or items_xml
        has_otb = False
        has_xml = False

        # Heuristic check
        if self.editor.id_mapper:
             has_otb = True # Likely OTB based

        # Ideally editor would expose this detail.
        self.lbl_otb.setText("Loaded" if has_otb else "—")
        self.lbl_xml.setText("Loaded" if has_xml else "—")

    def _on_reload(self) -> None:
        """Trigger reload."""
        if hasattr(self.editor, "_reload_item_definitions_for_current_context"):
            self.editor._reload_item_definitions_for_current_context(source="assets_dock")
            self.update_info()

    def _on_change(self) -> None:
        """Open client data loader."""
        if hasattr(self.editor, "_open_client_data_loader"):
            self.editor._open_client_data_loader()
            self.update_info()
