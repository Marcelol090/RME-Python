"""Tile serialization for live collaboration network transfer.

Provides encoding/decoding of tile data for network transmission.
Used by MAP_CHUNK packets during initial map synchronization.

Layer: core (no PyQt6 imports)
"""

from __future__ import annotations

import struct
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import Optional  # noqa: F401 - placeholder for future type hints

TILE_UPDATE_MAGIC = b"TUP1"


def encode_tile(tile: Any) -> bytes:
    """Encode a tile object for network transfer.

    Format:
        <x:i32><y:i32><z:u8><flags:u8><item_count:u16>
        [<item_id:u16><subtype:u8>] * item_count
        <ground_id:u16>  (0 if none)

    Args:
        tile: Tile object with x, y, z, items, ground attributes

    Returns:
        Encoded bytes
    """
    if tile is None:
        return b""

    x = int(getattr(tile, "x", 0))
    y = int(getattr(tile, "y", 0))
    z = int(getattr(tile, "z", 0))

    ground = getattr(tile, "ground", None)
    house_id = getattr(tile, "house_id", None)

    # Flags: 1 if ground exists, 2 if house id exists (parity with tests)
    flags = 0
    if ground is not None:
        flags |= 1
    if house_id is not None:
        flags |= 2

    # Get items
    items = getattr(tile, "items", None) or []
    item_count = min(len(items), 0xFFFF)

    data = struct.pack("<iiB B H", x, y, z, flags, item_count)

    # Encode items
    for item in items[:item_count]:
        item_id = int(getattr(item, "id", 0))
        subtype = int(getattr(item, "subtype", 0) or getattr(item, "count", 1))
        data += struct.pack("<HB", item_id, subtype)

    # Ground ID
    ground_id = int(getattr(ground, "id", 0)) if ground else 0
    data += struct.pack("<H", ground_id)

    # Optional fields
    if house_id is not None:
        data += struct.pack("<I", int(house_id or 0))

    return data


def decode_tile(payload: bytes, offset: int = 0) -> tuple[dict[str, Any], int]:
    """Decode a tile from network payload.

    Args:
        payload: Bytes containing tile data
        offset: Starting position in payload

    Returns:
        (tile_dict, new_offset) tuple
    """
    if len(payload) < offset + 12:
        return {}, offset

    x, y, z, flags, item_count = struct.unpack("<iiB B H", payload[offset : offset + 12])
    offset += 12

    items: list[dict[str, int]] = []
    tile = {
        "x": int(x),
        "y": int(y),
        "z": int(z),
        "flags": int(flags),
        "items": items,
        "ground_id": 0,
        "house_id": None,
    }

    # Decode items
    for _ in range(item_count):
        if len(payload) < offset + 3:
            break
        item_id, subtype = struct.unpack("<HB", payload[offset : offset + 3])
        offset += 3
        items.append({"id": int(item_id), "subtype": int(subtype)})

    # Ground ID
    if len(payload) >= offset + 2:
        tile["ground_id"] = int(struct.unpack("<H", payload[offset : offset + 2])[0])
        offset += 2

    # House ID (read if available, independent of flags for compatibility)
    if len(payload) >= offset + 4:
        tile["house_id"] = int(struct.unpack("<I", payload[offset : offset + 4])[0])
        offset += 4

    return tile, offset


def encode_tile_update(tiles: list[Any]) -> bytes:
    """Encode a TILE_UPDATE payload containing full tile data.

    Format:
        <magic:4 bytes> <tile_count:u16> [tile_data...] * tile_count
    """
    tile_count = min(len(tiles), 0xFFFF)
    data = bytearray()
    data += TILE_UPDATE_MAGIC
    data += struct.pack("<H", int(tile_count))
    for tile in tiles[:tile_count]:
        data += encode_tile(tile)
    return bytes(data)


def decode_tile_update(payload: bytes) -> tuple[list[dict[str, Any]], bool]:
    """Decode a TILE_UPDATE payload into tile dicts.

    Returns:
        (tiles, ok)
    """
    if len(payload) < 6 or payload[:4] != TILE_UPDATE_MAGIC:
        return [], False

    count = int(struct.unpack("<H", payload[4:6])[0])
    offset = 6
    tiles: list[dict[str, Any]] = []
    for _ in range(count):
        tile, offset = decode_tile(payload, offset)
        if not tile:
            break
        tiles.append(tile)
    return tiles, True


def encode_map_chunk(
    chunk_id: int,
    total_chunks: int,
    tiles: list[Any],
    *,
    x_min: int = 0,
    y_min: int = 0,
    z: int = 0,
) -> bytes:
    """Encode a chunk of tiles for MAP_CHUNK packet.

    Format:
        <chunk_id:u32><total_chunks:u32><tile_count:u16>
        <x_min:i32><y_min:i32><z:u8>
        [tile_data...] * tile_count

    Args:
        chunk_id: Current chunk number (0-indexed)
        total_chunks: Total number of chunks
        tiles: List of tile objects to encode
        x_min: Minimum X coordinate of chunk
        y_min: Minimum Y coordinate of chunk
        z: Z level of chunk

    Returns:
        Encoded bytes
    """
    tile_count = min(len(tiles), 0xFFFF)
    header = struct.pack(
        "<I I H iiB",
        int(chunk_id),
        int(total_chunks),
        tile_count,
        int(x_min),
        int(y_min),
        int(z),
    )

    data = header
    for tile in tiles[:tile_count]:
        data += encode_tile(tile)

    return data


def decode_map_chunk(payload: bytes) -> dict[str, Any]:
    """Decode a MAP_CHUNK packet.

    Returns:
        dict with chunk_id, total_chunks, tiles, x_min, y_min, z
    """
    if len(payload) < 19:
        return {"chunk_id": 0, "total_chunks": 0, "tiles": [], "x_min": 0, "y_min": 0, "z": 0}

    chunk_id, total_chunks, tile_count, x_min, y_min, z = struct.unpack("<I I H iiB", payload[:19])

    tiles: list[dict[str, Any]] = []
    result = {
        "chunk_id": int(chunk_id),
        "total_chunks": int(total_chunks),
        "tiles": tiles,
        "x_min": int(x_min),
        "y_min": int(y_min),
        "z": int(z),
    }

    offset = 19
    for _ in range(tile_count):
        tile, offset = decode_tile(payload, offset)
        if tile:
            tiles.append(tile)

    return result


def encode_map_request(x_min: int, y_min: int, x_max: int, y_max: int, z: int) -> bytes:
    """Encode a MAP_REQUEST packet.

    Format: <x_min:i32><y_min:i32><x_max:i32><y_max:i32><z:u8>
    """
    return struct.pack("<iiiiB", int(x_min), int(y_min), int(x_max), int(y_max), int(z))


def decode_map_request(payload: bytes) -> tuple[int, int, int, int, int]:
    """Decode a MAP_REQUEST packet.

    Returns:
        (x_min, y_min, x_max, y_max, z)
    """
    if len(payload) < 17:
        return 0, 0, 0, 0, 0
    x_min, y_min, x_max, y_max, z = struct.unpack("<iiiiB", payload[:17])
    return int(x_min), int(y_min), int(x_max), int(y_max), int(z)
