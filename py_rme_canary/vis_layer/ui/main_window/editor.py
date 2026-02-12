from __future__ import annotations

import logging
import os
from collections import OrderedDict

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
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
from py_rme_canary.vis_layer.ui.docks.modern_palette_dock import ModernPaletteDock
from py_rme_canary.vis_layer.ui.drawing_options_coordinator import (
    DrawingOptionsCoordinator,
    create_coordinator,
)
from py_rme_canary.vis_layer.ui.helpers import Viewport
from py_rme_canary.vis_layer.ui.indicators import IndicatorService
from py_rme_canary.vis_layer.ui.main_window.find_item import open_find_item
from py_rme_canary.vis_layer.ui.main_window.find_on_map import open_find_waypoint
from py_rme_canary.vis_layer.ui.resources.icon_pack import load_icon

logger = logging.getLogger(__name__)
from py_rme_canary.vis_layer.ui.main_window.build_actions import build_actions
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_assets import QtMapEditorAssetsMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_brushes import QtMapEditorBrushesMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_dialogs import QtMapEditorDialogsMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_docks import QtMapEditorDocksMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_edit import QtMapEditorEditMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file import QtMapEditorFileMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_friends import QtMapEditorFriendsMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_mirror import QtMapEditorMirrorMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_modern_ux import QtMapEditorModernUXMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_navigation import QtMapEditorNavigationMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_palettes import QtMapEditorPalettesMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_session import QtMapEditorSessionMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_toolbars import QtMapEditorToolbarsMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_view import QtMapEditorViewMixin


class QtMapEditor(
    QMainWindow,
    QtMapEditorModernUXMixin,
    QtMapEditorToolbarsMixin,
    QtMapEditorViewMixin,
    QtMapEditorPalettesMixin,
    QtMapEditorDocksMixin,
    QtMapEditorDialogsMixin,
    QtMapEditorAssetsMixin,
    QtMapEditorMirrorMixin,
    QtMapEditorFileMixin,
    QtMapEditorEditMixin,
    QtMapEditorFriendsMixin,
    QtMapEditorBrushesMixin,
    QtMapEditorNavigationMixin,
    QtMapEditorSessionMixin,
):
    # NOTE: A lot of UI construction happens in builder/mixin modules that
    # dynamically attach actions, docks, toolbars, and widgets onto the editor.
    # Declare those attributes here so mypy can type-check the whole vis_layer
    # without relying on file-level `# type: ignore`.

    # Menus created by builders
    _menu_toolbars: QMenu
    menu_file: QMenu
    menu_recent_files: QMenu
    menu_edit: QMenu
    menu_search: QMenu
    menu_selection: QMenu
    menu_help: QMenu
    menu_find_on_map: QMenu
    menu_tools: QMenu

    # Actions injected by builders
    act_new: QAction
    act_open: QAction
    act_save: QAction
    act_save_as: QAction
    act_exit: QAction
    act_import_monsters_npcs: QAction
    act_import_monster_folder: QAction
    act_import_map: QAction
    act_export_png: QAction
    act_export_otmm: QAction
    act_export_tilesets: QAction
    act_reload_data: QAction
    act_preferences: QAction
    act_extensions: QAction
    act_goto_website: QAction
    act_undo: QAction
    act_redo: QAction
    act_cancel: QAction
    act_command_palette: QAction
    act_copy: QAction
    act_cut: QAction
    act_paste: QAction
    act_delete_selection: QAction
    act_copy_position: QAction
    act_jump_to_brush: QAction
    act_jump_to_item: QAction
    act_duplicate_selection: QAction
    act_clear_selection: QAction
    act_move_selection_up: QAction
    act_move_selection_down: QAction
    act_automagic: QAction
    act_borderize_selection: QAction
    act_fill: QAction
    act_merge_move: QAction
    act_borderize_drag: QAction
    act_merge_paste: QAction
    act_borderize_paste: QAction
    act_selection_mode: QAction
    act_lasso_select: QAction
    act_selection_depth_compensate: QAction
    act_selection_depth_current: QAction
    act_selection_depth_lower: QAction
    act_selection_depth_visible: QAction
    act_selection_depth_group: QAction
    act_toggle_mirror: QAction
    act_mirror_axis_x: QAction
    act_mirror_axis_y: QAction
    act_mirror_axis_set_from_cursor: QAction
    mirror_axis_action_group: QActionGroup
    act_zoom_in: QAction
    act_zoom_out: QAction
    act_zoom_normal: QAction
    act_new_view: QAction
    act_new_instance: QAction
    act_fullscreen: QAction
    act_take_screenshot: QAction
    act_show_shade: QAction
    act_show_all_floors: QAction
    act_show_loose_items: QAction
    act_ghost_higher_floors: QAction
    act_show_client_box: QAction
    act_show_client_ids: QAction
    act_show_grid: QAction
    act_highlight_items: QAction
    act_show_monsters: QAction
    act_show_monsters_spawns: QAction
    act_show_npcs: QAction
    act_show_npcs_spawns: QAction
    act_show_special: QAction
    act_show_as_minimap: QAction
    act_only_show_colors: QAction
    act_only_show_modified: QAction
    act_clear_modified_state: QAction
    act_show_houses: QAction
    act_show_pathing: QAction
    act_show_tooltips: QAction
    act_show_preview: QAction
    act_ingame_preview: QAction
    act_show_wall_hooks: QAction
    act_show_pickupables: QAction
    act_show_moveables: QAction
    act_show_avoidables: QAction
    act_show_lights: QAction
    act_show_indicators_simple: QAction
    act_manage_client_profiles: QAction
    act_load_client_data_stack: QAction
    act_set_assets_dir: QAction
    act_goto_position: QAction
    act_goto_previous_position: QAction
    act_new_palette: QAction
    act_palette_terrain: QAction
    act_palette_doodad: QAction
    act_palette_item: QAction
    act_palette_collection: QAction
    act_palette_house: QAction
    act_palette_creature: QAction
    act_palette_npc: QAction
    act_palette_waypoint: QAction
    act_palette_zones: QAction
    act_palette_raw: QAction
    act_palette_large_icons: QAction
    act_window_minimap: QAction
    act_window_tool_options: QAction
    act_window_actions_history: QAction
    act_window_friends: QAction
    act_clear_invalid_tiles_selection: QAction
    act_clear_invalid_tiles_map: QAction
    act_randomize_selection: QAction
    act_randomize_map: QAction
    act_waypoint_set_here: QAction
    act_waypoint_delete: QAction
    act_switch_door_here: QAction
    act_convert_map_format: QAction
    act_remove_item_map: QAction
    act_remove_corpses_map: QAction
    act_remove_unreachable_map: QAction
    act_clear_invalid_house_tiles_map: QAction
    act_town_add_edit: QAction
    act_town_set_temple_here: QAction
    act_town_delete: QAction
    act_house_add_edit: QAction
    act_house_set_entry_here: QAction
    act_house_delete_definition: QAction
    act_house_set_id_on_selection: QAction
    act_house_clear_id_on_selection: QAction
    act_monster_spawn_set_here: QAction
    act_monster_spawn_delete_here: QAction
    act_monster_spawn_add_entry_here: QAction
    act_monster_spawn_delete_entry_here: QAction
    act_npc_spawn_set_here: QAction
    act_npc_spawn_delete_here: QAction
    act_npc_spawn_add_entry_here: QAction
    act_npc_spawn_delete_entry_here: QAction
    act_zone_add_edit: QAction
    act_zone_delete_definition: QAction
    act_src_connect: QAction
    act_src_disconnect: QAction
    act_live_host: QAction
    act_live_stop: QAction
    act_live_kick: QAction
    act_live_ban: QAction

    # Editor-owned actions (created in editor.py)
    act_find_item: QAction
    act_find_creature: QAction
    act_find_monster: QAction
    act_find_npc: QAction
    act_find_house: QAction
    act_find_unique_map: QAction
    act_find_action_map: QAction
    act_find_container_map: QAction
    act_find_writeable_map: QAction
    act_find_unique_selection: QAction
    act_find_action_selection: QAction
    act_find_container_selection: QAction
    act_find_writeable_selection: QAction
    act_map_statistics: QAction
    act_map_statistics_graphs: QAction
    act_replace_items: QAction
    act_replace_items_on_selection: QAction
    act_remove_item_on_selection: QAction
    act_find_waypoint: QAction
    act_find_on_map_item: QAction

    quick_replace_source_id: int | None
    quick_replace_target_id: int | None

    # Docks/widgets built by builders
    dock_minimap: QDockWidget | None
    dock_actions_history: QDockWidget | None
    dock_friends: QDockWidget | None
    dock_sprite_preview: QDockWidget
    minimap_widget: MinimapWidget | None
    friends_sidebar: object | None
    sprite_id_spin: QSpinBox
    sprite_preview: QLabel

    # Toolbars and their widgets
    tb_standard: QToolBar
    tb_brushes: QToolBar
    tb_sizes: QToolBar
    tb_position: QToolBar
    tb_indicators: QToolBar
    brush_id_entry: QSpinBox
    brush_label: QLabel
    size_spin: QSpinBox
    variation_spin: QSpinBox
    thickness_spin: QSpinBox
    thickness_cb: QCheckBox
    automagic_cb: QCheckBox
    shape_square: QPushButton
    shape_circle: QPushButton
    brush_shape_group: QButtonGroup
    cursor_pos_label: QLabel
    goto_x_spin: QSpinBox
    goto_y_spin: QSpinBox
    z_spin: QSpinBox

    # Toolbar actions (indicators + toolbar visibility)
    act_tb_hooks: QAction
    act_tb_pickupables: QAction
    act_tb_moveables: QAction
    act_tb_avoidables: QAction
    act_view_toolbar_brushes: QAction
    act_view_toolbar_position: QAction
    act_view_toolbar_sizes: QAction
    act_view_toolbar_standard: QAction
    act_view_toolbar_indicators: QAction

    status: QStatusBar
    canvas: OpenGLCanvasWidget
    drawing_options: DrawingOptions
    drawing_options_coordinator: DrawingOptionsCoordinator
    map_drawer: MapDrawer
    asset_profile: object | None
    friends_service: object | None
    friends_local_user_id: int | None
    friends_privacy_mode: str
    _friends_timer: QTimer | None

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("Noct Map Editor")
        self.setWindowIcon(load_icon("logo_axolotl"))
        self.resize(1280, 860)

        self.brush_mgr = BrushManager.from_json_file(os.path.join("data", "brushes.json"))
        extra_brushes = os.path.join("data", "brushes_extra.json")
        if os.path.exists(extra_brushes):
            self.brush_mgr.load_from_file(extra_brushes)
        materials_brushs = os.path.join("data", "materials", "brushs.xml")
        if os.path.exists(materials_brushs):
            try:
                self.brush_mgr.load_table_brushes_from_materials(materials_brushs)
                self.brush_mgr.load_carpet_brushes_from_materials(materials_brushs)
                self.brush_mgr.load_door_brushes_from_materials(materials_brushs)
            except Exception as exc:
                logger.warning("Failed to load table/carpet/door brushes from %s: %s", materials_brushs, exc)
        try:
            changed = int(self.brush_mgr.load_border_overrides_file())
            if changed > 0:
                logger.info("Loaded %d border override(s) for brushes", changed)
        except Exception as exc:
            logger.warning("Failed to load brush border overrides: %s", exc)

        self.map: GameMap = GameMap(header=MapHeader(otbm_version=2, width=256, height=256))
        self.session = EditorSession(self.map, self.brush_mgr, on_tiles_changed=self._on_tiles_changed)
        self.session.on_brush_size_changed = self._on_session_brush_size_changed

        self.viewport = Viewport()
        self.current_path: str | None = None

        # Detection context (drives safe, engine-aware flows)
        self.engine: str = "unknown"
        self.client_version: int = 0

        self.brush_size = 0
        self.brush_shape = "square"

        self.fill_armed = False
        self.paste_armed = False

        # Client sprite assets (legacy sprite sheets via catalog-content.json)
        self.assets_dir: str | None = None
        self.assets_selection_path: str | None = None
        self.sprite_assets = None
        self.appearance_assets = None
        self.asset_profile = None
        self.id_mapper = None
        # LRU cache to avoid unbounded growth
        self._sprite_cache: OrderedDict[tuple[int, int], QPixmap] = OrderedDict()
        self._memory_guard = default_memory_guard()
        self._sprite_render_temporarily_disabled: bool = False
        self._sprite_render_emergency_warned: bool = False
        self._sprite_render_disabled_reason: str | None = None
        self._animation_clock_ms: int = 0

        # Cross-version clipboard sprite matcher
        self.sprite_matcher = None

        # Selection mode (legacy-like box selection)
        self.selection_mode: bool = False
        self.lasso_enabled: bool = False

        # Mirror drawing (legacy-like: toggle, pick axis, set axis from cursor)
        self.mirror_enabled: bool = False
        self.mirror_axis: str = "x"  # "x" or "y"
        self.mirror_axis_value: int | None = None
        self._last_hover_tile: tuple[int, int] = (0, 0)
        self._position_history: list[tuple[int, int, int]] = []

        # View toggles (legacy-inspired)
        self.show_grid: bool = True
        self.show_wall_hooks: bool = False
        self.show_pickupables: bool = False
        self.show_moveables: bool = False
        self.show_avoidables: bool = False

        # View toggles (legacy menu parity)
        self.show_shade: bool = False
        self.show_all_floors: bool = True
        self.show_loose_items: bool = False
        self.ghost_higher_floors: bool = False
        self.show_client_box: bool = False
        self.show_client_ids: bool = False
        self.show_lights: bool = False
        self.highlight_items: bool = False

        self.show_monsters: bool = True
        self.show_monsters_spawns: bool = True
        self.show_npcs: bool = True
        self.show_npcs_spawns: bool = False
        self.show_special: bool = False

        self.show_as_minimap: bool = False
        self.only_show_colors: bool = False
        self.only_show_modified: bool = False

        self.show_houses_overlay: bool = True
        self.show_pathing: bool = False
        self.show_tooltips: bool = True
        self.show_preview: bool = True
        self.show_indicators: bool = True
        self.ingame_preview_enabled: bool = False
        self.ingame_preview_controller = None

        self._extra_views: list[QtMapEditor] = []
        self.quick_replace_source_id = None
        self.quick_replace_target_id = None
        self.palette_large_icons: bool = False

        # UI services
        self.indicators = IndicatorService()
        # Modern Palette Dock replacing PaletteManager
        self.palettes = ModernPaletteDock(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.palettes)

        self.actions_history = ActionsHistoryDock(self)

        # Optional docks (Window menu)
        self.dock_minimap: QDockWidget | None = None
        self.minimap_widget: MinimapWidget | None = None
        self.dock_actions_history: QDockWidget | None = None
        self.dock_friends: QDockWidget | None = None
        self.friends_sidebar = None
        self.friends_service = None
        self.friends_local_user_id = None
        self.friends_privacy_mode = "friends_only"
        self._friends_timer = None

        self.canvas = OpenGLCanvasWidget(self, editor=self)
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
        self.act_find_item = QAction(load_icon("action_find"), "Find Item...", self)
        self.act_find_item.setShortcut(QKeySequence("Ctrl+F"))
        self.act_find_item.triggered.connect(self._open_find_item_dialog)

        self.act_map_statistics = QAction(load_icon("action_statistics"), "Map Statistics...", self)
        self.act_map_statistics.triggered.connect(self._show_map_statistics)

        self.act_map_statistics_graphs = QAction(load_icon("action_statistics"), "Map Statistics (Graphs)...", self)
        self.act_map_statistics_graphs.setShortcut(QKeySequence("Ctrl+Shift+G"))
        self.act_map_statistics_graphs.triggered.connect(self._show_map_statistics_graphs)

        self.act_replace_items = QAction(load_icon("action_replace"), "Replace Items...", self)
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
        self._init_friends()

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
        self.act_show_client_ids.setChecked(bool(self.show_client_ids))
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
        if hasattr(self, "act_toggle_dark_mode"):
            self.act_toggle_dark_mode.blockSignals(True)
            self.act_toggle_dark_mode.setChecked(True)
            self.act_toggle_dark_mode.blockSignals(False)

        try:
            warnings = self._reload_item_definitions_for_current_context(source="startup")
            if warnings:
                logger.warning(" | ".join(warnings))
        except Exception:
            logger.exception("Failed to initialize item definitions at startup")

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

        # Small UX polish
        self.act_copy_position.setStatusTip("Copy current cursor position to clipboard")
        self.act_jump_to_brush.setStatusTip("Focus the brush list filter")
        self.act_jump_to_item.setStatusTip("Focus the brush id field")
        self.act_duplicate_selection.setStatusTip("Copy selection and arm paste")
        self.act_clear_selection.setStatusTip("Clear current selection")
        self.act_automagic.setStatusTip("Toggle automatic border functions (legacy: A)")
        self.act_borderize_selection.setStatusTip("Recreate automatic borders in the selected area")

        # Fallback icons for common actions (native style)
        if self.act_new.icon().isNull():
            self.act_new.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon))
        if self.act_open.icon().isNull():
            self.act_open.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton))
        if self.act_save.icon().isNull():
            self.act_save.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        if self.act_save_as.icon().isNull():
            self.act_save_as.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        if self.act_undo.icon().isNull():
            self.act_undo.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        if self.act_redo.icon().isNull():
            self.act_redo.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
