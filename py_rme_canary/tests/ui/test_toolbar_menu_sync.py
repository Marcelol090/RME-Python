import pytest

pytest.importorskip("PyQt6.QtWidgets")

from py_rme_canary.logic_layer.session.selection_modes import SelectionDepthMode
from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor  # noqa: E402


@pytest.fixture
def editor(qapp, qtbot):
    window = QtMapEditor()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitForWindowShown(window)
    return window


def test_primary_actions_have_custom_icons(editor):
    action_names = (
        "act_new",
        "act_open",
        "act_save",
        "act_save_as",
        "act_undo",
        "act_redo",
        "act_cut",
        "act_copy",
        "act_paste",
        "act_delete_selection",
        "act_fill",
        "act_selection_mode",
    )
    for action_name in action_names:
        action = getattr(editor, action_name)
        assert not action.icon().isNull(), f"Expected icon for {action_name}"


def test_modern_menu_bindings_are_exposed(editor):
    assert hasattr(editor, "menu_file")
    assert hasattr(editor, "menu_edit")
    assert hasattr(editor, "menu_help")

    file_action_texts = {action.text() for action in editor.menu_file.actions() if action.text()}
    edit_action_texts = {action.text() for action in editor.menu_edit.actions() if action.text()}

    assert "Settings..." in file_action_texts
    assert "Global Search..." in edit_action_texts
    assert "Command Palette..." in edit_action_texts
    assert editor.act_command_palette.shortcut().toString() == "Ctrl+K"


def test_assets_menu_exposes_client_data_loader(editor):
    menubar_actions = editor.menuBar().actions()
    assets_menu = next((action.menu() for action in menubar_actions if action.text() == "Assets"), None)
    assert assets_menu is not None
    assets_action_texts = {action.text() for action in assets_menu.actions() if action.text()}
    assert "Load Client Data..." in assets_action_texts


def test_window_menu_exposes_tool_options(editor):
    menubar_actions = editor.menuBar().actions()
    window_menu = next((action.menu() for action in menubar_actions if action.text() == "Window"), None)
    assert window_menu is not None
    window_action_texts = {action.text() for action in window_menu.actions() if action.text()}
    assert "Tool Options" in window_action_texts


def test_window_menu_exposes_brush_submenus(editor):
    menubar_actions = editor.menuBar().actions()
    window_menu = next((action.menu() for action in menubar_actions if action.text() == "Window"), None)
    assert window_menu is not None
    brush_menu = next((action.menu() for action in window_menu.actions() if action.text() == "Brush"), None)
    assert brush_menu is not None
    brush_action_texts = {action.text() for action in brush_menu.actions() if action.text()}
    assert "Size" in brush_action_texts
    assert "Shape" in brush_action_texts


def test_tool_options_action_shows_palette_dock(editor, qtbot):
    editor.dock_palette.hide()
    qtbot.wait(5)
    assert editor.dock_palette.isVisible() is False

    editor.act_window_tool_options.trigger()
    qtbot.wait(10)
    assert editor.dock_palette.isVisible() is True


def test_view_menu_exposes_show_client_ids(editor):
    menubar_actions = editor.menuBar().actions()
    view_menu = next((action.menu() for action in menubar_actions if action.text() == "View"), None)
    assert view_menu is not None
    view_action_texts = {action.text() for action in view_menu.actions() if action.text()}
    assert "Show Client IDs" in view_action_texts


def test_legacy_view_show_labels_are_aligned(editor):
    assert editor.act_show_all_floors.text() == "Show all Floors"
    assert editor.act_show_as_minimap.text() == "Show as Minimap"
    assert editor.act_only_show_colors.text() == "Only show Colors"
    assert editor.act_only_show_modified.text() == "Only show Modified"
    assert editor.act_show_grid.text() == "Show grid"
    assert editor.act_show_tooltips.text() == "Show tooltips"
    assert editor.act_show_light_strength.text() == "Show Light Strength"
    assert editor.act_show_technical_items.text() == "Show Technical Items"
    assert editor.act_show_monsters.text() == "Show creatures"
    assert editor.act_show_monsters_spawns.text() == "Show spawns"
    assert editor.act_highlight_items.text() == "Highlight Items"
    assert editor.act_highlight_locked_doors.text() == "Highlight Locked Doors"
    assert editor.act_show_wall_hooks.text() == "Show Wall Hooks"


def test_show_client_ids_action_updates_editor_flag(editor, qtbot):
    editor.act_show_client_ids.setChecked(True)
    qtbot.wait(5)
    assert editor.show_client_ids is True
    editor.act_show_client_ids.setChecked(False)
    qtbot.wait(5)
    assert editor.show_client_ids is False


def test_indicator_actions_are_bidirectionally_synced(editor, qtbot):
    editor.act_show_wall_hooks.setChecked(False)
    qtbot.wait(5)
    assert editor.act_tb_hooks.isChecked() is False

    editor.act_tb_hooks.setChecked(True)
    qtbot.wait(5)
    assert editor.act_show_wall_hooks.isChecked() is True


def test_toolbar_visibility_actions_follow_toolbar_state(editor, qtbot):
    editor.act_view_toolbar_brushes.setChecked(False)
    qtbot.wait(5)
    assert editor.tb_brushes.isVisible() is False

    editor.tb_brushes.setVisible(True)
    qtbot.wait(5)
    assert editor.act_view_toolbar_brushes.isChecked() is True


def test_automagic_action_and_checkbox_stay_synced(editor, qtbot):
    editor.act_automagic.setChecked(False)
    qtbot.wait(5)
    assert editor.automagic_cb.isChecked() is False

    editor.automagic_cb.setChecked(True)
    qtbot.wait(5)
    assert editor.act_automagic.isChecked() is True


def test_palette_menu_actions_target_modern_palette_dock(editor, qtbot):
    editor.act_palette_item.trigger()
    qtbot.wait(10)
    assert editor.palettes.current_palette_name == "item"
    assert editor.brush_filter is editor.dock_palette.brush_filter
    assert editor.brush_list is editor.dock_palette.brush_list


def test_palette_collection_action_targets_modern_palette_dock(editor, qtbot):
    editor.act_palette_collection.trigger()
    qtbot.wait(10)
    assert editor.palettes.current_palette_name == "collection"


def test_palette_actions_are_exclusive_and_follow_selected_palette(editor, qtbot):
    assert editor.act_palette_item.isCheckable() is True
    assert editor.act_palette_terrain.isCheckable() is True

    editor.act_palette_item.trigger()
    qtbot.wait(10)
    assert editor.palettes.current_palette_name == "item"
    assert editor.act_palette_item.isChecked() is True
    assert editor.act_palette_terrain.isChecked() is False

    editor.act_palette_terrain.trigger()
    qtbot.wait(10)
    assert editor.palettes.current_palette_name == "terrain"
    assert editor.act_palette_terrain.isChecked() is True
    assert editor.act_palette_item.isChecked() is False


def test_selection_depth_actions_are_exclusive_and_follow_mode(editor, qtbot):
    editor.act_selection_depth_current.trigger()
    qtbot.wait(10)
    assert editor.session.get_selection_depth_mode() == SelectionDepthMode.CURRENT
    assert editor.act_selection_depth_current.isChecked() is True
    assert editor.act_selection_depth_compensate.isChecked() is False

    editor._set_selection_depth_mode(SelectionDepthMode.VISIBLE)
    qtbot.wait(10)
    assert editor.act_selection_depth_visible.isChecked() is True
    assert editor.act_selection_depth_current.isChecked() is False


def test_brush_menu_actions_sync_with_editor_state(editor, qtbot):
    size_act = next((act for act in editor.act_brush_size_actions if int(act.data()) == 5), None)
    assert size_act is not None

    size_act.trigger()
    qtbot.wait(10)
    assert int(editor.brush_size) == 5
    assert size_act.isChecked() is True

    editor._set_brush_size(3)
    qtbot.wait(10)
    size3 = next(act for act in editor.act_brush_size_actions if int(act.data()) == 3)
    assert size3.isChecked() is True
    assert size_act.isChecked() is False

    editor.act_brush_shape_circle.trigger()
    qtbot.wait(10)
    assert editor.brush_shape == "circle"
    assert editor.act_brush_shape_circle.isChecked() is True
    assert editor.act_brush_shape_square.isChecked() is False

    editor._set_brush_shape("square")
    qtbot.wait(10)
    assert editor.act_brush_shape_square.isChecked() is True
    assert editor.act_brush_shape_circle.isChecked() is False
