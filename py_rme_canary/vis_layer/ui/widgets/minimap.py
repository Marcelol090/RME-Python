"""Minimap and Floor Indicator widgets.

Provides:
- Floor indicator with quick navigation
- Minimap preview
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


class FloorIndicator(QFrame):
    """Floor indicator with quick navigation buttons.

    Shows current floor with up/down buttons and direct floor selection.

    Signals:
        floor_changed: Emits new floor (0-15)
    """

    floor_changed = pyqtSignal(int)

    FLOOR_NAMES = {
        0: "+7 (Highest)",
        1: "+6",
        2: "+5",
        3: "+4",
        4: "+3",
        5: "+2",
        6: "+1",
        7: "Ground",
        8: "-1",
        9: "-2",
        10: "-3",
        11: "-4",
        12: "-5",
        13: "-6",
        14: "-7",
        15: "-8 (Deepest)",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._floor = 7  # Ground level
        self._min_floor = 0
        self._max_floor = 15

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Up button
        self.btn_up = QPushButton("▲")
        self.btn_up.setFixedSize(40, 28)
        self.btn_up.setToolTip("Floor up (PgUp)")
        self.btn_up.clicked.connect(self._floor_up)
        layout.addWidget(self.btn_up, alignment=Qt.AlignmentFlag.AlignCenter)

        # Floor display
        self.floor_display = QLabel("7")
        self.floor_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.floor_display.setFixedSize(40, 36)
        self.floor_display.setStyleSheet("""
            background: #1E1E2E;
            border: 2px solid #8B5CF6;
            border-radius: 8px;
            color: #E5E5E7;
            font-size: 16px;
            font-weight: 700;
        """)
        layout.addWidget(self.floor_display, alignment=Qt.AlignmentFlag.AlignCenter)

        # Floor name
        self.floor_name = QLabel("Ground")
        self.floor_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.floor_name.setStyleSheet("color: #A1A1AA; font-size: 9px;")
        layout.addWidget(self.floor_name)

        # Down button
        self.btn_down = QPushButton("▼")
        self.btn_down.setFixedSize(40, 28)
        self.btn_down.setToolTip("Floor down (PgDn)")
        self.btn_down.clicked.connect(self._floor_down)
        layout.addWidget(self.btn_down, alignment=Qt.AlignmentFlag.AlignCenter)

        self._update_display()

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet("""
            FloorIndicator {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 10px;
            }
            
            QPushButton {
                background: #363650;
                color: #A1A1AA;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 700;
            }
            
            QPushButton:hover {
                background: #8B5CF6;
                color: white;
            }
            
            QPushButton:disabled {
                background: #2A2A3E;
                color: #52525B;
            }
        """)

    def _update_display(self) -> None:
        """Update the floor display."""
        self.floor_display.setText(str(self._floor))

        name = self.FLOOR_NAMES.get(self._floor, f"Floor {self._floor}")
        # Truncate for display
        if len(name) > 10:
            name = name.split(" ")[0]
        self.floor_name.setText(name)

        # Update button states
        self.btn_up.setEnabled(self._floor > self._min_floor)
        self.btn_down.setEnabled(self._floor < self._max_floor)

    def _floor_up(self) -> None:
        """Go one floor up."""
        if self._floor > self._min_floor:
            self._floor -= 1
            self._update_display()
            self.floor_changed.emit(self._floor)

    def _floor_down(self) -> None:
        """Go one floor down."""
        if self._floor < self._max_floor:
            self._floor += 1
            self._update_display()
            self.floor_changed.emit(self._floor)

    def set_floor(self, floor: int) -> None:
        """Set the current floor."""
        floor = max(self._min_floor, min(self._max_floor, floor))
        if floor != self._floor:
            self._floor = floor
            self._update_display()

    def get_floor(self) -> int:
        """Get current floor."""
        return self._floor

    def set_floor_range(self, min_floor: int, max_floor: int) -> None:
        """Set allowed floor range."""
        self._min_floor = min_floor
        self._max_floor = max_floor
        self._update_display()


class MinimapWidget(QFrame):
    """Minimap showing overview of the map.

    Shows:
    - Map overview at current floor
    - Viewport rectangle
    - Click to navigate

    Signals:
        position_clicked: Emits (x, y) when clicked
    """

    position_clicked = pyqtSignal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._map_width = 256
        self._map_height = 256
        self._viewport_x = 0
        self._viewport_y = 0
        self._viewport_width = 32
        self._viewport_height = 24
        self._tiles_data: dict[tuple[int, int], int] = {}  # (x, y) -> color hint

        self.setMinimumSize(120, 120)
        self.setMaximumSize(200, 200)

        self.setCursor(Qt.CursorShape.CrossCursor)

        self._apply_style()

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet("""
            MinimapWidget {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 8px;
            }
        """)

    def set_map_size(self, width: int, height: int) -> None:
        """Set the map dimensions."""
        self._map_width = max(1, width)
        self._map_height = max(1, height)
        self.update()

    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        """Set the viewport rectangle."""
        self._viewport_x = x
        self._viewport_y = y
        self._viewport_width = width
        self._viewport_height = height
        self.update()

    def set_tile_hints(self, hints: dict[tuple[int, int], int]) -> None:
        """Set tile color hints for rendering.

        Args:
            hints: Dict mapping (x, y) to color value (0-3 for terrain type)
        """
        self._tiles_data = hints
        self.update()

    def paintEvent(self, event: object) -> None:
        """Paint the minimap."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width() - 4
        h = self.height() - 4
        offset_x = 2
        offset_y = 2

        # Calculate scale
        scale_x = w / self._map_width
        scale_y = h / self._map_height

        # Draw tiles (simplified - just colored dots)
        colors = [
            QColor(34, 139, 34),  # Ground - green
            QColor(0, 105, 148),  # Water - blue
            QColor(139, 69, 19),  # Sand - brown
            QColor(80, 80, 80),  # Stone - gray
        ]

        for (x, y), hint in self._tiles_data.items():
            px = offset_x + int(x * scale_x)
            py = offset_y + int(y * scale_y)
            color = colors[hint % len(colors)]
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRect(px, py, max(1, int(scale_x)), max(1, int(scale_y)))

        # Draw viewport rectangle
        vp_x = offset_x + int(self._viewport_x * scale_x)
        vp_y = offset_y + int(self._viewport_y * scale_y)
        vp_w = int(self._viewport_width * scale_x)
        vp_h = int(self._viewport_height * scale_y)

        painter.setPen(QPen(QColor(139, 92, 246), 2))  # Purple
        painter.setBrush(QBrush(QColor(139, 92, 246, 40)))  # Semi-transparent
        painter.drawRect(vp_x, vp_y, vp_w, vp_h)

    def mousePressEvent(self, event: object) -> None:
        """Handle click to navigate."""
        if hasattr(event, "position"):
            pos = event.position()

            w = self.width() - 4
            h = self.height() - 4

            # Convert to map coordinates
            x = int((pos.x() - 2) / w * self._map_width)
            y = int((pos.y() - 2) / h * self._map_height)

            x = max(0, min(self._map_width - 1, x))
            y = max(0, min(self._map_height - 1, y))

            self.position_clicked.emit(x, y)

        super().mousePressEvent(event)


class FloorMinimapPanel(QFrame):
    """Combined panel with floor indicator and minimap.

    Signals:
        floor_changed: Emits new floor
        position_clicked: Emits (x, y) from minimap click
    """

    floor_changed = pyqtSignal(int)
    position_clicked = pyqtSignal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Title
        title = QLabel("🗺️ Navigation")
        title.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: #A1A1AA;
        """)
        layout.addWidget(title)

        # Floor indicator
        self.floor_indicator = FloorIndicator()
        self.floor_indicator.floor_changed.connect(self.floor_changed.emit)
        layout.addWidget(self.floor_indicator, alignment=Qt.AlignmentFlag.AlignCenter)

        # Minimap
        self.minimap = MinimapWidget()
        self.minimap.position_clicked.connect(self.position_clicked.emit)
        layout.addWidget(self.minimap)

        layout.addStretch()

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet("""
            FloorMinimapPanel {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 10px;
            }
        """)

    def set_floor(self, floor: int) -> None:
        """Set current floor."""
        self.floor_indicator.set_floor(floor)

    def set_map_size(self, width: int, height: int) -> None:
        """Set map size for minimap."""
        self.minimap.set_map_size(width, height)

    def set_viewport(self, x: int, y: int, width: int, height: int) -> None:
        """Set viewport for minimap."""
        self.minimap.set_viewport(x, y, width, height)
