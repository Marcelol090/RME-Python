"""Export Tilesets Dialog - Export tilesets to file.

Dialog for exporting map tilesets to XML/JSON files.
Mirrors legacy C++ ExportTilesetsWindow from source/ui/map/export_tilesets_window.cpp.

Reference:
    - C++ ExportTilesetsWindow: source/ui/map/export_tilesets_window.h
    - TilesetExporter: core/persistence/tileset_exporter.py
"""

from __future__ import annotations

import logging
from enum import IntEnum, auto
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager
from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ExportFormat(IntEnum):
    """Export format types."""

    XML = auto()
    JSON = auto()


class ExportTilesetsDialog(ModernDialog):
    """Dialog for exporting tilesets to files.

    Provides interface for:
    - Selecting tilesets to export
    - Choosing output directory and filename
    - Selecting export format (XML/JSON)
    - Configuring export options

    Signals:
        export_requested: Emitted when user confirms export.
            Args: (tilesets: list[str], path: Path, format: ExportFormat)
    """

    export_requested = pyqtSignal(list, Path, ExportFormat)

    def __init__(
        self,
        tilesets: list[str] | None = None,
        default_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize export tilesets dialog.

        Args:
            tilesets: List of available tileset names.
            default_path: Default export directory.
            parent: Parent widget.
        """
        super().__init__(parent, title="Export Tilesets")
        self._available_tilesets = tilesets or []
        self._default_path = default_path or Path.home()

        self.setMinimumSize(500, 450)
        self.setModal(True)

        self._populate_content()
        self._apply_style()
        self._load_tilesets()
        self._validate()

    def _populate_content(self) -> None:
        """Initialize UI components."""
        self.content_layout.setSpacing(16)

        # Header label removed as title is present in ModernDialog

        # Tileset selection group
        selection_group = QGroupBox("Select Tilesets")
        selection_layout = QVBoxLayout(selection_group)

        # Select all / none buttons
        btn_layout = QHBoxLayout()

        self._btn_select_all = QPushButton("Select All")
        self._btn_select_all.clicked.connect(self._select_all)
        btn_layout.addWidget(self._btn_select_all)

        self._btn_select_none = QPushButton("Select None")
        self._btn_select_none.clicked.connect(self._select_none)
        btn_layout.addWidget(self._btn_select_none)

        btn_layout.addStretch()
        selection_layout.addLayout(btn_layout)

        # Tileset list
        self._tileset_list = QListWidget()
        self._tileset_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._tileset_list.itemSelectionChanged.connect(self._validate)
        selection_layout.addWidget(self._tileset_list)

        # Selection count
        self._selection_label = QLabel("0 tilesets selected")
        self._selection_label.setObjectName("selectionLabel")
        selection_layout.addWidget(self._selection_label)

        self.content_layout.addWidget(selection_group, 1)

        # Output configuration group
        output_group = QGroupBox("Output Configuration")
        output_layout = QFormLayout(output_group)
        output_layout.setSpacing(12)

        # Directory selection
        dir_layout = QHBoxLayout()

        self._directory_edit = QLineEdit()
        self._directory_edit.setText(str(self._default_path))
        self._directory_edit.textChanged.connect(self._validate)
        dir_layout.addWidget(self._directory_edit, 1)

        self._btn_browse = QPushButton("Browse...")
        self._btn_browse.clicked.connect(self._browse_directory)
        dir_layout.addWidget(self._btn_browse)

        output_layout.addRow("Directory:", dir_layout)

        # Filename
        self._filename_edit = QLineEdit()
        self._filename_edit.setText("tilesets")
        self._filename_edit.setPlaceholderText("Export filename (without extension)")
        self._filename_edit.textChanged.connect(self._validate)
        output_layout.addRow("Filename:", self._filename_edit)

        # Format selection
        self._format_combo = QComboBox()
        self._format_combo.addItem("XML (.xml)", ExportFormat.XML)
        self._format_combo.addItem("JSON (.json)", ExportFormat.JSON)
        self._format_combo.currentIndexChanged.connect(self._on_format_changed)
        output_layout.addRow("Format:", self._format_combo)

        self.content_layout.addWidget(output_group)

        # Options group
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)

        self._include_items_check = QCheckBox("Include item details")
        self._include_items_check.setChecked(True)
        self._include_items_check.setToolTip("Include full item information in export")
        options_layout.addWidget(self._include_items_check)

        self._pretty_print_check = QCheckBox("Pretty print (formatted output)")
        self._pretty_print_check.setChecked(True)
        self._pretty_print_check.setToolTip("Format output for readability")
        options_layout.addWidget(self._pretty_print_check)

        self._overwrite_check = QCheckBox("Overwrite existing files")
        self._overwrite_check.setChecked(False)
        self._overwrite_check.setToolTip("Replace files if they already exist")
        options_layout.addWidget(self._overwrite_check)

        self.content_layout.addWidget(options_group)

        # Error message area
        self._error_label = QLabel()
        self._error_label.setObjectName("errorLabel")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        self.content_layout.addWidget(self._error_label)

        # Preview of output path
        self._preview_label = QLabel()
        self._preview_label.setObjectName("previewLabel")
        self.content_layout.addWidget(self._preview_label)

        # Dialog buttons
        self.add_spacer_to_footer()
        self.add_button("Cancel", callback=self.reject)
        self._ok_button = self.add_button("Export", callback=self._on_accept, role="primary")

    def _apply_style(self) -> None:
        """Apply dark theme styling."""
        c = get_theme_manager().tokens["color"]
        r = get_theme_manager().tokens.get("radius", {})
        rad = r.get("md", 6)
        rad_sm = r.get("sm", 4)

        self.content_area.setStyleSheet(
            f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {c['border']['default']};
                border-radius: {rad}px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: {c['surface']['secondary']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {c['brand']['secondary']};
            }}
            QLabel {{
                color: {c['text']['primary']};
            }}
            QLabel#headerLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {c['brand']['secondary']};
            }}
            QLabel#selectionLabel {{
                font-size: 11px;
                color: {c['text']['tertiary']};
            }}
            QLabel#errorLabel {{
                font-size: 11px;
                color: {c['state']['error']};
                padding: 8px;
                background-color: rgba(243, 139, 168, 0.1);
                border-radius: {rad_sm}px;
            }}
            QLabel#previewLabel {{
                font-size: 11px;
                color: {c['brand']['active']};
                padding: 8px;
                background-color: {c['surface']['tertiary']};
                border-radius: {rad_sm}px;
            }}
            QListWidget {{
                background-color: {c['surface']['tertiary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
                color: {c['text']['primary']};
            }}
            QListWidget::item {{
                padding: 6px;
            }}
            QListWidget::item:selected {{
                background-color: {c['brand']['secondary']};
            }}
            QListWidget::item:hover {{
                background-color: {c['border']['default']};
            }}
            QLineEdit {{
                background-color: {c['surface']['tertiary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
                padding: 8px;
                color: {c['text']['primary']};
            }}
            QLineEdit:focus {{
                border-color: {c['brand']['secondary']};
            }}
            QComboBox {{
                background-color: {c['surface']['tertiary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
                padding: 8px 12px;
                color: {c['text']['primary']};
            }}
            QComboBox:focus {{
                border-color: {c['brand']['secondary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {c['text']['primary']};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['surface']['tertiary']};
                border: 1px solid {c['border']['default']};
                selection-background-color: {c['brand']['secondary']};
                color: {c['text']['primary']};
            }}
            QCheckBox {{
                color: {c['text']['primary']};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: {rad_sm}px;
                border: 1px solid {c['border']['default']};
                background-color: {c['surface']['tertiary']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {c['brand']['secondary']};
                border-color: {c['brand']['secondary']};
            }}
            QPushButton {{
                background-color: {c['border']['default']};
                border: none;
                border-radius: {rad}px;
                padding: 8px 16px;
                color: {c['text']['primary']};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {c['border']['strong']};
            }}
            QPushButton:pressed {{
                background-color: {c['brand']['secondary']};
            }}
            QPushButton:disabled {{
                background-color: {c['surface']['tertiary']};
                color: {c['text']['tertiary']};
            }}
            QDialogButtonBox QPushButton {{
                min-width: 90px;
            }}
        """
        )

    def _load_tilesets(self) -> None:
        """Load available tilesets into list."""
        self._tileset_list.clear()

        for name in sorted(self._available_tilesets):
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, name)
            self._tileset_list.addItem(item)

    def _select_all(self) -> None:
        """Select all tilesets."""
        self._tileset_list.selectAll()

    def _select_none(self) -> None:
        """Deselect all tilesets."""
        self._tileset_list.clearSelection()

    def _browse_directory(self) -> None:
        """Open directory browser."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            self._directory_edit.text(),
            QFileDialog.Option.ShowDirsOnly,
        )
        if directory:
            self._directory_edit.setText(directory)

    def _on_format_changed(self, index: int) -> None:
        """Handle format selection change."""
        self._update_preview()

    def _validate(self) -> None:
        """Validate inputs and update UI state."""
        errors = []
        selected_count = len(self._tileset_list.selectedItems())

        # Update selection label
        self._selection_label.setText(f"{selected_count} tileset(s) selected")

        # Check selection
        if selected_count == 0:
            errors.append("Select at least one tileset to export")

        # Check directory
        directory = Path(self._directory_edit.text())
        if not directory.exists():
            errors.append(f"Directory does not exist: {directory}")
        elif not directory.is_dir():
            errors.append("Path is not a directory")

        # Check filename
        filename = self._filename_edit.text().strip()
        if not filename:
            errors.append("Filename cannot be empty")
        elif any(c in filename for c in r'<>:"/\|?*'):
            errors.append("Filename contains invalid characters")

        # Update error display
        if errors:
            self._error_label.setText("\n".join(errors))
            self._error_label.show()
            self._ok_button.setEnabled(False)
        else:
            self._error_label.hide()
            self._ok_button.setEnabled(True)

        self._update_preview()

    def _update_preview(self) -> None:
        """Update output path preview."""
        directory = self._directory_edit.text()
        filename = self._filename_edit.text().strip()
        format_enum = self._format_combo.currentData()

        if format_enum == ExportFormat.XML:
            ext = ".xml"
        else:
            ext = ".json"

        if filename and directory:
            full_path = Path(directory) / f"{filename}{ext}"
            self._preview_label.setText(f"Output: {full_path}")
        else:
            self._preview_label.setText("Output: (invalid)")

    def _on_accept(self) -> None:
        """Handle Export button click."""
        # Get selected tilesets
        selected = [item.data(Qt.ItemDataRole.UserRole) for item in self._tileset_list.selectedItems()]

        # Build output path
        directory = Path(self._directory_edit.text())
        filename = self._filename_edit.text().strip()
        format_enum = self._format_combo.currentData()

        if format_enum == ExportFormat.XML:
            ext = ".xml"
        else:
            ext = ".json"

        output_path = directory / f"{filename}{ext}"

        # Check for existing file
        if output_path.exists() and not self._overwrite_check.isChecked():
            from PyQt6.QtWidgets import QMessageBox

            result = QMessageBox.question(
                self,
                "File Exists",
                f"File already exists:\n{output_path}\n\nOverwrite?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if result != QMessageBox.StandardButton.Yes:
                return

        # Emit export signal
        self.export_requested.emit(selected, output_path, format_enum)
        self.accept()

    def get_selected_tilesets(self) -> list[str]:
        """Get names of selected tilesets.

        Returns:
            List of selected tileset names.
        """
        return [item.data(Qt.ItemDataRole.UserRole) for item in self._tileset_list.selectedItems()]

    def get_export_path(self) -> Path:
        """Get the export output path.

        Returns:
            The full output file path.
        """
        directory = Path(self._directory_edit.text())
        filename = self._filename_edit.text().strip()
        format_enum = self._format_combo.currentData()

        if format_enum == ExportFormat.XML:
            ext = ".xml"
        else:
            ext = ".json"

        return directory / f"{filename}{ext}"

    def get_export_format(self) -> ExportFormat:
        """Get the selected export format.

        Returns:
            The export format enum value.
        """
        return self._format_combo.currentData()

    def get_options(self) -> dict:
        """Get export options.

        Returns:
            Dictionary with include_items, pretty_print, overwrite options.
        """
        return {
            "include_items": self._include_items_check.isChecked(),
            "pretty_print": self._pretty_print_check.isChecked(),
            "overwrite": self._overwrite_check.isChecked(),
        }

    def set_available_tilesets(self, tilesets: list[str]) -> None:
        """Set available tilesets.

        Args:
            tilesets: List of tileset names.
        """
        self._available_tilesets = tilesets
        self._load_tilesets()
