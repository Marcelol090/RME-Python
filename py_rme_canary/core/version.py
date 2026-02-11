"""Single source of truth for application version and build metadata.

Provides a frozen dataclass with the current version, channel, and
optional build metadata (commit hash, build date) that can be injected
at build time via environment variables or the release script.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from typing import Final

# Authoritative version — bump here for releases.
_MAJOR: Final[int] = 3
_MINOR: Final[int] = 0
_PATCH: Final[int] = 0
_PRE: Final[str] = ""  # e.g. "beta.1", "rc.1", "" for stable


@dataclass(frozen=True, slots=True)
class BuildInfo:
    """Immutable snapshot of version + build metadata."""

    major: int = _MAJOR
    minor: int = _MINOR
    patch: int = _PATCH
    pre: str = _PRE
    channel: str = "beta"
    commit_hash: str = ""
    build_date: str = ""
    build_number: int = 0

    # ── Derived properties ────────────────────────────────────────

    @property
    def semver(self) -> str:
        """Return full SemVer string, e.g. '3.0.0-beta.1'."""
        base = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            return f"{base}-{self.pre}"
        return base

    @property
    def short_version(self) -> str:
        """Return 'major.minor.patch'."""
        return f"{self.major}.{self.minor}.{self.patch}"

    @property
    def display_name(self) -> str:
        """Human-friendly display string."""
        return f"Canary Map Editor v{self.semver}"

    @property
    def user_agent(self) -> str:
        """User-agent string for HTTP requests."""
        return f"PyRME-Canary/{self.semver}"

    @property
    def version_tuple(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def is_newer_than(self, other: BuildInfo) -> bool:
        """Return True if *self* is a newer version than *other*."""
        if self.version_tuple != other.version_tuple:
            return self.version_tuple > other.version_tuple
        # Same numeric version: stable > pre-release
        if self.pre and not other.pre:
            return False
        if not self.pre and other.pre:
            return True
        return self.pre > other.pre


def _detect_git_hash() -> str:
    """Best-effort git commit short hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


@lru_cache(maxsize=1)
def get_build_info() -> BuildInfo:
    """Return the singleton BuildInfo for this process.

    Build-time overrides via environment variables:
    - PYRME_CHANNEL: release channel (stable/beta/nightly)
    - PYRME_COMMIT: git commit hash
    - PYRME_BUILD_DATE: ISO-8601 build date
    - PYRME_BUILD_NUMBER: CI build number
    """
    return BuildInfo(
        channel=os.getenv("PYRME_CHANNEL", "beta"),
        commit_hash=os.getenv("PYRME_COMMIT", _detect_git_hash()),
        build_date=os.getenv("PYRME_BUILD_DATE", ""),
        build_number=int(os.getenv("PYRME_BUILD_NUMBER", "0")),
    )


# Convenience alias
APP_VERSION: Final[str] = f"{_MAJOR}.{_MINOR}.{_PATCH}"
