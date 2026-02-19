from __future__ import annotations

from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_edit import format_position_for_copy


def test_format_position_for_copy_legacy_default() -> None:
    assert format_position_for_copy(100, 200, 7, copy_format=0) == "{x = 100, y = 200, z = 7}"


def test_format_position_for_copy_json() -> None:
    assert format_position_for_copy(100, 200, 7, copy_format=1) == '{"x":100,"y":200,"z":7}'


def test_format_position_for_copy_csv() -> None:
    assert format_position_for_copy(100, 200, 7, copy_format=2) == "100, 200, 7"


def test_format_position_for_copy_tuple() -> None:
    assert format_position_for_copy(100, 200, 7, copy_format=3) == "(100, 200, 7)"


def test_format_position_for_copy_position_wrapper() -> None:
    assert format_position_for_copy(100, 200, 7, copy_format=4) == "Position(100, 200, 7)"


def test_format_position_for_copy_invalid_fallbacks_to_legacy() -> None:
    assert format_position_for_copy(1, 2, 3, copy_format=99) == "{x = 1, y = 2, z = 3}"
