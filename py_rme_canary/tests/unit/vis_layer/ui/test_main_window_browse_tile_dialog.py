"""Tests for main-window browse tile dialog."""

from __future__ import annotations

import pytest

from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile

pytest.importorskip("PyQt6")


@pytest.fixture
def app():
    from PyQt6.QtWidgets import QApplication

    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


def test_show_properties_applies_item_changes(app, monkeypatch):
    from py_rme_canary.vis_layer.ui.main_window import browse_tile_dialog as module

    tile = Tile(x=100, y=200, z=7, items=[Item(id=2160)])
    dialog = module.BrowseTileDialog(tile=tile)
    dialog._items_list.setCurrentRow(0)

    def _edit(parent, item):
        item.action_id = 1000
        item.unique_id = 2000
        item.text = "hello"
        return True

    monkeypatch.setattr(module, "_edit_item_basic_properties", _edit)
    dialog._on_show_properties()

    assert tile.items[0].action_id == 1000
    assert tile.items[0].unique_id == 2000
    assert tile.items[0].text == "hello"


def test_show_properties_cancel_keeps_item(app, monkeypatch):
    from py_rme_canary.vis_layer.ui.main_window import browse_tile_dialog as module

    tile = Tile(x=100, y=200, z=7, items=[Item(id=2160, action_id=10)])
    dialog = module.BrowseTileDialog(tile=tile)
    dialog._items_list.setCurrentRow(0)

    monkeypatch.setattr(module, "_edit_item_basic_properties", lambda parent, item: False)
    dialog._on_show_properties()

    assert tile.items[0].action_id == 10
