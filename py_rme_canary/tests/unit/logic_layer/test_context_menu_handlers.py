from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.asset_manager import AssetManager
from py_rme_canary.logic_layer.brush_definitions import BrushManager
from py_rme_canary.logic_layer.context_menu_handlers import ContextMenuActionHandlers
from py_rme_canary.logic_layer.session.action_queue import ActionType
from py_rme_canary.logic_layer.session.editor import EditorSession


class _DummyStatus:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, message: str) -> None:
        self.messages.append(str(message))


class _DummyEditor:
    def __init__(self) -> None:
        self.status = _DummyStatus()
        self.selected_brush_id: int | None = None
        self.find_item_id: int | None = None
        self.quick_replace_source_id: int | None = None
        self.replace_dialog_opened = False

    def _set_selected_brush_id(self, brush_id: int) -> None:
        self.selected_brush_id = int(brush_id)

    def _find_item_by_id(self, item_id: int) -> None:
        self.find_item_id = int(item_id)

    def _set_quick_replace_source(self, item_id: int) -> None:
        self.quick_replace_source_id = int(item_id)

    def _open_replace_items_dialog(self) -> None:
        self.replace_dialog_opened = True


class _DummyCanvas:
    def __init__(self, editor: _DummyEditor) -> None:
        self._editor = editor


class _DummyMapper:
    def __init__(self, mapping: dict[int, int]) -> None:
        self._mapping = {int(k): int(v) for k, v in mapping.items()}

    def get_client_id(self, server_id: int) -> int | None:
        return self._mapping.get(int(server_id))


class _DummySettings:
    def __init__(self, *, enable_tileset_editing: bool) -> None:
        self._enable_tileset_editing = bool(enable_tileset_editing)

    def get_enable_tileset_editing(self) -> bool:
        return bool(self._enable_tileset_editing)


@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_copy_client_id_uses_id_mapper(app) -> None:
    asset_mgr = AssetManager.instance()
    original_mapper = getattr(asset_mgr, "_id_mapper", None)

    try:
        asset_mgr._id_mapper = _DummyMapper({123: 456})

        handlers = ContextMenuActionHandlers()
        handlers.copy_client_id(Item(id=123))

        assert QApplication.clipboard().text() == "456"
    finally:
        asset_mgr._id_mapper = original_mapper


def test_select_brush_uses_editor_callback(app) -> None:
    editor = _DummyEditor()
    handlers = ContextMenuActionHandlers(canvas=_DummyCanvas(editor))

    handlers.select_brush_for_item(Item(id=1209))

    assert editor.selected_brush_id == 1209
    assert editor.status.messages


def test_find_and_replace_actions_use_editor_callbacks(app) -> None:
    editor = _DummyEditor()
    handlers = ContextMenuActionHandlers(canvas=_DummyCanvas(editor))
    item = Item(id=321)

    handlers.find_all_items(item)
    handlers.replace_all_items(item)

    assert editor.find_item_id == 321
    assert editor.quick_replace_source_id == 321
    assert editor.replace_dialog_opened is True


def test_select_raw_brush_uses_item_id(app) -> None:
    editor = _DummyEditor()
    handlers = ContextMenuActionHandlers(canvas=_DummyCanvas(editor))

    handlers.select_raw_brush(Item(id=777))

    assert editor.selected_brush_id == 777


def test_move_item_to_tileset_requires_setting_enabled(app, monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _DummyEditor()
    handlers = ContextMenuActionHandlers(canvas=_DummyCanvas(editor))

    monkeypatch.setattr(
        "py_rme_canary.core.config.user_settings.get_user_settings",
        lambda: _DummySettings(enable_tileset_editing=False),
    )
    called: dict[str, bool] = {"dialog_called": False}

    class _FakeAddItemDialog:
        def __init__(self, *args, **kwargs) -> None:
            called["dialog_called"] = True

    monkeypatch.setattr("py_rme_canary.vis_layer.ui.main_window.add_item_dialog.AddItemDialog", _FakeAddItemDialog)

    handlers.move_item_to_tileset(Item(id=100))

    assert called["dialog_called"] is False
    assert any("Enable tileset editing" in msg for msg in editor.status.messages)


def test_move_item_to_tileset_opens_dialog_with_selected_item(app, monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _DummyEditor()
    handlers = ContextMenuActionHandlers(canvas=_DummyCanvas(editor))

    monkeypatch.setattr(
        "py_rme_canary.core.config.user_settings.get_user_settings",
        lambda: _DummySettings(enable_tileset_editing=True),
    )
    captured: dict[str, int] = {"initial_item_id": 0}

    class _FakeAddItemDialog:
        def __init__(self, *args, **kwargs) -> None:
            captured["initial_item_id"] = int(kwargs.get("initial_item_id", 0))

        def exec(self) -> int:
            return 1

        def get_selected_item_id(self) -> int:
            return int(captured["initial_item_id"])

    monkeypatch.setattr("py_rme_canary.vis_layer.ui.main_window.add_item_dialog.AddItemDialog", _FakeAddItemDialog)

    handlers.move_item_to_tileset(Item(id=4321))

    assert captured["initial_item_id"] == 4321
    assert any("Tileset" in msg for msg in editor.status.messages)


def _make_session_with_single_item(item_id: int = 2050) -> tuple[EditorSession, Tile]:
    game_map = GameMap(header=MapHeader(otbm_version=2, width=64, height=64))
    tile = Tile(x=10, y=10, z=7, items=[Item(id=int(item_id))])
    game_map.set_tile(tile)
    session = EditorSession(game_map=game_map, brush_manager=BrushManager())
    return session, tile


def test_rotate_item_is_transactional(app) -> None:
    session, tile = _make_session_with_single_item(item_id=2050)
    handlers = ContextMenuActionHandlers(editor_session=session)

    handlers.rotate_item(tile.items[0], tile, (10, 10, 7))

    updated = session.game_map.get_tile(10, 10, 7)
    assert updated is not None
    assert updated.items and int(updated.items[0].id) == 2051
    latest = session.action_queue.latest()
    assert latest is not None
    assert latest.type == ActionType.PAINT

    session.undo()
    reverted = session.game_map.get_tile(10, 10, 7)
    assert reverted is not None
    assert reverted.items and int(reverted.items[0].id) == 2050


def test_delete_item_is_transactional(app) -> None:
    session, tile = _make_session_with_single_item(item_id=321)
    handlers = ContextMenuActionHandlers(editor_session=session)

    handlers.delete_item(tile.items[0], tile, (10, 10, 7))

    updated = session.game_map.get_tile(10, 10, 7)
    assert updated is not None
    assert updated.items == []
    latest = session.action_queue.latest()
    assert latest is not None
    assert latest.type == ActionType.PAINT

    session.undo()
    reverted = session.game_map.get_tile(10, 10, 7)
    assert reverted is not None
    assert reverted.items and int(reverted.items[0].id) == 321


def test_edit_item_text_is_transactional(app, monkeypatch) -> None:
    session, tile = _make_session_with_single_item(item_id=777)
    session.game_map.set_tile(Tile(x=10, y=10, z=7, items=[Item(id=777, text="old")]))
    tile = session.game_map.get_tile(10, 10, 7)
    assert tile is not None

    handlers = ContextMenuActionHandlers(editor_session=session)
    monkeypatch.setattr(
        "py_rme_canary.logic_layer.context_menu_handlers.QInputDialog.getMultiLineText",
        lambda *args, **kwargs: ("new text", True),
    )

    handlers.edit_item_text(tile.items[0], tile, (10, 10, 7))

    updated = session.game_map.get_tile(10, 10, 7)
    assert updated is not None
    assert updated.items and updated.items[0].text == "new text"

    session.undo()
    reverted = session.game_map.get_tile(10, 10, 7)
    assert reverted is not None
    assert reverted.items and reverted.items[0].text == "old"
