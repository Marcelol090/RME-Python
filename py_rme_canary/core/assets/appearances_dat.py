from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


class AppearancesDatError(RuntimeError):
    """Raised when appearances.dat parsing fails."""


@dataclass(frozen=True, slots=True)
class SpritePhase:
    duration_min: int = 0
    duration_max: int = 0

    def duration_ms(self) -> int:
        dmin = int(self.duration_min)
        dmax = int(self.duration_max)
        if dmin > 0 and dmax > 0:
            return max(1, (dmin + dmax) // 2)
        if dmax > 0:
            return max(1, dmax)
        if dmin > 0:
            return max(1, dmin)
        return 100


@dataclass(frozen=True, slots=True)
class SpriteAnimation:
    phases: tuple[SpritePhase, ...] = ()
    default_start_phase: int = 0
    synchronized: bool = False
    random_start_phase: bool = False
    loop_type: int = 0
    loop_count: int = 0

    def phase_durations(self, phase_count: int) -> list[int]:
        durations: list[int] = []
        for idx in range(int(phase_count)):
            if idx < len(self.phases):
                durations.append(int(self.phases[idx].duration_ms()))
            else:
                durations.append(100)
        return durations

    def phase_order(self, phase_count: int) -> list[int]:
        phases = list(range(int(phase_count)))
        if self.loop_type == -1 and phase_count > 1:
            phases = phases + list(range(int(phase_count) - 2, 0, -1))
        return phases


@dataclass(frozen=True, slots=True)
class SpriteInfo:
    sprite_ids: tuple[int, ...] = ()
    layers: int = 1
    pattern_width: int = 1
    pattern_height: int = 1
    pattern_depth: int = 1
    animation: SpriteAnimation | None = None

    def sprites_per_phase(self) -> int:
        return max(1, int(self.layers) * int(self.pattern_width) * int(self.pattern_height) * int(self.pattern_depth))

    def phase_count(self) -> int:
        spp = self.sprites_per_phase()
        if spp <= 0:
            return 1
        return max(1, len(self.sprite_ids) // spp)

    def sprite_id_for_phase(self, phase_index: int) -> int | None:
        if not self.sprite_ids:
            return None
        spp = self.sprites_per_phase()
        idx = int(phase_index) * spp
        if 0 <= idx < len(self.sprite_ids):
            return int(self.sprite_ids[idx])
        return int(self.sprite_ids[0])

    def phase_index_for_time(self, time_ms: int, *, seed: int | None = None) -> int:
        if self.animation is None:
            return 0
        phase_count = self.phase_count()
        if phase_count <= 1:
            return 0

        order = self.animation.phase_order(phase_count)
        if not order:
            return 0

        start_phase = int(self.animation.default_start_phase or 0)
        if self.animation.random_start_phase and seed is not None:
            start_phase = int(seed) % phase_count
        if start_phase in order:
            idx = order.index(start_phase)
            order = order[idx:] + order[:idx]

        durations = self.animation.phase_durations(phase_count)
        total = sum(durations[p] for p in order)
        if total <= 0:
            return int(order[0])

        if self.animation.loop_type == 1 and int(self.animation.loop_count) > 0:
            max_time = total * int(self.animation.loop_count)
            if int(time_ms) >= max_time:
                return int(order[-1])

        t = int(time_ms) % total
        for phase in order:
            d = int(durations[phase])
            if t < d:
                return int(phase)
            t -= d
        return int(order[-1])


@dataclass(slots=True)
class AppearanceIndex:
    object_sprites: dict[int, int] = field(default_factory=dict)
    outfit_sprites: dict[int, int] = field(default_factory=dict)
    effect_sprites: dict[int, int] = field(default_factory=dict)
    missile_sprites: dict[int, int] = field(default_factory=dict)
    object_info: dict[int, SpriteInfo] = field(default_factory=dict)
    outfit_info: dict[int, SpriteInfo] = field(default_factory=dict)
    effect_info: dict[int, SpriteInfo] = field(default_factory=dict)
    missile_info: dict[int, SpriteInfo] = field(default_factory=dict)

    def get_sprite_id(
        self,
        appearance_id: int,
        *,
        kind: str = "object",
        time_ms: int | None = None,
        seed: int | None = None,
    ) -> int | None:
        kid = int(appearance_id)
        info = _get_sprite_info(self, kind=kind, appearance_id=kid)
        if info is None:
            return None
        if time_ms is None:
            return info.sprite_id_for_phase(0)
        phase = info.phase_index_for_time(int(time_ms), seed=seed)
        return info.sprite_id_for_phase(phase)


def resolve_appearances_path(assets_dir: str | Path) -> Path | None:
    """Resolve the appearances.dat path from assets/catalog-content.json."""
    p = Path(assets_dir)
    catalog_path = p / "catalog-content.json"
    if not catalog_path.exists():
        return None

    try:
        doc = json.loads(catalog_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise AppearancesDatError(f"Failed to parse catalog-content.json: {e}") from e

    if not isinstance(doc, list):
        raise AppearancesDatError("catalog-content.json must be a list")

    for entry in doc:
        if not isinstance(entry, dict):
            continue
        if entry.get("type") != "appearances":
            continue
        file_name = entry.get("file")
        if not file_name:
            continue
        return (p / str(file_name)).resolve()
    return None


def load_appearances_dat(path: str | Path) -> AppearanceIndex:
    """Load appearances.dat (protobuf) and build appearance -> sprite id index."""
    p = Path(path)
    if not p.exists():
        raise AppearancesDatError(f"appearances.dat not found: {p}")
    data = p.read_bytes()
    if not data:
        raise AppearancesDatError(f"appearances.dat empty: {p}")

    index = AppearanceIndex()
    _parse_appearances(data, index)
    return index


def _parse_appearances(data: bytes, index: AppearanceIndex) -> None:
    offset = 0
    kind_map = {1: "object", 2: "outfit", 3: "effect", 4: "missile"}
    size = len(data)
    while offset < size:
        field_number, wire_type, offset = _read_key(data, offset)
        if wire_type != 2:
            offset = _skip_value(data, offset, wire_type)
            continue
        length, offset = _read_varint(data, offset)
        payload = data[offset : offset + length]
        offset += length
        kind = kind_map.get(field_number)
        if kind is None:
            continue
        appearance_id, sprite_info = _parse_appearance(payload)
        if appearance_id is None or sprite_info is None:
            continue
        if kind == "object":
            index.object_info[int(appearance_id)] = sprite_info
            sprite_id = sprite_info.sprite_id_for_phase(0)
            if sprite_id is not None:
                index.object_sprites[int(appearance_id)] = int(sprite_id)
        elif kind == "outfit":
            index.outfit_info[int(appearance_id)] = sprite_info
            sprite_id = sprite_info.sprite_id_for_phase(0)
            if sprite_id is not None:
                index.outfit_sprites[int(appearance_id)] = int(sprite_id)
        elif kind == "effect":
            index.effect_info[int(appearance_id)] = sprite_info
            sprite_id = sprite_info.sprite_id_for_phase(0)
            if sprite_id is not None:
                index.effect_sprites[int(appearance_id)] = int(sprite_id)
        elif kind == "missile":
            index.missile_info[int(appearance_id)] = sprite_info
            sprite_id = sprite_info.sprite_id_for_phase(0)
            if sprite_id is not None:
                index.missile_sprites[int(appearance_id)] = int(sprite_id)


def _parse_appearance(payload: bytes) -> tuple[int | None, SpriteInfo | None]:
    appearance_id: int | None = None
    sprite_info: SpriteInfo | None = None
    offset = 0
    size = len(payload)
    while offset < size:
        field_number, wire_type, offset = _read_key(payload, offset)
        if field_number == 1 and wire_type == 0:
            appearance_id, offset = _read_varint(payload, offset)
            continue
        if field_number == 2 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            fg_payload = payload[offset : offset + length]
            offset += length
            if sprite_info is None:
                sprite_info = _parse_frame_group(fg_payload)
            continue
        offset = _skip_value(payload, offset, wire_type)
    return appearance_id, sprite_info


def _parse_frame_group(payload: bytes) -> SpriteInfo | None:
    offset = 0
    size = len(payload)
    sprite_info: SpriteInfo | None = None
    while offset < size:
        field_number, wire_type, offset = _read_key(payload, offset)
        if field_number == 3 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            info_payload = payload[offset : offset + length]
            offset += length
            if sprite_info is None:
                sprite_info = _parse_sprite_info(info_payload)
            continue
        offset = _skip_value(payload, offset, wire_type)
    return sprite_info


def _parse_sprite_info(payload: bytes) -> SpriteInfo | None:
    offset = 0
    size = len(payload)
    pattern_width = 1
    pattern_height = 1
    pattern_depth = 1
    layers = 1
    sprite_ids: list[int] = []
    animation: SpriteAnimation | None = None
    while offset < size:
        field_number, wire_type, offset = _read_key(payload, offset)
        if field_number == 1 and wire_type == 0:
            pattern_width, offset = _read_varint(payload, offset)
            continue
        if field_number == 2 and wire_type == 0:
            pattern_height, offset = _read_varint(payload, offset)
            continue
        if field_number == 3 and wire_type == 0:
            pattern_depth, offset = _read_varint(payload, offset)
            continue
        if field_number == 4 and wire_type == 0:
            layers, offset = _read_varint(payload, offset)
            continue
        if field_number == 5 and wire_type == 0:
            value, offset = _read_varint(payload, offset)
            sprite_ids.append(int(value))
            continue
        if field_number == 6 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            anim_payload = payload[offset : offset + length]
            offset += length
            animation = _parse_sprite_animation(anim_payload)
            continue
        offset = _skip_value(payload, offset, wire_type)
    if not sprite_ids:
        return None
    return SpriteInfo(
        sprite_ids=tuple(int(s) for s in sprite_ids),
        layers=int(layers),
        pattern_width=int(pattern_width),
        pattern_height=int(pattern_height),
        pattern_depth=int(pattern_depth),
        animation=animation,
    )


def _parse_sprite_animation(payload: bytes) -> SpriteAnimation:
    offset = 0
    size = len(payload)
    default_start_phase = 0
    synchronized = False
    random_start_phase = False
    loop_type = 0
    loop_count = 0
    phases: list[SpritePhase] = []

    while offset < size:
        field_number, wire_type, offset = _read_key(payload, offset)
        if field_number == 1 and wire_type == 0:
            default_start_phase, offset = _read_varint(payload, offset)
            continue
        if field_number == 2 and wire_type == 0:
            synchronized_val, offset = _read_varint(payload, offset)
            synchronized = bool(int(synchronized_val))
            continue
        if field_number == 3 and wire_type == 0:
            random_val, offset = _read_varint(payload, offset)
            random_start_phase = bool(int(random_val))
            continue
        if field_number == 4 and wire_type == 0:
            loop_type, offset = _read_varint(payload, offset)
            continue
        if field_number == 5 and wire_type == 0:
            loop_count, offset = _read_varint(payload, offset)
            continue
        if field_number == 6 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            phase_payload = payload[offset : offset + length]
            offset += length
            phases.append(_parse_sprite_phase(phase_payload))
            continue
        offset = _skip_value(payload, offset, wire_type)

    return SpriteAnimation(
        phases=tuple(phases),
        default_start_phase=int(default_start_phase),
        synchronized=bool(synchronized),
        random_start_phase=bool(random_start_phase),
        loop_type=int(loop_type),
        loop_count=int(loop_count),
    )


def _parse_sprite_phase(payload: bytes) -> SpritePhase:
    offset = 0
    size = len(payload)
    duration_min = 0
    duration_max = 0
    while offset < size:
        field_number, wire_type, offset = _read_key(payload, offset)
        if field_number == 1 and wire_type == 0:
            duration_min, offset = _read_varint(payload, offset)
            continue
        if field_number == 2 and wire_type == 0:
            duration_max, offset = _read_varint(payload, offset)
            continue
        offset = _skip_value(payload, offset, wire_type)
    return SpritePhase(duration_min=int(duration_min), duration_max=int(duration_max))


def _get_sprite_info(index: AppearanceIndex, *, kind: str, appearance_id: int) -> SpriteInfo | None:
    if kind == "object":
        return index.object_info.get(int(appearance_id))
    if kind == "outfit":
        return index.outfit_info.get(int(appearance_id))
    if kind == "effect":
        return index.effect_info.get(int(appearance_id))
    if kind == "missile":
        return index.missile_info.get(int(appearance_id))
    return None


def _read_key(data: bytes, offset: int) -> tuple[int, int, int]:
    key, offset = _read_varint(data, offset)
    field_number = int(key) >> 3
    wire_type = int(key) & 0x07
    return field_number, wire_type, offset


def _read_varint(data: bytes, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    size = len(data)
    while offset < size:
        b = data[offset]
        offset += 1
        value |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            return value, offset
        shift += 7
        if shift > 70:
            break
    raise AppearancesDatError("Invalid varint in appearances.dat")


def _skip_value(data: bytes, offset: int, wire_type: int) -> int:
    if wire_type == 0:  # varint
        _, offset = _read_varint(data, offset)
        return offset
    if wire_type == 1:  # 64-bit
        return offset + 8
    if wire_type == 2:  # length-delimited
        length, offset = _read_varint(data, offset)
        return offset + int(length)
    if wire_type == 5:  # 32-bit
        return offset + 4
    raise AppearancesDatError(f"Unsupported wire type: {wire_type}")
