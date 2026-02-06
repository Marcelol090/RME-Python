import pytest

pytest.importorskip("PyQt6.QtWidgets")

from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


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
