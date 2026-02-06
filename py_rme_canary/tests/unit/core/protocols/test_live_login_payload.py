from __future__ import annotations

from py_rme_canary.core.protocols.live_client import _encode_login_payload
from py_rme_canary.core.protocols.live_server import _decode_login_payload


def test_login_payload_roundtrip() -> None:
    payload = _encode_login_payload("alice", "secret")
    name, password = _decode_login_payload(payload)
    assert name == "alice"
    assert password == "secret"  # nosec


def test_login_payload_empty_password() -> None:
    payload = _encode_login_payload("bob", "")
    name, password = _decode_login_payload(payload)
    assert name == "bob"
    assert password == ""  # nosec


def test_login_payload_without_separator() -> None:
    name, password = _decode_login_payload(b"plain")
    assert name == "plain"
    assert password == ""  # nosec
