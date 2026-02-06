"""Preferences Dialog for py_rme_canary.

Ported from C++ PreferencesWindow (preferences.cpp - 735 lines).
Provides configuration UI with tabs: General, Editor, Graphics, Interface, Client Folder.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.core.config.user_settings import get_user_settings

if TYPE_CHECKING:
    from py_rme_canary.core.config.configuration_manager import ConfigurationManager


class PreferencesDialog(QDialog):
    """Preferences dialog with multiple configuration tabs.

    Provides UI for editing application settings:
    - General: Welcome dialog, backups, updates, undo settings
    - Editor: Editor-specific options
    - Graphics: Rendering and visual options
    - Interface: UI customization
    - Client Folder: Asset folder selection

    Based on C++ PreferencesWindow (preferences.cpp).
    """

    settings_changed = pyqtSignal()  # Emitted when user clicks Apply or OK

    def __init__(self, parent: QWidget | None = None, *, config_manager: ConfigurationManager | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.setMinimumSize(500, 400)

        self._config_manager = config_manager
        self._settings: dict[str, any] = {}
        self._load_current_settings()

        # Create tabs
        self._tabs = QTabWidget(self)
        self._tabs.addTab(self._create_general_page(), "General")
        self._tabs.addTab(self._create_editor_page(), "Editor")
        self._tabs.addTab(self._create_graphics_page(), "Graphics")
        self._tabs.addTab(self._create_ui_page(), "Interface")
        self._tabs.addTab(self._create_client_page(), "Client Folder")

        # Buttons
        self._button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        self._button_box.accepted.connect(self._on_ok)
        self._button_box.rejected.connect(self.reject)
        self._button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self._tabs)
        layout.addWidget(self._button_box)

    def _load_current_settings(self) -> None:
        """Load current settings from config manager or defaults."""
        # TODO: Load from actual config.toml or ConfigurationManager
        user_settings = get_user_settings()
        self._settings = {
            "show_welcome_dialog": True,
            "always_make_backup": True,
            "check_updates_on_startup": False,
            "only_one_instance": True,
            "enable_tileset_editing": False,
            "use_old_item_properties_window": False,
            "undo_queue_size": 1000,
            "undo_max_memory_mb": 256,
            "worker_threads": 4,
            "replace_count_limit": 10000,
            "delete_backup_days": 7,
            "copy_position_format": 0,  # 0-4 for different formats
            "client_assets_folder": user_settings.get_client_assets_folder(),
            "default_client_version": user_settings.get_default_client_version(),
            "auto_load_appearances": user_settings.get_auto_load_appearances(),
            "sprite_match_on_paste": user_settings.get_sprite_match_on_paste(),
        }

    def _create_general_page(self) -> QWidget:
        """Create General settings tab.

        Settings:
        - Welcome dialog on startup
        - Always make backup
        - Check for updates
        - Only one instance
        - Enable tileset editing
        - Old item properties window
        - Undo queue size
        - Undo memory limit
        - Worker threads
        - Replace count
        - Delete backup days
        - Copy position format
        """
        page = QWidget()
        layout = QVBoxLayout(page)

        # Checkboxes
        self._show_welcome_chk = QCheckBox("Show welcome dialog on startup")
        self._show_welcome_chk.setChecked(self._settings["show_welcome_dialog"])
        self._show_welcome_chk.setToolTip("Show welcome dialog when starting the editor")
        layout.addWidget(self._show_welcome_chk)

        self._always_backup_chk = QCheckBox("Always make map backup")
        self._always_backup_chk.setChecked(self._settings["always_make_backup"])
        layout.addWidget(self._always_backup_chk)

        self._check_updates_chk = QCheckBox("Check for updates on startup")
        self._check_updates_chk.setChecked(self._settings["check_updates_on_startup"])
        layout.addWidget(self._check_updates_chk)

        self._only_one_instance_chk = QCheckBox("Open all maps in the same instance")
        self._only_one_instance_chk.setChecked(self._settings["only_one_instance"])
        self._only_one_instance_chk.setToolTip(
            "When checked, maps opened using the shell will all be opened in the same instance"
        )
        layout.addWidget(self._only_one_instance_chk)

        self._enable_tileset_editing_chk = QCheckBox("Enable tileset editing")
        self._enable_tileset_editing_chk.setChecked(self._settings["enable_tileset_editing"])
        self._enable_tileset_editing_chk.setToolTip("Show tileset editing options")
        layout.addWidget(self._enable_tileset_editing_chk)

        self._use_old_properties_chk = QCheckBox("Use old item properties window")
        self._use_old_properties_chk.setChecked(self._settings["use_old_item_properties_window"])
        self._use_old_properties_chk.setToolTip("Enables the use of the old item properties window")
        layout.addWidget(self._use_old_properties_chk)

        layout.addSpacing(10)

        # Numeric settings
        form = QFormLayout()

        self._undo_size_spin = QSpinBox()
        self._undo_size_spin.setRange(0, 0x10000000)
        self._undo_size_spin.setValue(self._settings["undo_queue_size"])
        self._undo_size_spin.setToolTip("How many actions you can undo (high values increase memory usage)")
        form.addRow("Undo queue size:", self._undo_size_spin)

        self._undo_mem_spin = QSpinBox()
        self._undo_mem_spin.setRange(0, 4096)
        self._undo_mem_spin.setValue(self._settings["undo_max_memory_mb"])
        self._undo_mem_spin.setToolTip("Approximate memory limit for undo queue (MB)")
        form.addRow("Undo max memory (MB):", self._undo_mem_spin)

        self._worker_threads_spin = QSpinBox()
        self._worker_threads_spin.setRange(1, 64)
        self._worker_threads_spin.setValue(self._settings["worker_threads"])
        self._worker_threads_spin.setToolTip(
            "Number of threads for intensive operations (should match logical CPU cores)"
        )
        form.addRow("Worker threads:", self._worker_threads_spin)

        self._default_client_version_spin = QSpinBox()
        self._default_client_version_spin.setRange(0, 2000)
        self._default_client_version_spin.setValue(self._settings["default_client_version"])
        self._default_client_version_spin.setToolTip(
            "Default Tibia client version for new maps (0 = unknown/ask later)"
        )
        form.addRow("Default client version:", self._default_client_version_spin)

        self._replace_size_spin = QSpinBox()
        self._replace_size_spin.setRange(0, 100000)
        self._replace_size_spin.setValue(self._settings["replace_count_limit"])
        self._replace_size_spin.setToolTip("Maximum items to replace using Replace Item tool")
        form.addRow("Replace count limit:", self._replace_size_spin)

        self._delete_backup_days_spin = QSpinBox()
        self._delete_backup_days_spin.setRange(0, 365)
        self._delete_backup_days_spin.setValue(self._settings["delete_backup_days"])
        self._delete_backup_days_spin.setToolTip("Number of days before backups are automatically deleted")
        form.addRow("Delete backup after (days):", self._delete_backup_days_spin)

        layout.addLayout(form)
        layout.addSpacing(10)

        # Position format radio buttons
        pos_group = QGroupBox("Copy Position Format")
        pos_layout = QVBoxLayout(pos_group)
        self._pos_format_group = QButtonGroup(self)

        formats = [
            "  {x = 0, y = 0, z = 0}",
            '  {"x":0,"y":0,"z":0}',
            "  x, y, z",
            "  (x, y, z)",
            "  Position(x, y, z)",
        ]

        for idx, fmt in enumerate(formats):
            radio = QRadioButton(fmt)
            self._pos_format_group.addButton(radio, idx)
            pos_layout.addWidget(radio)
            if idx == self._settings["copy_position_format"]:
                radio.setChecked(True)

        layout.addWidget(pos_group)
        layout.addStretch()

        return page

    def _create_editor_page(self) -> QWidget:
        """Create Editor settings tab."""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Cross-version clipboard
        cross_version_group = QGroupBox("Cross-Version Copy/Paste")
        cross_version_layout = QVBoxLayout(cross_version_group)

        self._sprite_match_paste_chk = QCheckBox("Enable sprite match on paste (cross-version)")
        self._sprite_match_paste_chk.setChecked(self._settings["sprite_match_on_paste"])
        self._sprite_match_paste_chk.setToolTip(
            "When enabled, pasted items are matched by sprite hash across different client versions.\n"
            "This allows copying from one RME instance to another with different client files."
        )
        cross_version_layout.addWidget(self._sprite_match_paste_chk)

        info_label = QLabel(
            "This feature uses FNV-1a sprite hash matching to find equivalent sprites\n"
            "when pasting between different client versions (e.g., 10.98 → 13.x)."
        )
        info_label.setStyleSheet("color: #888; font-size: 10px;")
        info_label.setWordWrap(True)
        cross_version_layout.addWidget(info_label)

        layout.addWidget(cross_version_group)
        layout.addStretch()

        return page

    def _create_graphics_page(self) -> QWidget:
        """Create Graphics settings tab."""
        page = QWidget()
        layout = QVBoxLayout(page)

        label = QLabel("Graphics and rendering settings will be added here.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addStretch()

        return page

    def _create_ui_page(self) -> QWidget:
        """Create Interface settings tab."""
        page = QWidget()
        layout = QVBoxLayout(page)

        label = QLabel("UI customization settings will be added here.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addStretch()

        return page

    def _create_client_page(self) -> QWidget:
        """Create Client Folder settings tab."""
        page = QWidget()
        layout = QVBoxLayout(page)

        form = QFormLayout()

        # Assets folder picker
        folder_layout = QHBoxLayout()
        self._assets_folder_edit = QLineEdit(self._settings["client_assets_folder"])
        self._assets_folder_edit.setReadOnly(True)
        folder_layout.addWidget(self._assets_folder_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_assets_folder)
        folder_layout.addWidget(browse_btn)

        form.addRow("Client assets folder:", folder_layout)

        self._auto_load_appearances_chk = QCheckBox("Auto-load appearances.dat when available")
        self._auto_load_appearances_chk.setChecked(bool(self._settings.get("auto_load_appearances", True)))
        self._auto_load_appearances_chk.setToolTip(
            "If disabled, the editor will skip appearances.dat and use legacy sprites."
        )
        form.addRow(self._auto_load_appearances_chk)

        layout.addLayout(form)
        layout.addStretch()

        return page

    def _browse_assets_folder(self) -> None:
        """Open directory picker for client assets folder."""
        current_path = self._assets_folder_edit.text()
        folder = QFileDialog.getExistingDirectory(self, "Select Client Assets Folder", current_path or str(Path.home()))
        if folder:
            self._assets_folder_edit.setText(folder)

    def _save_settings(self) -> None:
        """Save current UI state to settings dict."""
        self._settings["show_welcome_dialog"] = self._show_welcome_chk.isChecked()
        self._settings["always_make_backup"] = self._always_backup_chk.isChecked()
        self._settings["check_updates_on_startup"] = self._check_updates_chk.isChecked()
        self._settings["only_one_instance"] = self._only_one_instance_chk.isChecked()
        self._settings["enable_tileset_editing"] = self._enable_tileset_editing_chk.isChecked()
        self._settings["use_old_item_properties_window"] = self._use_old_properties_chk.isChecked()

        self._settings["undo_queue_size"] = self._undo_size_spin.value()
        self._settings["undo_max_memory_mb"] = self._undo_mem_spin.value()
        self._settings["worker_threads"] = self._worker_threads_spin.value()
        self._settings["replace_count_limit"] = self._replace_size_spin.value()
        self._settings["delete_backup_days"] = self._delete_backup_days_spin.value()
        self._settings["default_client_version"] = self._default_client_version_spin.value()

        self._settings["copy_position_format"] = self._pos_format_group.checkedId()
        self._settings["client_assets_folder"] = self._assets_folder_edit.text()
        self._settings["auto_load_appearances"] = bool(self._auto_load_appearances_chk.isChecked())
        self._settings["sprite_match_on_paste"] = bool(self._sprite_match_paste_chk.isChecked())

        user_settings = get_user_settings()
        user_settings.set_default_client_version(int(self._settings["default_client_version"]))
        user_settings.set_client_assets_folder(str(self._settings["client_assets_folder"]))
        user_settings.set_auto_load_appearances(bool(self._settings["auto_load_appearances"]))
        user_settings.set_sprite_match_on_paste(bool(self._settings["sprite_match_on_paste"]))

        # TODO: Write to config.toml or ConfigurationManager
        print(f"[PreferencesDialog] Settings saved: {self._settings}")

    def _on_apply(self) -> None:
        """Handle Apply button click."""
        self._save_settings()
        self.settings_changed.emit()

    def _on_ok(self) -> None:
        """Handle OK button click."""
        self._save_settings()
        self.settings_changed.emit()
        self.accept()

    def get_settings(self) -> dict[str, any]:
        """Get current settings dictionary.

        Returns:
            Dictionary of setting key-value pairs
        """
        return self._settings.copy()
