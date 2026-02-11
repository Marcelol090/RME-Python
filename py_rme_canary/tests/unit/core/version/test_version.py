"""Tests for core.version module."""
from __future__ import annotations

import os
from unittest import mock

import pytest

from py_rme_canary.core.version import (
    APP_VERSION,
    BuildInfo,
    _detect_git_hash,
    get_build_info,
)

# ── BuildInfo dataclass ──────────────────────────────────────────


class TestBuildInfo:
    """Unit tests for the BuildInfo frozen dataclass."""

    def test_default_values(self) -> None:
        info = BuildInfo()
        assert info.major == 3
        assert info.minor == 0
        assert info.patch == 0
        assert info.pre == ""
        assert info.channel == "beta"

    def test_semver_stable(self) -> None:
        info = BuildInfo(major=3, minor=1, patch=2, pre="")
        assert info.semver == "3.1.2"

    def test_semver_prerelease(self) -> None:
        info = BuildInfo(major=3, minor=0, patch=0, pre="beta.1")
        assert info.semver == "3.0.0-beta.1"

    def test_short_version(self) -> None:
        info = BuildInfo(major=4, minor=2, patch=7)
        assert info.short_version == "4.2.7"

    def test_display_name(self) -> None:
        info = BuildInfo(major=3, minor=0, patch=0)
        assert info.display_name == "Canary Map Editor v3.0.0"

    def test_display_name_prerelease(self) -> None:
        info = BuildInfo(pre="rc.1")
        assert "rc.1" in info.display_name

    def test_user_agent(self) -> None:
        info = BuildInfo()
        assert info.user_agent.startswith("PyRME-Canary/")

    def test_version_tuple(self) -> None:
        info = BuildInfo(major=1, minor=2, patch=3)
        assert info.version_tuple == (1, 2, 3)

    def test_frozen(self) -> None:
        info = BuildInfo()
        with pytest.raises(AttributeError):
            info.major = 99  # type: ignore[misc]


class TestIsNewerThan:
    """Tests for version comparison logic."""

    def test_newer_major(self) -> None:
        old = BuildInfo(major=2, minor=9, patch=9)
        new = BuildInfo(major=3, minor=0, patch=0)
        assert new.is_newer_than(old)
        assert not old.is_newer_than(new)

    def test_newer_minor(self) -> None:
        old = BuildInfo(major=3, minor=0, patch=5)
        new = BuildInfo(major=3, minor=1, patch=0)
        assert new.is_newer_than(old)

    def test_newer_patch(self) -> None:
        old = BuildInfo(major=3, minor=0, patch=0)
        new = BuildInfo(major=3, minor=0, patch=1)
        assert new.is_newer_than(old)

    def test_same_version_not_newer(self) -> None:
        a = BuildInfo(major=3, minor=0, patch=0)
        b = BuildInfo(major=3, minor=0, patch=0)
        assert not a.is_newer_than(b)

    def test_stable_beats_prerelease(self) -> None:
        stable = BuildInfo(major=3, minor=0, patch=0, pre="")
        beta = BuildInfo(major=3, minor=0, patch=0, pre="beta.1")
        assert stable.is_newer_than(beta)
        assert not beta.is_newer_than(stable)

    def test_prerelease_ordering(self) -> None:
        beta1 = BuildInfo(major=3, minor=0, patch=0, pre="beta.1")
        beta2 = BuildInfo(major=3, minor=0, patch=0, pre="beta.2")
        assert beta2.is_newer_than(beta1)
        assert not beta1.is_newer_than(beta2)

    def test_rc_beats_beta(self) -> None:
        beta = BuildInfo(major=3, minor=0, patch=0, pre="beta.9")
        rc = BuildInfo(major=3, minor=0, patch=0, pre="rc.1")
        assert rc.is_newer_than(beta)


# ── get_build_info ────────────────────────────────────────────────


class TestGetBuildInfo:
    """Tests for the singleton factory."""

    def test_returns_build_info(self) -> None:
        # Clear the lru_cache to get fresh result
        get_build_info.cache_clear()
        info = get_build_info()
        assert isinstance(info, BuildInfo)

    def test_singleton_identity(self) -> None:
        get_build_info.cache_clear()
        a = get_build_info()
        b = get_build_info()
        assert a is b

    def test_env_override_channel(self) -> None:
        get_build_info.cache_clear()
        with mock.patch.dict(os.environ, {"PYRME_CHANNEL": "nightly"}):
            get_build_info.cache_clear()
            info = get_build_info()
            assert info.channel == "nightly"
        get_build_info.cache_clear()

    def test_env_override_commit(self) -> None:
        get_build_info.cache_clear()
        with mock.patch.dict(os.environ, {"PYRME_COMMIT": "abc1234"}):
            get_build_info.cache_clear()
            info = get_build_info()
            assert info.commit_hash == "abc1234"
        get_build_info.cache_clear()

    def test_env_override_build_number(self) -> None:
        get_build_info.cache_clear()
        with mock.patch.dict(os.environ, {"PYRME_BUILD_NUMBER": "42"}):
            get_build_info.cache_clear()
            info = get_build_info()
            assert info.build_number == 42
        get_build_info.cache_clear()


# ── APP_VERSION constant ──────────────────────────────────────────


def test_app_version_string() -> None:
    assert APP_VERSION == "3.0.0"


# ── _detect_git_hash ─────────────────────────────────────────────


class TestDetectGitHash:
    """Tests for git hash detection."""

    def test_returns_string(self) -> None:
        result = _detect_git_hash()
        assert isinstance(result, str)

    def test_handles_no_git(self) -> None:
        with mock.patch("py_rme_canary.core.version.subprocess.run",
                       side_effect=FileNotFoundError):
            result = _detect_git_hash()
            assert result == ""

    def test_handles_not_a_repo(self) -> None:
        mock_result = mock.Mock()
        mock_result.returncode = 128
        mock_result.stdout = ""
        with mock.patch("py_rme_canary.core.version.subprocess.run",
                       return_value=mock_result):
            result = _detect_git_hash()
            assert result == ""
