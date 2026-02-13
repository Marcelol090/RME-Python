"""Map Properties Dialog - Edit map metadata.

Modern dialog for editing map name, dimensions,
external file paths, and viewing statistics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


class MapPropertiesDialog(ModernDialog):
    """Dialog for editing map properties.

    Features:
    - General tab: dimensions, description
    - Files tab: external file paths
    - Statistics tab: read-only stats
    """

    def __init__(self, game_map: GameMap | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent, title="Map Properties")
        self._game_map = game_map

        self.setMinimumSize(500, 400)
        # ModernDialog handles modal and styling.

        self._setup_content()
        self._setup_footer()
        self._load_values()

    def _setup_content(self) -> None:
        """Initialize UI components."""
        self.content_layout.setSpacing(16)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_general_tab(), "General")
        self.tabs.addTab(self._create_files_tab(), "External Files")
        self.tabs.addTab(self._create_stats_tab(), "Statistics")
        self.content_layout.addWidget(self.tabs)

    def _setup_footer(self) -> None:
        """Setup dialog footer with buttons."""
        self.add_spacer_to_footer()
        self.add_button("Cancel", callback=self.reject, role="secondary")
        self.add_button("Ok", callback=self.accept, role="primary")

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Map name
        self.map_name = QLineEdit()
        self.map_name.setPlaceholderText("My Map")
        layout.addRow("Map Name:", self.map_name)

        # Dimensions
        dim_group = QGroupBox("Dimensions")
        dim_layout = QHBoxLayout(dim_group)

        self.width = QSpinBox()
        self.width.setRange(1, 65535)
        self.width.setValue(2048)
        self.width.setPrefix("W: ")
        dim_layout.addWidget(self.width)

        self.height = QSpinBox()
        self.height.setRange(1, 65535)
        self.height.setValue(2048)
        self.height.setPrefix("H: ")
        dim_layout.addWidget(self.height)

        layout.addRow(dim_group)

        # Description
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)
        self.description = QTextEdit()
        self.description.setPlaceholderText("Map description...")
        self.description.setMaximumHeight(100)
        desc_layout.addWidget(self.description)
        layout.addRow(desc_group)

        # OTBM version (read-only)
        tm = get_theme_manager()
        c = tm.tokens["color"]

        self.otbm_version = QLabel("—")
        self.otbm_version.setStyleSheet(f"color: {c['text']['tertiary']};")
        layout.addRow("OTBM Version:", self.otbm_version)

        return widget

    def _create_files_tab(self) -> QWidget:
        """Create external files tab."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Spawn monsters XML
        self.spawn_monsters_path = self._create_file_field("Spawn Monsters File:", "XML Files (*.xml)")
        layout.addRow("Monster Spawns:", self.spawn_monsters_path[0])

        # Spawn NPCs XML
        self.spawn_npcs_path = self._create_file_field("Spawn NPCs File:", "XML Files (*.xml)")
        layout.addRow("NPC Spawns:", self.spawn_npcs_path[0])

        # Houses XML
        self.houses_path = self._create_file_field("Houses File:", "XML Files (*.xml)")
        layout.addRow("Houses:", self.houses_path[0])

        return widget

    def _create_file_field(self, dialog_title: str, file_filter: str) -> tuple[QWidget, QLineEdit]:
        """Create a file path field with browse button."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        line_edit = QLineEdit()
        line_edit.setPlaceholderText("path/to/file.xml")
        layout.addWidget(line_edit)

        browse_btn = QPushButton("Browse...")
        browse_btn.setMaximumWidth(80)
        browse_btn.clicked.connect(lambda: self._browse_file(line_edit, dialog_title, file_filter))
        layout.addWidget(browse_btn)

        return container, line_edit

    def _browse_file(self, line_edit: QLineEdit, title: str, filter_str: str) -> None:
        """Open file browser dialog."""
        path, _ = QFileDialog.getOpenFileName(self, title, "", filter_str)
        if path:
            line_edit.setText(path)

    def _create_stats_tab(self) -> QWidget:
        """Create statistics tab (read-only)."""
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Statistics labels
        self.stat_tiles = QLabel("—")
        layout.addRow("Total Tiles:", self.stat_tiles)

        self.stat_houses = QLabel("—")
        layout.addRow("Houses:", self.stat_houses)

        self.stat_spawns = QLabel("—")
        layout.addRow("Spawn Areas:", self.stat_spawns)

        self.stat_waypoints = QLabel("—")
        layout.addRow("Waypoints:", self.stat_waypoints)

        self.stat_zones = QLabel("—")
        layout.addRow("Zones:", self.stat_zones)

        return widget

    def _load_values(self) -> None:
        """Load values from game map."""
        if not self._game_map:
            return

        gm = self._game_map

        # General
        self.map_name.setText(getattr(gm, "name", "") or "")
        self.width.setValue(getattr(gm, "width", 2048) or 2048)
        self.height.setValue(getattr(gm, "height", 2048) or 2048)
        self.description.setText(getattr(gm, "description", "") or "")

        # Statistics
        tiles_count = len(getattr(gm, "tiles", {}) or {})
        self.stat_tiles.setText(f"{tiles_count:,}")

        houses = getattr(gm, "houses", {}) or {}
        self.stat_houses.setText(str(len(houses)))

        m_spawns = len(getattr(gm, "monster_spawns", []) or [])
        n_spawns = len(getattr(gm, "npc_spawns", []) or [])
        self.stat_spawns.setText(f"{m_spawns} monsters, {n_spawns} NPCs")

        waypoints = getattr(gm, "waypoints", {}) or {}
        self.stat_waypoints.setText(str(len(waypoints)))

        zones = getattr(gm, "zones", {}) or {}
        self.stat_zones.setText(str(len(zones)))

    def get_values(self) -> dict:
        """Get edited values."""
        return {
            "name": self.map_name.text(),
            "width": self.width.value(),
            "height": self.height.value(),
            "description": self.description.toPlainText(),
        }
