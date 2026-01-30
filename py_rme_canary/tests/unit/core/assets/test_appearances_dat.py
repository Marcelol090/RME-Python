from __future__ import annotations

import json

from py_rme_canary.core.assets.appearances_dat import load_appearances_dat, resolve_appearances_path


def _varint(value: int) -> bytes:
    out = bytearray()
    v = int(value)
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


def _key(field_number: int, wire_type: int) -> bytes:
    return _varint((int(field_number) << 3) | int(wire_type))


def test_load_appearances_dat_minimal(tmp_path) -> None:
    sprite_info = _key(5, 0) + _varint(555)
    frame_group = _key(3, 2) + _varint(len(sprite_info)) + sprite_info
    appearance = _key(1, 0) + _varint(100) + _key(2, 2) + _varint(len(frame_group)) + frame_group
    appearances = _key(1, 2) + _varint(len(appearance)) + appearance

    path = tmp_path / "appearances.dat"
    path.write_bytes(appearances)

    idx = load_appearances_dat(path)
    assert idx.get_sprite_id(100, kind="object") == 555


def test_resolve_appearances_path(tmp_path) -> None:
    assets = tmp_path / "assets"
    assets.mkdir()
    ap = assets / "appearances-test.dat"
    ap.write_bytes(b"\x00")
    catalog = [
        {
            "type": "appearances",
            "file": "appearances-test.dat",
        }
    ]
    (assets / "catalog-content.json").write_text(json.dumps(catalog), encoding="utf-8")

    resolved = resolve_appearances_path(assets)
    assert resolved == ap.resolve()


def test_animation_phase_selection(tmp_path) -> None:
    # Two phases: 100ms then 200ms, sprite ids 111 -> 222.
    phase0 = _key(1, 0) + _varint(100) + _key(2, 0) + _varint(100)
    phase1 = _key(1, 0) + _varint(200) + _key(2, 0) + _varint(200)
    anim = _key(6, 2) + _varint(len(phase0)) + phase0 + _key(6, 2) + _varint(len(phase1)) + phase1

    sprite_info = _key(5, 0) + _varint(111) + _key(5, 0) + _varint(222) + _key(6, 2) + _varint(len(anim)) + anim
    frame_group = _key(3, 2) + _varint(len(sprite_info)) + sprite_info
    appearance = _key(1, 0) + _varint(100) + _key(2, 2) + _varint(len(frame_group)) + frame_group
    appearances = _key(1, 2) + _varint(len(appearance)) + appearance

    path = tmp_path / "appearances.dat"
    path.write_bytes(appearances)

    idx = load_appearances_dat(path)
    assert idx.get_sprite_id(100, kind="object", time_ms=0) == 111
    assert idx.get_sprite_id(100, kind="object", time_ms=150) == 222
