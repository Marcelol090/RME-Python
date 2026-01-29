from __future__ import annotations

from pathlib import Path

from py_rme_canary.logic_layer.sprite_system.legacy_dat import load_legacy_item_sprites


def _build_minimal_dat() -> bytes:
    data = bytearray()
    data += (0x12345678).to_bytes(4, "little")
    data += (100).to_bytes(2, "little")  # items
    data += (0).to_bytes(2, "little")  # outfits
    data += (0).to_bytes(2, "little")  # effects
    data += (0).to_bytes(2, "little")  # missiles

    data += (0).to_bytes(1, "little")  # DatFlagGround
    data += (0).to_bytes(2, "little")  # ground speed
    data += (0xFF).to_bytes(1, "little")  # DatFlagLast

    data += (1).to_bytes(1, "little")  # width
    data += (1).to_bytes(1, "little")  # height
    data += (1).to_bytes(1, "little")  # layers
    data += (1).to_bytes(1, "little")  # pattern_x
    data += (1).to_bytes(1, "little")  # pattern_y
    data += (1).to_bytes(1, "little")  # pattern_z
    data += (1).to_bytes(1, "little")  # frames

    data += (1).to_bytes(2, "little")  # sprite id
    return bytes(data)


def test_legacy_dat_reader_minimal(tmp_path: Path) -> None:
    dat_path = tmp_path / "Tibia.dat"
    dat_path.write_bytes(_build_minimal_dat())

    result = load_legacy_item_sprites(
        dat_path,
        sprite_count=10,
        is_extended=False,
        has_frame_durations=False,
    )
    info = result.items[100]
    assert info.width == 1
    assert info.height == 1
    assert info.layers == 1
    assert info.pattern_x == 1
    assert info.pattern_y == 1
    assert info.pattern_z == 1
    assert info.frames == 1
    assert info.sprite_ids == (1,)
