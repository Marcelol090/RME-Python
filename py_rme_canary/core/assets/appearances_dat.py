from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


class AppearancesDatError(RuntimeError):
    """Raised when appearances.dat parsing fails."""


# ---------------------------------------------------------------------------
# AppearanceFlags – parsed from protobuf field 3 of each Appearance message.
# Field numbers follow the Canary/TFS appearances.proto specification.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AppearanceFlagLight:
    """Light emission parameters (proto field 23 in AppearanceFlags)."""

    brightness: int = 0
    color: int = 0


@dataclass(frozen=True, slots=True)
class AppearanceFlagMarket:
    """Market/trade metadata (proto field 36 in AppearanceFlags)."""

    category: int = 0
    trade_as_object_id: int = 0
    show_as_object_id: int = 0
    minimum_level: int = 0


@dataclass(frozen=True, slots=True)
class AppearanceFlags:
    """Item property flags extracted from appearances.dat.

    Proto reference: ``message AppearanceFlags`` in Canary appearances.proto.
    Only boolean flags that are *absent* default to ``False``.
    """

    # Ground/bank (field 1) – ground speed stored as ``ground_speed``
    is_ground: bool = False
    ground_speed: int = 0
    # Rendering layers
    is_clip: bool = False          # field 2 – border clip
    is_bottom: bool = False        # field 3
    is_top: bool = False           # field 4
    # Item properties
    is_container: bool = False     # field 5
    is_stackable: bool = False     # field 6  (cumulative)
    is_usable: bool = False        # field 7
    is_forceuse: bool = False      # field 8
    is_multiuse: bool = False      # field 9
    # Writable
    is_writable: bool = False      # field 10
    max_text_length: int = 0
    is_writable_once: bool = False  # field 11
    max_text_length_once: int = 0
    # Physics
    is_liquidpool: bool = False    # field 12
    is_unpassable: bool = False    # field 13
    is_unmoveable: bool = False    # field 14
    blocks_projectiles: bool = False  # field 15 (unsight)
    is_avoid: bool = False         # field 16
    no_movement_animation: bool = False  # field 17
    is_pickupable: bool = False    # field 18  (take)
    is_liquid_container: bool = False  # field 19
    # Wall/hang
    is_hangable: bool = False      # field 20
    hook_direction: int = 0        # field 21 (0=none, 1=south, 2=east)
    is_rotatable: bool = False     # field 22
    # Light
    light: AppearanceFlagLight | None = None  # field 23
    # Visual
    dont_hide: bool = False        # field 24
    is_translucent: bool = False   # field 25
    shift_x: int = 0              # field 26
    shift_y: int = 0
    elevation: int = 0            # field 27
    is_lying_object: bool = False  # field 28
    animate_always: bool = False   # field 29
    # Minimap
    minimap_color: int = 0         # field 30 (automap)
    has_minimap_color: bool = False
    # Lens help
    lenshelp_id: int = 0           # field 31
    # Full bank
    is_fullbank: bool = False      # field 32
    is_ignore_look: bool = False   # field 33
    # Wearable
    clothes_slot: int = 0          # field 34
    # Default action
    default_action: int = 0        # field 35
    # Market
    market: AppearanceFlagMarket | None = None  # field 36
    # Wrap
    is_wrappable: bool = False     # field 37
    is_unwrappable: bool = False   # field 38
    is_topeffect: bool = False     # field 39
    # Corpse
    is_corpse: bool = False        # field 42
    is_player_corpse: bool = False  # field 43
    # Ammo
    is_ammo: bool = False          # field 45


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
    object_flags: dict[int, AppearanceFlags] = field(default_factory=dict)

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

    def get_flags(self, appearance_id: int) -> AppearanceFlags | None:
        """Return parsed AppearanceFlags for an object, or None if not found."""
        return self.object_flags.get(int(appearance_id))


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
        appearance_id, sprite_info, flags = _parse_appearance(payload)
        if appearance_id is None or sprite_info is None:
            continue
        if kind == "object":
            index.object_info[int(appearance_id)] = sprite_info
            sprite_id = sprite_info.sprite_id_for_phase(0)
            if sprite_id is not None:
                index.object_sprites[int(appearance_id)] = int(sprite_id)
            if flags is not None:
                index.object_flags[int(appearance_id)] = flags
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


def _parse_appearance(payload: bytes) -> tuple[int | None, SpriteInfo | None, AppearanceFlags | None]:
    appearance_id: int | None = None
    sprite_info: SpriteInfo | None = None
    flags: AppearanceFlags | None = None
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
        if field_number == 3 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            flags_payload = payload[offset : offset + length]
            offset += length
            flags = _parse_appearance_flags(flags_payload)
            continue
        offset = _skip_value(payload, offset, wire_type)
    return appearance_id, sprite_info, flags


def _parse_appearance_flags(payload: bytes) -> AppearanceFlags:
    """Parse the AppearanceFlags sub-message (proto field 3 of Appearance).

    Field numbers follow the Canary appearances.proto specification.
    """
    offset = 0
    size = len(payload)

    is_ground = False
    ground_speed = 0
    is_clip = False
    is_bottom = False
    is_top = False
    is_container = False
    is_stackable = False
    is_usable = False
    is_forceuse = False
    is_multiuse = False
    is_writable = False
    max_text_length = 0
    is_writable_once = False
    max_text_length_once = 0
    is_liquidpool = False
    is_unpassable = False
    is_unmoveable = False
    blocks_projectiles = False
    is_avoid = False
    no_movement_animation = False
    is_pickupable = False
    is_liquid_container = False
    is_hangable = False
    hook_direction = 0
    is_rotatable = False
    light: AppearanceFlagLight | None = None
    dont_hide = False
    is_translucent = False
    shift_x = 0
    shift_y = 0
    elevation_val = 0
    is_lying_object = False
    animate_always = False
    minimap_color = 0
    has_minimap_color = False
    lenshelp_id = 0
    is_fullbank = False
    is_ignore_look = False
    clothes_slot = 0
    default_action = 0
    market: AppearanceFlagMarket | None = None
    is_wrappable = False
    is_unwrappable = False
    is_topeffect = False
    is_corpse = False
    is_player_corpse = False
    is_ammo = False

    while offset < size:
        field_number, wire_type, offset = _read_key(payload, offset)

        # field 1: bank (sub-message) → is_ground + ground_speed
        if field_number == 1 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            is_ground = True
            ground_speed = _parse_single_uint32(sub, target_field=1)
            continue
        # field 2: clip (bool)
        if field_number == 2 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_clip = bool(val)
            continue
        # field 3: bottom (bool)
        if field_number == 3 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_bottom = bool(val)
            continue
        # field 4: top (bool)
        if field_number == 4 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_top = bool(val)
            continue
        # field 5: container (bool)
        if field_number == 5 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_container = bool(val)
            continue
        # field 6: cumulative / stackable (bool)
        if field_number == 6 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_stackable = bool(val)
            continue
        # field 7: usable (bool)
        if field_number == 7 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_usable = bool(val)
            continue
        # field 8: forceuse (bool)
        if field_number == 8 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_forceuse = bool(val)
            continue
        # field 9: multiuse (bool)
        if field_number == 9 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_multiuse = bool(val)
            continue
        # field 10: write (sub-message) → is_writable + max_text_length
        if field_number == 10 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            is_writable = True
            max_text_length = _parse_single_uint32(sub, target_field=1)
            continue
        # field 11: write_once (sub-message)
        if field_number == 11 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            is_writable_once = True
            max_text_length_once = _parse_single_uint32(sub, target_field=1)
            continue
        # field 12: liquidpool (bool)
        if field_number == 12 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_liquidpool = bool(val)
            continue
        # field 13: unpass (bool)
        if field_number == 13 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_unpassable = bool(val)
            continue
        # field 14: unmove (bool)
        if field_number == 14 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_unmoveable = bool(val)
            continue
        # field 15: unsight (bool) → blocks projectiles
        if field_number == 15 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            blocks_projectiles = bool(val)
            continue
        # field 16: avoid (bool)
        if field_number == 16 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_avoid = bool(val)
            continue
        # field 17: no_movement_animation (bool)
        if field_number == 17 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            no_movement_animation = bool(val)
            continue
        # field 18: take / pickupable (bool)
        if field_number == 18 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_pickupable = bool(val)
            continue
        # field 19: liquidcontainer (bool)
        if field_number == 19 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_liquid_container = bool(val)
            continue
        # field 20: hang (bool)
        if field_number == 20 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_hangable = bool(val)
            continue
        # field 21: hook (sub-message) → hook direction
        if field_number == 21 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            hook_direction = _parse_single_uint32(sub, target_field=1)
            continue
        # field 22: rotate (bool)
        if field_number == 22 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_rotatable = bool(val)
            continue
        # field 23: light (sub-message)
        if field_number == 23 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            light = _parse_light_flag(sub)
            continue
        # field 24: dont_hide (bool)
        if field_number == 24 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            dont_hide = bool(val)
            continue
        # field 25: translucent (bool)
        if field_number == 25 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_translucent = bool(val)
            continue
        # field 26: shift (sub-message) → displacement x, y
        if field_number == 26 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            shift_x, shift_y = _parse_shift_flag(sub)
            continue
        # field 27: height (sub-message) → elevation
        if field_number == 27 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            elevation_val = _parse_single_uint32(sub, target_field=1)
            continue
        # field 28: lying_object (bool)
        if field_number == 28 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_lying_object = bool(val)
            continue
        # field 29: animate_always (bool)
        if field_number == 29 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            animate_always = bool(val)
            continue
        # field 30: automap (sub-message) → minimap color
        if field_number == 30 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            minimap_color = _parse_single_uint32(sub, target_field=1)
            has_minimap_color = True
            continue
        # field 31: lenshelp (sub-message)
        if field_number == 31 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            lenshelp_id = _parse_single_uint32(sub, target_field=1)
            continue
        # field 32: fullbank (bool)
        if field_number == 32 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_fullbank = bool(val)
            continue
        # field 33: ignore_look (bool)
        if field_number == 33 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_ignore_look = bool(val)
            continue
        # field 34: clothes (sub-message) → slot
        if field_number == 34 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            clothes_slot = _parse_single_uint32(sub, target_field=1)
            continue
        # field 35: default_action (sub-message) → action enum
        if field_number == 35 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            default_action = _parse_single_uint32(sub, target_field=1)
            continue
        # field 36: market (sub-message)
        if field_number == 36 and wire_type == 2:
            length, offset = _read_varint(payload, offset)
            sub = payload[offset : offset + length]
            offset += length
            market = _parse_market_flag(sub)
            continue
        # field 37: wrap (bool)
        if field_number == 37 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_wrappable = bool(val)
            continue
        # field 38: unwrap (bool)
        if field_number == 38 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_unwrappable = bool(val)
            continue
        # field 39: topeffect (bool)
        if field_number == 39 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_topeffect = bool(val)
            continue
        # field 42: corpse (bool)
        if field_number == 42 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_corpse = bool(val)
            continue
        # field 43: player_corpse (bool)
        if field_number == 43 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_player_corpse = bool(val)
            continue
        # field 45: ammo (bool)
        if field_number == 45 and wire_type == 0:
            val, offset = _read_varint(payload, offset)
            is_ammo = bool(val)
            continue
        # Skip unknown fields
        offset = _skip_value(payload, offset, wire_type)

    return AppearanceFlags(
        is_ground=is_ground,
        ground_speed=int(ground_speed),
        is_clip=is_clip,
        is_bottom=is_bottom,
        is_top=is_top,
        is_container=is_container,
        is_stackable=is_stackable,
        is_usable=is_usable,
        is_forceuse=is_forceuse,
        is_multiuse=is_multiuse,
        is_writable=is_writable,
        max_text_length=int(max_text_length),
        is_writable_once=is_writable_once,
        max_text_length_once=int(max_text_length_once),
        is_liquidpool=is_liquidpool,
        is_unpassable=is_unpassable,
        is_unmoveable=is_unmoveable,
        blocks_projectiles=blocks_projectiles,
        is_avoid=is_avoid,
        no_movement_animation=no_movement_animation,
        is_pickupable=is_pickupable,
        is_liquid_container=is_liquid_container,
        is_hangable=is_hangable,
        hook_direction=int(hook_direction),
        is_rotatable=is_rotatable,
        light=light,
        dont_hide=dont_hide,
        is_translucent=is_translucent,
        shift_x=int(shift_x),
        shift_y=int(shift_y),
        elevation=int(elevation_val),
        is_lying_object=is_lying_object,
        animate_always=animate_always,
        minimap_color=int(minimap_color),
        has_minimap_color=has_minimap_color,
        lenshelp_id=int(lenshelp_id),
        is_fullbank=is_fullbank,
        is_ignore_look=is_ignore_look,
        clothes_slot=int(clothes_slot),
        default_action=int(default_action),
        market=market,
        is_wrappable=is_wrappable,
        is_unwrappable=is_unwrappable,
        is_topeffect=is_topeffect,
        is_corpse=is_corpse,
        is_player_corpse=is_player_corpse,
        is_ammo=is_ammo,
    )


def _parse_single_uint32(payload: bytes, *, target_field: int) -> int:
    """Extract a single uint32 from a tiny sub-message (e.g. AppearanceFlagBank)."""
    off = 0
    sz = len(payload)
    while off < sz:
        fn, wt, off = _read_key(payload, off)
        if fn == target_field and wt == 0:
            val, off = _read_varint(payload, off)
            return int(val)
        off = _skip_value(payload, off, wt)
    return 0


def _parse_light_flag(payload: bytes) -> AppearanceFlagLight:
    """Parse AppearanceFlagLight (brightness=1, color=2)."""
    brightness = 0
    color = 0
    off = 0
    sz = len(payload)
    while off < sz:
        fn, wt, off = _read_key(payload, off)
        if fn == 1 and wt == 0:
            brightness, off = _read_varint(payload, off)
            continue
        if fn == 2 and wt == 0:
            color, off = _read_varint(payload, off)
            continue
        off = _skip_value(payload, off, wt)
    return AppearanceFlagLight(brightness=int(brightness), color=int(color))


def _parse_shift_flag(payload: bytes) -> tuple[int, int]:
    """Parse AppearanceFlagShift (x=1, y=2)."""
    x = 0
    y = 0
    off = 0
    sz = len(payload)
    while off < sz:
        fn, wt, off = _read_key(payload, off)
        if fn == 1 and wt == 0:
            x, off = _read_varint(payload, off)
            continue
        if fn == 2 and wt == 0:
            y, off = _read_varint(payload, off)
            continue
        off = _skip_value(payload, off, wt)
    return int(x), int(y)


def _parse_market_flag(payload: bytes) -> AppearanceFlagMarket:
    """Parse AppearanceFlagMarket (category=1, trade_as=2, show_as=3, min_level=6)."""
    category = 0
    trade_as = 0
    show_as = 0
    min_level = 0
    off = 0
    sz = len(payload)
    while off < sz:
        fn, wt, off = _read_key(payload, off)
        if fn == 1 and wt == 0:
            category, off = _read_varint(payload, off)
            continue
        if fn == 2 and wt == 0:
            trade_as, off = _read_varint(payload, off)
            continue
        if fn == 3 and wt == 0:
            show_as, off = _read_varint(payload, off)
            continue
        if fn == 6 and wt == 0:
            min_level, off = _read_varint(payload, off)
            continue
        off = _skip_value(payload, off, wt)
    return AppearanceFlagMarket(
        category=int(category),
        trade_as_object_id=int(trade_as),
        show_as_object_id=int(show_as),
        minimum_level=int(min_level),
    )


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
