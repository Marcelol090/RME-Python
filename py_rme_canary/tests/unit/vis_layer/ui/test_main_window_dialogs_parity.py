from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

from py_rme_canary.core.data.item import Item
from py_rme_canary.vis_layer.ui.main_window.add_item_dialog import AddItemDialog
from py_rme_canary.vis_layer.ui.main_window.container_properties_dialog import ContainerPropertiesDialog
from py_rme_canary.vis_layer.ui.main_window.dialogs import FindEntityDialog


@pytest.fixture
def app() -> QApplication:
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


class _DummyItemType:
    def __init__(self, name: str) -> None:
        self.name = name


class _DummyItemsDb:
    def get_item_type(self, item_id: int) -> _DummyItemType:
        return _DummyItemType(name=f"Item-{item_id}")


def test_find_entity_dialog_set_mode_selects_tab(app: QApplication) -> None:
    dialog = FindEntityDialog()
    dialog.set_mode("house")
    assert dialog._tabs.tabText(dialog._tabs.currentIndex()) == "House"

    dialog.set_mode("creature")
    assert dialog._tabs.tabText(dialog._tabs.currentIndex()) == "Creature"

    dialog.set_mode("item")
    assert dialog._tabs.tabText(dialog._tabs.currentIndex()) == "Item"


def test_container_properties_dialog_add_item_updates_container(monkeypatch: pytest.MonkeyPatch, app: QApplication) -> None:
    class _FakeAddItemDialog:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def exec(self) -> int:
            return int(QDialog.DialogCode.Accepted)

        def get_selected_item_id(self) -> int:
            return 2152

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.container_properties_dialog.AddItemDialog",
        _FakeAddItemDialog,
    )

    container = Item(id=1987, items=(Item(id=100),))
    dialog = ContainerPropertiesDialog(container_item=container, items_db=_DummyItemsDb())
    dialog._on_add_item()

    updated = dialog.get_container()
    assert updated is not None
    assert [item.id for item in updated.items] == [100, 2152]


def test_container_properties_dialog_remove_item_updates_container(app: QApplication) -> None:
    container = Item(id=1987, items=(Item(id=100), Item(id=200)))
    dialog = ContainerPropertiesDialog(container_item=container, items_db=_DummyItemsDb())

    first = dialog._items_list.item(0)
    assert first is not None
    first.setSelected(True)
    dialog._on_remove_item()

    updated = dialog.get_container()
    assert updated is not None
    assert [item.id for item in updated.items] == [200]


def test_add_item_dialog_without_tileset_skips_confirmation(
    monkeypatch: pytest.MonkeyPatch, app: QApplication
) -> None:
    called = {"info": 0}

    def _fake_information(*_args, **_kwargs) -> None:
        called["info"] += 1

    monkeypatch.setattr(QMessageBox, "information", _fake_information)

    dialog = AddItemDialog(tileset_name="")
    dialog._on_item_id_changed(123)
    dialog._on_add_clicked()

    assert called["info"] == 0
    assert dialog.result() == int(QDialog.DialogCode.Accepted)


def test_add_item_dialog_with_tileset_shows_confirmation(monkeypatch: pytest.MonkeyPatch, app: QApplication) -> None:
    called = {"info": 0}

    def _fake_information(*_args, **_kwargs) -> None:
        called["info"] += 1

    monkeypatch.setattr(QMessageBox, "information", _fake_information)

    dialog = AddItemDialog(tileset_name="Terrain")
    dialog._on_item_id_changed(123)
    dialog._on_add_clicked()

    assert called["info"] == 1
    assert dialog.result() == int(QDialog.DialogCode.Accepted)
