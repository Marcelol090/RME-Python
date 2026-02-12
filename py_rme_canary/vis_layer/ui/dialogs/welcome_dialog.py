"""Welcome Dialog - First-run experience.

Modern welcome dialog with:
- Frameless glassmorphism layout
- Quick actions (New, Open, Preferences)
- Scrollable recent files list
- "Show on Startup" toggle
- Full Antigravity theme token integration
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.resources.icon_pack import load_icon
from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    pass


class _ActionButton(QFrame):
    """Hoverable action button for the sidebar."""

    clicked = pyqtSignal()

    def __init__(self, emoji: str, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        icon_lbl = QLabel(emoji)
        icon_lbl.setStyleSheet("font-size: 18px; background: transparent;")
        layout.addWidget(icon_lbl)

        text_lbl = QLabel(title)
        text_lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {c['text']['primary']}; background: transparent;"
        )
        layout.addWidget(text_lbl)
        layout.addStretch()

        self.setStyleSheet(
            f"""
            _ActionButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: {r['md']}px;
            }}
            _ActionButton:hover {{
                background: {c['state']['hover']};
                border-color: {c['border']['default']};
            }}
        """
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)


class _RecentFileItem(QFrame):
    """A single recent file entry with hover effects."""

    clicked = pyqtSignal(str)

    def __init__(self, filepath: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._path = filepath
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)

        filename = os.path.basename(filepath)
        dirname = os.path.dirname(filepath)

        name_lbl = QLabel(filename)
        name_lbl.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {c['text']['primary']}; background: transparent;"
        )
        layout.addWidget(name_lbl)

        path_lbl = QLabel(dirname)
        path_lbl.setStyleSheet(f"font-size: 11px; color: {c['text']['tertiary']}; background: transparent;")
        path_lbl.setWordWrap(True)
        layout.addWidget(path_lbl)

        self.setStyleSheet(
            f"""
            _RecentFileItem {{
                background: {c['surface']['tertiary']};
                border: 1px solid transparent;
                border-radius: {r['sm']}px;
            }}
            _RecentFileItem:hover {{
                background: {c['state']['hover']};
                border-color: {c['border']['interactive']};
            }}
        """
        )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.clicked.emit(self._path)
        super().mousePressEvent(event)


class WelcomeDialog(QDialog):
    """Welcome dialog shown on startup.

    Signals:
        new_map_requested: User wants to create new map
        open_map_requested: User wants to open existing map
        recent_file_selected: User selected a recent file (path)
    """

    new_map_requested = pyqtSignal()
    open_map_requested = pyqtSignal()
    recent_file_selected = pyqtSignal(str)

    def __init__(
        self,
        recent_files: list[str] | list[tuple[str, str]] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._recent_files = recent_files or []
        self._dragging = False
        self._drag_position = QPoint()

        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Noct Map Editor")
        self.setMinimumSize(780, 520)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        # Glass container
        container = QFrame()
        container.setObjectName("WelcomeContainer")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(Qt.GlobalColor.black)
        shadow.setOffset(0, 10)
        container.setGraphicsEffect(shadow)

        container.setStyleSheet(
            f"""
            QFrame#WelcomeContainer {{
                background-color: {c['surface']['primary']};
                border: 1px solid {c['border']['default']};
                border-radius: {r['xl']}px;
            }}
        """
        )

        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Left Sidebar ──
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)
        sidebar.setStyleSheet(
            f"""
            QWidget#Sidebar {{
                background-color: {c['surface']['secondary']};
                border-top-left-radius: {r['xl']}px;
                border-bottom-left-radius: {r['xl']}px;
                border-right: 1px solid {c['border']['default']};
            }}
        """
        )

        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(24, 28, 24, 20)
        side_layout.setSpacing(6)

        # Brand
        brand_row = QHBoxLayout()
        brand_icon = QLabel()
        brand_icon.setPixmap(load_icon("logo_axolotl").pixmap(24, 24))
        brand_icon.setStyleSheet("background: transparent;")
        brand_row.addWidget(brand_icon)

        brand = QLabel("Noct Map Editor")
        brand.setStyleSheet(
            f"""
            font-size: 22px; font-weight: 800;
            color: {c['brand']['primary']};
            background: transparent;
        """
        )
        brand_row.addWidget(brand)
        brand_row.addStretch()
        side_layout.addLayout(brand_row)

        tagline = QLabel("Powered by Axolotl Engine")
        tagline.setStyleSheet(f"font-size: 12px; color: {c['text']['secondary']}; background: transparent;")
        side_layout.addWidget(tagline)

        side_layout.addSpacing(28)

        # Section label
        qs = QLabel("QUICK START")
        qs.setStyleSheet(
            f"font-size: 10px; font-weight: 700; letter-spacing: 1.5px;"
            f" color: {c['text']['tertiary']}; background: transparent;"
        )
        side_layout.addWidget(qs)
        side_layout.addSpacing(8)

        # Action buttons
        btn_new = _ActionButton("📄", "New Map", sidebar)
        btn_new.clicked.connect(self._on_new)
        side_layout.addWidget(btn_new)

        btn_open = _ActionButton("📂", "Open Map", sidebar)
        btn_open.clicked.connect(self._on_open)
        side_layout.addWidget(btn_open)

        btn_prefs = _ActionButton("⚙️", "Preferences", sidebar)
        btn_prefs.clicked.connect(self._on_preferences)
        side_layout.addWidget(btn_prefs)

        side_layout.addStretch()

        # Version
        ver = QLabel("v1.0.0-alpha")
        ver.setStyleSheet(f"font-size: 10px; color: {c['text']['disabled']}; background: transparent;")
        side_layout.addWidget(ver)

        main_layout.addWidget(sidebar)

        # ── Right Panel (Recent Files) ──
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(28, 28, 28, 20)
        right_layout.setSpacing(12)

        # Header row
        header_row = QHBoxLayout()
        recent_hdr = QLabel("Recent Projects")
        recent_hdr.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {c['text']['primary']};")
        header_row.addWidget(recent_hdr)
        header_row.addStretch()

        close_btn = QLabel("✕")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"font-size: 16px; color: {c['text']['secondary']}; padding: 4px 8px;")
        close_btn.mousePressEvent = lambda _: self.reject()
        header_row.addWidget(close_btn)
        right_layout.addLayout(header_row)

        # Scrollable recent files
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(6)

        if self._recent_files:
            for entry in self._recent_files[:15]:
                path = str(entry[0]) if isinstance(entry, list | tuple) and len(entry) >= 1 else str(entry)
                item = _RecentFileItem(path, scroll_content)
                item.clicked.connect(self._on_recent_clicked)
                scroll_layout.addWidget(item)
        else:
            empty = QLabel("No recent files")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {c['text']['disabled']}; font-size: 13px; padding: 40px;")
            scroll_layout.addWidget(empty)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        right_layout.addWidget(scroll, stretch=1)

        # Footer: Show on Startup
        self._show_startup_chk = QCheckBox("Show on Startup")
        self._show_startup_chk.setChecked(True)
        self._show_startup_chk.setStyleSheet(f"color: {c['text']['tertiary']}; font-size: 11px;")
        right_layout.addWidget(self._show_startup_chk)

        main_layout.addWidget(right, stretch=1)
        outer.addWidget(container)

    # ── Drag support (frameless window) ──
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging = False

    # ── Actions ──
    def _on_new(self) -> None:
        self.new_map_requested.emit()
        self.accept()

    def _on_open(self) -> None:
        self.open_map_requested.emit()
        self.accept()

    def _on_preferences(self) -> None:
        """Open preferences dialog without closing welcome."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.settings_dialog import (
                SettingsDialog,
            )

            dlg = SettingsDialog(parent=self)
            dlg.exec()
        except ImportError:
            pass

    def _on_recent_clicked(self, path: str) -> None:
        self.recent_file_selected.emit(path)
        self.accept()

    @property
    def show_on_startup(self) -> bool:
        return self._show_startup_chk.isChecked()
