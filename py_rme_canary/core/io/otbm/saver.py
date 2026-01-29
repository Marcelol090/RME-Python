"""OTBM map saver - serialize GameMap to OTBM binary format.

This module provides functionality to serialize GameMap data structures
back to the OTBM binary format used by Tibia map editors.
"""

from __future__ import annotations

import struct
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from ...constants.item_attributes import (
    ITEMATTR_BOOLEAN,
    ITEMATTR_DOUBLE,
    ITEMATTR_FLOAT,
    ITEMATTR_INTEGER,
    ITEMATTR_NONE,
    ITEMATTR_STRING,
)
from ...constants.otbm import (
    ESCAPE_CHAR,
    MAGIC_OTBM,
    NODE_END,
    NODE_START,
    OTBM_ATTR_ACTION_ID,
    OTBM_ATTR_ATTRIBUTE_MAP,
    OTBM_ATTR_CHARGES,
    OTBM_ATTR_COUNT,
    OTBM_ATTR_DEPOT_ID,
    OTBM_ATTR_DESC,
    OTBM_ATTR_DESCRIPTION,
    OTBM_ATTR_EXT_HOUSE_FILE,
    OTBM_ATTR_EXT_SPAWN_MONSTER_FILE,
    OTBM_ATTR_EXT_SPAWN_NPC_FILE,
    OTBM_ATTR_EXT_ZONE_FILE,
    OTBM_ATTR_HOUSEDOORID,
    OTBM_ATTR_ITEM,
    OTBM_ATTR_RUNE_CHARGES,
    OTBM_ATTR_TELE_DEST,
    OTBM_ATTR_TEXT,
    OTBM_ATTR_TILE_FLAGS,
    OTBM_ATTR_UNIQUE_ID,
    OTBM_HOUSETILE,
    OTBM_ITEM,
    OTBM_MAP_DATA,
    OTBM_ROOTV1,
    OTBM_TILE,
    OTBM_TILE_AREA,
    OTBM_TILE_ZONE,
    OTBM_TOWN,
    OTBM_TOWNS,
    OTBM_WAYPOINT,
    OTBM_WAYPOINTS,
)
from ...data.gamemap import GameMap
from ...data.item import Item, ItemAttribute
from ...data.tile import Tile
from ...database.id_mapper import IdMapper
from ...database.items_xml import ItemsXML
from ..atomic_io import save_bytes_atomic
from ..houses_xml import save_houses
from ..spawn_xml import save_monster_spawns, save_npc_spawns
from ..zones_xml import save_zones

# =============================================================================
# Helper functions
# =============================================================================


def _u8(v: int) -> int:
    """Ensure value fits in unsigned 8-bit."""
    if not (0 <= v <= 0xFF):
        raise ValueError(f"u8 out of range: {v}")
    return v


def _u16(v: int) -> int:
    """Ensure value fits in unsigned 16-bit."""
    if not (0 <= v <= 0xFFFF):
        raise ValueError(f"u16 out of range: {v}")
    return v


def _u32(v: int) -> int:
    """Ensure value fits in unsigned 32-bit."""
    if not (0 <= v <= 0xFFFFFFFF):
        raise ValueError(f"u32 out of range: {v}")
    return v


def _escape_bytes(data: bytes) -> bytes:
    """Escape special bytes in payload data."""
    out = bytearray()
    for b in data:
        if b in (NODE_START, NODE_END, ESCAPE_CHAR):
            out.append(ESCAPE_CHAR)
        out.append(b)
    return bytes(out)


def _node_bytes(node_type: int, payload: bytes, children: tuple[bytes, ...] = ()) -> bytes:
    """Build a complete node with type, payload, and children.

    Important: there is no explicit payload length.
    Payload ends when an unescaped NODE_START (first child) or NODE_END is seen.
    """
    out = bytearray()
    out.append(NODE_START)
    out.append(node_type & 0xFF)
    out += _escape_bytes(payload)
    for child in children:
        out += child
    out.append(NODE_END)
    return bytes(out)


def _string_attr(tag: int, text: str) -> bytes:
    """Build a string attribute with tag and length-prefixed text."""
    raw = (text or "").encode("utf-8", errors="replace")
    if len(raw) > 0xFFFF:
        raw = raw[:0xFFFF]
    return struct.pack("<BH", _u8(tag), _u16(len(raw))) + raw


def _string_payload(text: str) -> bytes:
    """Build a length-prefixed string for payload (no tag)."""
    raw = (text or "").encode("utf-8", errors="replace")
    if len(raw) > 0xFFFF:
        raw = raw[:0xFFFF]
    return struct.pack("<H", _u16(len(raw))) + raw


def _is_compact_ground_item(item: Item) -> bool:
    """Check if item can be written as compact tile attribute.

    RME only writes a compact item in the tile payload for simple ground.
    Compact payload cannot represent attributes/containers, so be conservative.
    """
    return (
        item.action_id is None
        and item.unique_id is None
        and not item.text
        and not item.description
        and item.destination is None
        and item.count is None
        and item.subtype is None
        and item.depot_id is None
        and item.house_door_id is None
        and not item.items
        and not item.attribute_map
    )


def _resolve_item_id_for_save(
    item_id: int,
    *,
    id_mapper: IdMapper | None,
    otbm_version: int,
) -> int:
    if int(otbm_version) >= 5:
        if id_mapper is None:
            raise ValueError("id_mapper is required to save ClientID OTBM (version >= 5)")
        mapped = id_mapper.get_client_id(int(item_id))
        if mapped is None:
            raise ValueError(f"No client id mapping for server id {item_id}")
        return int(mapped)
    return int(item_id)


# =============================================================================
# Attribute map handling
# =============================================================================


def _build_attribute_map_attr(entries: tuple[ItemAttribute, ...]) -> bytes:
    """Build OTBM_ATTR_ATTRIBUTE_MAP payload from ItemAttribute entries."""
    out = bytearray()
    out += struct.pack("<BH", _u8(OTBM_ATTR_ATTRIBUTE_MAP), _u16(len(entries)))

    for entry in entries:
        key = bytes(entry.key_bytes)
        if len(key) > 0xFFFF:
            key = key[:0xFFFF]
        out += struct.pack("<H", _u16(len(key))) + key

        atype = int(entry.type)
        out += struct.pack("<B", _u8(atype))

        raw = bytes(entry.raw)
        if atype == ITEMATTR_NONE:
            continue
        if atype == ITEMATTR_STRING:
            out += struct.pack("<I", len(raw) & 0xFFFFFFFF) + raw
            continue
        if atype in (ITEMATTR_INTEGER, ITEMATTR_FLOAT):
            if len(raw) != 4:
                raise ValueError(f"Invalid attribute-map raw size for type {atype}: expected 4, got {len(raw)}")
            out += raw
            continue
        if atype == ITEMATTR_DOUBLE:
            if len(raw) != 8:
                raise ValueError(f"Invalid attribute-map raw size for type {atype}: expected 8, got {len(raw)}")
            out += raw
            continue
        if atype == ITEMATTR_BOOLEAN:
            if len(raw) != 1:
                raise ValueError(f"Invalid attribute-map raw size for type {atype}: expected 1, got {len(raw)}")
            out += raw
            continue

        raise ValueError(f"Unsupported attribute-map type: {atype}")

    return bytes(out)


def _merge_attribute_map_with_derived(item: Item) -> tuple[ItemAttribute, ...]:
    """Merge existing attribute_map with derived attributes from item fields."""
    existing = item.attribute_map
    if not existing and (
        item.action_id is None
        and item.unique_id is None
        and not item.text
        and not item.description
        and item.destination is None
        and item.depot_id is None
        and item.house_door_id is None
        and item.subtype is None
    ):
        return ()

    present_keys = {e.key_bytes for e in existing}
    derived: list[ItemAttribute] = []

    def add_i32(key: bytes, value: int | None) -> None:
        if value is None:
            return
        if key in present_keys:
            return
        raw = int(value).to_bytes(4, "little", signed=True)
        derived.append(ItemAttribute(key_bytes=key, type=ITEMATTR_INTEGER, raw=raw))

    def add_str(key: bytes, value: str | None) -> None:
        if not value:
            return
        if key in present_keys:
            return
        raw = (value or "").encode("utf-8", errors="replace")
        derived.append(ItemAttribute(key_bytes=key, type=ITEMATTR_STRING, raw=raw))

    add_i32(b"aid", item.action_id)
    add_i32(b"uid", item.unique_id)
    add_str(b"text", item.text)
    add_str(b"desc", item.description)
    add_i32(b"subtype", item.subtype)
    add_i32(b"depotid", item.depot_id)
    add_i32(b"doorid", item.house_door_id)

    if item.destination is not None:
        add_i32(b"destination.x", int(item.destination.x))
        add_i32(b"destination.y", int(item.destination.y))
        add_i32(b"destination.z", int(item.destination.z))

    if not derived:
        return existing
    return tuple(existing) + tuple(derived)


# =============================================================================
# Item serialization
# =============================================================================


def _build_item_payload(
    item: Item,
    items_db: ItemsXML | None,
    *,
    otbm_version: int,
    id_mapper: IdMapper | None,
) -> bytes:
    """Build the binary payload for an item node."""
    # OTBM stores the ServerID / logical id (or ClientID for v5+).
    if int(item.id) == 0:
        raise ValueError(
            "Refusing to serialize Item with server id 0 (likely an unknown-id placeholder from the loader)"
        )
    resolved_id = _resolve_item_id_for_save(int(item.id), id_mapper=id_mapper, otbm_version=int(otbm_version))
    payload = bytearray(struct.pack("<H", _u16(int(resolved_id))))

    # Legacy parity (RME): in OTBM v1, stackable/fluid/splash write subtype as a raw u8
    # directly after the item id.
    if int(otbm_version) == 1 and items_db is not None:
        it_type = items_db.get(int(item.id))
        if it_type is not None and (it_type.stackable or it_type.fluid_container or it_type.splash):
            st = int(item.subtype) if item.subtype is not None else int(item.count) if item.count is not None else 1
            payload += struct.pack("<B", _u8(st & 0xFF))

    # Count/subtype heuristics
    if items_db is not None and int(otbm_version) >= 2:
        it_type = items_db.get(int(item.id))
        if it_type is not None and (it_type.stackable or it_type.fluid_container or it_type.splash):
            # Legacy parity: for OTBM>=2, these types always encode subtype via COUNT (u8).
            st = int(item.subtype) if item.subtype is not None else int(item.count) if item.count is not None else 1
            payload += struct.pack("<BB", _u8(OTBM_ATTR_COUNT), _u8(st & 0xFF))
        else:
            # Non-stackable: use count when explicitly set, else encode subtype as charges.
            effective_count = item.count
            if effective_count is not None and int(effective_count) != 1:
                payload += struct.pack("<BB", _u8(OTBM_ATTR_COUNT), _u8(int(effective_count)))
            elif item.subtype is not None:
                st = int(item.subtype)
                if 0 <= st <= 0xFF:
                    payload += struct.pack("<BB", _u8(OTBM_ATTR_RUNE_CHARGES), _u8(st))
                else:
                    payload += struct.pack("<BH", _u8(OTBM_ATTR_CHARGES), _u16(st & 0xFFFF))
    else:
        # No items_db semantics: keep conservative heuristic.
        effective_count = item.count
        if effective_count is not None and int(effective_count) != 1:
            payload += struct.pack("<BB", _u8(OTBM_ATTR_COUNT), _u8(int(effective_count)))
        elif item.subtype is not None:
            st = int(item.subtype)
            if 0 <= st <= 0xFF:
                payload += struct.pack("<BB", _u8(OTBM_ATTR_RUNE_CHARGES), _u8(st))
            else:
                payload += struct.pack("<BH", _u8(OTBM_ATTR_CHARGES), _u16(st & 0xFFFF))

    # Standard attributes
    if item.action_id is not None and int(item.action_id) > 0:
        payload += struct.pack("<BH", _u8(OTBM_ATTR_ACTION_ID), _u16(int(item.action_id)))

    if item.unique_id is not None and int(item.unique_id) > 0:
        payload += struct.pack("<BH", _u8(OTBM_ATTR_UNIQUE_ID), _u16(int(item.unique_id)))

    if item.text:
        payload += _string_attr(OTBM_ATTR_TEXT, item.text)

    if item.description:
        payload += _string_attr(OTBM_ATTR_DESC, item.description)

    if item.destination is not None:
        d = item.destination
        payload += struct.pack(
            "<BHHB",
            _u8(OTBM_ATTR_TELE_DEST),
            _u16(int(d.x)),
            _u16(int(d.y)),
            _u8(int(d.z)),
        )

    if item.depot_id is not None and int(item.depot_id) >= 0:
        payload += struct.pack("<BH", _u8(OTBM_ATTR_DEPOT_ID), _u16(int(item.depot_id)))

    if item.house_door_id is not None and int(item.house_door_id) >= 0:
        payload += struct.pack("<BB", _u8(OTBM_ATTR_HOUSEDOORID), _u8(int(item.house_door_id)))

    # Attribute map
    if item.attribute_map:
        payload += _build_attribute_map_attr(_merge_attribute_map_with_derived(item))
    else:
        derived = _merge_attribute_map_with_derived(item)
        if derived:
            payload += _build_attribute_map_attr(derived)

    return bytes(payload)


def _build_item_node(
    item: Item,
    items_db: ItemsXML | None,
    *,
    otbm_version: int,
    id_mapper: IdMapper | None,
) -> bytes:
    """Build a complete OTBM_ITEM node including children (container contents)."""
    payload = _build_item_payload(item, items_db, otbm_version=int(otbm_version), id_mapper=id_mapper)
    children: tuple[bytes, ...] = ()
    if item.items:
        children = tuple(
            _build_item_node(ch, items_db, otbm_version=int(otbm_version), id_mapper=id_mapper)
            for ch in item.items
        )
    return _node_bytes(OTBM_ITEM, payload, children)


# =============================================================================
# Tile serialization
# =============================================================================


def _build_tile_node(
    *,
    base_x: int,
    base_y: int,
    tile: Tile,
    otbm_version: int,
    id_mapper: IdMapper | None,
) -> bytes:
    """Build a complete tile node (without items_db semantics)."""
    rel_x = tile.x - base_x
    rel_y = tile.y - base_y
    if not (0 <= rel_x <= 255 and 0 <= rel_y <= 255):
        raise ValueError(f"Tile out of area bounds: ({tile.x},{tile.y}) vs base ({base_x},{base_y})")

    node_type = OTBM_HOUSETILE if tile.house_id is not None else OTBM_TILE

    payload = bytearray(struct.pack("<BB", _u8(rel_x), _u8(rel_y)))
    if tile.house_id is not None:
        payload += struct.pack("<I", int(tile.house_id) & 0xFFFFFFFF)

    if int(tile.map_flags) != 0:
        payload += struct.pack("<BI", _u8(OTBM_ATTR_TILE_FLAGS), int(tile.map_flags) & 0xFFFFFFFF)

    # RME behavior: ground is often stored as a compact item (OTBM_ATTR_ITEM)
    children_items: list[Item] = []
    if tile.ground is not None:
        if int(otbm_version) >= 2 and _is_compact_ground_item(tile.ground):
            resolved_id = _resolve_item_id_for_save(
                int(tile.ground.id),
                id_mapper=id_mapper,
                otbm_version=int(otbm_version),
            )
            payload += struct.pack("<BH", _u8(OTBM_ATTR_ITEM), _u16(int(resolved_id)))
        else:
            children_items.append(tile.ground)

    children_items.extend(tile.items)

    children: list[bytes] = [
        _build_item_node(it, None, otbm_version=int(otbm_version), id_mapper=id_mapper) for it in children_items
    ]
    if tile.zones:
        zones_sorted = sorted(int(z) for z in tile.zones)
        zp = bytearray(struct.pack("<H", _u16(len(zones_sorted))))
        for zid in zones_sorted:
            zp += struct.pack("<H", _u16(int(zid)))
        children.append(_node_bytes(OTBM_TILE_ZONE, bytes(zp)))
    return _node_bytes(node_type, bytes(payload), tuple(children))


def _build_tile_node_with_items_db(
    *,
    base_x: int,
    base_y: int,
    tile: Tile,
    items_db: ItemsXML,
    otbm_version: int,
    id_mapper: IdMapper | None,
) -> bytes:
    """Build a complete tile node with items_db semantics."""
    rel_x = tile.x - base_x
    rel_y = tile.y - base_y
    if not (0 <= rel_x <= 255 and 0 <= rel_y <= 255):
        raise ValueError(f"Tile out of area bounds: ({tile.x},{tile.y}) vs base ({base_x},{base_y})")

    node_type = OTBM_HOUSETILE if tile.house_id is not None else OTBM_TILE

    payload = bytearray(struct.pack("<BB", _u8(rel_x), _u8(rel_y)))
    if tile.house_id is not None:
        payload += struct.pack("<I", int(tile.house_id) & 0xFFFFFFFF)

    if int(tile.map_flags) != 0:
        payload += struct.pack("<BI", _u8(OTBM_ATTR_TILE_FLAGS), int(tile.map_flags) & 0xFFFFFFFF)

    children_items: list[Item] = []
    if tile.ground is not None:
        if int(otbm_version) >= 2 and _is_compact_ground_item(tile.ground):
            resolved_id = _resolve_item_id_for_save(
                int(tile.ground.id),
                id_mapper=id_mapper,
                otbm_version=int(otbm_version),
            )
            payload += struct.pack("<BH", _u8(OTBM_ATTR_ITEM), _u16(int(resolved_id)))
        else:
            children_items.append(tile.ground)

    children_items.extend(tile.items)

    children: list[bytes] = [
        _build_item_node(it, items_db, otbm_version=int(otbm_version), id_mapper=id_mapper)
        for it in children_items
    ]
    if tile.zones:
        zones_sorted = sorted(int(z) for z in tile.zones)
        zp = bytearray(struct.pack("<H", _u16(len(zones_sorted))))
        for zid in zones_sorted:
            zp += struct.pack("<H", _u16(int(zid)))
        children.append(_node_bytes(OTBM_TILE_ZONE, bytes(zp)))
    return _node_bytes(node_type, bytes(payload), tuple(children))


# =============================================================================
# Map structure building
# =============================================================================


@dataclass(frozen=True, slots=True)
class _AreaKey:
    """Key for grouping tiles by 256x256 area."""

    base_x: int
    base_y: int
    z: int


def _group_tiles_into_areas(tiles: Iterable[Tile]) -> dict[_AreaKey, list[Tile]]:
    """Group tiles by their containing 256x256 area."""
    out: dict[_AreaKey, list[Tile]] = {}
    for t in tiles:
        base_x = (int(t.x) // 256) * 256
        base_y = (int(t.y) // 256) * 256
        key = _AreaKey(base_x=base_x, base_y=base_y, z=int(t.z))
        out.setdefault(key, []).append(t)
    return out


def _build_map_data_payload(game_map: GameMap) -> bytes:
    """Build the MAP_DATA node payload (description, external file refs)."""
    h = game_map.header
    out = bytearray()
    if h.description:
        out += _string_attr(OTBM_ATTR_DESCRIPTION, h.description)
    if h.spawnmonsterfile:
        out += _string_attr(OTBM_ATTR_EXT_SPAWN_MONSTER_FILE, h.spawnmonsterfile)
    if h.housefile:
        out += _string_attr(OTBM_ATTR_EXT_HOUSE_FILE, h.housefile)
    if h.spawnnpcfile:
        out += _string_attr(OTBM_ATTR_EXT_SPAWN_NPC_FILE, h.spawnnpcfile)
    if h.zonefile:
        out += _string_attr(OTBM_ATTR_EXT_ZONE_FILE, h.zonefile)
    return bytes(out)


# =============================================================================
# Public API
# =============================================================================


def serialize(
    game_map: GameMap,
    *,
    items_db: ItemsXML | None = None,
    id_mapper: IdMapper | None = None,
) -> bytes:
    """Serialize a GameMap to OTBM binary format.

    Args:
        game_map: The map to serialize.
        items_db: Optional items database for semantic handling.

    Returns:
        The complete OTBM file as bytes.
    """
    # Root header: version, width, height, major/minor items.
    # RME writes major/minor item versions; we keep 4/4 for compatibility.
    h = game_map.header
    root_payload = struct.pack(
        "<IHHII",
        int(h.otbm_version),
        _u16(int(h.width)),
        _u16(int(h.height)),
        4,
        4,
    )

    areas = _group_tiles_into_areas(game_map.tiles.values())
    area_nodes: list[bytes] = []
    for key, tiles in areas.items():
        tiles_sorted = sorted(tiles, key=lambda t: (t.x, t.y, t.z))
        payload = struct.pack("<HHB", _u16(key.base_x), _u16(key.base_y), _u8(key.z))
        if items_db is None:
            children = tuple(
                _build_tile_node(
                    base_x=key.base_x,
                    base_y=key.base_y,
                    tile=t,
                    otbm_version=int(h.otbm_version),
                    id_mapper=id_mapper,
                )
                for t in tiles_sorted
            )
        else:
            children = tuple(
                _build_tile_node_with_items_db(
                    base_x=key.base_x,
                    base_y=key.base_y,
                    tile=t,
                    items_db=items_db,
                    otbm_version=int(h.otbm_version),
                    id_mapper=id_mapper,
                )
                for t in tiles_sorted
            )
        area_nodes.append(_node_bytes(OTBM_TILE_AREA, payload, children))

    map_children: list[bytes] = list(area_nodes)

    # Towns
    if getattr(game_map, "towns", None):
        towns_children: list[bytes] = []
        for tid, town in sorted(game_map.towns.items(), key=lambda kv: int(kv[0])):
            t_payload = bytearray()
            t_payload += struct.pack("<I", _u32(int(tid)))
            t_payload += _string_payload(str(getattr(town, "name", "")))
            pos = getattr(town, "temple_position", None)
            if pos is None:
                x = y = 0
                z = 7
            else:
                x = int(getattr(pos, "x", 0))
                y = int(getattr(pos, "y", 0))
                z = int(getattr(pos, "z", 7))
            t_payload += struct.pack("<HHB", _u16(x), _u16(y), _u8(z))
            towns_children.append(_node_bytes(OTBM_TOWN, bytes(t_payload)))
        map_children.append(_node_bytes(OTBM_TOWNS, b"", tuple(towns_children)))

    # Waypoints
    if game_map.waypoints:
        wp_children: list[bytes] = []
        for name, pos in sorted(game_map.waypoints.items(), key=lambda kv: kv[0].casefold()):
            wp_payload = bytearray()
            wp_payload += _string_payload(str(name))
            wp_payload += struct.pack("<HHB", _u16(int(pos.x)), _u16(int(pos.y)), _u8(int(pos.z)))
            wp_children.append(_node_bytes(OTBM_WAYPOINT, bytes(wp_payload)))
        map_children.append(_node_bytes(OTBM_WAYPOINTS, b"", tuple(wp_children)))

    map_data_payload = _build_map_data_payload(game_map)
    map_data_node = _node_bytes(OTBM_MAP_DATA, map_data_payload, tuple(map_children))

    root_node = _node_bytes(OTBM_ROOTV1, root_payload, (map_data_node,))

    return MAGIC_OTBM + root_node


def save_game_map_atomic(path: str, game_map: GameMap, *, id_mapper: IdMapper | None = None) -> None:
    """Save a GameMap atomically (no items_db)."""
    save_bytes_atomic(path, serialize(game_map, id_mapper=id_mapper))


def save_game_map_atomic_with_items_db(
    path: str,
    game_map: GameMap,
    *,
    items_db: ItemsXML,
    id_mapper: IdMapper | None = None,
) -> None:
    """Save a GameMap atomically with items_db semantics."""
    save_bytes_atomic(path, serialize(game_map, items_db=items_db, id_mapper=id_mapper))


def save_game_map_bundle_atomic(
    path: str,
    game_map: GameMap,
    *,
    items_db: ItemsXML | None = None,
    id_mapper: IdMapper | None = None,
    save_externals: bool = True,
) -> None:
    """Save an OTBM and its referenced external XML files.

    External files are saved only when their filename is present in the header.
    Paths are resolved relative to the OTBM location unless already absolute.
    """
    save_bytes_atomic(path, serialize(game_map, items_db=items_db, id_mapper=id_mapper))

    if not save_externals:
        return

    base_dir = Path(path).parent
    h = game_map.header

    def resolve(p: str) -> Path:
        pp = Path(p)
        return pp if pp.is_absolute() else (base_dir / pp)

    if h.spawnmonsterfile:
        p = resolve(h.spawnmonsterfile)
        p.parent.mkdir(parents=True, exist_ok=True)
        save_monster_spawns(p, game_map.monster_spawns)

    if h.spawnnpcfile:
        p = resolve(h.spawnnpcfile)
        p.parent.mkdir(parents=True, exist_ok=True)
        save_npc_spawns(p, game_map.npc_spawns)

    if h.housefile:
        p = resolve(h.housefile)
        p.parent.mkdir(parents=True, exist_ok=True)
        save_houses(p, game_map.houses.values())

    if h.zonefile:
        p = resolve(h.zonefile)
        p.parent.mkdir(parents=True, exist_ok=True)
        save_zones(p, game_map.zones.values())
