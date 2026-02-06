from __future__ import annotations

from dataclasses import dataclass

import pytest

pytest.importorskip("PyQt6")

from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_session import QtMapEditorSessionMixin


@dataclass(slots=True)
class _Center:
    x: int
    y: int
    z: int


@dataclass(slots=True)
class _Entry:
    name: str
    dx: int
    dy: int


@dataclass(slots=True)
class _MonsterArea:
    center: _Center
    radius: int
    monsters: tuple[_Entry, ...]


@dataclass(slots=True)
class _NpcArea:
    center: _Center
    radius: int
    npcs: tuple[_Entry, ...]


def test_parse_prefixed_int_accepts_standard_label() -> None:
    assert QtMapEditorSessionMixin._parse_prefixed_int("42: City") == 42


def test_parse_prefixed_int_returns_none_for_invalid_input() -> None:
    assert QtMapEditorSessionMixin._parse_prefixed_int("not-an-id") is None


def test_collect_spawn_entry_names_at_cursor_monsters() -> None:
    names = QtMapEditorSessionMixin._collect_spawn_entry_names_at_cursor(
        [
            _MonsterArea(
                center=_Center(x=100, y=200, z=7),
                radius=5,
                monsters=(
                    _Entry(name="Dragon", dx=0, dy=0),
                    _Entry(name="Demon", dx=1, dy=0),
                ),
            ),
            _MonsterArea(
                center=_Center(x=100, y=200, z=7),
                radius=5,
                monsters=(_Entry(name="Rat", dx=0, dy=0),),
            ),
        ],
        entries_attr="monsters",
        x=100,
        y=200,
        z=7,
    )
    assert names == ["Dragon"]


def test_collect_spawn_entry_names_at_cursor_npcs() -> None:
    names = QtMapEditorSessionMixin._collect_spawn_entry_names_at_cursor(
        [
            _NpcArea(
                center=_Center(x=55, y=66, z=7),
                radius=4,
                npcs=(
                    _Entry(name="Guide", dx=0, dy=0),
                    _Entry(name="Banker", dx=0, dy=0),
                ),
            )
        ],
        entries_attr="npcs",
        x=55,
        y=66,
        z=7,
    )
    assert names == ["Guide", "Banker"]


def test_collect_spawn_entry_names_at_cursor_respects_floor_and_radius() -> None:
    names = QtMapEditorSessionMixin._collect_spawn_entry_names_at_cursor(
        [
            _MonsterArea(
                center=_Center(x=10, y=10, z=6),
                radius=2,
                monsters=(_Entry(name="WrongFloor", dx=0, dy=0),),
            ),
            _MonsterArea(
                center=_Center(x=10, y=10, z=7),
                radius=1,
                monsters=(_Entry(name="TooFar", dx=0, dy=0),),
            ),
        ],
        entries_attr="monsters",
        x=13,
        y=13,
        z=7,
    )
    assert names == []
