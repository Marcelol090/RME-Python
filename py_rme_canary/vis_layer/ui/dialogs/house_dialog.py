"""House Management Dialog.

Modern dialog for house operations:
- List all houses
- Create/edit/delete houses
- Set entry points
- Visual house info cards
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.houses import House


class HouseCard(QFrame):
    """Card displaying house information."""

    clicked = pyqtSignal(int)  # house_id
    goto_clicked = pyqtSignal(int, int, int)  # x, y, z
    edit_clicked = pyqtSignal(int)  # house_id

    def __init__(self, house: House, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._house = house
        self._selected = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header row
        header = QHBoxLayout()

        # House icon + name
        name = QLabel(f"🏠 {self._house.name or 'Unnamed House'}")
        name.setStyleSheet("font-weight: 600; color: #E5E5E7; font-size: 13px;")
        header.addWidget(name)

        header.addStretch()

        # ID badge
        id_badge = QLabel(f"#{self._house.id}")
        id_badge.setStyleSheet("""
            background: #363650;
            color: #A1A1AA;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-family: 'JetBrains Mono', monospace;
        """)
        header.addWidget(id_badge)

        layout.addLayout(header)

        # Info row
        info = QHBoxLayout()
        info.setSpacing(16)

        # Rent
        rent = self._house.rent or 0
        rent_label = QLabel(f"💰 {rent:,} gold")
        rent_label.setStyleSheet("color: #F59E0B; font-size: 11px;")
        info.addWidget(rent_label)

        # Guildhall indicator
        if getattr(self._house, "guildhall", False):
            guild_label = QLabel("⚔️ Guildhall")
            guild_label.setStyleSheet("color: #8B5CF6; font-size: 11px;")
            info.addWidget(guild_label)

        info.addStretch()

        layout.addLayout(info)

        # Entry position
        entry = self._house.entry
        if entry:
            entry_text = f"📍 Entry: ({int(entry.x)}, {int(entry.y)}, {int(entry.z)})"
        else:
            entry_text = "📍 Entry: Not set"

        entry_label = QLabel(entry_text)
        entry_label.setStyleSheet("color: #52525B; font-size: 10px;")
        layout.addWidget(entry_label)

        # Action buttons
        actions = QHBoxLayout()
        actions.setSpacing(8)

        if entry:
            goto_btn = QPushButton("Go To")
            goto_btn.setFixedHeight(24)
            goto_btn.clicked.connect(self._on_goto)
            actions.addWidget(goto_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setFixedHeight(24)
        edit_btn.clicked.connect(self._on_edit)
        actions.addWidget(edit_btn)

        actions.addStretch()

        layout.addLayout(actions)

    def _apply_style(self) -> None:
        """Apply styling."""
        border = "#8B5CF6" if self._selected else "#363650"
        bg = "#363650" if self._selected else "#2A2A3E"

        self.setStyleSheet(f"""
            HouseCard {{
                background: {bg};
                border: 2px solid {border};
                border-radius: 10px;
            }}
            
            QPushButton {{
                background: #404060;
                color: #E5E5E7;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 10px;
            }}
            
            QPushButton:hover {{
                background: #8B5CF6;
            }}
        """)

    def set_selected(self, selected: bool) -> None:
        """Set selection state."""
        self._selected = selected
        self._apply_style()

    def _on_goto(self) -> None:
        """Handle go to button."""
        entry = self._house.entry
        if entry:
            self.goto_clicked.emit(int(entry.x), int(entry.y), int(entry.z))

    def _on_edit(self) -> None:
        """Handle edit button."""
        self.edit_clicked.emit(self._house.id)

    def mousePressEvent(self, event: object) -> None:
        """Handle click."""
        self.clicked.emit(self._house.id)
        super().mousePressEvent(event)


class HouseListDialog(QDialog):
    """Dialog for managing map houses.

    Signals:
        house_selected: Emits house_id when selected
        goto_position: Emits (x, y, z) for navigation
    """

    house_selected = pyqtSignal(int)
    goto_position = pyqtSignal(int, int, int)

    def __init__(self, game_map: GameMap | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._game_map = game_map
        self._house_cards: list[HouseCard] = []
        self._selected_house_id: int | None = None

        self.setWindowTitle("House Manager")
        self.setMinimumSize(500, 500)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()
        self._load_houses()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("🏠 Houses")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #E5E5E7;
        """)
        header_layout.addWidget(header)

        header_layout.addStretch()

        self.count_label = QLabel("0 houses")
        self.count_label.setStyleSheet("color: #A1A1AA;")
        header_layout.addWidget(self.count_label)

        layout.addLayout(header_layout)

        # Search
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Search houses...")
        self.search.textChanged.connect(self._filter_list)
        layout.addWidget(self.search)

        # House cards scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setSpacing(8)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)

        # Action buttons
        action_layout = QHBoxLayout()

        self.btn_add = QPushButton("➕ New House")
        self.btn_add.clicked.connect(self._on_add)
        action_layout.addWidget(self.btn_add)

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

    def _load_houses(self) -> None:
        """Load houses from map."""
        # Clear existing cards
        for card in self._house_cards:
            card.deleteLater()
        self._house_cards.clear()

        # Clear layout (except stretch)
        while self.cards_layout.count() > 1:
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._game_map:
            self.count_label.setText("No map loaded")
            return

        houses = getattr(self._game_map, "houses", {}) or {}

        for house_id, house in sorted(houses.items()):
            card = HouseCard(house)
            card.clicked.connect(self._on_card_clicked)
            card.goto_clicked.connect(self._on_goto)
            card.edit_clicked.connect(self._on_edit)

            # Insert before stretch
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
            self._house_cards.append(card)

        count = len(houses)
        self.count_label.setText(f"{count} house{'s' if count != 1 else ''}")

        if count == 0:
            empty = QLabel("No houses defined yet.\nClick 'New House' to create one.")
            empty.setStyleSheet("color: #52525B; padding: 20px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.cards_layout.insertWidget(0, empty)

    def _filter_list(self, text: str) -> None:
        """Filter houses by search text."""
        text_lower = text.lower()

        for card in self._house_cards:
            name = card._house.name or ""
            house_id = str(card._house.id)
            visible = text_lower in name.lower() or text_lower in house_id
            card.setVisible(visible)

    def _on_card_clicked(self, house_id: int) -> None:
        """Handle card click."""
        self._selected_house_id = house_id

        for card in self._house_cards:
            card.set_selected(card._house.id == house_id)

        self.btn_delete.setEnabled(True)
        self.house_selected.emit(house_id)

    def _on_goto(self, x: int, y: int, z: int) -> None:
        """Handle go to click."""
        self.goto_position.emit(x, y, z)

    def _on_edit(self, house_id: int) -> None:
        """Open house edit dialog."""
        if not self._game_map:
            return

        houses = getattr(self._game_map, "houses", {}) or {}
        house = houses.get(house_id)

        if house:
            dialog = HouseEditDialog(house, parent=self)
            if dialog.exec():
                values = dialog.get_values()
                # Apply changes
                house.name = values.get("name", house.name)
                house.rent = values.get("rent", house.rent)
                if hasattr(house, "guildhall"):
                    house.guildhall = values.get("guildhall", False)
                self._load_houses()

    def _on_add(self) -> None:
        """Create new house."""
        if not self._game_map:
            return

        houses = getattr(self._game_map, "houses", {}) or {}

        # Find next available ID
        next_id = max(houses.keys(), default=0) + 1

        # Create house
        from py_rme_canary.core.data.houses import House

        new_house = House(id=next_id, name=f"House {next_id}")

        if not hasattr(self._game_map, "houses") or self._game_map.houses is None:
            self._game_map.houses = {}

        self._game_map.houses[next_id] = new_house
        self._load_houses()

        # Open edit dialog
        self._on_edit(next_id)

    def _on_delete(self) -> None:
        """Delete selected house."""
        if not self._selected_house_id or not self._game_map:
            return

        houses = getattr(self._game_map, "houses", {}) or {}
        house = houses.get(self._selected_house_id)

        if not house:
            return

        reply = QMessageBox.question(
            self,
            "Delete House",
            f"Delete house '{house.name}' (#{house.id})?\n\n"
            "This will also clear house IDs from all tiles assigned to this house.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            del houses[self._selected_house_id]
            self._selected_house_id = None
            self.btn_delete.setEnabled(False)
            self._load_houses()


class HouseEditDialog(QDialog):
    """Dialog for editing house properties."""

    def __init__(
        self,
        house: House | None = None,
        *,
        house_id: int | None = None,
        house_name: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        if house is None:
            from py_rme_canary.core.data.houses import House as HouseModel  # lazy import

            hid = house_id if house_id is not None else 0
            hname = house_name if house_name is not None else ""
            house = HouseModel(id=int(hid), name=hname)

        self._house = house

        self.setWindowTitle(f"Edit House #{self._house.id}")
        self.setMinimumWidth(350)
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
        self.name_input = QLineEdit(self._house.name or "")
        form.addRow("Name:", self.name_input)

        # Rent
        self.rent_input = QSpinBox()
        self.rent_input.setRange(0, 999999)
        self.rent_input.setValue(self._house.rent or 0)
        self.rent_input.setSuffix(" gold")
        form.addRow("Rent:", self.rent_input)

        # Guildhall
        self.guildhall_check = QCheckBox("Is Guildhall")
        self.guildhall_check.setChecked(getattr(self._house, "guildhall", False))
        form.addRow("", self.guildhall_check)

        layout.addLayout(form)

        # Entry position (read-only)
        entry = self._house.entry
        if entry:
            entry_text = f"Entry: ({int(entry.x)}, {int(entry.y)}, {int(entry.z)})"
        else:
            entry_text = "Entry: Not set"
        entry_label = QLabel(entry_text)
        entry_label.setStyleSheet("color: #A1A1AA; font-size: 11px;")
        layout.addWidget(entry_label)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
            
            QLineEdit, QSpinBox {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 6px;
                padding: 8px;
                color: #E5E5E7;
            }
            
            QLineEdit:focus, QSpinBox:focus {
                border-color: #8B5CF6;
            }
            
            QCheckBox {
                color: #E5E5E7;
            }
            
            QLabel {
                color: #A1A1AA;
            }
        """)

    def get_values(self) -> dict:
        """Get edited values."""
        return {
            "name": self.name_input.text().strip(),
            "rent": self.rent_input.value(),
            "guildhall": self.guildhall_check.isChecked(),
        }
