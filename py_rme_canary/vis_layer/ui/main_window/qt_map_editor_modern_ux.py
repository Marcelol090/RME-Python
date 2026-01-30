"""Comprehensive Modern UI/UX Integration for QtMapEditor.

Integrates all modern UI components, dialogs, and features:
- Theme system
- Properties panel
- Overlays (brush cursor, paste preview, selection)
- Dialogs (welcome, settings, search, waypoints, houses, zones, spawns)
- Context menus
- Clipboard system
- Keyboard shortcuts
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor
    from py_rme_canary.vis_layer.ui.docks.modern_properties_panel import ModernPropertiesPanel
    from py_rme_canary.vis_layer.ui.overlays.brush_cursor import BrushCursorOverlay
    from py_rme_canary.vis_layer.ui.overlays.paste_preview import PastePreviewOverlay, SelectionOverlay
    from py_rme_canary.vis_layer.ui.menus.context_menus import TileContextMenu
    from py_rme_canary.logic_layer.clipboard import ClipboardManager

logger = logging.getLogger(__name__)


class QtMapEditorModernUXMixin:
    """Mixin that adds modern UI/UX features to QtMapEditor.

    Complete feature set:
    - Modern dark theme application
    - Modern properties panel with tabs
    - Brush cursor overlay
    - Paste preview overlay
    - Selection overlay with marching ants
    - Context menus for tiles/items
    - Clipboard with history and transforms
    - Recent files management
    - All modern dialogs
    """

    # Type hints for mixin attributes
    modern_properties_panel: "ModernPropertiesPanel | None"
    brush_cursor_overlay: "BrushCursorOverlay | None"
    paste_preview_overlay: "PastePreviewOverlay | None"
    selection_overlay: "SelectionOverlay | None"
    tile_context_menu: "TileContextMenu | None"
    clipboard: "ClipboardManager | None"
    _theme_applied: bool
    _modern_ux_initialized: bool

    def init_modern_ux(self: "QtMapEditor") -> None:
        """Initialize all modern UX features.

        Call this after __init__ setup is complete.
        """
        self._theme_applied = False
        self._modern_ux_initialized = False

        # Component references
        self.modern_properties_panel = None
        self.brush_cursor_overlay = None
        self.paste_preview_overlay = None
        self.selection_overlay = None
        self.tile_context_menu = None
        self.clipboard = None

        # Apply theme first
        self._apply_modern_theme()

        # Setup components
        self._setup_modern_properties_panel()
        self._setup_overlays()
        self._setup_context_menus()
        self._setup_clipboard()
        self._setup_recent_files()
        self._setup_modern_actions()

        self._modern_ux_initialized = True
        logger.info("Modern UX fully initialized")

    def _apply_modern_theme(self: "QtMapEditor") -> None:
        """Apply modern dark theme to the application."""
        try:
            from py_rme_canary.vis_layer.ui.theme.integration import apply_modern_theme
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if app:
                if apply_modern_theme(app):
                    self._theme_applied = True
                    logger.debug("Modern theme applied successfully")

        except ImportError as e:
            logger.warning(f"Modern theme not available: {e}")
        except Exception as e:
            logger.error(f"Error applying modern theme: {e}")

    def _setup_modern_properties_panel(self: "QtMapEditor") -> None:
        """Setup the modern properties panel dock."""
        try:
            from PyQt6.QtCore import Qt
            from py_rme_canary.vis_layer.ui.docks.modern_properties_panel import ModernPropertiesPanel

            self.modern_properties_panel = ModernPropertiesPanel(self)
            self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.modern_properties_panel)
            logger.debug("Modern properties panel created")

        except ImportError as e:
            logger.warning(f"Modern properties panel not available: {e}")

    def _setup_overlays(self: "QtMapEditor") -> None:
        """Setup all canvas overlays."""
        if not hasattr(self, 'canvas') or not self.canvas:
            return

        # Brush cursor overlay
        try:
            from py_rme_canary.vis_layer.ui.overlays.brush_cursor import BrushCursorOverlay
            self.brush_cursor_overlay = BrushCursorOverlay(self.canvas)
            tile_size = getattr(self.drawing_options, 'tile_size', 32) if hasattr(self, 'drawing_options') else 32
            self.brush_cursor_overlay.set_tile_size(tile_size)
            self.brush_cursor_overlay.set_visible(False)
        except ImportError:
            pass

        # Paste preview overlay
        try:
            from py_rme_canary.vis_layer.ui.overlays.paste_preview import PastePreviewOverlay, SelectionOverlay
            self.paste_preview_overlay = PastePreviewOverlay(self.canvas)
            self.selection_overlay = SelectionOverlay(self.canvas)
        except ImportError:
            pass

    def _setup_context_menus(self: "QtMapEditor") -> None:
        """Setup context menu handlers."""
        try:
            from py_rme_canary.vis_layer.ui.menus.context_menus import TileContextMenu

            self.tile_context_menu = TileContextMenu(self)
            self.tile_context_menu.set_callbacks({
                'copy': lambda: self._do_copy(),
                'cut': lambda: self._do_cut(),
                'paste': lambda: self._do_paste(),
                'delete': lambda: self._do_delete(),
                'can_paste': lambda: self.clipboard.can_paste() if self.clipboard else False,
                'select_all': lambda: self._do_select_all(),
                'deselect': lambda: self._do_deselect(),
                'properties': lambda: self._show_tile_properties(),
                'copy_position': lambda: self._copy_position_to_clipboard(),
                'goto': lambda: self.show_goto_position_dialog(),
                'set_waypoint': lambda: self.show_waypoint_quick_add(),
                'delete_waypoint': lambda: self._delete_waypoint_here(),
                'has_waypoint': lambda: self._has_waypoint_at_cursor(),
                'set_monster_spawn': lambda: self._place_monster_spawn(),
                'set_npc_spawn': lambda: self._place_npc_spawn(),
                'delete_spawn': lambda: self._delete_spawn_here(),
                'edit_house': lambda: self.show_house_manager(),
                'clear_house': lambda: self._clear_house_id(),
                'assign_house': lambda: self._assign_house_dialog(),
                'set_house_entry': lambda: self._set_house_entry_here(),
            })
            logger.debug("Context menus configured")

        except ImportError as e:
            logger.debug(f"Context menus not available: {e}")

    def _setup_clipboard(self: "QtMapEditor") -> None:
        """Setup clipboard system."""
        try:
            from py_rme_canary.logic_layer.clipboard import ClipboardManager
            self.clipboard = ClipboardManager.instance()
            logger.debug("Clipboard system initialized")
        except ImportError:
            pass

    def _setup_recent_files(self: "QtMapEditor") -> None:
        """Setup recent files menu integration."""
        try:
            from py_rme_canary.vis_layer.ui.utils.recent_files import build_recent_files_menu

            if hasattr(self, 'menu_file') and hasattr(self.menu_file, 'addMenu'):
                self.menu_recent_files = self.menu_file.addMenu("Recent Files")
                build_recent_files_menu(self.menu_recent_files, on_file_selected=self._open_recent_file)

        except ImportError:
            pass

    def _setup_modern_actions(self: "QtMapEditor") -> None:
        """Setup additional modern UI actions in menus."""
        try:
            from PyQt6.QtGui import QAction, QKeySequence

            # Add to Edit menu (if exists)
            if hasattr(self, 'menu_edit'):
                self.menu_edit.addSeparator()

                act_global_search = QAction("🔍 Global Search...", self)
                act_global_search.setShortcut(QKeySequence("Ctrl+Shift+F"))
                act_global_search.triggered.connect(self.show_global_search)
                self.menu_edit.addAction(act_global_search)

            # Add to Tools menu (if exists)
            if hasattr(self, 'menu_tools'):
                self.menu_tools.addSeparator()

                act_waypoints = QAction("📍 Waypoint Manager...", self)
                act_waypoints.triggered.connect(self.show_waypoint_manager)
                self.menu_tools.addAction(act_waypoints)

                act_houses = QAction("🏠 House Manager...", self)
                act_houses.triggered.connect(self.show_house_manager)
                self.menu_tools.addAction(act_houses)

                act_spawns = QAction("👹 Spawn Manager...", self)
                act_spawns.triggered.connect(self.show_spawn_manager)
                self.menu_tools.addAction(act_spawns)

                act_zones = QAction("🗺️ Zone Manager...", self)
                act_zones.triggered.connect(self.show_zone_manager)
                self.menu_tools.addAction(act_zones)

                act_towns = QAction("🏰 Town Manager...", self)
                act_towns.triggered.connect(self.show_town_manager)
                self.menu_tools.addAction(act_towns)

            # Settings in appropriate menu
            if hasattr(self, 'menu_file'):
                self.menu_file.addSeparator()
                act_settings = QAction("⚙️ Settings...", self)
                act_settings.triggered.connect(self.show_settings_dialog)
                self.menu_file.addAction(act_settings)

            logger.debug("Modern actions added to menus")

        except Exception as e:
            logger.warning(f"Error setting up modern actions: {e}")

    # ========== Dialog Methods ==========

    def show_global_search(self: "QtMapEditor") -> None:
        """Show global search dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.global_search import GlobalSearchDialog

            dialog = GlobalSearchDialog(game_map=self.map, parent=self)
            dialog.goto_position.connect(self.goto_position)
            dialog.show()  # Non-modal

        except ImportError:
            self._show_not_implemented("Global Search")

    def show_waypoint_manager(self: "QtMapEditor") -> None:
        """Show waypoint manager dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.waypoint_dialog import WaypointListDialog

            current_pos = self._get_cursor_position()
            dialog = WaypointListDialog(game_map=self.map, current_pos=current_pos, parent=self)
            dialog.waypoint_selected.connect(lambda n, x, y, z: self.goto_position(x, y, z))
            dialog.exec()

        except ImportError:
            self._show_not_implemented("Waypoint Manager")

    def show_waypoint_quick_add(self: "QtMapEditor") -> None:
        """Show quick waypoint add dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.waypoint_dialog import WaypointQuickAdd

            pos = self._get_cursor_position()
            dialog = WaypointQuickAdd(position=pos, parent=self)
            if dialog.exec():
                name = dialog.get_name()
                if name and self.map:
                    from py_rme_canary.core.data.position import Position
                    if not hasattr(self.map, 'waypoints') or self.map.waypoints is None:
                        self.map.waypoints = {}
                    self.map.waypoints[name] = Position(x=pos[0], y=pos[1], z=pos[2])

        except ImportError:
            pass

    def show_house_manager(self: "QtMapEditor") -> None:
        """Show house manager dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.house_dialog import HouseListDialog

            dialog = HouseListDialog(game_map=self.map, parent=self)
            dialog.goto_position.connect(self.goto_position)
            dialog.exec()

        except ImportError:
            self._show_not_implemented("House Manager")

    def show_spawn_manager(self: "QtMapEditor") -> None:
        """Show spawn manager dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.spawn_manager import SpawnManagerDialog

            dialog = SpawnManagerDialog(game_map=self.map, parent=self)
            dialog.goto_position.connect(self.goto_position)
            dialog.exec()

        except ImportError:
            self._show_not_implemented("Spawn Manager")

    def show_zone_manager(self: "QtMapEditor") -> None:
        """Show zone manager dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.zone_town_dialogs import ZoneListDialog

            dialog = ZoneListDialog(game_map=self.map, parent=self)
            dialog.exec()

        except ImportError:
            self._show_not_implemented("Zone Manager")

    def show_town_manager(self: "QtMapEditor") -> None:
        """Show town manager dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.zone_town_dialogs import TownListDialog

            current_pos = self._get_cursor_position()
            dialog = TownListDialog(game_map=self.map, current_pos=current_pos, parent=self)
            dialog.goto_position.connect(self.goto_position)
            dialog.exec()

        except ImportError:
            self._show_not_implemented("Town Manager")

    def show_settings_dialog(self: "QtMapEditor") -> None:
        """Show settings dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.settings_dialog import SettingsDialog

            dialog = SettingsDialog(parent=self)
            dialog.settings_applied.connect(self._apply_settings)
            dialog.exec()

        except ImportError:
            self._show_not_implemented("Settings")

    def show_goto_position_dialog(self: "QtMapEditor") -> None:
        """Show go to position dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.navigation_dialogs import GoToPositionDialog

            pos = self._get_cursor_position()
            map_width = self.map.header.width if self.map else 65535
            map_height = self.map.header.height if self.map else 65535

            dialog = GoToPositionDialog(
                current_x=pos[0], current_y=pos[1], current_z=pos[2],
                map_width=map_width, map_height=map_height,
                parent=self
            )
            dialog.position_selected.connect(self.goto_position)
            dialog.exec()

        except ImportError:
            self._show_not_implemented("Go To Position")

    def show_welcome_dialog(self: "QtMapEditor") -> None:
        """Show the welcome dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.welcome_dialog import WelcomeDialog
            from py_rme_canary.vis_layer.ui.utils.recent_files import RecentFilesManager

            recent = RecentFilesManager.instance().get_recent_files()
            dialog = WelcomeDialog(recent_files=recent, parent=self)
            dialog.new_map_requested.connect(lambda: self.act_new.trigger() if hasattr(self, 'act_new') else None)
            dialog.open_map_requested.connect(lambda: self.act_open.trigger() if hasattr(self, 'act_open') else None)
            dialog.recent_file_selected.connect(self._open_recent_file)
            dialog.exec()

        except ImportError:
            pass

    def show_map_properties_dialog(self: "QtMapEditor") -> None:
        """Show map properties dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.map_dialogs import MapPropertiesDialog

            dialog = MapPropertiesDialog(game_map=self.map, parent=self)
            if dialog.exec():
                values = dialog.get_values()
                if self.map:
                    if hasattr(self.map, 'name'):
                        self.map.name = values.get('name', '')
                    if hasattr(self.map, 'description'):
                        self.map.description = values.get('description', '')

        except ImportError:
            pass

    def show_about_dialog(self: "QtMapEditor") -> None:
        """Show about dialog."""
        try:
            from py_rme_canary.vis_layer.ui.dialogs.map_dialogs import AboutDialog
            dialog = AboutDialog(parent=self)
            dialog.exec()
        except ImportError:
            pass

    # ========== Overlay Methods ==========

    def update_brush_cursor(self: "QtMapEditor", x: int, y: int, visible: bool = True) -> None:
        """Update brush cursor position and visibility."""
        if self.brush_cursor_overlay:
            from PyQt6.QtCore import QPoint
            self.brush_cursor_overlay.set_position(QPoint(x, y))
            self.brush_cursor_overlay.set_visible(visible)
            brush_size = getattr(self, 'brush_size', 1) or 1
            self.brush_cursor_overlay.set_brush_size(brush_size)
            is_circle = getattr(self, 'brush_shape', 'square') == 'circle'
            self.brush_cursor_overlay.set_circle_shape(is_circle)

    def update_paste_preview(self: "QtMapEditor", positions: list, is_cut: bool = False) -> None:
        """Update paste preview overlay."""
        if self.paste_preview_overlay:
            self.paste_preview_overlay.set_preview_positions(positions, is_cut)
            self.paste_preview_overlay.set_visible(bool(positions))

    def clear_paste_preview(self: "QtMapEditor") -> None:
        """Clear paste preview overlay."""
        if self.paste_preview_overlay:
            self.paste_preview_overlay.clear_preview()
            self.paste_preview_overlay.set_visible(False)

    # ========== Properties Panel Methods ==========

    def show_properties_for_tile(self: "QtMapEditor", tile: object) -> None:
        """Show tile properties in the modern properties panel."""
        if self.modern_properties_panel and tile:
            self.modern_properties_panel.show_tile(tile)

    def show_properties_for_item(self: "QtMapEditor", item: object) -> None:
        """Show item properties in the modern properties panel."""
        if self.modern_properties_panel and item:
            self.modern_properties_panel.show_item(item)

    def show_properties_for_house(self: "QtMapEditor", house: object) -> None:
        """Show house properties in the modern properties panel."""
        if self.modern_properties_panel and house:
            self.modern_properties_panel.show_house(house)

    # ========== Context Menu Methods ==========

    def show_tile_context_menu(self: "QtMapEditor", tile: object, has_selection: bool = False) -> None:
        """Show context menu for a tile."""
        if self.tile_context_menu:
            self.tile_context_menu.show_for_tile(tile, has_selection)

    # ========== Helper Methods ==========

    def goto_position(self: "QtMapEditor", x: int, y: int, z: int) -> None:
        """Navigate to a position on the map."""
        if hasattr(self, 'viewport'):
            self.viewport.center_x = x
            self.viewport.center_y = y
        if hasattr(self, 'z_spin'):
            self.z_spin.setValue(z)
        if hasattr(self, 'canvas'):
            self.canvas.update()

    def _get_cursor_position(self: "QtMapEditor") -> tuple[int, int, int]:
        """Get current cursor position."""
        x = getattr(self, '_last_hover_tile', (0, 0))[0]
        y = getattr(self, '_last_hover_tile', (0, 0))[1]
        z = self.z_spin.value() if hasattr(self, 'z_spin') else 7
        return (x, y, z)

    def _open_recent_file(self: "QtMapEditor", path: str) -> None:
        """Open a file from the recent files list."""
        if hasattr(self, 'do_open_file'):
            self.do_open_file(path)

    def _apply_settings(self: "QtMapEditor", settings: dict) -> None:
        """Apply settings from settings dialog."""
        logger.info(f"Applying settings: {list(settings.keys())}")

    def _show_not_implemented(self: "QtMapEditor", feature: str) -> None:
        """Show not implemented message."""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Not Available", f"{feature} is not available yet.")

    # Stub methods for context menu callbacks
    def _do_copy(self: "QtMapEditor") -> None:
        if hasattr(self, 'act_copy'):
            self.act_copy.trigger()

    def _do_cut(self: "QtMapEditor") -> None:
        if hasattr(self, 'act_cut'):
            self.act_cut.trigger()

    def _do_paste(self: "QtMapEditor") -> None:
        if hasattr(self, 'act_paste'):
            self.act_paste.trigger()

    def _do_delete(self: "QtMapEditor") -> None:
        if hasattr(self, 'act_delete_selection'):
            self.act_delete_selection.trigger()

    def _do_select_all(self: "QtMapEditor") -> None:
        pass  # Would select all visible tiles

    def _do_deselect(self: "QtMapEditor") -> None:
        if hasattr(self, 'act_clear_selection'):
            self.act_clear_selection.trigger()

    def _show_tile_properties(self: "QtMapEditor") -> None:
        pass  # Would show tile dialog

    def _copy_position_to_clipboard(self: "QtMapEditor") -> None:
        if hasattr(self, 'act_copy_position'):
            self.act_copy_position.trigger()

    def _delete_waypoint_here(self: "QtMapEditor") -> None:
        pass

    def _has_waypoint_at_cursor(self: "QtMapEditor") -> bool:
        return False

    def _place_monster_spawn(self: "QtMapEditor") -> None:
        pass

    def _place_npc_spawn(self: "QtMapEditor") -> None:
        pass

    def _delete_spawn_here(self: "QtMapEditor") -> None:
        pass

    def _clear_house_id(self: "QtMapEditor") -> None:
        pass

    def _assign_house_dialog(self: "QtMapEditor") -> None:
        self.show_house_manager()

    def _set_house_entry_here(self: "QtMapEditor") -> None:
        pass


def integrate_modern_ux(editor: "QtMapEditor") -> None:
    """Integrate modern UX features into an existing editor instance.

    Call this after the editor is fully initialized.

    Args:
        editor: QtMapEditor instance to enhance
    """
    # Add mixin methods dynamically
    mixin = QtMapEditorModernUXMixin()

    # Copy methods to editor
    for name in dir(mixin):
        if not name.startswith('_') or name.startswith('_apply') or name.startswith('_setup'):
            method = getattr(mixin, name)
            if callable(method):
                setattr(editor, name, method.__get__(editor, type(editor)))

    # Initialize
    editor.init_modern_ux()
