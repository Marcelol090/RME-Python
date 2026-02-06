from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from py_rme_canary.core.data.item import Item
from py_rme_canary.vis_layer.ui.dialogs.find_item_dialog import FindItemDialog, SearchFilters, SearchMode


@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_type_filter_matches_detector_categories(app) -> None:
    dialog = FindItemDialog(game_map=None)

    assert dialog._item_matches(Item(id=1209), SearchFilters(search_mode=SearchMode.TYPE, search_value="door"))
    assert dialog._item_matches(Item(id=1987), SearchFilters(search_mode=SearchMode.TYPE, search_value="container"))
    assert dialog._item_matches(Item(id=1387), SearchFilters(search_mode=SearchMode.TYPE, search_value="teleports"))
    assert dialog._item_matches(Item(id=2050), SearchFilters(search_mode=SearchMode.TYPE, search_value="rotatable"))
    assert not dialog._item_matches(Item(id=2050), SearchFilters(search_mode=SearchMode.TYPE, search_value="door"))


def test_type_filter_allows_empty_query(app) -> None:
    dialog = FindItemDialog(game_map=None)

    assert dialog._item_matches(Item(id=9999), SearchFilters(search_mode=SearchMode.TYPE, search_value=""))
