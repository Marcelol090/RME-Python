"""Canary Map Editor - Auto Updater.

This module provides a small, dependency-light update checker.

Legacy reference: source/updater.cpp
"""

from __future__ import annotations

import json
import logging
import platform
import re
import threading
import urllib.request
from urllib.parse import urlparse
from collections.abc import Callable
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class UpdateInfo:
    latest_version: str
    url: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateCheckResult:
    is_update_available: bool
    current_version: str
    info: UpdateInfo | None
    raw: str | None = None
    error: str | None = None


FetchFunc = Callable[[str, float], bytes]


class Updater:
    """Checks for updates and optionally triggers a self-update flow.

    The API keeps `check_for_updates()` for compatibility, but the preferred API is `check()`.
    """

    # Default: GitHub releases API (override in app config)
    UPDATE_URL = "https://api.github.com/repos/your-team/py-rme-canary/releases/latest"

    def __init__(
        self,
        *,
        current_version: str | None = None,
        update_url: str | None = None,
        timeout_s: float = 5.0,
        fetch: FetchFunc | None = None,
    ) -> None:
        self.current_version = current_version or self._detect_current_version() or "0.0.0"
        self.update_url = update_url or self.UPDATE_URL
        self.timeout_s = timeout_s
        self._fetch: FetchFunc = fetch or self._default_fetch
        self.last_result: UpdateCheckResult | None = None

    def check_for_updates(self) -> bool:
        """Compatibility wrapper.

        Returns True if a newer version is available.
        Details are available in `last_result`.
        """
        self.last_result = self.check()
        return self.last_result.is_update_available

    def check(self) -> UpdateCheckResult:
        """Performs a synchronous update check."""
        log.info("Checking for updates...")
        try:
            raw_bytes = self._fetch(self.update_url, self.timeout_s)
            raw = raw_bytes.decode("utf-8", errors="replace")
            info = self._parse_update_response(raw_bytes, raw)
            if info is None:
                return UpdateCheckResult(
                    is_update_available=False,
                    current_version=self.current_version,
                    info=None,
                    raw=raw,
                    error="Could not parse update response",
                )

            is_newer = self._is_version_newer(info.latest_version, self.current_version)
            return UpdateCheckResult(
                is_update_available=is_newer,
                current_version=self.current_version,
                info=info,
                raw=raw,
                error=None,
            )
        except Exception as e:
            log.error("Update check failed: %s", e)
            return UpdateCheckResult(
                is_update_available=False,
                current_version=self.current_version,
                info=None,
                raw=None,
                error=str(e),
            )

    def check_async(self, callback: Callable[[UpdateCheckResult], None]) -> threading.Thread:
        """Runs update check on a background thread and invokes callback with the result."""

        def _worker() -> None:
            result = self.check()
            self.last_result = result
            try:
                callback(result)
            except Exception as e:  # pragma: no cover
                log.exception("Updater callback failed: %s", e)

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread

    def perform_update(self) -> None:
        """Best-effort update trigger.

        The legacy editor shipped platform-specific updaters. Here we keep this as a hook.
        If we have a URL from the last check, we log it so the UI can open it.
        """
        url = self.last_result.info.url if (self.last_result and self.last_result.info) else None
        if platform.system() == "Windows":
            log.info("Starting Windows updater hook...")
        else:
            log.info("Starting Unix updater hook...")

        if url:
            log.info("Update URL: %s", url)

    @staticmethod
    def build_legacy_url(*, base: str, os_name: str, version_id: str, beta: bool = False) -> str:
        """Builds a legacy-style update.php URL (mirrors source/updater.cpp)."""
        suffix = "&beta" if beta else ""
        return f"{base}?os={os_name}&verid={version_id}{suffix}"

    @staticmethod
    def _default_fetch(url: str, timeout_s: float) -> bytes:
        safe_url = Updater._validate_update_url(url)
        req = urllib.request.Request(
            safe_url,
            headers={
                "User-Agent": "py-rme-canary-updater/1.0",
                "Accept": "application/json, text/plain, */*",
            },
        )
        # Scheme validated above; only http/https allowed.
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # nosec B310
            return resp.read()

    @staticmethod
    def _detect_current_version() -> str | None:
        """Best-effort version detection for installed distributions."""
        try:
            from importlib.metadata import PackageNotFoundError, version

            try:
                return version("py-rme-canary")
            except PackageNotFoundError:
                return None
        except Exception:
            return None

    @staticmethod
    def _parse_update_response(raw_bytes: bytes, raw_text: str) -> UpdateInfo | None:
        """Parses update response into UpdateInfo.

        Supported formats:
        - GitHub release JSON: {"tag_name": "v1.2.3", "html_url": "...", "body": "..."}
        - Plain text: first version-like token wins, optionally with a URL in the same string.
        """
        # Try JSON first
        try:
            decoded = json.loads(raw_bytes.decode("utf-8"))
            if isinstance(decoded, dict):
                tag = decoded.get("tag_name") or decoded.get("name")
                if isinstance(tag, str) and tag.strip():
                    latest_version = tag.strip().lstrip("v")
                    url = decoded.get("html_url") or decoded.get("url")
                    notes = decoded.get("body")
                    return UpdateInfo(latest_version=latest_version, url=url, notes=notes)
        except Exception:
            pass

        # Fallback: plaintext
        # Common patterns: "1.2.3" or "ver=1.2.3" or "1.2.3|https://..."
        version_match = re.search(r"\b(\d+)(?:\.(\d+))?(?:\.(\d+))?\b", raw_text)
        if not version_match:
            return None

        major = version_match.group(1) or "0"
        minor = version_match.group(2) or "0"
        patch = version_match.group(3) or "0"
        latest_version = f"{int(major)}.{int(minor)}.{int(patch)}"

        url_match = re.search(r"https?://\S+", raw_text)
        url = url_match.group(0) if url_match else None
        return UpdateInfo(latest_version=latest_version, url=url)

    @staticmethod
    def _is_version_newer(latest: str, current: str) -> bool:
        return Updater._version_key(latest) > Updater._version_key(current)

    @staticmethod
    def _version_key(version_str: str) -> tuple[int, int, int, int, str]:
        """Converts version to a sortable key.

        Ensures release versions sort above prereleases when the numeric parts match,
        e.g. "1.0.0" > "1.0.0-beta".
        """
        cleaned = version_str.strip().lstrip("v")
        match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-+](.+))?$", cleaned)
        if not match:
            return (0, 0, 0, 0, cleaned)

        major = int(match.group(1) or 0)
        minor = int(match.group(2) or 0)
        patch = int(match.group(3) or 0)
        suffix = match.group(4) or ""
        is_release = 1 if suffix == "" else 0
        return (major, minor, patch, is_release, suffix)

    @staticmethod
    def _validate_update_url(url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"https", "http"}:
            raise ValueError(f"Unsupported update URL scheme: {parsed.scheme!r}")
        if not parsed.netloc:
            raise ValueError("Invalid update URL: missing host")
        return url


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    u = Updater()
    result = u.check()
    if result.is_update_available:
        u.perform_update()
    else:
        print("No updates available.")
