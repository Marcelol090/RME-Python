from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any

from py_rme_canary.logic_layer.rust_accel import fnv1a_64

VIEW_FLAG_ACTION_PAIRS: tuple[tuple[str, str], ...] = (
    ("show_grid", "act_show_grid"),
    ("show_tooltips", "act_show_tooltips"),
    ("show_as_minimap", "act_show_as_minimap"),
    ("show_shade", "act_show_shade"),
    ("show_all_floors", "act_show_all_floors"),
    ("show_loose_items", "act_show_loose_items"),
    ("ghost_higher_floors", "act_ghost_higher_floors"),
    ("show_client_box", "act_show_client_box"),
    ("show_client_ids", "act_show_client_ids"),
    ("show_lights", "act_show_lights"),
    ("highlight_items", "act_highlight_items"),
    ("show_monsters", "act_show_monsters"),
    ("show_monsters_spawns", "act_show_monsters_spawns"),
    ("show_npcs", "act_show_npcs"),
    ("show_npcs_spawns", "act_show_npcs_spawns"),
    ("show_special", "act_show_special"),
    ("only_show_colors", "act_only_show_colors"),
    ("only_show_modified", "act_only_show_modified"),
    ("show_houses_overlay", "act_show_houses"),
    ("show_pathing", "act_show_pathing"),
    ("show_preview", "act_show_preview"),
    ("show_indicators", "act_show_indicators_simple"),
    ("show_wall_hooks", "act_show_wall_hooks"),
    ("show_pickupables", "act_show_pickupables"),
    ("show_moveables", "act_show_moveables"),
    ("show_avoidables", "act_show_avoidables"),
)

MIRRORED_ACTION_PAIRS: tuple[tuple[str, str], ...] = (
    ("act_tb_hooks", "act_show_wall_hooks"),
    ("act_tb_pickupables", "act_show_pickupables"),
    ("act_tb_moveables", "act_show_moveables"),
    ("act_tb_avoidables", "act_show_avoidables"),
)


def _action_checked(obj: object | None) -> bool:
    if obj is None:
        return False
    try:
        fn = getattr(obj, "isChecked", None)
        return bool(fn()) if callable(fn) else False
    except Exception:
        return False


def _set_action_checked(obj: object | None, value: bool) -> None:
    if obj is None:
        return
    with contextlib.suppress(Exception):
        block = getattr(obj, "blockSignals", None)
        if callable(block):
            block(True)
        setter = getattr(obj, "setChecked", None)
        if callable(setter):
            setter(bool(value))
        if callable(block):
            block(False)


def _action_enabled(obj: object | None) -> bool:
    if obj is None:
        return False
    try:
        fn = getattr(obj, "isEnabled", None)
        return bool(fn()) if callable(fn) else False
    except Exception:
        return False


def _set_action_enabled(obj: object | None, value: bool) -> None:
    if obj is None:
        return
    with contextlib.suppress(Exception):
        block = getattr(obj, "blockSignals", None)
        if callable(block):
            block(True)
        setter = getattr(obj, "setEnabled", None)
        if callable(setter):
            setter(bool(value))
        if callable(block):
            block(False)


def _call0(fn: Callable[[], Any] | None, default: Any = None) -> Any:
    if fn is None:
        return default
    try:
        return fn()
    except Exception:
        return default


def _snapshot_string(editor: object) -> str:
    parts: list[str] = []

    # Automagic
    parts.append(f"aa:{int(_action_checked(getattr(editor, 'act_automagic', None)))}")
    parts.append(f"ac:{int(_action_checked(getattr(editor, 'automagic_cb', None)))}")

    # Selection depth state
    session = getattr(editor, "session", None)
    mode = None
    if session is not None:
        mode = _call0(getattr(session, "get_selection_depth_mode", None), None)
    parts.append(f"sdm:{str(mode)}")
    for action_name in (
        "act_selection_depth_compensate",
        "act_selection_depth_current",
        "act_selection_depth_lower",
        "act_selection_depth_visible",
    ):
        parts.append(f"{action_name}:{int(_action_checked(getattr(editor, action_name, None)))}")

    # Theme state
    try:
        from py_rme_canary.vis_layer.ui.theme import get_theme_manager

        theme_name = str(get_theme_manager().current_theme)
    except Exception:
        theme_name = ""
    parts.append(f"theme:{theme_name}")
    for action_name in (
        "act_theme_noct_green_glass",
        "act_theme_noct_8bit_glass",
        "act_theme_noct_liquid_glass",
    ):
        parts.append(f"{action_name}:{int(_action_checked(getattr(editor, action_name, None)))}")

    # Brush / session state
    brush_size = int(getattr(editor, "brush_size", 0) or 0)
    parts.append(f"bs:{brush_size}")
    session_brush = int(getattr(session, "brush_size", 0) or 0) if session is not None else 0
    parts.append(f"sbs:{session_brush}")
    parts.append(f"bsh:{str(getattr(editor, 'brush_shape', 'square') or 'square')}")
    brush_toolbar = getattr(editor, "brush_toolbar", None)
    parts.append(f"tbs:{int(getattr(brush_toolbar, '_size', 0) or 0)}")
    parts.append(f"tsh:{str(getattr(brush_toolbar, '_shape', ''))}")
    parts.append(f"ta:{int(bool(getattr(brush_toolbar, '_automagic', False)))}")
    parts.append(f"absd:{int(_action_enabled(getattr(editor, 'act_brush_size_decrease', None)))}")
    parts.append(f"absi:{int(_action_enabled(getattr(editor, 'act_brush_size_increase', None)))}")
    parts.append(f"abss:{int(_action_checked(getattr(editor, 'act_brush_shape_square', None)))}")
    parts.append(f"absc:{int(_action_checked(getattr(editor, 'act_brush_shape_circle', None)))}")
    parts.append(f"sm:{int(bool(getattr(editor, 'selection_mode', False)))}")
    parts.append(f"asm:{int(_action_checked(getattr(editor, 'act_selection_mode', None)))}")

    # View flags <-> actions
    for flag_name, action_name in VIEW_FLAG_ACTION_PAIRS:
        parts.append(f"f:{flag_name}:{int(bool(getattr(editor, flag_name, False)))}")
        parts.append(f"a:{action_name}:{int(_action_checked(getattr(editor, action_name, None)))}")
    for action_name, mirror_name in MIRRORED_ACTION_PAIRS:
        parts.append(f"m:{action_name}:{int(_action_checked(getattr(editor, action_name, None)))}")
        parts.append(f"m:{mirror_name}:{int(_action_checked(getattr(editor, mirror_name, None)))}")

    return "|".join(parts)


def verify_and_repair_ui_backend_contract(editor: object, *, last_signature: int) -> tuple[list[str], int]:
    snapshot = _snapshot_string(editor)
    signature = fnv1a_64(snapshot.encode("utf-8"))
    if int(signature) == int(last_signature):
        return [], int(signature)

    repairs: list[str] = []

    # 1) Automagic action <-> checkbox
    act_automagic = getattr(editor, "act_automagic", None)
    automagic_cb = getattr(editor, "automagic_cb", None)
    if act_automagic is not None and automagic_cb is not None:
        action_state = _action_checked(act_automagic)
        cb_state = _action_checked(automagic_cb)
        if action_state != cb_state:
            _set_action_checked(automagic_cb, action_state)
            apply_ui = getattr(editor, "apply_ui_state_to_session", None)
            _call0(apply_ui)
            repairs.append("automagic_sync")

    # 2) Selection depth actions must reflect backend mode
    session = getattr(editor, "session", None)
    mode = _call0(getattr(session, "get_selection_depth_mode", None), None) if session is not None else None
    mode_action = {
        "compensate": "act_selection_depth_compensate",
        "current": "act_selection_depth_current",
        "lower": "act_selection_depth_lower",
        "visible": "act_selection_depth_visible",
    }
    selected_name = mode_action.get(str(mode), "act_selection_depth_compensate")
    for action_name in mode_action.values():
        _set_action_checked(getattr(editor, action_name, None), action_name == selected_name)

    # 3) Theme actions must reflect ThemeManager.current_theme
    try:
        from py_rme_canary.vis_layer.ui.theme import get_theme_manager

        current_theme = str(get_theme_manager().current_theme)
    except Exception:
        current_theme = ""
    theme_actions = (
        ("act_theme_noct_green_glass", "noct_green_glass"),
        ("act_theme_noct_8bit_glass", "noct_8bit_glass"),
        ("act_theme_noct_liquid_glass", "noct_liquid_glass"),
    )
    for action_name, theme_name in theme_actions:
        _set_action_checked(getattr(editor, action_name, None), bool(current_theme == theme_name))

    # 4) Brush size must stay consistent with session
    brush_size = int(getattr(editor, "brush_size", 0) or 0)
    if session is not None:
        session_brush = int(getattr(session, "brush_size", 0) or 0)
        if brush_size > 0 and session_brush != brush_size:
            with contextlib.suppress(Exception):
                session.brush_size = int(brush_size)
            repairs.append("brush_size_sync")

    # 4b) Brush toolbar must mirror canonical editor/action state
    brush_toolbar = getattr(editor, "brush_toolbar", None)
    if brush_toolbar is not None:
        toolbar_size = int(getattr(brush_toolbar, "_size", 0) or 0)
        if brush_size > 0 and toolbar_size != brush_size:
            with contextlib.suppress(Exception):
                brush_toolbar.set_size(int(brush_size))
            repairs.append("brush_toolbar_size_sync")

        shape = str(getattr(editor, "brush_shape", "square") or "square")
        toolbar_shape = str(getattr(brush_toolbar, "_shape", "") or "")
        if toolbar_shape != shape:
            with contextlib.suppress(Exception):
                brush_toolbar.set_shape(shape)
            repairs.append("brush_toolbar_shape_sync")

        act_automagic = getattr(editor, "act_automagic", None)
        action_state = _action_checked(act_automagic)
        toolbar_automagic = bool(getattr(brush_toolbar, "_automagic", False))
        if toolbar_automagic != action_state:
            with contextlib.suppress(Exception):
                brush_toolbar.set_automagic(bool(action_state))
            repairs.append("brush_toolbar_automagic_sync")

    # 4c) Brush actions must reflect canonical brush state
    shape = str(getattr(editor, "brush_shape", "square") or "square")
    if shape not in ("square", "circle"):
        shape = "square"
    square_action = getattr(editor, "act_brush_shape_square", None)
    circle_action = getattr(editor, "act_brush_shape_circle", None)
    if square_action is not None and _action_checked(square_action) != bool(shape == "square"):
        _set_action_checked(square_action, bool(shape == "square"))
        repairs.append("brush_shape_square_action_sync")
    if circle_action is not None and _action_checked(circle_action) != bool(shape == "circle"):
        _set_action_checked(circle_action, bool(shape == "circle"))
        repairs.append("brush_shape_circle_action_sync")

    dec_action = getattr(editor, "act_brush_size_decrease", None)
    inc_action = getattr(editor, "act_brush_size_increase", None)
    dec_should_enable = bool(brush_size > 1)
    inc_should_enable = bool(brush_size < 11)
    if dec_action is not None and _action_enabled(dec_action) != dec_should_enable:
        _set_action_enabled(dec_action, dec_should_enable)
        repairs.append("brush_size_decrease_action_sync")
    if inc_action is not None and _action_enabled(inc_action) != inc_should_enable:
        _set_action_enabled(inc_action, inc_should_enable)
        repairs.append("brush_size_increase_action_sync")

    # 4d) Selection mode action must mirror canonical editor state
    selection_mode = bool(getattr(editor, "selection_mode", False))
    act_selection_mode = getattr(editor, "act_selection_mode", None)
    if act_selection_mode is not None and _action_checked(act_selection_mode) != selection_mode:
        _set_action_checked(act_selection_mode, selection_mode)
        repairs.append("selection_mode_action_sync")

    # 5) Refresh cursor profile after theme sync
    cursor_overlay = getattr(editor, "brush_cursor_overlay", None)
    if cursor_overlay is not None:
        with contextlib.suppress(Exception):
            cursor_overlay.refresh_theme_profile()

    # 6) View flags and actions must stay in sync
    for flag_name, action_name in VIEW_FLAG_ACTION_PAIRS:
        action = getattr(editor, action_name, None)
        if action is None:
            continue
        action_state = _action_checked(action)
        flag_state = bool(getattr(editor, flag_name, False))
        if action_state != flag_state:
            _set_action_checked(action, flag_state)
            repairs.append(f"{flag_name}_sync")

    # 7) Mirrored toolbar/menu actions must stay in sync
    for toolbar_action_name, menu_action_name in MIRRORED_ACTION_PAIRS:
        toolbar_action = getattr(editor, toolbar_action_name, None)
        menu_action = getattr(editor, menu_action_name, None)
        if toolbar_action is None or menu_action is None:
            continue
        menu_state = _action_checked(menu_action)
        tb_state = _action_checked(toolbar_action)
        if tb_state != menu_state:
            _set_action_checked(toolbar_action, menu_state)
            repairs.append(f"{toolbar_action_name}_mirror_sync")

    if repairs:
        coordinator = getattr(editor, "drawing_options_coordinator", None)
        _call0(getattr(coordinator, "sync_from_editor", None))
        canvas = getattr(editor, "canvas", None)
        _call0(getattr(canvas, "update", None))

    repairs = sorted({str(item) for item in repairs if str(item)})

    final_signature = fnv1a_64(_snapshot_string(editor).encode("utf-8"))
    return repairs, int(final_signature)
