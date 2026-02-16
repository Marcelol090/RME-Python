"""Quick Access Toolbar / Favorites.

Provides quick access to frequently used brushes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
)

if TYPE_CHECKING:
    pass


@dataclass(slots=True)
class FavoriteItem:
    """A favorite/quick access item."""

    item_id: int
    name: str
    icon: str = "BR"
    category: str = ""


class FavoriteButton(QPushButton):
    """Button for a favorite item."""

    item_clicked = pyqtSignal(int)  # item_id
    remove_requested = pyqtSignal(int)  # item_id

    def __init__(self, item: FavoriteItem, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._item = item

        self.setText(item.icon)
        self.setToolTip(f"{item.name}\nRight-click to remove")
        self.setFixedSize(40, 40)

        self.clicked.connect(lambda: self.item_clicked.emit(item.item_id))

        self._apply_style()

    def _apply_style(self) -> None:
        """Apply styling."""
        from py_rme_canary.vis_layer.ui.theme import get_theme_manager
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.setStyleSheet(
            f"""
            FavoriteButton {{
                background: {c["surface"]["secondary"]};
                color: {c["text"]["primary"]};
                border: 2px solid transparent;
                border-radius: {r["md"]}px;
                font-size: 18px;
            }}

            FavoriteButton:hover {{
                background: {c["state"]["hover"]};
                border-color: {c["brand"]["primary"]};
            }}

            FavoriteButton:pressed {{
                background: {c["brand"]["primary"]};
            }}
            """
        )

    def contextMenuEvent(self, event: object) -> None:
        """Handle right-click."""
        from PyQt6.QtWidgets import QMenu

        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 6px;
                padding: 4px;
                color: #E5E5E7;
            }
            QMenu::item {
                padding: 6px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: #8B5CF6;
            }
        """
        )

        remove_action = menu.addAction("Remove from favorites")

        action = menu.exec(event.globalPos())
        if action == remove_action:
            self.remove_requested.emit(self._item.item_id)


class QuickAccessBar(QFrame):
    """Quick access toolbar for favorite brushes.

    Signals:
        item_selected: Emits item_id when clicked
    """

    item_selected = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._items: list[FavoriteItem] = []
        self._buttons: list[FavoriteButton] = []

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        from py_rme_canary.vis_layer.ui.theme import get_theme_manager
        tm = get_theme_manager()
        c = tm.tokens["color"]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # Label
        label = QLabel("Fav")
        label.setToolTip("Favorites")
        label.setStyleSheet(f"color: {c['brand']['secondary']}; font-weight: bold;")
        layout.addWidget(label)

        # Scroll area for buttons
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setMaximumHeight(48)

        self.buttons_container = QWidget()
        self.buttons_layout = QHBoxLayout(self.buttons_container)
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.setSpacing(4)
        self.buttons_layout.addStretch()

        scroll.setWidget(self.buttons_container)
        layout.addWidget(scroll)

        # Add button
        self.btn_add = QPushButton("+")
        self.btn_add.setFixedSize(32, 32)
        self.btn_add.setToolTip("Add current brush to favorites")
        layout.addWidget(self.btn_add)

    def _apply_style(self) -> None:
        """Apply styling."""
        from py_rme_canary.vis_layer.ui.theme import get_theme_manager
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.setStyleSheet(
            f"""
            QuickAccessBar {{
                background: {c["surface"]["secondary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["lg"]}px;
            }}

            QPushButton {{
                background: {c["surface"]["tertiary"]};
                color: {c["text"]["secondary"]};
                border: none;
                border-radius: {r["sm"]}px;
                font-size: 14px;
            }}

            QPushButton:hover {{
                background: {c["brand"]["primary"]};
                color: {c["text"]["primary"]};
            }}
            """
        )

    def add_favorite(self, item: FavoriteItem) -> None:
        """Add a favorite item."""
        # Check if already exists
        for existing in self._items:
            if existing.item_id == item.item_id:
                return

        self._items.append(item)

        btn = FavoriteButton(item)
        btn.item_clicked.connect(self.item_selected.emit)
        btn.remove_requested.connect(self._remove_by_id)

        # Insert before stretch
        self.buttons_layout.insertWidget(self.buttons_layout.count() - 1, btn)
        self._buttons.append(btn)

    def remove_favorite(self, item_id: int) -> None:
        """Remove a favorite by ID."""
        self._remove_by_id(item_id)

    def _remove_by_id(self, item_id: int) -> None:
        """Remove item by ID."""
        for i, item in enumerate(self._items):
            if item.item_id == item_id:
                self._items.pop(i)
                btn = self._buttons.pop(i)
                btn.deleteLater()
                break

    def set_favorites(self, items: list[FavoriteItem]) -> None:
        """Set all favorites."""
        # Clear existing
        for btn in self._buttons:
            btn.deleteLater()
        self._buttons.clear()
        self._items.clear()

        # Add new
        for item in items:
            self.add_favorite(item)

    def get_favorites(self) -> list[FavoriteItem]:
        """Get current favorites."""
        return self._items.copy()
