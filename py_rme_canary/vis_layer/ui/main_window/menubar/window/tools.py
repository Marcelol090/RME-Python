from __future__ import annotations


def new_view(editor) -> None:
    editor._new_view()


def toggle_fullscreen(editor) -> None:
    editor._toggle_fullscreen()


def take_screenshot(editor) -> None:
    editor._take_screenshot()


def set_view_flag(editor, flag: str, value: bool) -> None:
    editor._set_view_flag(str(flag), bool(value))


def toggle_sprite_preview(editor, value: bool) -> None:
    editor._toggle_sprite_preview(bool(value))


def toggle_indicators_simple(editor, value: bool) -> None:
    editor._toggle_indicators_simple(bool(value))


def toggle_wall_hooks(editor, value: bool) -> None:
    editor._toggle_wall_hooks(bool(value))


def toggle_pickupables(editor, value: bool) -> None:
    editor._toggle_pickupables(bool(value))


def toggle_moveables(editor, value: bool) -> None:
    editor._toggle_moveables(bool(value))


def toggle_avoidables(editor, value: bool) -> None:
    editor._toggle_avoidables(bool(value))


def toggle_minimap_dock(editor, value: bool) -> None:
    editor._toggle_minimap_dock(bool(value))


def toggle_actions_history_dock(editor, value: bool) -> None:
    editor._toggle_actions_history_dock(bool(value))
