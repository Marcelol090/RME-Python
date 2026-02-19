"""Tileset Properties Dialog - Configure tileset settings.

Modern PyQt6 dialog for managing map tilesets and their properties.
Replaces deprecated PySide6 version in _experimental/tileset.py.

Mirrors legacy C++ TilesetWindow/AddTilesetWindow from:
- source/ui/tileset_window.cpp
- source/ui/add_tileset_window.cpp

Reference:
    - C++ TilesetWindow: source/ui/tileset_window.h
    - C++ AddTilesetWindow: source/ui/add_tileset_window.h
    - Tileset system: core/data/tileset.py
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TilesetCategory(IntEnum):
    """Tileset category types."""

    TERRAIN = auto()
    DOODAD = auto()
    ITEM = auto()
    RAW = auto()
    CREATURE = auto()
    HOUSE = auto()
    WAYPOINT = auto()
    ZONE = auto()


@dataclass
class TilesetItem:
    """Represents an item in a tileset.

    Attributes:
        item_id: The game item ID.
        name: Display name (optional).
        weight: Randomization weight.
    """

    item_id: int
    name: str = ""
    weight: int = 100


@dataclass
class TilesetData:
    """Represents a tileset configuration.

    Attributes:
        name: Tileset name.
        category: Tileset category type.
        items: List of items in the tileset.
        auto_border: Enable auto-border for terrain.
        randomize: Enable randomization.
    """

    name: str
    category: TilesetCategory = TilesetCategory.TERRAIN
    items: list[TilesetItem] = field(default_factory=list)
    auto_border: bool = True
    randomize: bool = True


class TilesetItemTable(QTableWidget):
    """Table showing items in a tileset."""

    item_selected = pyqtSignal(int)  # item_id
    items_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_table()

    def _setup_table(self) -> None:
        """Configure table columns and behavior."""
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["ID", "Name", "Weight"])

        # Column sizing
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(0, 70)
        self.setColumnWidth(2, 70)

        # Selection behavior
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        # Alternating row colors
        self.setAlternatingRowColors(True)

        # Context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos) -> None:
        """Show context menu for item operations."""
        menu = QMenu(self)

        remove_action = QAction("Remove Selected", self)
        remove_action.triggered.connect(self.remove_selected)
        menu.addAction(remove_action)

        menu.addSeparator()

        clear_action = QAction("Clear All", self)
        clear_action.triggered.connect(self.clear_items)
        menu.addAction(clear_action)

        menu.exec(self.mapToGlobal(pos))

    def add_item(self, item: TilesetItem) -> None:
        """Add an item to the table."""
        row = self.rowCount()
        self.insertRow(row)

        id_item = QTableWidgetItem(str(item.item_id))
        id_item.setData(Qt.ItemDataRole.UserRole, item.item_id)
        id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        name_item = QTableWidgetItem(item.name or f"Item {item.item_id}")

        weight_item = QTableWidgetItem(str(item.weight))

        self.setItem(row, 0, id_item)
        self.setItem(row, 1, name_item)
        self.setItem(row, 2, weight_item)

        self.items_changed.emit()

    def remove_selected(self) -> None:
        """Remove selected items from table."""
        rows = sorted(set(idx.row() for idx in self.selectedIndexes()), reverse=True)
        for row in rows:
            self.removeRow(row)
        self.items_changed.emit()

    def clear_items(self) -> None:
        """Clear all items from table."""
        self.setRowCount(0)
        self.items_changed.emit()

    def get_items(self) -> list[TilesetItem]:
        """Get all items from the table.

        Returns:
            List of TilesetItem objects.
        """
        items = []
        for row in range(self.rowCount()):
            item_id = self.item(row, 0).data(Qt.ItemDataRole.UserRole)
            name = self.item(row, 1).text()
            try:
                weight = int(self.item(row, 2).text())
            except (ValueError, TypeError):
                weight = 100

            items.append(TilesetItem(item_id=item_id, name=name, weight=weight))
        return items

    def set_items(self, items: list[TilesetItem]) -> None:
        """Set items in the table.

        Args:
            items: List of TilesetItem objects.
        """
        self.setRowCount(0)
        for item in items:
            self.add_item(item)


class TilesetPropertiesDialog(QDialog):
    """Dialog for managing tileset configuration.

    Provides interface for:
    - Creating and editing tilesets
    - Adding/removing items to tilesets
    - Configuring auto-border and randomization
    - Managing multiple tilesets

    Signals:
        tileset_changed: Emitted when a tileset is modified.
        tileset_created: Emitted when a new tileset is created.
        tileset_deleted: Emitted when a tileset is deleted.
    """

    tileset_changed = pyqtSignal(TilesetData)
    tileset_created = pyqtSignal(TilesetData)
    tileset_deleted = pyqtSignal(str)  # tileset name

    def __init__(
        self,
        tilesets: list[TilesetData] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize tileset properties dialog.

        Args:
            tilesets: List of existing tilesets to edit.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._tilesets: dict[str, TilesetData] = {}

        if tilesets:
            for ts in tilesets:
                self._tilesets[ts.name] = ts

        self._current_tileset: TilesetData | None = None

        self.setWindowTitle("Tileset Configuration")
        self.setMinimumSize(700, 500)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()
        self._load_tilesets()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Tileset list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("Tilesets"))

        self._tileset_list = QListWidget()
        self._tileset_list.currentItemChanged.connect(self._on_tileset_selected)
        left_layout.addWidget(self._tileset_list)

        # List buttons
        btn_layout = QHBoxLayout()

        self._btn_new = QPushButton("New")
        self._btn_new.clicked.connect(self._create_tileset)
        btn_layout.addWidget(self._btn_new)

        self._btn_duplicate = QPushButton("Duplicate")
        self._btn_duplicate.clicked.connect(self._duplicate_tileset)
        btn_layout.addWidget(self._btn_duplicate)

        self._btn_delete = QPushButton("Delete")
        self._btn_delete.clicked.connect(self._delete_tileset)
        btn_layout.addWidget(self._btn_delete)

        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        # Right panel - Tileset properties
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Properties group
        props_group = QGroupBox("Properties")
        props_layout = QFormLayout(props_group)
        props_layout.setSpacing(10)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Tileset name")
        self._name_edit.textChanged.connect(self._on_name_changed)
        props_layout.addRow("Name:", self._name_edit)

        # Options
        options_layout = QHBoxLayout()

        self._auto_border_check = QCheckBox("Auto-Border")
        self._auto_border_check.setChecked(True)
        self._auto_border_check.setToolTip("Automatically apply borders to terrain")
        options_layout.addWidget(self._auto_border_check)

        self._randomize_check = QCheckBox("Randomize")
        self._randomize_check.setChecked(True)
        self._randomize_check.setToolTip("Randomize item selection based on weights")
        options_layout.addWidget(self._randomize_check)

        options_layout.addStretch()
        props_layout.addRow("Options:", options_layout)

        right_layout.addWidget(props_group)

        # Items group
        items_group = QGroupBox("Included Items")
        items_layout = QVBoxLayout(items_group)

        self._items_table = TilesetItemTable()
        items_layout.addWidget(self._items_table)

        # Add item controls
        add_layout = QHBoxLayout()

        self._item_id_spin = QSpinBox()
        self._item_id_spin.setRange(1, 65535)
        self._item_id_spin.setPrefix("ID: ")
        add_layout.addWidget(self._item_id_spin)

        self._btn_add_item = QPushButton("Add Item")
        self._btn_add_item.clicked.connect(self._add_item)
        add_layout.addWidget(self._btn_add_item)

        self._btn_remove_item = QPushButton("Remove Selected")
        self._btn_remove_item.clicked.connect(self._items_table.remove_selected)
        add_layout.addWidget(self._btn_remove_item)

        add_layout.addStretch()
        items_layout.addLayout(add_layout)

        right_layout.addWidget(items_group, 1)

        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([200, 500])

        layout.addWidget(splitter, 1)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_style(self) -> None:
        """Apply dark theme styling."""
        c = get_theme_manager().tokens["color"]
        r = get_theme_manager().tokens.get("radius", {})
        rad = r.get("md", 6)
        rad_sm = r.get("sm", 4)

        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {c['surface']['primary']};
                color: {c['text']['primary']};
            }}
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
            QTableWidget {{
                background-color: {c['surface']['tertiary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
                color: {c['text']['primary']};
                gridline-color: {c['border']['default']};
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QTableWidget::item:selected {{
                background-color: {c['brand']['secondary']};
            }}
            QHeaderView::section {{
                background-color: {c['surface']['secondary']};
                color: {c['text']['primary']};
                padding: 6px;
                border: none;
                border-bottom: 1px solid {c['border']['default']};
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
            QSpinBox {{
                background-color: {c['surface']['tertiary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
                padding: 6px 10px;
                color: {c['text']['primary']};
            }}
            QSpinBox:focus {{
                border-color: {c['brand']['secondary']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {c['border']['default']};
                border: none;
                width: 20px;
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
            QSplitter::handle {{
                background-color: {c['border']['default']};
                width: 2px;
            }}
            QDialogButtonBox QPushButton {{
                min-width: 90px;
            }}
        """
        )

    def _load_tilesets(self) -> None:
        """Load tilesets into the list."""
        self._tileset_list.clear()

        for name in sorted(self._tilesets.keys()):
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, name)
            self._tileset_list.addItem(item)

        if self._tileset_list.count() > 0:
            self._tileset_list.setCurrentRow(0)

    def _on_tileset_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        """Handle tileset selection change."""
        # Save previous tileset
        if previous is not None and self._current_tileset is not None:
            self._save_current_tileset()

        # Load new tileset
        if current is not None:
            name = current.data(Qt.ItemDataRole.UserRole)
            self._current_tileset = self._tilesets.get(name)
            self._load_current_tileset()
        else:
            self._current_tileset = None
            self._clear_form()

    def _load_current_tileset(self) -> None:
        """Load current tileset into form."""
        if self._current_tileset is None:
            return

        self._name_edit.setText(self._current_tileset.name)
        self._auto_border_check.setChecked(self._current_tileset.auto_border)
        self._randomize_check.setChecked(self._current_tileset.randomize)
        self._items_table.set_items(self._current_tileset.items)

    def _save_current_tileset(self) -> None:
        """Save form values to current tileset."""
        if self._current_tileset is None:
            return

        self._current_tileset.auto_border = self._auto_border_check.isChecked()
        self._current_tileset.randomize = self._randomize_check.isChecked()
        self._current_tileset.items = self._items_table.get_items()

    def _clear_form(self) -> None:
        """Clear the form fields."""
        self._name_edit.clear()
        self._auto_border_check.setChecked(True)
        self._randomize_check.setChecked(True)
        self._items_table.clear_items()

    def _on_name_changed(self, text: str) -> None:
        """Handle tileset name change."""
        current = self._tileset_list.currentItem()
        if current is not None:
            old_name = current.data(Qt.ItemDataRole.UserRole)
            if text and text != old_name:
                # Update internal data
                if old_name in self._tilesets:
                    tileset = self._tilesets.pop(old_name)
                    tileset.name = text
                    self._tilesets[text] = tileset
                    self._current_tileset = tileset

                # Update list item
                current.setText(text)
                current.setData(Qt.ItemDataRole.UserRole, text)

    def _create_tileset(self) -> None:
        """Create a new tileset."""
        # Generate unique name
        base_name = "New Tileset"
        name = base_name
        counter = 1
        while name in self._tilesets:
            name = f"{base_name} {counter}"
            counter += 1

        tileset = TilesetData(name=name)
        self._tilesets[name] = tileset

        item = QListWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, name)
        self._tileset_list.addItem(item)
        self._tileset_list.setCurrentItem(item)

        self.tileset_created.emit(tileset)

    def _duplicate_tileset(self) -> None:
        """Duplicate the selected tileset."""
        if self._current_tileset is None:
            return

        # Generate unique name
        base_name = f"{self._current_tileset.name} Copy"
        name = base_name
        counter = 1
        while name in self._tilesets:
            name = f"{base_name} {counter}"
            counter += 1

        tileset = TilesetData(
            name=name,
            category=self._current_tileset.category,
            items=self._current_tileset.items.copy(),
            auto_border=self._current_tileset.auto_border,
            randomize=self._current_tileset.randomize,
        )
        self._tilesets[name] = tileset

        item = QListWidgetItem(name)
        item.setData(Qt.ItemDataRole.UserRole, name)
        self._tileset_list.addItem(item)
        self._tileset_list.setCurrentItem(item)

        self.tileset_created.emit(tileset)

    def _delete_tileset(self) -> None:
        """Delete the selected tileset."""
        current = self._tileset_list.currentItem()
        if current is None:
            return

        name = current.data(Qt.ItemDataRole.UserRole)
        if name in self._tilesets:
            del self._tilesets[name]

        row = self._tileset_list.row(current)
        self._tileset_list.takeItem(row)

        self.tileset_deleted.emit(name)

    def _add_item(self) -> None:
        """Add an item to the current tileset."""
        item_id = self._item_id_spin.value()
        self._items_table.add_item(TilesetItem(item_id=item_id))

    def _on_accept(self) -> None:
        """Handle OK button click."""
        # Save current tileset
        self._save_current_tileset()

        # Emit changes for all tilesets
        for tileset in self._tilesets.values():
            self.tileset_changed.emit(tileset)

        self.accept()

    def get_tilesets(self) -> list[TilesetData]:
        """Get all tilesets.

        Returns:
            List of TilesetData objects.
        """
        self._save_current_tileset()
        return list(self._tilesets.values())

    def add_tileset(self, tileset: TilesetData) -> None:
        """Add a tileset.

        Args:
            tileset: The tileset to add.
        """
        self._tilesets[tileset.name] = tileset
        self._load_tilesets()
