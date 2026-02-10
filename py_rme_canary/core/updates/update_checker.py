"""Asynchronous update checker against the release manifest endpoint.

Fetches the update manifest JSON from a configurable URL, compares
versions with the running build, and emits a typed result.  Designed
for non-blocking use (runs in a background thread via
concurrent.futures).
"""
from __future__ import annotations

import hashlib
import json
import logging
import urllib.request
import urllib.error
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Final

from py_rme_canary.core.version import BuildInfo, get_build_info

logger: Final = logging.getLogger(__name__)

# Default manifest endpoints per channel.
_DEFAULT_MANIFEST_URLS: Final[dict[str, str]] = {
    "stable": "https://py-rme-canary.dev/releases/stable/manifest.json",
    "beta": "https://py-rme-canary.dev/releases/beta/manifest.json",
    "nightly": "https://py-rme-canary.dev/releases/nightly/manifest.json",
}

_TIMEOUT_SECONDS: Final[int] = 10


@dataclass(frozen=True, slots=True)
class UpdateAsset:
    """A downloadable artifact from the manifest."""
    name: str
    size: int
    sha256: str
    download_url: str


@dataclass(frozen=True, slots=True)
class UpdateCheckResult:
    """Result of a single update check."""
    available: bool
    current_version: str
    latest_version: str = ""
    channel: str = ""
    assets: tuple[UpdateAsset, ...] = ()
    error: str = ""


def _parse_manifest(raw: bytes) -> dict[str, Any]:
    """Parse and minimally validate the manifest JSON."""
    data: dict[str, Any] = json.loads(raw)
    if "version" not in data or "assets" not in data:
        raise ValueError("Manifest missing required fields: version, assets")
    return data


def _version_from_string(version_str: str) -> BuildInfo:
    """Parse a SemVer string like '3.1.0-beta.1' into a BuildInfo."""
    pre = ""
    if "-" in version_str:
        version_str, pre = version_str.split("-", 1)
    parts = version_str.split(".")
    major = int(parts[0]) if len(parts) > 0 else 0
    minor = int(parts[1]) if len(parts) > 1 else 0
    patch = int(parts[2]) if len(parts) > 2 else 0
    return BuildInfo(major=major, minor=minor, patch=patch, pre=pre)


def check_for_updates(
    *,
    manifest_url: str | None = None,
    current: BuildInfo | None = None,
) -> UpdateCheckResult:
    """Synchronously check for available updates.

    Parameters
    ----------
    manifest_url:
        Override the manifest URL. If None, the URL is derived
        from the current channel.
    current:
        Override the running version. If None, get_build_info()
        is used.

    Returns
    -------
    UpdateCheckResult
        Always returns a result (never raises). Errors are captured
        in the error field.
    """
    if current is None:
        current = get_build_info()

    url = manifest_url or _DEFAULT_MANIFEST_URLS.get(
        current.channel, _DEFAULT_MANIFEST_URLS["stable"]
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": current.user_agent},
        )
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            raw = resp.read()

        data = _parse_manifest(raw)
        latest_version_str: str = str(data["version"])
        latest = _version_from_string(latest_version_str)

        assets: list[UpdateAsset] = []
        for a in data.get("assets", []):
            assets.append(UpdateAsset(
                name=str(a.get("name", "")),
                size=int(a.get("size", 0)),
                sha256=str(a.get("sha256", "")),
                download_url=str(a.get("download_url", "")),
            ))

        available = latest.is_newer_than(current)

        return UpdateCheckResult(
            available=available,
            current_version=current.semver,
            latest_version=latest_version_str,
            channel=str(data.get("channel", current.channel)),
            assets=tuple(assets),
        )

    except urllib.error.URLError as exc:
        logger.debug("Update check network error: %s", exc)
        return UpdateCheckResult(
            available=False,
            current_version=current.semver,
            error=f"Network error: {exc.reason}",
        )
    except Exception as exc:
        logger.debug("Update check failed: %s", exc)
        return UpdateCheckResult(
            available=False,
            current_version=current.semver,
            error=str(exc),
        )


class UpdateChecker:
    """Non-blocking update checker using a thread pool.

    Usage::

        checker = UpdateChecker()
        future = checker.check_async()
        # ... later ...
        result = future.result(timeout=15)
    """

    def __init__(self, *, manifest_url: str | None = None) -> None:
        self._manifest_url = manifest_url
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="update-check")

    def check_async(self, *, current: BuildInfo | None = None) -> Future[UpdateCheckResult]:
        """Submit an async update check. Returns a Future."""
        return self._pool.submit(
            check_for_updates,
            manifest_url=self._manifest_url,
            current=current,
        )

    def shutdown(self) -> None:
        """Gracefully shutdown the thread pool."""
        self._pool.shutdown(wait=False)
