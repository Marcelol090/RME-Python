"""
Tileset Management UI (DEPRECATED - PySide6).

⚠️ WARNING: This file uses PySide6. The main application uses PyQt6.
   Do NOT import this file in production code.

Original purpose - Replaces source/tileset_window.cpp
"""

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
)


class TilesetDialog(QDialog):
    """
    Dialog for managing map tilesets.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tileset Configuration")
        self.resize(600, 450)

        main_layout = QHBoxLayout(self)

        # Left: List of Tilesets
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Available Tilesets:"))
        self.tileset_list = QListWidget()
        self.tileset_list.addItems(["Default", "Nature", "Cave", "City"])  # Dummy data
        left_panel.addWidget(self.tileset_list)

        # List controls
        list_btns = QHBoxLayout()
        self.btn_add = QPushButton("New")
        self.btn_remove = QPushButton("Remove")
        self.btn_duplicate = QPushButton("Duplicate")
        list_btns.addWidget(self.btn_add)
        list_btns.addWidget(self.btn_duplicate)
        list_btns.addWidget(self.btn_remove)
        left_panel.addLayout(list_btns)

        main_layout.addLayout(left_panel, 1)

        # Right: Details
        right_panel = QGroupBox("Properties")
        form_layout = QFormLayout(right_panel)

        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)

        self.chk_auto_border = QCheckBox("Enable Auto-Border")
        self.chk_auto_border.setChecked(True)
        form_layout.addRow(self.chk_auto_border)

        self.chk_randomize = QCheckBox("Enable Randomization")
        form_layout.addRow(self.chk_randomize)

        # Placeholder for Included IDs table
        self.ids_list = QListWidget()
        form_layout.addRow("Included Item IDs:", self.ids_list)

        main_layout.addWidget(right_panel, 2)

        # Note: Button box would need additional layout restructuring
        # This is a prototype/placeholder implementation


class AddTilesetDialog(QDialog):
    """
    Simple dialog to add a new tileset.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Tileset")
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Tileset Name")
        layout.addWidget(self.name_input)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
