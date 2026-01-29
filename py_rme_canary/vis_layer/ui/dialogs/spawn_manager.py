"""Spawn Manager Dialog.

Modern dialog for managing monster and NPC spawns:
- List all spawns with creature counts
- Edit spawn properties
- Add/remove creatures from spawns
- Navigate to spawn locations
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


class SpawnCard(QFrame):
    """Card showing spawn information."""

    clicked = pyqtSignal(object)  # spawn
    goto_clicked = pyqtSignal(int, int, int)
    edit_clicked = pyqtSignal(object)

    def __init__(
        self,
        spawn: object,
        spawn_type: str = "monster",
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._spawn = spawn
        self._spawn_type = spawn_type
        self._selected = False

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        header = QHBoxLayout()

        icon = "👹" if self._spawn_type == "monster" else "👤"
        type_name = "Monster Spawn" if self._spawn_type == "monster" else "NPC Spawn"

        title = QLabel(f"{icon} {type_name}")
        title.setStyleSheet("font-weight: 600; color: #E5E5E7; font-size: 12px;")
        header.addWidget(title)

        header.addStretch()

        # Radius badge
        radius = getattr(self._spawn, 'radius', 0)
        badge = QLabel(f"r={radius}")
        badge.setStyleSheet("""
            background: #363650;
            color: #A1A1AA;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
        """)
        header.addWidget(badge)

        layout.addLayout(header)

        # Position
        center = self._spawn.center
        pos = f"📍 ({int(center.x)}, {int(center.y)}, {int(center.z)})"
        pos_label = QLabel(pos)
        pos_label.setStyleSheet("color: #A1A1AA; font-size: 11px;")
        layout.addWidget(pos_label)

        # Creature list
        if self._spawn_type == "monster":
            creatures = getattr(self._spawn, 'monsters', []) or []
        else:
            creatures = getattr(self._spawn, 'npcs', []) or []

        if creatures:
            creature_names = [getattr(c, 'name', '?') for c in creatures[:3]]
            if len(creatures) > 3:
                creature_names.append(f"+{len(creatures) - 3} more")
            creatures_text = ", ".join(creature_names)
        else:
            creatures_text = "No creatures"

        creatures_label = QLabel(creatures_text)
        creatures_label.setStyleSheet("color: #52525B; font-size: 10px;")
        creatures_label.setWordWrap(True)
        layout.addWidget(creatures_label)

        # Action buttons
        actions = QHBoxLayout()
        actions.setSpacing(6)

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
            SpawnCard {{
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
        """Handle go to."""
        center = self._spawn.center
        self.goto_clicked.emit(int(center.x), int(center.y), int(center.z))

    def _on_edit(self) -> None:
        """Handle edit."""
        self.edit_clicked.emit(self._spawn)

    def mousePressEvent(self, event: object) -> None:
        """Handle click."""
        self.clicked.emit(self._spawn)
        super().mousePressEvent(event)


class SpawnEditDialog(QDialog):
    """Dialog for editing a spawn."""

    def __init__(
        self,
        spawn: object,
        spawn_type: str = "monster",
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._spawn = spawn
        self._spawn_type = spawn_type

        icon = "👹" if spawn_type == "monster" else "👤"
        self.setWindowTitle(f"{icon} Edit {'Monster' if spawn_type == 'monster' else 'NPC'} Spawn")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Position
        center = self._spawn.center
        pos_label = QLabel(f"📍 Position: ({int(center.x)}, {int(center.y)}, {int(center.z)})")
        pos_label.setStyleSheet("color: #A1A1AA; font-size: 12px;")
        layout.addWidget(pos_label)

        # Form
        form = QFormLayout()
        form.setSpacing(12)

        # Radius
        self.radius_spin = QSpinBox()
        self.radius_spin.setRange(1, 15)
        self.radius_spin.setValue(getattr(self._spawn, 'radius', 3))
        form.addRow("Radius:", self.radius_spin)

        # Spawn time (for monsters)
        if self._spawn_type == "monster":
            self.spawn_time = QSpinBox()
            self.spawn_time.setRange(1, 3600)
            self.spawn_time.setValue(getattr(self._spawn, 'spawn_time', 60))
            self.spawn_time.setSuffix(" sec")
            form.addRow("Spawn time:", self.spawn_time)

        layout.addLayout(form)

        # Creature list
        creatures_label = QLabel("Creatures:")
        creatures_label.setStyleSheet("color: #E5E5E7; font-weight: 600;")
        layout.addWidget(creatures_label)

        self.creature_list = QListWidget()
        self.creature_list.setMaximumHeight(150)

        if self._spawn_type == "monster":
            creatures = getattr(self._spawn, 'monsters', []) or []
        else:
            creatures = getattr(self._spawn, 'npcs', []) or []

        for creature in creatures:
            name = getattr(creature, 'name', '?')
            item = QListWidgetItem(f"• {name}")
            item.setData(Qt.ItemDataRole.UserRole, creature)
            self.creature_list.addItem(item)

        layout.addWidget(self.creature_list)

        # Creature actions
        creature_actions = QHBoxLayout()

        self.creature_input = QLineEdit()
        self.creature_input.setPlaceholderText("Creature name...")
        creature_actions.addWidget(self.creature_input)

        btn_add = QPushButton("Add")
        btn_add.clicked.connect(self._add_creature)
        creature_actions.addWidget(btn_add)

        btn_remove = QPushButton("Remove")
        btn_remove.clicked.connect(self._remove_creature)
        creature_actions.addWidget(btn_remove)

        layout.addLayout(creature_actions)

        layout.addStretch()

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

            QSpinBox, QLineEdit {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 6px;
                padding: 8px;
                color: #E5E5E7;
            }

            QSpinBox:focus, QLineEdit:focus {
                border-color: #8B5CF6;
            }

            QListWidget {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 6px;
                color: #E5E5E7;
            }

            QPushButton {
                background: #363650;
                color: #E5E5E7;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }

            QPushButton:hover {
                background: #8B5CF6;
            }
        """)

    def _add_creature(self) -> None:
        """Add creature to list."""
        name = self.creature_input.text().strip()
        if not name:
            return

        item = QListWidgetItem(f"• {name}")
        self.creature_list.addItem(item)
        self.creature_input.clear()

    def _remove_creature(self) -> None:
        """Remove selected creature."""
        item = self.creature_list.currentItem()
        if item:
            row = self.creature_list.row(item)
            self.creature_list.takeItem(row)

    def get_values(self) -> dict:
        """Get edited values."""
        creatures = []
        for i in range(self.creature_list.count()):
            item = self.creature_list.item(i)
            text = item.text().lstrip("• ")
            creatures.append(text)

        values = {
            'radius': self.radius_spin.value(),
            'creatures': creatures
        }

        if self._spawn_type == "monster":
            values['spawn_time'] = self.spawn_time.value()

        return values


class SpawnManagerDialog(QDialog):
    """Main spawn manager dialog.

    Signals:
        goto_position: Emits (x, y, z) for navigation
    """

    goto_position = pyqtSignal(int, int, int)

    def __init__(
        self,
        game_map: "GameMap | None" = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._game_map = game_map
        self._spawn_cards: list[SpawnCard] = []

        self.setWindowTitle("Spawn Manager")
        self.setMinimumSize(550, 500)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()
        self._load_spawns()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        header = QLabel("👹 Spawn Manager")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: 700;
            color: #E5E5E7;
        """)
        header_layout.addWidget(header)

        header_layout.addStretch()

        self.count_label = QLabel("")
        self.count_label.setStyleSheet("color: #A1A1AA;")
        header_layout.addWidget(self.count_label)

        layout.addLayout(header_layout)

        # Tabs for monster/npc
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: #2A2A3E;
                color: #A1A1AA;
                padding: 10px 20px;
                border-radius: 6px 6px 0 0;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #8B5CF6;
                color: white;
            }
        """)

        # Monster spawns tab
        monster_tab = QWidget()
        monster_layout = QVBoxLayout(monster_tab)
        monster_layout.setContentsMargins(0, 12, 0, 0)

        monster_scroll = QScrollArea()
        monster_scroll.setWidgetResizable(True)
        monster_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.monster_container = QWidget()
        self.monster_layout = QVBoxLayout(self.monster_container)
        self.monster_layout.setSpacing(8)
        self.monster_layout.addStretch()

        monster_scroll.setWidget(self.monster_container)
        monster_layout.addWidget(monster_scroll)

        self.tabs.addTab(monster_tab, "👹 Monsters")

        # NPC spawns tab
        npc_tab = QWidget()
        npc_layout = QVBoxLayout(npc_tab)
        npc_layout.setContentsMargins(0, 12, 0, 0)

        npc_scroll = QScrollArea()
        npc_scroll.setWidgetResizable(True)
        npc_scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.npc_container = QWidget()
        self.npc_layout = QVBoxLayout(self.npc_container)
        self.npc_layout.setSpacing(8)
        self.npc_layout.addStretch()

        npc_scroll.setWidget(self.npc_container)
        npc_layout.addWidget(npc_scroll)

        self.tabs.addTab(npc_tab, "👤 NPCs")

        layout.addWidget(self.tabs)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        layout.addWidget(buttons)

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet("""
            QDialog {
                background: #1E1E2E;
            }
        """)

    def _load_spawns(self) -> None:
        """Load spawns from map."""
        # Clear existing
        for card in self._spawn_cards:
            card.deleteLater()
        self._spawn_cards.clear()

        # Clear layouts (except stretch)
        for layout in [self.monster_layout, self.npc_layout]:
            while layout.count() > 1:
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        if not self._game_map:
            self.count_label.setText("No map loaded")
            return

        monster_count = 0
        npc_count = 0

        # Monster spawns
        m_spawns = getattr(self._game_map, 'monster_spawns', []) or []
        for spawn in m_spawns:
            card = SpawnCard(spawn, "monster")
            card.goto_clicked.connect(self._on_goto)
            card.edit_clicked.connect(self._on_edit_spawn)

            self.monster_layout.insertWidget(self.monster_layout.count() - 1, card)
            self._spawn_cards.append(card)
            monster_count += 1

        # NPC spawns
        n_spawns = getattr(self._game_map, 'npc_spawns', []) or []
        for spawn in n_spawns:
            card = SpawnCard(spawn, "npc")
            card.goto_clicked.connect(self._on_goto)
            card.edit_clicked.connect(self._on_edit_spawn)

            self.npc_layout.insertWidget(self.npc_layout.count() - 1, card)
            self._spawn_cards.append(card)
            npc_count += 1

        # Update count
        self.count_label.setText(f"{monster_count} monster, {npc_count} NPC spawns")

        # Add empty messages if needed
        if monster_count == 0:
            empty = QLabel("No monster spawns defined")
            empty.setStyleSheet("color: #52525B; padding: 20px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.monster_layout.insertWidget(0, empty)

        if npc_count == 0:
            empty = QLabel("No NPC spawns defined")
            empty.setStyleSheet("color: #52525B; padding: 20px;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.npc_layout.insertWidget(0, empty)

    def _on_goto(self, x: int, y: int, z: int) -> None:
        """Handle go to."""
        self.goto_position.emit(x, y, z)

    def _on_edit_spawn(self, spawn: object) -> None:
        """Open spawn edit dialog."""
        spawn_type = "monster" if hasattr(spawn, 'monsters') else "npc"

        dialog = SpawnEditDialog(spawn, spawn_type, self)
        if dialog.exec():
            values = dialog.get_values()

            # Apply values
            spawn.radius = values['radius']
            if 'spawn_time' in values:
                spawn.spawn_time = values['spawn_time']

            # Would need to update creature list
            # This is simplified

            self._load_spawns()
