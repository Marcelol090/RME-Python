from __future__ import annotations

from typing import TYPE_CHECKING

from py_rme_canary.vis_layer.ui.resources.icon_pack import load_icon

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


def build_menus_and_toolbars(editor: QtMapEditor) -> None:
    mb = editor.menuBar()

    m_file = mb.addMenu(load_icon("menu_file"), "File")
    editor.menu_file = m_file
    m_file.addAction(editor.act_new)
    m_file.addAction(editor.act_open)
    m_file.addAction(editor.act_save)
    m_file.addAction(editor.act_save_as)
    if hasattr(editor, "act_generate_map"):
        m_file.addAction(editor.act_generate_map)
    if hasattr(editor, "act_close_map"):
        m_file.addAction(editor.act_close_map)
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
    if any(hasattr(editor, act) for act in ("act_export_png", "act_export_otmm", "act_export_tilesets", "act_export_minimap")):
        m_export = m_file.addMenu("Export")
        if hasattr(editor, "act_export_minimap"):
            m_export.addAction(editor.act_export_minimap)
        if hasattr(editor, "act_export_png"):
            m_export.addAction(editor.act_export_png)
        if hasattr(editor, "act_export_otmm"):
            m_export.addAction(editor.act_export_otmm)
        if hasattr(editor, "act_export_tilesets"):
            m_export.addAction(editor.act_export_tilesets)
        m_file.addSeparator()

    if hasattr(editor, "act_reload_data"):
        m_reload = m_file.addMenu("Reload")
        m_reload.addAction(editor.act_reload_data)
        m_file.addSeparator()

    if hasattr(editor, "act_preferences"):
        m_file.addAction(editor.act_preferences)

    m_file.addAction(editor.act_exit)

    m_edit = mb.addMenu(load_icon("menu_edit"), "Edit")
    editor.menu_edit = m_edit
    m_edit.addAction(editor.act_undo)
    m_edit.addAction(editor.act_redo)
    m_edit.addSeparator()

    # Replace Items (C++ Edit > Replace Items... Ctrl+Shift+F)
    m_edit.addAction(editor.act_replace_items)
    m_edit.addSeparator()

    # Border Options submenu (C++ Edit > Border Options)
    m_border = m_edit.addMenu("Border Options")
    m_border.addAction(editor.act_automagic)
    m_border.addSeparator()
    m_border.addAction(editor.act_borderize_selection)
    if hasattr(editor, "act_borderize_map"):
        m_border.addAction(editor.act_borderize_map)
    if hasattr(editor, "act_randomize_selection"):
        m_border.addAction(editor.act_randomize_selection)
    if hasattr(editor, "act_randomize_map_full"):
        m_border.addAction(editor.act_randomize_map_full)
    if hasattr(editor, "act_border_builder"):
        m_border.addSeparator()
        m_border.addAction(editor.act_border_builder)

    # Other Options submenu (C++ Edit > Other Options)
    m_other = m_edit.addMenu("Other Options")
    m_other.addAction(editor.act_remove_item_map)
    m_other.addAction(editor.act_remove_corpses_map)
    m_other.addAction(editor.act_remove_unreachable_map)
    m_other.addAction(editor.act_clear_invalid_house_tiles_map)
    m_other.addAction(editor.act_clear_modified_state)

    m_edit.addSeparator()
    m_edit.addAction(editor.act_cut)
    m_edit.addAction(editor.act_copy)
    m_edit.addAction(editor.act_paste)
    m_edit.addSeparator()
    if hasattr(editor, "act_global_search"):
        m_edit.addAction(editor.act_global_search)
    m_edit.addAction(editor.act_command_palette)

    # ---- Editor Menu (C++ separate "Editor" menu) ----
    m_editor = mb.addMenu("Editor")
    m_editor.addAction(editor.act_new_view)
    m_editor.addAction(editor.act_fullscreen)
    m_editor.addAction(editor.act_take_screenshot)
    m_editor.addSeparator()
    m_zoom_ed = m_editor.addMenu("Zoom")
    m_zoom_ed.addAction(editor.act_zoom_in)
    m_zoom_ed.addAction(editor.act_zoom_out)
    m_zoom_ed.addAction(editor.act_zoom_normal)

    # ---- Search Menu (C++ Search) ----
    m_search = mb.addMenu(load_icon("menu_search"), "Search")
    editor.menu_search = m_search
    m_search.addAction(editor.act_find_item)
    m_search.addSeparator()
    if hasattr(editor, "act_find_unique_map"):
        m_search.addAction(editor.act_find_unique_map)
    if hasattr(editor, "act_find_action_map"):
        m_search.addAction(editor.act_find_action_map)
    if hasattr(editor, "act_find_container_map"):
        m_search.addAction(editor.act_find_container_map)
    if hasattr(editor, "act_find_writeable_map"):
        m_search.addAction(editor.act_find_writeable_map)
    m_search.addSeparator()
    m_search.addAction(editor.act_find_everything_map)

    # ---- Map Menu (C++ Map) ----
    m_map = mb.addMenu(load_icon("menu_map"), "Map")
    m_map.addAction(editor.act_edit_towns)
    m_map.addSeparator()
    m_map.addAction(editor.act_map_cleanup)
    m_map.addAction(editor.act_map_properties)
    m_map.addAction(editor.act_map_statistics_legacy)

    # ---- Selection Menu (C++ Selection) ----
    m_selection = mb.addMenu("Selection")
    editor.menu_selection = m_selection
    m_selection.addAction(editor.act_replace_items_on_selection)
    m_selection.addAction(editor.act_find_item_selection)
    m_selection.addAction(editor.act_remove_item_on_selection)
    m_selection.addSeparator()

    # Find on Selection submenu (C++ Selection > Find on Selection)
    m_find_sel = m_selection.addMenu("Find on Selection")
    m_find_sel.addAction(editor.act_find_everything_selection)
    m_find_sel.addSeparator()
    m_find_sel.addAction(editor.act_find_unique_selection)
    m_find_sel.addAction(editor.act_find_action_selection)
    m_find_sel.addAction(editor.act_find_container_selection)
    m_find_sel.addAction(editor.act_find_writeable_selection)

    m_selection.addSeparator()
    # Selection Mode submenu (C++ Selection > Selection Mode)
    m_sel_mode = m_selection.addMenu("Selection Mode")
    m_sel_mode.addAction(editor.act_selection_depth_compensate)
    m_sel_mode.addSeparator()
    m_sel_mode.addAction(editor.act_selection_depth_current)
    m_sel_mode.addAction(editor.act_selection_depth_lower)
    m_sel_mode.addAction(editor.act_selection_depth_visible)

    m_selection.addSeparator()
    m_selection.addAction(editor.act_borderize_selection)
    if hasattr(editor, "act_randomize_selection"):
        m_selection.addAction(editor.act_randomize_selection)

    # ---- View Menu (C++ View) ----
    m_view = mb.addMenu(load_icon("menu_view"), "View")
    # C++ "View" menu: view options
    m_view.addAction(editor.act_show_all_floors)
    m_view.addAction(editor.act_show_as_minimap)
    m_view.addAction(editor.act_only_show_colors)
    m_view.addAction(editor.act_only_show_modified)
    if hasattr(editor, "act_always_show_zones"):
        m_view.addAction(editor.act_always_show_zones)
    if hasattr(editor, "act_ext_house_shader"):
        m_view.addAction(editor.act_ext_house_shader)
    m_view.addSeparator()
    m_view.addAction(editor.act_show_tooltips)
    m_view.addAction(editor.act_show_grid)
    m_view.addAction(editor.act_show_client_box)
    m_view.addSeparator()
    m_view.addAction(editor.act_show_loose_items)
    m_view.addAction(editor.act_ghost_higher_floors)
    m_view.addAction(editor.act_show_shade)
    if hasattr(editor, "act_show_client_ids"):
        m_view.addSeparator()
        m_view.addAction(editor.act_show_client_ids)
    if hasattr(editor, "act_ingame_preview"):
        m_view.addAction(editor.act_ingame_preview)

    # C++ "Show" menu: item/zone filters (merged into a submenu)
    m_show = mb.addMenu("Show")
    m_show.addAction(editor.act_show_preview)
    if hasattr(editor, "act_show_lights"):
        m_show.addAction(editor.act_show_lights)
    if hasattr(editor, "act_show_light_strength"):
        m_show.addAction(editor.act_show_light_strength)
    if hasattr(editor, "act_show_technical_items"):
        m_show.addAction(editor.act_show_technical_items)
    m_show.addSeparator()
    m_show.addAction(editor.act_show_monsters)
    m_show.addAction(editor.act_show_monsters_spawns)
    m_show.addAction(editor.act_show_npcs)
    m_show.addAction(editor.act_show_npcs_spawns)
    m_show.addAction(editor.act_show_special)
    m_show.addAction(editor.act_show_houses)
    m_show.addAction(editor.act_show_pathing)
    if hasattr(editor, "act_show_towns"):
        m_show.addAction(editor.act_show_towns)
    if hasattr(editor, "act_show_waypoints"):
        m_show.addAction(editor.act_show_waypoints)
    m_show.addSeparator()
    m_show.addAction(editor.act_highlight_items)
    if hasattr(editor, "act_highlight_locked_doors"):
        m_show.addAction(editor.act_highlight_locked_doors)
    m_show.addAction(editor.act_show_wall_hooks)

    # C++ "Navigate" menu
    m_navigate = mb.addMenu("Navigate")
    m_navigate.addAction(editor.act_goto_previous_position)
    m_navigate.addAction(editor.act_goto_position)
    if hasattr(editor, "act_jump_to_brush"):
        m_navigate.addAction(editor.act_jump_to_brush)
    if hasattr(editor, "act_jump_to_item"):
        m_navigate.addAction(editor.act_jump_to_item)
    m_navigate.addSeparator()
    # Floor submenu (0-15)
    m_floor = m_navigate.addMenu("Floor")
    if hasattr(editor, "act_floor_actions"):
        for act in editor.act_floor_actions:
            m_floor.addAction(act)

    # ---- Window Menu (C++ Window) ----
    m_window = mb.addMenu(load_icon("menu_window"), "Window")
    m_window.addAction(editor.act_window_minimap)
    if hasattr(editor, "act_window_tool_options"):
        m_window.addAction(editor.act_window_tool_options)
    if hasattr(editor, "act_ingame_preview"):
        m_window.addAction(editor.act_ingame_preview)
    m_window.addAction(editor.act_new_palette)

    # Palette submenu (C++ Window > Palette)
    m_palette = m_window.addMenu("Palette")
    m_palette.addAction(editor.act_palette_terrain)
    m_palette.addAction(editor.act_palette_doodad)
    m_palette.addAction(editor.act_palette_item)
    m_palette.addAction(editor.act_palette_collection)
    m_palette.addAction(editor.act_palette_house)
    m_palette.addAction(editor.act_palette_creature)
    m_palette.addAction(editor.act_palette_npc)
    m_palette.addAction(editor.act_palette_waypoint)
    m_palette.addAction(editor.act_palette_zones)
    m_palette.addAction(editor.act_palette_raw)

    # Toolbars submenu (C++ Window > Toolbars)
    m_toolbars = m_window.addMenu("Toolbars")
    # toggleViewAction()s added after toolbars are created
    editor._menu_toolbars = m_toolbars

    # Extra Window items (PyRME extensions beyond C++)
    m_window.addSeparator()
    m_window.addAction(editor.act_window_actions_history)
    m_window.addAction(editor.act_window_live_log)
    if hasattr(editor, "act_window_friends"):
        m_window.addAction(editor.act_window_friends)
    m_window.addSeparator()
    m_window.addAction(editor.act_palette_large_icons)
    if hasattr(editor, "act_toggle_dark_mode"):
        m_window.addAction(editor.act_toggle_dark_mode)

    # ---- Mirror Menu (PyRME extension) ----
    m_mirror = mb.addMenu(load_icon("menu_mirror"), "Mirror")
    m_mirror.addAction(editor.act_toggle_mirror)
    m_axis = m_mirror.addMenu("Mirror Axis")
    m_axis.addAction(editor.act_mirror_axis_x)
    m_axis.addAction(editor.act_mirror_axis_y)
    m_mirror.addSeparator()
    m_mirror.addAction(editor.act_mirror_axis_set_from_cursor)

    # ---- Assets Menu (PyRME extension) ----
    m_assets = mb.addMenu(load_icon("menu_assets"), "Assets")
    if hasattr(editor, "act_manage_client_profiles"):
        m_assets.addAction(editor.act_manage_client_profiles)
        m_assets.addSeparator()
    if hasattr(editor, "act_load_client_data_stack"):
        m_assets.addAction(editor.act_load_client_data_stack)
    m_assets.addAction(editor.act_set_assets_dir)
    if hasattr(editor, "act_load_appearances"):
        m_assets.addAction(editor.act_load_appearances)
    if hasattr(editor, "act_unload_appearances"):
        m_assets.addAction(editor.act_unload_appearances)

    # ---- Live Menu (PyRME extension) ----
    m_live = mb.addMenu(load_icon("menu_live"), "Live")
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

    # ---- Experimental Menu (C++ parity) ----
    m_experimental = mb.addMenu("Experimental")
    if hasattr(editor, "act_experimental_fog"):
        m_experimental.addAction(editor.act_experimental_fog)

    # ---- Help / About Menu (C++ About) ----
    m_help = mb.addMenu(load_icon("menu_help"), "Help")
    editor.menu_help = m_help
    if hasattr(editor, "act_extensions"):
        m_help.addAction(editor.act_extensions)
    if hasattr(editor, "act_goto_website"):
        m_help.addAction(editor.act_goto_website)
    if hasattr(editor, "act_extensions") or hasattr(editor, "act_goto_website"):
        m_help.addSeparator()
    if hasattr(editor, "act_about"):
        m_help.addAction(editor.act_about)
