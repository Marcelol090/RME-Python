"""Modern About Dialog.

Refactored to use ModernDialog and ThemeTokens.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager


class AboutDialog(ModernDialog):
    """
    Modern About Dialog with Antigravity styling.
    
    Features:
    - Centered glass layout
    - Brand gradient typography
    - Scrolling credits section
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, title="About")
        self.setFixedSize(500, 420)
        self._setup_content()
        self._setup_footer()
        self._apply_antigravity_style()

    def _setup_content(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]

        layout = self.content_layout
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 40, 40, 0)

        # 1. Logo / Title Section
        self.title_lbl = QLabel("Py RME Canary")
        self.title_lbl.setObjectName("AboutTitle")
        self.title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_lbl)

        self.version_lbl = QLabel("Version 1.0.0 (Canary)")
        self.version_lbl.setObjectName("AboutVersion")
        self.version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.version_lbl)

        # 2. Description
        desc_text = (
            "A modern, premium Map Editor for Open Tibia Servers.\n"
            "Built with Python, PyQt6, and the Antigravity Design System."
        )
        self.desc_lbl = QLabel(desc_text)
        self.desc_lbl.setObjectName("AboutDesc")
        self.desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)

        # 3. Credits / Contributors Scroll Area
        self.credits_box = QGroupBox("Credits")
        self.credits_box.setObjectName("CreditsBox")
        credits_layout = QVBoxLayout(self.credits_box)
        credits_layout.setContentsMargins(12, 24, 12, 12)
        
        # Simple scrollable list for credits
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        credits_content = QWidget()
        credits_content.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(credits_content)
        vbox.setSpacing(4)
        
        contributors = [
            "Google Deepmind - AI Architecture",
            "User - Lead Developer",
            "Remere - Original RME",
            "Edubart - OTBM Specs",
            "Open Tibia Community",
            "Canary Project Team",
        ]
        
        for name in contributors:
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color: {c['text']['primary']}; font-size: 12px;")
            vbox.addWidget(lbl)
            
        vbox.addStretch()
        scroll.setWidget(credits_content)
        credits_layout.addWidget(scroll)
        
        layout.addWidget(self.credits_box)
        layout.addStretch()

    def _apply_antigravity_style(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]
        
        self.setStyleSheet(f"""
            QLabel#AboutTitle {{
                color: {c["brand"]["primary"]};
                font-size: 28px;
                font-weight: 800;
                letter-spacing: 1px;
            }}
            
            QLabel#AboutVersion {{
                color: {c["text"]["tertiary"]};
                font-size: 13px;
                font-weight: 500;
            }}
            
            QLabel#AboutDesc {{
                color: {c["text"]["secondary"]};
                font-size: 14px;
                line-height: 1.4;
            }}
            
            QGroupBox#CreditsBox {{
                border: 1px solid {c["surface"]["tertiary"]};
                border-radius: {r["lg"]}px;
                background-color: {c["surface"]["secondary"]};
                margin-top: 16px;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                color: {c["text"]["tertiary"]};
            }}
            
            QGroupBox#CreditsBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                background-color: transparent;
            }}
        """)

    def _setup_footer(self) -> None:
        # Centered Close Button
        footer_layout = self.footer_container.layout()
        if footer_layout:
             # Clear default spacer/buttons if needed, but ModernDialog adds them
             # We'll just add ours, layout is HBox
             pass
        
        self.add_spacer_to_footer()
        self.add_button("Visit GitHub", role="secondary", callback=lambda: None) # Placeholder
        self.add_button("Close", callback=self.accept, role="primary")
        self.add_spacer_to_footer()
