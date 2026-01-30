"""Import Map Dialog for py_rme_canary.

Provides UI for importing another map with offset and merge options.
Based on C++ import functionality.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


class ImportMapDialog(QDialog):
    """Dialog for importing another map with offset.

    Allows importing OTBM files into current map with:
    - X/Y/Z offset
    - Merge mode for items/creatures
    - House/spawn import options
    """

    def __init__(self, parent=None, *, current_map: GameMap | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Import Map")
        self.setModal(True)
        self.setMinimumWidth(450)

        self._current_map = current_map
        self._import_path: Path | None = None

        # Create UI
        layout = QVBoxLayout(self)

        # File selection
        file_group = QGroupBox("Map File")
        file_layout = QHBoxLayout(file_group)

        self._file_edit = QLineEdit()
        self._file_edit.setReadOnly(True)
        self._file_edit.setPlaceholderText("Select OTBM file to import...")
        file_layout.addWidget(self._file_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        file_layout.addWidget(browse_btn)

        layout.addWidget(file_group)

        # Offset settings
        offset_group = QGroupBox("Offset")
        offset_layout = QFormLayout(offset_group)

        self._offset_x_spin = QSpinBox()
        self._offset_x_spin.setRange(-32768, 32767)
        self._offset_x_spin.setValue(0)
        offset_layout.addRow("X Offset:", self._offset_x_spin)

        self._offset_y_spin = QSpinBox()
        self._offset_y_spin.setRange(-32768, 32767)
        self._offset_y_spin.setValue(0)
        offset_layout.addRow("Y Offset:", self._offset_y_spin)

        self._offset_z_spin = QSpinBox()
        self._offset_z_spin.setRange(-8, 8)
        self._offset_z_spin.setValue(0)
        offset_layout.addRow("Z Offset:", self._offset_z_spin)

        layout.addWidget(offset_group)

        # Import options
        options_group = QGroupBox("Import Options")
        options_layout = QVBoxLayout(options_group)

        self._import_tiles_chk = QCheckBox("Import tiles")
        self._import_tiles_chk.setChecked(True)
        options_layout.addWidget(self._import_tiles_chk)

        self._import_houses_chk = QCheckBox("Import houses")
        self._import_houses_chk.setChecked(True)
        options_layout.addWidget(self._import_houses_chk)

        self._import_spawns_chk = QCheckBox("Import spawns")
        self._import_spawns_chk.setChecked(True)
        options_layout.addWidget(self._import_spawns_chk)

        self._import_zones_chk = QCheckBox("Import zones")
        self._import_zones_chk.setChecked(False)
        options_layout.addWidget(self._import_zones_chk)

        layout.addWidget(options_group)

        # Merge mode
        merge_group = QGroupBox("Items/Creatures Merge Mode")
        merge_layout = QVBoxLayout(merge_group)
        self._merge_mode_group = QButtonGroup(self)

        self._merge_radio = QRadioButton("Merge - Combine with existing")
        self._merge_radio.setChecked(True)
        self._merge_mode_group.addButton(self._merge_radio, 0)
        merge_layout.addWidget(self._merge_radio)

        self._replace_radio = QRadioButton("Replace - Overwrite existing")
        self._merge_mode_group.addButton(self._replace_radio, 1)
        merge_layout.addWidget(self._replace_radio)

        self._skip_radio = QRadioButton("Skip - Don't import items/creatures")
        self._merge_mode_group.addButton(self._skip_radio, 2)
        merge_layout.addWidget(self._skip_radio)

        layout.addWidget(merge_group)

        # Dialog buttons
        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self._button_box.accepted.connect(self._on_import)
        self._button_box.rejected.connect(self.reject)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        layout.addWidget(self._button_box)

    def _browse_file(self) -> None:
        """Open file dialog to select OTBM file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Map to Import", "", "OTBM Files (*.otbm);;All Files (*)"
        )

        if file_path:
            self._import_path = Path(file_path)
            self._file_edit.setText(str(self._import_path))
            self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    def _on_import(self) -> None:
        """Handle import button click."""
        if not self._import_path:
            return

        if self._current_map is None:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(self, "Import Map", "No target map loaded.")
            return

        from PyQt6.QtWidgets import QMessageBox

        from py_rme_canary.logic_layer.operations.map_import import import_map_with_offset

        try:
            report = import_map_with_offset(
                target_map=self._current_map,
                source_path=self._import_path,
                offset=(
                    self._offset_x_spin.value(),
                    self._offset_y_spin.value(),
                    self._offset_z_spin.value(),
                ),
                import_tiles=self._import_tiles_chk.isChecked(),
                import_houses=self._import_houses_chk.isChecked(),
                import_spawns=self._import_spawns_chk.isChecked(),
                import_zones=self._import_zones_chk.isChecked(),
                merge_mode=self._merge_mode_group.checkedId(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "Import Map", str(exc))
            return

        summary = [
            f"Tiles imported: {report.tiles_imported}",
            f"Houses imported: {report.houses_imported}",
            f"Spawns imported: {report.spawns_imported}",
            f"Zones imported: {report.zones_imported}",
        ]
        if report.skipped_out_of_bounds:
            summary.append(f"Skipped (out of bounds): {report.skipped_out_of_bounds}")
        if report.house_id_mapping and any(k != v for k, v in report.house_id_mapping.items()):
            summary.append("House IDs remapped to avoid collisions.")
        if report.zone_id_mapping and any(k != v for k, v in report.zone_id_mapping.items()):
            summary.append("Zone IDs remapped to avoid collisions.")

        QMessageBox.information(self, "Import Complete", "\n".join(summary))
        self.accept()

    def get_import_settings(self) -> dict:
        """Get import settings configured by user.

        Returns:
            Dictionary with import configuration
        """
        return {
            "file_path": self._import_path,
            "offset_x": self._offset_x_spin.value(),
            "offset_y": self._offset_y_spin.value(),
            "offset_z": self._offset_z_spin.value(),
            "import_tiles": self._import_tiles_chk.isChecked(),
            "import_houses": self._import_houses_chk.isChecked(),
            "import_spawns": self._import_spawns_chk.isChecked(),
            "import_zones": self._import_zones_chk.isChecked(),
            "merge_mode": self._merge_mode_group.checkedId(),  # 0=Merge, 1=Replace, 2=Skip
        }
