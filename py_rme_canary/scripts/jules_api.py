#!/usr/bin/env python3
"""Lightweight Jules API client used by local quality workflows.

The module intentionally avoids third-party dependencies so it can run in
minimal CI/automation environments.
"""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://jules.googleapis.com/v1alpha"
_ENV_CANDIDATES = (".env", "py_rme_canary/.env")


class JulesAPIError(RuntimeError):
    """Raised when Jules API replies with an HTTP/network error."""

    def __init__(self, message: str, *, status: int | None = None, payload: object | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload


@dataclass(frozen=True, slots=True)
class JulesConfig:
    """Resolved Jules API configuration."""

    api_key: str
    source: str
    branch: str = "main"
    timeout_seconds: float = 30.0
    base_url: str = DEFAULT_BASE_URL

    def normalized_source(self) -> str:
        return normalize_source(self.source)


def normalize_source(source: str | None) -> str:
    """Normalize source to the expected `sources/...` format."""
    value = str(source or "").strip()
    if not value:
        return ""
    if value.startswith("sources/"):
        return value
    return f"sources/{value}"


def _strip_optional_quotes(value: str) -> str:
    raw = value.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]
    return raw


def read_env_file(path: Path) -> dict[str, str]:
    """Read KEY=VALUE pairs from an env file."""
    if not path.exists() or not path.is_file():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :].strip()
        key, raw_value = stripped.split("=", 1)
        key = key.strip()
        if not key:
            continue
        values[key] = _strip_optional_quotes(raw_value)
    return values


def load_env_defaults(project_root: Path, *, override: bool = False) -> dict[str, str]:
    """Load env variables from known project env files."""
    loaded: dict[str, str] = {}
    for relative in _ENV_CANDIDATES:
        env_path = project_root / relative
        for key, value in read_env_file(env_path).items():
            loaded[key] = value
            if override or key not in os.environ:
                os.environ[key] = value
    return loaded


def resolve_config(
    project_root: Path,
    *,
    source: str | None = None,
    branch: str | None = None,
    timeout_seconds: float = 30.0,
) -> JulesConfig:
    """Resolve JulesConfig from env + explicit arguments."""
    load_env_defaults(project_root, override=False)
    api_key = str(os.environ.get("JULES_API_KEY", "")).strip()
    selected_source = normalize_source(source or os.environ.get("JULES_SOURCE", ""))
    selected_branch = str(branch or os.environ.get("JULES_BRANCH", "main")).strip() or "main"

    if not api_key:
        raise ValueError("Missing JULES_API_KEY.")
    if not selected_source:
        raise ValueError("Missing JULES_SOURCE.")

    return JulesConfig(
        api_key=api_key,
        source=selected_source,
        branch=selected_branch,
        timeout_seconds=float(timeout_seconds),
    )


def _decode_json_payload(raw_data: bytes) -> object:
    body = raw_data.decode("utf-8", errors="replace").strip()
    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {"raw": body}


class JulesClient:
    """Small Jules API HTTP client."""

    def __init__(self, config: JulesConfig) -> None:
        self._config = config

    @property
    def config(self) -> JulesConfig:
        return self._config

    def _url(self, path: str, query: dict[str, Any] | None = None) -> str:
        normalized_path = path.lstrip("/")
        base = self._config.base_url.rstrip("/")
        url = f"{base}/{normalized_path}"
        if query:
            url = f"{url}?{urlencode(query)}"
        return url

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> object:
        body: bytes | None = None
        headers = {
            "x-goog-api-key": self._config.api_key,
            "Accept": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = Request(self._url(path, query=query), data=body, headers=headers, method=method.upper())
        try:
            with urlopen(request, timeout=self._config.timeout_seconds) as response:
                raw_data = response.read()
                return _decode_json_payload(raw_data)
        except HTTPError as exc:
            payload_obj = _decode_json_payload(exc.read()) if exc.fp else {}
            raise JulesAPIError(
                f"Jules API HTTP error {exc.code}",
                status=int(exc.code),
                payload=payload_obj,
            ) from exc
        except URLError as exc:
            raise JulesAPIError(f"Jules API network error: {exc.reason}") from exc

    def list_sources(self, *, page_size: int = 100, page_token: str = "") -> object:
        query: dict[str, Any] = {"pageSize": int(page_size)}
        token = str(page_token).strip()
        if token:
            query["pageToken"] = token
        return self._request("GET", "sources", query=query)

    def list_sessions(self, *, page_size: int = 50, page_token: str = "") -> object:
        query: dict[str, Any] = {"pageSize": int(page_size)}
        token = str(page_token).strip()
        if token:
            query["pageToken"] = token
        return self._request("GET", "sessions", query=query)

    def create_session(
        self,
        *,
        prompt: str,
        source: str | None = None,
        branch: str | None = None,
        require_plan_approval: bool = False,
        automation_mode: str | None = None,
    ) -> object:
        selected_source = normalize_source(source or self._config.source)
        selected_branch = str(branch or self._config.branch).strip() or "main"

        source_context: dict[str, Any] = {"source": selected_source}
        source_context["githubRepoContext"] = {"startingBranch": selected_branch}

        payload: dict[str, Any] = {
            "prompt": str(prompt),
            "sourceContext": source_context,
        }
        if require_plan_approval:
            payload["requirePlanApproval"] = True
        if automation_mode:
            payload["automationMode"] = str(automation_mode)

        return self._request("POST", "sessions", payload=payload)

    def get_session(self, session_name: str) -> object:
        normalized = normalize_session_name(session_name)
        if not normalized:
            raise ValueError("Session name is empty.")
        return self._request("GET", normalized)

    def list_session_activities(self, session_name: str, *, page_size: int = 20, page_token: str = "") -> object:
        normalized = normalize_session_name(session_name)
        if not normalized:
            raise ValueError("Session name is empty.")
        query: dict[str, Any] = {"pageSize": int(page_size)}
        token = str(page_token).strip()
        if token:
            query["pageToken"] = token
        return self._request("GET", f"{normalized}/activities", query=query)

    def get_latest_activity(self, session_name: str) -> object:
        normalized = normalize_session_name(session_name)
        if not normalized:
            raise ValueError("Session name is empty.")

        candidates = (
            f"{normalized}/activities:latest",
            f"{normalized}/activities",
        )
        last_error: JulesAPIError | None = None
        for path in candidates:
            try:
                if path.endswith("/activities"):
                    return self._request("GET", path, query={"pageSize": 1})
                return self._request("GET", path)
            except JulesAPIError as exc:
                last_error = exc
                if exc.status not in {400, 404, 405}:
                    break
        if last_error is None:
            raise JulesAPIError("Failed to retrieve session latest activity.")
        raise last_error

    def approve_plan(self, session_name: str) -> object:
        normalized = normalize_session_name(session_name)
        if not normalized:
            raise ValueError("Session name is empty.")
        return self._request("POST", f"{normalized}:approvePlan", payload={})

    def send_message(self, session_name: str, *, message: str) -> object:
        normalized = normalize_session_name(session_name)
        if not normalized:
            raise ValueError("Session name is empty.")
        text = str(message).strip()
        if not text:
            raise ValueError("Message is empty.")
        return self._request("POST", f"{normalized}:sendMessage", payload={"message": text})

    def source_exists(self, source_name: str) -> bool:
        normalized = normalize_source(source_name)
        response = self.list_sources()
        if not isinstance(response, dict):
            return False
        sources = response.get("sources", [])
        if not isinstance(sources, list):
            return False
        for entry in sources:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name", "")).strip()
            if not name:
                continue
            if name == normalized:
                return True
            if name.endswith(f"/{normalized}"):
                return True
        return False


def normalize_session_name(value: str | None) -> str:
    """Normalize session identifier to `sessions/<id>` format."""
    raw = str(value or "").strip()
    if not raw:
        return ""
    if raw.startswith("sessions/"):
        return raw
    if "/sessions/" in raw:
        return f"sessions/{raw.split('/sessions/', 1)[1]}"
    return f"sessions/{raw}"


def write_json(path: Path, payload: object) -> None:
    """Write JSON payload to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def resolve_git_branch(project_root: Path) -> str:
    """Resolve current git branch with a safe fallback."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(project_root),
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        return "main"
    if completed.returncode != 0:
        return "main"
    branch = completed.stdout.strip()
    return branch or "main"
