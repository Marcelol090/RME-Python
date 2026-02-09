from __future__ import annotations

from pathlib import Path

from py_rme_canary.core.config.configuration_manager import ConfigurationManager
from py_rme_canary.core.config.project import MapMetadata


def _normalize(path: Path | None) -> str:
    return str(path).replace("\\", "/") if path is not None else ""


def test_from_sniff_falls_back_to_package_data_when_workspace_has_no_definitions(tmp_path: Path) -> None:
    metadata = MapMetadata(engine="tfs", client_version=1098, otbm_version=2, source="test")

    cfg = ConfigurationManager.from_sniff(metadata, workspace_root=tmp_path)

    assert cfg.definitions.items_otb is not None
    assert cfg.definitions.items_xml is not None
    assert cfg.definitions.brushes_json is not None
    assert _normalize(cfg.definitions.items_otb).endswith("/py_rme_canary/data/1098/items.otb")
    assert _normalize(cfg.definitions.items_xml).endswith("/py_rme_canary/data/1098/items.xml")
    assert _normalize(cfg.definitions.brushes_json).endswith("/py_rme_canary/data/brushes.json")


def test_from_sniff_prefers_workspace_data_when_available(tmp_path: Path) -> None:
    data_root = tmp_path / "data" / "1310"
    data_root.mkdir(parents=True, exist_ok=True)
    items_otb = data_root / "items.otb"
    items_xml = data_root / "items.xml"
    items_otb.write_bytes(b"placeholder")
    items_xml.write_text("<items/>", encoding="utf-8")

    metadata = MapMetadata(engine="canary", client_version=1310, otbm_version=5, source="test")
    cfg = ConfigurationManager.from_sniff(metadata, workspace_root=tmp_path)

    assert cfg.definitions.items_otb == items_otb
    assert cfg.definitions.items_xml == items_xml
