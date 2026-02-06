from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from py_rme_canary.core.data.item import Item
from py_rme_canary.logic_layer.asset_manager import AssetManager
from py_rme_canary.logic_layer.context_menu_handlers import ContextMenuActionHandlers


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
