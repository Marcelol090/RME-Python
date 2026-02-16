"""Zone and Town Management Dialogs.

Modern dialogs for:
- Zone creation/editing
- Town management
- Temple position settings
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
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


class ColorButton(QPushButton):
    """Button that shows and allows selecting a color."""

    color_changed = pyqtSignal(QColor)

    def __init__(self, color: QColor | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        if color is None:
            color = QColor(139, 92, 246)

        self._color = color
        self.setFixedSize(60, 30)
        self.clicked.connect(self._pick_color)
        self._update_style()

    def _update_style(self) -> None:
        """Update button appearance."""
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.setStyleSheet(
            f"""
            ColorButton {{
                background: {self._color.name()};
                border: 2px solid {c['border']['default']};
                border-radius: {r['sm']}px;
            }}
            ColorButton:hover {{
                border-color: {c['brand']['primary']};
            }}
        """
        )

    def _pick_color(self) -> None:
        """Open color picker."""
        color = QColorDialog.getColor(self._color, self.parentWidget(), "Select Color")
        if color.isValid():
            self._color = color
            self._update_style()
            self.color_changed.emit(color)

    def color(self) -> QColor:
        """Get current color."""
        return self._color

    def set_color(self, color: QColor) -> None:
        """Set current color."""
        self._color = color
        self._update_style()


class ZoneListDialog(ModernDialog):
    """Dialog for managing map zones.

    Zones are named areas with associated colors for visualization.
    """

    zone_selected = pyqtSignal(str)

    def __init__(self, game_map: GameMap | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent, title="Zone Manager")

        self._game_map = game_map

        self.setMinimumSize(400, 400)

        self._init_content()
        self._apply_style()
        self._load_zones()

    def _init_content(self) -> None:
        """Initialize UI components."""
        layout = self.content_layout
        layout.setSpacing(12)

        # Zone list
        self.zone_list = QListWidget()
        self.zone_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.zone_list.itemDoubleClicked.connect(self._on_edit)
        layout.addWidget(self.zone_list)

        # Footer Buttons
        self.add_spacer_to_footer()

        self.btn_delete = self.add_button("Delete", callback=self._on_delete, role="secondary")
        self.btn_delete.setEnabled(False)

        self.btn_edit = self.add_button("Edit", callback=self._on_edit, role="secondary")
        self.btn_edit.setEnabled(False)

        self.btn_add = self.add_button("New Zone", callback=self._on_add, role="primary")

    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.content_area.setStyleSheet(
            f"""
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

    def _load_zones(self) -> None:
        """Load zones from map."""
        self.zone_list.clear()

        if not self._game_map:
            return

        zones = getattr(self._game_map, "zones", {}) or {}

        for zone_id, zone in sorted(zones.items()):
            # Create colored indicator
            color = getattr(zone, "color", None)
            color_text = "● " if color else "○ "

            name = getattr(zone, "name", zone_id) or zone_id
            text = f"{color_text}{name}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, zone_id)
            self.zone_list.addItem(item)

        if self.zone_list.count() == 0:
            item = QListWidgetItem("No zones defined")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.zone_list.addItem(item)

    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        has_selection = len(self.zone_list.selectedItems()) > 0

        if has_selection:
            item = self.zone_list.currentItem()
            has_selection = item and item.data(Qt.ItemDataRole.UserRole) is not None

        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

    def _on_add(self) -> None:
        """Create new zone."""
        dialog = ZoneEditDialog(parent=self)
        if dialog.exec():
            values = dialog.get_values()
            name = values.get("name", "")

            if not name:
                return

            # Create zone
            if not self._game_map:
                return

            if not hasattr(self._game_map, "zones") or self._game_map.zones is None:
                self._game_map.zones = {}

            # Find unique ID
            zone_id = name.lower().replace(" ", "_")

            # Store zone (simplified - would need Zone class)
            self._game_map.zones[zone_id] = {"name": name, "color": values.get("color", "#8B5CF6")}

            self._load_zones()

    def _on_edit(self) -> None:
        """Edit selected zone."""
        item = self.zone_list.currentItem()
        if not item:
            return

        zone_id = item.data(Qt.ItemDataRole.UserRole)
        if not zone_id or not self._game_map:
            return

        zones = getattr(self._game_map, "zones", {}) or {}
        zone = zones.get(zone_id)

        if zone:
            dialog = ZoneEditDialog(zone=zone, parent=self)
            if dialog.exec():
                values = dialog.get_values()
                zones[zone_id] = values
                self._load_zones()

    def _on_delete(self) -> None:
        """Delete selected zone."""
        item = self.zone_list.currentItem()
        if not item:
            return

        zone_id = item.data(Qt.ItemDataRole.UserRole)
        if not zone_id or not self._game_map:
            return

        reply = QMessageBox.question(
            self,
            "Delete Zone",
            f"Delete zone '{zone_id}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            zones = getattr(self._game_map, "zones", {}) or {}
            if zone_id in zones:
                del zones[zone_id]
                self._load_zones()


class ZoneEditDialog(ModernDialog):
    """Dialog for editing zone properties."""

    def __init__(self, zone: object | None = None, parent: QWidget | None = None) -> None:
        self._zone = zone
        self._is_new = zone is None

        super().__init__(parent, title="New Zone" if self._is_new else "Edit Zone")

        self.setMinimumWidth(300)

        self._init_content()
        self._apply_style()

    def _init_content(self) -> None:
        """Initialize UI."""
        layout = self.content_layout
        layout.setSpacing(16)

        # Form
        form = QFormLayout()
        form.setSpacing(12)

        # Name
        name = ""
        if self._zone:
            name = getattr(self._zone, "name", "") or (
                self._zone.get("name", "") if isinstance(self._zone, dict) else ""
            )
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("Zone name...")
        form.addRow("Name:", self.name_input)

        # Color
        color = QColor(139, 92, 246)
        if self._zone:
            color_str = getattr(self._zone, "color", None) or (
                self._zone.get("color", None) if isinstance(self._zone, dict) else None
            )
            if color_str:
                color = QColor(color_str)

        self.color_btn = ColorButton(color)
        form.addRow("Color:", self.color_btn)

        layout.addLayout(form)

        # Buttons
        self.add_spacer_to_footer()
        self.add_button("Cancel", callback=self.reject, role="secondary")
        self.add_button("Ok", callback=self.accept, role="primary")

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
                padding: 8px;
                color: {c["text"]["primary"]};
            }}

            QLineEdit:focus {{
                border-color: {c["brand"]["primary"]};
            }}

            QLabel {{
                color: {c["text"]["secondary"]};
            }}
        """
        )

    def get_values(self) -> dict:
        """Get entered values."""
        return {"name": self.name_input.text().strip(), "color": self.color_btn.color().name()}


class TownListDialog(ModernDialog):
    """Dialog for managing map towns.

    Towns have temple positions for player respawning.
    """

    goto_position = pyqtSignal(int, int, int)

    def __init__(
        self,
        game_map: GameMap | None = None,
        current_pos: tuple[int, int, int] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent, title="Town Manager")

        self._game_map = game_map
        self._current_pos = current_pos or (0, 0, 7)

        self.setMinimumSize(450, 400)

        self._init_content()
        self._apply_style()
        self._load_towns()

    def _init_content(self) -> None:
        """Initialize UI components."""
        tm = get_theme_manager()
        c = tm.tokens["color"]

        layout = self.content_layout
        layout.setSpacing(12)

        # Town list
        self.town_list = QListWidget()
        self.town_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.town_list.itemDoubleClicked.connect(self._on_goto_temple)
        layout.addWidget(self.town_list)

        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        self.btn_add = QPushButton("New Town")
        self.btn_add.clicked.connect(self._on_add)
        action_layout.addWidget(self.btn_add)

        self.btn_goto = QPushButton("Go To Temple")
        self.btn_goto.setEnabled(False)
        self.btn_goto.clicked.connect(self._on_goto_temple)
        action_layout.addWidget(self.btn_goto)

        self.btn_set_temple = QPushButton("Set Temple Here")
        self.btn_set_temple.setEnabled(False)
        self.btn_set_temple.clicked.connect(self._on_set_temple)
        action_layout.addWidget(self.btn_set_temple)

        self.btn_delete = QPushButton("Delete")
        self.btn_delete.setFixedWidth(72)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete)
        action_layout.addWidget(self.btn_delete)

        layout.addLayout(action_layout)

        # Current position
        pos_label = QLabel(f"Current: ({self._current_pos[0]}, {self._current_pos[1]}, {self._current_pos[2]})")
        pos_label.setStyleSheet(f"color: {c['text']['secondary']}; font-size: 11px;")
        layout.addWidget(pos_label)

        # Footer Buttons
        self.add_spacer_to_footer()
        self.add_button("Close", callback=self.accept, role="secondary")

    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.content_area.setStyleSheet(
            f"""
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
                padding: 8px 12px;
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

    def _load_towns(self) -> None:
        """Load towns from map."""
        self.town_list.clear()

        if not self._game_map:
            return

        towns = getattr(self._game_map, "towns", {}) or {}

        for town_id, town in sorted(towns.items()):
            name = getattr(town, "name", f"Town {town_id}") or f"Town {town_id}"
            temple = getattr(town, "temple_position", None)

            temple_text = f"({int(temple.x)}, {int(temple.y)}, {int(temple.z)})" if temple else "Temple not set"

            text = f"{name}\n    ID: {town_id} | {temple_text}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, {"id": town_id, "name": name, "temple": temple})
            self.town_list.addItem(item)

        if self.town_list.count() == 0:
            item = QListWidgetItem("No towns defined")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.town_list.addItem(item)

    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        item = self.town_list.currentItem()
        has_selection = item and item.data(Qt.ItemDataRole.UserRole) is not None

        self.btn_goto.setEnabled(has_selection)
        self.btn_set_temple.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

        # Check if temple is set
        if has_selection:
            data = item.data(Qt.ItemDataRole.UserRole)
            self.btn_goto.setEnabled(data.get("temple") is not None)

    def _on_add(self) -> None:
        """Create new town."""
        name, ok = QInputDialog.getText(self, "New Town", "Town name:")

        if not ok or not name:
            return

        if not self._game_map:
            return

        towns = getattr(self._game_map, "towns", {}) or {}

        # Find next ID
        next_id = max([int(k) for k in towns], default=0) + 1

        x, y, z = self._current_pos
        self._upsert_town(
            town_id=int(next_id),
            name=str(name).strip(),
            x=int(x),
            y=int(y),
            z=int(z),
        )
        self._load_towns()

    def _on_goto_temple(self) -> None:
        """Navigate to selected town's temple."""
        item = self.town_list.currentItem()
        if not item:
            return

        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        temple = data.get("temple")
        if temple:
            self.goto_position.emit(int(temple.x), int(temple.y), int(temple.z))

    def _on_set_temple(self) -> None:
        """Set current position as town temple."""
        item = self.town_list.currentItem()
        if not item or not self._game_map:
            return

        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        town_id = data.get("id")
        towns = getattr(self._game_map, "towns", {}) or {}
        town = towns.get(town_id)

        if town is None:
            return

        self._set_town_temple(
            town_id=int(town_id),
            x=int(self._current_pos[0]),
            y=int(self._current_pos[1]),
            z=int(self._current_pos[2]),
        )
        self._load_towns()

    def _on_delete(self) -> None:
        """Delete selected town."""
        item = self.town_list.currentItem()
        if not item or not self._game_map:
            return

        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return

        town_id = data.get("id")
        name = data.get("name", f"Town {town_id}")

        reply = QMessageBox.question(
            self,
            "Delete Town",
            f"Delete town '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self._town_has_linked_houses(int(town_id)):
                QMessageBox.warning(
                    self,
                    "Delete Town",
                    "You cannot delete a town that still has houses associated with it.",
                )
                return

            self._delete_town(int(town_id))
            self._load_towns()

    def _town_has_linked_houses(self, town_id: int) -> bool:
        houses = getattr(self._game_map, "houses", {}) if self._game_map is not None else {}
        return any(int(getattr(house, "townid", 0) or 0) == int(town_id) for house in (houses or {}).values())

    def _session(self):
        parent = self.parent()
        return getattr(parent, "session", None)

    def _upsert_town(self, *, town_id: int, name: str, x: int, y: int, z: int) -> None:
        session = self._session()
        if session is not None and hasattr(session, "upsert_town"):
            with contextlib.suppress(Exception):
                session.upsert_town(
                    town_id=int(town_id),
                    name=str(name),
                    temple_x=int(x),
                    temple_y=int(y),
                    temple_z=int(z),
                )
                self._refresh_parent_after_change()
                return

        if self._game_map is None:
            return
        from py_rme_canary.core.data.item import Position
        from py_rme_canary.core.data.towns import Town

        self._game_map.towns[int(town_id)] = Town(
            id=int(town_id),
            name=str(name),
            temple_position=Position(x=int(x), y=int(y), z=int(z)),
        )
        self._refresh_parent_after_change()

    def _set_town_temple(self, *, town_id: int, x: int, y: int, z: int) -> None:
        session = self._session()
        if session is not None and hasattr(session, "set_town_temple_position"):
            with contextlib.suppress(Exception):
                session.set_town_temple_position(town_id=int(town_id), x=int(x), y=int(y), z=int(z))
                self._refresh_parent_after_change()
                return

        if self._game_map is None:
            return
        current = (self._game_map.towns or {}).get(int(town_id))
        if current is None:
            return
        from py_rme_canary.core.data.item import Position
        from py_rme_canary.core.data.towns import Town

        self._game_map.towns[int(town_id)] = Town(
            id=int(current.id),
            name=str(current.name),
            temple_position=Position(x=int(x), y=int(y), z=int(z)),
        )
        self._refresh_parent_after_change()

    def _delete_town(self, town_id: int) -> None:
        session = self._session()
        if session is not None and hasattr(session, "delete_town"):
            with contextlib.suppress(Exception):
                session.delete_town(town_id=int(town_id))
                self._refresh_parent_after_change()
                return

        towns = getattr(self._game_map, "towns", {}) if self._game_map is not None else {}
        if int(town_id) in (towns or {}):
            towns = getattr(self._game_map, "towns", {}) or {}
            del towns[int(town_id)]
            self._refresh_parent_after_change()

    def _refresh_parent_after_change(self) -> None:
        parent = self.parent()
        if parent is None:
            return
        with contextlib.suppress(Exception):
            parent.canvas.update()
        with contextlib.suppress(Exception):
            parent._set_dirty(True)
