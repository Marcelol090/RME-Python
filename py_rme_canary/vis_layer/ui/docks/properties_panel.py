"""Properties Panel - inspects and edits tile/item/house properties.

Mirrors C++ properties_window.cpp functionality.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QDockWidget,
    QFormLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.houses import House
    from py_rme_canary.core.data.item import Item, Position
    from py_rme_canary.core.data.spawns import MonsterSpawnArea, NpcSpawnArea
    from py_rme_canary.core.data.tile import Tile
    from py_rme_canary.core.data.zones import Zone


class PropertiesPanel(QDockWidget):
    """Dock widget for inspecting/editing entity properties.

    Displays properties for:
    - Tiles (position, flags, ground item)
    - Items (ID, name, text, count, charges)
    - Houses (name, rent, town, owner)
    - Spawns (creature type, interval, radius)
    - Waypoints (name, position)
    - Zones (name, id)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize properties panel."""
        super().__init__("Properties", parent)

        # Scrollable content area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._content = QWidget()
        self._layout = QFormLayout(self._content)
        self._scroll.setWidget(self._content)

        self.setWidget(self._scroll)

        # Current entity being edited
        self._current_tile: Tile | None = None
        self._current_item: Item | None = None
        self._current_house: House | None = None
        self._current_waypoint: tuple[str, Position] | None = None
        self._current_zone: Zone | None = None
        self._current_monster_spawn: MonsterSpawnArea | None = None
        self._current_npc_spawn: NpcSpawnArea | None = None

        # Form fields (created dynamically)
        self._fields: dict[str, QWidget] = {}

    def show_tile(self, tile: Tile) -> None:
        """Display tile properties."""
        self._current_tile = tile
        self._current_item = None
        self._current_house = None
        self._current_waypoint = None
        self._current_zone = None
        self._current_monster_spawn = None
        self._current_npc_spawn = None

        self.clear()

        self._add_readonly("Position", f"{tile.x}, {tile.y}, {tile.z}")
        self._add_readonly("Ground ID", str(tile.ground.id if tile.ground else "None"))

        # Show flags
        if tile.house_id:
            self._add_readonly("House ID", str(tile.house_id))
        if tile.map_flags:
            self._add_readonly("Map Flags", hex(tile.map_flags))

    def show_item(self, item: Item) -> None:
        """Display item properties."""
        self._current_item = item
        self._current_tile = None
        self._current_house = None
        self._current_waypoint = None
        self._current_zone = None
        self._current_monster_spawn = None
        self._current_npc_spawn = None

        self.clear()

        self._add_readonly("Item ID", str(item.id))

        # Show optional attributes
        if item.client_id:
            self._add_readonly("Client ID", str(item.client_id))
        if item.count:
            self._add_readonly("Count", str(item.count))
        if item.subtype:
            self._add_readonly("Subtype", str(item.subtype))

    def show_house(self, house: House) -> None:
        """Display house properties."""
        self._current_house = house
        self._current_item = None
        self._current_tile = None
        self._current_waypoint = None
        self._current_zone = None
        self._current_monster_spawn = None
        self._current_npc_spawn = None

        self.clear()

        self._add_readonly("House ID", str(house.id))

        # Editable name
        name_edit = QLineEdit()
        name_edit.setText(house.name)
        # Note: Since House is frozen, changes don't persist to the dataclass
        # In real editor, would emit signal for parent to create new House instance
        self._add_field("Name", name_edit)

        # Editable rent
        rent_spin = QSpinBox()
        rent_spin.setRange(0, 1000000)
        rent_spin.setValue(house.rent)
        self._add_field("Rent", rent_spin)

        self._add_readonly("Town ID", str(house.townid))

    def show_waypoint(self, name: str, position: Position) -> None:
        """Display waypoint properties (read-only)."""
        self._current_waypoint = (str(name), position)
        self._current_tile = None
        self._current_item = None
        self._current_house = None
        self._current_zone = None
        self._current_monster_spawn = None
        self._current_npc_spawn = None

        self.clear()

        self._add_readonly("Waypoint", str(name))
        self._add_readonly("Position", f"{int(position.x)}, {int(position.y)}, {int(position.z)}")

    def show_zone(self, zone: Zone) -> None:
        """Display zone properties (read-only)."""
        self._current_zone = zone
        self._current_tile = None
        self._current_item = None
        self._current_house = None
        self._current_waypoint = None
        self._current_monster_spawn = None
        self._current_npc_spawn = None

        self.clear()

        self._add_readonly("Zone ID", str(int(zone.id)))
        self._add_readonly("Name", str(zone.name))

    def show_monster_spawn_area(self, area: MonsterSpawnArea) -> None:
        """Display monster spawn area properties (read-only)."""
        self._current_monster_spawn = area
        self._current_tile = None
        self._current_item = None
        self._current_house = None
        self._current_waypoint = None
        self._current_zone = None
        self._current_npc_spawn = None

        self.clear()

        self._add_readonly("Type", "Monster Spawn")
        self._add_readonly("Center", f"{int(area.center.x)}, {int(area.center.y)}, {int(area.center.z)}")
        self._add_readonly("Radius", str(int(area.radius)))
        self._add_readonly("Entries", str(len(area.monsters)))

    def show_npc_spawn_area(self, area: NpcSpawnArea) -> None:
        """Display NPC spawn area properties (read-only)."""
        self._current_npc_spawn = area
        self._current_tile = None
        self._current_item = None
        self._current_house = None
        self._current_waypoint = None
        self._current_zone = None
        self._current_monster_spawn = None

        self.clear()

        self._add_readonly("Type", "NPC Spawn")
        self._add_readonly("Center", f"{int(area.center.x)}, {int(area.center.y)}, {int(area.center.z)}")
        self._add_readonly("Radius", str(int(area.radius)))
        self._add_readonly("Entries", str(len(area.npcs)))

    def clear(self) -> None:
        """Clear all properties from display."""
        # Remove all widgets from layout
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._fields.clear()
        self._current_tile = None
        self._current_item = None
        self._current_house = None
        self._current_waypoint = None
        self._current_zone = None
        self._current_monster_spawn = None
        self._current_npc_spawn = None

    def get_display_text(self) -> str:
        """Get all displayed text (for testing)."""
        text_parts: list[str] = []

        for row in range(self._layout.rowCount()):
            label_item = self._layout.itemAt(row, QFormLayout.ItemRole.LabelRole)
            field_item = self._layout.itemAt(row, QFormLayout.ItemRole.FieldRole)

            if label_item and label_item.widget():
                label = label_item.widget()
                if isinstance(label, QLabel):
                    text_parts.append(label.text())

            if field_item and field_item.widget():
                field = field_item.widget()
                if isinstance(field, (QLabel, QLineEdit)):
                    text_parts.append(field.text())
                elif isinstance(field, QSpinBox):
                    text_parts.append(str(field.value()))

        return " ".join(text_parts)

    def set_text_value(self, text: str) -> None:
        """Set text field value (for testing)."""
        for field in self._fields.values():
            if isinstance(field, QLineEdit):
                field.setText(text)
                break

    def set_house_name(self, name: str) -> None:
        """Set house name field (for testing)."""
        # Find Name field in the form
        for row in range(self._layout.rowCount()):
            label_item = self._layout.itemAt(row, QFormLayout.ItemRole.LabelRole)
            if label_item and label_item.widget():
                label = label_item.widget()
                if isinstance(label, QLabel) and "Name" in label.text():
                    field_item = self._layout.itemAt(row, QFormLayout.ItemRole.FieldRole)
                    if field_item and isinstance(field_item.widget(), QLineEdit):
                        field_item.widget().setText(name)
                        break

    def _add_readonly(self, label: str, value: str) -> None:
        """Add read-only field."""
        value_label = QLabel(value)
        self._layout.addRow(label + ":", value_label)
        self._fields[label] = value_label

    def _add_field(self, label: str, widget: QWidget) -> None:
        """Add editable field."""
        self._layout.addRow(label + ":", widget)
        self._fields[label] = widget
