"""Tests for core.protocols.live_packets encoding/decoding."""

from __future__ import annotations

import struct

import pytest

from py_rme_canary.core.protocols.live_packets import (
    ConnectionState,
    NetworkHeader,
    PacketType,
    decode_chat,
    decode_client_list,
    decode_cursor,
    encode_chat,
    encode_cursor,
)


# --- PacketType enum ---


class TestPacketType:
    def test_login_value(self) -> None:
        assert int(PacketType.LOGIN) == 1

    def test_cursor_update_value(self) -> None:
        assert int(PacketType.CURSOR_UPDATE) == 21

    def test_all_types_unique(self) -> None:
        values = [int(pt) for pt in PacketType]
        assert len(values) == len(set(values))


# --- ConnectionState enum ---


class TestConnectionState:
    def test_ordering(self) -> None:
        assert ConnectionState.DISCONNECTED < ConnectionState.CONNECTING
        assert ConnectionState.CONNECTING < ConnectionState.CONNECTED
        assert ConnectionState.CONNECTED < ConnectionState.AUTHENTICATED


# --- NetworkHeader ---


class TestNetworkHeader:
    def test_pack_unpack_roundtrip(self) -> None:
        data = NetworkHeader.pack(1, 21, 14)
        h = NetworkHeader.unpack(data)
        assert h.version == 1
        assert h.packet_type == 21
        assert h.size == 14

    def test_pack_length(self) -> None:
        data = NetworkHeader.pack(1, 1, 0)
        assert len(data) == 8  # HHI = 2+2+4

    def test_zero_size(self) -> None:
        data = NetworkHeader.pack(1, 1, 0)
        h = NetworkHeader.unpack(data)
        assert h.size == 0


# --- Cursor encoding ---


class TestCursorEncoding:
    def test_roundtrip(self) -> None:
        payload = encode_cursor(42, 1000, 2000, 7)
        cid, x, y, z = decode_cursor(payload)
        assert cid == 42
        assert x == 1000
        assert y == 2000
        assert z == 7

    def test_negative_coords(self) -> None:
        payload = encode_cursor(1, -100, -200, 0)
        cid, x, y, z = decode_cursor(payload)
        assert x == -100
        assert y == -200

    def test_decode_short_payload(self) -> None:
        cid, x, y, z = decode_cursor(b"\x00\x01")
        assert cid == 0
        assert x == 0

    def test_payload_length(self) -> None:
        payload = encode_cursor(1, 0, 0, 0)
        assert len(payload) == 14  # I + i + i + H = 4+4+4+2


# --- Chat encoding ---


class TestChatEncoding:
    def test_roundtrip(self) -> None:
        payload = encode_chat(5, "Alice", "Hello!")
        cid, name, msg = decode_chat(payload)
        assert cid == 5
        assert name == "Alice"
        assert msg == "Hello!"

    def test_empty_message(self) -> None:
        payload = encode_chat(1, "Bob", "")
        cid, name, msg = decode_chat(payload)
        assert name == "Bob"
        assert msg == ""

    def test_unicode_message(self) -> None:
        payload = encode_chat(1, "日本語", "こんにちは")
        cid, name, msg = decode_chat(payload)
        assert name == "日本語"
        assert msg == "こんにちは"

    def test_decode_short_payload(self) -> None:
        cid, name, msg = decode_chat(b"\x01")
        assert cid == 0
        assert name == ""
        assert msg == ""


# --- Client list decoding ---


class TestClientListDecoding:
    def test_decode_empty(self) -> None:
        result = decode_client_list(b"")
        assert result == []

    def test_decode_single_client(self) -> None:
        # Build payload: count=1, then client_id=7, r=255, g=0, b=0, name_len=3, name="Bob"
        count = struct.pack("<H", 1)
        client_data = struct.pack("<I BBB B", 7, 255, 0, 0, 3) + b"Bob"
        payload = count + client_data
        result = decode_client_list(payload)
        assert len(result) == 1
        assert result[0]["client_id"] == 7
        assert result[0]["color"] == (255, 0, 0)
        assert result[0]["name"] == "Bob"

    def test_decode_multiple_clients(self) -> None:
        count = struct.pack("<H", 2)
        c1 = struct.pack("<I BBB B", 1, 255, 0, 0, 3) + b"One"
        c2 = struct.pack("<I BBB B", 2, 0, 255, 0, 3) + b"Two"
        result = decode_client_list(count + c1 + c2)
        assert len(result) == 2
        assert result[0]["name"] == "One"
        assert result[1]["name"] == "Two"

    def test_decode_truncated(self) -> None:
        count = struct.pack("<H", 5)  # Claims 5 clients
        c1 = struct.pack("<I BBB B", 1, 0, 0, 0, 1) + b"A"
        result = decode_client_list(count + c1)
        assert len(result) == 1  # Only 1 fully decodable