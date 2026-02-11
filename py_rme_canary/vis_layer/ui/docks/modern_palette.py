"""Modern palette primitives used by the palette dock."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget


@dataclass(slots=True)
class BrushCardData:
    """Lightweight DTO for a brush card entry."""

    brush_id: int
    name: str
    brush_type: str
    sprite_id: int | None = None


def _make_fallback_icon(text: str, size: int) -> QPixmap:
    """Create a colored placeholder icon with the first 2 chars of the item name."""
    px = QPixmap(size, size)
    px.fill(QColor(0, 0, 0, 0))

    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Antigravity palette: Deep glassy backgrounds with subtle borders
    hue = abs(hash(text)) % 360
    # Use cooler, deeper colors for the background
    bg = QColor.fromHsl(hue, 60, 25, 200)
    # Bright border
    border = QColor.fromHsl(hue, 80, 60, 180)

    # Rounded background
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(bg)
    painter.drawRoundedRect(1, 1, size - 2, size - 2, 6.0, 6.0)

    # Border
    from PyQt6.QtGui import QPen

    painter.setPen(QPen(border, 1.0))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(1, 1, size - 2, size - 2, 6.0, 6.0)

    # Text label (first 2 chars)
    label = text[:2].upper() if text else "?"
    # Use Segoe UI or Inter if available, fallback to sans-serif
    font = QFont("Segoe UI", max(8, size // 3))
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(255, 255, 255, 230))
    painter.drawText(0, 0, size, size, Qt.AlignmentFlag.AlignCenter, label)

    painter.end()
    return px


class ModernPaletteWidget(QWidget):
    """Brush list widget with icon cards used inside tabs — Antigravity style."""

    brush_selected = pyqtSignal(int)

    def __init__(
        self,
        *,
        sprite_lookup: Callable[[int, int], QPixmap | None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._sprite_lookup = sprite_lookup
        self._icon_px = 36
        self._entries: list[BrushCardData] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self.list_widget = QListWidget(self)
        self.list_widget.setObjectName("AssetGrid")
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setUniformItemSizes(True)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setWordWrap(True)
        self.list_widget.setSpacing(6)
        self.list_widget.setIconSize(QSize(self._icon_px, self._icon_px))
        self.list_widget.setGridSize(QSize(self._icon_px + 24, self._icon_px + 28))
        self.list_widget.itemClicked.connect(self._emit_selected)
        self.list_widget.itemActivated.connect(self._emit_selected)
        # Enhanced Antigravity styling for the list items
        self.list_widget.setStyleSheet(
            """
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: rgba(19, 19, 29, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 8px;
                padding: 4px;
                color: rgba(229, 229, 231, 0.8);
            }
            QListWidget::item:hover {
                background: rgba(139, 92, 246, 0.12);
                border-color: rgba(139, 92, 246, 0.25);
                color: #ffffff;
            }
            QListWidget::item:selected {
                background: rgba(139, 92, 246, 0.25);
                border-color: rgba(139, 92, 246, 0.5);
                color: #ffffff;
            }
        """
        )
        layout.addWidget(self.list_widget)

        # Empty state label
        self._empty_label = QListWidgetItem("No items to display")
        self._empty_label.setFlags(Qt.ItemFlag.NoItemFlags)

    def set_icon_size(self, icon_px: int) -> None:
        """Set list icon size and rerender current entries."""
        new_px = max(12, min(64, int(icon_px)))
        if new_px == int(self._icon_px):
            return
        self._icon_px = int(new_px)
        self.list_widget.setIconSize(QSize(self._icon_px, self._icon_px))
        self.list_widget.setGridSize(QSize(self._icon_px + 24, self._icon_px + 28))
        self._render_entries(self._entries)

    def set_brushes(self, brushes: list[BrushCardData]) -> None:
        """Replace displayed brushes, preserving given ordering."""
        self._entries = list(brushes)
        self._render_entries(self._entries)

    def _render_entries(self, brushes: list[BrushCardData]) -> None:
        self.list_widget.clear()

        if not brushes:
            empty = QListWidgetItem("  No items found")
            empty.setFlags(Qt.ItemFlag.NoItemFlags)
            empty.setForeground(QColor(136, 136, 160))
            self.list_widget.addItem(empty)
            return

        for entry in brushes:
            item = QListWidgetItem(str(entry.name))
            item.setData(Qt.ItemDataRole.UserRole, int(entry.brush_id))
            tooltip = f"{entry.name}\nType: {entry.brush_type}\nID: {int(entry.brush_id)}"
            if entry.sprite_id is not None:
                tooltip += f"\nSprite: {int(entry.sprite_id)}"
            item.setToolTip(tooltip)

            # Try sprite lookup, fall back to generated placeholder icon
            icon_set = False
            if self._sprite_lookup is not None:
                sid = int(entry.sprite_id or 0)
                if sid > 0:
                    try:
                        pixmap = self._sprite_lookup(sid, int(self._icon_px))
                    except Exception:
                        pixmap = None
                    if pixmap is not None and not pixmap.isNull():
                        item.setIcon(QIcon(pixmap))
                        icon_set = True

            if not icon_set:
                # Generate a colored fallback icon
                fallback = _make_fallback_icon(entry.name, int(self._icon_px))
                item.setIcon(QIcon(fallback))

            self.list_widget.addItem(item)

    def _emit_selected(self, item: QListWidgetItem) -> None:
        value = item.data(Qt.ItemDataRole.UserRole)
        if value is None:
            return
        self.brush_selected.emit(int(value))
