from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Position
from py_rme_canary.core.data.towns import Town
from py_rme_canary.vis_layer.ui.dialogs.zone_town_dialogs import TownListDialog


@pytest.fixture
def app():
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _build_map() -> GameMap:
    game_map = GameMap(header=MapHeader(otbm_version=4, width=256, height=256))
    game_map.towns[1] = Town(id=1, name="Thais", temple_position=Position(x=100, y=200, z=7))
    return game_map


def test_town_list_dialog_uses_temple_position_field(app):
    game_map = _build_map()
    dialog = TownListDialog(game_map=game_map, current_pos=(10, 20, 7))

    item = dialog.town_list.item(0)
    assert item is not None
    payload = item.data(Qt.ItemDataRole.UserRole)
    assert payload is not None
    temple = payload.get("temple")
    assert temple is not None
    assert (int(temple.x), int(temple.y), int(temple.z)) == (100, 200, 7)


def test_town_list_dialog_add_uses_current_position_when_no_session(app, monkeypatch):
    game_map = _build_map()
    dialog = TownListDialog(game_map=game_map, current_pos=(33, 44, 5))
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.dialogs.zone_town_dialogs.QInputDialog.getText",
        lambda *args, **kwargs: ("Carlin", True),
    )

    dialog._on_add()

    added = game_map.towns.get(2)
    assert added is not None
    assert added.name == "Carlin"
    assert (int(added.temple_position.x), int(added.temple_position.y), int(added.temple_position.z)) == (33, 44, 5)


def test_town_list_dialog_set_temple_uses_session(app, monkeypatch):
    game_map = _build_map()
    dialog = TownListDialog(game_map=game_map, current_pos=(7, 8, 9))
    dialog.town_list.setCurrentRow(0)

    calls: list[tuple[int, int, int, int]] = []

    class _Session:
        def set_town_temple_position(self, *, town_id: int, x: int, y: int, z: int):
            calls.append((int(town_id), int(x), int(y), int(z)))
            return None

    monkeypatch.setattr(dialog, "_session", lambda: _Session())
    dialog._on_set_temple()

    assert calls == [(1, 7, 8, 9)]


def test_town_list_dialog_delete_blocks_when_houses_linked(app, monkeypatch):
    game_map = _build_map()
    game_map.houses[100] = House(id=100, name="H1", townid=1)
    dialog = TownListDialog(game_map=game_map, current_pos=(0, 0, 7))
    dialog.town_list.setCurrentRow(0)

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.dialogs.zone_town_dialogs.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )

    warning_calls: list[str] = []

    def _warning(*args, **kwargs):
        warning_calls.append("warning")
        return None

    monkeypatch.setattr("py_rme_canary.vis_layer.ui.dialogs.zone_town_dialogs.QMessageBox.warning", _warning)

    deleted: list[int] = []
    monkeypatch.setattr(dialog, "_delete_town", lambda town_id: deleted.append(int(town_id)))

    dialog._on_delete()

    assert warning_calls == ["warning"]
    assert deleted == []
