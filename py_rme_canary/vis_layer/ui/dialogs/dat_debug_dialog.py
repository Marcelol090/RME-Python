"""DAT Debug View Dialog.

Debug tool for viewing and inspecting loaded sprites from DAT/SPR files.
Useful for verifying sprite loading and identifying missing/corrupted sprites.

Mirrors legacy C++ DatDebugView from source/dat_debug_view.cpp.

Reference:
    - C++ DatDebugView: source/dat_debug_view.cpp
    - Graphics System: vis_layer/renderer/
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QAbstractListModel, QModelIndex, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SpriteInfo:
    """Information about a sprite for the debug view.

    Attributes:
        sprite_id: Unique sprite identifier.
        width: Sprite width in pixels.
        height: Sprite height in pixels.
        layers: Number of animation layers.
        frames: Number of animation frames.
        is_valid: Whether sprite data is valid.
        pixmap: Cached QPixmap for display (optional).
    """

    sprite_id: int
    width: int = 32
    height: int = 32
    layers: int = 1
    frames: int = 1
    is_valid: bool = True
    pixmap: QPixmap | None = None


class SpriteListModel(QAbstractListModel):
    """Model for sprite list display."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sprites: list[SpriteInfo] = []
        self._filtered_indices: list[int] = []
        self._filter_text = ""

    def set_sprites(self, sprites: list[SpriteInfo]) -> None:
        """Set the sprite list."""
        self.beginResetModel()
        self._sprites = sprites
        self._apply_filter()
        self.endResetModel()

    def set_filter(self, text: str) -> None:
        """Filter sprites by ID (partial match)."""
        self.beginResetModel()
        self._filter_text = text.strip()
        self._apply_filter()
        self.endResetModel()

    def _apply_filter(self) -> None:
        """Apply current filter to sprite list."""
        if not self._filter_text:
            self._filtered_indices = list(range(len(self._sprites)))
        else:
            try:
                # Try exact ID match first
                target_id = int(self._filter_text)
                self._filtered_indices = [
                    i for i, s in enumerate(self._sprites) if str(s.sprite_id).startswith(str(target_id))
                ]
            except ValueError:
                # Fall back to string match
                self._filtered_indices = [
                    i for i, s in enumerate(self._sprites) if self._filter_text.lower() in str(s.sprite_id).lower()
                ]

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._filtered_indices)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        idx = index.row()
        if idx < 0 or idx >= len(self._filtered_indices):
            return None

        sprite = self._sprites[self._filtered_indices[idx]]

        if role == Qt.ItemDataRole.DisplayRole:
            return f"ID: {sprite.sprite_id}"
        elif role == Qt.ItemDataRole.UserRole:
            return sprite
        elif role == Qt.ItemDataRole.DecorationRole:
            return sprite.pixmap if sprite.pixmap else None

        return None

    def get_sprite(self, row: int) -> SpriteInfo | None:
        """Get sprite info by visible row."""
        if row < 0 or row >= len(self._filtered_indices):
            return None
        return self._sprites[self._filtered_indices[row]]


class SpriteDelegate(QStyledItemDelegate):
    """Custom delegate for sprite list items."""

    CELL_SIZE = 48
    SPRITE_SIZE = 32

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

    def sizeHint(self, option, index: QModelIndex) -> QSize:
        return QSize(self.CELL_SIZE, self.CELL_SIZE)

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        painter.save()

        # Background
        if option.state & 1:  # Selected
            painter.fillRect(option.rect, QColor("#8B5CF6"))
        elif option.state & 2:  # Hover
            painter.fillRect(option.rect, QColor("#2A2A3E"))
        else:
            painter.fillRect(option.rect, QColor("#1A1A2E"))

        sprite = index.data(Qt.ItemDataRole.UserRole)
        if sprite:
            # Draw sprite placeholder
            sprite_rect = option.rect.adjusted(2, 2, -2, -16)

            if sprite.pixmap and not sprite.pixmap.isNull():
                scaled = sprite.pixmap.scaled(
                    sprite_rect.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                x = sprite_rect.x() + (sprite_rect.width() - scaled.width()) // 2
                y = sprite_rect.y() + (sprite_rect.height() - scaled.height()) // 2
                painter.drawPixmap(x, y, scaled)
            else:
                # Draw placeholder
                painter.setPen(QColor("#363650"))
                painter.setBrush(QColor("#2A2A3E"))
                painter.drawRect(sprite_rect)

                if not sprite.is_valid:
                    painter.setPen(QColor("#EF4444"))
                    painter.drawText(sprite_rect, Qt.AlignmentFlag.AlignCenter, "✗")

            # Draw ID label
            painter.setPen(QColor("#A1A1AA"))
            label_rect = option.rect.adjusted(2, self.CELL_SIZE - 16, -2, -2)
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, str(sprite.sprite_id))

        painter.restore()


class SpriteDetailPanel(QFrame):
    """Panel showing detailed sprite information."""

    go_to_id = pyqtSignal(int)  # Request to scroll to specific ID

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sprite: SpriteInfo | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.setMinimumWidth(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel("Sprite Details")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #E5E5E7;")
        layout.addWidget(title)

        # Preview
        preview_group = QGroupBox("Preview")
        preview_group.setStyleSheet(
            """
            QGroupBox {
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
        )
        preview_layout = QVBoxLayout(preview_group)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(64, 64)
        self.preview_label.setStyleSheet("background: #2A2A3E; border-radius: 4px;")
        preview_layout.addWidget(self.preview_label)

        layout.addWidget(preview_group)

        # Info form
        info_group = QGroupBox("Information")
        info_group.setStyleSheet(preview_group.styleSheet())
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(8)

        labels = ["Sprite ID:", "Width:", "Height:", "Layers:", "Frames:", "Status:"]
        self._info_values: list[QLabel] = []

        for i, label_text in enumerate(labels):
            label = QLabel(label_text)
            label.setStyleSheet("color: #A1A1AA;")
            info_layout.addWidget(label, i, 0)

            value = QLabel("—")
            value.setStyleSheet("color: #E5E5E7; font-weight: bold;")
            info_layout.addWidget(value, i, 1)
            self._info_values.append(value)

        layout.addWidget(info_group)

        # Go to ID
        goto_group = QGroupBox("Navigate")
        goto_group.setStyleSheet(preview_group.styleSheet())
        goto_layout = QHBoxLayout(goto_group)

        self.goto_spin = QSpinBox()
        self.goto_spin.setRange(0, 999999)
        self.goto_spin.setStyleSheet(
            """
            QSpinBox {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 4px;
            }
        """
        )
        goto_layout.addWidget(self.goto_spin)

        goto_btn = QPushButton("Go")
        goto_btn.setStyleSheet(
            """
            QPushButton {
                background: #8B5CF6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #7C3AED; }
        """
        )
        goto_btn.clicked.connect(lambda: self.go_to_id.emit(self.goto_spin.value()))
        goto_layout.addWidget(goto_btn)

        layout.addWidget(goto_group)

        # Spacer
        layout.addStretch()

    def set_sprite(self, sprite: SpriteInfo | None) -> None:
        """Update panel with sprite info."""
        self._sprite = sprite

        if sprite is None:
            self.preview_label.clear()
            for val in self._info_values:
                val.setText("—")
            return

        # Update preview
        if sprite.pixmap and not sprite.pixmap.isNull():
            scaled = sprite.pixmap.scaled(
                64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.preview_label.setPixmap(scaled)
        else:
            self.preview_label.setText("No preview")

        # Update info
        self._info_values[0].setText(str(sprite.sprite_id))
        self._info_values[1].setText(f"{sprite.width}px")
        self._info_values[2].setText(f"{sprite.height}px")
        self._info_values[3].setText(str(sprite.layers))
        self._info_values[4].setText(str(sprite.frames))
        self._info_values[5].setText("✓ Valid" if sprite.is_valid else "✗ Invalid")
        self._info_values[5].setStyleSheet(
            "color: #10B981; font-weight: bold;" if sprite.is_valid else "color: #EF4444; font-weight: bold;"
        )


class DatDebugDialog(QDialog):
    """Debug dialog for viewing loaded sprites.

    Displays all loaded sprites in a grid with search functionality.
    Useful for debugging sprite loading and verifying client data.

    Mirrors legacy C++ DatDebugView from source/dat_debug_view.cpp.

    Example:
        >>> dialog = DatDebugDialog(parent)
        >>> dialog.load_sprites(sprite_provider)
        >>> dialog.exec()
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sprite_provider: Callable[[int], QPixmap | None] | None = None

        self.setWindowTitle("Sprite Debug Viewer")
        self.setMinimumSize(800, 600)
        self.setModal(False)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("DAT/SPR Debug Viewer")
        header.setStyleSheet("font-size: 18px; font-weight: 700; color: #E5E5E7;")
        layout.addWidget(header)

        desc = QLabel(
            "View and inspect all loaded sprites from client data files. " "Use the search box to filter by sprite ID."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #A1A1AA;")
        layout.addWidget(desc)

        # Search bar
        search_layout = QHBoxLayout()

        search_label = QLabel("Search ID:")
        search_label.setStyleSheet("color: #E5E5E7;")
        search_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter sprite ID...")
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 4px;
                color: #E5E5E7;
                padding: 8px 12px;
            }
            QLineEdit:focus { border-color: #8B5CF6; }
        """
        )
        search_layout.addWidget(self.search_input, 1)

        # Stats label
        self.stats_label = QLabel("0 sprites loaded")
        self.stats_label.setStyleSheet("color: #A1A1AA;")
        search_layout.addWidget(self.stats_label)

        layout.addLayout(search_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sprite list
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)

        self.sprite_model = SpriteListModel()
        self.sprite_list = QListView()
        self.sprite_list.setModel(self.sprite_model)
        self.sprite_list.setItemDelegate(SpriteDelegate())
        self.sprite_list.setViewMode(QListView.ViewMode.IconMode)
        self.sprite_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.sprite_list.setSpacing(4)
        self.sprite_list.setUniformItemSizes(True)
        self.sprite_list.selectionModel().currentChanged.connect(self._on_selection_changed)
        self.sprite_list.setStyleSheet(
            """
            QListView {
                background: #1A1A2E;
                border: 1px solid #363650;
                border-radius: 4px;
            }
        """
        )
        list_layout.addWidget(self.sprite_list)

        splitter.addWidget(list_container)

        # Detail panel
        self.detail_panel = SpriteDetailPanel()
        self.detail_panel.go_to_id.connect(self._scroll_to_id)
        splitter.addWidget(self.detail_panel)

        # Splitter sizes
        splitter.setSizes([500, 250])

        layout.addWidget(splitter, 1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_sprites)
        refresh_btn.setStyleSheet(
            """
            QPushButton {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover { background: #363650; }
        """
        )
        btn_layout.addWidget(refresh_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background: #8B5CF6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background: #7C3AED; }
        """
        )
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _apply_style(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(
            """
            QDialog { background: #0F0F1A; }
            QGroupBox {
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
        """
        )

    def _on_search(self, text: str) -> None:
        """Handle search input change."""
        self.sprite_model.set_filter(text)
        self._update_stats()

    def _on_selection_changed(self, current: QModelIndex, previous: QModelIndex) -> None:
        """Handle sprite selection change."""
        sprite = self.sprite_model.get_sprite(current.row())
        self.detail_panel.set_sprite(sprite)

    def _scroll_to_id(self, sprite_id: int) -> None:
        """Scroll to a specific sprite ID."""
        # Clear filter first
        self.search_input.clear()

        # Find the sprite
        for i in range(self.sprite_model.rowCount()):
            sprite = self.sprite_model.get_sprite(i)
            if sprite and sprite.sprite_id == sprite_id:
                index = self.sprite_model.index(i)
                self.sprite_list.scrollTo(index)
                self.sprite_list.setCurrentIndex(index)
                break

    def _update_stats(self) -> None:
        """Update the stats label."""
        total = len(self.sprite_model._sprites)
        visible = self.sprite_model.rowCount()
        if visible == total:
            self.stats_label.setText(f"{total} sprites")
        else:
            self.stats_label.setText(f"Showing {visible} of {total} sprites")

    def _refresh_sprites(self) -> None:
        """Refresh the sprite list."""
        if self._sprite_provider:
            self.load_sprites(self._sprite_provider)

    def load_sprites(self, provider: Callable[[int], QPixmap | None], max_id: int = 50000) -> None:
        """Load sprites from a provider function.

        Args:
            provider: Function that takes sprite ID and returns QPixmap or None.
            max_id: Maximum sprite ID to scan.
        """
        self._sprite_provider = provider
        sprites: list[SpriteInfo] = []

        for sprite_id in range(1, max_id + 1):
            try:
                pixmap = provider(sprite_id)
                if pixmap is not None and not pixmap.isNull():
                    sprites.append(
                        SpriteInfo(
                            sprite_id=sprite_id,
                            width=pixmap.width(),
                            height=pixmap.height(),
                            is_valid=True,
                            pixmap=pixmap,
                        )
                    )
            except Exception:
                # Skip invalid sprites
                pass

        self.sprite_model.set_sprites(sprites)
        self._update_stats()

    def load_sprites_from_list(self, sprites: list[SpriteInfo]) -> None:
        """Load sprites from a pre-built list.

        Args:
            sprites: List of SpriteInfo objects.
        """
        self.sprite_model.set_sprites(sprites)
        self._update_stats()


def open_dat_debug_dialog(
    parent: QWidget | None = None, sprite_provider: Callable[[int], QPixmap | None] | None = None
) -> DatDebugDialog:
    """Factory function to create and show the dialog.

    Args:
        parent: Parent widget.
        sprite_provider: Optional function to provide sprite pixmaps.

    Returns:
        The dialog instance.
    """
    dialog = DatDebugDialog(parent)
    if sprite_provider:
        dialog.load_sprites(sprite_provider)
    dialog.show()
    return dialog


__all__ = ["DatDebugDialog", "SpriteInfo", "open_dat_debug_dialog"]
