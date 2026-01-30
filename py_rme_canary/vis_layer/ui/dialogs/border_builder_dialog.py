"""Border Builder Dialog.

UI for viewing and managing border rules for auto-connecting brushes.
Allows users to preview border patterns and configure custom rules.

Layer: vis_layer (OK to use PyQt6)
Reference: AutoBorderProcessor in logic_layer/borders/processor.py
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSplitter,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.logic_layer.brush_definitions import BrushDefinition


class BorderPreviewWidget(QFrame):
    """Visual preview of 3x3 neighbor grid with border pattern."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(150, 150)
        self.setMaximumSize(200, 200)
        self._mask = 0
        self._key = "SOLITARY"
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)

    def set_pattern(self, mask: int, key: str) -> None:
        """Set the pattern to display."""
        self._mask = mask
        self._key = key
        self.update()

    def paintEvent(self, event: Any) -> None:
        """Draw the 3x3 preview grid."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cell = min(w, h) // 3

        # Draw grid
        painter.setPen(QPen(QColor("#363650"), 1))
        for i in range(4):
            painter.drawLine(i * cell, 0, i * cell, 3 * cell)
            painter.drawLine(0, i * cell, 3 * cell, i * cell)

        # Neighbor positions (N=0, E=1, S=2, W=3)
        neighbors = [
            (1, 0),  # North
            (2, 1),  # East
            (1, 2),  # South
            (0, 1),  # West
        ]

        # Draw center tile (selected)
        painter.setBrush(QColor("#8B5CF6"))
        painter.drawRect(cell, cell, cell, cell)

        # Draw neighbors based on mask
        for bit, (gx, gy) in enumerate(neighbors):
            if self._mask & (1 << bit):
                painter.setBrush(QColor("#4CAF50"))
            else:
                painter.setBrush(QColor("#2A2A3E"))
            painter.drawRect(gx * cell, gy * cell, cell, cell)

        # Draw key label
        painter.setPen(QColor("#E5E5E7"))
        painter.drawText(
            0, 3 * cell + 5, 3 * cell, 20,
            Qt.AlignmentFlag.AlignCenter,
            self._key
        )
        painter.end()


class BorderPatternList(QFrame):
    """List of all 16 border patterns with their sprite IDs."""

    pattern_selected = pyqtSignal(int, str)  # mask, key

    # Mask to key mapping (from AutoBorderProcessor)
    MASK_TO_KEY: dict[int, str] = {
        0: "SOLITARY",
        1: "END_SOUTH",
        2: "END_WEST",
        3: "CORNER_NE",
        4: "END_NORTH",
        5: "VERTICAL",
        6: "CORNER_SE",
        7: "T_WEST",
        8: "END_EAST",
        9: "CORNER_NW",
        10: "HORIZONTAL",
        11: "T_SOUTH",
        12: "CORNER_SW",
        13: "T_EAST",
        14: "T_NORTH",
        15: "CROSS",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._brush_def: BrushDefinition | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Title
        title = QLabel("Border Patterns (16)")
        title.setStyleSheet("font-weight: bold; color: #E5E5E7;")
        layout.addWidget(title)

        # Pattern list
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: #1A1A2E;
                border: 1px solid #363650;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                color: #E5E5E7;
                border-bottom: 1px solid #2A2A3E;
            }
            QListWidget::item:selected {
                background: #8B5CF6;
            }
            QListWidget::item:hover {
                background: #2A2A3E;
            }
        """)
        self.list_widget.currentRowChanged.connect(self._on_row_changed)

        # Populate patterns
        for mask in range(16):
            key = self.MASK_TO_KEY[mask]
            item = QListWidgetItem(f"[{mask:04b}] {key}")
            item.setData(Qt.ItemDataRole.UserRole, mask)
            item.setData(Qt.ItemDataRole.UserRole + 1, key)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

    def _on_row_changed(self, row: int) -> None:
        """Emit signal when pattern selected."""
        item = self.list_widget.item(row)
        if item:
            mask = item.data(Qt.ItemDataRole.UserRole)
            key = item.data(Qt.ItemDataRole.UserRole + 1)
            self.pattern_selected.emit(mask, key)

    def set_brush(self, brush_def: BrushDefinition | None) -> None:
        """Update list with brush-specific sprite IDs."""
        self._brush_def = brush_def
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item is None:
                continue
            mask = item.data(Qt.ItemDataRole.UserRole)
            key = item.data(Qt.ItemDataRole.UserRole + 1)

            sprite_id = "—"
            if brush_def is not None:
                border_val = brush_def.get_border(key)
                if border_val:
                    sprite_id = str(border_val)

            item.setText(f"[{mask:04b}] {key}: {sprite_id}")


class BorderBuilderDialog(QDialog):
    """Dialog for viewing and managing border rules.

    Shows:
    - List of brushes with borders
    - 16 border patterns with sprite IDs
    - Visual pattern preview
    - Brush configuration
    """

    def __init__(self, brush_manager: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.brush_manager = brush_manager

        self.setWindowTitle("Border Builder")
        self.setMinimumSize(800, 600)
        self.setModal(False)

        self._setup_ui()
        self._apply_style()
        self._load_brushes()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("🧱 Border Builder")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #E5E5E7;")
        layout.addWidget(title)

        description = QLabel(
            "View and manage border patterns for auto-connecting brushes. "
            "Select a brush to see its border sprite mappings."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #A1A1AA; margin-bottom: 8px;")
        layout.addWidget(description)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - Brush list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        brush_label = QLabel("Brushes with Borders")
        brush_label.setStyleSheet("font-weight: bold; color: #E5E5E7;")
        left_layout.addWidget(brush_label)

        self.brush_list = QListWidget()
        self.brush_list.setStyleSheet("""
            QListWidget {
                background: #1A1A2E;
                border: 1px solid #363650;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                color: #E5E5E7;
            }
            QListWidget::item:selected {
                background: #8B5CF6;
            }
        """)
        self.brush_list.currentItemChanged.connect(self._on_brush_selected)
        left_layout.addWidget(self.brush_list)

        splitter.addWidget(left_panel)

        # Center panel - Pattern list
        self.pattern_list = BorderPatternList()
        self.pattern_list.pattern_selected.connect(self._on_pattern_selected)
        splitter.addWidget(self.pattern_list)

        # Right panel - Preview and info
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Preview
        preview_group = QGroupBox("Pattern Preview")
        preview_group.setStyleSheet("""
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
                left: 10px;
                padding: 0 5px;
            }
        """)
        preview_layout = QVBoxLayout(preview_group)

        self.preview_widget = BorderPreviewWidget()
        preview_layout.addWidget(self.preview_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        right_layout.addWidget(preview_group)

        # Brush info
        info_group = QGroupBox("Brush Info")
        info_group.setStyleSheet("""
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
                left: 10px;
                padding: 0 5px;
            }
        """)
        info_layout = QFormLayout(info_group)
        info_layout.setSpacing(8)

        self.info_name = QLabel("—")
        self.info_name.setStyleSheet("color: #E5E5E7;")
        info_layout.addRow("Name:", self.info_name)

        self.info_type = QLabel("—")
        self.info_type.setStyleSheet("color: #E5E5E7;")
        info_layout.addRow("Type:", self.info_type)

        self.info_server_id = QLabel("—")
        self.info_server_id.setStyleSheet("color: #E5E5E7;")
        info_layout.addRow("Server ID:", self.info_server_id)

        self.info_border_count = QLabel("—")
        self.info_border_count.setStyleSheet("color: #E5E5E7;")
        info_layout.addRow("Borders:", self.info_border_count)

        right_layout.addWidget(info_group)
        right_layout.addStretch()

        splitter.addWidget(right_panel)

        # Set splitter sizes
        splitter.setSizes([200, 300, 300])
        layout.addWidget(splitter)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_close)

        layout.addLayout(button_layout)

    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        self.setStyleSheet("""
            QDialog {
                background: #1E1E2E;
            }
            QLabel {
                color: #A1A1AA;
            }
            QPushButton {
                background: #363650;
                color: #E5E5E7;
                border: 1px solid #52525B;
                border-radius: 6px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background: #404060;
                border-color: #8B5CF6;
            }
        """)

    def _load_brushes(self) -> None:
        """Load brushes that have border definitions."""
        if self.brush_manager is None:
            return

        # Get all brushes with borders
        brushes = getattr(self.brush_manager, "all_brushes", None)
        if brushes is None:
            brushes = getattr(self.brush_manager, "_brushes", {})

        if callable(brushes):
            brushes = brushes()

        if isinstance(brushes, dict):
            brushes = brushes.values()

        for brush in brushes:
            if brush is None:
                continue
            borders = getattr(brush, "borders", None)
            if borders and len(borders) > 0:
                name = getattr(brush, "name", None) or str(getattr(brush, "server_id", "?"))
                brush_type = getattr(brush, "brush_type", "unknown")
                server_id = getattr(brush, "server_id", 0)

                item = QListWidgetItem(f"[{brush_type}] {name}")
                item.setData(Qt.ItemDataRole.UserRole, brush)
                self.brush_list.addItem(item)

        if self.brush_list.count() > 0:
            self.brush_list.setCurrentRow(0)

    def _on_brush_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        """Handle brush selection."""
        if current is None:
            self.pattern_list.set_brush(None)
            self._update_info(None)
            return

        brush = current.data(Qt.ItemDataRole.UserRole)
        self.pattern_list.set_brush(brush)
        self._update_info(brush)

    def _update_info(self, brush: Any) -> None:
        """Update brush info panel."""
        if brush is None:
            self.info_name.setText("—")
            self.info_type.setText("—")
            self.info_server_id.setText("—")
            self.info_border_count.setText("—")
            return

        name = getattr(brush, "name", None) or "Unnamed"
        brush_type = getattr(brush, "brush_type", "unknown")
        server_id = getattr(brush, "server_id", 0)
        borders = getattr(brush, "borders", {})

        self.info_name.setText(str(name))
        self.info_type.setText(str(brush_type))
        self.info_server_id.setText(str(server_id))
        self.info_border_count.setText(f"{len(borders)} defined")

    def _on_pattern_selected(self, mask: int, key: str) -> None:
        """Handle pattern selection in list."""
        self.preview_widget.set_pattern(mask, key)
