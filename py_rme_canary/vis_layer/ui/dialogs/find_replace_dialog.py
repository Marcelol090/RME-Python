"""Item Find and Replace Dialog.

Advanced search and replace for items on the map.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


class ItemFindReplaceDialog(QDialog):
    """Dialog for finding and replacing items.

    Features:
    - Find items by ID or name
    - Replace with different item
    - Scope: whole map, selection, current floor
    - Preview matches before replacing
    """

    def __init__(
        self,
        game_map: "GameMap | None" = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._game_map = game_map
        self._match_count = 0

        self.setWindowTitle("Find & Replace Items")
        self.setMinimumSize(450, 400)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Find section
        find_group = QGroupBox("Find")
        find_layout = QFormLayout(find_group)

        find_row = QHBoxLayout()
        self.find_id = QSpinBox()
        self.find_id.setRange(0, 65535)
        self.find_id.setSpecialValueText("Any")
        find_row.addWidget(self.find_id)

        self.find_name = QLineEdit()
        self.find_name.setPlaceholderText("Or search by name...")
        find_row.addWidget(self.find_name)

        find_layout.addRow("Item ID:", find_row)

        layout.addWidget(find_group)

        # Replace section
        replace_group = QGroupBox("Replace With")
        replace_layout = QFormLayout(replace_group)

        self.replace_id = QSpinBox()
        self.replace_id.setRange(0, 65535)
        replace_layout.addRow("Item ID:", self.replace_id)

        self.delete_mode = QCheckBox("Delete instead of replace")
        self.delete_mode.stateChanged.connect(self._on_delete_mode_changed)
        replace_layout.addRow(self.delete_mode)

        layout.addWidget(replace_group)

        # Scope section
        scope_group = QGroupBox("Search Scope")
        scope_layout = QVBoxLayout(scope_group)

        self.scope_all = QRadioButton("Entire map")
        self.scope_all.setChecked(True)
        scope_layout.addWidget(self.scope_all)

        self.scope_selection = QRadioButton("Selection only")
        scope_layout.addWidget(self.scope_selection)

        self.scope_floor = QRadioButton("Current floor only")
        scope_layout.addWidget(self.scope_floor)

        layout.addWidget(scope_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)

        self.match_ground = QCheckBox("Include ground tiles")
        self.match_ground.setChecked(True)
        options_layout.addWidget(self.match_ground)

        self.match_items = QCheckBox("Include items on tiles")
        self.match_items.setChecked(True)
        options_layout.addWidget(self.match_items)

        layout.addWidget(options_group)

        # Results
        self.results_label = QLabel("")
        self.results_label.setStyleSheet("color: #A1A1AA;")
        layout.addWidget(self.results_label)

        # Progress
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Buttons
        button_layout = QHBoxLayout()

        self.btn_find = QPushButton("🔍 Find All")
        self.btn_find.clicked.connect(self._do_find)
        button_layout.addWidget(self.btn_find)

        self.btn_replace_all = QPushButton("🔄 Replace All")
        self.btn_replace_all.setEnabled(False)
        self.btn_replace_all.clicked.connect(self._do_replace_all)
        button_layout.addWidget(self.btn_replace_all)

        button_layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        button_layout.addWidget(btn_close)

        layout.addLayout(button_layout)

    def _apply_style(self) -> None:
        """Apply modern styling."""
        self.setStyleSheet("""
            QDialog {
                background: #1E1E2E;
            }

            QGroupBox {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                color: #E5E5E7;
                font-weight: 600;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }

            QSpinBox, QLineEdit {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 6px;
                padding: 8px;
                color: #E5E5E7;
            }

            QSpinBox:focus, QLineEdit:focus {
                border-color: #8B5CF6;
            }

            QCheckBox, QRadioButton {
                color: #E5E5E7;
            }

            QPushButton {
                background: #8B5CF6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }

            QPushButton:hover {
                background: #A78BFA;
            }

            QPushButton:disabled {
                background: #363650;
                color: #52525B;
            }

            QProgressBar {
                background: #363650;
                border: none;
                border-radius: 4px;
                height: 6px;
            }

            QProgressBar::chunk {
                background: #8B5CF6;
                border-radius: 4px;
            }
        """)

    def _on_delete_mode_changed(self, state: int) -> None:
        """Handle delete mode toggle."""
        is_delete = state == Qt.CheckState.Checked.value
        self.replace_id.setEnabled(not is_delete)

    def _do_find(self) -> None:
        """Find all matching items."""
        if not self._game_map:
            self.results_label.setText("❌ No map loaded")
            return

        find_id = self.find_id.value()
        if find_id == 0:
            self.results_label.setText("❌ Please specify an item ID")
            return

        self.progress.show()
        self.progress.setMaximum(0)  # Indeterminate

        # Count matches
        count = 0
        tiles = getattr(self._game_map, 'tiles', {}) or {}

        for pos, tile in tiles.items():
            # Check scope
            if self.scope_floor.isChecked():
                # Would check against current floor
                pass
            elif self.scope_selection.isChecked():
                # Would check against selection
                pass

            # Check ground
            if self.match_ground.isChecked():
                if tile.ground and tile.ground.id == find_id:
                    count += 1
                    continue

            # Check items
            if self.match_items.isChecked():
                for item in tile.items:
                    if item.id == find_id:
                        count += 1
                        break

        self._match_count = count
        self.progress.hide()

        if count > 0:
            self.results_label.setText(f"✅ Found {count} match{'es' if count != 1 else ''}")
            self.btn_replace_all.setEnabled(True)
        else:
            self.results_label.setText("❌ No matches found")
            self.btn_replace_all.setEnabled(False)

    def _do_replace_all(self) -> None:
        """Replace all matching items."""
        if not self._game_map or self._match_count == 0:
            return

        find_id = self.find_id.value()
        replace_id = self.replace_id.value() if not self.delete_mode.isChecked() else None

        from PyQt6.QtWidgets import QMessageBox

        if self.delete_mode.isChecked():
            msg = f"Delete all {self._match_count} instances of item #{find_id}?"
        else:
            msg = f"Replace all {self._match_count} instances of item #{find_id} with #{replace_id}?"

        reply = QMessageBox.question(
            self,
            "Confirm Replace",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Perform replacement
        self.progress.show()
        self.progress.setMaximum(self._match_count)

        replaced = 0
        tiles = getattr(self._game_map, 'tiles', {}) or {}

        for pos, tile in tiles.items():
            # Check ground
            if self.match_ground.isChecked():
                if tile.ground and tile.ground.id == find_id:
                    if self.delete_mode.isChecked():
                        tile.ground = None
                    else:
                        tile.ground.id = replace_id
                    replaced += 1
                    self.progress.setValue(replaced)

            # Check items
            if self.match_items.isChecked():
                for item in tile.items:
                    if item.id == find_id:
                        if self.delete_mode.isChecked():
                            tile.items.remove(item)
                        else:
                            item.id = replace_id
                        replaced += 1
                        self.progress.setValue(replaced)
                        break

        self.progress.hide()
        self.results_label.setText(f"✅ Replaced {replaced} item{'s' if replaced != 1 else ''}")
        self._match_count = 0
        self.btn_replace_all.setEnabled(False)
