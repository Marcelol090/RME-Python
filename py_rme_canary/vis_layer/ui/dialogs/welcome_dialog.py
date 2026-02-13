"""
Modern Welcome Screen — Antigravity Style.

Features:
- Logo display (Axolotl/Noct)
- Recent file list with time-ago formatting
- New/Open actions
- Glassmorphism design
- Theme integration
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect
)

from py_rme_canary.vis_layer.ui.resources.icon_pack import load_icon
from py_rme_canary.vis_layer.ui.theme import get_theme_manager
from py_rme_canary.vis_layer.ui.icons import icon_logo_axolotl

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget


class RecentFileWidget(QWidget):
    """Custom widget for recent file list item."""

    def __init__(self, path: str, parent=None) -> None:
        super().__init__(parent)
        self.path = path

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        # Filename
        name = os.path.basename(path)
        self.name_lbl = QLabel(name)
        self.name_lbl.setObjectName("RecentName")
        layout.addWidget(self.name_lbl)

        # Path (truncated)
        self.path_lbl = QLabel(path)
        self.path_lbl.setObjectName("RecentPath")
        self.path_lbl.setWordWrap(False)
        layout.addWidget(self.path_lbl)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style()

    def _apply_style(self):
        tm = get_theme_manager()
        c = tm.tokens["color"]

        self.setStyleSheet(f"""
            QWidget {{
                background: transparent;
                border-radius: 8px;
            }}
            QWidget:hover {{
                background-color: {c["state"]["hover"]};
            }}
            QLabel#RecentName {{
                color: {c["text"]["primary"]};
                font-weight: 600;
                font-size: 14px;
                background: transparent;
            }}
            QLabel#RecentPath {{
                color: {c["text"]["tertiary"]};
                font-size: 11px;
                background: transparent;
            }}
        """)


class WelcomeDialog(QDialog):
    """
    Modern Welcome Screen.
    """

    new_map_requested = pyqtSignal()
    open_map_requested = pyqtSignal()
    recent_file_selected = pyqtSignal(str)

    def __init__(self, recent_files: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(800, 500)

        self.recent_files = recent_files
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main Container with Shadow
        self.container = QWidget(self)
        self.container.setObjectName("Container")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 10)
        self.container.setGraphicsEffect(shadow)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Left Panel (Brand & Actions)
        self.left_panel = QFrame()
        self.left_panel.setObjectName("LeftPanel")
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(40, 40, 40, 40)
        left_layout.setSpacing(24)

        # Logo
        self.logo_lbl = QLabel()
        self.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft)
        left_layout.addWidget(self.logo_lbl)

        # App Name & Version
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        self.title_lbl = QLabel("Noct Map Editor")
        self.title_lbl.setObjectName("AppTitle")
        self.subtitle_lbl = QLabel("Canary Studio • v2.0.0")
        self.subtitle_lbl.setObjectName("AppSubtitle")
        title_box.addWidget(self.title_lbl)
        title_box.addWidget(self.subtitle_lbl)
        left_layout.addLayout(title_box)

        left_layout.addStretch()

        # Actions
        self.btn_new = QPushButton("New Map")
        self.btn_new.setObjectName("ActionBtn")
        self.btn_new.setIcon(load_icon("action_new"))
        self.btn_new.setIconSize(QSize(20, 20))
        self.btn_new.clicked.connect(self._on_new)
        self.btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        left_layout.addWidget(self.btn_new)

        self.btn_open = QPushButton("Open Map")
        self.btn_open.setObjectName("ActionBtn")
        self.btn_open.setIcon(load_icon("action_open"))
        self.btn_open.setIconSize(QSize(20, 20))
        self.btn_open.clicked.connect(self._on_open)
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        left_layout.addWidget(self.btn_open)

        # Footer
        footer = QLabel("© 2026 Canary Project")
        footer.setObjectName("Footer")
        left_layout.addSpacing(20)
        left_layout.addWidget(footer)

        container_layout.addWidget(self.left_panel, 2)

        # Right Panel (Recent Files)
        self.right_panel = QFrame()
        self.right_panel.setObjectName("RightPanel")
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(24, 24, 24, 24)
        right_layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()
        lbl_recent = QLabel("Recent Projects")
        lbl_recent.setObjectName("RecentHeader")
        header_layout.addWidget(lbl_recent)

        # Close Button
        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("CloseButton")
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close.clicked.connect(self.reject)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_close)

        right_layout.addLayout(header_layout)

        # List
        self.recent_list = QListWidget()
        self.recent_list.setObjectName("RecentList")
        self.recent_list.setFrameShape(QFrame.Shape.NoFrame)
        self.recent_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.recent_list.itemClicked.connect(self._on_recent_clicked)

        self._populate_recent()
        right_layout.addWidget(self.recent_list)

        container_layout.addWidget(self.right_panel, 3)
        layout.addWidget(self.container)

    def _populate_recent(self):
        self.recent_list.clear()
        if not self.recent_files:
            item = QListWidgetItem("No recent files found.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Just add basic item
            self.recent_list.addItem(item)
            return

        for path in self.recent_files:
            if not path: continue

            widget = RecentFileWidget(path)

            item = QListWidgetItem(self.recent_list)
            item.setSizeHint(QSize(0, 68))
            item.setData(Qt.ItemDataRole.UserRole, path)

            self.recent_list.addItem(item)
            self.recent_list.setItemWidget(item, widget)

    def _apply_style(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]
        profile = tm.profile

        # Programmatic Logo
        logo_icon = icon_logo_axolotl(size=96, theme_style=profile["component_style"])
        if not logo_icon.isNull():
            self.logo_lbl.setPixmap(logo_icon.pixmap(96, 96))
        else:
            self.logo_lbl.setText("NOCT")
            self.logo_lbl.setStyleSheet(f"font-size: 48px; font-weight: 800; color: {c['brand']['primary']};")

        # Stylesheet
        self.setStyleSheet(f"""
            QWidget#Container {{
                background-color: {c["surface"]["primary"]};
                border-radius: {r["xl"]}px;
                border: 1px solid {c["border"]["default"]};
            }}

            /* Left Panel */
            QFrame#LeftPanel {{
                background-color: {c["surface"]["secondary"]};
                border-top-left-radius: {r["xl"]}px;
                border-bottom-left-radius: {r["xl"]}px;
                border-right: 1px solid {c["border"]["default"]};
            }}

            QLabel#AppTitle {{
                color: {c["text"]["primary"]};
                font-size: 24px;
                font-weight: 700;
                letter-spacing: -0.5px;
            }}

            QLabel#AppSubtitle {{
                color: {c["brand"]["primary"]};
                font-size: 13px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}

            QLabel#Footer {{
                color: {c["text"]["disabled"]};
                font-size: 11px;
            }}

            QPushButton#ActionBtn {{
                text-align: left;
                padding-left: 20px;
                height: 48px;
                background-color: {c["surface"]["elevated"]};
                color: {c["text"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["md"]}px;
                font-weight: 600;
            }}
            QPushButton#ActionBtn:hover {{
                background-color: {c["state"]["hover"]};
                border-color: {c["brand"]["secondary"]};
                color: {c["brand"]["active"]};
            }}
            QPushButton#ActionBtn:pressed {{
                background-color: {c["state"]["active"]};
            }}

            /* Right Panel */
            QFrame#RightPanel {{
                background-color: transparent;
                border-top-right-radius: {r["xl"]}px;
                border-bottom-right-radius: {r["xl"]}px;
            }}

            QLabel#RecentHeader {{
                color: {c["text"]["secondary"]};
                font-size: 12px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            QPushButton#CloseButton {{
                background: transparent;
                border: none;
                color: {c["text"]["tertiary"]};
                font-size: 18px;
                border-radius: {r["round"]}px;
            }}
            QPushButton#CloseButton:hover {{
                background-color: {c["state"]["error"]};
                color: white;
            }}

            QListWidget {{
                background: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background: transparent;
                border-radius: {r["md"]}px;
                margin-bottom: 4px;
                padding: 4px;
            }}
            QListWidget::item:hover {{
                background: {c["state"]["hover"]};
            }}
            QListWidget::item:selected {{
                background: {c["state"]["active"]};
                border: 1px solid {c["brand"]["primary"]};
            }}
        """)

    def _on_new(self):
        self.new_map_requested.emit()
        self.accept()

    def _on_open(self):
        self.open_map_requested.emit()
        self.accept()

    def _on_recent_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.recent_file_selected.emit(path)
            self.accept()
