"""
Live Editing Protocol Definitions.

Ported from source/live_packets.h
"""

import struct
from dataclasses import dataclass
from enum import IntEnum


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

    # Chat / Interaction
    MESSAGE = 20
    CURSOR_UPDATE = 21


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
