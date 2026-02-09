"""Modern Palette Dock with Grid View."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLineEdit,
    QListView,
    QSlider,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class ModernPaletteDock(QDockWidget):
    """Modern palette dock with grid view and advanced filtering."""

    def __init__(self, editor: QtMapEditor, parent: QWidget | None = None) -> None:
        super().__init__("Modern Palette", parent)
        self.editor = editor
        self._brushes = []
        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(200)
        self._filter_timer.timeout.connect(self._refresh_list)

        self._setup_ui()
        self._setup_connections()

        # Initial load delayed to allow editor to fully init
        QTimer.singleShot(500, self.refresh)

    def _setup_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Top Bar: Category and Search
        top_layout = QHBoxLayout()

        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "All", "Terrain", "Doodad", "Item", "Creature", "House", "Zone", "RAW"
        ])
        top_layout.addWidget(self.category_combo)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search brushes...")
        self.search_edit.setClearButtonEnabled(True)
        top_layout.addWidget(self.search_edit)

        layout.addLayout(top_layout)

        # View Settings
        view_settings_layout = QHBoxLayout()

        self.icon_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.icon_size_slider.setRange(16, 128)
        self.icon_size_slider.setValue(48)
        self.icon_size_slider.setToolTip("Icon Size")
        view_settings_layout.addWidget(self.icon_size_slider)

        layout.addLayout(view_settings_layout)

        # Main List View
        self.list_view = QListView()
        self.list_view.setViewMode(QListView.ViewMode.IconMode)
        self.list_view.setResizeMode(QListView.ResizeMode.Adjust)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setGridSize(QSize(56, 72))  # Initial grid size
        self.list_view.setWordWrap(True)
        self.list_view.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.list_view.setEditTriggers(QListView.EditTrigger.NoEditTriggers)

        self.model = QStandardItemModel()
        self.list_view.setModel(self.model)

        layout.addWidget(self.list_view)

        self.setWidget(container)

    def _setup_connections(self) -> None:
        self.category_combo.currentTextChanged.connect(self._trigger_refresh)
        self.search_edit.textChanged.connect(self._trigger_refresh)
        self.icon_size_slider.valueChanged.connect(self._update_icon_size)
        self.list_view.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def _trigger_refresh(self) -> None:
        self._filter_timer.start()

    def _update_icon_size(self, size: int) -> None:
        grid_width = size + 16
        grid_height = size + 32  # Extra space for text
        self.list_view.setIconSize(QSize(size, size))
        self.list_view.setGridSize(QSize(grid_width, grid_height))

    def refresh(self) -> None:
        """Reload all brushes from manager."""
        self._refresh_list()

    def _refresh_list(self) -> None:
        self.model.clear()

        category = self.category_combo.currentText().lower()
        search = self.search_edit.text().lower()

        # This is a simplified logic. In a real scenario we would fetch brushes efficiently.
        # We access the brush manager directly.
        brush_mgr = self.editor.brush_mgr
        if not brush_mgr:
            return

        # Fetch brushes based on category
        # Currently leveraging private attributes or iter methods if available
        # Assuming brush_mgr has methods or we iterate all

        items = []

        if category == "doodad" or category == "all":
             for sid, name in brush_mgr.iter_doodad_brushes():
                 if search and search not in str(name).lower():
                     continue
                 items.append(self._create_item(int(sid), str(name), "doodad"))

        if category == "terrain" or category == "all":
             # Logic to fetch terrain brushes
             # This depends on how BrushManager exposes them.
             # Reusing PaletteManager logic would be ideal but it's UI coupled.
             # We assume raw iteration for now
             for brush_id, brush in getattr(brush_mgr, "_brushes", {}).items():
                 btype = getattr(brush, "brush_type", "")
                 if btype in ("ground", "carpet"):
                     if search and search not in str(getattr(brush, "name", "")).lower():
                         continue
                     items.append(self._create_item(int(brush_id), str(getattr(brush, "name", "")), "terrain"))

        # Add more categories logic...

        for item in items:
            self.model.appendRow(item)

    def _create_item(self, brush_id: int, name: str, category: str) -> QStandardItem:
        item = QStandardItem(name)
        item.setData(brush_id, Qt.ItemDataRole.UserRole)
        item.setData(category, Qt.ItemDataRole.UserRole + 1)
        item.setToolTip(f"{name} (ID: {brush_id})")

        # Load icon (expensive, should be async or cached)
        try:
            pm = self.editor._sprite_pixmap_for_server_id(brush_id, tile_px=32)
            if pm and not pm.isNull():
                item.setIcon(QIcon(pm))
        except Exception:
            pass

        return item

    def _on_selection_changed(self, selected, deselected) -> None:
        indexes = selected.indexes()
        if not indexes:
            return

        index = indexes[0]
        brush_id = self.model.data(index, Qt.ItemDataRole.UserRole)

        if brush_id is not None:
            # Activate brush in editor
            self.editor._set_selected_brush_id(int(brush_id))
