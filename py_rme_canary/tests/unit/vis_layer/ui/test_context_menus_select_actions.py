from __future__ import annotations

import pytest

pytest.importorskip("PyQt6.QtWidgets", exc_type=ImportError)

from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.vis_layer.ui.menus import context_menus as menus_module


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


def _base_callbacks() -> dict[str, object]:
    return {
        "selection_has_selection": lambda: False,
        "selection_can_paste": lambda: False,
        "selection_copy": lambda: None,
        "selection_cut": lambda: None,
        "selection_paste": lambda: None,
        "selection_delete": lambda: None,
        "copy_position": lambda: None,
    }


def test_item_context_menu_disables_move_to_tileset_when_capability_is_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(menus_module, "ContextMenuBuilder", _FakeBuilder)
    callbacks = _base_callbacks()
    callbacks.update(
        {
            "move_to_tileset": lambda: None,
            "can_move_to_tileset": lambda: False,
            "properties": lambda: None,
            "browse_tile": lambda: None,
            "find_all": lambda: None,
            "replace_all": lambda: None,
        }
    )

    menu = menus_module.ItemContextMenu(None)
    menu.set_callbacks(callbacks)
    menu.show_for_item(item=Item(id=100), tile=Tile(x=1, y=2, z=7), position=(1, 2, 7))

    builder = _FakeBuilder.last
    assert builder is not None
    move_entries = [entry for entry in builder.actions if entry[0] == "action" and entry[1] == "Move To Tileset..."]
    assert len(move_entries) == 1
    assert move_entries[0][2] is False


def test_item_context_menu_keeps_select_action_order_stable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(menus_module, "ContextMenuBuilder", _FakeBuilder)
    callbacks = _base_callbacks()
    callbacks.update(
        {
            "select_wall": lambda: None,
            "select_ground": lambda: None,
            "select_collection": lambda: None,
            "properties": lambda: None,
            "browse_tile": lambda: None,
            "find_all": lambda: None,
            "replace_all": lambda: None,
        }
    )

    menu = menus_module.ItemContextMenu(None)
    menu.set_callbacks(callbacks)
    menu.show_for_item(item=Item(id=4500), tile=Tile(x=5, y=6, z=7), position=(5, 6, 7))

    builder = _FakeBuilder.last
    assert builder is not None
    labels = [entry[1] for entry in builder.actions if entry[0] == "action"]

    assert labels.index("Select Wallbrush") < labels.index("Select Groundbrush")
    assert labels.index("Select Groundbrush") < labels.index("Select Collection")
