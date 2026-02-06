from __future__ import annotations

import logging
import os
from collections import OrderedDict

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QKeySequence, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QDockWidget,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QStyle,
    QToolBar,
)

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.memory_guard import default_memory_guard
from py_rme_canary.logic_layer.brush_definitions import BrushManager
from py_rme_canary.logic_layer.drawing_options import DrawingOptions
from py_rme_canary.logic_layer.editor_session import EditorSession
from py_rme_canary.vis_layer.renderer import OpenGLCanvasWidget
from py_rme_canary.vis_layer.renderer.map_drawer import MapDrawer
from py_rme_canary.vis_layer.ui.docks.actions_history import ActionsHistoryDock
from py_rme_canary.vis_layer.ui.docks.minimap import MinimapWidget
from py_rme_canary.vis_layer.ui.drawing_options_coordinator import (
    DrawingOptionsCoordinator,
    create_coordinator,
)
from py_rme_canary.vis_layer.ui.helpers import Viewport
from py_rme_canary.vis_layer.ui.indicators import IndicatorService
from py_rme_canary.vis_layer.ui.main_window.find_item import open_find_item
from py_rme_canary.vis_layer.ui.main_window.find_on_map import open_find_waypoint
from py_rme_canary.logic_layer.friends_client import FriendsClient

logger = logging.getLogger(__name__)
from py_rme_canary.vis_layer.ui.docks.palette import PaletteManager
from py_rme_canary.vis_layer.ui.main_window.build_actions import build_actions
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_assets import QtMapEditorAssetsMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_brushes import QtMapEditorBrushesMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_dialogs import QtMapEditorDialogsMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_docks import QtMapEditorDocksMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_edit import QtMapEditorEditMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file import QtMapEditorFileMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_mirror import QtMapEditorMirrorMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_modern_ux import QtMapEditorModernUXMixin


class QtMapEditor(
    QMainWindow,
    QtMapEditorAssetsMixin,
    QtMapEditorBrushesMixin,
    QtMapEditorDialogsMixin,
    QtMapEditorDocksMixin,
    QtMapEditorEditMixin,
    QtMapEditorFileMixin,
    QtMapEditorMirrorMixin,
    QtMapEditorModernUXMixin,
):
    """
    Main editor window with split implementation for maintainability.
    """

    def __init__(self, assets_dir: str | None = None, parent: QMainWindow | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Py RME Canary - Map Editor")
        self.resize(1280, 800)

        # Initialize core logic
        self.session = EditorSession()
        self.map = self.session.game_map
        self.brush_manager = BrushManager()

        # Friends System
        self.friends_client = FriendsClient()
        self.friends_client.connect_to_server() # Start mock connection

        # Initialize UI state tracking
        self.viewport = Viewport()
        self.ghost_higher_floors = False
        self.show_client_box = False
        self.highlight_items = False
        self.show_monsters = True
        self.show_monsters_spawns = True
        self.show_npcs = True
        self.show_npcs_spawns = False
        self.show_special = False
        self.show_as_minimap = True
        self.only_show_colors = False
        self.only_show_modified = False
        self.show_houses_overlay = True
        self.show_pathing = False
        self.show_tooltips = True
        self.show_preview = True
        self.show_indicators = True
        self.palette_large_icons = False

        # Initialize sub-systems
        self.actions_history = ActionsHistoryDock(self.session)
        self.palette_manager = PaletteManager(self, self.brush_manager)
        self.indicator_service = IndicatorService(self)

        # Build UI
        self.canvas = OpenGLCanvasWidget(self)
        self.setCentralWidget(self.canvas)

        self.status = QStatusBar(self)
        self.setStatusBar(self.status)

        # Core actions + wiring live in ui/main_window/build_actions.py
        build_actions(self)

        self.drawing_options = DrawingOptions()
        self.drawing_options_coordinator = create_coordinator(self, self.drawing_options)
        self.drawing_options_coordinator.sync_from_editor()
        self.map_drawer = MapDrawer(options=self.drawing_options, game_map=self.map)

        # Screenshot parity: Edit menu (Find/Replace/Stats/Tools)
        self.act_find_item = QAction("Find Item...", self)
        self.act_find_item.setShortcut(QKeySequence("Ctrl+F"))
        self.act_find_item.triggered.connect(self._open_find_item_dialog)

        self.act_map_statistics = QAction("Map Statistics...", self)
        self.act_map_statistics.triggered.connect(self._show_map_statistics)

        self.act_replace_items = QAction("Replace Items...", self)
        self.act_replace_items.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self.act_replace_items.triggered.connect(self._open_replace_items_dialog)

        self.act_replace_items_on_selection = QAction("Replace Items on Selection...", self)
        self.act_replace_items_on_selection.triggered.connect(self._open_replace_items_on_selection_dialog)

        self.act_remove_item_on_selection = QAction("Remove Item on Selection...", self)
        self.act_remove_item_on_selection.triggered.connect(self._open_remove_item_on_selection_dialog)

        self.menu_find_on_map = QMenu("Find on Map", self)
        self.act_find_waypoint = QAction("Waypoint...", self)
        self.act_find_waypoint.triggered.connect(lambda _c=False: open_find_waypoint(self))
        self.menu_find_on_map.addAction(self.act_find_waypoint)

        self.act_find_on_map_item = QAction("Item...", self)
        self.act_find_on_map_item.triggered.connect(lambda _c=False: open_find_item(self))
        self.menu_find_on_map.addAction(self.act_find_on_map_item)

        self.menu_tools = QMenu("Tools", self)
        if hasattr(self, "act_clear_invalid_tiles_selection"):
            self.menu_tools.addAction(self.act_clear_invalid_tiles_selection)
        if hasattr(self, "act_clear_invalid_tiles_map"):
            self.menu_tools.addAction(self.act_clear_invalid_tiles_map)

        self.menu_tools.addSeparator()

        if hasattr(self, "act_randomize_selection"):
            self.menu_tools.addAction(self.act_randomize_selection)
        if hasattr(self, "act_randomize_map"):
            self.menu_tools.addAction(self.act_randomize_map)

        self.menu_tools.addSeparator()

        if hasattr(self, "act_waypoint_set_here"):
            self.menu_tools.addAction(self.act_waypoint_set_here)
        if hasattr(self, "act_waypoint_delete"):
            self.menu_tools.addAction(self.act_waypoint_delete)

        if hasattr(self, "act_switch_door_here"):
            self.menu_tools.addAction(self.act_switch_door_here)

        if hasattr(self, "act_town_add_edit"):
            self.menu_tools.addAction(self.act_town_add_edit)
        if hasattr(self, "act_town_set_temple_here"):
            self.menu_tools.addAction(self.act_town_set_temple_here)
        if hasattr(self, "act_town_delete"):
            self.menu_tools.addAction(self.act_town_delete)

        self.menu_tools.addSeparator()

        if hasattr(self, "act_monster_spawn_set_here"):
            self.menu_tools.addAction(self.act_monster_spawn_set_here)
        if hasattr(self, "act_monster_spawn_delete_here"):
            self.menu_tools.addAction(self.act_monster_spawn_delete_here)
        if hasattr(self, "act_monster_spawn_add_entry_here"):
            self.menu_tools.addAction(self.act_monster_spawn_add_entry_here)
        if hasattr(self, "act_monster_spawn_delete_entry_here"):
            self.menu_tools.addAction(self.act_monster_spawn_delete_entry_here)
        if hasattr(self, "act_npc_spawn_set_here"):
            self.menu_tools.addAction(self.act_npc_spawn_set_here)
        if hasattr(self, "act_npc_spawn_delete_here"):
            self.menu_tools.addAction(self.act_npc_spawn_delete_here)
        if hasattr(self, "act_npc_spawn_add_entry_here"):
            self.menu_tools.addAction(self.act_npc_spawn_add_entry_here)
        if hasattr(self, "act_npc_spawn_delete_entry_here"):
            self.menu_tools.addAction(self.act_npc_spawn_delete_entry_here)

        self.menu_tools.addSeparator()

        if hasattr(self, "act_house_set_id_on_selection"):
            self.menu_tools.addAction(self.act_house_set_id_on_selection)
        if hasattr(self, "act_house_clear_id_on_selection"):
            self.menu_tools.addAction(self.act_house_clear_id_on_selection)

        if hasattr(self, "act_house_add_edit"):
            self.menu_tools.addAction(self.act_house_add_edit)
        if hasattr(self, "act_house_set_entry_here"):
            self.menu_tools.addAction(self.act_house_set_entry_here)
        if hasattr(self, "act_house_delete_definition"):
            self.menu_tools.addAction(self.act_house_delete_definition)

        if hasattr(self, "act_zone_add_edit"):
            self.menu_tools.addAction(self.act_zone_add_edit)
        if hasattr(self, "act_zone_delete_definition"):
            self.menu_tools.addAction(self.act_zone_delete_definition)

        self._build_menus_and_toolbars()
        self._build_docks()

        self.session.set_live_chat_callback(self._handle_live_chat)
        self.session.set_live_client_list_callback(self._handle_live_client_list)
        self.session.set_live_cursor_callback(self._handle_live_cursor)

        self._live_timer = QTimer(self)
        self._live_timer.setInterval(50)
        self._live_timer.timeout.connect(self._poll_live_events)
        self._live_timer.start()

        self._update_brush_label()
        self.apply_ui_state_to_session()
        self.act_ghost_higher_floors.setChecked(bool(self.ghost_higher_floors))
        self.act_show_client_box.setChecked(bool(self.show_client_box))
        self.act_highlight_items.setChecked(bool(self.highlight_items))

        self.act_show_monsters.setChecked(bool(self.show_monsters))
        self.act_show_monsters_spawns.setChecked(bool(self.show_monsters_spawns))
        self.act_show_npcs.setChecked(bool(self.show_npcs))
        self.act_show_npcs_spawns.setChecked(bool(self.show_npcs_spawns))
        self.act_show_special.setChecked(bool(self.show_special))

        self.act_show_as_minimap.setChecked(bool(self.show_as_minimap))
        self.act_only_show_colors.setChecked(bool(self.only_show_colors))
        self.act_only_show_modified.setChecked(bool(self.only_show_modified))

        self.act_show_houses.setChecked(bool(self.show_houses_overlay))
        self.act_show_pathing.setChecked(bool(self.show_pathing))
        self.act_show_tooltips.setChecked(bool(self.show_tooltips))
        self.act_show_preview.setChecked(bool(self.show_preview))
        self.act_show_indicators_simple.setChecked(bool(self.show_indicators))
        self.act_palette_large_icons.setChecked(bool(self.palette_large_icons))

        self.act_palette_large_icons.setChecked(bool(self.palette_large_icons))

        # Initialize Modern UX features (theme, overlays, menus)
        self.init_modern_ux()

        self._enable_action_logging()

    def _enable_action_logging(self) -> None:
        """Attach logging to QAction triggers for session tracing."""
        action_logger = logging.getLogger("ui.actions")
        seen: set[int] = set()
        for action in self.findChildren(QAction):
            aid = id(action)
            if aid in seen:
                continue
            seen.add(aid)
            name = action.objectName() or action.text()

            def _handler(checked: bool = False, *, _name: str = name) -> None:
                action_logger.info("Action triggered: %s checked=%s", _name, checked)

            action.triggered.connect(_handler)

    def advance_animation_clock(self, delta_ms: int) -> None:
        if int(delta_ms) <= 0:
            return
        self._animation_clock_ms = (int(self._animation_clock_ms) + int(delta_ms)) % 1_000_000_000

    def animation_time_ms(self) -> int:
        return int(self._animation_clock_ms)

    def _sync_dock_action(self, action: QAction, visible: bool) -> None:
        action.setChecked(visible)
