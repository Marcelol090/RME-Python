from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMenu

from py_rme_canary.vis_layer.ui.docks.search_results_dock import (
    SearchResult,
    SearchResultsDock,
    SearchResultSet,
    SearchResultsTableWidget,
)


@pytest.fixture
def app():
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


@pytest.fixture
def mock_theme_manager():
    with patch("py_rme_canary.vis_layer.ui.docks.search_results_dock.get_theme_manager") as mock:
        mock.return_value.tokens = {
            "color": {
                "surface": {"primary": "#111111", "secondary": "#222222", "tertiary": "#333333"},
                "text": {"primary": "#f0f0f0", "tertiary": "#808080"},
                "brand": {"primary": "#00ff88"},
                "border": {"default": "#555555"},
            },
            "radius": {"sm": 4},
        }
        yield mock


def test_table_select_all_on_map_emits_visible_positions(app, mock_theme_manager):
    table = SearchResultsTableWidget()
    table.set_results(
        [
            SearchResult(x=1, y=1, z=7),
            SearchResult(x=2, y=2, z=7),
            SearchResult(x=3, y=3, z=7),
        ]
    )
    table.setRowHidden(1, True)

    emitted: list[list[tuple[int, int, int]]] = []
    table.select_positions_requested.connect(emitted.append)

    jump_action = QAction("Jump to Location", table)
    copy_action = QAction("Copy Position", table)
    select_all_action = QAction("Select All on Map", table)

    with (
        patch.object(QMenu, "addAction", side_effect=[jump_action, copy_action, select_all_action]),
        patch.object(QMenu, "exec", return_value=select_all_action),
        patch.object(table, "get_selected_results", return_value=[]),
    ):
        table._show_context_menu(QPoint(0, 0))

    assert emitted == [[(1, 1, 7), (3, 3, 7)]]


def test_search_results_dock_applies_selection_to_editor_session(app, mock_theme_manager):
    editor = MagicMock()
    editor.session = MagicMock()
    editor.session.set_selection_tiles.return_value = {(1, 2, 7), (3, 4, 7)}
    editor.canvas = MagicMock()

    dock = SearchResultsDock(editor=editor)
    emitted: list[list[tuple[int, int, int]]] = []
    dock.selection_requested.connect(emitted.append)

    dock._apply_selection_on_map([(1, 2, 7), (1, 2, 7), (3, 4, 7)])

    assert emitted == [[(1, 2, 7), (3, 4, 7)]]
    editor.session.set_selection_tiles.assert_called_once_with([(1, 2, 7), (3, 4, 7)])
    editor.center_on_position.assert_called_once_with(1, 2, 7)
    editor.canvas.update.assert_called_once()
    editor._update_action_enabled_states.assert_called_once()
    editor._set_status.assert_called_once_with("Selected 2 search result tile(s).", 3000)


def test_select_all_results_routes_to_map_selection(app, mock_theme_manager):
    dock = SearchResultsDock(editor=MagicMock())
    dock._current_set = SearchResultSet(
        query="anything",
        results=[SearchResult(x=10, y=20, z=7), SearchResult(x=30, y=40, z=7)],
    )

    with patch.object(dock, "_apply_selection_on_map") as apply_mock:
        dock.select_all_results()

    apply_mock.assert_called_once_with([(10, 20, 7), (30, 40, 7)])
