"""Modern About Dialog.

Refactored to use ModernDialog and ThemeTokens.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager


class AboutDialog(ModernDialog):
    """Modern About Dialog with project info."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, title="About")
        self.setFixedSize(500, 300)

        self._setup_content()
        self._setup_footer()

    def _setup_content(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]

        layout = self.content_layout
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("py_rme_canary")
        title.setStyleSheet(f"color: {c['brand']['primary']}; font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Version
        version = QLabel("Version 1.0.0 (Canary)")
        version.setStyleSheet(f"color: {c['text']['primary']}; font-size: 14px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        # Description
        desc = QLabel("A modern, Python-based Map Editor for OTS.\nBased on Remere's Map Editor.")
        desc.setStyleSheet(f"color: {c['text']['secondary']}; font-size: 13px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()

        # Credits
        credits_lbl = QLabel("Developed by Google Deepmind & User")
        credits_lbl.setStyleSheet(f"color: {c['text']['tertiary']}; font-size: 11px;")
        credits_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits_lbl)

    def _setup_footer(self) -> None:
        self.add_spacer_to_footer()
        self.add_button("Close", callback=self.accept, role="primary")
        self.add_spacer_to_footer()
