from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PyQt6")

from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_assets import QtMapEditorAssetsMixin  # noqa: E402


class _DummyEditor(QtMapEditorAssetsMixin):
    pass


def test_normalize_optional_path_handles_empty_values() -> None:
    assert QtMapEditorAssetsMixin._normalize_optional_path("") is None
    assert QtMapEditorAssetsMixin._normalize_optional_path("   ") is None


def test_load_item_definitions_from_explicit_paths_reads_otb_and_xml() -> None:
    editor = _DummyEditor()
    otb_path = Path("py_rme_canary/data/1098/items.otb").resolve()
    xml_path = Path("py_rme_canary/data/1098/items.xml").resolve()

    id_mapper, warnings, counts = editor._load_item_definitions_from_explicit_paths(
        items_otb_path=otb_path,
        items_xml_path=xml_path,
    )

    assert id_mapper is not None
    assert len(getattr(id_mapper, "server_to_client", {}) or {}) > 1000
    assert int(counts.get("items_xml_count", 0)) > 100
    assert not any(msg.startswith("items_otb_error:") for msg in warnings)
