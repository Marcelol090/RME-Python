"""Modern Assets Dock — Antigravity Style.

Combines asset status, sprite preview, and resource management.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager
from py_rme_canary.vis_layer.ui.resources.icon_pack import load_icon

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class StatusIndicator(QWidget):
    """Colored dot indicating status."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self._active = False
        self._color = "#EF4444"  # Default red

    def set_status(self, active: bool) -> None:
        self._active = active
        self._color = "#3EEA8D" if active else "#EF4444"  # Green / Red
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = QColor(self._color)
        p.setBrush(c)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(2, 2, 8, 8)

        # Glow
        if self._active:
            c.setAlpha(100)
            p.setBrush(c)
            p.drawEllipse(0, 0, 12, 12)


class ModernAssetsDock(QDockWidget):
    """
    Antigravity-styled dock for managing assets and previewing sprites.
    """

    def __init__(self, editor: QtMapEditor, parent: QWidget | None = None) -> None:
        super().__init__("Assets & Sprites", parent)
        self.editor = editor

        self._setup_ui()
        self._apply_style()
        self.update_info()

    def _setup_ui(self) -> None:
        self.container = QWidget()
        main_layout = QVBoxLayout(self.container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll Area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(16)

        # --- Section 1: Sprite Preview ---
        self._create_preview_section()

        # --- Section 2: Asset Status ---
        self._create_status_section()

        self.layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        self.setWidget(self.container)

    def _create_preview_section(self) -> None:
        group = QFrame()
        group.setObjectName("Card")
        l = QVBoxLayout(group)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        icon_lbl = QLabel()
        icon_lbl.setPixmap(load_icon("icon_image").pixmap(16, 16) if not load_icon("icon_image").isNull() else QPixmap())
        header_lbl = QLabel("SPRITE PREVIEW")
        header_lbl.setObjectName("SectionHeader")
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(header_lbl)
        header_layout.addStretch()
        l.addLayout(header_layout)

        # ID Input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("ID:"))

        self.sprite_id_spin = QSpinBox()
        self.sprite_id_spin.setRange(0, 10_000_000)
        self.sprite_id_spin.setValue(0)
        self.sprite_id_spin.valueChanged.connect(self._on_sprite_changed)
        input_layout.addWidget(self.sprite_id_spin)
        l.addLayout(input_layout)

        # Preview Box
        self.preview_box = QFrame()
        self.preview_box.setObjectName("PreviewBox")
        self.preview_box.setMinimumHeight(120)
        pb_layout = QVBoxLayout(self.preview_box)
        pb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_lbl = QLabel("No Sprite")
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pb_layout.addWidget(self.preview_lbl)

        l.addWidget(self.preview_box)

        self.layout.addWidget(group)

    def _create_status_section(self) -> None:
        group = QFrame()
        group.setObjectName("Card")
        l = QVBoxLayout(group)
        l.setContentsMargins(12, 12, 12, 12)
        l.setSpacing(8)

        # Header
        header_layout = QHBoxLayout()
        header_lbl = QLabel("ASSET STATUS")
        header_lbl.setObjectName("SectionHeader")
        header_layout.addWidget(header_lbl)
        header_layout.addStretch()
        l.addLayout(header_layout)

        # Info Grid
        self.info_client = self._add_info_row(l, "Client Version:", "Unknown")
        self.info_path = self._add_info_row(l, "Path:", "Not set")

        # Separator
        sep = QFrame()
        sep.setObjectName("Separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        l.addWidget(sep)

        # Resources with indicators
        self.status_dat = self._add_status_row(l, "Tibia.dat")
        self.status_spr = self._add_status_row(l, "Tibia.spr")
        self.status_otb = self._add_status_row(l, "items.otb")
        self.status_xml = self._add_status_row(l, "items.xml")

        # Actions
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_load = QPushButton("Load Assets")
        self.btn_load.clicked.connect(self._on_change)
        btn_layout.addWidget(self.btn_load)

        self.btn_reload = QPushButton("Reload")
        self.btn_reload.setObjectName("SecondaryButton")
        self.btn_reload.clicked.connect(self._on_reload)
        btn_layout.addWidget(self.btn_reload)

        l.addLayout(btn_layout)

        self.layout.addWidget(group)

    def _add_info_row(self, layout, label: str, value: str) -> QLabel:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setObjectName("LabelDim")
        val = QLabel(value)
        val.setObjectName("LabelValue")
        val.setAlignment(Qt.AlignmentFlag.AlignRight)
        # val.setWordWrap(True) # Path might be long

        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(val)
        layout.addLayout(row)
        return val

    def _add_status_row(self, layout, label: str) -> StatusIndicator:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setObjectName("LabelValue")
        ind = StatusIndicator()

        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(ind)
        layout.addLayout(row)
        return ind

    def _apply_style(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.setStyleSheet(f"""
            ModernAssetsDock {{
                background: {c["surface"]["primary"]};
            }}

            QScrollArea {{
                background: transparent;
                border: none;
            }}

            QWidget {{
                background: transparent;
            }}

            QFrame#Card {{
                background: {c["surface"]["secondary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["lg"]}px;
            }}

            QFrame#PreviewBox {{
                background: {c["surface"]["tertiary"]};
                border: 1px dashed {c["border"]["strong"]};
                border-radius: {r["md"]}px;
            }}

            QLabel#SectionHeader {{
                color: {c["brand"]["primary"]};
                font-weight: 700;
                font-size: 11px;
                letter-spacing: 1px;
            }}

            QLabel#LabelDim {{
                color: {c["text"]["tertiary"]};
                font-size: 12px;
            }}

            QLabel#LabelValue {{
                color: {c["text"]["secondary"]};
                font-weight: 500;
                font-size: 12px;
            }}

            QFrame#Separator {{
                background: {c["border"]["default"]};
            }}

            QPushButton {{
                background: {c["brand"]["primary"]};
                color: {c["text"]["primary"]};
                border: none;
                border-radius: {r["sm"]}px;
                padding: 6px 12px;
                font-weight: 600;
            }}

            QPushButton:hover {{
                background: {c["brand"]["secondary"]};
            }}

            QPushButton#SecondaryButton {{
                background: {c["surface"]["tertiary"]};
                border: 1px solid {c["border"]["default"]};
            }}

            QPushButton#SecondaryButton:hover {{
                background: {c["state"]["hover"]};
                border-color: {c["brand"]["primary"]};
            }}
        """)

    def _on_sprite_changed(self, value: int) -> None:
        """Forward change to editor logic."""
        if hasattr(self.editor, "_update_sprite_preview"):
            self.editor._update_sprite_preview()

    def update_info(self) -> None:
        """Update UI with editor state."""
        # Profile
        self.info_client.setText(str(self.editor.client_version or "—"))

        path = str(self.editor.assets_dir or "Not set")
        if len(path) > 25:
            path = "..." + path[-22:]
        self.info_path.setText(path)
        self.info_path.setToolTip(str(self.editor.assets_dir or ""))

        # Status
        has_assets = self.editor.sprite_assets is not None
        self.status_dat.set_status(has_assets)
        self.status_spr.set_status(has_assets)

        # Heuristic for OTB/XML
        has_otb = bool(self.editor.id_mapper)
        # We assume XML is loaded if mapper exists, loosely
        self.status_otb.set_status(has_otb)
        self.status_xml.set_status(has_otb) # Simplified

    def _on_change(self):
        if hasattr(self.editor, "_open_client_data_loader"):
            self.editor._open_client_data_loader()
            self.update_info()

    def _on_reload(self):
        if hasattr(self.editor, "_reload_item_definitions_for_current_context"):
            self.editor._reload_item_definitions_for_current_context(source="assets_dock")
            self.update_info()
