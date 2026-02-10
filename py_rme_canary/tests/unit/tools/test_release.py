"""Tests for tools/release.py manifest generation and validation."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest

import importlib.util
import sys

# Load tools/release.py directly to avoid namespace collision with py_rme_canary/tools/
_RELEASE_PY = Path(__file__).resolve().parents[4] / "tools" / "release.py"
_spec = importlib.util.spec_from_file_location("tools_release", _RELEASE_PY)
assert _spec is not None and _spec.loader is not None
_release = importlib.util.module_from_spec(_spec)
sys.modules["tools_release"] = _release
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
_spec.loader.exec_module(_release)

_sha256 = _release._sha256
_validate_manifest_basic = _release._validate_manifest_basic
generate_manifest = _release.generate_manifest


# ── _sha256 helper ───────────────────────────────────────────────


class TestSha256:
    """File hashing tests."""

    def test_known_hash(self, tmp_path: Path) -> None:
        f = tmp_path / 'test.bin'
        f.write_bytes(b'hello world')
        expected = hashlib.sha256(b'hello world').hexdigest()
        assert _sha256(f) == expected

    def test_empty_file(self, tmp_path: Path) -> None:
        f = tmp_path / 'empty.bin'
        f.write_bytes(b'')
        expected = hashlib.sha256(b'').hexdigest()
        assert _sha256(f) == expected

    def test_large_file(self, tmp_path: Path) -> None:
        f = tmp_path / 'big.bin'
        data = b'x' * (1 << 17)  # 128KB
        f.write_bytes(data)
        expected = hashlib.sha256(data).hexdigest()
        assert _sha256(f) == expected


# ── _validate_manifest_basic ─────────────────────────────────────


class TestValidateManifestBasic:
    """Manifest validation tests."""

    def _valid_manifest(self) -> dict:
        return {
            'manifest_version': 1,
            'generated_at': '2026-01-01T00:00:00+00:00',
            'channel': 'stable',
            'version': '3.0.0',
            'security': {'checksums_required': True, 'signature': {'required': True, 'algorithm': 'cosign', 'status': 'unsigned'}},
            'rollback': {'enabled': True, 'strategy': 'keep-last-known-good'},
            'assets': [{'name': 'a.exe', 'size': 100, 'sha256': 'a' * 64, 'download_url': 'https://x'}],
        }

    def test_valid_passes(self) -> None:
        errors = _validate_manifest_basic(self._valid_manifest())
        assert errors == []

    def test_missing_version(self) -> None:
        m = self._valid_manifest()
        del m['version']
        errors = _validate_manifest_basic(m)
        assert any('version' in e for e in errors)

    def test_bad_channel(self) -> None:
        m = self._valid_manifest()
        m['channel'] = 'invalid'
        errors = _validate_manifest_basic(m)
        assert any('channel' in e.lower() for e in errors)

    def test_empty_assets(self) -> None:
        m = self._valid_manifest()
        m['assets'] = []
        errors = _validate_manifest_basic(m)
        assert any('assets' in e for e in errors)

    def test_bad_sha256(self) -> None:
        m = self._valid_manifest()
        m['assets'][0]['sha256'] = 'short'
        errors = _validate_manifest_basic(m)
        assert any('sha256' in e for e in errors)

    def test_missing_asset_fields(self) -> None:
        m = self._valid_manifest()
        m['assets'] = [{'name': 'a.exe'}]
        errors = _validate_manifest_basic(m)
        assert len(errors) >= 3  # missing size, sha256, download_url (+ bad sha256)


# ── generate_manifest ────────────────────────────────────────────


class TestGenerateManifest:
    """Test manifest generation with fake artifacts."""

    def test_generates_valid_manifest(self, tmp_path: Path) -> None:
        exe = tmp_path / 'CanaryMapEditor.exe'
        exe.write_bytes(b'FAKE_EXE_CONTENT')

        manifest = generate_manifest(
            channel='beta',
            artifact_dir=tmp_path,
            download_base_url='https://example.com/releases/download',
        )

        assert manifest['version'] == '3.0.0'
        assert manifest['channel'] == 'beta'
        assert len(manifest['assets']) == 1
        assert manifest['assets'][0]['name'] == 'CanaryMapEditor.exe'
        assert manifest['assets'][0]['size'] == len(b'FAKE_EXE_CONTENT')
        assert len(manifest['assets'][0]['sha256']) == 64

    def test_no_artifacts_raises(self, tmp_path: Path) -> None:
        with pytest.raises(RuntimeError, match='No release artifacts'):
            generate_manifest(artifact_dir=tmp_path)

    def test_missing_dir_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            generate_manifest(artifact_dir=Path('/nonexistent/path'))

    def test_security_stable_requires_signature(self, tmp_path: Path) -> None:
        exe = tmp_path / 'CanaryMapEditor.exe'
        exe.write_bytes(b'x')
        manifest = generate_manifest(channel='stable', artifact_dir=tmp_path)
        assert manifest['security']['signature']['required'] is True

    def test_security_beta_no_signature(self, tmp_path: Path) -> None:
        exe = tmp_path / 'CanaryMapEditor.exe'
        exe.write_bytes(b'x')
        manifest = generate_manifest(channel='beta', artifact_dir=tmp_path)
        assert manifest['security']['signature']['required'] is False

    def test_rollback_with_previous(self, tmp_path: Path) -> None:
        exe = tmp_path / 'CanaryMapEditor.exe'
        exe.write_bytes(b'x')
        manifest = generate_manifest(
            channel='stable',
            artifact_dir=tmp_path,
            previous_version='2.9.0',
        )
        assert manifest['rollback']['previous_version'] == '2.9.0'
        assert '2.9.0' in manifest['rollback']['previous_manifest_url']

    def test_rollback_without_previous(self, tmp_path: Path) -> None:
        exe = tmp_path / 'CanaryMapEditor.exe'
        exe.write_bytes(b'x')
        manifest = generate_manifest(channel='stable', artifact_dir=tmp_path)
        assert manifest['rollback']['previous_version'] is None
        assert manifest['rollback']['previous_manifest_url'] is None

    def test_multiple_artifacts(self, tmp_path: Path) -> None:
        (tmp_path / 'CanaryMapEditor.exe').write_bytes(b'win')
        (tmp_path / 'CanaryMapEditor.AppImage').write_bytes(b'linux')
        (tmp_path / 'CanaryMapEditor.dmg').write_bytes(b'macos')
        (tmp_path / 'README.md').write_bytes(b'ignore me')
        manifest = generate_manifest(channel='stable', artifact_dir=tmp_path)
        names = [a['name'] for a in manifest['assets']]
        assert 'CanaryMapEditor.exe' in names
        assert 'CanaryMapEditor.AppImage' in names
        assert 'CanaryMapEditor.dmg' in names
        assert 'README.md' not in names
