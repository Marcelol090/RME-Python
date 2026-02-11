from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtGui import QAction, QActionGroup, QKeySequence

from py_rme_canary.logic_layer.session.selection_modes import SelectionDepthMode
from py_rme_canary.vis_layer.ui.main_window import find_item, live_connect
from py_rme_canary.vis_layer.ui.main_window.menubar.assets import tools as assets_tools
from py_rme_canary.vis_layer.ui.main_window.menubar.edit import tools as edit_tools
from py_rme_canary.vis_layer.ui.main_window.menubar.file import tools as file_tools
from py_rme_canary.vis_layer.ui.main_window.menubar.map import tools as map_tools
from py_rme_canary.vis_layer.ui.main_window.menubar.mirror import tools as mirror_tools
from py_rme_canary.vis_layer.ui.main_window.menubar.mode import tools as mode_tools
from py_rme_canary.vis_layer.ui.main_window.menubar.view import tools as view_tools
from py_rme_canary.vis_layer.ui.main_window.menubar.window import tools as window_tools
from py_rme_canary.vis_layer.ui.resources.icon_pack import load_icon

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


def build_actions(editor: QtMapEditor) -> None:
    """Create QActions and connect signals.

    This mutates `editor` by setting attributes like `act_open`, etc.
    """

    # File
    editor.act_new = QAction(load_icon("action_new"), "New", editor)
    editor.act_open = QAction(load_icon("action_open"), "Open…", editor)
    editor.act_save = QAction(load_icon("action_save"), "Save", editor)
    editor.act_save_as = QAction(load_icon("action_save_as"), "Save As…", editor)
    editor.act_exit = QAction(load_icon("action_exit"), "Exit", editor)
    editor.act_import_monsters_npcs = QAction("Import Monsters/NPC...", editor)
    editor.act_import_monster_folder = QAction("Import Monster Folder...", editor)
    editor.act_import_map = QAction("Import Map...", editor)

    # Generate Map / Close Map (C++ parity)
    editor.act_generate_map = QAction(load_icon("action_generate"), "Generate Map...", editor)
    editor.act_generate_map.triggered.connect(lambda _c=False: file_tools.generate_map(editor))

    editor.act_close_map = QAction(load_icon("action_close"), "Close", editor)
    editor.act_close_map.setShortcut(QKeySequence("Ctrl+Q"))
    editor.act_close_map.triggered.connect(lambda _c=False: file_tools.close_map(editor))

    editor.act_new.setShortcut(QKeySequence.StandardKey.New)
    editor.act_open.setShortcut(QKeySequence.StandardKey.Open)
    editor.act_save.setShortcut(QKeySequence.StandardKey.Save)
    editor.act_save_as.setShortcut(QKeySequence("Ctrl+Alt+S"))

    editor.act_new.triggered.connect(lambda _c=False: file_tools.new_map(editor))
    editor.act_open.triggered.connect(lambda _c=False: file_tools.open_map(editor))
    editor.act_save.triggered.connect(lambda _c=False: file_tools.save(editor))
    editor.act_save_as.triggered.connect(lambda _c=False: file_tools.save_as(editor))
    editor.act_exit.triggered.connect(lambda _c=False: file_tools.exit_app(editor))
    editor.act_import_monsters_npcs.triggered.connect(lambda _c=False: file_tools.import_monsters_npcs(editor))
    editor.act_import_monster_folder.triggered.connect(lambda _c=False: file_tools.import_monster_folder(editor))
    editor.act_import_map.triggered.connect(lambda _c=False: file_tools.import_map(editor))

    # Export
    editor.act_export_png = QAction("Export as PNG...", editor)
    editor.act_export_png.triggered.connect(lambda _c=False: file_tools.export_png(editor))

    editor.act_export_otmm = QAction("Export OTMM...", editor)
    editor.act_export_otmm.triggered.connect(lambda _c=False: file_tools.export_otmm(editor))
    editor.act_export_tilesets = QAction("Export Tilesets...", editor)
    editor.act_export_tilesets.triggered.connect(lambda _c=False: file_tools.export_tilesets(editor))

    editor.act_export_minimap = QAction("Export Minimap...", editor)
    editor.act_export_minimap.triggered.connect(lambda _c=False: file_tools.export_minimap(editor))

    editor.act_reload_data = QAction(load_icon("action_reload"), "Reload Data Files", editor)
    editor.act_reload_data.setShortcut(QKeySequence("F5"))
    editor.act_reload_data.triggered.connect(lambda _c=False: file_tools.reload_data(editor))

    editor.act_preferences = QAction(load_icon("action_preferences"), "Preferences...", editor)
    editor.act_preferences.triggered.connect(lambda _c=False: file_tools.open_preferences(editor))

    editor.act_extensions = QAction(load_icon("action_extensions"), "Extensions...", editor)
    editor.act_extensions.setShortcut(QKeySequence("F2"))
    editor.act_extensions.triggered.connect(lambda _c=False: file_tools.open_extensions(editor))

    editor.act_goto_website = QAction(load_icon("action_website"), "Goto Website", editor)
    editor.act_goto_website.setShortcut(QKeySequence("F3"))
    editor.act_goto_website.triggered.connect(lambda _c=False: file_tools.goto_website(editor))

    editor.act_about = QAction(load_icon("action_about"), "About...", editor)
    editor.act_about.setShortcut(QKeySequence("F1"))
    editor.act_about.triggered.connect(lambda _c=False: editor._show_about())

    # Replace Items
    editor.act_replace_items = QAction(load_icon("action_replace"), "Replace Items...", editor)
    editor.act_replace_items.setShortcut(QKeySequence("Ctrl+Shift+F"))
    editor.act_replace_items.triggered.connect(lambda _c=False: edit_tools.replace_items(editor))

    # Check Duplicate UIDs
    editor.act_check_uid = QAction("Check Duplicate UIDs...", editor)
    editor.act_check_uid.setShortcut(QKeySequence("Ctrl+U"))
    editor.act_check_uid.triggered.connect(lambda _c=False: edit_tools.check_uid(editor))

    # Edit
    editor.act_undo = QAction(load_icon("action_undo"), "Undo", editor)
    editor.act_redo = QAction(load_icon("action_redo"), "Redo", editor)
    editor.act_undo.setShortcut(QKeySequence.StandardKey.Undo)
    editor.act_redo.setShortcut(QKeySequence.StandardKey.Redo)
    editor.act_undo.triggered.connect(lambda _c=False: edit_tools.undo(editor))
    editor.act_redo.triggered.connect(lambda _c=False: edit_tools.redo(editor))

    editor.act_cancel = QAction("Cancel", editor)
    editor.act_cancel.setShortcut(QKeySequence("Esc"))
    editor.act_cancel.triggered.connect(lambda _c=False: edit_tools.cancel(editor))

    editor.act_command_palette = QAction(load_icon("action_find"), "Command Palette...", editor)
    editor.act_command_palette.setShortcut(QKeySequence("Ctrl+K"))
    editor.act_command_palette.triggered.connect(lambda _c=False: editor._show_command_palette())

    editor.act_copy = QAction(load_icon("action_copy"), "Copy", editor)
    editor.act_cut = QAction(load_icon("action_cut"), "Cut", editor)
    editor.act_paste = QAction(load_icon("action_paste"), "Paste", editor)
    editor.act_delete_selection = QAction(load_icon("action_delete"), "Delete Selection", editor)

    editor.act_copy.setShortcut(QKeySequence.StandardKey.Copy)
    editor.act_cut.setShortcut(QKeySequence.StandardKey.Cut)
    editor.act_paste.setShortcut(QKeySequence.StandardKey.Paste)
    editor.act_delete_selection.setShortcut(QKeySequence.StandardKey.Delete)

    editor.act_copy.triggered.connect(lambda _c=False: edit_tools.copy(editor))
    editor.act_cut.triggered.connect(lambda _c=False: edit_tools.cut(editor))
    editor.act_paste.triggered.connect(lambda _c=False: edit_tools.arm_paste(editor))
    editor.act_delete_selection.triggered.connect(lambda _c=False: edit_tools.delete_selection(editor))

    # Lasso Selection
    editor.act_lasso_select = QAction("Lasso Select", editor)
    editor.act_lasso_select.setCheckable(True)
    # NOTE: C++ reserves L for Show Animation. Lasso has no hotkey in legacy.
    editor.act_lasso_select.toggled.connect(lambda v: edit_tools.toggle_lasso(editor, v))

    # Legacy edit helpers (menubar.xml)
    editor.act_copy_position = QAction("Copy Position", editor)
    editor.act_copy_position.setShortcut(QKeySequence("Ctrl+Shift+P"))
    editor.act_copy_position.triggered.connect(lambda _c=False: edit_tools.copy_position(editor))

    editor.act_jump_to_brush = QAction("Jump to Brush...", editor)
    editor.act_jump_to_brush.setShortcut(QKeySequence("J"))
    editor.act_jump_to_brush.triggered.connect(lambda _c=False: edit_tools.jump_to_brush(editor))

    editor.act_jump_to_item = QAction("Jump to Item...", editor)
    editor.act_jump_to_item.setShortcut(QKeySequence("Ctrl+J"))
    editor.act_jump_to_item.triggered.connect(lambda _c=False: edit_tools.jump_to_item(editor))

    editor.act_duplicate_selection = QAction("Duplicate Selection", editor)
    editor.act_duplicate_selection.setShortcut(QKeySequence("Ctrl+D"))
    editor.act_duplicate_selection.triggered.connect(lambda _c=False: edit_tools.duplicate_selection(editor))

    editor.act_clear_selection = QAction(load_icon("action_clear_selection"), "Clear Selection", editor)
    # NOTE: No shortcut — Esc is handled by act_cancel which calls escape_pressed()
    editor.act_clear_selection.triggered.connect(lambda _c=False: edit_tools.escape_pressed(editor))

    editor.act_move_selection_up = QAction("Move Selection Up", editor)
    editor.act_move_selection_down = QAction("Move Selection Down", editor)
    editor.act_move_selection_up.setShortcut(QKeySequence("Ctrl+PgUp"))
    editor.act_move_selection_down.setShortcut(QKeySequence("Ctrl+PgDown"))
    editor.act_move_selection_up.triggered.connect(lambda _c=False: edit_tools.move_selection_z(editor, -1))
    editor.act_move_selection_down.triggered.connect(lambda _c=False: edit_tools.move_selection_z(editor, +1))

    # Border Options
    editor.act_automagic = QAction(load_icon("tool_automagic"), "Border Automagic", editor)
    editor.act_automagic.setCheckable(True)
    editor.act_automagic.setShortcut(QKeySequence("A"))
    editor.act_automagic.toggled.connect(lambda v: edit_tools.toggle_automagic(editor, v))

    editor.act_borderize_selection = QAction(load_icon("action_borderize"), "Borderize Selection", editor)
    editor.act_borderize_selection.setShortcut(QKeySequence("Ctrl+B"))
    editor.act_borderize_selection.triggered.connect(lambda _c=False: edit_tools.borderize_selection(editor))

    editor.act_border_builder = QAction("Border Builder...", editor)
    editor.act_border_builder.triggered.connect(lambda _c=False: edit_tools.open_border_builder(editor))

    editor.act_borderize_map = QAction("Borderize Map", editor)
    editor.act_borderize_map.triggered.connect(lambda _c=False: edit_tools.borderize_map(editor))

    editor.act_randomize_map_full = QAction("Randomize Map", editor)
    editor.act_randomize_map_full.triggered.connect(lambda _c=False: edit_tools.randomize_map(editor))

    # Symmetry Options
    editor.act_symmetry_vertical = QAction("Symmetry Vertical", editor)
    editor.act_symmetry_vertical.setCheckable(True)
    editor.act_symmetry_vertical.setShortcut(QKeySequence("Ctrl+Shift+V"))
    editor.act_symmetry_vertical.toggled.connect(lambda v: edit_tools.toggle_symmetry_vertical(editor, v))

    editor.act_symmetry_horizontal = QAction("Symmetry Horizontal", editor)
    editor.act_symmetry_horizontal.setCheckable(True)
    editor.act_symmetry_horizontal.setShortcut(QKeySequence("Ctrl+Shift+H"))
    editor.act_symmetry_horizontal.toggled.connect(lambda v: edit_tools.toggle_symmetry_horizontal(editor, v))

    editor.act_fill = QAction(load_icon("action_fill"), "Fill", editor)
    editor.act_fill.setShortcut(QKeySequence("Ctrl+Shift+D"))
    editor.act_fill.triggered.connect(lambda _c=False: edit_tools.arm_fill(editor))

    editor.act_merge_move = QAction("Merge Move", editor)
    editor.act_merge_move.setCheckable(True)
    editor.act_borderize_drag = QAction("Borderize Drag", editor)
    editor.act_borderize_drag.setCheckable(True)
    editor.act_merge_paste = QAction("Merge Paste", editor)
    editor.act_merge_paste.setCheckable(True)
    editor.act_borderize_paste = QAction("Borderize Paste", editor)
    editor.act_borderize_paste.setCheckable(True)

    editor.act_merge_move.triggered.connect(lambda _c=False: edit_tools.apply_ui_state_to_session(editor))
    editor.act_borderize_drag.triggered.connect(lambda _c=False: edit_tools.apply_ui_state_to_session(editor))
    editor.act_merge_paste.triggered.connect(lambda _c=False: edit_tools.apply_ui_state_to_session(editor))
    editor.act_borderize_paste.triggered.connect(lambda _c=False: edit_tools.apply_ui_state_to_session(editor))

    editor.act_selection_mode = QAction(load_icon("action_select"), "Selection Mode", editor)
    editor.act_selection_mode.setCheckable(True)
    editor.act_selection_mode.triggered.connect(lambda _c=False: mode_tools.toggle_selection_mode(editor))

    editor.act_selection_depth_compensate = QAction("Compensate Selection", editor)
    editor.act_selection_depth_current = QAction("Current Floor", editor)
    editor.act_selection_depth_lower = QAction("Lower Floors", editor)
    editor.act_selection_depth_visible = QAction("Visible Floors", editor)

    editor.act_selection_depth_group = QActionGroup(editor)
    editor.act_selection_depth_group.setExclusive(True)
    for act in (
        editor.act_selection_depth_compensate,
        editor.act_selection_depth_current,
        editor.act_selection_depth_lower,
        editor.act_selection_depth_visible,
    ):
        act.setCheckable(True)
        editor.act_selection_depth_group.addAction(act)

    editor.act_selection_depth_compensate.triggered.connect(
        lambda _c=False: mode_tools.set_selection_depth(editor, SelectionDepthMode.COMPENSATE)
    )
    editor.act_selection_depth_current.triggered.connect(
        lambda _c=False: mode_tools.set_selection_depth(editor, SelectionDepthMode.CURRENT)
    )
    editor.act_selection_depth_lower.triggered.connect(
        lambda _c=False: mode_tools.set_selection_depth(editor, SelectionDepthMode.LOWER)
    )
    editor.act_selection_depth_visible.triggered.connect(
        lambda _c=False: mode_tools.set_selection_depth(editor, SelectionDepthMode.VISIBLE)
    )

    # Mirror
    editor.act_toggle_mirror = QAction("Mirror Drawing", editor)
    editor.act_toggle_mirror.setCheckable(True)
    editor.act_toggle_mirror.setShortcut(QKeySequence("Ctrl+Shift+M"))
    editor.act_toggle_mirror.triggered.connect(lambda _c=False: mirror_tools.toggle_mirror_drawing(editor))

    editor.act_mirror_axis_x = QAction("Mirror Axis X", editor)
    editor.act_mirror_axis_x.setCheckable(True)
    editor.act_mirror_axis_x.triggered.connect(lambda _c=False: mirror_tools.set_axis(editor, "x"))

    editor.act_mirror_axis_y = QAction("Mirror Axis Y", editor)
    editor.act_mirror_axis_y.setCheckable(True)
    editor.act_mirror_axis_y.triggered.connect(lambda _c=False: mirror_tools.set_axis(editor, "y"))
    editor.mirror_axis_action_group = QActionGroup(editor)
    editor.mirror_axis_action_group.setExclusive(True)
    editor.mirror_axis_action_group.addAction(editor.act_mirror_axis_x)
    editor.mirror_axis_action_group.addAction(editor.act_mirror_axis_y)

    editor.act_mirror_axis_set_from_cursor = QAction("Set Mirror Axis From Cursor", editor)
    editor.act_mirror_axis_set_from_cursor.setShortcut(QKeySequence("Ctrl+Shift+."))
    editor.act_mirror_axis_set_from_cursor.triggered.connect(lambda _c=False: mirror_tools.set_axis_from_cursor(editor))

    # Zoom
    editor.act_zoom_in = QAction(load_icon("action_zoom_in"), "Zoom In", editor)
    editor.act_zoom_out = QAction(load_icon("action_zoom_out"), "Zoom Out", editor)
    editor.act_zoom_normal = QAction("Zoom Normal", editor)
    editor.act_zoom_normal.setShortcut(QKeySequence("Ctrl+0"))
    editor.act_zoom_in.setShortcut(QKeySequence("Ctrl++"))
    editor.act_zoom_out.setShortcut(QKeySequence("Ctrl+-"))
    editor.act_zoom_in.triggered.connect(lambda _c=False: view_tools.set_zoom(editor, editor.viewport.tile_px + 2))
    editor.act_zoom_out.triggered.connect(lambda _c=False: view_tools.set_zoom(editor, editor.viewport.tile_px - 2))
    editor.act_zoom_normal.triggered.connect(lambda _c=False: view_tools.set_zoom(editor, 16))

    # Window/View parity actions
    editor.act_new_view = QAction("New View", editor)
    editor.act_new_view.setShortcut(QKeySequence("Ctrl+Shift+N"))
    editor.act_new_view.triggered.connect(lambda _c=False: window_tools.new_view(editor))

    editor.act_new_instance = QAction("New Instance", editor)
    editor.act_new_instance.setShortcut(QKeySequence("Ctrl+Alt+N"))
    editor.act_new_instance.triggered.connect(lambda _c=False: window_tools.new_instance(editor))

    editor.act_fullscreen = QAction(load_icon("action_fullscreen"), "Enter Fullscreen", editor)
    editor.act_fullscreen.setShortcut(QKeySequence("F11"))
    editor.act_fullscreen.triggered.connect(lambda _c=False: window_tools.toggle_fullscreen(editor))

    editor.act_take_screenshot = QAction(load_icon("action_screenshot"), "Take Screenshot", editor)
    editor.act_take_screenshot.setShortcut(QKeySequence("F10"))
    editor.act_take_screenshot.triggered.connect(lambda _c=False: window_tools.take_screenshot(editor))

    editor.act_show_shade = QAction("Show shade", editor)
    editor.act_show_shade.setCheckable(True)
    editor.act_show_shade.setShortcut(QKeySequence("Q"))
    editor.act_show_shade.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_shade", v))

    editor.act_show_all_floors = QAction("Show all floors", editor)
    editor.act_show_all_floors.setCheckable(True)
    editor.act_show_all_floors.setShortcut(QKeySequence("Ctrl+W"))
    editor.act_show_all_floors.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_all_floors", v))

    editor.act_show_loose_items = QAction("Ghost loose items", editor)
    editor.act_show_loose_items.setCheckable(True)
    editor.act_show_loose_items.setShortcut(QKeySequence("G"))
    editor.act_show_loose_items.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_loose_items", v))

    editor.act_ghost_higher_floors = QAction("Ghost higher floors", editor)
    editor.act_ghost_higher_floors.setCheckable(True)
    editor.act_ghost_higher_floors.setShortcut(QKeySequence("Ctrl+L"))
    editor.act_ghost_higher_floors.toggled.connect(
        lambda v: window_tools.set_view_flag(editor, "ghost_higher_floors", v)
    )

    editor.act_show_client_box = QAction("Show client box", editor)
    editor.act_show_client_box.setCheckable(True)
    editor.act_show_client_box.setShortcut(QKeySequence("Shift+I"))
    editor.act_show_client_box.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_client_box", v))

    editor.act_show_client_ids = QAction("Show Client IDs", editor)
    editor.act_show_client_ids.setCheckable(True)
    editor.act_show_client_ids.setShortcut(QKeySequence("Ctrl+Shift+I"))
    editor.act_show_client_ids.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_client_ids", v))

    editor.act_show_grid = QAction(load_icon("action_grid"), "Show Grid", editor)
    editor.act_show_grid.setCheckable(True)
    editor.act_show_grid.setShortcut(QKeySequence("Shift+G"))
    editor.act_show_grid.toggled.connect(lambda v: view_tools.toggle_grid(editor, v))

    editor.act_highlight_items = QAction("Highlight items", editor)
    editor.act_highlight_items.setCheckable(True)
    editor.act_highlight_items.setShortcut(QKeySequence("V"))
    editor.act_highlight_items.toggled.connect(lambda v: window_tools.set_view_flag(editor, "highlight_items", v))

    editor.act_show_monsters = QAction("Show monsters", editor)
    editor.act_show_monsters.setCheckable(True)
    editor.act_show_monsters.setShortcut(QKeySequence("F"))
    editor.act_show_monsters.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_monsters", v))

    editor.act_show_monsters_spawns = QAction("Show monsters spawns", editor)
    editor.act_show_monsters_spawns.setCheckable(True)
    editor.act_show_monsters_spawns.setShortcut(QKeySequence("S"))
    editor.act_show_monsters_spawns.toggled.connect(
        lambda v: window_tools.set_view_flag(editor, "show_monsters_spawns", v)
    )

    editor.act_show_npcs = QAction("Show npcs", editor)
    editor.act_show_npcs.setCheckable(True)
    # Free up legacy Z/X for brush variation cycling.
    editor.act_show_npcs.setShortcut(QKeySequence("Alt+X"))
    editor.act_show_npcs.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_npcs", v))

    # Legacy-inspired: brush variation hotkeys (Z/X)
    editor.act_brush_variation_prev = QAction("Brush Variation -", editor)
    editor.act_brush_variation_prev.setShortcut(QKeySequence("Z"))
    editor.act_brush_variation_prev.triggered.connect(lambda _c=False: editor._cycle_brush_variation(-1))
    editor.addAction(editor.act_brush_variation_prev)

    editor.act_brush_variation_next = QAction("Brush Variation +", editor)
    editor.act_brush_variation_next.setShortcut(QKeySequence("X"))
    editor.act_brush_variation_next.triggered.connect(lambda _c=False: editor._cycle_brush_variation(1))
    editor.addAction(editor.act_brush_variation_next)

    editor.act_show_npcs_spawns = QAction("Show npcs spawns", editor)
    editor.act_show_npcs_spawns.setCheckable(True)
    # NOTE: C++ does not assign a hotkey to Show NPC Spawns. U belongs to Highlight Locked Doors.
    editor.act_show_npcs_spawns.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_npcs_spawns", v))

    editor.act_show_special = QAction("Show special", editor)
    editor.act_show_special.setCheckable(True)
    editor.act_show_special.setShortcut(QKeySequence("E"))
    editor.act_show_special.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_special", v))

    editor.act_show_as_minimap = QAction(load_icon("action_minimap"), "Show as minimap", editor)
    editor.act_show_as_minimap.setCheckable(True)
    editor.act_show_as_minimap.setShortcut(QKeySequence("Shift+E"))
    editor.act_show_as_minimap.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_as_minimap", v))

    editor.act_only_show_colors = QAction("Only show colors", editor)
    editor.act_only_show_colors.setCheckable(True)
    editor.act_only_show_colors.setShortcut(QKeySequence("Ctrl+E"))
    editor.act_only_show_colors.toggled.connect(lambda v: window_tools.set_view_flag(editor, "only_show_colors", v))

    # Dark Mode
    editor.act_toggle_dark_mode = QAction("Dark Mode", editor)
    editor.act_toggle_dark_mode.setCheckable(True)
    editor.act_toggle_dark_mode.setShortcut(QKeySequence("Ctrl+Shift+D"))
    editor.act_toggle_dark_mode.toggled.connect(lambda v: window_tools.toggle_dark_mode(editor, v))

    editor.act_only_show_modified = QAction("Only show modified", editor)
    editor.act_only_show_modified.setCheckable(True)
    editor.act_only_show_modified.setShortcut(QKeySequence("Ctrl+M"))
    editor.act_only_show_modified.toggled.connect(lambda v: window_tools.set_view_flag(editor, "only_show_modified", v))

    editor.act_clear_modified_state = QAction("Clear Modified State", editor)
    editor.act_clear_modified_state.triggered.connect(lambda _c=False: editor._clear_modified_state())

    # Tools (Edit -> Tools)
    editor.act_clear_invalid_tiles_selection = QAction("Clear Invalid Tiles (Selection)", editor)
    editor.act_clear_invalid_tiles_selection.triggered.connect(
        lambda _c=False: editor._clear_invalid_tiles(selection_only=True)
    )

    editor.act_clear_invalid_tiles_map = QAction("Clear Invalid Tiles (Map)", editor)
    editor.act_clear_invalid_tiles_map.triggered.connect(
        lambda _c=False: editor._clear_invalid_tiles(selection_only=False)
    )

    editor.act_randomize_selection = QAction(load_icon("action_randomize"), "Randomize (Selection)", editor)
    editor.act_randomize_selection.triggered.connect(lambda _c=False: editor._randomize(selection_only=True))

    editor.act_randomize_map = QAction("Randomize (Map)", editor)
    editor.act_randomize_map.triggered.connect(lambda _c=False: editor._randomize(selection_only=False))

    # Map Tools (New Legacy Parity)
    editor.act_remove_item_map = QAction(load_icon("action_remove_item"), "Remove Items by ID...", editor)
    editor.act_remove_item_map.setShortcut(QKeySequence("Ctrl+Shift+R"))
    editor.act_remove_item_map.triggered.connect(lambda _c=False: editor._map_remove_item_global())

    editor.act_remove_corpses_map = QAction("Remove all Corpses...", editor)
    editor.act_remove_corpses_map.triggered.connect(lambda _c=False: editor._map_remove_corpses())

    editor.act_remove_unreachable_map = QAction("Remove all Unreachable Tiles...", editor)
    editor.act_remove_unreachable_map.triggered.connect(lambda _c=False: editor._map_remove_unreachable())

    editor.act_clear_invalid_house_tiles_map = QAction("Clear Invalid Houses", editor)
    editor.act_clear_invalid_house_tiles_map.triggered.connect(lambda _c=False: editor._map_clear_invalid_house_tiles())

    editor.act_remove_monsters_selection = QAction("Remove Monsters", editor)
    editor.act_remove_monsters_selection.triggered.connect(
        lambda _c=False: map_tools.remove_monsters(editor, selection_only=True)
    )

    editor.act_convert_map_format = QAction("Convert Map Format...", editor)
    editor.act_convert_map_format.triggered.connect(lambda _c=False: editor._convert_map_format())

    # Map legacy parity (C++ Map menu)
    editor.act_edit_towns = QAction(load_icon("action_town"), "Edit Towns...", editor)
    editor.act_edit_towns.setShortcut(QKeySequence("Ctrl+T"))
    editor.act_edit_towns.triggered.connect(lambda _c=False: editor._edit_towns())

    editor.act_map_cleanup = QAction(load_icon("action_cleanup"), "Cleanup...", editor)
    editor.act_map_cleanup.triggered.connect(lambda _c=False: editor._map_cleanup())

    editor.act_map_properties = QAction(load_icon("action_properties"), "Properties...", editor)
    editor.act_map_properties.setShortcut(QKeySequence("Ctrl+P"))
    editor.act_map_properties.triggered.connect(lambda _c=False: editor._open_map_properties())

    editor.act_map_statistics_legacy = QAction(load_icon("action_statistics"), "Statistics", editor)
    editor.act_map_statistics_legacy.setShortcut(QKeySequence("F8"))
    editor.act_map_statistics_legacy.triggered.connect(lambda _c=False: editor._show_map_statistics())

    # Floor navigation (C++ Navigate > Floor submenu)
    editor.act_floor_actions = []
    for floor_level in range(16):
        act = QAction(f"Floor {floor_level}", editor)
        act.triggered.connect(
            (lambda fl: lambda _c=False: view_tools.goto_floor(editor, fl))(floor_level)
        )
        editor.act_floor_actions.append(act)

    # Navigate actions (C++ Navigate menu)
    # NOTE: act_goto_previous_position is created later in this function;
    # build_menus.py references it directly — no alias needed here.

    # View/Show toggles missing from C++ parity
    editor.act_always_show_zones = QAction("Always show zones", editor)
    editor.act_always_show_zones.setCheckable(True)
    editor.act_always_show_zones.toggled.connect(
        lambda v: window_tools.set_view_flag(editor, "always_show_zones", v)
    )

    editor.act_ext_house_shader = QAction("Extended house shader", editor)
    editor.act_ext_house_shader.setCheckable(True)
    editor.act_ext_house_shader.toggled.connect(
        lambda v: window_tools.set_view_flag(editor, "ext_house_shader", v)
    )

    editor.act_show_light_strength = QAction("Show light strength", editor)
    editor.act_show_light_strength.setCheckable(True)
    editor.act_show_light_strength.setShortcut(QKeySequence("Shift+K"))
    editor.act_show_light_strength.toggled.connect(
        lambda v: window_tools.set_view_flag(editor, "show_light_strength", v)
    )

    editor.act_show_technical_items = QAction("Show technical items", editor)
    editor.act_show_technical_items.setCheckable(True)
    editor.act_show_technical_items.setShortcut(QKeySequence("Shift+T"))
    editor.act_show_technical_items.toggled.connect(
        lambda v: window_tools.set_view_flag(editor, "show_technical_items", v)
    )

    editor.act_show_towns = QAction("Show towns", editor)
    editor.act_show_towns.setCheckable(True)
    editor.act_show_towns.toggled.connect(
        lambda v: window_tools.set_view_flag(editor, "show_towns", v)
    )

    editor.act_show_waypoints = QAction("Show waypoints", editor)
    editor.act_show_waypoints.setCheckable(True)
    editor.act_show_waypoints.setShortcut(QKeySequence("Shift+W"))
    editor.act_show_waypoints.toggled.connect(
        lambda v: window_tools.set_view_flag(editor, "show_waypoints", v)
    )

    editor.act_highlight_locked_doors = QAction("Highlight locked doors", editor)
    editor.act_highlight_locked_doors.setCheckable(True)
    editor.act_highlight_locked_doors.setShortcut(QKeySequence("U"))
    editor.act_highlight_locked_doors.toggled.connect(
        lambda v: window_tools.set_view_flag(editor, "highlight_locked_doors", v)
    )

    editor.act_experimental_fog = QAction("Fog in light view", editor)
    editor.act_experimental_fog.setCheckable(True)
    editor.act_experimental_fog.toggled.connect(
        lambda v: window_tools.set_view_flag(editor, "experimental_fog", v)
    )

    # Show Lights (C++ Show menu: Shift+L)
    editor.act_show_lights = QAction(load_icon("action_show_lights"), "Show Light", editor)
    editor.act_show_lights.setCheckable(True)
    editor.act_show_lights.setShortcut(QKeySequence("Shift+L"))
    editor.act_show_lights.setChecked(bool(getattr(editor, "show_lights", False)))
    editor.act_show_lights.toggled.connect(
        lambda v: window_tools.set_view_flag(editor, "show_lights", v)
    )

    # Selection menu actions (C++ parity)
    editor.act_replace_items_on_selection = QAction(load_icon("action_replace"), "Replace Items on Selection", editor)
    editor.act_replace_items_on_selection.triggered.connect(
        lambda _c=False: editor._replace_items_on_selection()
    )

    editor.act_remove_item_on_selection = QAction(load_icon("action_remove_item"), "Remove Item on Selection", editor)
    editor.act_remove_item_on_selection.triggered.connect(
        lambda _c=False: editor._remove_item_on_selection()
    )

    editor.act_waypoint_set_here = QAction("Set Waypoint Here...", editor)
    editor.act_waypoint_set_here.triggered.connect(lambda _c=False: editor._waypoint_set_here())

    editor.act_waypoint_delete = QAction("Delete Waypoint...", editor)
    editor.act_waypoint_delete.triggered.connect(lambda _c=False: editor._waypoint_delete())

    editor.act_switch_door_here = QAction("Switch Door", editor)
    editor.act_switch_door_here.triggered.connect(lambda _c=False: editor._switch_door_here())

    editor.act_town_add_edit = QAction("Add/Edit Town...", editor)
    editor.act_town_add_edit.triggered.connect(lambda _c=False: editor._town_add_edit())

    editor.act_town_set_temple_here = QAction("Set Town Temple Here...", editor)
    editor.act_town_set_temple_here.triggered.connect(lambda _c=False: editor._town_set_temple_here())

    editor.act_town_delete = QAction("Delete Town...", editor)
    editor.act_town_delete.triggered.connect(lambda _c=False: editor._town_delete())

    editor.act_house_set_id_on_selection = QAction("Set House ID on Selection...", editor)
    editor.act_house_set_id_on_selection.triggered.connect(lambda _c=False: editor._house_set_id_on_selection())

    editor.act_house_clear_id_on_selection = QAction("Clear House ID on Selection", editor)
    editor.act_house_clear_id_on_selection.triggered.connect(lambda _c=False: editor._house_clear_id_on_selection())

    editor.act_house_add_edit = QAction("Add/Edit House...", editor)
    editor.act_house_add_edit.triggered.connect(lambda _c=False: editor._house_add_edit())

    editor.act_house_set_entry_here = QAction("Set House Entry Here...", editor)
    editor.act_house_set_entry_here.triggered.connect(lambda _c=False: editor._house_set_entry_here())

    editor.act_house_delete_definition = QAction("Delete House...", editor)
    editor.act_house_delete_definition.triggered.connect(lambda _c=False: editor._house_delete_definition())

    editor.act_zone_add_edit = QAction("Add/Edit Zone...", editor)
    editor.act_zone_add_edit.triggered.connect(lambda _c=False: editor._zone_add_edit())

    editor.act_zone_delete_definition = QAction("Delete Zone...", editor)
    editor.act_zone_delete_definition.triggered.connect(lambda _c=False: editor._zone_delete_definition())

    editor.act_monster_spawn_set_here = QAction("Set Monster Spawn Here...", editor)
    editor.act_monster_spawn_set_here.triggered.connect(lambda _c=False: editor._monster_spawn_set_here())

    editor.act_monster_spawn_delete_here = QAction("Delete Monster Spawn Here", editor)
    editor.act_monster_spawn_delete_here.triggered.connect(lambda _c=False: editor._monster_spawn_delete_here())

    editor.act_npc_spawn_set_here = QAction("Set NPC Spawn Here...", editor)
    editor.act_npc_spawn_set_here.triggered.connect(lambda _c=False: editor._npc_spawn_set_here())

    editor.act_npc_spawn_delete_here = QAction("Delete NPC Spawn Here", editor)
    editor.act_npc_spawn_delete_here.triggered.connect(lambda _c=False: editor._npc_spawn_delete_here())

    editor.act_monster_spawn_add_entry_here = QAction("Add Monster Here...", editor)
    editor.act_monster_spawn_add_entry_here.triggered.connect(lambda _c=False: editor._monster_spawn_add_entry_here())

    editor.act_monster_spawn_delete_entry_here = QAction("Delete Monster Here...", editor)
    editor.act_monster_spawn_delete_entry_here.triggered.connect(
        lambda _c=False: editor._monster_spawn_delete_entry_here()
    )

    editor.act_npc_spawn_add_entry_here = QAction("Add NPC Here...", editor)
    editor.act_npc_spawn_add_entry_here.triggered.connect(lambda _c=False: editor._npc_spawn_add_entry_here())

    editor.act_npc_spawn_delete_entry_here = QAction("Delete NPC Here...", editor)
    editor.act_npc_spawn_delete_entry_here.triggered.connect(lambda _c=False: editor._npc_spawn_delete_entry_here())

    editor.act_show_houses = QAction(load_icon("action_show_houses"), "Show houses", editor)
    editor.act_show_houses.setCheckable(True)
    editor.act_show_houses.setShortcut(QKeySequence("Ctrl+H"))
    editor.act_show_houses.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_houses_overlay", v))

    editor.act_show_pathing = QAction(load_icon("action_show_pathing"), "Show pathing", editor)
    editor.act_show_pathing.setCheckable(True)
    editor.act_show_pathing.setShortcut(QKeySequence("O"))
    editor.act_show_pathing.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_pathing", v))

    editor.act_show_tooltips = QAction("Show Tooltips", editor)
    editor.act_show_tooltips.setCheckable(True)
    editor.act_show_tooltips.setShortcut(QKeySequence("Y"))
    editor.act_show_tooltips.toggled.connect(lambda v: window_tools.set_view_flag(editor, "show_tooltips", v))

    editor.act_show_preview = QAction(load_icon("action_animation"), "Show Animation", editor)
    editor.act_show_preview.setCheckable(True)
    editor.act_show_preview.setShortcut(QKeySequence("L"))
    editor.act_show_preview.toggled.connect(lambda v: window_tools.toggle_sprite_preview(editor, v))

    editor.act_ingame_preview = QAction(load_icon("action_ingame_preview"), "In-Game Preview", editor)
    editor.act_ingame_preview.setCheckable(True)
    editor.act_ingame_preview.setShortcut(QKeySequence("F9"))
    editor.act_ingame_preview.toggled.connect(lambda v: view_tools.toggle_ingame_preview(editor, v))

    editor.act_show_indicators_simple = QAction("Show Indicators", editor)
    editor.act_show_indicators_simple.setCheckable(True)
    editor.act_show_indicators_simple.toggled.connect(lambda v: window_tools.toggle_indicators_simple(editor, v))

    # Indicators fine-grained
    editor.act_show_wall_hooks = QAction(load_icon("indicator_hooks"), "Wall Hooks", editor)
    editor.act_show_wall_hooks.setCheckable(True)
    editor.act_show_wall_hooks.setShortcut(QKeySequence("K"))
    editor.act_show_wall_hooks.toggled.connect(lambda v: window_tools.toggle_wall_hooks(editor, v))

    editor.act_show_pickupables = QAction(load_icon("indicator_pickupables"), "Pickupables", editor)
    editor.act_show_pickupables.setCheckable(True)
    editor.act_show_pickupables.toggled.connect(lambda v: window_tools.toggle_pickupables(editor, v))

    editor.act_show_moveables = QAction(load_icon("indicator_moveables"), "Moveables", editor)
    editor.act_show_moveables.setCheckable(True)
    editor.act_show_moveables.toggled.connect(lambda v: window_tools.toggle_moveables(editor, v))

    editor.act_show_avoidables = QAction(load_icon("indicator_avoidables"), "Avoidables", editor)
    editor.act_show_avoidables.setCheckable(True)
    editor.act_show_avoidables.toggled.connect(lambda v: window_tools.toggle_avoidables(editor, v))

    # GoTo (matches screenshot)
    editor.act_goto_previous_position = QAction(load_icon("action_goto_back"), "Go to Previous Position", editor)
    editor.act_goto_previous_position.setShortcut(QKeySequence("P"))
    editor.act_goto_previous_position.triggered.connect(lambda _c=False: edit_tools.goto_previous_position(editor))

    editor.act_goto_position = QAction(load_icon("action_goto"), "Go to Position...", editor)
    editor.act_goto_position.setShortcut(QKeySequence("Ctrl+G"))
    editor.act_goto_position.triggered.connect(lambda _c=False: edit_tools.goto_position(editor))

    # Palettes
    editor.act_new_palette = QAction("New Palette", editor)
    editor.act_palette_terrain = QAction(load_icon("action_terrain"), "Terrain", editor)
    editor.act_palette_doodad = QAction("Doodad", editor)
    editor.act_palette_item = QAction("Item", editor)
    editor.act_palette_collection = QAction("Collection", editor)
    editor.act_palette_house = QAction(load_icon("action_house"), "House", editor)
    editor.act_palette_creature = QAction(load_icon("action_creature"), "Creature", editor)
    editor.act_palette_npc = QAction("NPC", editor)
    editor.act_palette_waypoint = QAction(load_icon("action_waypoint"), "Waypoint", editor)
    editor.act_palette_zones = QAction("Zones", editor)
    editor.act_palette_raw = QAction("RAW", editor)
    editor.palette_action_group = QActionGroup(editor)
    editor.palette_action_group.setExclusive(True)
    for _act in (
        editor.act_palette_terrain,
        editor.act_palette_doodad,
        editor.act_palette_item,
        editor.act_palette_collection,
        editor.act_palette_house,
        editor.act_palette_creature,
        editor.act_palette_npc,
        editor.act_palette_waypoint,
        editor.act_palette_zones,
        editor.act_palette_raw,
    ):
        _act.setCheckable(True)
        editor.palette_action_group.addAction(_act)
    editor.act_palette_large_icons = QAction("Large Palette Icons", editor)
    editor.act_palette_large_icons.setCheckable(True)
    editor.act_palette_large_icons.toggled.connect(lambda v: editor._toggle_palette_large_icons(v))

    editor.act_palette_terrain.setShortcut(QKeySequence("T"))
    editor.act_palette_doodad.setShortcut(QKeySequence("D"))
    editor.act_palette_item.setShortcut(QKeySequence("I"))
    editor.act_palette_collection.setShortcut(QKeySequence("N"))
    editor.act_palette_house.setShortcut(QKeySequence("H"))
    editor.act_palette_creature.setShortcut(QKeySequence("C"))
    editor.act_palette_npc.setShortcut(QKeySequence("Alt+N"))
    editor.act_palette_waypoint.setShortcut(QKeySequence("W"))
    editor.act_palette_zones.setShortcut(QKeySequence("Ctrl+Alt+Z"))
    editor.act_palette_raw.setShortcut(QKeySequence("R"))

    editor.act_new_palette.triggered.connect(lambda _c=False: edit_tools.create_additional_palette(editor))
    editor.act_palette_terrain.triggered.connect(lambda _c=False: edit_tools.select_palette(editor, "terrain"))
    editor.act_palette_doodad.triggered.connect(lambda _c=False: edit_tools.select_palette(editor, "doodad"))
    editor.act_palette_item.triggered.connect(lambda _c=False: edit_tools.select_palette(editor, "item"))
    editor.act_palette_collection.triggered.connect(lambda _c=False: edit_tools.select_palette(editor, "collection"))
    editor.act_palette_house.triggered.connect(lambda _c=False: edit_tools.select_palette(editor, "house"))
    editor.act_palette_creature.triggered.connect(lambda _c=False: edit_tools.select_palette(editor, "creature"))
    editor.act_palette_npc.triggered.connect(lambda _c=False: edit_tools.select_palette(editor, "npc"))
    editor.act_palette_waypoint.triggered.connect(lambda _c=False: edit_tools.select_palette(editor, "waypoint"))
    editor.act_palette_zones.triggered.connect(lambda _c=False: edit_tools.select_palette(editor, "zones"))
    editor.act_palette_raw.triggered.connect(lambda _c=False: edit_tools.select_palette(editor, "raw"))

    # Docks
    editor.act_window_minimap = QAction(load_icon("action_minimap"), "Minimap", editor)
    editor.act_window_minimap.setCheckable(True)
    editor.act_window_minimap.setShortcut(QKeySequence("M"))
    editor.act_window_minimap.toggled.connect(lambda v: window_tools.toggle_minimap_dock(editor, v))

    editor.act_window_tool_options = QAction("Tool Options", editor)
    editor.act_window_tool_options.triggered.connect(lambda _c=False: window_tools.open_tool_options(editor))

    editor.act_window_actions_history = QAction("Actions History", editor)
    editor.act_window_actions_history.setCheckable(True)
    editor.act_window_actions_history.toggled.connect(lambda v: window_tools.toggle_actions_history_dock(editor, v))

    editor.act_window_live_log = QAction("Live Log", editor)
    editor.act_window_live_log.setCheckable(True)
    editor.act_window_live_log.toggled.connect(lambda v: window_tools.toggle_live_log_dock(editor, v))

    editor.act_window_friends = QAction("Friends", editor)
    editor.act_window_friends.setCheckable(True)
    editor.act_window_friends.toggled.connect(lambda v: window_tools.toggle_friends_dock(editor, v))

    # Assets
    editor.act_manage_client_profiles = QAction("Manage Client Profiles...", editor)
    editor.act_manage_client_profiles.triggered.connect(lambda _c=False: assets_tools.manage_client_profiles(editor))

    editor.act_load_client_data_stack = QAction("Load Client Data...", editor)
    editor.act_load_client_data_stack.triggered.connect(lambda _c=False: assets_tools.load_client_data_stack(editor))

    editor.act_set_assets_dir = QAction("Set Assets Directory…", editor)
    editor.act_set_assets_dir.triggered.connect(lambda _c=False: assets_tools.choose_assets_dir(editor))

    editor.act_load_appearances = QAction("Load appearances.dat…", editor)
    editor.act_load_appearances.triggered.connect(lambda _c=False: assets_tools.load_appearances(editor))

    editor.act_unload_appearances = QAction("Unload appearances.dat", editor)
    editor.act_unload_appearances.triggered.connect(lambda _c=False: assets_tools.unload_appearances(editor))

    # Find
    editor.act_find_item = QAction(load_icon("action_find"), "Find Item...", editor)
    editor.act_find_item.setShortcut(QKeySequence("Ctrl+F"))
    editor.act_find_item.triggered.connect(lambda _c=False: find_item.open_find_dialog(editor, "item"))

    # Find Everything (C++ parity: Search > Find Everything)
    editor.act_find_everything_map = QAction("Find Everything", editor)
    editor.act_find_everything_map.triggered.connect(
        lambda _c=False: find_item.open_find_everything(editor, selection_only=False)
    )

    editor.act_find_everything_selection = QAction("Find Everything", editor)
    editor.act_find_everything_selection.triggered.connect(
        lambda _c=False: find_item.open_find_everything(editor, selection_only=True)
    )

    editor.act_find_item_selection = QAction("Find Item on Selection", editor)
    editor.act_find_item_selection.triggered.connect(
        lambda _c=False: find_item.open_find_dialog(editor, "item", selection_only=True)
    )

    editor.act_find_creature = QAction(load_icon("action_creature"), "Find Creature...", editor)
    editor.act_find_creature.triggered.connect(lambda _c=False: find_item.open_find_dialog(editor, "creature"))

    # Aliases for rollout plan coverage
    editor.act_find_monster = QAction("Find Monster...", editor)
    editor.act_find_monster.triggered.connect(lambda _c=False: find_item.open_find_dialog(editor, "creature"))

    editor.act_find_npc = QAction("Find NPC...", editor)
    editor.act_find_npc.triggered.connect(lambda _c=False: find_item.open_find_dialog(editor, "creature"))

    editor.act_find_house = QAction(load_icon("action_house"), "Find House...", editor)
    editor.act_find_house.triggered.connect(lambda _c=False: find_item.open_find_dialog(editor, "house"))

    editor.act_find_unique_map = QAction("Find Unique", editor)
    editor.act_find_unique_map.triggered.connect(
        lambda _c=False: find_item.open_find_unique(editor, selection_only=False)
    )

    editor.act_find_action_map = QAction("Find Action", editor)
    editor.act_find_action_map.triggered.connect(
        lambda _c=False: find_item.open_find_action(editor, selection_only=False)
    )

    editor.act_find_container_map = QAction("Find Container", editor)
    editor.act_find_container_map.triggered.connect(
        lambda _c=False: find_item.open_find_container(editor, selection_only=False)
    )

    editor.act_find_writeable_map = QAction("Find Writeable", editor)
    editor.act_find_writeable_map.triggered.connect(
        lambda _c=False: find_item.open_find_writeable(editor, selection_only=False)
    )

    editor.act_find_unique_selection = QAction("Find Unique", editor)
    editor.act_find_unique_selection.triggered.connect(
        lambda _c=False: find_item.open_find_unique(editor, selection_only=True)
    )

    editor.act_find_action_selection = QAction("Find Action", editor)
    editor.act_find_action_selection.triggered.connect(
        lambda _c=False: find_item.open_find_action(editor, selection_only=True)
    )

    editor.act_find_container_selection = QAction("Find Container", editor)
    editor.act_find_container_selection.triggered.connect(
        lambda _c=False: find_item.open_find_container(editor, selection_only=True)
    )

    editor.act_find_writeable_selection = QAction("Find Writeable", editor)
    editor.act_find_writeable_selection.triggered.connect(
        lambda _c=False: find_item.open_find_writeable(editor, selection_only=True)
    )

    # Live Editing
    editor.act_src_connect = QAction("Connect to Server...", editor)
    editor.act_src_connect.triggered.connect(lambda _c=False: live_connect.open_connect_dialog(editor))

    editor.act_src_disconnect = QAction("Disconnect", editor)
    editor.act_src_disconnect.triggered.connect(lambda _c=False: live_connect.disconnect_live(editor))

    editor.act_live_host = QAction("Host Live Server...", editor)
    editor.act_live_host.triggered.connect(lambda _c=False: live_connect.open_host_dialog(editor))

    editor.act_live_stop = QAction("Stop Live Server", editor)
    editor.act_live_stop.triggered.connect(lambda _c=False: live_connect.stop_host(editor))

    editor.act_live_kick = QAction("Kick Client...", editor)
    editor.act_live_kick.triggered.connect(lambda _c=False: live_connect.kick_client(editor))

    editor.act_live_ban = QAction("Ban Client...", editor)
    editor.act_live_ban.triggered.connect(lambda _c=False: live_connect.ban_client(editor))

    # Apply defaults based on editor state (idempotent)
    editor.act_show_grid.setChecked(bool(getattr(editor, "show_grid", True)))
    editor.act_show_wall_hooks.setChecked(bool(getattr(editor, "show_wall_hooks", False)))
    editor.act_show_pickupables.setChecked(bool(getattr(editor, "show_pickupables", False)))
    editor.act_show_moveables.setChecked(bool(getattr(editor, "show_moveables", False)))
    editor.act_show_avoidables.setChecked(bool(getattr(editor, "show_avoidables", False)))

    editor.act_show_shade.setChecked(bool(getattr(editor, "show_shade", False)))
    editor.act_show_all_floors.setChecked(bool(getattr(editor, "show_all_floors", True)))
    editor.act_show_loose_items.setChecked(bool(getattr(editor, "show_loose_items", False)))
    editor.act_ghost_higher_floors.setChecked(bool(getattr(editor, "ghost_higher_floors", False)))
    editor.act_show_client_box.setChecked(bool(getattr(editor, "show_client_box", False)))
    editor.act_show_client_ids.setChecked(bool(getattr(editor, "show_client_ids", False)))

    editor.act_highlight_items.setChecked(bool(getattr(editor, "highlight_items", False)))

    editor.act_show_monsters.setChecked(bool(getattr(editor, "show_monsters", True)))
    editor.act_show_monsters_spawns.setChecked(bool(getattr(editor, "show_monsters_spawns", True)))
    editor.act_show_npcs.setChecked(bool(getattr(editor, "show_npcs", True)))
    editor.act_show_npcs_spawns.setChecked(bool(getattr(editor, "show_npcs_spawns", False)))
    editor.act_show_special.setChecked(bool(getattr(editor, "show_special", False)))

    editor.act_show_as_minimap.setChecked(bool(getattr(editor, "show_as_minimap", False)))
    editor.act_only_show_colors.setChecked(bool(getattr(editor, "only_show_colors", False)))
    editor.act_only_show_modified.setChecked(bool(getattr(editor, "only_show_modified", False)))

    editor.act_show_houses.setChecked(bool(getattr(editor, "show_houses_overlay", True)))
    editor.act_show_pathing.setChecked(bool(getattr(editor, "show_pathing", False)))
    editor.act_show_tooltips.setChecked(bool(getattr(editor, "show_tooltips", True)))
    editor.act_show_preview.setChecked(bool(getattr(editor, "show_preview", True)))
    editor.act_show_indicators_simple.setChecked(bool(getattr(editor, "show_indicators", True)))
    if hasattr(editor, "act_ingame_preview"):
        editor.act_ingame_preview.setChecked(bool(getattr(editor, "ingame_preview_enabled", False)))

    # New view toggles defaults (C++ parity)
    editor.act_always_show_zones.setChecked(bool(getattr(editor, "always_show_zones", False)))
    editor.act_ext_house_shader.setChecked(bool(getattr(editor, "ext_house_shader", False)))
    editor.act_show_light_strength.setChecked(bool(getattr(editor, "show_light_strength", False)))
    editor.act_show_technical_items.setChecked(bool(getattr(editor, "show_technical_items", False)))
    editor.act_show_towns.setChecked(bool(getattr(editor, "show_towns", False)))
    editor.act_show_waypoints.setChecked(bool(getattr(editor, "show_waypoints", False)))
    editor.act_highlight_locked_doors.setChecked(bool(getattr(editor, "highlight_locked_doors", False)))
    editor.act_experimental_fog.setChecked(bool(getattr(editor, "experimental_fog", False)))

    # Selection depth defaults (legacy uses COMPENSATE)
    try:
        depth_mode = editor.session.get_selection_depth_mode()
    except Exception:
        depth_mode = SelectionDepthMode.COMPENSATE
    editor._sync_selection_depth_actions(depth_mode)
