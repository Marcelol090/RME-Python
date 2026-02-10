from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("PyQt6")

from py_rme_canary.core.database.id_mapper import IdMapper
from py_rme_canary.vis_layer.ui.main_window import qt_map_editor_assets as assets_module
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_assets import QtMapEditorAssetsMixin


class _DummyEditor(QtMapEditorAssetsMixin):
    pass


def test_merge_id_mappers_fills_only_missing_entries() -> None:
    primary = IdMapper(client_to_server={10: 1, 20: 2}, server_to_client={1: 10, 2: 20})
    secondary = IdMapper(
        client_to_server={20: 2, 30: 3, 40: 4},
        server_to_client={2: 20, 3: 30, 4: 40},
    )

    merged, added = QtMapEditorAssetsMixin._merge_id_mappers(primary=primary, secondary=secondary)

    assert merged is not None
    assert int(added) == 2
    assert merged.get_client_id(1) == 10
    assert merged.get_client_id(2) == 20
    assert merged.get_client_id(3) == 30
    assert merged.get_client_id(4) == 40


def test_load_items_definitions_for_config_merges_otb_with_xml(monkeypatch) -> None:
    class _FakeItems:
        def __init__(self, *, c2s: dict[int, int], s2c: dict[int, int]) -> None:
            self.client_to_server = dict(c2s)
            self.server_to_client = dict(s2c)

    def _load_otb(_path):
        return _FakeItems(c2s={1010: 101}, s2c={101: 1010})

    def _load_xml(_path, strict_mapping=False):  # noqa: ARG001
        return _FakeItems(c2s={1010: 101, 2020: 202}, s2c={101: 1010, 202: 2020})

    monkeypatch.setattr(assets_module.ItemsOTB, "load", staticmethod(_load_otb))
    monkeypatch.setattr(assets_module.ItemsXML, "load", staticmethod(_load_xml))

    cfg = SimpleNamespace(
        definitions=SimpleNamespace(
            items_otb=Path("C:/defs/items.otb"),
            items_xml=Path("C:/defs/items.xml"),
        )
    )
    _items_db, mapper, warnings = QtMapEditorAssetsMixin._load_items_definitions_for_config(cfg)

    assert mapper is not None
    assert mapper.get_client_id(101) == 1010
    assert mapper.get_client_id(202) == 2020
    assert any(msg.startswith("items_mapper_merge:") for msg in warnings)


def test_load_item_definitions_from_explicit_paths_merges_otb_with_xml(monkeypatch) -> None:
    class _FakeItems:
        def __init__(self, *, c2s: dict[int, int], s2c: dict[int, int]) -> None:
            self.client_to_server = dict(c2s)
            self.server_to_client = dict(s2c)

    def _load_otb(_path):
        return _FakeItems(c2s={3000: 300}, s2c={300: 3000})

    def _load_xml(_path, strict_mapping=False):  # noqa: ARG001
        return _FakeItems(c2s={3000: 300, 4000: 400}, s2c={300: 3000, 400: 4000})

    monkeypatch.setattr(assets_module.ItemsOTB, "load", staticmethod(_load_otb))
    monkeypatch.setattr(assets_module.ItemsXML, "load", staticmethod(_load_xml))

    editor = _DummyEditor()
    mapper, warnings, counts = editor._load_item_definitions_from_explicit_paths(
        items_otb_path=Path("C:/defs/items.otb"),
        items_xml_path=Path("C:/defs/items.xml"),
    )

    assert mapper is not None
    assert mapper.get_client_id(300) == 3000
    assert mapper.get_client_id(400) == 4000
    assert int(counts.get("items_otb_count", 0)) == 2
    assert any(msg.startswith("items_mapper_merge:") for msg in warnings)
