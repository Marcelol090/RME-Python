"""Tileset Browser with categorized brush access.

Modern tileset browser with:
- Category tree/list
- Brush grid display
- Search and filter
- Favorites
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


@dataclass(slots=True)
class TilesetCategory:
    """A tileset category for organizing brushes."""

    id: str
    name: str
    icon: str = ""
    brush_count: int = 0


@dataclass(slots=True)
class TilesetBrush:
    """A brush within a tileset."""

    brush_id: int
    name: str
    category_id: str
    sprite_id: int | None = None


class CategoryList(QListWidget):
    """Side list of tileset categories."""

    category_selected = pyqtSignal(str)  # category id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._categories: list[TilesetCategory] = []

        self.setStyleSheet("""
            QListWidget {
                background: #2A2A3E;
                border: none;
                border-radius: 8px;
                outline: none;
            }
            
            QListWidget::item {
                padding: 12px 16px;
                border-radius: 6px;
                margin: 2px 4px;
                color: #E5E5E7;
            }
            
            QListWidget::item:hover {
                background: #363650;
            }
            
            QListWidget::item:selected {
                background: #8B5CF6;
            }
        """)

        self.itemClicked.connect(self._on_item_clicked)

    def set_categories(self, categories: list[TilesetCategory]) -> None:
        """Set the list of categories."""
        self._categories = categories
        self.clear()

        for cat in categories:
            icon = cat.icon or "📁"
            text = f"{icon} {cat.name}"
            if cat.brush_count > 0:
                text += f" ({cat.brush_count})"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, cat.id)
            self.addItem(item)

        # Select first item
        if self.count() > 0:
            self.setCurrentRow(0)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle category selection."""
        category_id = item.data(Qt.ItemDataRole.UserRole)
        self.category_selected.emit(category_id)


class BrushGridItem(QFrame):
    """Individual brush item in the grid."""

    clicked = pyqtSignal(int)  # brush_id

    def __init__(self, brush: TilesetBrush, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._brush = brush
        self._selected = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(72, 72)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Sprite placeholder
        sprite = QLabel(brush.name[0].upper() if brush.name else "?")
        sprite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sprite.setFixedSize(40, 40)
        sprite.setStyleSheet("""
            background: #1E1E2E;
            border-radius: 6px;
            color: #8B5CF6;
            font-size: 18px;
            font-weight: 700;
        """)
        layout.addWidget(sprite, alignment=Qt.AlignmentFlag.AlignCenter)

        # Name
        name = QLabel(self._truncate(brush.name, 10))
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet("color: #A1A1AA; font-size: 9px;")
        layout.addWidget(name)

        self._update_style()

    def _truncate(self, text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        return text[: max_len - 1] + "…"

    def _update_style(self) -> None:
        if self._selected:
            self.setStyleSheet("""
                BrushGridItem {
                    background: #363650;
                    border: 2px solid #8B5CF6;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                BrushGridItem {
                    background: #2A2A3E;
                    border: 1px solid #363650;
                    border-radius: 8px;
                }
                BrushGridItem:hover {
                    background: #363650;
                    border-color: #8B5CF6;
                }
            """)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self._update_style()

    def mousePressEvent(self, event: object) -> None:
        if hasattr(event, "button") and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._brush.brush_id)
        super().mousePressEvent(event)


class TilesetBrowser(QWidget):
    """Complete tileset browser widget.

    Signals:
        brush_selected: Emits brush_id when brush is clicked
    """

    brush_selected = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._categories: list[TilesetCategory] = []
        self._brushes: list[TilesetBrush] = []
        self._current_category: str = ""
        self._selected_brush_id: int | None = None
        self._brush_items: list[BrushGridItem] = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Search bar
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search brushes...")
        self.search.setStyleSheet("""
            QLineEdit {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 8px;
                padding: 10px 14px;
                color: #E5E5E7;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #8B5CF6;
            }
            QLineEdit::placeholder {
                color: #52525B;
            }
        """)
        self.search.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search)

        # Splitter for categories and brushes
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Category list
        self.category_list = CategoryList()
        self.category_list.setMaximumWidth(180)
        self.category_list.category_selected.connect(self._on_category_changed)
        splitter.addWidget(self.category_list)

        # Brush grid area
        brush_container = QWidget()
        brush_layout = QVBoxLayout(brush_container)
        brush_layout.setContentsMargins(0, 0, 0, 0)

        # Category header
        self.category_header = QLabel("")
        self.category_header.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #E5E5E7;
            padding: 8px 0;
        """)
        brush_layout.addWidget(self.category_header)

        # Scroll area for grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)

        self.brush_grid = QWidget()
        self.brush_grid_layout = QHBoxLayout(self.brush_grid)
        self.brush_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.brush_grid_layout.setSpacing(8)
        self.brush_grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # Use flow layout simulation with wrap
        from PyQt6.QtWidgets import QGridLayout

        self.brush_grid_layout = QGridLayout(self.brush_grid)
        self.brush_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.brush_grid_layout.setSpacing(8)

        scroll.setWidget(self.brush_grid)
        brush_layout.addWidget(scroll)

        splitter.addWidget(brush_container)
        splitter.setSizes([180, 400])

        layout.addWidget(splitter)

    def set_data(self, categories: list[TilesetCategory], brushes: list[TilesetBrush]) -> None:
        """Set tileset data.

        Args:
            categories: List of category definitions
            brushes: List of all brushes
        """
        self._categories = categories
        self._brushes = brushes

        # Update category brush counts
        for cat in categories:
            cat.brush_count = sum(1 for b in brushes if b.category_id == cat.id)

        self.category_list.set_categories(categories)

        # Select first category
        if categories:
            self._show_category(categories[0].id)

    def _show_category(self, category_id: str) -> None:
        """Display brushes for a category."""
        self._current_category = category_id

        # Find category name
        cat = next((c for c in self._categories if c.id == category_id), None)
        if cat:
            self.category_header.setText(f"{cat.icon} {cat.name}")
        else:
            self.category_header.setText("")

        # Filter brushes
        filtered = [b for b in self._brushes if b.category_id == category_id]

        # Clear grid
        for item in self._brush_items:
            item.deleteLater()
        self._brush_items.clear()

        # Clear layout
        while self.brush_grid_layout.count():
            child = self.brush_grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add brushes in grid (5 columns)
        cols = 5
        for i, brush in enumerate(filtered):
            item = BrushGridItem(brush)
            item.clicked.connect(self._on_brush_clicked)

            # Check if selected
            if brush.brush_id == self._selected_brush_id:
                item.set_selected(True)

            row = i // cols
            col = i % cols
            self.brush_grid_layout.addWidget(item, row, col)
            self._brush_items.append(item)

    def _on_category_changed(self, category_id: str) -> None:
        """Handle category selection change."""
        self._show_category(category_id)

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        if not text:
            # Reset to current category
            self._show_category(self._current_category)
            return

        # Search across all brushes
        text_lower = text.lower()
        filtered = [b for b in self._brushes if text_lower in b.name.lower() or text_lower in str(b.brush_id)]

        self.category_header.setText(f"🔍 Search: {len(filtered)} results")

        # Clear and rebuild grid
        for item in self._brush_items:
            item.deleteLater()
        self._brush_items.clear()

        while self.brush_grid_layout.count():
            child = self.brush_grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        cols = 5
        for i, brush in enumerate(filtered[:50]):  # Limit results
            item = BrushGridItem(brush)
            item.clicked.connect(self._on_brush_clicked)

            row = i // cols
            col = i % cols
            self.brush_grid_layout.addWidget(item, row, col)
            self._brush_items.append(item)

    def _on_brush_clicked(self, brush_id: int) -> None:
        """Handle brush click."""
        self._selected_brush_id = brush_id

        # Update selection state
        for item in self._brush_items:
            item.set_selected(item._brush.brush_id == brush_id)

        self.brush_selected.emit(brush_id)

    def select_brush(self, brush_id: int) -> None:
        """Programmatically select a brush."""
        self._selected_brush_id = brush_id

        # Find category and switch to it
        brush = next((b for b in self._brushes if b.brush_id == brush_id), None)
        if brush and brush.category_id != self._current_category:
            self._show_category(brush.category_id)

            # Select in category list
            for i in range(self.category_list.count()):
                item = self.category_list.item(i)
                if item and item.data(Qt.ItemDataRole.UserRole) == brush.category_id:
                    self.category_list.setCurrentItem(item)
                    break
        else:
            # Just update selection in current view
            for item in self._brush_items:
                item.set_selected(item._brush.brush_id == brush_id)
