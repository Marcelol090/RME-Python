"""Brush Toolbar & Tool Selector — Antigravity Design.

Quick access toolbar for brush settings:
- Brush size buttons with glow states
- Shape toggle with custom painted icons
- Automagic toggle
- Tool selector with painted icons
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QRectF, QSize, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.icons import tool_icons
from py_rme_canary.vis_layer.ui.resources.icon_pack import load_icon
from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Painted icon helpers (no Unicode, no emoji, no external files)
# ---------------------------------------------------------------------------

def _painted_square_icon(size: int = 20, checked: bool = False) -> QIcon:
    px = QPixmap(size, size)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    color = QColor(255, 255, 255, 200) if checked else QColor(161, 161, 170, 160)
    fill = QColor(255, 255, 255, 30) if checked else QColor(161, 161, 170, 15)
    p.setPen(QPen(color, 1.5))
    p.setBrush(QBrush(fill))
    m = size * 0.2
    p.drawRoundedRect(QRectF(m, m, size - 2 * m, size - 2 * m), 2.0, 2.0)
    p.end()
    return QIcon(px)


def _painted_circle_icon(size: int = 20, checked: bool = False) -> QIcon:
    px = QPixmap(size, size)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    color = QColor(255, 255, 255, 200) if checked else QColor(161, 161, 170, 160)
    fill = QColor(255, 255, 255, 30) if checked else QColor(161, 161, 170, 15)
    p.setPen(QPen(color, 1.5))
    p.setBrush(QBrush(fill))
    m = size * 0.2
    p.drawEllipse(QRectF(m, m, size - 2 * m, size - 2 * m))
    p.end()
    return QIcon(px)


def _painted_tool_icon(letter: str, size: int = 22) -> QIcon:
    """Fallback: letter inside a rounded square."""
    px = QPixmap(size, size)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(161, 161, 170, 140), 1.0))
    p.setBrush(QBrush(QColor(54, 54, 80, 60)))
    p.drawRoundedRect(QRectF(2, 2, size - 4, size - 4), 5, 5)
    from PyQt6.QtGui import QFont
    font = QFont("Segoe UI", max(8, size // 3))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QColor(200, 200, 210, 220))
    from PyQt6.QtCore import Qt
    p.drawText(0, 0, size, size, Qt.AlignmentFlag.AlignCenter, letter)
    p.end()
    return QIcon(px)


class BrushToolbar(QFrame):
    """Toolbar for brush settings — Antigravity style.

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
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(6)

        # Size buttons
        size_group = QButtonGroup(self)
        size_group.setExclusive(True)

        for size in [1, 3, 5, 7, 9]:
            btn = QPushButton(str(size))
            btn.setFixedSize(30, 30)
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
        sep1.setFixedWidth(1)
        sep1.setStyleSheet("background: rgba(255, 255, 255, 0.06);")
        layout.addWidget(sep1)

        # Shape toggle — custom painted icons
        self.btn_square = QPushButton()
        self.btn_square.setFixedSize(32, 32)
        self.btn_square.setCheckable(True)
        self.btn_square.setChecked(True)
        self.btn_square.setIcon(_painted_square_icon(18, True))
        self.btn_square.setIconSize(QSize(18, 18))
        self.btn_square.setToolTip("Square brush (Q)")
        self.btn_square.clicked.connect(lambda: self._set_shape("square"))
        layout.addWidget(self.btn_square)

        self.btn_circle = QPushButton()
        self.btn_circle.setFixedSize(32, 32)
        self.btn_circle.setCheckable(True)
        self.btn_circle.setIcon(_painted_circle_icon(18, False))
        self.btn_circle.setIconSize(QSize(18, 18))
        self.btn_circle.setToolTip("Circle brush (Q)")
        self.btn_circle.clicked.connect(lambda: self._set_shape("circle"))
        layout.addWidget(self.btn_circle)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFixedWidth(1)
        sep2.setStyleSheet("background: rgba(255, 255, 255, 0.06);")
        layout.addWidget(sep2)

        # Automagic toggle
        self.btn_automagic = QPushButton("Auto")
        self.btn_automagic.setFixedSize(44, 30)
        self.btn_automagic.setCheckable(True)
        self.btn_automagic.setChecked(True)
        self.btn_automagic.setIcon(load_icon("tool_automagic"))
        self.btn_automagic.setToolTip("Automagic borders (A)")
        self.btn_automagic.clicked.connect(self._on_automagic_clicked)
        layout.addWidget(self.btn_automagic)

        layout.addStretch()

    def _apply_style(self) -> None:
        """Apply toolbar style from active theme tokens."""
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]
        self.setStyleSheet(
            f"""
            BrushToolbar {{
                background: {c["surface"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["lg"]}px;
            }}

            QPushButton {{
                background: {c["surface"]["secondary"]};
                color: {c["text"]["secondary"]};
                border: 1px solid transparent;
                border-radius: {r["md"]}px;
                font-size: 12px;
                font-weight: 700;
            }}

            QPushButton:hover {{
                background: {c["state"]["hover"]};
                border-color: {c["border"]["interactive"]};
                color: {c["text"]["primary"]};
            }}

            QPushButton:checked {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {c["state"]["active"]}, stop:1 {c["brand"]["primary"]});
                border: 1px solid {c["border"]["interactive"]};
                color: {c["text"]["primary"]};
            }}
        """
        )

    def refresh_theme(self) -> None:
        self._apply_style()

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
        # Update icons to reflect checked state
        self.btn_square.setIcon(_painted_square_icon(18, shape == "square"))
        self.btn_circle.setIcon(_painted_circle_icon(18, shape == "circle"))
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
        self.btn_square.setIcon(_painted_square_icon(18, shape == "square"))
        self.btn_circle.setIcon(_painted_circle_icon(18, shape == "circle"))

    def set_automagic(self, enabled: bool) -> None:
        """Set automagic state."""
        self._automagic = enabled
        self.btn_automagic.setChecked(enabled)

    def toggle_shape(self) -> None:
        """Toggle between square and circle."""
        new_shape = "circle" if self._shape == "square" else "square"
        self._set_shape(new_shape)


class ToolSelector(QFrame):
    """Tool selection bar — Antigravity style.

    Signals:
        tool_changed: Emits tool name
    """

    tool_changed = pyqtSignal(str)

    TOOLS = [
        ("pointer", "tool_pointer", "Select/Move (V)"),
        ("pencil", "tool_pencil", "Draw (B)"),
        ("eraser", "tool_eraser", "Erase (E)"),
        ("fill", "tool_fill", "Fill (G)"),
        ("select", "tool_select", "Rectangle Select (M)"),
        ("picker", "tool_picker", "Color Picker (I)"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_tool = "pencil"

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(4)

        self._tool_buttons = {}
        _fallbacks = tool_icons(20)

        for tool_id, icon_name, tooltip in self.TOOLS:
            btn = QPushButton()
            btn.setFixedSize(38, 38)
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setProperty("toolId", tool_id)
            icon = load_icon(icon_name)
            if not icon.isNull():
                btn.setIcon(icon)
                btn.setIconSize(QSize(20, 20))
            elif tool_id in _fallbacks:
                btn.setIcon(_fallbacks[tool_id])
                btn.setIconSize(QSize(20, 20))
            else:
                # Last resort: painted letter
                fallback = _painted_tool_icon(tool_id[:1].upper(), 22)
                btn.setIcon(fallback)
                btn.setIconSize(QSize(20, 20))
            btn.clicked.connect(lambda checked, t=tool_id: self._on_tool_clicked(t))
            layout.addWidget(btn)
            self._tool_buttons[tool_id] = btn

            if tool_id == "pencil":
                btn.setChecked(True)

        layout.addStretch()

    def _apply_style(self) -> None:
        """Antigravity styling."""
        self.setStyleSheet(
            """
            ToolSelector {
                background: rgba(16, 16, 24, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 14px;
            }

            QPushButton {
                background: transparent;
                color: rgba(161, 161, 170, 0.8);
                border: 1px solid transparent;
                border-radius: 10px;
                font-size: 16px;
            }

            QPushButton:hover {
                background: rgba(139, 92, 246, 0.1);
                border-color: rgba(139, 92, 246, 0.15);
            }

            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(139, 92, 246, 0.3), stop:1 rgba(124, 58, 237, 0.25));
                border: 1px solid rgba(139, 92, 246, 0.45);
            }
        """
        )

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
