from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("PyQt6.QtWidgets", exc_type=ImportError)

from PyQt6.QtCore import QPoint

from py_rme_canary.logic_layer import context_menu_handlers as handlers_module
from py_rme_canary.vis_layer.renderer import opengl_canvas as opengl_module
from py_rme_canary.vis_layer.ui.canvas import widget as canvas_module
from py_rme_canary.vis_layer.ui.menus import context_menus as menus_module


class _FakeMap:
    def __init__(self, *, width: int = 256, height: int = 256, tile: object | None = None) -> None:
        self.header = SimpleNamespace(width=int(width), height=int(height))
        self._tile = tile
        self.calls: list[tuple[int, int, int]] = []

    def get_tile(self, x: int, y: int, z: int) -> object | None:
        self.calls.append((int(x), int(y), int(z)))
        return self._tile


class _FakeSession:
    def __init__(self, *, has_selection: bool) -> None:
        self._has_selection = bool(has_selection)

    def has_selection(self) -> bool:
        return bool(self._has_selection)


class _FakeHandlers:
    instances: list[_FakeHandlers] = []

    def __init__(self, *, editor_session: object | None, canvas: object | None, palette: object | None) -> None:
        self.editor_session = editor_session
        self.canvas = canvas
        self.palette = palette
        self.item_calls: list[tuple[object, object | None, tuple[int, int, int] | None]] = []
        self.tile_calls: list[tuple[object | None, tuple[int, int, int] | None]] = []
        self.__class__.instances.append(self)

    def get_item_context_callbacks(
        self, *, item: object, tile: object | None = None, position: tuple[int, int, int] | None = None
    ) -> dict[str, object]:
        self.item_calls.append((item, tile, position))
        return {"sentinel": "item"}

    def get_tile_context_callbacks(
        self, *, tile: object | None = None, position: tuple[int, int, int] | None = None
    ) -> dict[str, object]:
        self.tile_calls.append((tile, position))
        return {"sentinel": "tile"}


class _FakeMenu:
    instances: list[_FakeMenu] = []

    def __init__(self, parent: object | None = None) -> None:
        self.parent = parent
        self.callbacks: dict[str, object] = {}
        self.show_args: tuple[object | None, object | None, dict[str, object]] | None = None
        self.__class__.instances.append(self)

    def set_callbacks(self, callbacks: dict[str, object]) -> None:
        self.callbacks = dict(callbacks)

    def show_for_item(
        self,
        item: object | None,
        tile: object | None = None,
        *,
        has_selection: bool = False,
        position: tuple[int, int, int] | None = None,
    ) -> None:
        self.show_args = (
            item,
            tile,
            {
                "has_selection": bool(has_selection),
                "position": position,
            },
        )


class _FakeBuilder:
    last: _FakeBuilder | None = None

    def __init__(self, _parent: object | None = None) -> None:
        self.actions: list[tuple[str, str, bool]] = []
        self.__class__.last = self

    def add_action(self, text: str, _callback=None, _shortcut: str = "", *, enabled: bool = True) -> None:
        self.actions.append(("action", str(text), bool(enabled)))

    def add_separator(self) -> None:
        self.actions.append(("sep", "", True))

    def add_submenu(self, text: str) -> None:
        self.actions.append(("submenu", str(text), True))

    def end_submenu(self) -> None:
        self.actions.append(("end_submenu", "", True))

    def exec_at_cursor(self) -> None:
        return None


def _patch_context_menu_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    _FakeHandlers.instances.clear()
    _FakeMenu.instances.clear()
    monkeypatch.setattr(handlers_module, "ContextMenuActionHandlers", _FakeHandlers)
    monkeypatch.setattr(menus_module, "ItemContextMenu", _FakeMenu)


def test_map_canvas_context_menu_supports_empty_tile(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_context_menu_pipeline(monkeypatch)
    editor = SimpleNamespace(
        map=_FakeMap(tile=None),
        viewport=SimpleNamespace(z=7),
        session=_FakeSession(has_selection=True),
        palettes=SimpleNamespace(),
    )
    fake_canvas = SimpleNamespace(_editor=editor, _tile_at=lambda _x, _y: (21, 34))

    canvas_module.MapCanvasWidget._open_context_menu_at(fake_canvas, QPoint(4, 9))

    assert len(_FakeHandlers.instances) == 1
    handler = _FakeHandlers.instances[0]
    assert handler.tile_calls == [(None, (21, 34, 7))]
    assert handler.item_calls == []

    assert len(_FakeMenu.instances) == 1
    menu = _FakeMenu.instances[0]
    assert menu.callbacks.get("sentinel") == "tile"
    assert menu.show_args is not None
    item, tile, kwargs = menu.show_args
    assert item is None
    assert tile is None
    assert kwargs["has_selection"] is True
    assert kwargs["position"] == (21, 34, 7)


def test_opengl_canvas_context_menu_supports_empty_tile(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_context_menu_pipeline(monkeypatch)
    editor = SimpleNamespace(
        map=_FakeMap(tile=None),
        viewport=SimpleNamespace(z=7),
        session=_FakeSession(has_selection=False),
        palettes=SimpleNamespace(),
    )
    fake_canvas = SimpleNamespace(_editor=editor, _tile_at=lambda _x, _y: (12, 15))

    opengl_module.OpenGLCanvasWidget._open_context_menu_at(fake_canvas, QPoint(2, 6))

    assert len(_FakeHandlers.instances) == 1
    handler = _FakeHandlers.instances[0]
    assert handler.tile_calls == [(None, (12, 15, 7))]
    assert handler.item_calls == []

    assert len(_FakeMenu.instances) == 1
    menu = _FakeMenu.instances[0]
    assert menu.callbacks.get("sentinel") == "tile"
    assert menu.show_args is not None
    item, tile, kwargs = menu.show_args
    assert item is None
    assert tile is None
    assert kwargs["has_selection"] is False
    assert kwargs["position"] == (12, 15, 7)


def test_item_context_menu_uses_position_for_copy_when_tile_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(menus_module, "ContextMenuBuilder", _FakeBuilder)
    callbacks = {
        "selection_has_selection": lambda: False,
        "selection_can_paste": lambda: False,
        "selection_copy": lambda: None,
        "selection_cut": lambda: None,
        "selection_paste": lambda: None,
        "selection_delete": lambda: None,
        "copy_position": lambda: None,
    }

    menu = menus_module.ItemContextMenu(None)
    menu.set_callbacks(callbacks)
    menu.show_for_item(
        item=None,
        tile=None,
        has_selection=False,
        position=(100, 200, 7),
    )

    builder = _FakeBuilder.last
    assert builder is not None
    action_labels = [entry[1] for entry in builder.actions if entry[0] == "action"]
    assert "Copy Position (100, 200, 7)" in action_labels
