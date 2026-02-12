from __future__ import annotations

import pytest

pytest.importorskip("PyQt6.QtWidgets", exc_type=ImportError)

from PyQt6.QtWidgets import QApplication

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.item import Position as ItemPosition
from py_rme_canary.core.data.spawns import MonsterSpawnArea
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.asset_manager import AssetManager
from py_rme_canary.logic_layer.brush_definitions import VIRTUAL_SPAWN_MONSTER_TOOL_ID, BrushManager
from py_rme_canary.logic_layer.context_menu_handlers import ContextMenuActionHandlers
from py_rme_canary.logic_layer.session.action_queue import ActionType
from py_rme_canary.logic_layer.session.editor import EditorSession


class _DummyStatus:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, message: str) -> None:  # noqa: N802
        self.messages.append(str(message))


class _DummyEditor:
    def __init__(self) -> None:
        self.status = _DummyStatus()
        self.selected_brush_id: int | None = None
        self.selected_palette: str | None = None
        self.find_item_id: int | None = None
        self.quick_replace_source_id: int | None = None
        self.replace_dialog_opened = False
        self.copy_selection_calls = 0
        self.cut_selection_calls = 0
        self.delete_selection_calls = 0
        self.replace_selection_calls = 0
        self.paste_armed = False

    def _set_selected_brush_id(self, brush_id: int) -> None:
        self.selected_brush_id = int(brush_id)

    def _select_palette(self, palette_key: str) -> None:
        self.selected_palette = str(palette_key)

    def _find_item_by_id(self, item_id: int) -> None:
        self.find_item_id = int(item_id)

    def _set_quick_replace_source(self, item_id: int) -> None:
        self.quick_replace_source_id = int(item_id)

    def _open_replace_items_dialog(self) -> None:
        self.replace_dialog_opened = True

    def _copy_selection(self) -> None:
        self.copy_selection_calls += 1

    def _cut_selection(self) -> None:
        self.cut_selection_calls += 1

    def _delete_selection(self) -> None:
        self.delete_selection_calls += 1

    def _replace_items_on_selection(self) -> None:
        self.replace_selection_calls += 1

    def _arm_paste(self) -> None:
        self.paste_armed = True


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


class _DummyBrushDef:
    def __init__(self, server_id: int, brush_type: str) -> None:
        self.server_id = int(server_id)
        self.brush_type = str(brush_type)


class _DummyBrushManager:
    def __init__(self, mapping: dict[int, tuple[int, str]]) -> None:
        self._mapping = {int(k): (int(v[0]), str(v[1])) for k, v in mapping.items()}

    def get_brush_any(self, server_id: int) -> _DummyBrushDef | None:
        resolved = self._mapping.get(int(server_id))
        if resolved is None:
            return None
        return _DummyBrushDef(server_id=int(resolved[0]), brush_type=str(resolved[1]))


class _DummySession:
    def __init__(self, brush_manager: _DummyBrushManager) -> None:
        self.brush_manager = brush_manager


class _DummyPasteSession:
    def __init__(self) -> None:
        self.paste_calls: list[tuple[int, int, int]] = []

    def has_selection(self) -> bool:
        return True

    def can_paste(self) -> bool:
        return True

    def paste_buffer(self, *, x: int, y: int, z: int) -> None:
        self.paste_calls.append((int(x), int(y), int(z)))


class _DummySelectionSession:
    def __init__(self, *, has_selection: bool) -> None:
        self._has_selection = bool(has_selection)

    def has_selection(self) -> bool:
        return bool(self._has_selection)


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


def test_copy_position_uses_legacy_lua_table_format(app) -> None:
    handlers = ContextMenuActionHandlers()
    handlers.copy_position((321, 654, 7))
    assert QApplication.clipboard().text() == "{x=321, y=654, z=7}"


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


def test_select_collection_brush_selects_collection_palette(app) -> None:
    editor = _DummyEditor()
    handlers = ContextMenuActionHandlers(canvas=_DummyCanvas(editor))

    handlers.select_collection_brush(Item(id=555))

    assert editor.selected_brush_id == 555
    assert editor.selected_palette == "collection"


def test_select_wall_brush_uses_resolved_brush_and_palette(app) -> None:
    editor = _DummyEditor()
    session = _DummySession(_DummyBrushManager({4500: (3000, "wall")}))
    handlers = ContextMenuActionHandlers(editor_session=session, canvas=_DummyCanvas(editor))
    tile = Tile(x=10, y=20, z=7, items=[Item(id=4500)])

    handlers.select_wall_brush(item=tile.items[0], tile=tile)

    assert editor.selected_brush_id == 3000
    assert editor.selected_palette == "terrain"


def test_get_item_context_callbacks_include_legacy_select_keys(app) -> None:
    editor = _DummyEditor()
    session = _DummySession(
        _DummyBrushManager(
            {
                301: (301, "ground"),
                4500: (3000, "wall"),
                777: (777, "door"),
            }
        )
    )
    handlers = ContextMenuActionHandlers(editor_session=session, canvas=_DummyCanvas(editor))
    tile = Tile(x=10, y=20, z=7, ground=Item(id=301), items=[Item(id=4500), Item(id=777)], house_id=5)

    callbacks = handlers.get_item_context_callbacks(item=tile.items[-1], tile=tile, position=(10, 20, 7))

    assert "select_wall" in callbacks
    assert "select_door" in callbacks
    assert "select_ground" in callbacks
    assert "select_collection" in callbacks
    assert "select_house" in callbacks


def test_select_spawn_brush_prefers_spawn_marker_tool(app) -> None:
    editor = _DummyEditor()
    handlers = ContextMenuActionHandlers(canvas=_DummyCanvas(editor))
    tile = Tile(
        x=10,
        y=20,
        z=7,
        spawn_monster=MonsterSpawnArea(center=ItemPosition(x=10, y=20, z=7), radius=3),
    )

    handlers.select_spawn_brush(tile=tile)

    assert editor.selected_brush_id == int(VIRTUAL_SPAWN_MONSTER_TOOL_ID)
    assert editor.selected_palette == "creature"


def test_tile_context_callbacks_include_selection_operations(app) -> None:
    editor = _DummyEditor()
    handlers = ContextMenuActionHandlers(canvas=_DummyCanvas(editor))
    tile = Tile(x=3, y=4, z=7)

    callbacks = handlers.get_tile_context_callbacks(tile=tile, position=(3, 4, 7))

    assert "selection_copy" in callbacks
    assert "selection_cut" in callbacks
    assert "selection_paste" in callbacks
    assert "selection_delete" in callbacks
    assert "selection_replace_tiles" in callbacks


def test_tile_context_callbacks_include_legacy_select_brush_keys(app) -> None:
    editor = _DummyEditor()
    session = _DummySession(
        _DummyBrushManager(
            {
                301: (301, "ground"),
                4500: (3000, "wall"),
            }
        )
    )
    handlers = ContextMenuActionHandlers(editor_session=session, canvas=_DummyCanvas(editor))
    tile = Tile(x=3, y=4, z=7, ground=Item(id=301), items=[Item(id=4500)])

    callbacks = handlers.get_tile_context_callbacks(tile=tile, position=(3, 4, 7))

    assert "select_raw" in callbacks
    assert "select_wall" in callbacks
    assert "select_ground" in callbacks
    assert "select_collection" in callbacks


def test_selection_callbacks_delegate_to_editor_methods(app) -> None:
    editor = _DummyEditor()
    handlers = ContextMenuActionHandlers(canvas=_DummyCanvas(editor))
    callbacks = handlers.get_tile_context_callbacks(tile=Tile(x=1, y=1, z=7), position=(1, 1, 7))

    callbacks["selection_copy"]()
    callbacks["selection_cut"]()
    callbacks["selection_delete"]()
    callbacks["selection_replace_tiles"]()

    assert editor.copy_selection_calls == 1
    assert editor.cut_selection_calls == 1
    assert editor.delete_selection_calls == 1
    assert editor.replace_selection_calls == 1


def test_paste_at_position_uses_session_paste_buffer(app) -> None:
    editor = _DummyEditor()
    editor.session = _DummyPasteSession()
    handlers = ContextMenuActionHandlers(canvas=_DummyCanvas(editor))

    handlers.paste_at_position((10, 20, 7))

    assert editor.session.paste_calls == [(10, 20, 7)]
    assert editor.paste_armed is False


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


def test_can_move_item_to_tileset_reflects_user_setting(app, monkeypatch: pytest.MonkeyPatch) -> None:
    handlers = ContextMenuActionHandlers()

    monkeypatch.setattr(
        "py_rme_canary.core.config.user_settings.get_user_settings",
        lambda: _DummySettings(enable_tileset_editing=False),
    )
    assert handlers.can_move_item_to_tileset() is False

    monkeypatch.setattr(
        "py_rme_canary.core.config.user_settings.get_user_settings",
        lambda: _DummySettings(enable_tileset_editing=True),
    )
    assert handlers.can_move_item_to_tileset() is True


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


def test_item_context_callbacks_expose_can_move_to_tileset(app, monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _DummyEditor()
    handlers = ContextMenuActionHandlers(canvas=_DummyCanvas(editor))
    tile = Tile(x=10, y=10, z=7, items=[Item(id=4321)])

    monkeypatch.setattr(
        "py_rme_canary.core.config.user_settings.get_user_settings",
        lambda: _DummySettings(enable_tileset_editing=False),
    )
    callbacks = handlers.get_item_context_callbacks(item=tile.items[0], tile=tile, position=(10, 10, 7))
    assert "can_move_to_tileset" in callbacks
    assert callbacks["can_move_to_tileset"]() is False


def test_tile_context_callbacks_expose_selection_replace_capability(app) -> None:
    editor = _DummyEditor()
    session = _DummySelectionSession(has_selection=True)
    handlers = ContextMenuActionHandlers(editor_session=session, canvas=_DummyCanvas(editor))
    callbacks = handlers.get_tile_context_callbacks(tile=Tile(x=1, y=2, z=7), position=(1, 2, 7))

    assert "can_selection_replace_tiles" in callbacks
    assert callbacks["can_selection_replace_tiles"]() is True


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


def test_open_item_properties_is_transactional(app, monkeypatch) -> None:
    session, _tile = _make_session_with_single_item(item_id=777)
    session.game_map.set_tile(Tile(x=10, y=10, z=7, items=[Item(id=777, action_id=10, unique_id=20, text="old")]))
    tile = session.game_map.get_tile(10, 10, 7)
    assert tile is not None

    handlers = ContextMenuActionHandlers(editor_session=session)

    def _fake_edit(_parent, draft_item):
        draft_item.action_id = 111
        draft_item.unique_id = 222
        draft_item.text = "new text"
        return True

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.browse_tile_dialog._edit_item_basic_properties",
        _fake_edit,
    )

    handlers.open_item_properties(tile.items[0], tile, (10, 10, 7))

    updated = session.game_map.get_tile(10, 10, 7)
    assert updated is not None
    assert updated.items
    assert updated.items[0].action_id == 111
    assert updated.items[0].unique_id == 222
    assert updated.items[0].text == "new text"

    latest = session.action_queue.latest()
    assert latest is not None
    assert latest.type == ActionType.PAINT

    session.undo()
    reverted = session.game_map.get_tile(10, 10, 7)
    assert reverted is not None
    assert reverted.items
    assert reverted.items[0].action_id == 10
    assert reverted.items[0].unique_id == 20
    assert reverted.items[0].text == "old"


def test_open_item_properties_cancel_keeps_item_unchanged(app, monkeypatch) -> None:
    session, _tile = _make_session_with_single_item(item_id=900)
    session.game_map.set_tile(Tile(x=10, y=10, z=7, items=[Item(id=900, action_id=5, unique_id=6, text="stay")]))
    tile = session.game_map.get_tile(10, 10, 7)
    assert tile is not None

    handlers = ContextMenuActionHandlers(editor_session=session)
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.browse_tile_dialog._edit_item_basic_properties",
        lambda *_args, **_kwargs: False,
    )

    handlers.open_item_properties(tile.items[0], tile, (10, 10, 7))

    unchanged = session.game_map.get_tile(10, 10, 7)
    assert unchanged is not None
    assert unchanged.items
    assert unchanged.items[0].action_id == 5
    assert unchanged.items[0].unique_id == 6
    assert unchanged.items[0].text == "stay"
    assert session.action_queue.latest() is None
