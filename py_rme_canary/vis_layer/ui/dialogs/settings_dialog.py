"""Settings/Preferences Dialog.

Modern settings dialog with 5 categories matching C++ RME Redux:
- General settings (welcome, backup, updater, undo queue, workers, copy-pos format)
- Editor behavior (borders, doors, eraser, spawns, merge, duplicate ID warnings)
- Graphics (anti-alias, shader, cursor colors, screenshot, FPS, sprite cache)
- Interface (palette styles, mouse, scroll/zoom speed, double-click)
- Client Version (default version, per-version asset directory pickers)

Refactored to use ModernDialog with responsive layout.
"""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.core.config.user_settings import get_user_settings
from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _color_button(initial: str = "#ffffff") -> QPushButton:
    """Create a color picker button."""
    btn = QPushButton()
    btn.setFixedSize(32, 24)
    btn.setProperty("_color", initial)
    btn.setStyleSheet(f"background: {initial}; border: 1px solid #555; border-radius: 4px;")

    def _pick() -> None:
        from PyQt6.QtGui import QColor

        c = QColorDialog.getColor(QColor(btn.property("_color")), btn, "Choose Color")
        if c.isValid():
            btn.setProperty("_color", c.name())
            btn.setStyleSheet(f"background: {c.name()}; border: 1px solid #555; border-radius: 4px;")

    btn.clicked.connect(_pick)
    return btn


def _dir_picker(placeholder: str = "") -> QWidget:
    """Create a directory picker row (line edit + browse button)."""
    row = QWidget()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(4)
    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    edit.setObjectName("dir_edit")
    lay.addWidget(edit, 1)
    btn = QPushButton("Browse…")
    btn.setFixedWidth(80)

    def _browse() -> None:
        d = QFileDialog.getExistingDirectory(row, "Select Directory", edit.text())
        if d:
            edit.setText(d)

    btn.clicked.connect(_browse)
    lay.addWidget(btn)
    return row


def _section_label(text: str, color_token: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {color_token}; margin-top: 8px;")
    return lbl


def _dir_picker_text(widget: QWidget) -> str:
    edit = widget.findChild(QLineEdit, "dir_edit")
    if edit is None:
        return ""
    return str(edit.text() or "").strip()


def _set_dir_picker_text(widget: QWidget, value: str) -> None:
    edit = widget.findChild(QLineEdit, "dir_edit")
    if edit is None:
        return
    edit.setText(str(value or ""))


# ---------------------------------------------------------------------------
# Category Base
# ---------------------------------------------------------------------------

class SettingsCategory(QFrame):
    """Base class for settings category widgets."""

    settings_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._changed = False
        self.setFrameShape(QFrame.Shape.NoFrame)

    def has_changes(self) -> bool:
        return self._changed

    def mark_changed(self) -> None:
        self._changed = True
        self.settings_changed.emit()

    def apply_settings(self) -> None:
        self._changed = False

    def reset_settings(self) -> None:
        pass

    def collect_settings(self) -> dict[str, object]:
        return {}


def _scrollable(inner: QWidget) -> QScrollArea:
    """Wrap *inner* in a scroll area for responsiveness."""
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setFrameShape(QFrame.Shape.NoFrame)
    sa.setWidget(inner)
    sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    return sa


# ---------------------------------------------------------------------------
# 1) General Settings  (matches C++ "General" tab)
# ---------------------------------------------------------------------------

class GeneralSettings(SettingsCategory):
    """General application settings – mirrors C++ Preferences > General."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        tm = get_theme_manager()
        c = tm.tokens["color"]

        title = QLabel("General Settings")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c['text']['primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # --- Startup section ---
        layout.addWidget(_section_label("Startup", c["text"]["secondary"]))

        self.show_welcome = QCheckBox("Show welcome dialog on startup")
        self.show_welcome.setObjectName("show_welcome")
        self.show_welcome.setChecked(True)
        self.show_welcome.stateChanged.connect(self.mark_changed)
        form.addRow(self.show_welcome)

        self.check_updates = QCheckBox("Check for updates on startup")
        self.check_updates.setObjectName("check_updates")
        self.check_updates.setChecked(True)
        self.check_updates.stateChanged.connect(self.mark_changed)
        form.addRow(self.check_updates)

        self.only_one_instance = QCheckBox("Open all maps in the same instance")
        self.only_one_instance.setObjectName("only_one_instance")
        self.only_one_instance.setChecked(False)
        self.only_one_instance.stateChanged.connect(self.mark_changed)
        form.addRow(self.only_one_instance)

        # --- Saving section ---
        layout.addWidget(_section_label("Saving", c["text"]["secondary"]))

        self.create_backup = QCheckBox("Always make backup on save")
        self.create_backup.setObjectName("always_backup")
        self.create_backup.setChecked(True)
        self.create_backup.stateChanged.connect(self.mark_changed)
        form.addRow(self.create_backup)

        auto_save_row = QHBoxLayout()
        self.auto_save = QCheckBox("Auto-save every")
        self.auto_save.setObjectName("auto_save")
        self.auto_save.setChecked(True)
        self.auto_save.stateChanged.connect(self.mark_changed)
        auto_save_row.addWidget(self.auto_save)
        self.auto_save_interval = QSpinBox()
        self.auto_save_interval.setObjectName("auto_save_interval")
        self.auto_save_interval.setRange(1, 60)
        self.auto_save_interval.setValue(5)
        self.auto_save_interval.setSuffix(" min")
        self.auto_save_interval.valueChanged.connect(self.mark_changed)
        auto_save_row.addWidget(self.auto_save_interval)
        auto_save_row.addStretch()
        form.addRow(auto_save_row)

        # --- Undo section ---
        layout.addWidget(_section_label("Undo / Redo", c["text"]["secondary"]))

        self.undo_queue_size = QSpinBox()
        self.undo_queue_size.setObjectName("undo_queue_size")
        self.undo_queue_size.setRange(0, 268_000_000)
        self.undo_queue_size.setValue(1000)
        self.undo_queue_size.setToolTip("0 = unlimited. Maximum number of stored undo actions.")
        self.undo_queue_size.valueChanged.connect(self.mark_changed)
        form.addRow("Undo queue size:", self.undo_queue_size)

        self.undo_memory_mb = QSpinBox()
        self.undo_memory_mb.setObjectName("undo_memory_mb")
        self.undo_memory_mb.setRange(0, 4096)
        self.undo_memory_mb.setValue(256)
        self.undo_memory_mb.setSuffix(" MB")
        self.undo_memory_mb.setToolTip("0 = unlimited. Max memory used by undo buffer.")
        self.undo_memory_mb.valueChanged.connect(self.mark_changed)
        form.addRow("Undo memory limit:", self.undo_memory_mb)

        # --- Performance section ---
        layout.addWidget(_section_label("Threading", c["text"]["secondary"]))

        self.worker_threads = QSpinBox()
        self.worker_threads.setObjectName("worker_threads")
        self.worker_threads.setRange(1, 64)
        self.worker_threads.setValue(max(1, (os.cpu_count() or 4) // 2))
        self.worker_threads.valueChanged.connect(self.mark_changed)
        form.addRow("Worker threads:", self.worker_threads)

        # --- Copy format ---
        layout.addWidget(_section_label("Clipboard", c["text"]["secondary"]))

        self.copy_pos_format = QComboBox()
        self.copy_pos_format.setObjectName("copy_pos_format")
        self.copy_pos_format.addItems([
            "{x=0,y=0,z=0}",
            '{"x":0,"y":0,"z":0}',
            "x, y, z",
            "(x, y, z)",
            "Position(x, y, z)",
        ])
        self.copy_pos_format.currentIndexChanged.connect(self.mark_changed)
        form.addRow("Copy position format:", self.copy_pos_format)

        # Recent files
        self.recent_count = QSpinBox()
        self.recent_count.setObjectName("recent_files_count")
        self.recent_count.setRange(0, 20)
        self.recent_count.setValue(10)
        self.recent_count.valueChanged.connect(self.mark_changed)
        form.addRow("Recent files to show:", self.recent_count)

        # Auto-load appearances
        self.auto_load_appearances = QCheckBox("Auto-load appearances.dat when available")
        self.auto_load_appearances.setObjectName("auto_load_appearances")
        self.auto_load_appearances.setChecked(True)
        self.auto_load_appearances.stateChanged.connect(self.mark_changed)
        form.addRow(self.auto_load_appearances)

        # Tileset editing
        self.enable_tileset_editing = QCheckBox("Enable tileset editing")
        self.enable_tileset_editing.setObjectName("enable_tileset_editing")
        self.enable_tileset_editing.setChecked(False)
        self.enable_tileset_editing.stateChanged.connect(self.mark_changed)
        form.addRow(self.enable_tileset_editing)

        layout.addLayout(form)
        layout.addStretch()
        self._load_current_settings()

    def _load_current_settings(self) -> None:
        settings = get_user_settings()
        self.show_welcome.setChecked(bool(settings.get_show_welcome_dialog()))
        self.check_updates.setChecked(bool(settings.get_check_updates_on_startup()))
        self.only_one_instance.setChecked(bool(settings.get_only_one_instance()))
        self.create_backup.setChecked(bool(settings.get_always_make_backup()))
        self.undo_queue_size.setValue(int(settings.get_undo_queue_size()))
        self.undo_memory_mb.setValue(int(settings.get_undo_max_memory_mb()))
        self.worker_threads.setValue(int(settings.get_worker_threads()))
        self.copy_pos_format.setCurrentIndex(int(settings.get_copy_position_format()))
        self.auto_load_appearances.setChecked(bool(settings.get_auto_load_appearances()))
        self.enable_tileset_editing.setChecked(bool(settings.get_enable_tileset_editing()))
        self._changed = False

    def collect_settings(self) -> dict[str, object]:
        return {
            "show_welcome_dialog": bool(self.show_welcome.isChecked()),
            "check_updates_on_startup": bool(self.check_updates.isChecked()),
            "only_one_instance": bool(self.only_one_instance.isChecked()),
            "always_make_backup": bool(self.create_backup.isChecked()),
            "auto_save": bool(self.auto_save.isChecked()),
            "auto_save_interval": int(self.auto_save_interval.value()),
            "undo_queue_size": int(self.undo_queue_size.value()),
            "undo_max_memory_mb": int(self.undo_memory_mb.value()),
            "worker_threads": int(self.worker_threads.value()),
            "copy_position_format": int(self.copy_pos_format.currentIndex()),
            "recent_files_count": int(self.recent_count.value()),
            "auto_load_appearances": bool(self.auto_load_appearances.isChecked()),
            "enable_tileset_editing": bool(self.enable_tileset_editing.isChecked()),
        }


# ---------------------------------------------------------------------------
# 2) Editor Settings  (matches C++ "Editor" tab)
# ---------------------------------------------------------------------------

class EditorSettings(SettingsCategory):
    """Editor behavior settings – mirrors C++ Preferences > Editor."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        tm = get_theme_manager()
        c = tm.tokens["color"]

        title = QLabel("Editor Settings")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c['text']['primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # --- Brush behaviour ---
        layout.addWidget(_section_label("Brush Behavior", c["text"]["secondary"]))

        self.default_brush_size = QSpinBox()
        self.default_brush_size.setObjectName("default_brush_size")
        self.default_brush_size.setRange(1, 11)
        self.default_brush_size.setValue(1)
        self.default_brush_size.valueChanged.connect(self.mark_changed)
        form.addRow("Default brush size:", self.default_brush_size)

        self.automagic_default = QCheckBox("Enable automagic by default")
        self.automagic_default.setObjectName("automagic_default")
        self.automagic_default.setChecked(True)
        self.automagic_default.stateChanged.connect(self.mark_changed)
        form.addRow(self.automagic_default)

        self.doodad_eraser_same = QCheckBox("Doodad brush only erases same type")
        self.doodad_eraser_same.setObjectName("doodad_erase_same")
        self.doodad_eraser_same.setChecked(True)
        self.doodad_eraser_same.stateChanged.connect(self.mark_changed)
        form.addRow(self.doodad_eraser_same)

        self.eraser_leave_unique = QCheckBox("Eraser leaves unique items")
        self.eraser_leave_unique.setObjectName("eraser_leave_unique")
        self.eraser_leave_unique.setChecked(True)
        self.eraser_leave_unique.stateChanged.connect(self.mark_changed)
        form.addRow(self.eraser_leave_unique)

        # --- Houses & Doors ---
        layout.addWidget(_section_label("Houses & Doors", c["text"]["secondary"]))

        self.house_brush_remove = QCheckBox("House brush removes items")
        self.house_brush_remove.setObjectName("house_brush_remove")
        self.house_brush_remove.setChecked(True)
        self.house_brush_remove.stateChanged.connect(self.mark_changed)
        form.addRow(self.house_brush_remove)

        self.auto_assign_doorid = QCheckBox("Auto-assign door IDs")
        self.auto_assign_doorid.setObjectName("auto_assign_doorid")
        self.auto_assign_doorid.setChecked(True)
        self.auto_assign_doorid.stateChanged.connect(self.mark_changed)
        form.addRow(self.auto_assign_doorid)

        # --- Spawns ---
        layout.addWidget(_section_label("Spawns & Creatures", c["text"]["secondary"]))

        self.auto_create_spawn = QCheckBox("Auto-create spawn when placing creature")
        self.auto_create_spawn.setObjectName("auto_create_spawn")
        self.auto_create_spawn.setChecked(True)
        self.auto_create_spawn.stateChanged.connect(self.mark_changed)
        form.addRow(self.auto_create_spawn)

        # --- Warnings ---
        layout.addWidget(_section_label("Warnings", c["text"]["secondary"]))

        self.warn_duplicate_ids = QCheckBox("Warn for duplicate IDs on map")
        self.warn_duplicate_ids.setObjectName("warn_duplicate_ids")
        self.warn_duplicate_ids.setChecked(True)
        self.warn_duplicate_ids.stateChanged.connect(self.mark_changed)
        form.addRow(self.warn_duplicate_ids)

        self.prevent_toporder = QCheckBox("Prevent toporder conflicts")
        self.prevent_toporder.setObjectName("prevent_toporder")
        self.prevent_toporder.setChecked(False)
        self.prevent_toporder.stateChanged.connect(self.mark_changed)
        form.addRow(self.prevent_toporder)

        # --- Paste/Move behaviour ---
        layout.addWidget(_section_label("Paste & Move", c["text"]["secondary"]))

        self.merge_paste = QCheckBox("Use merge paste")
        self.merge_paste.setObjectName("merge_paste")
        self.merge_paste.setChecked(False)
        self.merge_paste.stateChanged.connect(self.mark_changed)
        form.addRow(self.merge_paste)

        self.merge_move = QCheckBox("Use merge move")
        self.merge_move.setObjectName("merge_move")
        self.merge_move.setChecked(False)
        self.merge_move.stateChanged.connect(self.mark_changed)
        form.addRow(self.merge_move)

        self.borderize_paste = QCheckBox("Auto-borderize after paste")
        self.borderize_paste.setObjectName("borderize_paste")
        self.borderize_paste.setChecked(True)
        self.borderize_paste.stateChanged.connect(self.mark_changed)
        form.addRow(self.borderize_paste)

        self.sprite_match_paste = QCheckBox("Sprite match on paste (cross-version)")
        self.sprite_match_paste.setObjectName("sprite_match_on_paste")
        self.sprite_match_paste.setToolTip(
            "Enable sprite hash matching for cross-version copy/paste.\n"
            "Allows copying between RME instances with different client versions."
        )
        self.sprite_match_paste.setChecked(True)
        self.sprite_match_paste.stateChanged.connect(self.mark_changed)
        form.addRow(self.sprite_match_paste)

        self.default_floor = QSpinBox()
        self.default_floor.setObjectName("default_floor")
        self.default_floor.setRange(0, 15)
        self.default_floor.setValue(7)
        self.default_floor.valueChanged.connect(self.mark_changed)
        form.addRow("Default floor (Z):", self.default_floor)

        self.group_same_actions = QCheckBox("Group same-type actions in undo")
        self.group_same_actions.setObjectName("group_same_actions")
        self.group_same_actions.setChecked(True)
        self.group_same_actions.stateChanged.connect(self.mark_changed)
        form.addRow(self.group_same_actions)

        layout.addLayout(form)
        layout.addStretch()
        self._load_current_settings()

    def _load_current_settings(self) -> None:
        settings = get_user_settings()
        self.default_brush_size.setValue(int(settings.get_default_brush_size()))
        self.automagic_default.setChecked(bool(settings.get_automagic_default()))
        self.eraser_leave_unique.setChecked(bool(settings.get_eraser_leave_unique()))
        self.merge_paste.setChecked(bool(settings.get_merge_paste_default()))
        self.merge_move.setChecked(bool(settings.get_merge_move_default()))
        self.borderize_paste.setChecked(bool(settings.get_borderize_paste_default()))
        self.sprite_match_paste.setChecked(bool(settings.get_sprite_match_on_paste()))
        self._changed = False

    def collect_settings(self) -> dict[str, object]:
        return {
            "default_brush_size": int(self.default_brush_size.value()),
            "automagic_default": bool(self.automagic_default.isChecked()),
            "doodad_erase_same": bool(self.doodad_eraser_same.isChecked()),
            "eraser_leave_unique": bool(self.eraser_leave_unique.isChecked()),
            "house_brush_remove": bool(self.house_brush_remove.isChecked()),
            "auto_assign_doorid": bool(self.auto_assign_doorid.isChecked()),
            "auto_create_spawn": bool(self.auto_create_spawn.isChecked()),
            "warn_duplicate_ids": bool(self.warn_duplicate_ids.isChecked()),
            "prevent_toporder": bool(self.prevent_toporder.isChecked()),
            "merge_paste": bool(self.merge_paste.isChecked()),
            "merge_move": bool(self.merge_move.isChecked()),
            "borderize_paste": bool(self.borderize_paste.isChecked()),
            "sprite_match_on_paste": bool(self.sprite_match_paste.isChecked()),
            "default_floor": int(self.default_floor.value()),
            "group_same_actions": bool(self.group_same_actions.isChecked()),
        }


# ---------------------------------------------------------------------------
# 3) Graphics Settings  (matches C++ "Graphics" tab)
# ---------------------------------------------------------------------------

class GraphicsSettings(SettingsCategory):
    """Graphics settings – mirrors C++ Preferences > Graphics."""

    THEME_OPTIONS: list[tuple[str, str]] = [
        ("Noct Green Glass", "glass_morphism"),
        ("Noct 8-bit Glass", "glass_8bit"),
        ("Noct Liquid Glass", "liquid_glass"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        tm = get_theme_manager()
        c = tm.tokens["color"]

        title = QLabel("Graphics")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c['text']['primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # --- Rendering ---
        layout.addWidget(_section_label("Rendering", c["text"]["secondary"]))

        self.anti_aliasing = QCheckBox("Enable anti-aliasing (MSAA 4x)")
        self.anti_aliasing.setObjectName("anti_aliasing")
        self.anti_aliasing.setChecked(True)
        self.anti_aliasing.stateChanged.connect(self.mark_changed)
        form.addRow(self.anti_aliasing)

        self.hw_accel = QCheckBox("Enable hardware acceleration (OpenGL)")
        self.hw_accel.setObjectName("hw_acceleration")
        self.hw_accel.setChecked(True)
        self.hw_accel.stateChanged.connect(self.mark_changed)
        form.addRow(self.hw_accel)

        self.vsync = QCheckBox("Enable VSync")
        self.vsync.setObjectName("vsync")
        self.vsync.setChecked(True)
        self.vsync.stateChanged.connect(self.mark_changed)
        form.addRow(self.vsync)

        self.hide_items_zoomed = QCheckBox("Hide items when zoomed out")
        self.hide_items_zoomed.setObjectName("hide_items_zoomed")
        self.hide_items_zoomed.setChecked(True)
        self.hide_items_zoomed.stateChanged.connect(self.mark_changed)
        form.addRow(self.hide_items_zoomed)

        self.use_memcached = QCheckBox("Use memcached sprites")
        self.use_memcached.setObjectName("use_memcached")
        self.use_memcached.setChecked(True)
        self.use_memcached.stateChanged.connect(self.mark_changed)
        form.addRow(self.use_memcached)

        # FPS
        fps_row = QHBoxLayout()
        self.fps_limit = QSpinBox()
        self.fps_limit.setObjectName("fps_limit")
        self.fps_limit.setRange(0, 300)
        self.fps_limit.setValue(60)
        self.fps_limit.setToolTip("0 = unlimited")
        self.fps_limit.valueChanged.connect(self.mark_changed)
        fps_row.addWidget(self.fps_limit)
        fps_row.addWidget(QLabel("FPS"))
        fps_row.addStretch()
        self.show_fps = QCheckBox("Show FPS counter")
        self.show_fps.setObjectName("show_fps")
        self.show_fps.setChecked(False)
        self.show_fps.stateChanged.connect(self.mark_changed)
        fps_row.addWidget(self.show_fps)
        form.addRow("FPS limit:", fps_row)

        # --- Sprite cache ---
        layout.addWidget(_section_label("Sprite Cache", c["text"]["secondary"]))

        self.cache_size = QSpinBox()
        self.cache_size.setObjectName("sprite_cache_size")
        self.cache_size.setRange(50, 10000)
        self.cache_size.setValue(500)
        self.cache_size.setSuffix(" sprites")
        self.cache_size.setSingleStep(50)
        self.cache_size.valueChanged.connect(self.mark_changed)
        form.addRow("Sprite cache size:", self.cache_size)

        self.max_tiles = QSpinBox()
        self.max_tiles.setObjectName("max_rendered_tiles")
        self.max_tiles.setRange(1000, 50000)
        self.max_tiles.setValue(10000)
        self.max_tiles.setSingleStep(1000)
        self.max_tiles.valueChanged.connect(self.mark_changed)
        form.addRow("Max rendered tiles:", self.max_tiles)

        self.memory_warning = QSpinBox()
        self.memory_warning.setObjectName("memory_warning_mb")
        self.memory_warning.setRange(100, 4000)
        self.memory_warning.setValue(500)
        self.memory_warning.setSuffix(" MB")
        self.memory_warning.valueChanged.connect(self.mark_changed)
        form.addRow("Memory warning at:", self.memory_warning)

        # --- Colors & Cursor ---
        layout.addWidget(_section_label("Cursor & Colors", c["text"]["secondary"]))

        cursor_row = QHBoxLayout()
        cursor_row.addWidget(QLabel("Primary cursor:"))
        self.cursor_color = _color_button("#ffffff")
        self.cursor_color.setObjectName("cursor_color_primary")
        cursor_row.addWidget(self.cursor_color)
        cursor_row.addWidget(QLabel("Secondary:"))
        self.cursor_color_2 = _color_button("#ff8800")
        self.cursor_color_2.setObjectName("cursor_color_secondary")
        cursor_row.addWidget(self.cursor_color_2)
        cursor_row.addStretch()
        form.addRow(cursor_row)

        self.icon_bg = QComboBox()
        self.icon_bg.setObjectName("icon_background")
        self.icon_bg.addItems(["Black", "Gray", "White"])
        self.icon_bg.currentIndexChanged.connect(self.mark_changed)
        form.addRow("Icon background:", self.icon_bg)

        # --- Screenshots ---
        layout.addWidget(_section_label("Screenshots", c["text"]["secondary"]))

        self.screenshot_dir_widget = _dir_picker("Default: ~/Pictures")
        self.screenshot_dir_widget.setObjectName("screenshot_dir")
        form.addRow("Screenshot directory:", self.screenshot_dir_widget)

        self.screenshot_fmt = QComboBox()
        self.screenshot_fmt.setObjectName("screenshot_format")
        self.screenshot_fmt.addItems(["PNG", "JPG", "BMP"])
        self.screenshot_fmt.currentIndexChanged.connect(self.mark_changed)
        form.addRow("Screenshot format:", self.screenshot_fmt)

        # --- Theme ---
        layout.addWidget(_section_label("Theme", c["text"]["secondary"]))

        self.theme = QComboBox()
        self.theme.setObjectName("theme")
        for label, _theme_name in self.THEME_OPTIONS:
            self.theme.addItem(label)

        self.theme.currentIndexChanged.connect(self._on_theme_changed)
        form.addRow("Theme:", self.theme)

        self.accent_color = QComboBox()
        self.accent_color.setObjectName("accent_color")
        self.accent_color.addItems(["Purple (Default)", "Blue", "Green", "Pink", "Orange"])
        self.accent_color.currentIndexChanged.connect(self.mark_changed)
        form.addRow("Accent color:", self.accent_color)

        grid_row = QHBoxLayout()
        self.grid_opacity = QSlider(Qt.Orientation.Horizontal)

        self.grid_opacity.setObjectName("grid_opacity")
        self.grid_opacity.setRange(0, 100)
        self.grid_opacity.setValue(50)
        self.grid_opacity.valueChanged.connect(self.mark_changed)
        grid_row.addWidget(self.grid_opacity)
        self.grid_opacity_label = QLabel("50%")
        self.grid_opacity_label.setFixedWidth(40)
        self.grid_opacity.valueChanged.connect(lambda v: self.grid_opacity_label.setText(f"{v}%"))
        grid_row.addWidget(self.grid_opacity_label)
        form.addRow("Grid opacity:", grid_row)

        self.show_grid = QCheckBox("Show grid by default")
        self.show_grid.setObjectName("show_grid_default")
        self.show_grid.setChecked(True)
        self.show_grid.stateChanged.connect(self.mark_changed)
        form.addRow(self.show_grid)

        self.animation_speed = QComboBox()
        self.animation_speed.setObjectName("animation_speed")
        self.animation_speed.addItems(["Fast", "Normal", "Slow", "None"])
        self.animation_speed.setCurrentIndex(1)
        self.animation_speed.currentIndexChanged.connect(self.mark_changed)
        form.addRow("Animation speed:", self.animation_speed)

        self.show_tooltips = QCheckBox("Show rich tooltips")
        self.show_tooltips.setObjectName("show_tooltips")
        self.show_tooltips.setChecked(True)
        self.show_tooltips.stateChanged.connect(self.mark_changed)
        form.addRow(self.show_tooltips)

        layout.addLayout(form)
        layout.addStretch()
        self._load_current_settings()

    def _load_current_settings(self) -> None:
        settings = get_user_settings()
        theme_name = str(settings.get_theme_name() or get_theme_manager().current_theme)
        theme_values = [theme for _, theme in self.THEME_OPTIONS]
        if theme_name in theme_values:
            self.theme.setCurrentIndex(theme_values.index(theme_name))
        else:
            self.theme.setCurrentIndex(0)
        self.show_grid.setChecked(bool(settings.get_show_grid_default()))
        self.show_tooltips.setChecked(bool(settings.get_show_tooltips_default()))
        self._changed = False

    def _on_theme_changed(self, index: int) -> None:
        """Apply theme immediately for preview."""
        tm = get_theme_manager()
        themes = [theme for _, theme in self.THEME_OPTIONS]
        if 0 <= index < len(themes):
            tm.set_theme(themes[index])
        self.mark_changed()

    def collect_settings(self) -> dict[str, object]:
        themes = [theme for _, theme in self.THEME_OPTIONS]
        idx = int(self.theme.currentIndex())
        selected_theme = themes[idx] if 0 <= idx < len(themes) else themes[0]
        return {
            "theme_name": str(selected_theme),
            "show_grid_default": bool(self.show_grid.isChecked()),
            "show_tooltips_default": bool(self.show_tooltips.isChecked()),
            "grid_opacity": int(self.grid_opacity.value()),
            "animation_speed": str(self.animation_speed.currentText()),
        }


# ---------------------------------------------------------------------------
# 4) Interface Settings  (matches C++ "Interface" tab)
# ---------------------------------------------------------------------------

class InterfaceSettings(SettingsCategory):
    """Interface settings – mirrors C++ Preferences > Interface."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._palette_style_combos: dict[str, QComboBox] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        tm = get_theme_manager()
        c = tm.tokens["color"]

        title = QLabel("Interface")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c['text']['primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # --- Palette Styles ---
        layout.addWidget(_section_label("Palette Display Style", c["text"]["secondary"]))

        _style_items = ["Large Icons", "Small Icons", "Listbox with Icons"]
        for name, obj_name in [
            ("Terrain palette:", "palette_terrain_style"),
            ("Doodad palette:", "palette_doodad_style"),
            ("Item palette:", "palette_item_style"),
            ("RAW palette:", "palette_raw_style"),
            ("Collection palette:", "palette_collection_style"),
        ]:
            combo = QComboBox()
            combo.setObjectName(obj_name)
            combo.addItems(_style_items)
            combo.currentIndexChanged.connect(self.mark_changed)
            form.addRow(name, combo)
            self._palette_style_combos[obj_name] = combo

        # --- Large Icons toggles ---
        layout.addWidget(_section_label("Large Icons", c["text"]["secondary"]))

        for label_text, obj_name in [
            ("Terrain", "large_terrain"),
            ("Collection", "large_collection"),
            ("Doodad", "large_doodad"),
            ("Item", "large_item"),
            ("House", "large_house"),
            ("RAW", "large_raw"),
            ("Container", "large_container"),
            ("Pick-item dialog", "large_pick_item"),
        ]:
            cb = QCheckBox(f"Use large icons for {label_text}")
            cb.setObjectName(obj_name)
            cb.setChecked(True)
            cb.stateChanged.connect(self.mark_changed)
            form.addRow(cb)

        # --- Mouse ---
        layout.addWidget(_section_label("Mouse & Input", c["text"]["secondary"]))

        self.switch_buttons = QCheckBox("Switch mouse buttons (draw=right, pan=left)")
        self.switch_buttons.setObjectName("switch_mouse_buttons")
        self.switch_buttons.setChecked(False)
        self.switch_buttons.stateChanged.connect(self.mark_changed)
        form.addRow(self.switch_buttons)

        self.double_click_props = QCheckBox("Double-click opens properties")
        self.double_click_props.setObjectName("double_click_props")
        self.double_click_props.setChecked(True)
        self.double_click_props.stateChanged.connect(self.mark_changed)
        form.addRow(self.double_click_props)

        self.inversed_scroll = QCheckBox("Use inversed scroll direction")
        self.inversed_scroll.setObjectName("inversed_scroll")
        self.inversed_scroll.setChecked(False)
        self.inversed_scroll.stateChanged.connect(self.mark_changed)
        form.addRow(self.inversed_scroll)

        # Scroll speed
        scroll_row = QHBoxLayout()
        self.scroll_speed = QSlider(Qt.Orientation.Horizontal)
        self.scroll_speed.setObjectName("scroll_speed")
        self.scroll_speed.setRange(1, 100)
        self.scroll_speed.setValue(50)
        self.scroll_speed.valueChanged.connect(self.mark_changed)
        scroll_row.addWidget(self.scroll_speed)
        self.scroll_speed_lbl = QLabel("50")
        self.scroll_speed_lbl.setFixedWidth(30)
        self.scroll_speed.valueChanged.connect(lambda v: self.scroll_speed_lbl.setText(str(v)))
        scroll_row.addWidget(self.scroll_speed_lbl)
        form.addRow("Scroll speed:", scroll_row)

        # Zoom speed
        zoom_row = QHBoxLayout()
        self.zoom_speed = QSlider(Qt.Orientation.Horizontal)
        self.zoom_speed.setObjectName("zoom_speed")
        self.zoom_speed.setRange(1, 100)
        self.zoom_speed.setValue(50)
        self.zoom_speed.valueChanged.connect(self.mark_changed)
        zoom_row.addWidget(self.zoom_speed)
        self.zoom_speed_lbl = QLabel("50")
        self.zoom_speed_lbl.setFixedWidth(30)
        self.zoom_speed.valueChanged.connect(lambda v: self.zoom_speed_lbl.setText(str(v)))
        zoom_row.addWidget(self.zoom_speed_lbl)
        form.addRow("Zoom speed:", zoom_row)

        layout.addLayout(form)
        layout.addStretch()
        self._load_current_settings()

    def _load_current_settings(self) -> None:
        settings = get_user_settings()
        for key, combo in self._palette_style_combos.items():
            palette_name = key.replace("palette_", "").replace("_style", "")
            combo.setCurrentIndex(int(settings.get_palette_style(palette_name, default=0)))
        self.switch_buttons.setChecked(bool(settings.get_switch_mouse_buttons()))
        self.double_click_props.setChecked(bool(settings.get_double_click_properties()))
        self.inversed_scroll.setChecked(bool(settings.get_inversed_scroll()))
        self.scroll_speed.setValue(int(settings.get_scroll_speed()))
        self.zoom_speed.setValue(int(settings.get_zoom_speed()))
        self._changed = False

    def collect_settings(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "switch_mouse_buttons": bool(self.switch_buttons.isChecked()),
            "double_click_properties": bool(self.double_click_props.isChecked()),
            "inversed_scroll": bool(self.inversed_scroll.isChecked()),
            "scroll_speed": int(self.scroll_speed.value()),
            "zoom_speed": int(self.zoom_speed.value()),
        }
        for key, combo in self._palette_style_combos.items():
            payload[key] = int(combo.currentIndex())
        return payload


# ---------------------------------------------------------------------------
# 5) Client Version Settings  (matches C++ "Client Version" tab)
# ---------------------------------------------------------------------------

class ClientVersionSettings(SettingsCategory):
    """Client version settings – mirrors C++ Preferences > Client Version."""

    # Well-known client versions (like C++ enumerates)
    VERSIONS: list[tuple[int, str]] = [
        (740, "7.40"),
        (760, "7.60"),
        (800, "8.00"),
        (810, "8.10"),
        (820, "8.20"),
        (840, "8.40"),
        (850, "8.50"),
        (854, "8.54"),
        (860, "8.60"),
        (870, "8.70"),
        (910, "9.10"),
        (920, "9.20"),
        (946, "9.46"),
        (954, "9.54"),
        (960, "9.60"),
        (970, "9.70"),
        (986, "9.86"),
        (1010, "10.10"),
        (1020, "10.20"),
        (1021, "10.21"),
        (1030, "10.30"),
        (1031, "10.31"),
        (1035, "10.35"),
        (1041, "10.41"),
        (1077, "10.77"),
        (1098, "10.98"),
        (1271, "12.71"),
        (1281, "12.81"),
        (1285, "12.85"),
        (1286, "12.86"),
        (1287, "12.87"),
        (1290, "12.90"),
        (1310, "13.10"),
        (1320, "13.20"),
        (1330, "13.30"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._version_dir_widgets: dict[int, QWidget] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        tm = get_theme_manager()
        c = tm.tokens["color"]

        title = QLabel("Client Version")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c['text']['primary']};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # Default version
        self.default_version = QComboBox()
        self.default_version.setObjectName("default_client_version")
        self.default_version.addItem("Auto-detect", 0)
        for vid, vlabel in self.VERSIONS:
            self.default_version.addItem(f"Client {vlabel} ({vid})", vid)
        self.default_version.currentIndexChanged.connect(self.mark_changed)
        form.addRow("Default client version:", self.default_version)

        self.check_signatures = QCheckBox("Check file signatures when loading data")
        self.check_signatures.setObjectName("check_signatures")
        self.check_signatures.setChecked(False)
        self.check_signatures.stateChanged.connect(self.mark_changed)
        form.addRow(self.check_signatures)

        layout.addLayout(form)

        # Per-version data directories
        layout.addWidget(_section_label("Data Directories (per version)", c["text"]["secondary"]))

        version_scroll = QScrollArea()
        version_scroll.setWidgetResizable(True)
        version_scroll.setFrameShape(QFrame.Shape.NoFrame)
        version_scroll.setMinimumHeight(200)
        version_inner = QWidget()
        version_form = QFormLayout(version_inner)
        version_form.setSpacing(6)

        for vid, vlabel in self.VERSIONS:
            picker = _dir_picker(f"Path to client {vlabel} data (DAT/SPR)…")
            picker.setObjectName(f"version_dir_{vid}")
            self._version_dir_widgets[vid] = picker
            version_form.addRow(f"Client {vlabel}:", picker)

        version_scroll.setWidget(version_inner)
        layout.addWidget(version_scroll, 1)

        layout.addStretch()
        self._load_current_settings()

    def _load_current_settings(self) -> None:
        settings = get_user_settings()
        default_version = int(settings.get_default_client_version() or 0)
        idx = self.default_version.findData(default_version)
        self.default_version.setCurrentIndex(idx if idx >= 0 else 0)
        fallback_assets = str(settings.get_client_assets_folder() or "").strip()
        if fallback_assets:
            selected_version = int(self.default_version.currentData() or 0)
            picker = self._version_dir_widgets.get(selected_version)
            if picker is not None:
                _set_dir_picker_text(picker, fallback_assets)
        self._changed = False

    def collect_settings(self) -> dict[str, object]:
        default_version = int(self.default_version.currentData() or 0)
        version_dirs: dict[str, str] = {}
        for vid, picker in self._version_dir_widgets.items():
            text = _dir_picker_text(picker)
            if text:
                version_dirs[str(int(vid))] = text

        default_assets_dir = ""
        if default_version > 0:
            picker = self._version_dir_widgets.get(default_version)
            if picker is not None:
                default_assets_dir = _dir_picker_text(picker)
        if not default_assets_dir:
            default_assets_dir = next(iter(version_dirs.values()), "")

        return {
            "default_client_version": int(default_version),
            "check_signatures": bool(self.check_signatures.isChecked()),
            "version_dirs": version_dirs,
            "client_assets_folder": str(default_assets_dir),
        }


# ---------------------------------------------------------------------------
# Main SettingsDialog (5 categories, responsive)
# ---------------------------------------------------------------------------

class SettingsDialog(ModernDialog):
    """
    Modern Settings Dialog with Antigravity Design.

    Features:
    - Vertical sidebar navigation with icons
    - Glassmorphism panels
    - Smooth transitions (via QStackedWidget)
    """

    settings_applied = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, title="Preferences")
        self.resize(1000, 700)
        self._categories: list[SettingsCategory] = []
        self._setup_content()
        self._apply_antigravity_style()

    def _setup_content(self) -> None:
        """Setup the split-view layout."""
        # Main layout is a horizontal split
        self.body_layout = QHBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(24)

        # 1. Sidebar (Navigation)
        self._nav_list = QListWidget()
        self._nav_list.setObjectName("SettingsNav")
        self._nav_list.setFixedWidth(240)
        self._nav_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._nav_list.currentRowChanged.connect(self._on_category_changed)

        self.body_layout.addWidget(self._nav_list)

        # 2. Content Area (Stacked)
        self._stack = QStackedWidget()
        self._stack.setObjectName("SettingsContent")
        self.body_layout.addWidget(self._stack)

        # Add categories
        # Note: In a real app we'd load SVG icons. Here we use text alignment.
        self._add_category("General", "browser.svg", GeneralSettings(self))
        self._add_category("Editor", "edit.svg", EditorSettings(self))
        self._add_category("Graphics", "monitor.svg", GraphicsSettings(self))
        self._add_category("Interface", "layout.svg", InterfaceSettings(self))
        self._add_category("Client Version", "server.svg", ClientVersionSettings(self))

        # Set main layout to ModernDialog content (wrapping it in a widget)
        container = QWidget()
        container.setLayout(self.body_layout)

        wrapper_layout = QVBoxLayout()
        wrapper_layout.setContentsMargins(24, 24, 24, 24)
        wrapper_layout.addWidget(container)
        self.set_content_layout(wrapper_layout)

        # Select first item
        self._nav_list.setCurrentRow(0)

        # Footer actions
        self.add_spacer_to_footer()
        self.add_button("Reset to Defaults", callback=self._reset_all, role="secondary")
        self.add_button("Save Changes", callback=self.accept, role="primary")

    def _add_category(self, name: str, icon_name: str, widget: SettingsCategory) -> None:
        """Add a settings category."""
        # Create list item
        item = QListWidgetItem(name)
        item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self._nav_list.addItem(item)

        self._categories.append(widget)

        # Wrap in scroll area for safety
        scroll = _scrollable(widget)
        self._stack.addWidget(scroll)

        # Connect change signal
        widget.settings_changed.connect(self._on_settings_changed)

    def _apply_antigravity_style(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        # Custom styling for the Settings Dialog
        self.setStyleSheet(f"""
            /* Sidebar Navigation */
            QListWidget#SettingsNav {{
                background-color: {c["surface"]["secondary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["lg"]}px;
                outline: none;
                padding: 8px;
            }}

            QListWidget#SettingsNav::item {{
                height: 48px;
                padding-left: 16px;
                border-radius: {r["md"]}px;
                font-weight: 600;
                color: {c["text"]["secondary"]};
                margin-bottom: 4px;
            }}

            QListWidget#SettingsNav::item:hover {{
                background-color: {c["state"]["hover"]};
                color: {c["text"]["primary"]};
            }}

            QListWidget#SettingsNav::item:selected {{
                background-color: {c["brand"]["primary"]};
                color: #ffffff;
            }}

            /* Content Area */
            QStackedWidget#SettingsContent {{
                background: transparent;
            }}

            /* Scroll Area adjustment */
            QScrollArea {{
                background: transparent;
                border: none;
            }}

            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}

            /* Section Headers in Content */
            QLabel {{
                color: {c["text"]["primary"]};
            }}
        """)

    def _on_category_changed(self, row: int) -> None:
        self._stack.setCurrentIndex(row)

    def _on_settings_changed(self) -> None:
        # Enable save button or show indicator?
        pass

    def _reset_all(self) -> None:
        """Reset all categories to defaults."""
        res = QMessageBox.question(
            self,
            "Reset Preferences",
            "Are you sure you want to reset all preferences to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if res == QMessageBox.StandardButton.Yes:
            for cat in self._categories:
                cat.reset_settings()

    def _collect_settings(self) -> dict[str, object]:
        payload: dict[str, object] = {}
        for cat in self._categories:
            if isinstance(cat, GeneralSettings):
                payload["general"] = cat.collect_settings()
            elif isinstance(cat, EditorSettings):
                payload["editor"] = cat.collect_settings()
            elif isinstance(cat, GraphicsSettings):
                payload["graphics"] = cat.collect_settings()
            elif isinstance(cat, InterfaceSettings):
                payload["interface"] = cat.collect_settings()
            elif isinstance(cat, ClientVersionSettings):
                payload["client_version"] = cat.collect_settings()
        return payload

    def accept(self) -> None:
        """Save all changes on accept."""
        for cat in self._categories:
            if cat.has_changes():
                cat.apply_settings()

        self.settings_applied.emit(self._collect_settings())

        super().accept()
