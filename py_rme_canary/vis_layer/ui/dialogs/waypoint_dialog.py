"""Waypoint Management Dialog.

Modern dialog for waypoint operations:
- List all waypoints
- Create/edit/delete waypoints
- Navigation to waypoint
- Search and filtering
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


class WaypointListDialog(QDialog):
    """Dialog for managing map waypoints.

    Signals:
        waypoint_selected: Emits (name, x, y, z) when user navigates to waypoint
    """

    waypoint_selected = pyqtSignal(str, int, int, int)

    def __init__(
        self,
        game_map: GameMap | None = None,
        current_pos: tuple[int, int, int] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._game_map = game_map
        self._current_pos = current_pos or (0, 0, 7)

        self.setWindowTitle("Waypoint Manager")
        self.setMinimumSize(450, 400)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()
        self._load_waypoints()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Waypoints")
        header.setStyleSheet(
            """
            font-size: 18px;
            font-weight: 700;
            color: #E5E5E7;
        """
        )
        layout.addWidget(header)

        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search waypoints...")
        self.search.textChanged.connect(self._filter_list)
        layout.addWidget(self.search)

        # Waypoint list
        self.waypoint_list = QListWidget()
        self.waypoint_list.itemDoubleClicked.connect(self._on_goto)
        self.waypoint_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.waypoint_list)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        self.btn_goto = QPushButton("Go To")
        self.btn_goto.setEnabled(False)
        self.btn_goto.clicked.connect(self._on_goto)
        action_layout.addWidget(self.btn_goto)

        self.btn_add = QPushButton("Add Here")
        self.btn_add.clicked.connect(self._on_add)
        action_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("Rename")
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._on_rename)
        action_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete)
        action_layout.addWidget(self.btn_delete)

        layout.addLayout(action_layout)

        # Current position info
        pos_label = QLabel(f"Current: ({self._current_pos[0]}, {self._current_pos[1]}, {self._current_pos[2]})")
        pos_label.setStyleSheet("color: #52525B; font-size: 11px;")
        layout.addWidget(pos_label)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)

    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        self.setStyleSheet(
            """
            QDialog {
                background: #1E1E2E;
            }

            QLineEdit {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 8px;
                padding: 10px 14px;
                color: #E5E5E7;
            }

            QLineEdit:focus {
                border-color: #8B5CF6;
            }

            QListWidget {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 8px;
                color: #E5E5E7;
                outline: none;
            }

            QListWidget::item {
                padding: 10px 12px;
                border-radius: 6px;
                margin: 2px 4px;
            }

            QListWidget::item:hover {
                background: #363650;
            }

            QListWidget::item:selected {
                background: #8B5CF6;
            }

            QPushButton {
                background: #363650;
                color: #E5E5E7;
                border: 1px solid #52525B;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }

            QPushButton:hover {
                background: #404060;
                border-color: #8B5CF6;
            }

            QPushButton:disabled {
                background: #2A2A3E;
                color: #52525B;
                border-color: #363650;
            }
        """
        )

    def _load_waypoints(self) -> None:
        """Load waypoints from map."""
        self.waypoint_list.clear()

        if not self._game_map:
            return

        waypoints = getattr(self._game_map, "waypoints", {}) or {}

        for name, pos in sorted(waypoints.items()):
            text = str(name)
            subtitle = f"({int(pos.x)}, {int(pos.y)}, {int(pos.z)})"

            item = QListWidgetItem(f"{text}\n    {subtitle}")
            item.setData(Qt.ItemDataRole.UserRole, {"name": name, "x": int(pos.x), "y": int(pos.y), "z": int(pos.z)})
            self.waypoint_list.addItem(item)

        if self.waypoint_list.count() == 0:
            item = QListWidgetItem("No waypoints defined")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(Qt.GlobalColor.gray)
            self.waypoint_list.addItem(item)

    def _filter_list(self, text: str) -> None:
        """Filter waypoint list by search text."""
        text_lower = text.lower()

        for i in range(self.waypoint_list.count()):
            item = self.waypoint_list.item(i)
            if item:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data:
                    visible = text_lower in data.get("name", "").lower()
                    item.setHidden(not visible)
                else:
                    item.setHidden(bool(text))

    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        has_selection = len(self.waypoint_list.selectedItems()) > 0

        # Check if valid waypoint selected
        if has_selection:
            item = self.waypoint_list.currentItem()
            has_selection = item and item.data(Qt.ItemDataRole.UserRole) is not None

        self.btn_goto.setEnabled(has_selection)
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

    def _on_goto(self) -> None:
        """Navigate to selected waypoint."""
        item = self.waypoint_list.currentItem()
        if not item:
            return

        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.waypoint_selected.emit(data["name"], data["x"], data["y"], data["z"])

    def _on_add(self) -> None:
        """Add new waypoint at current position."""
        name, ok = QInputDialog.getText(self, "Add Waypoint", "Waypoint name:", text="")

        if ok and name and self._game_map:
            # Check for duplicates
            waypoints = getattr(self._game_map, "waypoints", {}) or {}
            if name in waypoints:
                QMessageBox.warning(self, "Duplicate", f"A waypoint named '{name}' already exists.")
                return

            # Add waypoint (would need Position class)
            from py_rme_canary.core.data.position import Position

            if not hasattr(self._game_map, "waypoints") or self._game_map.waypoints is None:
                self._game_map.waypoints = {}

            self._game_map.waypoints[name] = Position(
                x=self._current_pos[0], y=self._current_pos[1], z=self._current_pos[2]
            )

            self._load_waypoints()

    def _on_rename(self) -> None:
        """Rename selected waypoint."""
        item = self.waypoint_list.currentItem()
        if not item:
            return

        data = item.data(Qt.ItemDataRole.UserRole)
        if not data or not self._game_map:
            return

        old_name = data["name"]

        new_name, ok = QInputDialog.getText(self, "Rename Waypoint", "New name:", text=old_name)

        if ok and new_name and new_name != old_name:
            waypoints = getattr(self._game_map, "waypoints", {}) or {}

            if new_name in waypoints:
                QMessageBox.warning(self, "Duplicate", f"A waypoint named '{new_name}' already exists.")
                return

            # Rename
            if old_name in waypoints:
                pos = waypoints.pop(old_name)
                waypoints[new_name] = pos
                self._load_waypoints()

    def _on_delete(self) -> None:
        """Delete selected waypoint."""
        item = self.waypoint_list.currentItem()
        if not item:
            return

        data = item.data(Qt.ItemDataRole.UserRole)
        if not data or not self._game_map:
            return

        name = data["name"]

        reply = QMessageBox.question(
            self,
            "Delete Waypoint",
            f"Delete waypoint '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            waypoints = getattr(self._game_map, "waypoints", {}) or {}
            if name in waypoints:
                del waypoints[name]
                self._load_waypoints()


class WaypointQuickAdd(QDialog):
    """Quick dialog to add waypoint at position."""

    def __init__(self, position: tuple[int, int, int], parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._position = position

        self.setWindowTitle("Add Waypoint")
        self.setFixedWidth(300)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Position info
        pos_label = QLabel(f"Position: ({self._position[0]}, {self._position[1]}, {self._position[2]})")
        pos_label.setStyleSheet("color: #A1A1AA;")
        layout.addWidget(pos_label)

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Waypoint name...")
        layout.addWidget(self.name_input)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.name_input.setFocus()

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet(
            """
            QDialog {
                background: #1E1E2E;
            }

            QLineEdit {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 8px;
                padding: 10px;
                color: #E5E5E7;
            }

            QLineEdit:focus {
                border-color: #8B5CF6;
            }
        """
        )

    def get_name(self) -> str:
        """Get entered waypoint name."""
        return self.name_input.text().strip()
