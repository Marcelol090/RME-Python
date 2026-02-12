from __future__ import annotations

from dataclasses import dataclass

from py_rme_canary.vis_layer.ui.main_window.ui_backend_contract import verify_and_repair_ui_backend_contract


class _Action:
    def __init__(self, checked: bool = False) -> None:
        self._checked = bool(checked)

    def isChecked(self) -> bool:  # noqa: N802
        return bool(self._checked)

    def setChecked(self, value: bool) -> None:  # noqa: N802
        self._checked = bool(value)

    def blockSignals(self, _value: bool) -> None:  # noqa: N802
        return


@dataclass
class _Session:
    brush_size: int = 1
    mode: str = "compensate"

    def get_selection_depth_mode(self) -> str:
        return self.mode


class _Overlay:
    def __init__(self) -> None:
        self.refreshed = False

    def refresh_theme_profile(self) -> None:
        self.refreshed = True


class _Coordinator:
    def __init__(self) -> None:
        self.sync_calls = 0

    def sync_from_editor(self) -> None:
        self.sync_calls += 1


class _Canvas:
    def __init__(self) -> None:
        self.update_calls = 0

    def update(self) -> None:
        self.update_calls += 1


class _BrushToolbar:
    def __init__(self) -> None:
        self._size = 1
        self._shape = "square"
        self._automagic = False

    def set_size(self, size: int) -> None:
        self._size = int(size)

    def set_shape(self, shape: str) -> None:
        self._shape = str(shape)

    def set_automagic(self, enabled: bool) -> None:
        self._automagic = bool(enabled)


class _EditorStub:
    def __init__(self) -> None:
        self.act_automagic = _Action(True)
        self.automagic_cb = _Action(False)
        self.act_selection_depth_compensate = _Action(False)
        self.act_selection_depth_current = _Action(False)
        self.act_selection_depth_lower = _Action(True)
        self.act_selection_depth_visible = _Action(False)
        self.act_theme_noct_green_glass = _Action(False)
        self.act_theme_noct_8bit_glass = _Action(True)
        self.act_theme_noct_liquid_glass = _Action(False)
        self.brush_size = 3
        self.session = _Session(brush_size=1, mode="current")
        self.brush_cursor_overlay = _Overlay()
        self.drawing_options_coordinator = _Coordinator()
        self.canvas = _Canvas()
        self.brush_toolbar = _BrushToolbar()

        self.show_grid = True
        self.act_show_grid = _Action(False)
        self.show_tooltips = True
        self.act_show_tooltips = _Action(True)
        self.show_as_minimap = False
        self.act_show_as_minimap = _Action(False)
        self.show_preview = False
        self.act_show_preview = _Action(True)
        self.show_wall_hooks = True
        self.act_show_wall_hooks = _Action(False)
        self.act_tb_hooks = _Action(False)
        self.show_pickupables = False
        self.act_show_pickupables = _Action(False)
        self.act_tb_pickupables = _Action(True)
        self.show_moveables = False
        self.act_show_moveables = _Action(False)
        self.act_tb_moveables = _Action(False)
        self.show_avoidables = False
        self.act_show_avoidables = _Action(False)
        self.act_tb_avoidables = _Action(False)

        self.apply_calls = 0

    def apply_ui_state_to_session(self) -> None:
        self.apply_calls += 1


def test_ui_backend_contract_repairs_automagic_and_brush_size() -> None:
    editor = _EditorStub()
    repairs, sig = verify_and_repair_ui_backend_contract(editor, last_signature=0)

    assert sig > 0
    assert "automagic_sync" in repairs
    assert "brush_size_sync" in repairs
    assert editor.automagic_cb.isChecked() is True
    assert editor.session.brush_size == 3
    assert editor.apply_calls == 1


def test_ui_backend_contract_syncs_selection_mode_actions() -> None:
    editor = _EditorStub()
    editor.session.mode = "visible"
    repairs, _ = verify_and_repair_ui_backend_contract(editor, last_signature=0)

    assert isinstance(repairs, list)
    assert editor.act_selection_depth_visible.isChecked() is True
    assert editor.act_selection_depth_current.isChecked() is False
    assert editor.act_selection_depth_compensate.isChecked() is False


def test_ui_backend_contract_uses_signature_short_circuit() -> None:
    editor = _EditorStub()
    _, sig = verify_and_repair_ui_backend_contract(editor, last_signature=0)
    repairs2, sig2 = verify_and_repair_ui_backend_contract(editor, last_signature=sig)

    assert repairs2 == []
    assert sig2 == sig


def test_ui_backend_contract_syncs_extended_view_flags_and_refreshes_rendering() -> None:
    editor = _EditorStub()
    repairs, _ = verify_and_repair_ui_backend_contract(editor, last_signature=0)

    assert "show_grid_sync" in repairs
    assert "show_preview_sync" in repairs
    assert "show_wall_hooks_sync" in repairs
    assert repairs == sorted(repairs)
    assert len(repairs) == len(set(repairs))
    assert editor.act_show_grid.isChecked() is True
    assert editor.act_show_preview.isChecked() is False
    assert editor.act_show_wall_hooks.isChecked() is True
    assert editor.drawing_options_coordinator.sync_calls == 1
    assert editor.canvas.update_calls == 1


def test_ui_backend_contract_syncs_toolbar_menu_mirrors() -> None:
    editor = _EditorStub()
    editor.show_wall_hooks = True
    editor.act_show_wall_hooks.setChecked(True)
    editor.act_tb_hooks.setChecked(False)
    editor.show_pickupables = False
    editor.act_show_pickupables.setChecked(False)
    editor.act_tb_pickupables.setChecked(True)

    repairs, _ = verify_and_repair_ui_backend_contract(editor, last_signature=0)

    assert "act_tb_hooks_mirror_sync" in repairs
    assert "act_tb_pickupables_mirror_sync" in repairs
    assert editor.act_tb_hooks.isChecked() is True
    assert editor.act_tb_pickupables.isChecked() is False


def test_ui_backend_contract_syncs_brush_toolbar_with_backend_state() -> None:
    editor = _EditorStub()
    editor.brush_size = 7
    editor.brush_shape = "circle"
    editor.act_automagic.setChecked(True)
    editor.brush_toolbar._size = 1
    editor.brush_toolbar._shape = "square"
    editor.brush_toolbar._automagic = False

    repairs, _ = verify_and_repair_ui_backend_contract(editor, last_signature=0)

    assert "brush_toolbar_size_sync" in repairs
    assert "brush_toolbar_shape_sync" in repairs
    assert "brush_toolbar_automagic_sync" in repairs
    assert editor.brush_toolbar._size == 7
    assert editor.brush_toolbar._shape == "circle"
    assert editor.brush_toolbar._automagic is True
