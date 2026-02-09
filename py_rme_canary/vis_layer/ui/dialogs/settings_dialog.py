"""Settings/Preferences Dialog.

Modern settings dialog with categories:
- General settings
- Editor behavior
- Appearance/Theme
- Keyboard shortcuts
- Performance

Refactored to use ModernDialog.
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QMessageBox
)

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager


class SettingsCategory(QFrame):
    """Base class for settings category widgets."""

    settings_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._changed = False
        # Remove frame styling as it will be inside ModernDialog
        self.setFrameShape(QFrame.Shape.NoFrame)

    def has_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self._changed

    def mark_changed(self) -> None:
        """Mark as having changes."""
        self._changed = True
        self.settings_changed.emit()

    def apply_settings(self) -> None:
        """Apply current settings."""
        self._changed = False

    def reset_settings(self) -> None:
        """Reset to default values."""
        pass


class GeneralSettings(SettingsCategory):
    """General application settings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        tm = get_theme_manager()
        c = tm.tokens["color"]

        # Title
        title = QLabel("General Settings")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c['text']['primary']};")
        layout.addWidget(title)

        # Form
        form = QFormLayout()
        form.setSpacing(12)

        # Auto-save
        self.auto_save = QCheckBox("Auto-save every")
        self.auto_save.setChecked(True)
        self.auto_save.stateChanged.connect(self.mark_changed)

        auto_save_row = QHBoxLayout()
        auto_save_row.addWidget(self.auto_save)

        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setValue(5)
        self.auto_save_interval.setSuffix(" min")
        self.auto_save_interval.valueChanged.connect(self.mark_changed)
        auto_save_row.addWidget(self.auto_save_interval)
        auto_save_row.addStretch()

        form.addRow(auto_save_row)

        # Create backup
        self.create_backup = QCheckBox("Create backup on save")
        self.create_backup.setChecked(True)
        self.create_backup.stateChanged.connect(self.mark_changed)
        form.addRow(self.create_backup)

        # Show welcome
        self.show_welcome = QCheckBox("Show welcome screen on startup")
        self.show_welcome.setChecked(True)
        self.show_welcome.stateChanged.connect(self.mark_changed)
        form.addRow(self.show_welcome)

        # Recent files count
        self.recent_count = QSpinBox()
        self.recent_count.setRange(0, 20)
        self.recent_count.setValue(10)
        self.recent_count.valueChanged.connect(self.mark_changed)
        form.addRow("Recent files to show:", self.recent_count)

        # Default client version (used for new maps)
        self.default_client_version = QSpinBox()
        self.default_client_version.setRange(0, 2000)
        self.default_client_version.setObjectName("default_client_version")
        self.default_client_version.setToolTip("Default Tibia client version for new maps (0 = unknown)")
        try:
            from py_rme_canary.core.config.user_settings import get_user_settings

            self.default_client_version.setValue(get_user_settings().get_default_client_version())
        except Exception:
            self.default_client_version.setValue(0)
        self.default_client_version.valueChanged.connect(self.mark_changed)
        form.addRow("Default client version:", self.default_client_version)

        self.auto_load_appearances = QCheckBox("Auto-load appearances.dat when available")
        self.auto_load_appearances.setObjectName("auto_load_appearances")
        try:
            from py_rme_canary.core.config.user_settings import get_user_settings

            self.auto_load_appearances.setChecked(get_user_settings().get_auto_load_appearances())
        except Exception:
            self.auto_load_appearances.setChecked(True)
        self.auto_load_appearances.stateChanged.connect(self.mark_changed)
        form.addRow(self.auto_load_appearances)

        layout.addLayout(form)
        layout.addStretch()


class EditorSettings(SettingsCategory):
    """Editor behavior settings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        tm = get_theme_manager()
        c = tm.tokens["color"]

        title = QLabel("Editor Settings")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c['text']['primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        # Default brush size
        self.default_brush_size = QSpinBox()
        self.default_brush_size.setRange(1, 11)
        self.default_brush_size.setValue(1)
        self.default_brush_size.valueChanged.connect(self.mark_changed)
        form.addRow("Default brush size:", self.default_brush_size)

        # Undo limit
        self.undo_limit = QSpinBox()
        self.undo_limit.setRange(10, 500)
        self.undo_limit.setValue(100)
        self.undo_limit.setSingleStep(10)
        self.undo_limit.valueChanged.connect(self.mark_changed)
        form.addRow("Undo history limit:", self.undo_limit)

        # Automagic enabled by default
        self.automagic_default = QCheckBox("Enable automagic by default")
        self.automagic_default.setChecked(True)
        self.automagic_default.stateChanged.connect(self.mark_changed)
        form.addRow(self.automagic_default)

        # Merge paste (combine items vs replace)
        self.merge_paste = QCheckBox("Merge when pasting (don't replace)")
        self.merge_paste.setChecked(False)
        self.merge_paste.stateChanged.connect(self.mark_changed)
        form.addRow(self.merge_paste)

        # Borderize after paste
        self.borderize_paste = QCheckBox("Auto-borderize after paste")
        self.borderize_paste.setChecked(True)
        self.borderize_paste.stateChanged.connect(self.mark_changed)
        form.addRow(self.borderize_paste)

        # Sprite match on paste (cross-version)
        self.sprite_match_paste = QCheckBox("Sprite match on paste (cross-version)")
        self.sprite_match_paste.setObjectName("sprite_match_on_paste")
        self.sprite_match_paste.setToolTip(
            "Enable sprite hash matching for cross-version copy/paste.\n"
            "Allows copying between RME instances with different client versions."
        )
        try:
            from py_rme_canary.core.config.user_settings import get_user_settings

            self.sprite_match_paste.setChecked(get_user_settings().get_sprite_match_on_paste())
        except Exception:
            self.sprite_match_paste.setChecked(True)
        self.sprite_match_paste.stateChanged.connect(self.mark_changed)
        form.addRow(self.sprite_match_paste)

        # Default floor
        self.default_floor = QSpinBox()
        self.default_floor.setRange(0, 15)
        self.default_floor.setValue(7)
        self.default_floor.valueChanged.connect(self.mark_changed)
        form.addRow("Default floor (Z):", self.default_floor)

        layout.addLayout(form)
        layout.addStretch()


class AppearanceSettings(SettingsCategory):
    """Appearance and theme settings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        tm = get_theme_manager()
        c = tm.tokens["color"]

        title = QLabel("Appearance")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c['text']['primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        # Theme selection
        self.theme = QComboBox()
        self.theme.addItems(["Dark (Modern)", "Light (Coming Soon)", "System"])
        self.theme.setCurrentIndex(0)
        self.theme.currentIndexChanged.connect(self.mark_changed)
        form.addRow("Theme:", self.theme)

        # Accent color
        self.accent_color = QComboBox()
        self.accent_color.addItems(["Purple (Default)", "Blue", "Green", "Pink", "Orange"])
        self.accent_color.currentIndexChanged.connect(self.mark_changed)
        form.addRow("Accent color:", self.accent_color)

        # Grid opacity
        grid_row = QHBoxLayout()
        self.grid_opacity = QSlider(Qt.Orientation.Horizontal)
        self.grid_opacity.setRange(0, 100)
        self.grid_opacity.setValue(50)
        self.grid_opacity.valueChanged.connect(self.mark_changed)
        grid_row.addWidget(self.grid_opacity)

        self.grid_opacity_label = QLabel("50%")
        self.grid_opacity_label.setFixedWidth(40)
        self.grid_opacity.valueChanged.connect(lambda v: self.grid_opacity_label.setText(f"{v}%"))
        grid_row.addWidget(self.grid_opacity_label)
        form.addRow("Grid opacity:", grid_row)

        # Show grid
        self.show_grid = QCheckBox("Show grid by default")
        self.show_grid.setChecked(True)
        self.show_grid.stateChanged.connect(self.mark_changed)
        form.addRow(self.show_grid)

        # Animation speed
        self.animation_speed = QComboBox()
        self.animation_speed.addItems(["Fast", "Normal", "Slow", "None"])
        self.animation_speed.setCurrentIndex(1)
        self.animation_speed.currentIndexChanged.connect(self.mark_changed)
        form.addRow("Animation speed:", self.animation_speed)

        # Show tooltips
        self.show_tooltips = QCheckBox("Show rich tooltips")
        self.show_tooltips.setChecked(True)
        self.show_tooltips.stateChanged.connect(self.mark_changed)
        form.addRow(self.show_tooltips)

        layout.addLayout(form)
        layout.addStretch()


class PerformanceSettings(SettingsCategory):
    """Performance and optimization settings."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        tm = get_theme_manager()
        c = tm.tokens["color"]

        title = QLabel("Performance")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c['text']['primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(12)

        # Sprite cache size
        self.cache_size = QSpinBox()
        self.cache_size.setRange(50, 2000)
        self.cache_size.setValue(500)
        self.cache_size.setSuffix(" sprites")
        self.cache_size.setSingleStep(50)
        self.cache_size.valueChanged.connect(self.mark_changed)
        form.addRow("Sprite cache size:", self.cache_size)

        # Max rendered tiles
        self.max_tiles = QSpinBox()
        self.max_tiles.setRange(1000, 50000)
        self.max_tiles.setValue(10000)
        self.max_tiles.setSingleStep(1000)
        self.max_tiles.valueChanged.connect(self.mark_changed)
        form.addRow("Max rendered tiles:", self.max_tiles)

        # Hardware acceleration
        self.hw_accel = QCheckBox("Enable hardware acceleration")
        self.hw_accel.setChecked(True)
        self.hw_accel.stateChanged.connect(self.mark_changed)
        form.addRow(self.hw_accel)

        # VSync
        self.vsync = QCheckBox("Enable VSync")
        self.vsync.setChecked(True)
        self.vsync.stateChanged.connect(self.mark_changed)
        form.addRow(self.vsync)

        # Render FPS limit
        self.fps_limit = QComboBox()
        self.fps_limit.addItems(["Unlimited", "144", "120", "60", "30"])
        self.fps_limit.setCurrentIndex(3)  # 60 FPS
        self.fps_limit.currentIndexChanged.connect(self.mark_changed)
        form.addRow("FPS limit:", self.fps_limit)

        # Memory warning
        self.memory_warning = QSpinBox()
        self.memory_warning.setRange(100, 4000)
        self.memory_warning.setValue(500)
        self.memory_warning.setSuffix(" MB")
        self.memory_warning.valueChanged.connect(self.mark_changed)
        form.addRow("Memory warning at:", self.memory_warning)

        layout.addLayout(form)
        layout.addStretch()


class SettingsDialog(ModernDialog):
    """Main settings dialog with category navigation.

    Signals:
        settings_applied: Emitted when settings are applied
    """

    settings_applied = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, title="Settings")

        self._categories: list[tuple[str, str, SettingsCategory]] = []

        self.setMinimumSize(700, 500)

        self._setup_content()
        self._setup_footer()

    def _setup_content(self) -> None:
        """Initialize UI components."""
        tm = get_theme_manager()
        c = tm.tokens["color"]

        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left sidebar - category list
        sidebar = QWidget()
        sidebar.setFixedWidth(180)
        # Use theme token if possible, or slight variant
        sidebar.setStyleSheet(f"background: {c['surface']['secondary']}; border-right: 1px solid {c['border']['default']};")

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(4)

        # Category list
        self.category_list = QListWidget()
        self.category_list.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px 16px;
                border-radius: 8px;
                color: {c['text']['secondary']};
                margin: 2px 0;
            }}
            QListWidget::item:hover {{
                background: {c['surface']['tertiary']};
                color: {c['text']['primary']};
            }}
            QListWidget::item:selected {{
                background: {c['brand']['primary']};
                color: white;
            }}
        """)
        self.category_list.currentRowChanged.connect(self._on_category_changed)
        sidebar_layout.addWidget(self.category_list)

        sidebar_layout.addStretch()

        layout.addWidget(sidebar)

        # Right side - settings content
        right_panel = QWidget()
        right_panel.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Stacked widget for category content
        self.stack = QStackedWidget()
        right_layout.addWidget(self.stack)

        layout.addWidget(right_panel)

        # Add default categories
        self._add_category("General", "general", GeneralSettings())
        self._add_category("Editor", "editor", EditorSettings())
        self._add_category("Appearance", "appearance", AppearanceSettings())
        self._add_category("Performance", "performance", PerformanceSettings())

        # Select first
        self.category_list.setCurrentRow(0)

        self.set_content_layout(layout)

    def _setup_footer(self) -> None:
        self.add_button("Reset to Defaults", callback=self._on_reset)
        self.add_spacer_to_footer()
        self.add_button("Cancel", callback=self.reject)
        self.add_button("Apply", callback=self._on_apply, role="primary")

    def _add_category(self, display_name: str, category_id: str, widget: SettingsCategory) -> None:
        """Add a settings category."""
        self._categories.append((display_name, category_id, widget))

        item = QListWidgetItem(display_name)
        item.setData(Qt.ItemDataRole.UserRole, category_id)
        self.category_list.addItem(item)

        self.stack.addWidget(widget)

    def _on_category_changed(self, index: int) -> None:
        """Handle category selection change."""
        self.stack.setCurrentIndex(index)

    def _on_apply(self) -> None:
        """Apply settings and close."""
        settings = self._gather_settings()

        # Apply each category
        for _, _, widget in self._categories:
            widget.apply_settings()

        self.settings_applied.emit(settings)
        self.accept()

    def _on_reset(self) -> None:
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Reset all settings to defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            for _, _, widget in self._categories:
                widget.reset_settings()

    def _gather_settings(self) -> dict[str, Any]:
        """Gather all settings into a dict."""
        settings: dict[str, Any] = {}

        for _, category_id, widget in self._categories:
            category_settings = {}

            # Iterate widget children and extract values
            for child in widget.findChildren(QWidget):
                name = child.objectName()
                if not name:
                    continue

                if isinstance(child, QCheckBox):
                    category_settings[name] = child.isChecked()
                elif isinstance(child, QSpinBox):
                    category_settings[name] = child.value()
                elif isinstance(child, QComboBox):
                    category_settings[name] = child.currentText()
                elif isinstance(child, QSlider):
                    category_settings[name] = child.value()

            settings[category_id] = category_settings

        return settings
