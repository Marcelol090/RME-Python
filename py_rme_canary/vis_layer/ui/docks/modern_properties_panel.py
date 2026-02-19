"""Modern Properties Panel with editable fields and tabs.

Enhanced version of properties_panel.py with:
- Tab-based organization (Tile, Item, House, Spawn)
- Editable fields with validation
- Apply/Revert buttons
- Modern styling
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    from py_rme_canary.core.data.houses import House
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.spawns import MonsterSpawnArea, NpcSpawnArea
    from py_rme_canary.core.data.tile import Tile


@dataclass(slots=True)
class PropertyChange:
    """Represents a pending property change."""

    field_name: str
    old_value: Any
    new_value: Any


class ModernPropertiesPanel(QDockWidget):
    """Modern properties panel with tabs and editable fields.

    Signals:
        changes_applied: Emitted when user applies changes
        changes_reverted: Emitted when user reverts changes
    """

    changes_applied = pyqtSignal(object)  # Emits modified entity
    changes_reverted = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Properties", parent)

        self._current_tile: Tile | None = None
        self._current_item: Item | None = None
        self._current_house: House | None = None
        # Store context (coords, etc) for applying changes
        self._current_details: dict[str, Any] = {}
        self._pending_changes: list[PropertyChange] = []

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        # Main container
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # Header with entity info
        self.header = QLabel("Select an entity")
        self.header.setObjectName("propertiesHeader")
        main_layout.addWidget(self.header)

        # Tab widget for different property types
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Create tabs
        self.tile_tab = self._create_tile_tab()
        self.item_tab = self._create_item_tab()
        self.house_tab = self._create_house_tab()
        self.spawn_tab = self._create_spawn_tab()

        self.item_advanced_tab = self._create_item_advanced_tab()

        self.tabs.addTab(self.tile_tab, "Tile")
        self.tabs.addTab(self.item_tab, "Item")
        self.tabs.addTab(self.item_advanced_tab, "Advanced")
        self.tabs.addTab(self.house_tab, "House")
        self.tabs.addTab(self.spawn_tab, "Spawn")

        # Advanced tab initially hidden (only shown when an item is selected)
        self.tabs.setTabVisible(2, False)

        main_layout.addWidget(self.tabs)

        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setObjectName("primaryButton")
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self._on_apply)

        self.btn_revert = QPushButton("Revert")
        self.btn_revert.setObjectName("secondaryButton")
        self.btn_revert.setEnabled(False)
        self.btn_revert.clicked.connect(self._on_revert)

        button_layout.addStretch()
        button_layout.addWidget(self.btn_revert)
        button_layout.addWidget(self.btn_apply)

        main_layout.addLayout(button_layout)

        self.setWidget(container)

    def _create_tile_tab(self) -> QWidget:
        """Create tile properties tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Position (read-only)
        self.tile_position = QLabel("—")
        self.tile_position.setObjectName("monoLabel")
        layout.addRow("Position:", self.tile_position)

        # Ground ID (read-only)
        self.tile_ground = QLabel("—")
        layout.addRow("Ground:", self.tile_ground)

        # House ID
        self.tile_house_id = QSpinBox()
        self.tile_house_id.setRange(0, 65535)
        self.tile_house_id.valueChanged.connect(lambda v: self._mark_changed("house_id", v))
        layout.addRow("House ID:", self.tile_house_id)

        # Flags group
        flags_group = QGroupBox("Tile Flags")
        flags_layout = QGridLayout(flags_group)

        self.flag_pz = QCheckBox("Protection Zone (PZ)")
        self.flag_pz.stateChanged.connect(lambda: self._mark_changed("flag_pz", self.flag_pz.isChecked()))
        flags_layout.addWidget(self.flag_pz, 0, 0)

        self.flag_no_logout = QCheckBox("No Logout")
        self.flag_no_logout.stateChanged.connect(
            lambda: self._mark_changed("flag_no_logout", self.flag_no_logout.isChecked())
        )
        flags_layout.addWidget(self.flag_no_logout, 0, 1)

        self.flag_no_pvp = QCheckBox("No PvP")
        self.flag_no_pvp.stateChanged.connect(lambda: self._mark_changed("flag_no_pvp", self.flag_no_pvp.isChecked()))
        flags_layout.addWidget(self.flag_no_pvp, 1, 0)

        self.flag_pvp_zone = QCheckBox("PvP Zone")
        self.flag_pvp_zone.stateChanged.connect(
            lambda: self._mark_changed("flag_pvp_zone", self.flag_pvp_zone.isChecked())
        )
        flags_layout.addWidget(self.flag_pvp_zone, 1, 1)

        layout.addRow(flags_group)

        return widget

    def _create_item_tab(self) -> QWidget:
        """Create item properties tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Item ID (read-only)
        self.item_id = QLabel("—")
        self.item_id.setObjectName("monoLabel")
        layout.addRow("Item ID:", self.item_id)

        # Image Preview
        self.item_preview = QLabel()
        self.item_preview.setFixedSize(32, 32)
        # Styled in _apply_style via objectName
        self.item_preview.setObjectName("itemPreview")
        layout.addRow("Preview:", self.item_preview)

        # Client ID (read-only)
        self.item_client_id = QLabel("—")
        layout.addRow("Client ID:", self.item_client_id)

        # Count/Subtype
        self.item_count = QSpinBox()
        self.item_count.setRange(0, 255)
        self.item_count.valueChanged.connect(lambda v: self._mark_changed("count", v))
        layout.addRow("Count:", self.item_count)

        # Action ID
        self.item_action_id = QSpinBox()
        self.item_action_id.setRange(0, 65535)
        self.item_action_id.valueChanged.connect(lambda v: self._mark_changed("action_id", v))
        layout.addRow("Action ID:", self.item_action_id)

        # Unique ID
        self.item_unique_id = QSpinBox()
        self.item_unique_id.setRange(0, 65535)
        self.item_unique_id.valueChanged.connect(lambda v: self._mark_changed("unique_id", v))
        layout.addRow("Unique ID:", self.item_unique_id)

        # Tier (C++ parity: createClassificationFields — visible for weapon/equipment/classified items)
        self.item_tier = QSpinBox()
        self.item_tier.setRange(0, 255)
        self.item_tier.setToolTip("Item tier (0–255). Shown for weapon/equipment/classified items.")
        self.item_tier.valueChanged.connect(lambda v: self._mark_changed("tier", v))
        self.item_tier_label = QLabel("Tier:")
        layout.addRow(self.item_tier_label, self.item_tier)
        # Hidden until item with classification/weapon/equipment is shown
        self.item_tier_label.setVisible(False)
        self.item_tier.setVisible(False)

        # Text (for books/signs)
        text_group = QGroupBox("Text Content")
        text_layout = QVBoxLayout(text_group)
        self.item_text = QTextEdit()
        self.item_text.setMaximumHeight(80)
        self.item_text.textChanged.connect(lambda: self._mark_changed("text", self.item_text.toPlainText()))
        text_layout.addWidget(self.item_text)
        layout.addRow(text_group)

        # Destination (for teleports)
        dest_group = QGroupBox("Teleport Destination")
        dest_layout = QHBoxLayout(dest_group)

        self.item_dest_x = QSpinBox()
        self.item_dest_x.setRange(0, 65535)
        self.item_dest_x.setPrefix("X: ")
        dest_layout.addWidget(self.item_dest_x)

        self.item_dest_y = QSpinBox()
        self.item_dest_y.setRange(0, 65535)
        self.item_dest_y.setPrefix("Y: ")
        dest_layout.addWidget(self.item_dest_y)

        self.item_dest_z = QSpinBox()
        self.item_dest_z.setRange(0, 15)
        self.item_dest_z.setPrefix("Z: ")
        dest_layout.addWidget(self.item_dest_z)

        layout.addRow(dest_group)

        return widget

    def _create_house_tab(self) -> QWidget:
        """Create house properties tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # House ID (read-only)
        self.house_id = QLabel("—")
        self.house_id.setObjectName("monoLabel")
        layout.addRow("House ID:", self.house_id)

        # Name
        self.house_name = QLineEdit()
        self.house_name.textChanged.connect(lambda t: self._mark_changed("name", t))
        layout.addRow("Name:", self.house_name)

        # Rent
        self.house_rent = QSpinBox()
        self.house_rent.setRange(0, 999999)
        self.house_rent.setSuffix(" gold")
        self.house_rent.valueChanged.connect(lambda v: self._mark_changed("rent", v))
        layout.addRow("Rent:", self.house_rent)

        # Town
        self.house_town = QComboBox()
        self.house_town.currentIndexChanged.connect(lambda i: self._mark_changed("townid", i))
        layout.addRow("Town:", self.house_town)

        # Guildhall
        self.house_guildhall = QCheckBox("Is Guildhall")
        self.house_guildhall.stateChanged.connect(
            lambda: self._mark_changed("guildhall", self.house_guildhall.isChecked())
        )
        layout.addRow("", self.house_guildhall)

        # Entry position (read-only)
        self.house_entry = QLabel("—")
        self.house_entry.setObjectName("monoLabel")
        layout.addRow("Entry:", self.house_entry)

        # Doors count (read-only)
        self.house_doors = QLabel("—")
        layout.addRow("Doors:", self.house_doors)

        return widget

    def _create_item_advanced_tab(self) -> QWidget:
        """Create the Advanced attributes tab — C++ parity with PropertiesWindow::createAttributesPanel().

        Displays a Key / Type / Value editable table matching the C++ AttributeService:
          - Types: Number, Float, Boolean, String
          - Add Attribute button appends a new empty row
          - Remove Attribute button deletes the selected row
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Table: Key | Type | Value
        self.attr_table = QTableWidget(0, 3)
        self.attr_table.setObjectName("attrTable")
        self.attr_table.setHorizontalHeaderLabels(["Key", "Type", "Value"])
        self.attr_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.attr_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.attr_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.attr_table.verticalHeader().setVisible(False)
        self.attr_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.attr_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.attr_table.setAlternatingRowColors(True)
        self.attr_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
        )
        # Type column changed handler — re-validate value when type changes
        self.attr_table.cellChanged.connect(self._on_attr_cell_changed)
        layout.addWidget(self.attr_table)

        # Add / Remove buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_add_attr = QPushButton("+ Add Attribute")
        self.btn_add_attr.setObjectName("secondaryButton")
        self.btn_add_attr.clicked.connect(self._on_add_attribute)
        btn_row.addWidget(self.btn_add_attr)

        self.btn_remove_attr = QPushButton("− Remove")
        self.btn_remove_attr.setObjectName("secondaryButton")
        self.btn_remove_attr.clicked.connect(self._on_remove_attribute)
        btn_row.addWidget(self.btn_remove_attr)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        return widget

    def _create_spawn_tab(self) -> QWidget:
        """Create spawn properties tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Type
        self.spawn_type = QLabel("—")
        layout.addRow("Type:", self.spawn_type)

        # Center (read-only)
        self.spawn_center = QLabel("—")
        self.spawn_center.setObjectName("monoLabel")
        layout.addRow("Center:", self.spawn_center)

        # Radius
        self.spawn_radius = QSpinBox()
        self.spawn_radius.setRange(1, 11)
        self.spawn_radius.valueChanged.connect(lambda v: self._mark_changed("radius", v))
        layout.addRow("Radius:", self.spawn_radius)

        # Spawn time
        self.spawn_time = QSpinBox()
        self.spawn_time.setRange(0, 86400)
        self.spawn_time.setSuffix(" sec")
        self.spawn_time.valueChanged.connect(lambda v: self._mark_changed("spawn_time", v))
        layout.addRow("Spawn Time:", self.spawn_time)

        # Creatures count (read-only)
        self.spawn_count = QLabel("—")
        layout.addRow("Creatures:", self.spawn_count)

        return widget

    def _apply_style(self) -> None:
        """Apply modern styling using theme tokens."""
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.setStyleSheet(
            f"""
            ModernPropertiesPanel {{
                background: {c["surface"]["primary"]};
            }}

            #propertiesHeader {{
                color: {c["text"]["primary"]};
                font-size: 14px;
                font-weight: 600;
                padding: 8px 0;
            }}

            #monoLabel {{
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                color: {c["brand"]["primary"]};
            }}

            #itemPreview {{
                background: {c["surface"]["secondary"]};
                border-radius: {r["sm"]}px;
            }}

            QGroupBox {{
                background: {c["surface"]["secondary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["md"]}px;
                margin-top: 16px;
                padding-top: 8px;
                font-weight: 600;
                color: {c["text"]["primary"]};
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: {c["text"]["secondary"]};
            }}

            #primaryButton {{
                background: {c["brand"]["primary"]};
                color: {c["text"]["primary"]};
                border: none;
                border-radius: {r["md"]}px;
                padding: 8px 16px;
                font-weight: 600;
                min-width: 80px;
            }}

            #primaryButton:hover {{
                background: {c["brand"]["secondary"]};
            }}

            #primaryButton:disabled {{
                background: {c["surface"]["tertiary"]};
                color: {c["text"]["disabled"]};
            }}

            #secondaryButton {{
                background: {c["surface"]["tertiary"]};
                color: {c["text"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["md"]}px;
                padding: 8px 16px;
                font-weight: 500;
                min-width: 80px;
            }}

            #secondaryButton:hover {{
                background: {c["state"]["hover"]};
                border-color: {c["brand"]["primary"]};
            }}

            #secondaryButton:disabled {{
                background: {c["surface"]["secondary"]};
                color: {c["text"]["disabled"]};
                border-color: {c["surface"]["tertiary"]};
            }}

            QTableWidget#attrTable {{
                background: {c["surface"]["secondary"]};
                alternate-background-color: {c["surface"]["primary"]};
                color: {c["text"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["md"]}px;
                gridline-color: {c["border"]["subtle"]};
                selection-background-color: {c["state"]["selected"]};
                selection-color: {c["text"]["primary"]};
            }}

            QTableWidget#attrTable QHeaderView::section {{
                background: {c["surface"]["tertiary"]};
                color: {c["text"]["secondary"]};
                border: none;
                border-bottom: 1px solid {c["border"]["default"]};
                padding: 4px 8px;
                font-weight: 600;
                font-size: 11px;
            }}
        """
        )

    # ------------------------------------------------------------------
    # Advanced Attributes tab helpers (C++ AttributeService parity)
    # ------------------------------------------------------------------

    _ATTR_TYPES: list[str] = ["String", "Number", "Float", "Boolean"]

    def _populate_attr_table(self, attributes: dict[str, object]) -> None:
        """Fill attr_table from an item's attributes dict: keys → str, values → typed."""
        self.attr_table.blockSignals(True)
        self.attr_table.setRowCount(0)

        for key, value in attributes.items():
            row = self.attr_table.rowCount()
            self.attr_table.insertRow(row)

            # Key
            key_item = QTableWidgetItem(str(key))
            self.attr_table.setItem(row, 0, key_item)

            # Detect type
            if isinstance(value, bool):
                type_str, val_str = "Boolean", "1" if value else "0"
            elif isinstance(value, int):
                type_str, val_str = "Number", str(value)
            elif isinstance(value, float):
                type_str, val_str = "Float", str(value)
            else:
                type_str, val_str = "String", str(value)

            # Type dropdown cell
            type_combo = QComboBox()
            type_combo.addItems(self._ATTR_TYPES)
            type_combo.setCurrentText(type_str)
            self.attr_table.setCellWidget(row, 1, type_combo)

            # Value
            val_item = QTableWidgetItem(val_str)
            self.attr_table.setItem(row, 2, val_item)

        self.attr_table.blockSignals(False)

    def _collect_attributes(self) -> dict[str, object]:
        """Read all rows from attr_table and return a key→typed-value dict."""
        result: dict[str, object] = {}
        for row in range(self.attr_table.rowCount()):
            key_item = self.attr_table.item(row, 0)
            val_item = self.attr_table.item(row, 2)
            if not key_item or not key_item.text().strip():
                continue

            key = key_item.text().strip()
            val_str = val_item.text() if val_item else ""

            type_combo = self.attr_table.cellWidget(row, 1)
            type_str = type_combo.currentText() if type_combo else "String"

            try:
                if type_str == "Number":
                    result[key] = int(val_str)
                elif type_str == "Float":
                    result[key] = float(val_str)
                elif type_str == "Boolean":
                    result[key] = val_str == "1" or val_str.lower() == "true"
                else:
                    result[key] = val_str
            except (ValueError, TypeError):
                result[key] = val_str

        return result

    def _on_attr_cell_changed(self, row: int, col: int) -> None:
        """Mark attributes as changed when any cell edits."""
        if col in (0, 2):  # Key or Value column changed
            self._mark_changed("custom_attributes", self._collect_attributes())

    def _on_add_attribute(self) -> None:
        """Append a new empty row (C++ PropertiesWindow::OnClickAddAttribute parity)."""
        row = self.attr_table.rowCount()
        self.attr_table.insertRow(row)
        self.attr_table.setItem(row, 0, QTableWidgetItem(""))

        type_combo = QComboBox()
        type_combo.addItems(self._ATTR_TYPES)
        self.attr_table.setCellWidget(row, 1, type_combo)

        self.attr_table.setItem(row, 2, QTableWidgetItem(""))
        self.attr_table.editItem(self.attr_table.item(row, 0))
        self._mark_changed("custom_attributes", self._collect_attributes())

    def _on_remove_attribute(self) -> None:
        """Remove selected row (C++ PropertiesWindow::OnClickRemoveAttribute parity)."""
        rows = self.attr_table.selectedItems()
        if not rows:
            return
        row = self.attr_table.currentRow()
        if row >= 0:
            self.attr_table.removeRow(row)
            self._mark_changed("custom_attributes", self._collect_attributes())

    def _mark_changed(self, field: str, value: Any) -> None:
        """Mark a field as changed."""
        # Enable buttons
        self.btn_apply.setEnabled(True)
        self.btn_revert.setEnabled(True)

        # Track change
        self._pending_changes.append(
            PropertyChange(
                field_name=field,
                old_value=None,  # Would need to track original
                new_value=value,
            )
        )

    def _on_apply(self) -> None:
        """Apply pending changes."""
        if not self._pending_changes:
            return

        # Get parent editor session
        parent = self.parent()
        session = getattr(parent, "session", None)
        if hasattr(parent, "parent") and session is None:  # In case docked
            session = getattr(parent.parent(), "session", None)

        if session is None:
            return

        # Collate changes
        changes = {c.field_name: c.new_value for c in self._pending_changes}

        context_type = "tile"
        if self._current_item:
            context_type = "item"
        elif self._current_house:
            context_type = "house"
        elif self.spawn_type.text() != "—":  # Spawn
            context_type = "spawn"

        session.apply_property_changes(
            context_type=context_type, context_details=self._current_details, changes=changes
        )

        self._pending_changes.clear()
        self.btn_apply.setEnabled(False)
        self.btn_revert.setEnabled(False)

    def _on_revert(self) -> None:
        """Revert to original values."""
        self._pending_changes.clear()
        self.btn_apply.setEnabled(False)
        self.btn_revert.setEnabled(False)

        # Reload current entity
        if self._current_tile:
            self.show_tile(self._current_tile)
        elif self._current_item:
            self.show_item(self._current_item)
        elif self._current_house:
            self.show_house(self._current_house)

        self.changes_reverted.emit()

    def show_tile(self, tile: Tile) -> None:
        """Display tile properties."""
        self._current_tile = tile
        self._current_item = None
        self._current_house = None
        self._current_details = {"x": tile.x, "y": tile.y, "z": tile.z}
        self._pending_changes.clear()

        self.header.setText(f"Tile @ ({tile.x}, {tile.y}, {tile.z})")
        self.tabs.setCurrentIndex(0)

        # Update fields
        self.tile_position.setText(f"({tile.x}, {tile.y}, {tile.z})")

        ground_text = str(tile.ground.id) if tile.ground else "None"
        self.tile_ground.setText(ground_text)

        self.tile_house_id.blockSignals(True)
        self.tile_house_id.setValue(tile.house_id or 0)
        self.tile_house_id.blockSignals(False)

        # Parse flags
        flags = tile.map_flags or 0
        self.flag_pz.blockSignals(True)
        self.flag_pz.setChecked(bool(flags & 0x01))
        self.flag_pz.blockSignals(False)

        self.flag_no_logout.blockSignals(True)
        self.flag_no_logout.setChecked(bool(flags & 0x02))
        self.flag_no_logout.blockSignals(False)

        self.btn_apply.setEnabled(False)
        self.btn_revert.setEnabled(False)

    def show_item(self, item: Item, position: tuple[int, int, int] | None = None, stack_pos: int = -1) -> None:
        """Display item properties."""
        self._current_item = item
        self._current_tile = None
        self._current_house = None

        if position:
            self._current_details = {"x": position[0], "y": position[1], "z": position[2], "stack_pos": stack_pos}
        else:
            self._current_details = {}

        self._pending_changes.clear()

        self.header.setText(f"Item #{item.id}")
        self.tabs.setCurrentIndex(1)

        # Update fields
        self.item_id.setText(str(item.id))
        self.item_client_id.setText(str(item.client_id or "—"))

        self.item_count.blockSignals(True)
        self.item_count.setValue(item.count or 0)
        self.item_count.blockSignals(False)

        self.item_action_id.blockSignals(True)
        self.item_action_id.setValue(getattr(item, "action_id", 0) or 0)
        self.item_action_id.blockSignals(False)

        self.item_unique_id.blockSignals(True)
        self.item_unique_id.setValue(getattr(item, "unique_id", 0) or 0)
        self.item_unique_id.blockSignals(False)

        self.item_text.blockSignals(True)
        self.item_text.setText(getattr(item, "text", "") or "")
        self.item_text.blockSignals(False)

        # Destination
        dest = getattr(item, "destination", None)
        if dest:
            self.item_dest_x.setValue(int(dest.x))
            self.item_dest_y.setValue(int(dest.y))
            self.item_dest_z.setValue(int(dest.z))
        else:
            self.item_dest_x.setValue(0)
            self.item_dest_y.setValue(0)
            self.item_dest_z.setValue(0)

        # Update Preview
        try:
            from py_rme_canary.logic_layer.asset_manager import AssetManager

            pm = AssetManager.instance().get_sprite(int(item.id))
            if pm:
                self.item_preview.setPixmap(pm.scaled(32, 32, aspectRatioMode=1))  # Keep aspect
            else:
                self.item_preview.clear()
        except Exception:
            self.item_preview.clear()

        # Connect dest fields
        self.item_dest_x.valueChanged.connect(lambda v: self._mark_changed("destination_x", v))
        self.item_dest_y.valueChanged.connect(lambda v: self._mark_changed("destination_y", v))
        self.item_dest_z.valueChanged.connect(lambda v: self._mark_changed("destination_z", v))

        # --- Tier field visibility (C++ createClassificationFields parity) ---
        # Show tier for items with classification > 0, weapons, or wearable equipment
        classification = getattr(item, "classification", 0) or 0
        is_weapon = getattr(item, "is_weapon", False)
        is_equipment = getattr(item, "is_wearable_equipment", False) or getattr(item, "is_equipment", False)
        show_tier = bool(classification > 0 or is_weapon or is_equipment)
        self.item_tier_label.setVisible(show_tier)
        self.item_tier.setVisible(show_tier)
        if show_tier:
            self.item_tier.blockSignals(True)
            self.item_tier.setValue(getattr(item, "tier", 0) or 0)
            self.item_tier.blockSignals(False)

        # --- Advanced Attributes tab (C++ createAttributesPanel parity) ---
        raw_attrs = getattr(item, "attributes", None) or getattr(item, "extra_attributes", None) or {}
        self._populate_attr_table(raw_attrs)
        # Show or hide the Advanced tab (index 2)
        self.tabs.setTabVisible(2, True)

        self.btn_apply.setEnabled(False)
        self.btn_revert.setEnabled(False)

    def show_house(self, house: House) -> None:
        """Display house properties."""
        self._current_house = house
        self._current_tile = None
        self._current_item = None
        self._pending_changes.clear()

        self.header.setText(f"House #{house.id}")
        self.tabs.setCurrentIndex(2)

        # Update fields
        self.house_id.setText(str(house.id))

        self.house_name.blockSignals(True)
        self.house_name.setText(house.name or "")
        self.house_name.blockSignals(False)

        self.house_rent.blockSignals(True)
        self.house_rent.setValue(house.rent or 0)
        self.house_rent.blockSignals(False)

        self.house_guildhall.blockSignals(True)
        self.house_guildhall.setChecked(getattr(house, "guildhall", False))
        self.house_guildhall.blockSignals(False)

        # Entry position
        entry = house.entry
        if entry:
            self.house_entry.setText(f"({int(entry.x)}, {int(entry.y)}, {int(entry.z)})")
        else:
            self.house_entry.setText("Not set")

        # Doors (placeholder)
        self.house_doors.setText("—")

        self.btn_apply.setEnabled(False)
        self.btn_revert.setEnabled(False)

    def show_spawn(self, area: MonsterSpawnArea | NpcSpawnArea, spawn_type: str = "Monster") -> None:
        """Display spawn area properties."""
        self._current_tile = None
        self._current_item = None
        self._current_house = None
        self._pending_changes.clear()

        self.header.setText(f"{spawn_type} Spawn Area")
        self.tabs.setCurrentIndex(3)

        # Update fields
        self.spawn_type.setText(spawn_type)

        center = area.center
        self.spawn_center.setText(f"({int(center.x)}, {int(center.y)}, {int(center.z)})")

        self.spawn_radius.blockSignals(True)
        self.spawn_radius.setValue(area.radius)
        self.spawn_radius.blockSignals(False)

        # Count
        creatures = getattr(area, "monsters", []) or getattr(area, "npcs", []) or []
        self.spawn_count.setText(str(len(creatures)))

        self.btn_apply.setEnabled(False)
        self.btn_revert.setEnabled(False)

    def clear(self) -> None:
        """Clear all displayed properties."""
        self._current_tile = None
        self._current_item = None
        self._current_house = None
        self._pending_changes.clear()

        self.header.setText("Select an entity")

        self.btn_apply.setEnabled(False)
        self.btn_revert.setEnabled(False)
