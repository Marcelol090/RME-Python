"""
Modern Progress Dialog for Map Loading.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QGraphicsDropShadowEffect,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager


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
        self.setMinimumWidth(480)

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
        container_layout.setSpacing(16)

        # Title
        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("Title")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.title_lbl)

        # Status Label
        self.status_lbl = QLabel(label_text)
        self.status_lbl.setObjectName("Status")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setWordWrap(True)
        container_layout.addWidget(self.status_lbl)

        # Progress Bar
        self.bar = QProgressBar()
        self.bar.setRange(self._minimum, self._maximum)
        self.bar.setValue(self._value)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(6)
        container_layout.addWidget(self.bar)

        # Cancel Button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.setFixedWidth(120)
        self.cancel_btn.clicked.connect(self.cancel)

        # Center button
        btn_wrapper = QWidget()
        btn_layout = QVBoxLayout(btn_wrapper)
        btn_layout.setContentsMargins(0, 16, 0, 0)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.addWidget(self.cancel_btn)
        container_layout.addWidget(btn_wrapper)

        layout.addWidget(self.container)

    def _apply_style(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.setStyleSheet(f"""
            QWidget#Container {{
                background-color: {c["surface"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["xl"]}px;
            }}
            
            QLabel#Title {{
                color: {c["text"]["primary"]};
                font-size: 20px;
                font-weight: 700;
                letter-spacing: 0.5px;
            }}
            
            QLabel#Status {{
                color: {c["text"]["secondary"]};
                font-size: 14px;
            }}
            
            QProgressBar {{
                background-color: {c["surface"]["secondary"]};
                border-radius: 3px;
                border: none;
            }}
            
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c["brand"]["primary"]}, stop:1 {c["brand"]["secondary"]});
                border-radius: 3px;
            }}
            
            QPushButton {{
                background-color: transparent;
                border: 1px solid {c["border"]["default"]};
                color: {c["text"]["secondary"]};
                border-radius: {r["md"]}px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            
            QPushButton:hover {{
                background-color: {c["state"]["hover"]};
                color: {c["text"]["primary"]};
                border-color: {c["border"]["strong"]};
            }}
        """)

    def setLabelText(self, text: str) -> None:
        self.status_lbl.setText(text)
        QApplication.processEvents()

    def setValue(self, value: int) -> None:
        self.bar.setValue(value)
        QApplication.processEvents()

    def wasCanceled(self) -> bool:
        return self._canceled

    def cancel(self) -> None:
        self._canceled = True
        self.status_lbl.setText("Canceling...")
        self.close()

    def closeEvent(self, event) -> None:
        if not self._canceled:
            # Prevent closing by Esc unless canceled
            event.ignore()
        else:
            event.accept()
