from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication

from py_rme_canary.logic_layer.asset_manager import AssetManager
from py_rme_canary.vis_layer.ui.main_window.dialogs import FindItemDialog


@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_find_item_dialog_defaults_to_server_id(app) -> None:
    dialog = FindItemDialog()
    dialog._id_spin.setValue(4500)
    result = dialog.result_value()

    assert result.query_mode == "server_id"
    assert result.query_value == 4500
    assert result.server_id == 4500
    assert result.resolved


def test_main_find_item_dialog_client_id_mapping_success(app, monkeypatch) -> None:
    class _FakeMapper:
        def get_server_id(self, client_id: int) -> int | None:
            return {7000: 2160}.get(int(client_id))

    class _FakeAssetManager:
        def __init__(self) -> None:
            self._id_mapper = _FakeMapper()
            self._items_xml = None

    monkeypatch.setattr(AssetManager, "instance", staticmethod(lambda: _FakeAssetManager()))

    dialog = FindItemDialog()
    dialog._mode_combo.setCurrentIndex(1)  # Client ID
    dialog._id_spin.setValue(7000)
    result = dialog.result_value()

    assert result.query_mode == "client_id"
    assert result.query_value == 7000
    assert result.server_id == 2160
    assert result.resolved


def test_main_find_item_dialog_client_id_mapping_failure(app, monkeypatch) -> None:
    class _FakeMapper:
        def get_server_id(self, _client_id: int) -> int | None:
            return None

    class _FakeItemsXml:
        def get_server_id(self, _client_id: int) -> int | None:
            return None

    class _FakeAssetManager:
        def __init__(self) -> None:
            self._id_mapper = _FakeMapper()
            self._items_xml = _FakeItemsXml()

    monkeypatch.setattr(AssetManager, "instance", staticmethod(lambda: _FakeAssetManager()))

    dialog = FindItemDialog()
    dialog._mode_combo.setCurrentIndex(1)  # Client ID
    dialog._id_spin.setValue(9999)
    result = dialog.result_value()

    assert result.query_mode == "client_id"
    assert result.query_value == 9999
    assert result.server_id == 0
    assert not result.resolved
    assert "No ServerID mapping" in result.error
