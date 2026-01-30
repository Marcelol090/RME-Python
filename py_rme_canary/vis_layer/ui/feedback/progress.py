"""Progress indicator for long operations.

Shows progress bar with cancel option for operations like:
- Map loading/saving
- Find/Replace across map
- Borderize/Randomize
"""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ProgressDialog(QDialog):
    """Progress dialog for long-running operations.

    Features:
    - Animated progress bar
    - Cancel button
    - ETA estimation
    - Indeterminate mode for unknown length

    Signals:
        cancelled: Emitted when user cancels
    """

    cancelled = pyqtSignal()

    def __init__(
        self,
        title: str = "Processing",
        message: str = "Please wait...",
        cancellable: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._cancellable = cancellable
        self._cancelled = False

        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint | Qt.WindowType.WindowTitleHint)

        self._setup_ui(message)
        self._apply_style()

    def _setup_ui(self, message: str) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Message
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("""
            color: #E5E5E7;
            font-size: 14px;
            font-weight: 500;
        """)
        layout.addWidget(self.message_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Status/details
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #A1A1AA; font-size: 12px;")
        layout.addWidget(self.status_label)

        # Cancel button
        if self._cancellable:
            self.cancel_btn = QPushButton("Cancel")
            self.cancel_btn.clicked.connect(self._on_cancel)
            layout.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        self.setStyleSheet("""
            QDialog {
                background: #1E1E2E;
            }
            
            QProgressBar {
                background: #2A2A3E;
                border: none;
                border-radius: 6px;
                height: 12px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8B5CF6, stop:0.5 #EC4899, stop:1 #8B5CF6);
                border-radius: 6px;
            }
            
            QPushButton {
                background: #363650;
                color: #E5E5E7;
                border: 1px solid #52525B;
                border-radius: 6px;
                padding: 8px 24px;
            }
            
            QPushButton:hover {
                background: #404060;
                border-color: #8B5CF6;
            }
        """)

    def set_progress(self, value: int, status: str = "") -> None:
        """Update progress value and status.

        Args:
            value: Progress value (0-100)
            status: Optional status text
        """
        self.progress_bar.setValue(min(100, max(0, value)))
        if status:
            self.status_label.setText(status)

    def set_message(self, message: str) -> None:
        """Update the main message."""
        self.message_label.setText(message)

    def set_indeterminate(self, indeterminate: bool = True) -> None:
        """Set indeterminate mode (unknown progress length)."""
        if indeterminate:
            self.progress_bar.setMaximum(0)  # Makes it indeterminate
        else:
            self.progress_bar.setMaximum(100)

    def is_cancelled(self) -> bool:
        """Check if user has cancelled."""
        return self._cancelled

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self._cancelled = True
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setText("Cancelling...")
        self.cancelled.emit()

    def close_on_complete(self, delay_ms: int = 500) -> None:
        """Close dialog after a short delay.

        Args:
            delay_ms: Delay before closing
        """
        self.progress_bar.setValue(100)
        self.status_label.setText("Complete!")
        if hasattr(self, "cancel_btn"):
            self.cancel_btn.hide()
        QTimer.singleShot(delay_ms, self.accept)


class ProgressContext:
    """Context manager for progress dialogs.

    Usage:
        with ProgressContext("Loading Map", parent=self) as progress:
            for i, item in enumerate(items):
                if progress.is_cancelled():
                    break
                progress.update(i * 100 // total, f"Item {i}")
                process(item)
    """

    def __init__(
        self,
        title: str = "Processing",
        message: str = "Please wait...",
        parent: QWidget | None = None,
        cancellable: bool = True,
    ) -> None:
        self._dialog = ProgressDialog(title=title, message=message, cancellable=cancellable, parent=parent)

    def __enter__(self) -> ProgressContext:
        self._dialog.show()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        if exc_type is None:
            self._dialog.close_on_complete()
        else:
            self._dialog.accept()

    def update(self, value: int, status: str = "") -> None:
        """Update progress."""
        self._dialog.set_progress(value, status)
        # Process events to keep UI responsive
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            app.processEvents()

    def is_cancelled(self) -> bool:
        """Check if cancelled."""
        return self._dialog.is_cancelled()

    def set_message(self, message: str) -> None:
        """Update message."""
        self._dialog.set_message(message)


def run_with_progress(
    title: str, items: list, process_item: Callable[[object, int, int], None], parent: QWidget | None = None
) -> bool:
    """Run a batch operation with progress dialog.

    Args:
        title: Dialog title
        items: List of items to process
        process_item: Function taking (item, index, total)
        parent: Parent widget

    Returns:
        True if completed, False if cancelled
    """
    total = len(items)
    if total == 0:
        return True

    with ProgressContext(title, f"Processing {total} items...", parent) as progress:
        for i, item in enumerate(items):
            if progress.is_cancelled():
                return False

            progress.update((i + 1) * 100 // total, f"Item {i + 1} of {total}")
            process_item(item, i, total)

    return True
