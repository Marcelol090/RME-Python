"""Zone and Town Management Dialogs.

Modern dialogs for:
- Zone creation/editing
- Town management
- Temple position settings
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtGui import QColor

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.zones import Zone


class ColorButton(QPushButton):
    """Button that shows and allows selecting a color."""
    
    color_changed = pyqtSignal(QColor)
    
    def __init__(
        self,
        color: QColor = QColor(139, 92, 246),
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        
        self._color = color
        self.setFixedSize(60, 30)
        self.clicked.connect(self._pick_color)
        self._update_style()
        
    def _update_style(self) -> None:
        """Update button appearance."""
        self.setStyleSheet(f"""
            ColorButton {{
                background: {self._color.name()};
                border: 2px solid #363650;
                border-radius: 6px;
            }}
            ColorButton:hover {{
                border-color: #8B5CF6;
            }}
        """)
        
    def _pick_color(self) -> None:
        """Open color picker."""
        color = QColorDialog.getColor(
            self._color,
            self.parentWidget(),
            "Select Color"
        )
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


class ZoneListDialog(QDialog):
    """Dialog for managing map zones.
    
    Zones are named areas with associated colors for visualization.
    """
    
    zone_selected = pyqtSignal(str)
    
    def __init__(
        self,
        game_map: "GameMap | None" = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        
        self._game_map = game_map
        
        self.setWindowTitle("Zone Manager")
        self.setMinimumSize(400, 400)
        self.setModal(True)
        
        self._setup_ui()
        self._apply_style()
        self._load_zones()
        
    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🗺️ Zones")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #E5E5E7;
        """)
        layout.addWidget(header)
        
        # Zone list
        self.zone_list = QListWidget()
        self.zone_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.zone_list.itemDoubleClicked.connect(self._on_edit)
        layout.addWidget(self.zone_list)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)
        
        self.btn_add = QPushButton("➕ New Zone")
        self.btn_add.clicked.connect(self._on_add)
        action_layout.addWidget(self.btn_add)
        
        self.btn_edit = QPushButton("✏️ Edit")
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._on_edit)
        action_layout.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton("🗑️ Delete")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete)
        action_layout.addWidget(self.btn_delete)
        
        action_layout.addStretch()
        
        layout.addLayout(action_layout)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
        
    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        self.setStyleSheet("""
            QDialog {
                background: #1E1E2E;
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
            }
            
            QPushButton:hover {
                background: #404060;
                border-color: #8B5CF6;
            }
            
            QPushButton:disabled {
                background: #2A2A3E;
                color: #52525B;
            }
        """)
        
    def _load_zones(self) -> None:
        """Load zones from map."""
        self.zone_list.clear()
        
        if not self._game_map:
            return
            
        zones = getattr(self._game_map, 'zones', {}) or {}
        
        for zone_id, zone in sorted(zones.items()):
            # Create colored indicator
            color = getattr(zone, 'color', None)
            if color:
                color_text = f"● "
            else:
                color_text = "○ "
                
            name = getattr(zone, 'name', zone_id) or zone_id
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
            name = values.get('name', '')
            
            if not name:
                return
                
            # Create zone
            if not self._game_map:
                return
                
            if not hasattr(self._game_map, 'zones') or self._game_map.zones is None:
                self._game_map.zones = {}
                
            # Find unique ID
            zone_id = name.lower().replace(' ', '_')
            
            # Store zone (simplified - would need Zone class)
            self._game_map.zones[zone_id] = {
                'name': name,
                'color': values.get('color', '#8B5CF6')
            }
            
            self._load_zones()
            
    def _on_edit(self) -> None:
        """Edit selected zone."""
        item = self.zone_list.currentItem()
        if not item:
            return
            
        zone_id = item.data(Qt.ItemDataRole.UserRole)
        if not zone_id or not self._game_map:
            return
            
        zones = getattr(self._game_map, 'zones', {}) or {}
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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            zones = getattr(self._game_map, 'zones', {}) or {}
            if zone_id in zones:
                del zones[zone_id]
                self._load_zones()


class ZoneEditDialog(QDialog):
    """Dialog for editing zone properties."""
    
    def __init__(
        self,
        zone: object | None = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        
        self._zone = zone
        self._is_new = zone is None
        
        self.setWindowTitle("New Zone" if self._is_new else "Edit Zone")
        self.setMinimumWidth(300)
        self.setModal(True)
        
        self._setup_ui()
        self._apply_style()
        
    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Form
        form = QFormLayout()
        form.setSpacing(12)
        
        # Name
        name = ""
        if self._zone:
            name = getattr(self._zone, 'name', '') or (
                self._zone.get('name', '') if isinstance(self._zone, dict) else ''
            )
        self.name_input = QLineEdit(name)
        self.name_input.setPlaceholderText("Zone name...")
        form.addRow("Name:", self.name_input)
        
        # Color
        color = QColor(139, 92, 246)
        if self._zone:
            color_str = getattr(self._zone, 'color', None) or (
                self._zone.get('color', None) if isinstance(self._zone, dict) else None
            )
            if color_str:
                color = QColor(color_str)
                
        self.color_btn = ColorButton(color)
        form.addRow("Color:", self.color_btn)
        
        layout.addLayout(form)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet("""
            QDialog {
                background: #1E1E2E;
                color: #E5E5E7;
            }
            
            QLineEdit {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 6px;
                padding: 8px;
                color: #E5E5E7;
            }
            
            QLineEdit:focus {
                border-color: #8B5CF6;
            }
            
            QLabel {
                color: #A1A1AA;
            }
        """)
        
    def get_values(self) -> dict:
        """Get entered values."""
        return {
            'name': self.name_input.text().strip(),
            'color': self.color_btn.color().name()
        }


class TownListDialog(QDialog):
    """Dialog for managing map towns.
    
    Towns have temple positions for player respawning.
    """
    
    goto_position = pyqtSignal(int, int, int)
    
    def __init__(
        self,
        game_map: "GameMap | None" = None,
        current_pos: tuple[int, int, int] | None = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        
        self._game_map = game_map
        self._current_pos = current_pos or (0, 0, 7)
        
        self.setWindowTitle("Town Manager")
        self.setMinimumSize(450, 400)
        self.setModal(True)
        
        self._setup_ui()
        self._apply_style()
        self._load_towns()
        
    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("🏰 Towns")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #E5E5E7;
        """)
        layout.addWidget(header)
        
        # Town list
        self.town_list = QListWidget()
        self.town_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.town_list.itemDoubleClicked.connect(self._on_goto_temple)
        layout.addWidget(self.town_list)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)
        
        self.btn_add = QPushButton("➕ New Town")
        self.btn_add.clicked.connect(self._on_add)
        action_layout.addWidget(self.btn_add)
        
        self.btn_goto = QPushButton("🚀 Go To Temple")
        self.btn_goto.setEnabled(False)
        self.btn_goto.clicked.connect(self._on_goto_temple)
        action_layout.addWidget(self.btn_goto)
        
        self.btn_set_temple = QPushButton("📍 Set Temple Here")
        self.btn_set_temple.setEnabled(False)
        self.btn_set_temple.clicked.connect(self._on_set_temple)
        action_layout.addWidget(self.btn_set_temple)
        
        self.btn_delete = QPushButton("🗑️")
        self.btn_delete.setFixedWidth(40)
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._on_delete)
        action_layout.addWidget(self.btn_delete)
        
        layout.addLayout(action_layout)
        
        # Current position
        pos_label = QLabel(
            f"Current: ({self._current_pos[0]}, {self._current_pos[1]}, {self._current_pos[2]})"
        )
        pos_label.setStyleSheet("color: #52525B; font-size: 11px;")
        layout.addWidget(pos_label)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)
        
    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        self.setStyleSheet("""
            QDialog {
                background: #1E1E2E;
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
                padding: 8px 12px;
            }
            
            QPushButton:hover {
                background: #404060;
                border-color: #8B5CF6;
            }
            
            QPushButton:disabled {
                background: #2A2A3E;
                color: #52525B;
            }
        """)
        
    def _load_towns(self) -> None:
        """Load towns from map."""
        self.town_list.clear()
        
        if not self._game_map:
            return
            
        towns = getattr(self._game_map, 'towns', {}) or {}
        
        for town_id, town in sorted(towns.items()):
            name = getattr(town, 'name', f"Town {town_id}") or f"Town {town_id}"
            temple = getattr(town, 'temple', None)
            
            if temple:
                temple_text = f"({int(temple.x)}, {int(temple.y)}, {int(temple.z)})"
            else:
                temple_text = "Temple not set"
                
            text = f"🏰 {name}\n    ID: {town_id} | {temple_text}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, {
                'id': town_id,
                'name': name,
                'temple': temple
            })
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
            self.btn_goto.setEnabled(data.get('temple') is not None)
            
    def _on_add(self) -> None:
        """Create new town."""
        name, ok = QInputDialog.getText(
            self,
            "New Town",
            "Town name:"
        )
        
        if not ok or not name:
            return
            
        if not self._game_map:
            return
            
        towns = getattr(self._game_map, 'towns', {}) or {}
        
        # Find next ID
        next_id = max([int(k) for k in towns.keys()], default=0) + 1
        
        # Create town (simplified)
        if not hasattr(self._game_map, 'towns') or self._game_map.towns is None:
            self._game_map.towns = {}
            
        # Would need Town class
        from dataclasses import dataclass, field
        
        @dataclass
        class TownData:
            name: str
            temple: object = None
            
        self._game_map.towns[next_id] = TownData(name=name)
        self._load_towns()
        
    def _on_goto_temple(self) -> None:
        """Navigate to selected town's temple."""
        item = self.town_list.currentItem()
        if not item:
            return
            
        data = item.data(Qt.ItemDataRole.UserRole)
        if not data:
            return
            
        temple = data.get('temple')
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
            
        town_id = data.get('id')
        towns = getattr(self._game_map, 'towns', {}) or {}
        town = towns.get(town_id)
        
        if town:
            from py_rme_canary.core.data.position import Position
            town.temple = Position(
                x=self._current_pos[0],
                y=self._current_pos[1],
                z=self._current_pos[2]
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
            
        town_id = data.get('id')
        name = data.get('name', f"Town {town_id}")
        
        reply = QMessageBox.question(
            self,
            "Delete Town",
            f"Delete town '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            towns = getattr(self._game_map, 'towns', {}) or {}
            if town_id in towns:
                del towns[town_id]
                self._load_towns()
