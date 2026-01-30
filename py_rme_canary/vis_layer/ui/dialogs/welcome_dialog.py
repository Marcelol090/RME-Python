"""Welcome Dialog - First-run experience.

Modern welcome dialog with:
- Quick actions (New, Open, Recent)
- Recent files list
- Example maps
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ActionCard(QFrame):
    """Clickable action card for welcome screen."""

    clicked = pyqtSignal()

    def __init__(self, icon: str, title: str, description: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui(icon, title, description)
        self._apply_style()

    def _setup_ui(self, icon: str, title: str, description: str) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 32px;")
        layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #E5E5E7;
        """)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 11px; color: #A1A1AA;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet("""
            ActionCard {
                background: #2A2A3E;
                border: 2px solid #363650;
                border-radius: 12px;
            }
            ActionCard:hover {
                background: #363650;
                border-color: #8B5CF6;
            }
        """)

    def mousePressEvent(self, event: object) -> None:
        """Emit clicked signal."""
        self.clicked.emit()
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
        self, recent_files: list[str] | list[tuple[str, str]] | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._recent_files = recent_files or []

        self.setWindowTitle("Welcome")
        self.setMinimumSize(700, 500)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QHBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Left side: Actions
        left_panel = QWidget()
        left_panel.setStyleSheet("background: #1E1E2E;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)
        left_layout.setContentsMargins(32, 32, 32, 32)

        # Header
        header = QLabel("🗺️ py_rme_canary")
        header.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #E5E5E7;
        """)
        left_layout.addWidget(header)

        subtitle = QLabel("Modern Map Editor for Open Tibia")
        subtitle.setStyleSheet("font-size: 12px; color: #8B5CF6;")
        left_layout.addWidget(subtitle)

        left_layout.addSpacing(24)

        # Quick Start label
        qs_label = QLabel("Quick Start")
        qs_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #A1A1AA;
        """)
        left_layout.addWidget(qs_label)

        # Action cards
        new_card = ActionCard("📄", "New Map", "Create a blank map with custom dimensions")
        new_card.clicked.connect(self._on_new)
        left_layout.addWidget(new_card)

        open_card = ActionCard("📂", "Open Map", "Open an existing .otbm map file")
        open_card.clicked.connect(self._on_open)
        left_layout.addWidget(open_card)

        left_layout.addStretch()

        # Footer
        footer = QLabel("Version 1.0.0-alpha")
        footer.setStyleSheet("font-size: 10px; color: #52525B;")
        left_layout.addWidget(footer)

        layout.addWidget(left_panel, stretch=1)

        # Right side: Recent files
        right_panel = QWidget()
        right_panel.setStyleSheet("background: #2A2A3E;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(12)
        right_layout.setContentsMargins(24, 32, 24, 24)

        # Recent header
        recent_header = QLabel("Recent Files")
        recent_header.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #E5E5E7;
        """)
        right_layout.addWidget(recent_header)

        # Recent files list
        self.recent_list = QListWidget()
        self.recent_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: #363650;
                border-radius: 8px;
                padding: 12px;
                margin: 4px 0;
                color: #E5E5E7;
            }
            QListWidget::item:hover {
                background: #404060;
            }
            QListWidget::item:selected {
                background: #8B5CF6;
            }
        """)
        self.recent_list.itemDoubleClicked.connect(self._on_recent_selected)

        # Populate recent files
        if self._recent_files:
            for entry in self._recent_files[:10]:
                # Support both (path, label) tuples and plain paths
                if isinstance(entry, (list, tuple)) and len(entry) >= 1:
                    path = entry[0]
                    filename = entry[1] if len(entry) > 1 else None
                else:
                    path = str(entry)
                    filename = None

                import os

                filename = filename or os.path.basename(path)
                item = QListWidgetItem(f"📄 {filename}")
                item.setData(Qt.ItemDataRole.UserRole, path)
                item.setToolTip(path)
                self.recent_list.addItem(item)
        else:
            empty_label = QLabel("No recent files")
            empty_label.setStyleSheet("color: #52525B; padding: 20px;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            right_layout.addWidget(empty_label)

        right_layout.addWidget(self.recent_list)

        layout.addWidget(right_panel, stretch=1)

    def _apply_style(self) -> None:
        """Apply overall styling."""
        self.setStyleSheet("""
            QDialog {
                background: #1E1E2E;
            }
        """)

    def _on_new(self) -> None:
        """Handle new map action."""
        self.new_map_requested.emit()
        self.accept()

    def _on_open(self) -> None:
        """Handle open map action."""
        self.open_map_requested.emit()
        self.accept()

    def _on_recent_selected(self, item: QListWidgetItem) -> None:
        """Handle recent file selection."""
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.recent_file_selected.emit(path)
            self.accept()
