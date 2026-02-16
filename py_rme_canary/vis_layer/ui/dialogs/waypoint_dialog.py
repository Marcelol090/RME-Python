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

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


class WaypointListDialog(ModernDialog):
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
        super().__init__(parent, title="Waypoint Manager")

        self._game_map = game_map
        self._current_pos = current_pos or (0, 0, 7)

        self.setMinimumSize(450, 400)

        self._init_content()
        self._apply_style()
        self._load_waypoints()

    def _init_content(self) -> None:
        """Initialize UI components."""
        tm = get_theme_manager()
        c = tm.tokens["color"]

        layout = self.content_layout
        layout.setSpacing(12)

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

        # Action buttons (bottom row inside content)
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
        pos_label.setStyleSheet(f"color: {c['text']['secondary']}; font-size: 11px;")
        layout.addWidget(pos_label)

    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.content_area.setStyleSheet(
            f"""
            QLineEdit {{
                background: {c["surface"]["secondary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["md"]}px;
                padding: 10px 14px;
                color: {c["text"]["primary"]};
            }}

            QLineEdit:focus {{
                border-color: {c["brand"]["primary"]};
            }}

            QListWidget {{
                background: {c["surface"]["secondary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["md"]}px;
                color: {c["text"]["primary"]};
                outline: none;
            }}

            QListWidget::item {{
                padding: 10px 12px;
                border-radius: {r["sm"]}px;
                margin: 2px 4px;
            }}

            QListWidget::item:hover {{
                background: {c["state"]["hover"]};
            }}

            QListWidget::item:selected {{
                background: {c["brand"]["primary"]};
                color: {c["surface"]["primary"]};
            }}

            QPushButton {{
                background: {c["surface"]["tertiary"]};
                color: {c["text"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["sm"]}px;
                padding: 8px 16px;
                font-size: 12px;
            }}

            QPushButton:hover {{
                background: {c["brand"]["primary"]};
                color: {c["surface"]["primary"]};
            }}

            QPushButton:disabled {{
                background: {c["surface"]["primary"]};
                color: {c["text"]["disabled"]};
                border-color: {c["border"]["default"]};
            }}
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


class WaypointQuickAdd(ModernDialog):
    """Quick dialog to add waypoint at position."""

    def __init__(self, position: tuple[int, int, int], parent: QWidget | None = None) -> None:
        self._position = position
        super().__init__(parent, title="Add Waypoint")

        self.setFixedWidth(300)

        self._init_content()
        self._apply_style()

    def _init_content(self) -> None:
        """Initialize UI."""
        tm = get_theme_manager()
        c = tm.tokens["color"]

        layout = self.content_layout
        layout.setSpacing(12)

        # Position info
        pos_label = QLabel(f"Position: ({self._position[0]}, {self._position[1]}, {self._position[2]})")
        pos_label.setStyleSheet(f"color: {c['text']['secondary']};")
        layout.addWidget(pos_label)

        # Name input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Waypoint name...")
        layout.addWidget(self.name_input)

        # Buttons
        self.add_spacer_to_footer()
        self.add_button("Cancel", callback=self.reject, role="secondary")
        self.add_button("Ok", callback=self.accept, role="primary")

        self.name_input.setFocus()

    def _apply_style(self) -> None:
        """Apply styling."""
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.content_area.setStyleSheet(
            f"""
            QLineEdit {{
                background: {c["surface"]["secondary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["sm"]}px;
                padding: 10px;
                color: {c["text"]["primary"]};
            }}

            QLineEdit:focus {{
                border-color: {c["brand"]["primary"]};
            }}
        """
        )

    def get_name(self) -> str:
        """Get entered waypoint name."""
        return self.name_input.text().strip()
