"""Extensions Dialog.

Manage material extensions - matches C++ ExtensionsDialog from Redux.
"""
from __future__ import annotations

import os
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


@dataclass
class MaterialExtension:
    """Information about a material extension."""

    name: str = ""
    author: str = ""
    description: str = ""
    version_string: str = ""
    url: str = ""
    author_url: str = ""
    enabled: bool = True
    file_path: str = ""


class ExtensionCard(QFrame):
    """Card widget displaying a single extension."""

    link_clicked = pyqtSignal(str)  # URL

    def __init__(self, extension: MaterialExtension, parent=None):
        super().__init__(parent)
        self._extension = extension
        self._setup_ui()
        self._style()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Extension name (clickable if URL exists)
        name_layout = QHBoxLayout()
        name_label = QLabel("Extension:")
        name_label.setStyleSheet("font-weight: bold; color: #8B8B9B;")
        name_layout.addWidget(name_label)

        if self._extension.url:
            name_btn = QPushButton(self._extension.name)
            name_btn.setFlat(True)
            name_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            name_btn.setStyleSheet(
                "QPushButton { color: #8B5CF6; text-decoration: underline; border: none; "
                "text-align: left; padding: 0; } QPushButton:hover { color: #A78BFA; }"
            )
            name_btn.clicked.connect(lambda: self.link_clicked.emit(self._extension.url))
            name_layout.addWidget(name_btn)
        else:
            name_value = QLabel(self._extension.name)
            name_value.setStyleSheet("color: #E5E5E7; font-weight: bold;")
            name_layout.addWidget(name_value)

        name_layout.addStretch()
        layout.addLayout(name_layout)

        # Author (clickable if URL exists)
        author_layout = QHBoxLayout()
        author_label = QLabel("Author:")
        author_label.setStyleSheet("font-weight: bold; color: #8B8B9B;")
        author_layout.addWidget(author_label)

        if self._extension.author_url:
            author_btn = QPushButton(self._extension.author)
            author_btn.setFlat(True)
            author_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            author_btn.setStyleSheet(
                "QPushButton { color: #8B5CF6; text-decoration: underline; border: none; "
                "text-align: left; padding: 0; } QPushButton:hover { color: #A78BFA; }"
            )
            author_btn.clicked.connect(lambda: self.link_clicked.emit(self._extension.author_url))
            author_layout.addWidget(author_btn)
        else:
            author_value = QLabel(self._extension.author or "Unknown")
            author_value.setStyleSheet("color: #E5E5E7;")
            author_layout.addWidget(author_value)

        author_layout.addStretch()
        layout.addLayout(author_layout)

        # Description
        desc_layout = QHBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet("font-weight: bold; color: #8B8B9B;")
        desc_layout.addWidget(desc_label)
        desc_value = QLabel(self._extension.description or "No description")
        desc_value.setStyleSheet("color: #E5E5E7;")
        desc_value.setWordWrap(True)
        desc_layout.addWidget(desc_value, 1)
        layout.addLayout(desc_layout)

        # Version/Clients
        version_layout = QHBoxLayout()
        version_label = QLabel("Clients:")
        version_label.setStyleSheet("font-weight: bold; color: #8B8B9B;")
        version_layout.addWidget(version_label)
        version_value = QLabel(self._extension.version_string or "All versions")
        version_value.setStyleSheet("color: #E5E5E7;")
        version_layout.addWidget(version_value)
        version_layout.addStretch()
        layout.addLayout(version_layout)

    def _style(self):
        self.setStyleSheet(
            """
            ExtensionCard {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 6px;
            }
        """
        )


class ExtensionsDialog(QDialog):
    """Manage material extensions.

    Matches C++ ExtensionsDialog from Redux - displays loaded extensions
    with metadata and provides access to extensions folder.
    """

    def __init__(self, parent=None, extensions: list[MaterialExtension] | None = None):
        super().__init__(parent)
        self._extensions = extensions or []

        self.setWindowTitle("Extensions")
        self.setMinimumSize(600, 500)
        self._setup_ui()
        self._style()
        self._populate_extensions()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Scroll area for extensions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #1E1E2E;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #363650;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #8B5CF6;
            }
        """
        )

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setSpacing(12)
        self._content_layout.setContentsMargins(0, 0, 8, 0)
        self._content_layout.addStretch()

        scroll.setWidget(self._content)
        layout.addWidget(scroll, 1)

        # Buttons
        btn_layout = QHBoxLayout()

        ok_btn = QPushButton("OK")
        ok_btn.setToolTip("Close window")
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)

        open_folder_btn = QPushButton("Open Extensions Folder")
        open_folder_btn.setToolTip("Open the extensions directory in file explorer")
        open_folder_btn.clicked.connect(self._open_extensions_folder)
        btn_layout.addWidget(open_folder_btn)

        layout.addLayout(btn_layout)

    def _style(self):
        self.setStyleSheet(
            """
            ExtensionsDialog {
                background: #1E1E2E;
            }
            QPushButton {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: #363650;
            }
            QPushButton:pressed {
                background: #8B5CF6;
            }
        """
        )

    def _populate_extensions(self):
        """Populate the list with extension cards."""
        # Remove old cards
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._extensions:
            # No extensions message
            no_ext_label = QLabel("No extensions loaded.")
            no_ext_label.setStyleSheet("color: #8B8B9B; font-style: italic; padding: 20px;")
            no_ext_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._content_layout.insertWidget(0, no_ext_label)
        else:
            # Add extension cards
            for ext in self._extensions:
                card = ExtensionCard(ext)
                card.link_clicked.connect(self._open_link)
                self._content_layout.insertWidget(self._content_layout.count() - 1, card)

    def _open_link(self, url: str):
        """Open URL in browser."""
        QDesktopServices.openUrl(QUrl(url))

    def _open_extensions_folder(self):
        """Open extensions folder in file explorer."""
        # Get extensions directory (configurable, default to app data)
        ext_dir = self._get_extensions_directory()

        # Ensure directory exists
        ext_dir.mkdir(parents=True, exist_ok=True)

        # Open in file explorer
        system = platform.system()
        if system == "Windows":
            os.startfile(str(ext_dir))
        elif system == "Darwin":  # macOS
            subprocess.run(["open", str(ext_dir)])
        else:  # Linux
            subprocess.run(["xdg-open", str(ext_dir)])

    def _get_extensions_directory(self) -> Path:
        """Get the extensions directory path."""
        # Try to use app data directory
        app_dir = Path.home() / ".py_rme_canary"
        return app_dir / "extensions"

    def set_extensions(self, extensions: list[MaterialExtension]):
        """Update the list of extensions."""
        self._extensions = extensions
        self._populate_extensions()

    @staticmethod
    def show_extensions(parent=None, extensions: list[MaterialExtension] | None = None):
        """Static helper to show the extensions dialog."""
        # Add some sample extensions for demo if none provided
        if extensions is None:
            extensions = [
                MaterialExtension(
                    name="Sample Extension",
                    author="PyRME Team",
                    description="A sample material extension for demonstration.",
                    version_string="7.40 - 12.00",
                    url="https://github.com/example/extension",
                    author_url="https://github.com/pyrme",
                ),
                MaterialExtension(
                    name="Custom Doodads Pack",
                    author="Community",
                    description="Additional doodads and decorations for maps.",
                    version_string="10.00+",
                ),
            ]

        dlg = ExtensionsDialog(parent, extensions)
        dlg.exec()
