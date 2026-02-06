"""Global Search Dialog.

Universal search across the map for:
- Items (by ID or name)
- Tiles (by properties)
- Houses
- Spawns
- Waypoints
- Zones
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


class SearchType(str, Enum):
    """Types of searchable entities."""

    ITEM = "item"
    TILE = "tile"
    HOUSE = "house"
    SPAWN = "spawn"
    WAYPOINT = "waypoint"
    ZONE = "zone"


@dataclass(slots=True)
class SearchResult:
    """Single search result."""

    result_type: SearchType
    name: str
    description: str
    position: tuple[int, int, int] | None
    entity_id: int | None = None
    metadata: dict | None = None


class SearchWorker(QThread):
    """Background worker for searching the map."""

    progress = pyqtSignal(int)
    result_found = pyqtSignal(SearchResult)
    finished_search = pyqtSignal(int)  # total count

    def __init__(self, game_map: GameMap, query: str, search_types: list[SearchType], parent: object = None) -> None:
        super().__init__(parent)
        self._game_map = game_map
        self._query = query.lower()
        self._search_types = search_types
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel the search."""
        self._cancelled = True

    def run(self) -> None:
        """Execute the search."""
        count = 0

        if SearchType.WAYPOINT in self._search_types:
            count += self._search_waypoints()

        if SearchType.HOUSE in self._search_types:
            count += self._search_houses()

        if SearchType.ZONE in self._search_types:
            count += self._search_zones()

        if SearchType.SPAWN in self._search_types:
            count += self._search_spawns()

        if SearchType.ITEM in self._search_types:
            count += self._search_items()

        self.finished_search.emit(count)

    def _search_waypoints(self) -> int:
        """Search waypoints."""
        waypoints = getattr(self._game_map, "waypoints", {}) or {}
        count = 0

        for name, pos in waypoints.items():
            if self._cancelled:
                break

            if self._query in name.lower():
                result = SearchResult(
                    result_type=SearchType.WAYPOINT,
                    name=name,
                    description="Waypoint",
                    position=(int(pos.x), int(pos.y), int(pos.z)),
                )
                self.result_found.emit(result)
                count += 1

        return count

    def _search_houses(self) -> int:
        """Search houses."""
        houses = getattr(self._game_map, "houses", {}) or {}
        count = 0

        for house_id, house in houses.items():
            if self._cancelled:
                break

            name = getattr(house, "name", "") or ""
            if self._query in name.lower() or self._query in str(house_id):
                entry = house.entry
                pos = (int(entry.x), int(entry.y), int(entry.z)) if entry else None

                result = SearchResult(
                    result_type=SearchType.HOUSE,
                    name=name or f"House #{house_id}",
                    description=f"ID: {house_id}, Rent: {house.rent or 0}",
                    position=pos,
                    entity_id=house_id,
                )
                self.result_found.emit(result)
                count += 1

        return count

    def _search_zones(self) -> int:
        """Search zones."""
        zones = getattr(self._game_map, "zones", {}) or {}
        count = 0

        for zone_id, zone in zones.items():
            if self._cancelled:
                break

            name = zone.get("name", zone_id) if isinstance(zone, dict) else getattr(zone, "name", zone_id)
            if self._query in str(name).lower() or self._query in zone_id.lower():
                result = SearchResult(
                    result_type=SearchType.ZONE, name=str(name), description=f"Zone: {zone_id}", position=None
                )
                self.result_found.emit(result)
                count += 1

        return count

    def _search_spawns(self) -> int:
        """Search spawns by creature name."""
        count = 0

        # Monster spawns
        m_spawns = getattr(self._game_map, "monster_spawns", []) or []
        for spawn in m_spawns:
            if self._cancelled:
                break

            center = spawn.center
            monsters = getattr(spawn, "monsters", []) or []

            for monster in monsters:
                name = getattr(monster, "name", "") or ""
                if self._query in name.lower():
                    result = SearchResult(
                        result_type=SearchType.SPAWN,
                        name=name,
                        description=f"Monster Spawn (r={spawn.radius})",
                        position=(int(center.x), int(center.y), int(center.z)),
                    )
                    self.result_found.emit(result)
                    count += 1

        # NPC spawns
        n_spawns = getattr(self._game_map, "npc_spawns", []) or []
        for spawn in n_spawns:
            if self._cancelled:
                break

            center = spawn.center
            npcs = getattr(spawn, "npcs", []) or []

            for npc in npcs:
                name = getattr(npc, "name", "") or ""
                if self._query in name.lower():
                    result = SearchResult(
                        result_type=SearchType.SPAWN,
                        name=name,
                        description="NPC Spawn",
                        position=(int(center.x), int(center.y), int(center.z)),
                    )
                    self.result_found.emit(result)
                    count += 1

        return count

    def _search_items(self) -> int:
        """Search items by ID."""
        # This would search through tiles for items
        # Limited implementation for now
        try:
            item_id = int(self._query)
        except ValueError:
            return 0

        count = 0
        tiles = getattr(self._game_map, "tiles", {}) or {}

        max_results = 100

        for _pos, tile in tiles.items():
            if self._cancelled or count >= max_results:
                break

            # Check ground
            if tile.ground and tile.ground.id == item_id:
                result = SearchResult(
                    result_type=SearchType.ITEM,
                    name=f"Item #{item_id} (ground)",
                    description="Ground at tile",
                    position=(tile.x, tile.y, tile.z),
                    entity_id=item_id,
                )
                self.result_found.emit(result)
                count += 1
                continue

            # Check items
            for item in tile.items:
                if item.id == item_id:
                    result = SearchResult(
                        result_type=SearchType.ITEM,
                        name=f"Item #{item_id}",
                        description="On tile",
                        position=(tile.x, tile.y, tile.z),
                        entity_id=item_id,
                    )
                    self.result_found.emit(result)
                    count += 1
                    break

        return count


class GlobalSearchDialog(QDialog):
    """Universal search dialog.

    Signals:
        goto_position: Emits (x, y, z) for navigation
    """

    goto_position = pyqtSignal(int, int, int)

    def __init__(self, game_map: GameMap | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._game_map = game_map
        self._worker: SearchWorker | None = None
        self._results: list[SearchResult] = []

        self.setWindowTitle("Global Search")
        self.setMinimumSize(550, 450)
        self.setModal(False)  # Non-modal for usability

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Search input
        search_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search for items, houses, spawns, waypoints...")
        self.search_input.returnPressed.connect(self._do_search)
        search_row.addWidget(self.search_input)

        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self._do_search)
        search_row.addWidget(self.btn_search)

        layout.addLayout(search_row)

        # Filter checkboxes
        filter_row = QHBoxLayout()
        filter_row.setSpacing(16)

        self.check_items = QCheckBox("Items")
        self.check_items.setChecked(True)
        filter_row.addWidget(self.check_items)

        self.check_houses = QCheckBox("Houses")
        self.check_houses.setChecked(True)
        filter_row.addWidget(self.check_houses)

        self.check_spawns = QCheckBox("Spawns")
        self.check_spawns.setChecked(True)
        filter_row.addWidget(self.check_spawns)

        self.check_waypoints = QCheckBox("Waypoints")
        self.check_waypoints.setChecked(True)
        filter_row.addWidget(self.check_waypoints)

        self.check_zones = QCheckBox("Zones")
        self.check_zones.setChecked(True)
        filter_row.addWidget(self.check_zones)

        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setMaximum(0)  # Indeterminate
        self.progress.hide()
        layout.addWidget(self.progress)

        # Results list
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self._on_result_clicked)
        layout.addWidget(self.results_list)

        # Status
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #A1A1AA; font-size: 11px;")
        layout.addWidget(self.status_label)

        # Buttons
        button_row = QHBoxLayout()

        self.btn_goto = QPushButton("🚀 Go To")
        self.btn_goto.setEnabled(False)
        self.btn_goto.clicked.connect(self._on_goto)
        button_row.addWidget(self.btn_goto)

        button_row.addStretch()

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        button_row.addWidget(btn_close)

        layout.addLayout(button_row)

    def _apply_style(self) -> None:
        """Apply modern styling."""
        self.setStyleSheet(
            """
            QDialog {
                background: #1E1E2E;
            }

            QLineEdit {
                background: #2A2A3E;
                border: 2px solid #363650;
                border-radius: 8px;
                padding: 10px 14px;
                color: #E5E5E7;
                font-size: 14px;
            }

            QLineEdit:focus {
                border-color: #8B5CF6;
            }

            QCheckBox {
                color: #A1A1AA;
                font-size: 12px;
            }

            QCheckBox:checked {
                color: #E5E5E7;
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

            QProgressBar {
                background: #363650;
                border: none;
                border-radius: 4px;
                height: 6px;
            }

            QProgressBar::chunk {
                background: #8B5CF6;
                border-radius: 4px;
            }

            QPushButton {
                background: #8B5CF6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }

            QPushButton:hover {
                background: #A78BFA;
            }

            QPushButton:disabled {
                background: #363650;
                color: #52525B;
            }
        """
        )

    def _get_search_types(self) -> list[SearchType]:
        """Get enabled search types."""
        types = []
        if self.check_items.isChecked():
            types.append(SearchType.ITEM)
        if self.check_houses.isChecked():
            types.append(SearchType.HOUSE)
        if self.check_spawns.isChecked():
            types.append(SearchType.SPAWN)
        if self.check_waypoints.isChecked():
            types.append(SearchType.WAYPOINT)
        if self.check_zones.isChecked():
            types.append(SearchType.ZONE)
        return types

    def _do_search(self) -> None:
        """Execute search."""
        query = self.search_input.text().strip()
        if not query or not self._game_map:
            return

        # Cancel previous search
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait()

        # Clear results
        self.results_list.clear()
        self._results.clear()

        # Show progress
        self.progress.show()
        self.btn_search.setEnabled(False)
        self.status_label.setText("Searching...")

        # Start search
        self._worker = SearchWorker(self._game_map, query, self._get_search_types())
        self._worker.result_found.connect(self._add_result)
        self._worker.finished_search.connect(self._on_search_complete)
        self._worker.start()

    def _add_result(self, result: SearchResult) -> None:
        """Add search result to list."""
        self._results.append(result)

        # Create list item
        icon = {
            SearchType.ITEM: "📦",
            SearchType.HOUSE: "🏠",
            SearchType.SPAWN: "👹",
            SearchType.WAYPOINT: "📍",
            SearchType.ZONE: "🗺️",
        }.get(result.result_type, "•")

        text = f"{icon} {result.name}"
        if result.description:
            text += f"\n    {result.description}"
        if result.position:
            text += f" @ ({result.position[0]}, {result.position[1]}, {result.position[2]})"

        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, len(self._results) - 1)
        self.results_list.addItem(item)

    def _on_search_complete(self, count: int) -> None:
        """Handle search completion."""
        self.progress.hide()
        self.btn_search.setEnabled(True)
        self.status_label.setText(f"Found {count} result{'s' if count != 1 else ''}")

        if count > 0:
            self.btn_goto.setEnabled(True)
            self.results_list.setFocus()

    def _on_result_clicked(self, item: QListWidgetItem) -> None:
        """Handle result double-click."""
        self._on_goto()

    def _on_goto(self) -> None:
        """Navigate to selected result."""
        item = self.results_list.currentItem()
        if not item:
            return

        index = item.data(Qt.ItemDataRole.UserRole)
        if index is None or index >= len(self._results):
            return

        result = self._results[index]
        if result.position:
            self.goto_position.emit(*result.position)
