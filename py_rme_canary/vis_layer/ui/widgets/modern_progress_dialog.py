"""
Modern Progress Dialog for Map Loading.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QGraphicsDropShadowEffect,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager
from py_rme_canary.vis_layer.ui.resources.icon_pack import load_icon


class CircularProgressBar(QWidget):
    """Circular progress bar with center text."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(120, 120)
        self._value = 0
        self._maximum = 100
        self._color_primary = QColor("#7C3AED")
        self._color_secondary = QColor("#2D2D2D")
        self._text_color = QColor("#FFFFFF")

    def setValue(self, value: int) -> None:
        self._value = value
        self.update()

    def setMaximum(self, value: int) -> None:
        self._maximum = value
        self.update()

    def setColors(self, primary: str, secondary: str, text: str) -> None:
        self._color_primary = QColor(primary)
        self._color_secondary = QColor(secondary)
        self._text_color = QColor(text)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(10, 10, -10, -10)

        # Background Circle
        pen_bg = QPen(self._color_secondary)
        pen_bg.setWidth(8)
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawEllipse(rect)

        # Progress Arc
        if self._maximum > 0:
            angle = int(360 * 16 * (self._value / self._maximum))
            pen_prog = QPen(self._color_primary)
            pen_prog.setWidth(8)
            pen_prog.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen_prog)
            # drawArc uses 1/16th of a degree
            # Start at 90 degrees (top), go negative (clockwise)
            painter.drawArc(rect, 90 * 16, -angle)

        # Percentage Text
        painter.setPen(self._text_color)
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)

        percentage = int((self._value / self._maximum) * 100) if self._maximum > 0 else 0
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{percentage}%")


class ModernProgressDialog(QDialog):
    """
    A modern, frameless progress dialog with glassmorphism styling.
    Replaces the native QProgressDialog for a premium feel.
    """

    def __init__(
        self,
        title: str = "Loading...",
        label_text: str = "Please wait...",
        minimum: int = 0,
        maximum: int = 100,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumWidth(400)

        self._canceled = False
        self._minimum = minimum
        self._maximum = maximum
        self._value = minimum

        self._setup_ui(title, label_text)
        self._apply_style()

    def _setup_ui(self, title: str, label_text: str) -> None:
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Glass container
        self.container = QWidget()
        self.container.setObjectName("Container")

        # Shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(32, 32, 32, 32)
        container_layout.setSpacing(20)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
        self.logo_lbl = QLabel()
        self.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.logo_lbl)

        # Circular Progress Bar
        self.bar = CircularProgressBar()
        self.bar.setFixedSize(120, 120)
        self.bar.setMaximum(self._maximum)
        self.bar.setValue(self._value)

        # Wrapper to center the circle
        bar_wrapper = QWidget()
        bar_layout = QVBoxLayout(bar_wrapper)
        bar_layout.setContentsMargins(0, 0, 0, 0)
        bar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bar_layout.addWidget(self.bar)
        container_layout.addWidget(bar_wrapper)

        # Title
        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setObjectName("Title")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.title_lbl)

        # Status Label
        self.status_lbl = QLabel(label_text.upper())
        self.status_lbl.setObjectName("Status")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setWordWrap(True)
        container_layout.addWidget(self.status_lbl)

        # Cancel Button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.clicked.connect(self.cancel)

        # Center button
        btn_wrapper = QWidget()
        btn_layout = QVBoxLayout(btn_wrapper)
        btn_layout.setContentsMargins(0, 10, 0, 0)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(self.cancel_btn)
        container_layout.addWidget(btn_wrapper)

        layout.addWidget(self.container)

    def _apply_style(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]
        profile = tm.profile

        # Update Logo based on theme profile
        logo_name = f"logo_{profile.get('logo', 'axolotl')}"
        logo_icon = load_icon(logo_name)
        if not logo_icon.isNull():
            pixmap = logo_icon.pixmap(80, 80)
            self.logo_lbl.setPixmap(pixmap)
        else:
            # Fallback if specific logo not found
            self.logo_lbl.setText(profile.get('app_name', 'Noct'))

        # Update Circular Bar Colors
        self.bar.setColors(
            primary=c["brand"]["primary"],
            secondary=c["surface"]["tertiary"],
            text=c["text"]["primary"]
        )

        self.setStyleSheet(f"""
            QWidget#Container {{
                background-color: {c["surface"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["xl"]}px;
            }}
            
            QLabel#Title {{
                color: {c["brand"]["primary"]};
                font-size: 14px;
                font-weight: 700;
                letter-spacing: 2px;
            }}
            
            QLabel#Status {{
                color: {c["text"]["secondary"]};
                font-size: 10px;
                letter-spacing: 1px;
            }}
            
            QPushButton {{
                background-color: transparent;
                border: 1px solid {c["border"]["default"]};
                color: {c["text"]["secondary"]};
                border-radius: {r["md"]}px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 600;
            }}
            
            QPushButton:hover {{
                background-color: {c["state"]["hover"]};
                color: {c["text"]["primary"]};
                border-color: {c["border"]["strong"]};
            }}
        """)

    def setLabelText(self, text: str) -> None:
        self.status_lbl.setText(text.upper())
        QApplication.processEvents()

    def setValue(self, value: int) -> None:
        self.bar.setValue(value)
        QApplication.processEvents()

    def setMaximum(self, value: int) -> None:
        self._maximum = value
        self.bar.setMaximum(value)

    def wasCanceled(self) -> bool:
        return self._canceled

    def cancel(self) -> None:
        self._canceled = True
        self.status_lbl.setText("CANCELING...")
        self.close()

    def closeEvent(self, event) -> None:
        if not self._canceled:
            # Prevent closing by Esc unless canceled (simulating modal progress)
            # But allow if explicitly closed by code? No, usually progress dialogs block.
            # We'll allow it if value >= maximum (done) or canceled.
            if self._value >= self._maximum:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
