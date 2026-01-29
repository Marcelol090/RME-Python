"""Brush Toolbar Widget.

Quick access toolbar for brush settings:
- Brush size buttons
- Shape toggle
- Automagic toggle
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


class BrushToolbar(QFrame):
    """Toolbar for brush settings.

    Signals:
        size_changed: Emits new brush size (1-11)
        shape_changed: Emits 'square' or 'circle'
        automagic_changed: Emits True/False
    """

    size_changed = pyqtSignal(int)
    shape_changed = pyqtSignal(str)
    automagic_changed = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._size = 1
        self._shape = "square"
        self._automagic = True

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Size buttons
        size_group = QButtonGroup(self)
        size_group.setExclusive(True)

        for size in [1, 3, 5, 7, 9]:
            btn = QPushButton(str(size))
            btn.setFixedSize(28, 28)
            btn.setCheckable(True)
            btn.setToolTip(f"Brush size {size}×{size}")
            btn.setProperty("brushSize", size)
            btn.clicked.connect(lambda checked, s=size: self._on_size_clicked(s))
            size_group.addButton(btn)
            layout.addWidget(btn)

            if size == 1:
                btn.setChecked(True)

        self._size_buttons = size_group

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("background: #363650;")
        layout.addWidget(sep1)

        # Shape toggle
        self.btn_square = QPushButton("▢")
        self.btn_square.setFixedSize(28, 28)
        self.btn_square.setCheckable(True)
        self.btn_square.setChecked(True)
        self.btn_square.setToolTip("Square brush (Q)")
        self.btn_square.clicked.connect(lambda: self._set_shape("square"))
        layout.addWidget(self.btn_square)

        self.btn_circle = QPushButton("○")
        self.btn_circle.setFixedSize(28, 28)
        self.btn_circle.setCheckable(True)
        self.btn_circle.setToolTip("Circle brush (Q)")
        self.btn_circle.clicked.connect(lambda: self._set_shape("circle"))
        layout.addWidget(self.btn_circle)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setStyleSheet("background: #363650;")
        layout.addWidget(sep2)

        # Automagic toggle
        self.btn_automagic = QPushButton("✨")
        self.btn_automagic.setFixedSize(32, 28)
        self.btn_automagic.setCheckable(True)
        self.btn_automagic.setChecked(True)
        self.btn_automagic.setToolTip("Automagic borders (A)")
        self.btn_automagic.clicked.connect(self._on_automagic_clicked)
        layout.addWidget(self.btn_automagic)

        layout.addStretch()

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet("""
            BrushToolbar {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 8px;
            }

            QPushButton {
                background: #363650;
                color: #A1A1AA;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #404060;
                color: #E5E5E7;
            }

            QPushButton:checked {
                background: #8B5CF6;
                color: white;
            }
        """)

    def _on_size_clicked(self, size: int) -> None:
        """Handle size button click."""
        if size != self._size:
            self._size = size
            self.size_changed.emit(size)

    def _set_shape(self, shape: str) -> None:
        """Set brush shape."""
        self._shape = shape
        self.btn_square.setChecked(shape == "square")
        self.btn_circle.setChecked(shape == "circle")
        self.shape_changed.emit(shape)

    def _on_automagic_clicked(self) -> None:
        """Handle automagic toggle."""
        self._automagic = self.btn_automagic.isChecked()
        self.automagic_changed.emit(self._automagic)

    def set_size(self, size: int) -> None:
        """Set current brush size."""
        self._size = size
        for btn in self._size_buttons.buttons():
            if btn.property("brushSize") == size:
                btn.setChecked(True)
                break

    def set_shape(self, shape: str) -> None:
        """Set current shape."""
        self._shape = shape
        self.btn_square.setChecked(shape == "square")
        self.btn_circle.setChecked(shape == "circle")

    def set_automagic(self, enabled: bool) -> None:
        """Set automagic state."""
        self._automagic = enabled
        self.btn_automagic.setChecked(enabled)

    def toggle_shape(self) -> None:
        """Toggle between square and circle."""
        new_shape = "circle" if self._shape == "square" else "square"
        self._set_shape(new_shape)


class ToolSelector(QFrame):
    """Tool selection bar.

    Signals:
        tool_changed: Emits tool name
    """

    tool_changed = pyqtSignal(str)

    TOOLS = [
        ("pointer", "👆", "Select/Move (V)"),
        ("pencil", "✏️", "Draw (B)"),
        ("eraser", "🧹", "Erase (E)"),
        ("fill", "🪣", "Fill (G)"),
        ("select", "🔲", "Rectangle Select (M)"),
        ("picker", "💉", "Color Picker (I)"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_tool = "pencil"

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(4)

        self._tool_buttons = {}

        for tool_id, icon, tooltip in self.TOOLS:
            btn = QPushButton(icon)
            btn.setFixedSize(36, 36)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setProperty("toolId", tool_id)
            btn.clicked.connect(lambda checked, t=tool_id: self._on_tool_clicked(t))
            layout.addWidget(btn)
            self._tool_buttons[tool_id] = btn

            if tool_id == "pencil":
                btn.setChecked(True)

        layout.addStretch()

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet("""
            ToolSelector {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 10px;
            }

            QPushButton {
                background: transparent;
                color: #A1A1AA;
                border: none;
                border-radius: 8px;
                font-size: 18px;
            }

            QPushButton:hover {
                background: #363650;
            }

            QPushbutton:checked {
                background: #8B5CF6;
            }
        """)

    def _on_tool_clicked(self, tool_id: str) -> None:
        """Handle tool click."""
        for tid, btn in self._tool_buttons.items():
            btn.setChecked(tid == tool_id)

        if tool_id != self._current_tool:
            self._current_tool = tool_id
            self.tool_changed.emit(tool_id)

    def set_tool(self, tool_id: str) -> None:
        """Set current tool."""
        if tool_id in self._tool_buttons:
            self._on_tool_clicked(tool_id)
