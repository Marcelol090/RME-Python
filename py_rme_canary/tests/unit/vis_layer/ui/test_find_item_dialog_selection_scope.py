from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QWidget

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.vis_layer.ui.dialogs.find_item_dialog import FindItemDialog, SearchFilters, SearchMode


class _DummySession:
    def __init__(self, selection_tiles: set[tuple[int, int, int]]) -> None:
        self._selection_tiles = set(selection_tiles)

    def get_selection_tiles(self) -> set[tuple[int, int, int]]:
        return set(self._selection_tiles)


class _DummyParent(QWidget):
    def __init__(self, selection_tiles: set[tuple[int, int, int]]) -> None:
        super().__init__()
        self.session = _DummySession(selection_tiles)


@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _make_map() -> GameMap:
    game_map = GameMap(header=MapHeader(otbm_version=2, width=64, height=64))
    game_map.set_tile(Tile(x=10, y=10, z=7, items=[Item(id=100)]))
    game_map.set_tile(Tile(x=20, y=20, z=7, items=[Item(id=100)]))
    return game_map


def test_selection_only_changes_scope(app) -> None:
    game_map = _make_map()
    parent = _DummyParent(selection_tiles={(10, 10, 7)})
    dialog = FindItemDialog(game_map=game_map, parent=parent)

    all_results = dialog._perform_search(SearchFilters(search_mode=SearchMode.ID, search_value="100"))
    selected_results = dialog._perform_search(
        SearchFilters(search_mode=SearchMode.ID, search_value="100", selection_only=True)
    )

    assert {(result.position[0], result.position[1], result.position[2]) for result in all_results} == {
        (10, 10, 7),
        (20, 20, 7),
    }
    assert {(result.position[0], result.position[1], result.position[2]) for result in selected_results} == {
        (10, 10, 7)
    }


def test_selection_only_without_selection_returns_no_results(app) -> None:
    game_map = _make_map()
    parent = _DummyParent(selection_tiles=set())
    dialog = FindItemDialog(game_map=game_map, parent=parent)

    selected_results = dialog._perform_search(
        SearchFilters(search_mode=SearchMode.ID, search_value="100", selection_only=True)
    )

    assert selected_results == []
