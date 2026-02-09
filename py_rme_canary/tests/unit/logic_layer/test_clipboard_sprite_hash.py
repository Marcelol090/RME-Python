"""Tests for sprite-hash-aware system clipboard conversion."""

from __future__ import annotations

from dataclasses import dataclass, field

from py_rme_canary.logic_layer.clipboard import ClipboardManager


@dataclass
class _MockItem:
    id: int
    count: int = 1


@dataclass
class _MockTile:
    x: int
    y: int
    z: int
    ground: _MockItem | None = None
    items: list[_MockItem] = field(default_factory=list)
    monsters: list = field(default_factory=list)
    npc: object | None = None
    spawn_monster: object | None = None
    spawn_npc: object | None = None
    house_id: int | None = None
    map_flags: int = 0


def test_copy_tiles_writes_sprite_hash_payload() -> None:
    manager = ClipboardManager.instance()
    manager.clear()

    tile = _MockTile(
        x=10,
        y=20,
        z=7,
        ground=_MockItem(id=100),
        items=[_MockItem(id=200)],
    )
    manager.copy_tiles(
        [tile],
        origin=(10, 20, 7),
        sprite_hash_lookup=lambda sid: {100: 111_000, 200: 222_000}.get(int(sid)),
    )

    entry = manager.get_current()
    assert entry is not None
    assert len(entry.data) == 1

    td = entry.data[0]
    assert td.ground_sprite_hash == 111_000
    assert td.items[0]["sprite_hash"] == 222_000


def test_convert_data_prefers_sprite_hash_over_name() -> None:
    manager = ClipboardManager.instance()
    manager.clear()

    payload = {
        "tiles": [
            {
                "ground_id": 10,
                "ground_name": "grass",
                "ground_sprite_hash": 9001,
                "items": [{"id": 20, "name": "stone", "sprite_hash": 9002}],
            }
        ],
        "items": [],
    }

    manager._convert_data(
        payload,
        source_v="13.x",
        target_v="10.x",
        name_resolver=lambda name: {"grass": 101, "stone": 201}.get(str(name)),
        hash_resolver=lambda h, _old, _name: {9001: 333, 9002: 444}.get(int(h)),
    )

    assert payload["tiles"][0]["ground_id"] == 333
    assert payload["tiles"][0]["items"][0]["id"] == 444


def test_convert_data_falls_back_to_name_when_hash_missing() -> None:
    manager = ClipboardManager.instance()
    manager.clear()

    payload = {
        "tiles": [
            {
                "ground_id": 10,
                "ground_name": "grass",
                "items": [{"id": 20, "name": "stone"}],
            }
        ],
        "items": [],
    }

    manager._convert_data(
        payload,
        source_v="13.x",
        target_v="10.x",
        name_resolver=lambda name: {"grass": 101, "stone": 201}.get(str(name)),
        hash_resolver=lambda _h, _old, _name: None,
    )

    assert payload["tiles"][0]["ground_id"] == 101
    assert payload["tiles"][0]["items"][0]["id"] == 201
