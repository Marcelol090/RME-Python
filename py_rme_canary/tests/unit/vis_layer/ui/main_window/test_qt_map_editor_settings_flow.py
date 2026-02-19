from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QDialog

from py_rme_canary.vis_layer.ui.main_window import qt_map_editor_modern_ux as modern_module
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file import QtMapEditorFileMixin
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_modern_ux import QtMapEditorModernUXMixin


class _StatusStub:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, msg: str, _timeout: int = 0) -> None:  # noqa: N802
        self.messages.append(str(msg))


class _CanvasStub:
    def __init__(self) -> None:
        self.updates = 0

    def update(self) -> None:
        self.updates += 1


class _ActionStub:
    def __init__(self) -> None:
        self.checked = False

    def setChecked(self, value: bool) -> None:  # noqa: N802
        self.checked = bool(value)


class _SessionStub:
    def __init__(self) -> None:
        self.eraser_leave_unique: bool | None = None

    def set_eraser_leave_unique(self, value: bool) -> None:
        self.eraser_leave_unique = bool(value)


class _FakeSettings:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}

    def __getattr__(self, name: str):
        if name.startswith("set_"):
            key = name.removeprefix("set_")

            def _setter(*args):
                if len(args) == 1:
                    self.values[key] = args[0]
                    return
                if len(args) >= 2:
                    self.values[f"{key}:{args[0]}"] = args[1]
                    return

            return _setter
        raise AttributeError(name)


class _ModernEditorStub(QtMapEditorModernUXMixin):
    def __init__(self) -> None:
        self.status = _StatusStub()
        self.canvas = _CanvasStub()
        self.session = _SessionStub()
        self.act_automagic = _ActionStub()
        self.act_merge_paste = _ActionStub()
        self.act_merge_move = _ActionStub()
        self.act_borderize_paste = _ActionStub()
        self.act_show_grid = _ActionStub()
        self.act_show_tooltips = _ActionStub()
        self.brush_size_set: int | None = None
        self.theme_set: str | None = None
        self.apply_ui_state_calls = 0
        self.switch_mouse_buttons = False
        self.double_click_properties = True
        self.inversed_scroll = False
        self.scroll_speed = 50
        self.zoom_speed = 50

    def _set_brush_size(self, value: int) -> None:
        self.brush_size_set = int(value)

    def _set_editor_theme(self, theme_name: str) -> None:
        self.theme_set = str(theme_name)

    def apply_ui_state_to_session(self) -> None:
        self.apply_ui_state_calls += 1


class _FileEditorStub(QtMapEditorFileMixin):
    def __init__(self, *, fail_modern: bool = False) -> None:
        self._fail_modern = bool(fail_modern)
        self.modern_calls = 0
        self.status = _StatusStub()
        self.updated_prefixes: list[str] = []

    def show_settings_dialog(self) -> None:
        self.modern_calls += 1
        if self._fail_modern:
            raise RuntimeError("modern dialog failed")

    def _update_status_capabilities(self, *, prefix: str) -> None:
        self.updated_prefixes.append(str(prefix))


def test_apply_settings_persists_and_updates_runtime(monkeypatch) -> None:
    fake_settings = _FakeSettings()
    monkeypatch.setattr(modern_module, "get_user_settings", lambda: fake_settings)

    editor = _ModernEditorStub()
    editor._apply_settings(
        {
            "general": {
                "show_welcome_dialog": False,
                "always_make_backup": False,
                "check_updates_on_startup": True,
                "only_one_instance": False,
                "undo_queue_size": 2048,
                "undo_max_memory_mb": 512,
                "worker_threads": 8,
                "copy_position_format": 2,
                "auto_load_appearances": True,
                "enable_tileset_editing": True,
            },
            "editor": {
                "default_brush_size": 5,
                "automagic_default": False,
                "eraser_leave_unique": False,
                "merge_paste": True,
                "merge_move": True,
                "borderize_paste": False,
                "sprite_match_on_paste": True,
            },
            "graphics": {
                "theme_name": "liquid_glass",
                "show_grid_default": False,
                "show_tooltips_default": False,
            },
            "interface": {
                "switch_mouse_buttons": True,
                "double_click_properties": False,
                "inversed_scroll": True,
                "scroll_speed": 33,
                "zoom_speed": 44,
                "palette_terrain_style": 1,
                "palette_collection_style": 2,
            },
            "client_version": {
                "default_client_version": 1330,
                "client_assets_folder": "/tmp/assets",
            },
        }
    )

    assert fake_settings.values["show_welcome_dialog"] is False
    assert fake_settings.values["copy_position_format"] == 2
    assert fake_settings.values["theme_name"] == "liquid_glass"
    assert fake_settings.values["default_client_version"] == 1330
    assert fake_settings.values["client_assets_folder"] == "/tmp/assets"
    assert editor.brush_size_set == 5
    assert editor.theme_set == "liquid_glass"
    assert editor.apply_ui_state_calls == 1
    assert editor.act_automagic.checked is False
    assert editor.act_merge_paste.checked is True
    assert editor.act_merge_move.checked is True
    assert editor.act_borderize_paste.checked is False
    assert editor.act_show_grid.checked is False
    assert editor.act_show_tooltips.checked is False
    assert editor.session.eraser_leave_unique is False
    assert editor.switch_mouse_buttons is True
    assert editor.double_click_properties is False
    assert editor.inversed_scroll is True
    assert editor.scroll_speed == 33
    assert editor.zoom_speed == 44
    assert editor.canvas.updates == 1
    assert editor.status.messages[-1] == "Preferences updated"


def test_goto_position_uses_center_view_on_when_available() -> None:
    editor = _ModernEditorStub()
    captured: list[tuple[int, int, int, bool]] = []

    def _center_view_on(x: int, y: int, z: int, *, push_history: bool = True) -> None:
        captured.append((int(x), int(y), int(z), bool(push_history)))

    editor.center_view_on = _center_view_on  # type: ignore[method-assign]
    editor.goto_position(100, 200, 7)

    assert captured == [(100, 200, 7, True)]


def test_open_preferences_prefers_modern_dialog() -> None:
    editor = _FileEditorStub(fail_modern=False)
    editor._open_preferences()

    assert editor.modern_calls == 1


def test_open_preferences_falls_back_to_legacy_dialog(monkeypatch) -> None:
    from py_rme_canary.vis_layer.ui.main_window import preferences_dialog as prefs_module

    calls = {"exec": 0}

    class _FakePreferencesDialog:
        def __init__(self, _parent) -> None:
            pass

        def exec(self):
            calls["exec"] += 1
            return QDialog.DialogCode.Accepted

    monkeypatch.setattr(prefs_module, "PreferencesDialog", _FakePreferencesDialog)

    editor = _FileEditorStub(fail_modern=True)
    editor._open_preferences()

    assert editor.modern_calls == 1
    assert calls["exec"] == 1
    assert editor.updated_prefixes[-1] == "Preferences updated"
    assert editor.status.messages[-1] == "Preferences updated"
