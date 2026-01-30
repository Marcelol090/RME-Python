from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtGui import QAction

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


def build_menus_and_toolbars(editor: QtMapEditor) -> None:
    mb = editor.menuBar()

    m_file = mb.addMenu("File")
    m_file.addAction(editor.act_new)
    m_file.addAction(editor.act_open)
    m_file.addAction(editor.act_save)
    m_file.addAction(editor.act_save_as)
    m_file.addSeparator()

    if (
        hasattr(editor, "act_import_monsters_npcs")
        or hasattr(editor, "act_import_monster_folder")
        or hasattr(editor, "act_import_map")
    ):
        m_import = m_file.addMenu("Import")
        if hasattr(editor, "act_import_map"):
            m_import.addAction(editor.act_import_map)
        if hasattr(editor, "act_import_monsters_npcs"):
            m_import.addAction(editor.act_import_monsters_npcs)
        if hasattr(editor, "act_import_monster_folder"):
            m_import.addAction(editor.act_import_monster_folder)
        m_file.addSeparator()

    # Export submenu
    if hasattr(editor, "act_export_png"):
        m_export = m_file.addMenu("Export")
        m_export.addAction(editor.act_export_png)
        m_file.addSeparator()

    m_file.addAction(editor.act_exit)

    m_edit = mb.addMenu("Edit")
    m_edit.addAction(editor.act_undo)
    m_edit.addAction(editor.act_redo)
    m_edit.addAction(editor.act_cancel)
    m_edit.addSeparator()

    # Screenshot shows Find/Replace/Map stats before Border Options.
    if hasattr(editor, "act_find_item"):
        m_edit.addAction(editor.act_find_item)
    if hasattr(editor, "act_find_creature"):
        m_edit.addAction(editor.act_find_creature)
    if hasattr(editor, "act_find_house"):
        m_edit.addAction(editor.act_find_house)
    if hasattr(editor, "act_find_npc"):
        m_edit.addAction(editor.act_find_npc)
    if hasattr(editor, "act_find_monster"):
        m_edit.addAction(editor.act_find_monster)

    if hasattr(editor, "act_map_statistics"):
        m_edit.addAction(editor.act_map_statistics)
    if hasattr(editor, "act_replace_items"):
        m_edit.addAction(editor.act_replace_items)
    if hasattr(editor, "act_replace_items_on_selection"):
        m_edit.addAction(editor.act_replace_items_on_selection)
    if hasattr(editor, "act_remove_item_on_selection"):
        m_edit.addAction(editor.act_remove_item_on_selection)
    if hasattr(editor, "menu_find_on_map"):
        m_edit.addMenu(editor.menu_find_on_map)

    if any(
        hasattr(editor, a)
        for a in (
            "act_find_item",
            "act_map_statistics",
            "act_replace_items",
            "act_replace_items_on_selection",
            "act_remove_item_on_selection",
            "menu_find_on_map",
        )
    ):
        m_edit.addSeparator()

    m_border = m_edit.addMenu("Border Options")
    m_border.addAction(editor.act_automagic)
    m_border.addSeparator()
    m_border.addAction(editor.act_borderize_selection)
    if hasattr(editor, "act_border_builder"):
        m_border.addSeparator()
        m_border.addAction(editor.act_border_builder)

    # Symmetry submenu
    if hasattr(editor, "act_symmetry_vertical"):
        m_symmetry = m_edit.addMenu("Symmetry")
        m_symmetry.addAction(editor.act_symmetry_vertical)
        m_symmetry.addAction(editor.act_symmetry_horizontal)

    # Tools Menu (Top Level)
    if hasattr(editor, "menu_tools"):
        mb.addMenu(editor.menu_tools)

    m_edit.addSeparator()
    m_edit.addAction(editor.act_goto_previous_position)
    m_edit.addAction(editor.act_goto_position)
    m_edit.addSeparator()

    m_edit.addAction(editor.act_jump_to_brush)
    m_edit.addAction(editor.act_jump_to_item)
    m_edit.addSeparator()

    m_edit.addAction(editor.act_cut)
    m_edit.addAction(editor.act_copy)
    m_edit.addAction(editor.act_paste)
    m_edit.addSeparator()
    m_edit.addAction(editor.act_delete_selection)

    m_edit.addSeparator()
    m_edit.addAction(editor.act_copy_position)
    m_edit.addAction(editor.act_duplicate_selection)
    m_edit.addAction(editor.act_clear_selection)

    m_edit.addSeparator()
    m_edit.addAction(editor.act_move_selection_up)
    m_edit.addAction(editor.act_move_selection_down)

    m_edit.addSeparator()
    m_edit.addAction(editor.act_fill)

    m_edit.addSeparator()
    m_edit.addAction(editor.act_merge_move)
    m_edit.addAction(editor.act_borderize_drag)
    m_edit.addAction(editor.act_merge_paste)
    m_edit.addAction(editor.act_borderize_paste)

    m_mode = mb.addMenu("Mode")
    m_mode.addAction(editor.act_selection_mode)
    m_selection_depth = m_mode.addMenu("Selection Depth")
    m_selection_depth.addAction(editor.act_selection_depth_compensate)
    m_selection_depth.addAction(editor.act_selection_depth_current)
    m_selection_depth.addAction(editor.act_selection_depth_lower)
    m_selection_depth.addAction(editor.act_selection_depth_visible)

    # Map Menu (Legacy Parity)
    m_map = mb.addMenu("Map")
    if hasattr(editor, "act_map_properties"):
        m_map.addAction(editor.act_map_properties)
        m_map.addSeparator()

    if hasattr(editor, "act_remove_monsters_selection"):
        m_map.addAction(editor.act_remove_monsters_selection)
    if hasattr(editor, "act_convert_map_format"):
        m_map.addAction(editor.act_convert_map_format)

    m_view = mb.addMenu("View")
    m_view.addAction(editor.act_zoom_in)
    m_view.addAction(editor.act_zoom_out)
    m_view.addAction(editor.act_zoom_normal)
    m_view.addSeparator()
    m_view.addAction(editor.act_show_grid)
    if hasattr(editor, "act_ingame_preview"):
        m_view.addAction(editor.act_ingame_preview)

    m_mirror = mb.addMenu("Mirror")
    m_mirror.addAction(editor.act_toggle_mirror)

    # Match legacy structure: "Mirror Axis" submenu.
    m_axis = m_mirror.addMenu("Mirror Axis")
    m_axis.addAction(editor.act_mirror_axis_x)
    m_axis.addAction(editor.act_mirror_axis_y)
    m_mirror.addSeparator()
    m_mirror.addAction(editor.act_mirror_axis_set_from_cursor)

    m_assets = mb.addMenu("Assets")
    m_assets.addAction(editor.act_set_assets_dir)
    if hasattr(editor, "act_load_appearances"):
        m_assets.addAction(editor.act_load_appearances)
    if hasattr(editor, "act_unload_appearances"):
        m_assets.addAction(editor.act_unload_appearances)

    m_live = mb.addMenu("Live")
    if hasattr(editor, "act_live_host"):
        m_live.addAction(editor.act_live_host)
    if hasattr(editor, "act_live_stop"):
        m_live.addAction(editor.act_live_stop)
    if hasattr(editor, "act_live_host") or hasattr(editor, "act_live_stop"):
        m_live.addSeparator()
    if hasattr(editor, "act_src_connect"):
        m_live.addAction(editor.act_src_connect)
    if hasattr(editor, "act_src_disconnect"):
        m_live.addAction(editor.act_src_disconnect)
    if hasattr(editor, "act_live_kick") or hasattr(editor, "act_live_ban"):
        m_live.addSeparator()
    if hasattr(editor, "act_live_kick"):
        m_live.addAction(editor.act_live_kick)
    if hasattr(editor, "act_live_ban"):
        m_live.addAction(editor.act_live_ban)

    # Window menu: keep legacy view toggles block + palettes/docks
    m_window = mb.addMenu("Window")

    m_toolbars = m_window.addMenu("Toolbars")
    m_window.addAction(editor.act_new_view)
    if hasattr(editor, "act_new_instance"):
        m_window.addAction(editor.act_new_instance)
    m_window.addAction(editor.act_fullscreen)
    m_window.addAction(editor.act_take_screenshot)
    m_window.addSeparator()

    m_window.addAction(editor.act_zoom_in)
    m_window.addAction(editor.act_zoom_out)
    m_window.addAction(editor.act_zoom_normal)
    m_window.addSeparator()

    m_window.addAction(editor.act_show_shade)
    m_window.addAction(editor.act_show_all_floors)
    m_window.addAction(editor.act_show_loose_items)
    m_window.addAction(editor.act_ghost_higher_floors)
    m_window.addAction(editor.act_show_client_box)

    # Lights submenu (placeholder action can be swapped for a richer group later)
    m_lights = m_window.addMenu("Lights")
    if hasattr(editor, "act_show_lights"):
        m_lights.addAction(editor.act_show_lights)
    else:
        act = QAction("Show lights", editor)
        act.setCheckable(True)
        act.setChecked(bool(getattr(editor, "show_lights", False)))
        act.toggled.connect(lambda v: editor._set_view_flag("show_lights", v))
        editor.act_show_lights = act
        m_lights.addAction(act)

    m_window.addAction(editor.act_show_grid)
    m_window.addAction(editor.act_highlight_items)
    m_window.addSeparator()

    m_window.addAction(editor.act_show_monsters)
    m_window.addAction(editor.act_show_monsters_spawns)
    m_window.addAction(editor.act_show_npcs)
    m_window.addAction(editor.act_show_npcs_spawns)
    m_window.addAction(editor.act_show_special)
    m_window.addAction(editor.act_show_as_minimap)
    m_window.addAction(editor.act_only_show_colors)
    m_window.addAction(editor.act_only_show_modified)
    m_window.addAction(editor.act_clear_modified_state)
    m_window.addSeparator()

    # Appearance
    if hasattr(editor, "act_toggle_dark_mode"):
        m_window.addAction(editor.act_toggle_dark_mode)
        m_window.addSeparator()

    m_window.addAction(editor.act_show_houses)
    m_window.addAction(editor.act_show_pathing)
    m_window.addAction(editor.act_show_tooltips)
    m_window.addAction(editor.act_show_preview)

    # Keep "Show Indicators" as submenu for fine-grained toggles.
    m_ind = m_window.addMenu("Show Indicators")
    m_ind.addAction(editor.act_show_wall_hooks)
    m_ind.addAction(editor.act_show_pickupables)
    m_ind.addAction(editor.act_show_moveables)
    m_ind.addAction(editor.act_show_avoidables)

    m_window.addSeparator()
    m_window.addAction(editor.act_window_minimap)
    m_window.addAction(editor.act_window_actions_history)
    m_window.addAction(editor.act_window_live_log)

    m_window.addSeparator()
    m_window.addAction(editor.act_new_palette)
    m_window.addAction(editor.act_palette_large_icons)
    m_window.addSeparator()
    m_window.addAction(editor.act_palette_terrain)
    m_window.addAction(editor.act_palette_doodad)
    m_window.addAction(editor.act_palette_item)
    m_window.addAction(editor.act_palette_house)
    m_window.addAction(editor.act_palette_creature)
    m_window.addAction(editor.act_palette_npc)
    m_window.addAction(editor.act_palette_waypoint)
    m_window.addAction(editor.act_palette_zones)
    m_window.addAction(editor.act_palette_raw)

    # Toolbars menu gets toggleViewAction() after toolbars are created.
    editor._menu_toolbars = m_toolbars

    # Help Menu
    m_help = mb.addMenu("Help")
    if hasattr(editor, "act_about"):
        m_help.addAction(editor.act_about)
