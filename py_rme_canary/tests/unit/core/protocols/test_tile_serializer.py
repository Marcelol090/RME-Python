from __future__ import annotations

from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.protocols.tile_serializer import decode_tile_update, encode_tile_update


def test_tile_update_roundtrip_single_tile() -> None:
    tile = Tile(
        x=10,
        y=20,
        z=7,
        ground=Item(id=100),
        items=[Item(id=200, subtype=3)],
        house_id=5,
        map_flags=4,
    )

    payload = encode_tile_update([tile])
    tiles, ok = decode_tile_update(payload)

    assert ok is True
    assert len(tiles) == 1
    decoded = tiles[0]
    assert decoded["x"] == 10
    assert decoded["y"] == 20
    assert decoded["z"] == 7
    assert decoded["ground_id"] == 100
    assert decoded["house_id"] == 5
    # Flags = 1 (Has Ground) | 2 (Has House) = 3
    assert decoded["flags"] == 3
    assert decoded["items"][0]["id"] == 200
    assert decoded["items"][0]["subtype"] == 3


def test_tile_update_roundtrip_empty_tile() -> None:
    tile = Tile(x=1, y=2, z=3)
    payload = encode_tile_update([tile])
    tiles, ok = decode_tile_update(payload)

    assert ok is True
    assert len(tiles) == 1
    decoded = tiles[0]
    assert decoded["x"] == 1
    assert decoded["y"] == 2
    assert decoded["z"] == 3
    assert decoded["ground_id"] == 0
    assert decoded["items"] == []


def test_tile_update_decode_invalid_payload() -> None:
    tiles, ok = decode_tile_update(b"\x00\x01\x02\x03")
    assert ok is False
    assert tiles == []
