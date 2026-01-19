from __future__ import annotations

import json
import lzma
import os
import struct
from collections import OrderedDict
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from py_rme_canary.core.memory_guard import MemoryGuard, MemoryGuardError, default_memory_guard

SPRITE_SHEET_WIDTH = 384
SPRITE_SHEET_HEIGHT = 384
BYTES_PER_PIXEL = 4
BYTES_IN_SPRITE_SHEET = SPRITE_SHEET_WIDTH * SPRITE_SHEET_HEIGHT * BYTES_PER_PIXEL
SPRITE_SHEET_WIDTH_BYTES = SPRITE_SHEET_WIDTH * BYTES_PER_PIXEL
LZMA_UNCOMPRESSED_SIZE = BYTES_IN_SPRITE_SHEET + 122  # matches legacy constant


class SpriteAppearancesError(RuntimeError):
    pass


@dataclass(slots=True)
class SpriteSheet:
    first_id: int
    last_id: int
    sprite_type: int  # legacy SpriteLayout enum value
    path: str
    loaded: bool = False
    data: bytes | None = None  # BGRA bytes, 384*384*4

    def sprite_size(self) -> tuple[int, int]:
        # Mirrors SpriteSheet::getSpriteSize() in legacy.
        # Base is 32x32; some layouts double width/height.
        if int(self.sprite_type) == 1:  # ONE_BY_TWO
            return (32, 64)
        if int(self.sprite_type) == 2:  # TWO_BY_ONE
            return (64, 32)
        if int(self.sprite_type) == 3:  # TWO_BY_TWO
            return (64, 64)
        return (32, 32)

    def contains(self, sprite_id: int) -> bool:
        sid = int(sprite_id)
        return int(self.first_id) <= sid <= int(self.last_id)


class SpriteAppearances:
    """Minimal port of `SpriteAppearances` focused on sprite sheet decoding.

    Legacy reference:
    - `source/sprite_appearances.cpp` (catalog-content + LZMA sheet decode + sprite extraction)

    Scope:
    - Loads `catalog-content.json` and sprite sheet metadata.
    - Decodes sheet files into raw BGRA pixels (384x384).
    - Extracts individual sprites by sprite id.

    This intentionally does *not* parse appearances protobuf nor map item ids -> sprite ids.
    """

    def __init__(self, *, assets_dir: str | Path, memory_guard: MemoryGuard | None = None):
        self.assets_dir = str(Path(assets_dir))
        self._sheets: list[SpriteSheet] = []
        self._sprite_cache: OrderedDict[int, tuple[int, int, bytes]] = OrderedDict()
        self._memory_guard = memory_guard or default_memory_guard()

    @property
    def sheets(self) -> list[SpriteSheet]:
        return list(self._sheets)

    def load_catalog_content(self, *, load_data: bool = False) -> None:
        catalog_path = Path(self.assets_dir) / "catalog-content.json"
        if not catalog_path.exists():
            raise SpriteAppearancesError(f"catalog-content.json not found: {catalog_path}")

        try:
            doc = json.loads(catalog_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise SpriteAppearancesError(f"Failed to parse catalog-content.json: {e}") from e

        sheets: list[SpriteSheet] = []
        for obj in doc:
            t = obj.get("type")
            if t != "sprite":
                continue

            try:
                first_id = int(obj["firstspriteid"])
                last_id = int(obj["lastspriteid"])
                sprite_type = int(obj["spritetype"])
                file_rel = str(obj["file"])
            except Exception as e:
                raise SpriteAppearancesError(f"Invalid sprite entry in catalog-content.json: {e}") from e

            path = str(Path(self.assets_dir) / file_rel)
            sheets.append(SpriteSheet(first_id=first_id, last_id=last_id, sprite_type=sprite_type, path=path))

        if not sheets:
            raise SpriteAppearancesError("No sprite sheets found in catalog-content.json")

        self._sheets = sheets

        if load_data:
            for s in self._sheets:
                self._load_sheet(s)

    def _find_sheet(self, sprite_id: int) -> SpriteSheet | None:
        sid = int(sprite_id)
        for sheet in self._sheets:
            if sheet.contains(sid):
                return sheet
        return None

    def _load_sheet(self, sheet: SpriteSheet) -> None:
        if sheet.loaded:
            return

        p = Path(sheet.path)
        if not p.exists():
            raise SpriteAppearancesError(f"Sprite sheet not found: {p}")

        blob = p.read_bytes()
        if not blob:
            raise SpriteAppearancesError(f"Sprite sheet empty: {p}")

        # Port of legacy header parsing from `SpriteAppearances::loadSpriteSheet`.
        pos = 0
        # Skip variable pad of NULs.
        while pos < len(blob) and blob[pos] == 0x00:
            pos += 1
        if pos >= len(blob):
            raise SpriteAppearancesError("Invalid sprite sheet header (all zeros)")

        # Skip remaining bytes of constant marker [0x70 0x0A 0xFA 0x80 0x24]
        # We are currently at 0x70; legacy does pos += 4 after consuming the first non-zero.
        pos += 4

        # Skip 7-bit int encoded LZMA file size.
        while pos < len(blob) and (blob[pos] & 0x80) == 0x80:
            pos += 1
        pos += 1  # consume final size byte

        if pos + 1 + 4 + 8 >= len(blob):
            raise SpriteAppearancesError("Invalid sprite sheet header (truncated)")

        lclppb = blob[pos]
        pos += 1

        lc = int(lclppb % 9)
        remainder = int(lclppb // 9)
        lp = int(remainder % 5)
        pb = int(remainder // 5)

        dict_size = 0
        for i in range(4):
            dict_size |= int(blob[pos + i]) << (i * 8)
        pos += 4

        # Skip cip compressed size (8 bytes)
        pos += 8

        try:
            decompressed = lzma.decompress(
                blob[pos:],
                format=lzma.FORMAT_RAW,
                filters=[
                    {
                        "id": lzma.FILTER_LZMA1,
                        "dict_size": int(dict_size),
                        "lc": int(lc),
                        "lp": int(lp),
                        "pb": int(pb),
                    }
                ],
            )
        except Exception as e:
            raise SpriteAppearancesError(f"Failed to LZMA-decompress sprite sheet: {e}") from e

        if len(decompressed) < 54:
            raise SpriteAppearancesError("Decompressed sprite sheet too small")

        pixel_offset = struct.unpack_from("<I", decompressed, 10)[0]
        if pixel_offset <= 0 or pixel_offset + BYTES_IN_SPRITE_SHEET > len(decompressed):
            raise SpriteAppearancesError("Invalid BMP pixel offset in decompressed sprite sheet")

        pixel_data = bytearray(decompressed[pixel_offset : pixel_offset + BYTES_IN_SPRITE_SHEET])

        # Flip vertically (legacy does this in-place).
        row_bytes = SPRITE_SHEET_WIDTH_BYTES
        for y in range(SPRITE_SHEET_HEIGHT // 2):
            y2 = SPRITE_SHEET_HEIGHT - y - 1
            a0 = y * row_bytes
            b0 = y2 * row_bytes
            tmp = pixel_data[a0 : a0 + row_bytes]
            pixel_data[a0 : a0 + row_bytes] = pixel_data[b0 : b0 + row_bytes]
            pixel_data[b0 : b0 + row_bytes] = tmp

        sheet.data = bytes(pixel_data)
        sheet.loaded = True

    def get_sprite_rgba(self, sprite_id: int) -> tuple[int, int, bytes]:
        """Return (w, h, BGRA bytes) for `sprite_id` (cached)."""

        sid = int(sprite_id)
        cached = self._sprite_cache.get(sid)
        if cached is not None:
            with suppress(Exception):
                self._sprite_cache.move_to_end(sid)
            return cached

        sheet = self._find_sheet(sid)
        if sheet is None:
            raise SpriteAppearancesError(f"No sheet for sprite id: {sid}")
        if not sheet.loaded:
            self._load_sheet(sheet)
        if sheet.data is None:
            raise SpriteAppearancesError("Sheet loaded but pixel data missing")

        sprite_w, sprite_h = sheet.sprite_size()

        sprite_offset = sid - int(sheet.first_id)
        if sprite_offset < 0 or sid > int(sheet.last_id):
            raise SpriteAppearancesError("Sprite id out of sheet bounds")

        all_columns = 12 if int(sprite_w) == 32 else 6  # matches legacy
        sprite_row = int(sprite_offset // all_columns)
        sprite_col = int(sprite_offset % all_columns)

        try:
            out = bytearray(sprite_w * sprite_h * BYTES_PER_PIXEL)
        except MemoryError as e:
            raise SpriteAppearancesError(f"Out of memory creating sprite buffer ({sprite_w}x{sprite_h})") from e
        src = sheet.data
        sprite_w_bytes = int(sprite_w) * BYTES_PER_PIXEL

        for y in range(int(sprite_h)):
            src_row = sprite_row * int(sprite_h) + y
            src_start = src_row * SPRITE_SHEET_WIDTH_BYTES + (sprite_col * sprite_w_bytes)
            dst_start = y * sprite_w_bytes
            out[dst_start : dst_start + sprite_w_bytes] = src[src_start : src_start + sprite_w_bytes]

        result = (int(sprite_w), int(sprite_h), bytes(out))
        try:
            self._sprite_cache[sid] = result
            self._sprite_cache.move_to_end(sid)
        except Exception:
            return result

        # Soft limit: warn once (no-op here; guard tracks warning state).
        # Hard limit: evict aggressively to a target below hard.
        try:
            self._memory_guard.check_cache_entries(
                kind="sprite_cache",
                entries=len(self._sprite_cache),
                stage="sprite_cache",
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


def resolve_assets_dir(path: str | os.PathLike[str]) -> str:
    """Accepts either client root or assets folder; returns assets folder."""

    p = Path(path)
    if not p.exists():
        raise SpriteAppearancesError(f"Path not found: {p}")

    # If it's already the assets directory.
    if (p / "catalog-content.json").exists():
        return str(p)

    # If user selected client root.
    if (p / "assets" / "catalog-content.json").exists():
        return str(p / "assets")

    raise SpriteAppearancesError(
        "Invalid assets path. Select the Tibia client folder (with assets/) or "
        "the assets folder (with catalog-content.json)."
    )
