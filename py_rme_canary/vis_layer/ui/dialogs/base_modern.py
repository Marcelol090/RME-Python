"""
Modern Dialog Base Class.

Provides a standardized, frameless, draggable dialog with
the application's theme and consistent layout structure.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent, QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFrame,
    QSizePolicy
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager


class ModernDialog(QDialog):
    """
    Base class for modern, themed dialogs.
    """

    def __init__(self, parent: QWidget | None = None, title: str = "Dialog") -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._title = title
        self._dragging = False
        self._drag_position = QPoint()

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self) -> None:
        # Main container with rounded corners and border
        self.container = QFrame(self)
        self.container.setObjectName("ModernDialogContainer")

        # Main Layout (Header -> Content -> Footer)
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header
        self.header = QWidget()
        self.header.setObjectName("ModernDialogHeader")
        self.header.setFixedHeight(40)

        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(16, 0, 8, 0)

        self.title_label = QLabel(self._title)
        self.title_label.setObjectName("ModernDialogTitle")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("ModernDialogCloseButton")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self.reject)
        header_layout.addWidget(self.close_btn)

        self.main_layout.addWidget(self.header)

        # Content Area (To be populated by subclasses)
        self.content_area = QWidget()
        self.content_area.setObjectName("ModernDialogContent")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(16)

        self.main_layout.addWidget(self.content_area)

        # Footer (Optional)
        self.footer = QWidget()
        self.footer.setObjectName("ModernDialogFooter")
        self.footer.setVisible(False) # Hidden by default
        self.footer_layout = QHBoxLayout(self.footer)
        self.footer_layout.setContentsMargins(24, 16, 24, 16)
        self.footer_layout.setSpacing(12)

        self.main_layout.addWidget(self.footer)

        # Outer Layout
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10) # For shadow
        outer_layout.addWidget(self.container)

    def _apply_theme(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.setStyleSheet(f"""
            QFrame#ModernDialogContainer {{
                background-color: {c["surface"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["lg"]}px;
            }}
            QWidget#ModernDialogHeader {{
                background-color: {c["surface"]["secondary"]};
                border-top-left-radius: {r["lg"]}px;
                border-top-right-radius: {r["lg"]}px;
                border-bottom: 1px solid {c["border"]["default"]};
            }}
            QLabel#ModernDialogTitle {{
                color: {c["text"]["primary"]};
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton#ModernDialogCloseButton {{
                background: transparent;
                border: none;
                color: {c["text"]["secondary"]};
                font-weight: bold;
                border-radius: {r["sm"]}px;
            }}
            QPushButton#ModernDialogCloseButton:hover {{
                background-color: {c["state"]["error"]};
                color: white;
            }}
            QWidget#ModernDialogFooter {{
                background-color: {c["surface"]["secondary"]};
                border-bottom-left-radius: {r["lg"]}px;
                border-bottom-right-radius: {r["lg"]}px;
                border-top: 1px solid {c["border"]["default"]};
            }}
        """)

    def set_content_layout(self, layout: QVBoxLayout) -> None:
        """Replace the default content layout."""
        QWidget().setLayout(self.content_layout) # Delete old
        self.content_layout = layout
        self.content_area.setLayout(layout)

    def add_button(self, text: str, callback=None, role="secondary") -> QPushButton:
        """Add a button to the footer."""
        self.footer.setVisible(True)
        btn = QPushButton(text)
        if callback:
            btn.clicked.connect(callback)

        if role == "primary":
            tm = get_theme_manager()
            c = tm.tokens["color"]
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c["brand"]["primary"]};
                    color: {c["text"]["primary"]};
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {c["brand"]["secondary"]};
                }}
            """)

        self.footer_layout.addWidget(btn)
        return btn

    def add_spacer_to_footer(self) -> None:
        self.footer.setVisible(True)
        self.footer_layout.addStretch()

    # Dragging Logic
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            # Only drag if clicking the header
            if self.header.geometry().contains(self.container.mapFrom(self, event.pos())):
                self._dragging = True
                self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging = False
