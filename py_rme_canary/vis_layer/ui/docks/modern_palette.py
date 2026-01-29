"""Modern Palette Widget with animated cards and immersive UX.

Replaces legacy list-based palette with card-based modern design.
Reference: palette_legacy_analysis.md / modern_ux_plan.md
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    pyqtProperty,
    pyqtSignal,
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


@dataclass(slots=True)
class BrushCardData:
    """Data for a brush card in the palette."""

    brush_id: int
    name: str
    brush_type: str = ""
    sprite_id: int | None = None
    category: str = ""


class AnimatedBrushCard(QFrame):
    """Single brush card with hover animations and selection state.

    Features:
    - Smooth hover lift effect (simulated via shadow)
    - Glow border on selection
    - Sprite preview (when available)
    - Click to select
    """

    clicked = pyqtSignal(int)  # Emits brush_id

    def __init__(
        self,
        data: BrushCardData,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.data = data
        self._selected = False
        self._hovered = False
        self._shadow_offset = 0.0

        self._setup_ui()
        self._setup_animations()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI elements."""
        self.setFixedSize(80, 90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Sprite preview area (placeholder for now)
        self.sprite_label = QLabel()
        self.sprite_label.setFixedSize(48, 48)
        self.sprite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sprite_label.setStyleSheet("""
            background: #1E1E2E;
            border-radius: 6px;
            color: #8B5CF6;
            font-size: 20px;
        """)
        # Show first letter of name as placeholder
        first_char = self.data.name[0].upper() if self.data.name else "?"
        self.sprite_label.setText(first_char)
        layout.addWidget(self.sprite_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Name label
        self.name_label = QLabel(self._truncate_name(self.data.name))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("""
            color: #E5E5E7;
            font-size: 10px;
            font-weight: 500;
        """)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)

        # Shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(0)
        self.shadow.setOffset(0, 0)
        self.shadow.setColor(QColor(139, 92, 246, 0))  # Purple, transparent
        self.setGraphicsEffect(self.shadow)

    def _truncate_name(self, name: str, max_len: int = 12) -> str:
        """Truncate name for display."""
        if len(name) <= max_len:
            return name
        return name[:max_len-2] + "…"

    def _setup_animations(self) -> None:
        """Setup hover and selection animations."""
        # Shadow animation for hover "lift" effect
        self._shadow_anim = QPropertyAnimation(self, b"shadowOffset")
        self._shadow_anim.setDuration(150)
        self._shadow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _apply_style(self) -> None:
        """Apply current style based on state."""
        if self._selected:
            border_color = "#8B5CF6"
            bg_color = "#363650"
            border_width = 2
        elif self._hovered:
            border_color = "#8B5CF6"
            bg_color = "#2A2A3E"
            border_width = 1
        else:
            border_color = "#363650"
            bg_color = "#2A2A3E"
            border_width = 1

        self.setStyleSheet(f"""
            AnimatedBrushCard {{
                background: {bg_color};
                border: {border_width}px solid {border_color};
                border-radius: 10px;
            }}
        """)

    @pyqtProperty(float)
    def shadowOffset(self) -> float:
        return self._shadow_offset

    @shadowOffset.setter
    def shadowOffset(self, value: float) -> None:
        self._shadow_offset = value
        self.shadow.setBlurRadius(value * 2)
        self.shadow.setOffset(0, value)
        alpha = int(min(255, value * 30))
        self.shadow.setColor(QColor(139, 92, 246, alpha))

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        self._selected = selected
        self._apply_style()

    def enterEvent(self, event: object) -> None:
        """Handle mouse enter."""
        self._hovered = True
        self._apply_style()

        # Animate shadow up
        self._shadow_anim.stop()
        self._shadow_anim.setStartValue(self._shadow_offset)
        self._shadow_anim.setEndValue(8.0)
        self._shadow_anim.start()

        super().enterEvent(event)

    def leaveEvent(self, event: object) -> None:
        """Handle mouse leave."""
        self._hovered = False
        self._apply_style()

        # Animate shadow down
        self._shadow_anim.stop()
        self._shadow_anim.setStartValue(self._shadow_offset)
        self._shadow_anim.setEndValue(0.0)
        self._shadow_anim.start()

        super().leaveEvent(event)

    def mousePressEvent(self, event: object) -> None:
        """Handle click."""
        if hasattr(event, 'button') and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.data.brush_id)
        super().mousePressEvent(event)


class ModernPaletteWidget(QWidget):
    """Modern card-based palette widget.

    Features:
    - Grid of animated brush cards
    - Live search filtering
    - Category collapse/expand
    - Recent brushes section
    - Smooth animations
    """

    brush_selected = pyqtSignal(int)  # Emits brush_id

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._cards: list[AnimatedBrushCard] = []
        self._selected_brush_id: int | None = None
        self._all_brushes: list[BrushCardData] = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search brushes...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 8px;
                padding: 8px 12px;
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
        self.search_bar.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_bar)

        # Scroll area for cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
        """)

        # Cards container
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)

    def set_brushes(self, brushes: list[BrushCardData]) -> None:
        """Set the list of brushes to display.

        Args:
            brushes: List of BrushCardData objects
        """
        self._all_brushes = brushes
        self._rebuild_cards()

    def _rebuild_cards(self, filter_text: str = "") -> None:
        """Rebuild the card grid with optional filtering."""
        # Clear existing cards
        for card in self._cards:
            card.deleteLater()
        self._cards.clear()

        # Clear layout
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Filter brushes
        filter_lower = filter_text.lower()
        filtered = [
            b for b in self._all_brushes
            if not filter_text or filter_lower in b.name.lower() or
               filter_lower in str(b.brush_id)
        ]

        # Create cards in grid (4 columns)
        cols = 4
        for i, brush_data in enumerate(filtered):
            card = AnimatedBrushCard(brush_data)
            card.clicked.connect(self._on_card_clicked)

            row = i // cols
            col = i % cols
            self.cards_layout.addWidget(card, row, col)
            self._cards.append(card)

            # Restore selection if applicable
            if brush_data.brush_id == self._selected_brush_id:
                card.set_selected(True)

    def _on_search_changed(self, text: str) -> None:
        """Handle search text change."""
        self._rebuild_cards(text)

    def _on_card_clicked(self, brush_id: int) -> None:
        """Handle card click."""
        # Update selection
        self._selected_brush_id = brush_id

        for card in self._cards:
            card.set_selected(card.data.brush_id == brush_id)

        # Emit signal
        self.brush_selected.emit(brush_id)

    def select_brush(self, brush_id: int) -> None:
        """Programmatically select a brush.

        Args:
            brush_id: ID of brush to select
        """
        self._selected_brush_id = brush_id

        for card in self._cards:
            card.set_selected(card.data.brush_id == brush_id)


class SectionHeader(QWidget):
    """Collapsible section header for palette categories."""

    toggled = pyqtSignal(bool)  # Emits expanded state

    def __init__(
        self,
        title: str,
        count: int = 0,
        expanded: bool = True,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._expanded = expanded

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Expand/collapse indicator
        self.arrow = QLabel("▼" if expanded else "▶")
        self.arrow.setStyleSheet("color: #A1A1AA; font-size: 10px;")
        layout.addWidget(self.arrow)

        # Title
        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("""
            color: #E5E5E7;
            font-size: 13px;
            font-weight: 600;
        """)
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Count badge
        if count > 0:
            self.count_label = QLabel(str(count))
            self.count_label.setStyleSheet("""
                background: #363650;
                color: #A1A1AA;
                font-size: 10px;
                padding: 2px 6px;
                border-radius: 8px;
            """)
            layout.addWidget(self.count_label)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            SectionHeader {
                background: #2A2A3E;
                border-radius: 6px;
            }
            SectionHeader:hover {
                background: #363650;
            }
        """)

    def mousePressEvent(self, event: object) -> None:
        """Toggle on click."""
        self._expanded = not self._expanded
        self.arrow.setText("▼" if self._expanded else "▶")
        self.toggled.emit(self._expanded)
        super().mousePressEvent(event)
