"""Container Properties Window.

Edit items inside containers - matches C++ ContainerPropertiesWindow from Redux.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

if TYPE_CHECKING:
    pass


@dataclass
class ContainerItem:
    """Item inside a container."""

    index: int
    item_id: int = 0
    name: str = ""
    client_id: int = 0
    action_id: int = 0
    unique_id: int = 0

    @property
    def is_empty(self) -> bool:
        return self.item_id == 0


class ContainerItemButton(QPushButton):
    """Button representing a container slot with item sprite."""

    item_clicked = pyqtSignal(int)  # index
    item_right_clicked = pyqtSignal(int, object)  # index, QPoint

    def __init__(self, index: int, item: ContainerItem | None = None, large: bool = True, parent=None):
        super().__init__(parent)
        self._index = index
        self._item = item
        self._large = large

        size = 36 if large else 20
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_right_click)
        self.clicked.connect(lambda: self.item_clicked.emit(self._index))
        self._update_tooltip()
        self._style()

    def _style(self):
        self.setStyleSheet(
            """
            ContainerItemButton {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 4px;
            }
            ContainerItemButton:hover {
                border-color: #8B5CF6;
                background: #363650;
            }
            ContainerItemButton:pressed {
                background: #8B5CF6;
            }
        """
        )

    def _update_tooltip(self):
        if self._item and not self._item.is_empty:
            self.setToolTip(self._item.name or f"Item #{self._item.item_id}")
        else:
            self.setToolTip("Empty Slot")

    def set_item(self, item: ContainerItem | None):
        self._item = item
        self._update_tooltip()
        self.update()

    def get_item(self) -> ContainerItem | None:
        return self._item

    def get_index(self) -> int:
        return self._index

    def _on_right_click(self, pos):
        self.item_right_clicked.emit(self._index, self.mapToGlobal(pos))

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._item and not self._item.is_empty:
            # Draw sprite placeholder
            rect = self.rect().adjusted(2, 2, -2, -2)
            painter.setPen(QPen(QColor(0x8B, 0x5C, 0xF6), 1))
            painter.setBrush(QColor(0x36, 0x36, 0x50))
            painter.drawRoundedRect(rect, 2, 2)

            # Draw item ID
            painter.setPen(QColor(0xE5, 0xE5, 0xE7))
            font = painter.font()
            font.setPointSize(7 if self._large else 5)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(self._item.item_id))
        else:
            # Draw empty slot indicator
            rect = self.rect().adjusted(4, 4, -4, -4)
            painter.setPen(QPen(QColor(0x36, 0x36, 0x50), 1, Qt.PenStyle.DotLine))
            painter.drawRect(rect)


class ContainerPropertiesWindow(QDialog):
    """Edit items inside a container.

    Matches C++ ContainerPropertiesWindow from Redux - provides grid of
    container slots with add/edit/remove functionality.
    """

    items_changed = pyqtSignal()  # Emitted when container contents change

    def __init__(
        self,
        parent=None,
        container_id: int = 0,
        container_name: str = "Container",
        volume: int = 20,
        action_id: int = 0,
        unique_id: int = 0,
        items: list[ContainerItem] | None = None,
        use_large_icons: bool = True,
    ):
        super().__init__(parent)
        self._container_id = container_id
        self._container_name = container_name
        self._volume = volume
        self._action_id = action_id
        self._unique_id = unique_id
        self._use_large = use_large_icons
        self._last_clicked_index: int = -1
        self._item_buttons: list[ContainerItemButton] = []

        # Initialize container items
        self._items: list[ContainerItem] = []
        for i in range(volume):
            if items and i < len(items):
                self._items.append(items[i])
            else:
                self._items.append(ContainerItem(index=i))

        self.setWindowTitle("Container Properties")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Properties group
        props_group = QGroupBox("Container Properties")
        props_layout = QGridLayout(props_group)
        props_layout.setSpacing(8)

        # ID and name
        props_layout.addWidget(QLabel(f"ID: {self._container_id}"), 0, 0)
        props_layout.addWidget(QLabel(f'"{self._container_name}"'), 0, 1)

        # Action ID
        props_layout.addWidget(QLabel("Action ID:"), 1, 0)
        self.action_id_spin = QSpinBox()
        self.action_id_spin.setRange(0, 65535)
        self.action_id_spin.setValue(self._action_id)
        self.action_id_spin.setToolTip("Action ID (0-65535). Used for scripting.")
        props_layout.addWidget(self.action_id_spin, 1, 1)

        # Unique ID
        props_layout.addWidget(QLabel("Unique ID:"), 2, 0)
        self.unique_id_spin = QSpinBox()
        self.unique_id_spin.setRange(0, 65535)
        self.unique_id_spin.setValue(self._unique_id)
        self.unique_id_spin.setToolTip("Unique ID (0-65535). Must be unique on the map.")
        props_layout.addWidget(self.unique_id_spin, 2, 1)

        layout.addWidget(props_group)

        # Contents group
        contents_group = QGroupBox(f"Contents (0/{self._volume})")
        self._contents_label = contents_group
        contents_layout = QGridLayout(contents_group)
        contents_layout.setSpacing(4)

        # Calculate columns based on icon size
        max_columns = 6 if self._use_large else 12

        for i in range(self._volume):
            item = self._items[i] if i < len(self._items) else None
            btn = ContainerItemButton(i, item, self._use_large, self)
            btn.item_clicked.connect(self._on_item_click)
            btn.item_right_clicked.connect(self._on_item_right_click)

            row = i // max_columns
            col = i % max_columns
            contents_layout.addWidget(btn, row, col)
            self._item_buttons.append(btn)

        layout.addWidget(contents_group)

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self._update_contents_label()

    def _style(self):
        self.setStyleSheet(
            """
            ContainerPropertiesWindow {
                background: #1E1E2E;
            }
            QGroupBox {
                color: #E5E5E7;
                font-weight: bold;
                border: 1px solid #363650;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QLabel {
                color: #E5E5E7;
            }
            QSpinBox {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 4px;
            }
            QSpinBox:focus {
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

    def _update_contents_label(self):
        count = sum(1 for item in self._items if not item.is_empty)
        self._contents_label.setTitle(f"Contents ({count}/{self._volume})")

    def _on_item_click(self, index: int):
        self._last_clicked_index = index
        item = self._items[index]
        if item.is_empty:
            self._add_item(index)
        else:
            self._edit_item(index)

    def _on_item_right_click(self, index: int, pos):
        self._last_clicked_index = index
        item = self._items[index]

        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
            }
            QMenu::item:selected {
                background: #8B5CF6;
            }
        """
        )

        if item.is_empty:
            menu.addAction("Add Item", lambda: self._add_item(index))
        else:
            menu.addAction("Edit Item", lambda: self._edit_item(index))
            menu.addAction("Add Item", lambda: self._add_item(index))
            menu.addSeparator()
            menu.addAction("Remove Item", lambda: self._remove_item(index))

        menu.exec(pos)

    def _add_item(self, index: int):
        """Show item picker and add item to slot."""
        # Import here to avoid circular imports
        try:
            from .find_item_dialog import FindItemDialog

            dlg = FindItemDialog(self, "Select Item")
            if dlg.exec() == QDialog.DialogCode.Accepted:
                result = dlg.get_result()
                if result:
                    self._items[index] = ContainerItem(
                        index=index,
                        item_id=result.item_id,
                        name=result.name,
                        client_id=result.client_id,
                    )
                    self._item_buttons[index].set_item(self._items[index])
                    self._update_contents_label()
                    self.items_changed.emit()
        except ImportError:
            # Fallback - just show placeholder
            QMessageBox.information(self, "Add Item", f"Add item to slot {index}")

    def _edit_item(self, index: int):
        """Show item properties dialog."""
        item = self._items[index]
        if item.is_empty:
            return
        QMessageBox.information(self, "Edit Item", f"Edit item: {item.name or f'#{item.item_id}'}\n" f"at slot {index}")

    def _remove_item(self, index: int):
        """Remove item from slot after confirmation."""
        reply = QMessageBox.question(
            self,
            "Remove Item",
            "Are you sure you want to remove this item from the container?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._items[index] = ContainerItem(index=index)
            self._item_buttons[index].set_item(self._items[index])
            self._update_contents_label()
            self.items_changed.emit()

    def _on_ok(self):
        self._action_id = self.action_id_spin.value()
        self._unique_id = self.unique_id_spin.value()
        self.accept()

    def get_action_id(self) -> int:
        return self._action_id

    def get_unique_id(self) -> int:
        return self._unique_id

    def get_items(self) -> list[ContainerItem]:
        return [item for item in self._items if not item.is_empty]

    def update_display(self):
        """Refresh all item buttons."""
        for i, btn in enumerate(self._item_buttons):
            if i < len(self._items):
                btn.set_item(self._items[i])
        self._update_contents_label()
