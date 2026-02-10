from __future__ import annotations

import json

from py_rme_canary.core.assets.appearances_dat import (
    AppearanceFlags,
    AppearanceFlagLight,
    AppearanceFlagMarket,
    load_appearances_dat,
    resolve_appearances_path,
)


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


# ---------------------------------------------------------------------------
# AppearanceFlags parsing tests
# ---------------------------------------------------------------------------

def _build_appearance_with_flags(appearance_id: int, sprite_id: int, flags_payload: bytes) -> bytes:
    """Helper: build a minimal Appearance message with flags."""
    sprite_info = _key(5, 0) + _varint(sprite_id)
    frame_group = _key(3, 2) + _varint(len(sprite_info)) + sprite_info
    appearance = (
        _key(1, 0) + _varint(appearance_id)
        + _key(2, 2) + _varint(len(frame_group)) + frame_group
        + _key(3, 2) + _varint(len(flags_payload)) + flags_payload
    )
    return _key(1, 2) + _varint(len(appearance)) + appearance


def test_flags_ground_item(tmp_path) -> None:
    """Ground items have bank flag (field 1) with ground speed."""
    # AppearanceFlagBank: field 1 (waypoints) = 150
    bank_msg = _key(1, 0) + _varint(150)
    flags = _key(1, 2) + _varint(len(bank_msg)) + bank_msg
    data = _build_appearance_with_flags(100, 555, flags)

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    f = idx.get_flags(100)
    assert f is not None
    assert f.is_ground is True
    assert f.ground_speed == 150
    assert f.is_container is False


def test_flags_container_stackable(tmp_path) -> None:
    """Container (field 5) and stackable/cumulative (field 6) booleans."""
    flags = _key(5, 0) + _varint(1) + _key(6, 0) + _varint(1)
    data = _build_appearance_with_flags(200, 666, flags)

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    f = idx.get_flags(200)
    assert f is not None
    assert f.is_container is True
    assert f.is_stackable is True
    assert f.is_ground is False


def test_flags_writable(tmp_path) -> None:
    """Writable item (field 10) with max_text_length."""
    write_msg = _key(1, 0) + _varint(512)
    flags = _key(10, 2) + _varint(len(write_msg)) + write_msg
    data = _build_appearance_with_flags(300, 777, flags)

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    f = idx.get_flags(300)
    assert f is not None
    assert f.is_writable is True
    assert f.max_text_length == 512


def test_flags_unpassable_unmoveable_pickupable(tmp_path) -> None:
    """Common physics flags: unpass (13), unmove (14), take (18)."""
    flags = (
        _key(13, 0) + _varint(1)  # unpassable
        + _key(14, 0) + _varint(1)  # unmoveable
        + _key(18, 0) + _varint(1)  # pickupable
    )
    data = _build_appearance_with_flags(400, 888, flags)

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    f = idx.get_flags(400)
    assert f is not None
    assert f.is_unpassable is True
    assert f.is_unmoveable is True
    assert f.is_pickupable is True
    assert f.blocks_projectiles is False


def test_flags_light(tmp_path) -> None:
    """Light emission (field 23) with brightness and color."""
    light_msg = _key(1, 0) + _varint(7) + _key(2, 0) + _varint(215)
    flags = _key(23, 2) + _varint(len(light_msg)) + light_msg
    data = _build_appearance_with_flags(500, 999, flags)

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    f = idx.get_flags(500)
    assert f is not None
    assert f.light is not None
    assert f.light.brightness == 7
    assert f.light.color == 215


def test_flags_shift_and_elevation(tmp_path) -> None:
    """Shift/displacement (field 26) and height/elevation (field 27)."""
    shift_msg = _key(1, 0) + _varint(8) + _key(2, 0) + _varint(16)
    height_msg = _key(1, 0) + _varint(24)
    flags = (
        _key(26, 2) + _varint(len(shift_msg)) + shift_msg
        + _key(27, 2) + _varint(len(height_msg)) + height_msg
    )
    data = _build_appearance_with_flags(600, 1010, flags)

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    f = idx.get_flags(600)
    assert f is not None
    assert f.shift_x == 8
    assert f.shift_y == 16
    assert f.elevation == 24


def test_flags_minimap_color(tmp_path) -> None:
    """Automap/minimap color (field 30)."""
    automap_msg = _key(1, 0) + _varint(210)
    flags = _key(30, 2) + _varint(len(automap_msg)) + automap_msg
    data = _build_appearance_with_flags(700, 1111, flags)

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    f = idx.get_flags(700)
    assert f is not None
    assert f.has_minimap_color is True
    assert f.minimap_color == 210


def test_flags_market(tmp_path) -> None:
    """Market data (field 36) with category, trade_as, show_as, min_level."""
    market_msg = (
        _key(1, 0) + _varint(13)  # category = SHIELDS
        + _key(2, 0) + _varint(2510)  # trade_as_object_id
        + _key(3, 0) + _varint(2510)  # show_as_object_id
        + _key(6, 0) + _varint(80)  # minimum_level
    )
    flags = _key(36, 2) + _varint(len(market_msg)) + market_msg
    data = _build_appearance_with_flags(800, 1212, flags)

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    f = idx.get_flags(800)
    assert f is not None
    assert f.market is not None
    assert f.market.category == 13
    assert f.market.trade_as_object_id == 2510
    assert f.market.show_as_object_id == 2510
    assert f.market.minimum_level == 80


def test_flags_corpse_and_hangable(tmp_path) -> None:
    """Corpse (field 42) and hangable (field 20) + hook south (field 21)."""
    hook_msg = _key(1, 0) + _varint(1)  # HOOK_TYPE_SOUTH
    flags = (
        _key(20, 0) + _varint(1)  # hangable
        + _key(21, 2) + _varint(len(hook_msg)) + hook_msg  # hook south
        + _key(42, 0) + _varint(1)  # corpse
    )
    data = _build_appearance_with_flags(900, 1313, flags)

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    f = idx.get_flags(900)
    assert f is not None
    assert f.is_hangable is True
    assert f.hook_direction == 1
    assert f.is_corpse is True
    assert f.is_player_corpse is False


def test_flags_combined_complex(tmp_path) -> None:
    """Combined complex flags: ground + container + writable + light + market."""
    bank_msg = _key(1, 0) + _varint(100)
    write_msg = _key(1, 0) + _varint(256)
    light_msg = _key(1, 0) + _varint(5) + _key(2, 0) + _varint(180)
    market_msg = _key(1, 0) + _varint(4) + _key(2, 0) + _varint(3000)
    flags = (
        _key(1, 2) + _varint(len(bank_msg)) + bank_msg
        + _key(5, 0) + _varint(1)  # container
        + _key(10, 2) + _varint(len(write_msg)) + write_msg
        + _key(13, 0) + _varint(1)  # unpassable
        + _key(22, 0) + _varint(1)  # rotatable
        + _key(23, 2) + _varint(len(light_msg)) + light_msg
        + _key(36, 2) + _varint(len(market_msg)) + market_msg
        + _key(37, 0) + _varint(1)  # wrappable
    )
    data = _build_appearance_with_flags(1000, 1414, flags)

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    f = idx.get_flags(1000)
    assert f is not None
    assert f.is_ground is True
    assert f.ground_speed == 100
    assert f.is_container is True
    assert f.is_writable is True
    assert f.max_text_length == 256
    assert f.is_unpassable is True
    assert f.is_rotatable is True
    assert f.light is not None
    assert f.light.brightness == 5
    assert f.market is not None
    assert f.market.category == 4
    assert f.is_wrappable is True


def test_flags_absent_returns_none_for_unknown_id(tmp_path) -> None:
    """get_flags returns None for an ID that doesn't exist."""
    sprite_info = _key(5, 0) + _varint(555)
    frame_group = _key(3, 2) + _varint(len(sprite_info)) + sprite_info
    appearance = _key(1, 0) + _varint(100) + _key(2, 2) + _varint(len(frame_group)) + frame_group
    data = _key(1, 2) + _varint(len(appearance)) + appearance

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    assert idx.get_flags(999) is None


def test_flags_empty_flags_message(tmp_path) -> None:
    """Empty flags message produces default AppearanceFlags (all false/zero)."""
    flags = b""  # empty sub-message
    data = _build_appearance_with_flags(100, 555, flags)

    path = tmp_path / "appearances.dat"
    path.write_bytes(data)
    idx = load_appearances_dat(path)

    f = idx.get_flags(100)
    assert f is not None
    assert f.is_ground is False
    assert f.is_container is False
    assert f.is_stackable is False
    assert f.light is None
    assert f.market is None
