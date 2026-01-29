from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


class LegacyDatError(RuntimeError):
    """Raised when legacy .dat parsing fails."""


DAT_FLAG_GROUND = 0
DAT_FLAG_GROUND_BORDER = 1
DAT_FLAG_ON_BOTTOM = 2
DAT_FLAG_ON_TOP = 3
DAT_FLAG_STACKABLE = 5
DAT_FLAG_LIGHT = 21
DAT_FLAG_DISPLACEMENT = 24
DAT_FLAG_ELEVATION = 25
DAT_FLAG_MINIMAP_COLOR = 28
DAT_FLAG_MARKET = 33
DAT_FLAG_TOP_EFFECT = 37
DAT_FLAG_LAST = 0xFF

_SKIP_U16_FLAGS = {
    0,  # Ground
    8,  # Writable
    9,  # WritableOnce
    32,  # Cloth
    29,  # LensHelp
    34,  # Usable
}


@dataclass(frozen=True, slots=True)
class LegacyAnimation:
    frames: int
    durations_ms: tuple[int, ...]
    start_frame: int = 0

    def frame_index_for_time(self, time_ms: int) -> int:
        frame_count = max(1, int(self.frames))
        if frame_count <= 1:
            return 0
        durations = self.durations_ms or tuple(200 for _ in range(frame_count))
        total = sum(int(d) for d in durations) or (frame_count * 200)
        t = int(time_ms) % int(total)
        for idx, duration in enumerate(durations):
            d = int(duration) if int(duration) > 0 else 200
            if t < d:
                return int(idx)
            t -= d
        return int(frame_count - 1)


@dataclass(frozen=True, slots=True)
class LegacyItemSpriteInfo:
    item_id: int
    sprite_ids: tuple[int, ...]
    width: int
    height: int
    layers: int
    pattern_x: int
    pattern_y: int
    pattern_z: int
    frames: int
    is_ground: bool = False
    is_bottom: bool = False
    is_top: bool = False
    is_stackable: bool = False
    draw_offset_x: int = 0
    draw_offset_y: int = 0
    draw_height: int = 0
    animation: LegacyAnimation | None = None

    def sprite_index(
        self,
        width: int,
        height: int,
        layer: int,
        pattern_x: int,
        pattern_y: int,
        pattern_z: int,
        frame: int,
    ) -> int:
        return (
            (((((int(frame) % max(1, int(self.frames))) * int(self.pattern_z) + int(pattern_z)) * int(self.pattern_y) + int(pattern_y))
            * int(self.pattern_x) + int(pattern_x)) * int(self.layers) + int(layer)) * int(self.height) + int(height)
        ) * int(self.width) + int(width)

    def sprite_id_at(
        self,
        width: int,
        height: int,
        layer: int,
        pattern_x: int,
        pattern_y: int,
        pattern_z: int,
        frame: int,
    ) -> int | None:
        if not self.sprite_ids:
            return None
        idx = self.sprite_index(width, height, layer, pattern_x, pattern_y, pattern_z, frame)
        if 0 <= idx < len(self.sprite_ids):
            return int(self.sprite_ids[idx])
        if len(self.sprite_ids) == 1:
            return int(self.sprite_ids[0])
        return int(self.sprite_ids[idx % len(self.sprite_ids)])


@dataclass(frozen=True, slots=True)
class LegacyItemSprites:
    signature: int
    item_count: int
    items: dict[int, LegacyItemSpriteInfo]


def load_legacy_item_sprites(
    dat_path: str | Path,
    *,
    sprite_count: int,
    is_extended: bool,
    has_frame_durations: bool | None = None,
) -> LegacyItemSprites:
    path = Path(dat_path)
    if not path.exists():
        raise LegacyDatError(f".dat not found: {path}")
    data = path.read_bytes()
    if len(data) < 12:
        raise LegacyDatError(f".dat too small: {path}")

    if has_frame_durations is None:
        primary = _parse_legacy_items(data, sprite_count, is_extended=is_extended, has_frame_durations=True)
        fallback = _parse_legacy_items(data, sprite_count, is_extended=is_extended, has_frame_durations=False)
        if primary.valid_ratio >= fallback.valid_ratio:
            return primary.result
        return fallback.result

    parsed = _parse_legacy_items(data, sprite_count, is_extended=is_extended, has_frame_durations=has_frame_durations)
    return parsed.result


@dataclass(slots=True)
class _ParseResult:
    result: LegacyItemSprites
    valid_ratio: float


def _parse_legacy_items(
    data: bytes,
    sprite_count: int,
    *,
    is_extended: bool,
    has_frame_durations: bool,
) -> _ParseResult:
    mv = memoryview(data)
    offset = 0

    def read_u8() -> int:
        nonlocal offset
        if offset + 1 > len(mv):
            raise LegacyDatError("Unexpected EOF reading u8")
        v = mv[offset]
        offset += 1
        return int(v)

    def read_u16() -> int:
        nonlocal offset
        if offset + 2 > len(mv):
            raise LegacyDatError("Unexpected EOF reading u16")
        v = int.from_bytes(mv[offset : offset + 2], "little")
        offset += 2
        return int(v)

    def read_u32() -> int:
        nonlocal offset
        if offset + 4 > len(mv):
            raise LegacyDatError("Unexpected EOF reading u32")
        v = int.from_bytes(mv[offset : offset + 4], "little")
        offset += 4
        return int(v)

    def read_i8() -> int:
        nonlocal offset
        if offset + 1 > len(mv):
            raise LegacyDatError("Unexpected EOF reading i8")
        v = int.from_bytes(mv[offset : offset + 1], "little", signed=True)
        offset += 1
        return int(v)

    def read_string() -> str:
        length = read_u16()
        nonlocal offset
        if offset + length > len(mv):
            raise LegacyDatError("Unexpected EOF reading string")
        raw = bytes(mv[offset : offset + length])
        offset += length
        return raw.decode("utf-8", errors="replace")

    signature = read_u32()
    item_count = read_u16()
    _outfits = read_u16()
    _effects = read_u16()
    _missiles = read_u16()

    items: dict[int, LegacyItemSpriteInfo] = {}
    valid_ids = 0
    total_ids = 0

    min_id = 100
    max_id = int(item_count)

    for item_id in range(min_id, max_id + 1):
        is_ground = False
        is_bottom = False
        is_top = False
        is_stackable = False
        draw_offset_x = 0
        draw_offset_y = 0
        draw_height = 0
        animation: LegacyAnimation | None = None

        while True:
            flag = read_u8()
            if flag == DAT_FLAG_LAST:
                break
            if flag == DAT_FLAG_GROUND:
                is_ground = True
            elif flag == DAT_FLAG_ON_BOTTOM:
                is_bottom = True
            elif flag == DAT_FLAG_ON_TOP:
                is_top = True
            elif flag == DAT_FLAG_STACKABLE:
                is_stackable = True

            if flag in _SKIP_U16_FLAGS:
                read_u16()
                continue
            if flag == DAT_FLAG_LIGHT:
                read_u16()
                read_u16()
                continue
            if flag == DAT_FLAG_DISPLACEMENT:
                draw_offset_x = read_u16()
                draw_offset_y = read_u16()
                continue
            if flag == DAT_FLAG_ELEVATION:
                draw_height = read_u16()
                continue
            if flag == DAT_FLAG_MINIMAP_COLOR:
                read_u16()
                continue
            if flag == DAT_FLAG_MARKET:
                read_u16()
                read_u16()
                read_u16()
                _ = read_string()
                read_u16()
                read_u16()
                continue

        width = read_u8()
        height = read_u8()
        if width > 1 or height > 1:
            read_u8()  # exact size
        layers = read_u8()
        pattern_x = read_u8()
        pattern_y = read_u8()
        pattern_z = read_u8()
        frames = read_u8()

        if frames > 1 and has_frame_durations:
            _async = read_u8()
            _loop_count = read_u32()
            start_frame = read_i8()
            durations: list[int] = []
            for _ in range(frames):
                dmin = read_u32()
                dmax = read_u32()
                durations.append(max(1, (int(dmin) + int(dmax)) // 2))
            animation = LegacyAnimation(frames=int(frames), durations_ms=tuple(durations), start_frame=int(start_frame))

        numsprites = (
            int(width)
            * int(height)
            * int(layers)
            * int(pattern_x)
            * int(pattern_y)
            * int(pattern_z)
            * int(frames)
        )
        sprite_ids: list[int] = []
        for _ in range(numsprites):
            if is_extended:
                sprite_id = read_u32()
            else:
                sprite_id = read_u16()
            sprite_ids.append(int(sprite_id))
            total_ids += 1
            if 0 < int(sprite_id) <= int(sprite_count):
                valid_ids += 1

        items[item_id] = LegacyItemSpriteInfo(
            item_id=int(item_id),
            sprite_ids=tuple(sprite_ids),
            width=int(width),
            height=int(height),
            layers=int(layers),
            pattern_x=int(pattern_x),
            pattern_y=int(pattern_y),
            pattern_z=int(pattern_z),
            frames=int(frames),
            is_ground=bool(is_ground),
            is_bottom=bool(is_bottom),
            is_top=bool(is_top),
            is_stackable=bool(is_stackable),
            draw_offset_x=int(draw_offset_x),
            draw_offset_y=int(draw_offset_y),
            draw_height=int(draw_height),
            animation=animation,
        )

    ratio = 1.0
    if total_ids > 0:
        ratio = float(valid_ids) / float(total_ids)
    result = LegacyItemSprites(signature=int(signature), item_count=int(item_count), items=items)
    return _ParseResult(result=result, valid_ratio=float(ratio))