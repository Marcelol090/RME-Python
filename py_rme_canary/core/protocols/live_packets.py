"""
Live Editing Protocol Definitions.

Ported from source/live_packets.h
"""

import struct
from dataclasses import dataclass
from enum import IntEnum
from typing import Any


class PacketType(IntEnum):
    # Connection / Handshake
    LOGIN = 1
    LOGIN_ERROR = 2
    LOGIN_SUCCESS = 3

    # Map Operations
    NODE_CHANGE = 10
    NODE_ADD = 11
    NODE_REMOVE = 12
    TILE_UPDATE = 13
    MAP_REQUEST = 14
    MAP_CHUNK = 15

    # Chat / Interaction
    MESSAGE = 20
    CURSOR_UPDATE = 21
    CLIENT_LIST = 22
    KICK = 23


class ConnectionState(IntEnum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    AUTHENTICATED = 3


@dataclass
class NetworkHeader:
    version: int
    packet_type: int
    size: int

    @staticmethod
    def pack(version: int, packet_type: int, size: int) -> bytes:
        return struct.pack("<HHI", version, packet_type, size)

    @staticmethod
    def unpack(data: bytes) -> "NetworkHeader":
        return NetworkHeader(*struct.unpack("<HHI", data))


# -----------------------------------------------------------------------------
# Cursor payload encoding/decoding
# -----------------------------------------------------------------------------


def encode_cursor(client_id: int, x: int, y: int, z: int) -> bytes:
    """Encode cursor position for network transmission.

    Format: <client_id:u32><x:i32><y:i32><z:i16>
    """
    return struct.pack("<IiiH", int(client_id), int(x), int(y), int(z))


def decode_cursor(payload: bytes) -> tuple[int, int, int, int]:
    """Decode cursor position from network payload.

    Returns: (client_id, x, y, z)
    """
    if len(payload) < 14:
        return 0, 0, 0, 0
    client_id, x, y, z = struct.unpack("<IiiH", payload[:14])
    return int(client_id), int(x), int(y), int(z)


# -----------------------------------------------------------------------------
# Chat message encoding/decoding
# -----------------------------------------------------------------------------


def encode_chat(client_id: int, name: str, message: str) -> bytes:
    """Encode a chat message for broadcast."""
    name_bytes = str(name or "").encode("utf-8")
    msg_bytes = str(message or "").encode("utf-8")
    return struct.pack("<I", int(client_id)) + name_bytes + b"\0" + msg_bytes


def decode_chat(payload: bytes) -> tuple[int, str, str]:
    """Decode a chat message payload.

    Returns: (client_id, name, message)
    """
    if len(payload) < 4:
        return 0, "", ""
    client_id = int(struct.unpack("<I", payload[:4])[0])
    rest = payload[4:]
    name_bytes, sep, msg_bytes = rest.partition(b"\0")
    name = name_bytes.decode("utf-8", errors="ignore")
    message = msg_bytes.decode("utf-8", errors="ignore") if sep else ""
    return client_id, name, message


def decode_client_list(payload: bytes) -> list[dict[str, Any]]:
    """Decode client list payload into list of dicts.

    Returns:
        [{"client_id": int, "color": (r,g,b), "name": str}, ...]
    """
    if len(payload) < 2:
        return []

    count = struct.unpack("<H", payload[:2])[0]
    offset = 2
    clients: list[dict[str, Any]] = []
    for _ in range(count):
        if len(payload) < offset + 8:
            break
        client_id, r, g, b, name_len = struct.unpack("<I BBB B", payload[offset : offset + 8])
        offset += 8
        if len(payload) < offset + name_len:
            break
        name = payload[offset : offset + name_len].decode("utf-8", errors="ignore")
        offset += name_len
        clients.append(
            {
                "client_id": int(client_id),
                "color": (int(r), int(g), int(b)),
                "name": name,
            }
        )
    return clients
