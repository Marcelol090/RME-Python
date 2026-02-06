"""Auto-Updater Dialog.

Dialog for checking and applying application updates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


# Application version
__version__ = "0.1.0-canary"


class UpdateChecker(QThread):
    """Worker thread for checking updates."""

    progress = pyqtSignal(str)  # status message
    finished = pyqtSignal(dict)  # result dict

    def __init__(self, current_version: str) -> None:
        super().__init__()
        self._current = current_version

    def run(self) -> None:
        """Check for updates."""
        import json
        import urllib.request

        self.progress.emit("Connecting to update server...")

        try:
            # GitHub releases API (placeholder URL)
            url = "https://api.github.com/repos/Marcelol090/RME-Python/releases/latest"

            req = urllib.request.Request(url)
            req.add_header("Accept", "application/vnd.github.v3+json")
            req.add_header("User-Agent", f"PyRME-Canary/{self._current}")

            self.progress.emit("Checking latest version...")

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            latest_version = data.get("tag_name", "").lstrip("v")
            release_notes = data.get("body", "No release notes available.")
            download_url = ""

            # Find appropriate asset
            for asset in data.get("assets", []):
                name = asset.get("name", "")
                if "windows" in name.lower() or name.endswith(".exe"):
                    download_url = asset.get("browser_download_url", "")
                    break

            self.progress.emit("Check complete")

            self.finished.emit(
                {
                    "success": True,
                    "current": self._current,
                    "latest": latest_version,
                    "notes": release_notes,
                    "download_url": download_url,
                    "update_available": latest_version > self._current,
                }
            )

        except Exception as e:
            self.finished.emit(
                {
                    "success": False,
                    "error": str(e),
                    "current": self._current,
                }
            )


class UpdateDialog(QDialog):
    """Dialog for checking and applying updates.

    Usage:
        dialog = UpdateDialog(parent)
        dialog.exec()
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._worker: UpdateChecker | None = None
        self._download_url = ""

        self.setWindowTitle("Check for Updates")
        self.setModal(True)
        self.resize(500, 350)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        icon = QLabel("UPD")
        icon.setStyleSheet("font-size: 20px; font-weight: 700; color: #8B5CF6;")
        header_layout.addWidget(icon)

        title_layout = QVBoxLayout()
        title = QLabel("PyRME Canary Updates")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #E5E5E7;")
        title_layout.addWidget(title)

        self._version_label = QLabel(f"Current version: {__version__}")
        self._version_label.setStyleSheet("color: #9CA3AF;")
        title_layout.addWidget(self._version_label)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Status
        self._status = QLabel("Click 'Check for Updates' to begin")
        self._status.setStyleSheet("color: #9CA3AF;")
        layout.addWidget(self._status)

        # Progress
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # Indeterminate
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        # Release notes
        self._notes_label = QLabel("Release Notes:")
        self._notes_label.setStyleSheet("color: #9CA3AF; font-weight: bold;")
        self._notes_label.setVisible(False)
        layout.addWidget(self._notes_label)

        self._notes = QTextEdit()
        self._notes.setReadOnly(True)
        self._notes.setVisible(False)
        self._notes.setMaximumHeight(150)
        layout.addWidget(self._notes)

        # Buttons
        button_layout = QHBoxLayout()

        self._check_btn = QPushButton("Check for Updates")
        self._check_btn.clicked.connect(self._check_updates)
        button_layout.addWidget(self._check_btn)

        self._download_btn = QPushButton("Download Update")
        self._download_btn.clicked.connect(self._download_update)
        self._download_btn.setVisible(False)
        button_layout.addWidget(self._download_btn)

        button_layout.addStretch()

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)

    def _apply_style(self) -> None:
        """Apply modern styling."""
        self.setStyleSheet(
            """
            QDialog {
                background: #1E1E2E;
                color: #E5E5E7;
            }

            QTextEdit {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 6px;
                color: #E5E5E7;
                padding: 8px;
            }

            QProgressBar {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 4px;
                text-align: center;
            }

            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B5CF6, stop:1 #A78BFA);
            }

            QPushButton {
                background: #8B5CF6;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
            }

            QPushButton:hover {
                background: #7C3AED;
            }

            QPushButton:disabled {
                background: #4B5563;
            }
        """
        )

    def _check_updates(self) -> None:
        """Start checking for updates."""
        self._check_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._download_btn.setVisible(False)
        self._notes_label.setVisible(False)
        self._notes.setVisible(False)

        self._worker = UpdateChecker(__version__)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, message: str) -> None:
        """Handle progress update."""
        self._status.setText(message)

    def _on_finished(self, result: dict) -> None:
        """Handle check complete."""
        self._check_btn.setEnabled(True)
        self._progress.setVisible(False)

        if not result.get("success"):
            self._status.setText(f"Error: {result.get('error', 'Unknown error')}")
            self._status.setStyleSheet("color: #EF4444;")
            return

        if result.get("update_available"):
            latest = result.get("latest", "?")
            self._status.setText(f"New version available: {latest}")
            self._status.setStyleSheet("color: #22C55E;")

            self._download_url = result.get("download_url", "")
            if self._download_url:
                self._download_btn.setVisible(True)

            # Show release notes
            notes = result.get("notes", "")
            if notes:
                self._notes_label.setVisible(True)
                self._notes.setVisible(True)
                self._notes.setPlainText(notes)
        else:
            self._status.setText("You are running the latest version!")
            self._status.setStyleSheet("color: #22C55E;")

    def _download_update(self) -> None:
        """Open download URL in browser."""
        if self._download_url:
            import webbrowser

            webbrowser.open(self._download_url)
