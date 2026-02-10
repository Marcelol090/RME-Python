#!/usr/bin/env python3
"""Release finalization script for Canary Map Editor.

Generates update manifests, computes checksums, and validates artifacts
against the project schema.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.resolve()

sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    """Compute SHA-256 hex digest of the given file."""
    h = hashlib.sha256()
    with path.open('rb') as fp:
        for chunk in iter(lambda: fp.read(1 << 16), b''):
            h.update(chunk)
    return h.hexdigest()


def _load_schema() -> dict[str, Any]:
    """Load the update manifest JSON schema."""
    schema_path = PROJECT_ROOT / 'py_rme_canary' / 'release' / 'update_manifest.schema.json'
    return json.loads(schema_path.read_text('utf-8'))


def _validate_manifest_basic(manifest: dict[str, Any]) -> list[str]:
    """Basic validation without 3rd-party deps (jsonschema optional)."""
    errors: list[str] = []
    required = [
        'manifest_version', 'generated_at', 'channel',
        'version', 'security', 'rollback', 'assets',
    ]
    for key in required:
        if key not in manifest:
            errors.append(f'Missing required key: {key}')
    if manifest.get('channel') not in ('stable', 'beta', 'nightly'):
        errors.append(f'Invalid channel: {manifest.get("channel")}')
    assets = manifest.get('assets', [])
    if not assets:
        errors.append('assets must have at least one entry')
    for i, asset in enumerate(assets):
        for field in ('name', 'size', 'sha256', 'download_url'):
            if field not in asset:
                errors.append(f'assets[{i}]: missing {field}')
        sha = asset.get('sha256', '')
        if len(sha) != 64 or not all(c in '0123456789abcdef' for c in sha):
            errors.append(f'assets[{i}]: invalid sha256')
    return errors


# ---------------------------------------------------------------------------
# Manifest generation
# ---------------------------------------------------------------------------

def generate_manifest(
    *,
    channel: str = 'stable',
    artifact_dir: Path | None = None,
    download_base_url: str = 'https://github.com/PyRME-Canary/releases/download',
    previous_version: str | None = None,
) -> dict[str, Any]:
    """Generate an update manifest from built artifacts."""
    from py_rme_canary.core.version import get_build_info

    build = get_build_info()
    version_str = build.semver
    tag = f'v{version_str}'

    dist_dir = artifact_dir or (PROJECT_ROOT / 'dist')
    if not dist_dir.exists():
        raise FileNotFoundError(f'Artifact directory not found: {dist_dir}')

    assets: list[dict[str, Any]] = []
    for file in sorted(dist_dir.iterdir()):
        if file.is_file() and file.suffix in ('.exe', '.AppImage', '.dmg', '.zip', '.tar.gz'):
            assets.append({
                'name': file.name,
                'size': file.stat().st_size,
                'sha256': _sha256(file),
                'download_url': f'{download_base_url}/{tag}/{file.name}',
            })

    if not assets:
        raise RuntimeError(f'No release artifacts found in {dist_dir}')

    sig_required = channel == 'stable'
    manifest: dict[str, Any] = {
        'manifest_version': 1,
        'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'channel': channel,
        'version': version_str,
        'manifest_url': f'{download_base_url}/{tag}/update_manifest.json',
        'security': {
            'checksums_required': True,
            'signature': {
                'required': sig_required,
                'algorithm': 'cosign-sigstore',
                'status': 'unsigned',
            },
        },
        'rollback': {
            'enabled': True,
            'previous_version': previous_version,
            'previous_manifest_url': (
                f'{download_base_url}/v{previous_version}/update_manifest.json'
                if previous_version else None
            ),
            'strategy': 'keep-last-known-good',
        },
        'assets': assets,
    }

    errors = _validate_manifest_basic(manifest)
    if errors:
        raise ValueError('Manifest validation failed:\n' + '\n'.join(errors))

    return manifest


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """Generate or validate update manifests."""
    import argparse

    parser = argparse.ArgumentParser(description='Release manifest generator')
    sub = parser.add_subparsers(dest='command', required=True)

    gen = sub.add_parser('generate', help='Generate update manifest')
    gen.add_argument('--channel', default='stable', choices=['stable', 'beta', 'nightly'])
    gen.add_argument('--artifact-dir', type=Path, default=None)
    gen.add_argument('--download-base-url', default='https://github.com/PyRME-Canary/releases/download')
    gen.add_argument('--previous-version', default=None)
    gen.add_argument('--output', '-o', type=Path, default=None)

    val = sub.add_parser('validate', help='Validate existing manifest')
    val.add_argument('manifest', type=Path)

    args = parser.parse_args()

    if args.command == 'generate':
        manifest = generate_manifest(
            channel=args.channel,
            artifact_dir=args.artifact_dir,
            download_base_url=args.download_base_url,
            previous_version=args.previous_version,
        )
        out = args.output or Path(f'update_manifest_{args.channel}.json')
        out.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        n = len(manifest['assets'])
        print(f'Manifest generated: {out}  ({n} asset(s), channel={args.channel})')

    elif args.command == 'validate':
        data = json.loads(args.manifest.read_text('utf-8'))
        errors = _validate_manifest_basic(data)
        if errors:
            for e in errors:
                print(f'ERROR: {e}')
            sys.exit(1)
        else:
            print(f'Manifest is valid: {data["version"]} ({data["channel"]})')


if __name__ == '__main__':
    main()
