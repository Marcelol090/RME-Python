"""Tests for core.updates.update_checker module."""
from __future__ import annotations

import json
from unittest import mock

import pytest

from py_rme_canary.core.updates.update_checker import (
    UpdateAsset,
    UpdateChecker,
    UpdateCheckResult,
    _parse_manifest,
    _version_from_string,
    check_for_updates,
)
from py_rme_canary.core.version import BuildInfo

# ── _version_from_string ─────────────────────────────────────────


class TestVersionFromString:
    """Parse SemVer strings into BuildInfo."""

    def test_stable_version(self) -> None:
        info = _version_from_string("3.1.2")
        assert info.major == 3
        assert info.minor == 1
        assert info.patch == 2
        assert info.pre == ""

    def test_prerelease_version(self) -> None:
        info = _version_from_string("3.0.0-beta.1")
        assert info.major == 3
        assert info.pre == "beta.1"

    def test_rc_version(self) -> None:
        info = _version_from_string("4.0.0-rc.2")
        assert info.major == 4
        assert info.pre == "rc.2"

    def test_major_only(self) -> None:
        info = _version_from_string("5")
        assert info.version_tuple == (5, 0, 0)

    def test_major_minor(self) -> None:
        info = _version_from_string("5.2")
        assert info.version_tuple == (5, 2, 0)


# ── _parse_manifest ──────────────────────────────────────────────


class TestParseManifest:
    """Manifest parsing and validation."""

    def test_valid_manifest(self) -> None:
        raw = json.dumps({
            "version": "3.1.0",
            "channel": "stable",
            "assets": [{"name": "a.exe", "size": 100, "sha256": "a" * 64, "download_url": "https://x"}],
        }).encode()
        data = _parse_manifest(raw)
        assert data["version"] == "3.1.0"

    def test_missing_version_raises(self) -> None:
        raw = json.dumps({"assets": []}).encode()
        with pytest.raises(ValueError, match="version"):
            _parse_manifest(raw)

    def test_missing_assets_raises(self) -> None:
        raw = json.dumps({"version": "1.0.0"}).encode()
        with pytest.raises(ValueError, match="assets"):
            _parse_manifest(raw)

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            _parse_manifest(b"not json")


# ── UpdateAsset / UpdateCheckResult dataclasses ──────────────────


class TestDataclasses:
    """Dataclass tests."""

    def test_update_asset_frozen(self) -> None:
        a = UpdateAsset(name="x.exe", size=1, sha256="a" * 64, download_url="https://x")
        assert a.name == "x.exe"
        with pytest.raises(AttributeError):
            a.name = "y.exe"  # type: ignore[misc]

    def test_update_check_result_defaults(self) -> None:
        r = UpdateCheckResult(available=False, current_version="3.0.0")
        assert r.latest_version == ""
        assert r.channel == ""
        assert r.assets == ()
        assert r.error == ""

    def test_update_check_result_with_data(self) -> None:
        asset = UpdateAsset(name="a.exe", size=42, sha256="b" * 64, download_url="https://x")
        r = UpdateCheckResult(
            available=True,
            current_version="3.0.0",
            latest_version="3.1.0",
            channel="stable",
            assets=(asset,),
        )
        assert r.available is True
        assert len(r.assets) == 1


# ── check_for_updates (mocked HTTP) ─────────────────────────────


def _make_manifest(version: str = "3.1.0", channel: str = "stable") -> bytes:
    """Create a valid manifest JSON."""
    return json.dumps({
        "version": version,
        "channel": channel,
        "assets": [
            {
                "name": "CanaryMapEditor.exe",
                "size": 50_000_000,
                "sha256": "a" * 64,
                "download_url": "https://example.com/v3.1.0/CanaryMapEditor.exe",
            }
        ],
    }).encode("utf-8")


class TestCheckForUpdates:
    """Integration tests with mocked HTTP."""

    def test_update_available(self) -> None:
        current = BuildInfo(major=3, minor=0, patch=0)
        manifest_bytes = _make_manifest("3.1.0")
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = manifest_bytes
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)

        with mock.patch("py_rme_canary.core.updates.update_checker.urllib.request.urlopen",
                       return_value=mock_resp):
            result = check_for_updates(
                manifest_url="https://example.com/manifest.json",
                current=current,
            )
        assert result.available is True
        assert result.latest_version == "3.1.0"
        assert len(result.assets) == 1
        assert result.error == ""

    def test_no_update_same_version(self) -> None:
        current = BuildInfo(major=3, minor=1, patch=0)
        manifest_bytes = _make_manifest("3.1.0")
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = manifest_bytes
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)

        with mock.patch("py_rme_canary.core.updates.update_checker.urllib.request.urlopen",
                       return_value=mock_resp):
            result = check_for_updates(
                manifest_url="https://example.com/manifest.json",
                current=current,
            )
        assert result.available is False

    def test_no_update_newer_current(self) -> None:
        current = BuildInfo(major=4, minor=0, patch=0)
        manifest_bytes = _make_manifest("3.1.0")
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = manifest_bytes
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)

        with mock.patch("py_rme_canary.core.updates.update_checker.urllib.request.urlopen",
                       return_value=mock_resp):
            result = check_for_updates(
                manifest_url="https://example.com/manifest.json",
                current=current,
            )
        assert result.available is False

    def test_network_error(self) -> None:
        import urllib.error
        current = BuildInfo(major=3, minor=0, patch=0)
        with mock.patch(
            "py_rme_canary.core.updates.update_checker.urllib.request.urlopen",
            side_effect=urllib.error.URLError("timeout"),
        ):
            result = check_for_updates(
                manifest_url="https://example.com/manifest.json",
                current=current,
            )
        assert result.available is False
        assert "Network error" in result.error

    def test_invalid_manifest(self) -> None:
        current = BuildInfo(major=3, minor=0, patch=0)
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = b"{\"bad\": true}"
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)

        with mock.patch("py_rme_canary.core.updates.update_checker.urllib.request.urlopen",
                       return_value=mock_resp):
            result = check_for_updates(
                manifest_url="https://example.com/manifest.json",
                current=current,
            )
        assert result.available is False
        assert result.error != ""

    def test_prerelease_update(self) -> None:
        current = BuildInfo(major=3, minor=0, patch=0, pre="beta.1", channel="beta")
        manifest_bytes = _make_manifest("3.0.0", "beta")
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = manifest_bytes
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)

        with mock.patch("py_rme_canary.core.updates.update_checker.urllib.request.urlopen",
                       return_value=mock_resp):
            result = check_for_updates(
                manifest_url="https://example.com/manifest.json",
                current=current,
            )
        # 3.0.0 stable is newer than 3.0.0-beta.1
        assert result.available is True


# ── UpdateChecker class ──────────────────────────────────────────


class TestUpdateChecker:
    """Test the async wrapper class."""

    def test_check_async_returns_future(self) -> None:
        checker = UpdateChecker(manifest_url="https://example.com/manifest.json")
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = _make_manifest("3.0.0")
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)

        with mock.patch("py_rme_canary.core.updates.update_checker.urllib.request.urlopen",
                       return_value=mock_resp):
            future = checker.check_async(current=BuildInfo(major=3, minor=0, patch=0))
            result = future.result(timeout=10)
        assert isinstance(result, UpdateCheckResult)
        checker.shutdown()

    def test_shutdown_no_error(self) -> None:
        checker = UpdateChecker()
        checker.shutdown()
