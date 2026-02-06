"""Find Item Dialog - Advanced search for items across the map.

Allows mappers to:
- Search by ID (Server or Client)
- Search by Name (with autocomplete)
- Search by Type (Wall, Door, Container, etc.)
- Advanced filters (ActionID, UniqueID, Text, Z-layer)
- Navigate to found items
- Replace all found items

Reference: RME/source/ui/find_item_window.cpp (20KB)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Item


class SearchMode(str, Enum):
    """Search mode enum."""

    ID = "id"
    NAME = "name"
    TYPE = "type"


@dataclass(slots=True)
class SearchResult:
    """Represents a single search result."""

    item: Item
    position: tuple[int, int, int]  # (x, y, z)
    tile_item_index: int  # Index in tile.items (-1 for ground)


@dataclass(slots=True)
class SearchFilters:
    """Advanced search filters."""

    search_mode: SearchMode = SearchMode.ID
    search_value: str = ""

    # Filters
    has_action_id: bool = False
    action_id_value: int = 0

    has_unique_id: bool = False
    unique_id_value: int = 0

    has_text: bool = False
    text_value: str = ""

    specific_z: bool = False
    z_value: int = 7

    selection_only: bool = False


class SearchResultWidget(QWidget):
    """Widget displaying a single search result."""

    clicked = pyqtSignal(tuple)  # Emits (x, y, z) position

    def __init__(self, result: SearchResult, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.result = result
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        # Item info
        item = self.result.item
        pos = self.result.position

        # Get item name from asset manager
        from py_rme_canary.logic_layer.asset_manager import AssetManager

        asset_mgr = AssetManager.instance()
        item_name = asset_mgr.get_item_name(item.id)

        # Format info text with name
        if item_name != f"Item #{item.id}":
            info_text = f"{item_name} (#{item.id}) @ ({pos[0]}, {pos[1]}, Floor {pos[2]})"
        else:
            info_text = f"ID {item.id} @ ({pos[0]}, {pos[1]}, Floor {pos[2]})"

        # Add attributes
        attrs = []
        if item.action_id:
            attrs.append(f"AID:{item.action_id}")
        if item.unique_id:
            attrs.append(f"UID:{item.unique_id}")
        if attrs:
            info_text += f" - {', '.join(attrs)}"

        label = QLabel(info_text)
        label.setStyleSheet(
            """
            QLabel {
                color: #E5E5E7;
                font-size: 12px;
                padding: 4px;
            }
        """
        )
        layout.addWidget(label, 1)

        # Jump button
        jump_btn = QPushButton("Jump →")
        jump_btn.setFixedWidth(80)
        jump_btn.setStyleSheet(
            """
            QPushButton {
                background: #363650;
                color: #E5E5E7;
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #8B5CF6;
                color: white;
            }
        """
        )
        jump_btn.clicked.connect(lambda: self.clicked.emit(pos))
        layout.addWidget(jump_btn)


class FindItemDialog(QDialog):
    """Dialog for finding items across the map with advanced filters.

    Features:
    - Search by ID, Name, or Type
    - Advanced filters (ActionID, UniqueID, Text, Z-layer)
    - Results list with clickable positions
    - "Replace All" integration
    - Selection-only search mode
    """

    jump_to_position = pyqtSignal(tuple)  # Emits (x, y, z) to jump in canvas
    replace_all_requested = pyqtSignal(list)  # Emits list of SearchResult

    def __init__(self, game_map: GameMap | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.game_map = game_map
        self._search_results: list[SearchResult] = []

        self.setWindowTitle("Find Items")
        self.setMinimumSize(600, 700)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Search Mode
        mode_group = QGroupBox("Search By")
        mode_layout = QHBoxLayout(mode_group)

        self.mode_group = QButtonGroup(self)

        self.id_radio = QRadioButton("ID")
        self.id_radio.setChecked(True)
        self.mode_group.addButton(self.id_radio)
        mode_layout.addWidget(self.id_radio)

        self.name_radio = QRadioButton("Name")
        self.mode_group.addButton(self.name_radio)
        mode_layout.addWidget(self.name_radio)

        self.type_radio = QRadioButton("Type")
        self.mode_group.addButton(self.type_radio)
        mode_layout.addWidget(self.type_radio)

        mode_layout.addStretch()
        layout.addWidget(mode_group)

        # Search Input
        search_group = QGroupBox("Search")
        search_layout = QFormLayout(search_group)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter ID, name, or type...")
        self.search_input.returnPressed.connect(self._on_search)
        search_layout.addRow("Value:", self.search_input)

        layout.addWidget(search_group)

        # Advanced Filters
        filters_group = QGroupBox("Filters")
        filters_layout = QFormLayout(filters_group)

        # Action ID filter
        aid_layout = QHBoxLayout()
        self.has_aid_check = QCheckBox()
        aid_layout.addWidget(self.has_aid_check)
        self.aid_spin = QSpinBox()
        self.aid_spin.setRange(0, 65535)
        self.aid_spin.setEnabled(False)
        self.has_aid_check.toggled.connect(self.aid_spin.setEnabled)
        aid_layout.addWidget(self.aid_spin)
        aid_layout.addStretch()
        filters_layout.addRow("Has Action ID:", aid_layout)

        # Unique ID filter
        uid_layout = QHBoxLayout()
        self.has_uid_check = QCheckBox()
        uid_layout.addWidget(self.has_uid_check)
        self.uid_spin = QSpinBox()
        self.uid_spin.setRange(0, 65535)
        self.uid_spin.setEnabled(False)
        self.has_uid_check.toggled.connect(self.uid_spin.setEnabled)
        uid_layout.addWidget(self.uid_spin)
        uid_layout.addStretch()
        filters_layout.addRow("Has Unique ID:", uid_layout)

        # Text filter
        text_layout = QHBoxLayout()
        self.has_text_check = QCheckBox()
        text_layout.addWidget(self.has_text_check)
        self.text_input = QLineEdit()
        self.text_input.setEnabled(False)
        self.has_text_check.toggled.connect(self.text_input.setEnabled)
        text_layout.addWidget(self.text_input)
        filters_layout.addRow("Contains Text:", text_layout)

        # Z-layer filter
        z_layout = QHBoxLayout()
        self.specific_z_check = QCheckBox()
        z_layout.addWidget(self.specific_z_check)
        self.z_spin = QSpinBox()
        self.z_spin.setRange(0, 15)
        self.z_spin.setValue(7)
        self.z_spin.setEnabled(False)
        self.specific_z_check.toggled.connect(self.z_spin.setEnabled)
        z_layout.addWidget(self.z_spin)
        z_layout.addStretch()
        filters_layout.addRow("Specific Floor:", z_layout)

        # Selection only
        self.selection_only_check = QCheckBox("Search in selection only")
        filters_layout.addRow("", self.selection_only_check)

        layout.addWidget(filters_group)

        # Search Button
        search_btn = QPushButton("🔍 Find")
        search_btn.clicked.connect(self._on_search)
        search_btn.setFixedHeight(40)
        layout.addWidget(search_btn)

        # Results
        results_group = QGroupBox("Results")
        results_layout = QVBoxLayout(results_group)

        self.results_label = QLabel("No results yet")
        self.results_label.setStyleSheet("color: #A1A1AA; font-style: italic;")
        results_layout.addWidget(self.results_label)

        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.results_list.setStyleSheet(
            """
            QListWidget {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                background: #2A2A3E;
                border-radius: 4px;
                padding: 2px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background: #363650;
                border: 1px solid #8B5CF6;
            }
            QListWidget::item:hover {
                background: #363650;
            }
        """
        )
        results_layout.addWidget(self.results_list)

        layout.addWidget(results_group)

        # Action Buttons
        button_layout = QHBoxLayout()

        self.replace_all_btn = QPushButton("Replace All...")
        self.replace_all_btn.clicked.connect(self._on_replace_all)
        self.replace_all_btn.setEnabled(False)
        button_layout.addWidget(self.replace_all_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _on_search(self) -> None:
        """Execute search based on current filters."""
        if not self.game_map:
            self.results_label.setText("⚠️ No map loaded")
            return

        # Build filters
        filters = self._build_filters()

        # Execute search
        self._search_results = self._perform_search(filters)

        # Update UI
        self._display_results()

    def _build_filters(self) -> SearchFilters:
        """Build SearchFilters from UI state."""
        # Determine search mode
        if self.id_radio.isChecked():
            mode = SearchMode.ID
        elif self.name_radio.isChecked():
            mode = SearchMode.NAME
        else:
            mode = SearchMode.TYPE

        return SearchFilters(
            search_mode=mode,
            search_value=self.search_input.text().strip(),
            has_action_id=self.has_aid_check.isChecked(),
            action_id_value=self.aid_spin.value(),
            has_unique_id=self.has_uid_check.isChecked(),
            unique_id_value=self.uid_spin.value(),
            has_text=self.has_text_check.isChecked(),
            text_value=self.text_input.text().strip(),
            specific_z=self.specific_z_check.isChecked(),
            z_value=self.z_spin.value(),
            selection_only=self.selection_only_check.isChecked(),
        )

    def _perform_search(self, filters: SearchFilters) -> list[SearchResult]:
        """Perform search across the map.

        Args:
            filters: Search filters

        Returns:
            List of search results
        """
        results = []

        if not self.game_map:
            return results

        # Iterate all tiles
        for tile in self.game_map.iter_tiles():
            # Z-layer filter
            if filters.specific_z and tile.z != filters.z_value:
                continue

            # Check ground
            if tile.ground and self._item_matches(tile.ground, filters):
                results.append(SearchResult(item=tile.ground, position=(tile.x, tile.y, tile.z), tile_item_index=-1))

            # Check items
            for i, item in enumerate(tile.items):
                if self._item_matches(item, filters):
                    results.append(SearchResult(item=item, position=(tile.x, tile.y, tile.z), tile_item_index=i))

        return results

    def _item_matches(self, item: Item, filters: SearchFilters) -> bool:
        """Check if an item matches search filters.

        Args:
            item: Item to check
            filters: Search filters

        Returns:
            True if item matches
        """
        # Search mode check
        if filters.search_mode == SearchMode.ID:
            if filters.search_value:
                try:
                    search_id = int(filters.search_value)
                    if item.id != search_id:
                        return False
                except ValueError:
                    return False

        elif filters.search_mode == SearchMode.NAME:
            # Search by item name using items.xml
            if filters.search_value:
                from py_rme_canary.logic_layer.asset_manager import AssetManager

                asset_mgr = AssetManager.instance()

                # Get item name and check if search term is in it
                item_name = asset_mgr.get_item_name(item.id).lower()
                search_term = filters.search_value.lower()

                if search_term not in item_name:
                    return False

        elif filters.search_mode == SearchMode.TYPE:
            if filters.search_value and not self._matches_type_filter(item, filters.search_value):
                return False

        # Action ID filter
        if filters.has_action_id and item.action_id != filters.action_id_value:
            return False

        # Unique ID filter
        if filters.has_unique_id and item.unique_id != filters.unique_id_value:
            return False

        # Text filter
        return not (filters.has_text and (not item.text or filters.text_value.lower() not in item.text.lower()))

    @staticmethod
    def _normalize_type_token(value: str) -> str:
        """Normalize type token for robust comparisons."""
        return "".join(ch for ch in str(value or "").casefold() if ch.isalnum())

    def _item_type_tokens(self, item: Item) -> set[str]:
        """Collect searchable type tokens from detector + items.xml metadata."""
        from py_rme_canary.logic_layer.asset_manager import AssetManager
        from py_rme_canary.logic_layer.item_type_detector import ItemTypeDetector

        asset_mgr = AssetManager.instance()
        metadata = asset_mgr.get_item_metadata(int(item.id))
        category = ItemTypeDetector.get_category(item)

        tokens: set[str] = {str(category.value)}

        name = asset_mgr.get_item_name(int(item.id))
        if name:
            tokens.add(str(name))

        if metadata is None:
            return tokens

        kind = str(metadata.kind or "").strip()
        if kind:
            tokens.add(kind)

        for key, raw_value in metadata.attributes.items():
            key_text = str(key or "").strip()
            if not key_text:
                continue

            value_text = str(raw_value or "").strip()
            lowered_value = value_text.casefold()

            if lowered_value in {"1", "true", "yes", "on"}:
                tokens.add(key_text)

            if key_text.casefold() in {"type", "group", "category", "slot", "weapon"} and value_text:
                tokens.add(value_text)

        return tokens

    def _matches_type_filter(self, item: Item, search_value: str) -> bool:
        """Match user-entered type query against item category/metadata."""
        from py_rme_canary.logic_layer.item_type_detector import ItemCategory, ItemTypeDetector

        query = self._normalize_type_token(search_value)
        if not query:
            return True

        aliases = {
            "magic": "magicfield",
            "magicfields": "magicfield",
            "trash": "trashholder",
            "trashcan": "trashholder",
            "trashholder": "trashholder",
            "trashhold": "trashholder",
            "mailboxes": "mailbox",
            "depots": "depot",
            "containers": "container",
            "doors": "door",
            "teleports": "teleport",
            "beds": "bed",
            "keys": "key",
            "podiums": "podium",
            "walls": "wall",
            "carpets": "carpet",
            "tables": "table",
            "chairs": "chair",
            "rotate": "rotatable",
            "rotation": "rotatable",
        }
        canonical = aliases.get(query, query)

        tokens = self._item_type_tokens(item)
        normalized_tokens = {self._normalize_type_token(t) for t in tokens if t}

        if canonical in normalized_tokens:
            return True
        if any(canonical in token for token in normalized_tokens):
            return True

        category = ItemTypeDetector.get_category(item)
        category_matches: dict[str, ItemCategory] = {
            "wall": ItemCategory.WALL,
            "carpet": ItemCategory.CARPET,
            "door": ItemCategory.DOOR,
            "table": ItemCategory.TABLE,
            "chair": ItemCategory.CHAIR,
            "container": ItemCategory.CONTAINER,
            "teleport": ItemCategory.TELEPORT,
        }
        expected = category_matches.get(canonical)
        if expected is not None:
            return category == expected

        if canonical == "rotatable":
            return ItemTypeDetector.is_rotatable(item)

        if canonical == "door":
            return ItemTypeDetector.is_door(item)

        if canonical == "teleport":
            return ItemTypeDetector.is_teleport(item)

        return False

    def _display_results(self) -> None:
        """Display search results in the list."""
        self.results_list.clear()

        count = len(self._search_results)

        if count == 0:
            self.results_label.setText("No results found")
            self.replace_all_btn.setEnabled(False)
            return

        self.results_label.setText(f"Found {count} item{'s' if count != 1 else ''}")
        self.replace_all_btn.setEnabled(True)

        # Add results to list
        for result in self._search_results:
            widget = SearchResultWidget(result)
            widget.clicked.connect(self._on_jump_to_result)

            list_item = QListWidgetItem(self.results_list)
            list_item.setSizeHint(widget.sizeHint())
            self.results_list.addItem(list_item)
            self.results_list.setItemWidget(list_item, widget)

    def _on_jump_to_result(self, position: tuple[int, int, int]) -> None:
        """Handle jump to result."""
        self.jump_to_position.emit(position)

    def _on_replace_all(self) -> None:
        """Handle replace all button."""
        if self._search_results:
            self.replace_all_requested.emit(self._search_results)

    def _apply_style(self) -> None:
        """Apply modern dark theme."""
        self.setStyleSheet(
            """
            FindItemDialog {
                background: #1E1E2E;
            }
            QGroupBox {
                color: #E5E5E7;
                font-weight: 600;
                border: 1px solid #363650;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
            QLineEdit, QSpinBox {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 6px;
                padding: 6px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border-color: #8B5CF6;
            }
            QRadioButton, QCheckBox {
                color: #E5E5E7;
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
            QPushButton:pressed {
                background: #7C3AED;
            }
            QPushButton:disabled {
                background: #363650;
                color: #52525B;
            }
        """
        )
