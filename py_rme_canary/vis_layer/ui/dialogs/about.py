"""Modern About Dialog."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme.colors import get_qcolor, get_theme_color


class AboutDialog(QDialog):
    """Modern About Dialog with gradient background and project info."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About py_rme_canary")
        self.setFixedSize(500, 300)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._setup_ui()

    def _setup_ui(self) -> None:
        # Main container with gradient
        container = QWidget(self)
        container.setObjectName("Container")
        container.setGeometry(0, 0, 500, 300)

        bg_color = get_theme_color("background")
        surface_color = get_theme_color("surface")
        accent_color = get_theme_color("primary")

        container.setStyleSheet(f"""
            #Container {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {bg_color}, stop:1 {surface_color}
                );
                border: 1px solid {get_theme_color("border")};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        # Title
        title = QLabel("py_rme_canary")
        title.setStyleSheet(f"color: {accent_color}; font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Version
        version = QLabel("Version 1.0.0 (Canary)")
        version.setStyleSheet("color: #E5E5E7; font-size: 14px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        # Description
        desc = QLabel("A modern, Python-based Map Editor for OTS.\nBased on Remere's Map Editor.")
        desc.setStyleSheet("color: #A1A1AA; font-size: 13px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()

        # Credits
        credits_lbl = QLabel("Developed by Google Deepmind & User")
        credits_lbl.setStyleSheet("color: #71717A; font-size: 11px;")
        credits_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits_lbl)

        # Close Button
        btn_close = QPushButton("Close")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(f"""
            QPushButton {{
                background: {accent_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 32px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {get_qcolor(accent_color).lighter(110).name()};
            }}
        """)
        btn_close.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()
