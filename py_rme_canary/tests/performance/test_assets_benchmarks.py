from __future__ import annotations

import struct
from pathlib import Path

import pytest

from py_rme_canary.core.assets.legacy_dat_spr import LegacySpriteArchive


def _write_minimal_spr(path: Path) -> None:
    sig = struct.pack("<I", 0x01020304)
    count = struct.pack("<H", 1)
    offset = struct.pack("<I", 10)
    sprite_data = struct.pack("<HH", 0, 1) + bytes([255, 0, 0]) + struct.pack("<HH", 1023, 0)
    size = struct.pack("<H", len(sprite_data))
    payload = bytes([0, 0, 0]) + size + sprite_data
    path.write_bytes(sig + count + offset + payload)


@pytest.mark.benchmark
def test_legacy_sprite_decode_benchmark(tmp_path: Path, benchmark) -> None:
    dat_path = tmp_path / "Tibia.dat"
    spr_path = tmp_path / "Tibia.spr"
    dat_path.write_bytes(b"\x00" * 12)
    _write_minimal_spr(spr_path)

    archive = LegacySpriteArchive(dat_path=dat_path, spr_path=spr_path)

    def decode_once() -> None:
        archive.get_sprite_rgba(1)

    benchmark(decode_once)
