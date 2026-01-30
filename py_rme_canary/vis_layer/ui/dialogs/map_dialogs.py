"""Map Properties Dialog - Edit map metadata.

Modern dialog for editing map name, dimensions,
external file paths, and viewing statistics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
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

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


class MapPropertiesDialog(QDialog):
    """Dialog for editing map properties.

    Features:
    - General tab: dimensions, description
    - Files tab: external file paths
    - Statistics tab: read-only stats
    """

    def __init__(self, game_map: GameMap | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._game_map = game_map

        self.setWindowTitle("Map Properties")
        self.setMinimumSize(500, 400)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()
        self._load_values()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), "General")
        tabs.addTab(self._create_files_tab(), "External Files")
        tabs.addTab(self._create_stats_tab(), "Statistics")
        layout.addWidget(tabs)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

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
        self.otbm_version = QLabel("—")
        self.otbm_version.setStyleSheet("color: #A1A1AA;")
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

    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        self.setStyleSheet("""
            QDialog {
                background: #1E1E2E;
                color: #E5E5E7;
            }
            
            QGroupBox {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 8px;
                font-weight: 600;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #A1A1AA;
            }
            
            QLineEdit, QTextEdit, QSpinBox {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 6px;
                padding: 8px;
                color: #E5E5E7;
            }
            
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
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
            
            QTabWidget::pane {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 8px;
            }
            
            QTabBar::tab {
                background: #1E1E2E;
                color: #A1A1AA;
                padding: 8px 16px;
                border: 1px solid #363650;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            
            QTabBar::tab:selected {
                background: #2A2A3E;
                color: #E5E5E7;
            }
        """)

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


class AboutDialog(QDialog):
    """About dialog with app info, credits, and links."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("About py_rme_canary")
        self.setFixedSize(400, 350)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo/Icon placeholder
        icon = QLabel("🗺️")
        icon.setStyleSheet("font-size: 48px;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        # Title
        title = QLabel("py_rme_canary")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: 700;
            color: #E5E5E7;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Version
        version = QLabel("Version 1.0.0-alpha")
        version.setStyleSheet("color: #8B5CF6; font-size: 13px;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        # Description
        desc = QLabel("Modern Python port of Remere's Map Editor\nfor Open Tibia servers")
        desc.setStyleSheet("color: #A1A1AA; font-size: 12px;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addStretch()

        # Credits
        credits = QLabel("Based on Remere's Map Editor by the RME Team\nPython port: py_rme_canary Team")
        credits.setStyleSheet("color: #52525B; font-size: 11px;")
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits)

        # License
        license_label = QLabel("Licensed under GPL v3")
        license_label.setStyleSheet("color: #52525B; font-size: 10px;")
        license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(license_label)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMaximumWidth(100)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _apply_style(self) -> None:
        """Apply dark styling."""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2A2A3E, stop:1 #1E1E2E);
            }
            
            QPushButton {
                background: #8B5CF6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: 500;
            }
            
            QPushButton:hover {
                background: #A78BFA;
            }
        """)
