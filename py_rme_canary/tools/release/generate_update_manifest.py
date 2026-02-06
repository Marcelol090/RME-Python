#!/usr/bin/env python3
"""Generate signed-ready update manifests for stable/beta/nightly channels."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ALLOWED_CHANNELS = {"stable", "beta", "nightly"}


def _utc_iso() -> str:
    tz = getattr(dt, "UTC", dt.UTC)
    return dt.datetime.now(tz).replace(microsecond=0).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_previous_manifest(path: Path | None) -> tuple[str | None, str | None]:
    if path is None or not path.exists():
        return None, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None, None
    previous_version = payload.get("version")
    previous_url = payload.get("manifest_url")
    return (
        str(previous_version) if previous_version else None,
        str(previous_url) if previous_url else None,
    )


def build_manifest(
    *,
    channel: str,
    version: str,
    assets: list[Path],
    base_url: str,
    previous_manifest_path: Path | None,
) -> dict[str, object]:
    previous_version, previous_manifest_url = _load_previous_manifest(previous_manifest_path)
    release_assets: list[dict[str, object]] = []

    for asset in assets:
        release_assets.append(
            {
                "name": asset.name,
                "size": int(asset.stat().st_size),
                "sha256": _sha256(asset),
                "download_url": f"{base_url.rstrip('/')}/{asset.name}",
            }
        )

    return {
        "manifest_version": 1,
        "generated_at": _utc_iso(),
        "channel": channel,
        "version": version,
        "security": {
            "checksums_required": True,
            "signature": {
                "required": channel == "stable",
                "algorithm": "cosign",
                "status": "unsigned",
            },
        },
        "rollback": {
            "enabled": True,
            "previous_version": previous_version,
            "previous_manifest_url": previous_manifest_url,
            "strategy": "keep-last-known-good",
        },
        "assets": release_assets,
    }


def write_xml_manifest(path: Path, manifest: dict[str, object]) -> None:
    root = ET.Element("updateManifest")
    root.set("channel", str(manifest["channel"]))
    root.set("version", str(manifest["version"]))
    root.set("generatedAt", str(manifest["generated_at"]))

    security = ET.SubElement(root, "security")
    security.set("checksumsRequired", "true")
    signature = (
        manifest.get("security", {}).get("signature", {})
        if isinstance(manifest.get("security"), dict)
        else {}
    )
    signature_node = ET.SubElement(security, "signature")
    signature_node.set("required", "true" if bool(signature.get("required")) else "false")
    signature_node.set("algorithm", str(signature.get("algorithm", "")))
    signature_node.set("status", str(signature.get("status", "")))

    rollback_data = (
        manifest.get("rollback", {})
        if isinstance(manifest.get("rollback"), dict)
        else {}
    )
    rollback = ET.SubElement(root, "rollback")
    rollback.set("enabled", "true" if bool(rollback_data.get("enabled")) else "false")
    rollback.set("strategy", str(rollback_data.get("strategy", "")))
    if rollback_data.get("previous_version"):
        rollback.set("previousVersion", str(rollback_data.get("previous_version")))
    if rollback_data.get("previous_manifest_url"):
        rollback.set("previousManifestUrl", str(rollback_data.get("previous_manifest_url")))

    assets_node = ET.SubElement(root, "assets")
    for item in manifest.get("assets", []):
        if not isinstance(item, dict):
            continue
        node = ET.SubElement(assets_node, "asset")
        node.set("name", str(item.get("name", "")))
        node.set("size", str(item.get("size", 0)))
        node.set("sha256", str(item.get("sha256", "")))
        node.set("downloadUrl", str(item.get("download_url", "")))

    tree = ET.ElementTree(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate release update manifest.")
    parser.add_argument("--channel", required=True, help="Release channel: stable|beta|nightly")
    parser.add_argument("--version", required=True, help="Release version label.")
    parser.add_argument(
        "--asset",
        action="append",
        required=True,
        help="Release asset path. Repeat for multiple assets.",
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Base download URL for assets (without trailing slash).",
    )
    parser.add_argument("--output-json", required=True, help="Manifest JSON output path.")
    parser.add_argument("--output-xml", default="", help="Optional XML output path.")
    parser.add_argument(
        "--previous-manifest",
        default="",
        help="Optional previous manifest JSON for rollback metadata.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    channel = str(args.channel).strip().lower()
    if channel not in ALLOWED_CHANNELS:
        print(f"Invalid channel: {channel}. Allowed: {sorted(ALLOWED_CHANNELS)}", file=sys.stderr)
        return 2

    assets = [Path(value).resolve() for value in args.asset]
    missing = [str(path) for path in assets if not path.exists() or not path.is_file()]
    if missing:
        print(f"Missing assets: {missing}", file=sys.stderr)
        return 2

    previous_manifest_path = (
        Path(args.previous_manifest).resolve()
        if str(args.previous_manifest).strip()
        else None
    )
    manifest = build_manifest(
        channel=channel,
        version=str(args.version).strip(),
        assets=assets,
        base_url=str(args.base_url).strip(),
        previous_manifest_path=previous_manifest_path,
    )

    output_json = Path(args.output_json).resolve()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    output_xml_value = str(args.output_xml).strip()
    if output_xml_value:
        write_xml_manifest(Path(output_xml_value).resolve(), manifest)

    print(f"Manifest generated: {output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
