"""
Modern Loading Dialog.

A frameless, themed dialog with logo and progress bar for file operations.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QLabel, QProgressBar, QWidget

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager


class ModernLoadingDialog(ModernDialog):
    """
    Dialog showing a loading state with logo and progress bar.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "Loading...",
        message: str = "Please wait..."
    ) -> None:
        super().__init__(parent, title)

        # Override setup to remove header buttons (modal behavior)
        self.close_btn.setVisible(False)
        self.header.setVisible(False) # Clean look, just content

        # Adjust layout for loading
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        self.content_layout.setSpacing(24)

        # Logo (Placeholder or Resource)
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Try to load application logo, fallback to text
        # Using a unicode or simple style if icon not available
        self.logo_label.setText("CANARY STUDIO")
        self.logo_label.setStyleSheet("font-size: 24px; font-weight: 800; letter-spacing: 2px;")
        self.content_layout.addWidget(self.logo_label)

        # Message
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setObjectName("LoadingMessage")
        self.content_layout.addWidget(self.message_label)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 0) # Indeterminate by default
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6) # Slim modern bar
        self.content_layout.addWidget(self.progress)

        # Apply specific theme overrides
        self._apply_loading_theme()

    def _apply_loading_theme(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]

        # Customize message label
        self.message_label.setStyleSheet(f"color: {c['text']['secondary']}; font-size: 14px;")

        # Ensure container has shadow for floating effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

    def set_message(self, message: str) -> None:
        """Update the status message."""
        self.message_label.setText(message)
        QApplication.processEvents() # Force UI update

    def set_progress(self, value: int, max_val: int = 100) -> None:
        """Set determinate progress."""
        self.progress.setRange(0, max_val)
        self.progress.setValue(value)
        QApplication.processEvents()

    def set_indeterminate(self) -> None:
        """Set indeterminate progress."""
        self.progress.setRange(0, 0)
        QApplication.processEvents()
