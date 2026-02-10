from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from py_rme_canary.core.data.item import Item
from py_rme_canary.logic_layer.asset_manager import AssetManager
from py_rme_canary.vis_layer.ui.dialogs.find_item_dialog import FindItemDialog, SearchFilters, SearchMode


@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_client_id_mode_matches_direct_item_client_id(app) -> None:
    dialog = FindItemDialog(game_map=None)
    item = Item(id=100, client_id=4500)

    assert dialog._item_matches(item, SearchFilters(search_mode=SearchMode.CLIENT_ID, search_value="4500"))
    assert not dialog._item_matches(item, SearchFilters(search_mode=SearchMode.CLIENT_ID, search_value="4501"))


def test_client_id_mode_uses_mapper_when_item_has_no_client_id(app, monkeypatch) -> None:
    class _FakeMapper:
        def get_client_id(self, server_id: int) -> int | None:
            return {100: 777}.get(int(server_id))

    class _FakeAssetManager:
        def __init__(self) -> None:
            self._id_mapper = _FakeMapper()

        def get_item_metadata(self, _server_id: int):
            return None

    fake_asset_manager = _FakeAssetManager()
    monkeypatch.setattr(AssetManager, "instance", staticmethod(lambda: fake_asset_manager))

    dialog = FindItemDialog(game_map=None)
    item = Item(id=100)
    assert dialog._item_matches(item, SearchFilters(search_mode=SearchMode.CLIENT_ID, search_value="777"))
    assert not dialog._item_matches(item, SearchFilters(search_mode=SearchMode.CLIENT_ID, search_value="778"))


def test_client_id_mode_updates_placeholder(app) -> None:
    dialog = FindItemDialog(game_map=None)
    dialog.client_id_radio.setChecked(True)
    assert "client id" in dialog.search_input.placeholderText().lower()
