from __future__ import annotations

import sys
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import py_rme_canary.logic_layer.rust_accel as rust_accel
from py_rme_canary.logic_layer.rust_accel import spawn_entry_names_at_cursor


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


@pytest.fixture(autouse=True)
def _reset_backend_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rust_accel, "_BACKEND_CACHE", None)
    monkeypatch.setattr(rust_accel, "_BACKEND_CACHE_READY", False)


def test_spawn_entry_names_at_cursor_python_fallback() -> None:
    areas = [
        _MonsterArea(
            center=_Center(x=20, y=30, z=7),
            radius=3,
            monsters=(
                _Entry(name="Dragon", dx=0, dy=0),
                _Entry(name="Demon", dx=1, dy=0),
            ),
        )
    ]

    names = spawn_entry_names_at_cursor(areas, entries_attr="monsters", x=20, y=30, z=7)
    assert names == ["Dragon"]


def test_spawn_entry_names_at_cursor_uses_backend_when_available(monkeypatch) -> None:
    backend_calls: list[tuple[object, int, int, int]] = []

    def _backend_fn(payload, x, y, z):
        backend_calls.append((payload, x, y, z))
        return ["BackendResult"]

    monkeypatch.setitem(
        sys.modules,
        "py_rme_canary_rust",
        SimpleNamespace(spawn_entry_names_at_cursor=_backend_fn),
    )

    areas = [
        _MonsterArea(
            center=_Center(x=10, y=10, z=7),
            radius=2,
            monsters=(_Entry(name="A", dx=0, dy=0),),
        )
    ]

    names = spawn_entry_names_at_cursor(areas, entries_attr="monsters", x=10, y=10, z=7)
    assert names == ["BackendResult"]
    assert len(backend_calls) == 1
    _, bx, by, bz = backend_calls[0]
    assert (bx, by, bz) == (10, 10, 7)


def test_spawn_entry_names_at_cursor_falls_back_when_backend_errors(monkeypatch) -> None:
    def _backend_fn(payload, x, y, z):
        raise RuntimeError("backend failure")

    monkeypatch.setitem(
        sys.modules,
        "py_rme_canary_rust",
        SimpleNamespace(spawn_entry_names_at_cursor=_backend_fn),
    )

    areas = [
        _MonsterArea(
            center=_Center(x=15, y=15, z=7),
            radius=2,
            monsters=(_Entry(name="FallbackMonster", dx=0, dy=0),),
        )
    ]

    names = spawn_entry_names_at_cursor(areas, entries_attr="monsters", x=15, y=15, z=7)
    assert names == ["FallbackMonster"]
