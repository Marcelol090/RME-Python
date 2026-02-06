"""Find Brush Dialog.

Quick brush finder with searchable list - matches C++ FindBrushDialog from Redux.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent, QPainter, QPen
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStyledItemDelegate,
    QVBoxLayout,
)

if TYPE_CHECKING:
    pass


@dataclass
class BrushInfo:
    """Brush info for display in list."""

    name: str
    brush_id: str
    category: str = ""
    sprite_id: int = 0
    is_raw: bool = False
    brush_ref: object = None

    def matches(self, q: str) -> bool:
        return q in self.name.lower() or q in self.brush_id.lower()


class BrushItemDelegate(QStyledItemDelegate):
    """Custom delegate for brush items with sprite preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._row_height = 36

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), self._row_height)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        if option.state & 0x0008:  # State_Selected
            painter.fillRect(option.rect, QColor(0x8B, 0x5C, 0xF6, 100))
        elif option.state & 0x1000:  # State_MouseOver
            painter.fillRect(option.rect, QColor(0x36, 0x36, 0x50))
        else:
            painter.fillRect(option.rect, QColor(0x1E, 0x1E, 0x2E))

        # Get brush info
        brush_info = index.data(Qt.ItemDataRole.UserRole)
        if brush_info:
            # Sprite placeholder (32x32)
            sprite_rect = option.rect.adjusted(4, 2, -option.rect.width() + 36, -2)
            painter.setPen(QPen(QColor(0x36, 0x36, 0x50), 1))
            painter.setBrush(QColor(0x2A, 0x2A, 0x3E))
            painter.drawRoundedRect(sprite_rect, 4, 4)

            # Sprite ID text as placeholder
            painter.setPen(QColor(0x8B, 0x8B, 0x9B))
            painter.drawText(sprite_rect, Qt.AlignmentFlag.AlignCenter, str(brush_info.sprite_id or "?"))

            # Brush name
            text_x = 44
            painter.setPen(QColor(0xE5, 0xE5, 0xE7))
            painter.drawText(text_x, option.rect.y() + 16, brush_info.name)

            # Category / id
            painter.setPen(QColor(0x8B, 0x8B, 0x9B))
            cat_text = brush_info.category or brush_info.brush_id
            if brush_info.is_raw:
                cat_text += " [RAW]"
            painter.drawText(text_x, option.rect.y() + 30, cat_text)

        painter.restore()


class BrushListBox(QListWidget):
    """Virtual list box for brushes with custom rendering."""

    brush_selected = pyqtSignal(object)  # BrushInfo
    brush_activated = pyqtSignal(object)  # BrushInfo (double-click)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._brushes: list[BrushInfo] = []
        self._no_matches = False
        self._cleared = True

        self.setItemDelegate(BrushItemDelegate(self))
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setStyleSheet(
            """
            BrushListBox {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 4px;
            }
            BrushListBox::item {
                padding: 2px;
            }
            BrushListBox::item:selected {
                background: transparent;
            }
        """
        )

        self.itemDoubleClicked.connect(self._on_dbl)
        self.itemSelectionChanged.connect(self._on_sel)
        self._show_placeholder("Type at least 2 characters to search...")

    def _show_placeholder(self, text: str):
        self.clear()
        item = QListWidgetItem(text)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setForeground(QColor(0x8B, 0x8B, 0x9B))
        self.addItem(item)

    def set_no_matches(self):
        self._no_matches = True
        self._cleared = False
        self._show_placeholder("No matches for your search.")

    def clear_list(self):
        self._cleared = True
        self._no_matches = False
        self._brushes.clear()
        self._show_placeholder("Type at least 2 characters to search...")

    def add_brush(self, brush_info: BrushInfo):
        if self._cleared or self._no_matches:
            self.clear()
            self._cleared = False
            self._no_matches = False

        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, brush_info)
        item.setSizeHint(QSize(0, 36))
        self.addItem(item)
        self._brushes.append(brush_info)

    def get_selected_brush(self) -> BrushInfo | None:
        items = self.selectedItems()
        if not items or self._no_matches or self._cleared:
            return None
        return items[0].data(Qt.ItemDataRole.UserRole)

    def _on_sel(self):
        brush = self.get_selected_brush()
        if brush:
            self.brush_selected.emit(brush)

    def _on_dbl(self, item):
        brush = item.data(Qt.ItemDataRole.UserRole)
        if brush:
            self.brush_activated.emit(brush)


class KeyForwardingLineEdit(QLineEdit):
    """Line edit that forwards up/down keys to parent."""

    key_navigation = pyqtSignal(int)  # -1 up, 1 down, -10 pgup, 10 pgdown

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_Up:
            self.key_navigation.emit(-1)
        elif key == Qt.Key.Key_Down:
            self.key_navigation.emit(1)
        elif key == Qt.Key.Key_PageUp:
            self.key_navigation.emit(-10)
        elif key == Qt.Key.Key_PageDown:
            self.key_navigation.emit(10)
        else:
            super().keyPressEvent(event)


class FindBrushDialog(QDialog):
    """Quick brush finder with searchable list.

    Matches C++ FindBrushDialog from Redux - provides fast keyboard-driven
    brush search with virtual list for performance.
    """

    brush_selected = pyqtSignal(object)  # Selected BrushInfo

    def __init__(self, parent=None, title: str = "Jump to Brush"):
        super().__init__(parent)
        self._result: BrushInfo | None = None
        self._all_brushes: list[BrushInfo] = []
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._refresh_contents)

        self.setWindowTitle(title)
        self.setMinimumSize(500, 500)
        self._setup_ui()
        self._style()
        self._populate_brushes()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Search field
        self.search_field = KeyForwardingLineEdit()
        self.search_field.setPlaceholderText("Type to search...")
        self.search_field.setToolTip("Type at least 2 characters to search for brushes.")
        self.search_field.textChanged.connect(self._on_text_change)
        self.search_field.returnPressed.connect(self._on_ok)
        self.search_field.key_navigation.connect(self._navigate_list)
        layout.addWidget(self.search_field)

        # Brush list
        self.brush_list = BrushListBox()
        self.brush_list.setMinimumSize(470, 400)
        self.brush_list.setToolTip("Double click to select.")
        self.brush_list.brush_activated.connect(self._on_brush_activated)
        layout.addWidget(self.brush_list, 1)

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.search_field.setFocus()

    def _style(self):
        self.setStyleSheet(
            """
            FindBrushDialog {
                background: #1E1E2E;
            }
            QLineEdit {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #8B5CF6;
            }
            QPushButton {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #363650;
            }
            QPushButton:pressed {
                background: #8B5CF6;
            }
        """
        )

    def _populate_brushes(self):
        """Populate with sample brushes - override for real data."""
        categories = ["Ground", "Doodad", "Wall", "Border", "Creature", "Spawn", "House"]
        for i in range(1, 200):
            cat = categories[i % len(categories)]
            is_raw = i % 10 == 0
            self._all_brushes.append(
                BrushInfo(
                    name=f"{cat} Brush {i}",
                    brush_id=f"brush_{i}",
                    category=cat,
                    sprite_id=100 + i,
                    is_raw=is_raw,
                )
            )
        # Add some named RAW brushes
        for item_id in [2160, 2195, 2148, 2152, 2166, 2167]:
            self._all_brushes.append(
                BrushInfo(
                    name=f"Item {item_id}",
                    brush_id=f"raw_{item_id}",
                    category="Raw",
                    sprite_id=item_id,
                    is_raw=True,
                )
            )

    def set_brushes(self, brushes: list[BrushInfo]):
        """Set the list of available brushes."""
        self._all_brushes = brushes
        self._refresh_contents()

    def _on_text_change(self):
        # Debounce search
        self._idle_timer.start(300)

    def _refresh_contents(self):
        self.brush_list.clear_list()

        search_text = self.search_field.text().lower().strip()
        if len(search_text) < 2:
            return

        # Search non-RAW brushes first, then RAWs
        non_raws = []
        raws = []
        for brush in self._all_brushes:
            if brush.matches(search_text):
                if brush.is_raw:
                    raws.append(brush)
                else:
                    non_raws.append(brush)

        # Add non-RAWs first
        for brush in non_raws:
            self.brush_list.add_brush(brush)

        # Then RAWs
        for brush in raws:
            self.brush_list.add_brush(brush)

        if non_raws or raws:
            self.brush_list.setCurrentRow(0)
        else:
            self.brush_list.set_no_matches()

    def _navigate_list(self, delta: int):
        count = self.brush_list.count()
        if count == 0:
            return
        current = self.brush_list.currentRow()
        if current < 0:
            new_row = 0
        else:
            new_row = max(0, min(count - 1, current + delta))
        self.brush_list.setCurrentRow(new_row)

    def _on_brush_activated(self, brush: BrushInfo):
        self._result = brush
        self.accept()

    def _on_ok(self):
        brush = self.brush_list.get_selected_brush()
        if brush:
            self._result = brush
            self.accept()
        elif self.brush_list.count() > 0:
            # Try to search immediately if nothing selected
            self._refresh_contents()
            brush = self.brush_list.get_selected_brush()
            if brush:
                self._result = brush
                self.accept()

    def get_result(self) -> BrushInfo | None:
        """Get the selected brush info."""
        return self._result

    @staticmethod
    def get_brush(parent=None, title: str = "Jump to Brush") -> BrushInfo | None:
        """Static helper to show dialog and get result."""
        dlg = FindBrushDialog(parent, title)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            return dlg.get_result()
        return None
