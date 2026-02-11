from __future__ import annotations

import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import jules_api  # type: ignore[import-not-found]


def _config() -> jules_api.JulesConfig:
    api_key = os.getenv("TEST_JULES_API_KEY", "dummy_key_for_testing")
    return jules_api.JulesConfig(api_key=api_key, source="sources/github/org/repo", branch="main")


def test_jules_client_list_methods_pass_query(monkeypatch) -> None:
    captured: list[tuple[str, str, object, object]] = []

    def _fake_request(self, method: str, path: str, *, payload=None, query=None):  # noqa: ANN001
        captured.append((method, path, payload, query))
        return {}

    monkeypatch.setattr(jules_api.JulesClient, "_request", _fake_request, raising=True)
    client = jules_api.JulesClient(_config())
    client.list_sources(page_size=25, page_token="tok1")
    client.list_sessions(page_size=15, page_token="tok2")
    client.list_session_activities("sessions/abc", page_size=10, page_token="tok3")

    assert captured[0] == ("GET", "sources", None, {"pageSize": 25, "pageToken": "tok1"})
    assert captured[1] == ("GET", "sessions", None, {"pageSize": 15, "pageToken": "tok2"})
    assert captured[2] == ("GET", "sessions/abc/activities", None, {"pageSize": 10, "pageToken": "tok3"})


def test_jules_client_action_methods_paths(monkeypatch) -> None:
    captured: list[tuple[str, str, object, object]] = []

    def _fake_request(self, method: str, path: str, *, payload=None, query=None):  # noqa: ANN001
        captured.append((method, path, payload, query))
        return {"ok": True}

    monkeypatch.setattr(jules_api.JulesClient, "_request", _fake_request, raising=True)
    client = jules_api.JulesClient(_config())
    client.approve_plan("abc123")
    client.send_message("sessions/abc123", message="continue")

    assert captured[0][0] == "POST"
    assert captured[0][1] == "sessions/abc123:approvePlan"
    assert captured[1][1] == "sessions/abc123:sendMessage"
    assert captured[1][2] == {"prompt": "continue"}


def test_get_latest_activity_falls_back_to_activities_list(monkeypatch) -> None:
    calls: list[str] = []

    def _fake_request(self, method: str, path: str, *, payload=None, query=None):  # noqa: ANN001
        calls.append(path)
        if path.endswith(":latest"):
            raise jules_api.JulesAPIError("missing", status=404)
        return {"activities": [{"name": "act-1"}]}

    monkeypatch.setattr(jules_api.JulesClient, "_request", _fake_request, raising=True)
    client = jules_api.JulesClient(_config())
    payload = client.get_latest_activity("abc123")
    assert payload == {"activities": [{"name": "act-1"}]}
    assert calls[0].endswith(":latest")
    assert calls[1].endswith("/activities")
