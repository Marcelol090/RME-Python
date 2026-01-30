from __future__ import annotations

import contextlib
import struct
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from py_rme_canary.core.memory_guard import MemoryGuard, MemoryGuardError, default_memory_guard

SPRITE_DIM = 32
SPRITE_PIXELS = SPRITE_DIM * SPRITE_DIM
BYTES_PER_PIXEL = 4


class LegacySpriteError(RuntimeError):
    """Raised when legacy .dat/.spr parsing fails."""


@dataclass(frozen=True, slots=True)
class LegacyDatInfo:
    signature: int
    items: int
    outfits: int
    effects: int
    missiles: int


def load_legacy_dat_info(path: str | Path) -> LegacyDatInfo:
    p = Path(path)
    if not p.exists():
        raise LegacySpriteError(f".dat not found: {p}")
    data = p.read_bytes()
    if len(data) < 12:
        raise LegacySpriteError(f".dat too small: {p}")
    signature = struct.unpack_from("<I", data, 0)[0]
    items, outfits, effects, missiles = struct.unpack_from("<HHHH", data, 4)
    return LegacyDatInfo(
        signature=int(signature),
        items=int(items),
        outfits=int(outfits),
        effects=int(effects),
        missiles=int(missiles),
    )


class LegacySpriteArchive:
    """Legacy Tibia .spr loader with on-demand decoding and cache."""

    def __init__(self, *, dat_path: str | Path, spr_path: str | Path, memory_guard: MemoryGuard | None = None) -> None:
        self.dat_path = Path(dat_path)
        self.spr_path = Path(spr_path)
        self._memory_guard = memory_guard or default_memory_guard()
        self._sprite_cache: OrderedDict[int, tuple[int, int, bytes]] = OrderedDict()

        self._sprite_offsets: list[int] = []
        self._sprite_count: int = 0
        self._is_extended: bool = False
        self.dat_info: LegacyDatInfo | None = None

        self._load_headers()

    @property
    def sprite_count(self) -> int:
        return int(self._sprite_count)

    @property
    def is_extended(self) -> bool:
        return bool(self._is_extended)

    def _load_headers(self) -> None:
        if self.dat_path.exists():
            self.dat_info = load_legacy_dat_info(self.dat_path)
        self._load_spr_index()

    def _load_spr_index(self) -> None:
        if not self.spr_path.exists():
            raise LegacySpriteError(f".spr not found: {self.spr_path}")

        file_size = int(self.spr_path.stat().st_size)
        if file_size < 8:
            raise LegacySpriteError(f".spr too small: {self.spr_path}")

        with self.spr_path.open("rb") as f:
            _signature = struct.unpack("<I", f.read(4))[0]

            # Try extended (u32) count first.
            count_u32 = struct.unpack("<I", f.read(4))[0]
            header_u32 = 8 + int(count_u32) * 4
            if count_u32 > 0 and header_u32 <= file_size:
                self._is_extended = True
                self._sprite_count = int(count_u32)
            else:
                f.seek(4)
                count_u16 = struct.unpack("<H", f.read(2))[0]
                header_u16 = 6 + int(count_u16) * 4
                if count_u16 <= 0 or header_u16 > file_size:
                    raise LegacySpriteError("Invalid sprite count in .spr header")
                self._is_extended = False
                self._sprite_count = int(count_u16)

            offsets = [0] * (self._sprite_count + 1)
            for idx in range(1, self._sprite_count + 1):
                raw = f.read(4)
                if len(raw) != 4:
                    raise LegacySpriteError("Unexpected EOF reading sprite offsets")
                offsets[idx] = struct.unpack("<I", raw)[0]
            self._sprite_offsets = offsets

    def get_sprite_rgba(self, sprite_id: int) -> tuple[int, int, bytes]:
        sid = int(sprite_id)
        if sid <= 0 or sid > self._sprite_count:
            raise LegacySpriteError(f"Sprite id out of range: {sid}")

        cached = self._sprite_cache.get(sid)
        if cached is not None:
            with contextlib.suppress(Exception):
                self._sprite_cache.move_to_end(sid)
            return cached

        offset = self._sprite_offsets[sid]
        if offset == 0:
            return (SPRITE_DIM, SPRITE_DIM, bytes(SPRITE_PIXELS * BYTES_PER_PIXEL))

        with self.spr_path.open("rb") as f:
            f.seek(int(offset) + 3)
            size_raw = f.read(2)
            if len(size_raw) != 2:
                raise LegacySpriteError(f"Sprite {sid} size header missing")
            size = struct.unpack("<H", size_raw)[0]
            if size <= 0:
                return (SPRITE_DIM, SPRITE_DIM, bytes(SPRITE_PIXELS * BYTES_PER_PIXEL))
            data = f.read(int(size))
            if len(data) != int(size):
                raise LegacySpriteError(f"Sprite {sid} data truncated")

        rgba = _decode_sprite_rle(data)
        result = (SPRITE_DIM, SPRITE_DIM, rgba)

        try:
            self._sprite_cache[sid] = result
            self._sprite_cache.move_to_end(sid)
        except Exception:
            return result

        try:
            self._memory_guard.check_cache_entries(
                kind="sprite_cache",
                entries=len(self._sprite_cache),
                stage="legacy_sprite_cache",
            )
        except MemoryGuardError:
            evict_to = int(self._memory_guard.config.evict_to_sprite_cache_entries)
            hard = int(self._memory_guard.config.hard_sprite_cache_entries)
            target = min(max(0, evict_to), max(0, hard - 1)) if hard > 0 else 0
            try:
                while len(self._sprite_cache) > target and self._sprite_cache:
                    self._sprite_cache.popitem(last=False)
            except Exception:
                self._sprite_cache.clear()

        return result


def _decode_sprite_rle(data: bytes) -> bytes:
    out = bytearray(SPRITE_PIXELS * BYTES_PER_PIXEL)
    pos = 0
    pixel = 0
    size = len(data)

    while pos + 4 <= size and pixel < SPRITE_PIXELS:
        transparent = data[pos] | (data[pos + 1] << 8)
        pos += 2
        colored = data[pos] | (data[pos + 1] << 8)
        pos += 2

        pixel += int(transparent)
        if pixel >= SPRITE_PIXELS:
            break

        for _ in range(int(colored)):
            if pos + 3 > size or pixel >= SPRITE_PIXELS:
                break
            r = int(data[pos])
            g = int(data[pos + 1])
            b = int(data[pos + 2])
            pos += 3

            base = pixel * BYTES_PER_PIXEL
            out[base : base + 4] = bytes([b, g, r, 0xFF])
            pixel += 1

    return bytes(out)
