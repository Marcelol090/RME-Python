from __future__ import annotations

import importlib.util
import json
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[3] / "tools" / "release" / "generate_update_manifest.py"
    spec = importlib.util.spec_from_file_location("generate_update_manifest", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generate_update_manifest_json_and_xml(tmp_path: Path) -> None:
    module = _load_module()

    asset = tmp_path / "map-editor.zip"
    asset.write_bytes(b"binary-content")

    previous_manifest = tmp_path / "previous.json"
    previous_manifest.write_text(
        json.dumps(
            {
                "version": "1.2.2",
                "manifest_url": "https://example.com/updates/stable/manifest.json",
            }
        ),
        encoding="utf-8",
    )

    output_json = tmp_path / "manifest.json"
    output_xml = tmp_path / "manifest.xml"

    exit_code = module.main(
        [
            "--channel",
            "stable",
            "--version",
            "1.2.3",
            "--asset",
            str(asset),
            "--base-url",
            "https://example.com/updates/stable",
            "--output-json",
            str(output_json),
            "--output-xml",
            str(output_xml),
            "--previous-manifest",
            str(previous_manifest),
        ]
    )

    assert exit_code == 0
    assert output_json.exists()
    assert output_xml.exists()

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["channel"] == "stable"
    assert payload["version"] == "1.2.3"
    assert payload["security"]["checksums_required"] is True
    assert payload["rollback"]["previous_version"] == "1.2.2"
    assert payload["assets"][0]["name"] == "map-editor.zip"
    assert payload["assets"][0]["download_url"].endswith("/map-editor.zip")


def test_generate_update_manifest_rejects_invalid_channel(tmp_path: Path) -> None:
    module = _load_module()
    asset = tmp_path / "package.whl"
    asset.write_bytes(b"wheel")
    output_json = tmp_path / "manifest.json"

    exit_code = module.main(
        [
            "--channel",
            "canary",
            "--version",
            "0.0.1",
            "--asset",
            str(asset),
            "--base-url",
            "https://example.com",
            "--output-json",
            str(output_json),
        ]
    )

    assert exit_code == 2
    assert not output_json.exists()
