"""Item parsing utilities for OTBM format.

Handles parsing of OTBM_ITEM nodes and item attributes.
"""

from __future__ import annotations

import struct
from collections.abc import Callable
from contextlib import suppress

from py_rme_canary.core.constants import (
    ITEMATTR_BOOLEAN,
    ITEMATTR_DOUBLE,
    ITEMATTR_FLOAT,
    ITEMATTR_INTEGER,
    ITEMATTR_NONE,
    ITEMATTR_STRING,
    OTBM_ATTR_ACTION_ID,
    OTBM_ATTR_ATTRIBUTE_MAP,
    OTBM_ATTR_CHARGES,
    OTBM_ATTR_COUNT,
    OTBM_ATTR_DEPOT_ID,
    OTBM_ATTR_DESC,
    OTBM_ATTR_HOUSEDOORID,
    OTBM_ATTR_RUNE_CHARGES,
    OTBM_ATTR_TELE_DEST,
    OTBM_ATTR_TEXT,
    OTBM_ATTR_UNIQUE_ID,
)
from py_rme_canary.core.data.item import Item, ItemAttribute, Position
from py_rme_canary.core.database.id_mapper import IdMapper
from py_rme_canary.core.database.items_xml import ItemsXML
from py_rme_canary.core.exceptions import OTBMParseError

from .streaming import EscapedPayloadReader, read_string, read_string_bytes


def read_attribute_map(payload: EscapedPayloadReader) -> tuple[ItemAttribute, ...]:
    """Read an OTBM_ATTR_ATTRIBUTE_MAP from payload."""
    n = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
    out: list[ItemAttribute] = []

    for _ in range(int(n)):
        key_bytes = read_string_bytes(payload)
        atype = payload.read_escaped_bytes(1)[0]

        if atype == ITEMATTR_STRING:
            slen = struct.unpack("<I", payload.read_escaped_bytes(4))[0]
            raw = payload.read_escaped_bytes(int(slen))
        elif atype in (ITEMATTR_INTEGER, ITEMATTR_FLOAT):
            raw = payload.read_escaped_bytes(4)
        elif atype == ITEMATTR_DOUBLE:
            raw = payload.read_escaped_bytes(8)
        elif atype == ITEMATTR_BOOLEAN:
            raw = payload.read_escaped_bytes(1)
        elif atype == ITEMATTR_NONE:
            raw = b""
        else:
            raise OTBMParseError(f"Unknown ItemAttribute type {atype}")

        out.append(ItemAttribute(key_bytes=bytes(key_bytes), type=int(atype), raw=bytes(raw)))

    return tuple(out)


def int32_from_raw(raw: bytes) -> int:
    """Convert 4-byte little-endian raw bytes to signed int32."""
    if len(raw) != 4:
        raise OTBMParseError(f"Invalid int32 raw size: expected 4, got {len(raw)}")
    return int(struct.unpack("<i", raw)[0])


def apply_known_attribute_map_fields(
    attribute_map: tuple[ItemAttribute, ...],
    *,
    subtype: int | None,
    count: int | None,
    text: str | None,
    description: str | None,
    action_id: int | None,
    unique_id: int | None,
    destination: Position | None,
    depot_id: int | None,
    house_door_id: int | None,
) -> tuple[
    int | None,  # subtype
    int | None,  # count
    str | None,  # text
    str | None,  # description
    int | None,  # action_id
    int | None,  # unique_id
    Position | None,  # destination
    int | None,  # depot_id
    int | None,  # house_door_id
]:
    """Apply known fields from attribute map to item fields.

    Legacy keys are set via Item::setAttribute in C++ (e.g. source/item.cpp,
    source/complexitem.h).
    """
    for attr in attribute_map:
        key = attr.key.lower()

        if key == "aid" and action_id is None:
            with suppress(Exception):
                action_id = int32_from_raw(attr.raw)
        elif key == "uid" and unique_id is None:
            with suppress(Exception):
                unique_id = int32_from_raw(attr.raw)
        elif key == "text" and not text:
            text = attr.raw.decode("utf-8", errors="replace")
        elif key == "desc" and not description:
            description = attr.raw.decode("utf-8", errors="replace")
        elif key == "subtype" and subtype is None:
            with suppress(Exception):
                subtype = int32_from_raw(attr.raw)
        elif key == "depotid" and depot_id is None:
            with suppress(Exception):
                depot_id = int32_from_raw(attr.raw)
        elif key == "doorid" and house_door_id is None:
            with suppress(Exception):
                house_door_id = int32_from_raw(attr.raw)
        elif key == "destination.x":
            # Destination components from attribute map
            pass

    # Handle destination from attribute map components
    dest_x = dest_y = dest_z = None
    for attr in attribute_map:
        key = attr.key.lower()
        with suppress(Exception):
            if key == "destination.x":
                dest_x = int32_from_raw(attr.raw)
            elif key == "destination.y":
                dest_y = int32_from_raw(attr.raw)
            elif key == "destination.z":
                dest_z = int32_from_raw(attr.raw)

    if destination is None and dest_x is not None and dest_y is not None and dest_z is not None:
        destination = Position(x=dest_x, y=dest_y, z=dest_z)

    return (
        subtype,
        count,
        text,
        description,
        action_id,
        unique_id,
        destination,
        depot_id,
        house_door_id,
    )


class ItemParser:
    """Parses OTBM item nodes."""

    def __init__(
        self,
        *,
        items_db: ItemsXML | None = None,
        id_mapper: IdMapper | None = None,
        unknown_item_policy: str = "placeholder",
        on_warning: Callable[..., None] | None = None,
        otbm_version: int = 2,
    ) -> None:
        self._items_db = items_db
        self._id_mapper = id_mapper
        self._unknown_item_policy = str(unknown_item_policy)
        self._on_warning = on_warning
        self._otbm_version = otbm_version

    def _resolve_raw_item_id(
        self,
        raw_item_id: int,
        *,
        tile_pos: tuple[int, int, int] | None = None,
    ) -> tuple[int, int | None, int | None]:
        raw_id = int(raw_item_id)
        client_id: int | None = None
        server_id = int(raw_id)
        raw_unknown_id: int | None = None

        if int(self._otbm_version) >= 5:
            # ClientID format: raw id is client-side; map to ServerID.
            client_id = int(raw_id)
            if self._id_mapper is not None:
                mapped = self._id_mapper.get_server_id(int(raw_id))
                if mapped is not None:
                    server_id = int(mapped)
                else:
                    if self._on_warning is not None:
                        self._on_warning(
                            code="missing_client_id_mapping",
                            message=f"No server id mapping for client id {raw_id}",
                            raw_id=int(raw_id),
                            tile_pos=tile_pos,
                            action=self._unknown_item_policy,
                        )
                    if self._unknown_item_policy == "error":
                        raise OTBMParseError(f"No server id mapping for client id {raw_id}")
                    raw_unknown_id = int(raw_id)
                    server_id = 0
            else:
                if self._on_warning is not None:
                    self._on_warning(
                        code="missing_id_mapper",
                        message="ClientID map loaded without IdMapper; ids may be incorrect.",
                        raw_id=int(raw_id),
                        tile_pos=tile_pos,
                    )
        else:
            if self._id_mapper is not None:
                try:
                    client_id = self._id_mapper.get_client_id(int(raw_id))
                except Exception:
                    client_id = None

        return int(server_id), client_id, raw_unknown_id

    def parse_compact_item_id(
        self,
        raw_item_id: int,
        *,
        tile_pos: tuple[int, int, int] | None = None,
    ) -> Item:
        item_id, client_id, raw_unknown_id = self._resolve_raw_item_id(raw_item_id, tile_pos=tile_pos)
        return Item(
            id=int(item_id),
            client_id=int(client_id) if client_id is not None else None,
            raw_unknown_id=int(raw_unknown_id) if raw_unknown_id is not None else None,
        )

    def parse_item_payload(
        self,
        payload: EscapedPayloadReader,
        *,
        tile_pos: tuple[int, int, int] | None = None,
    ) -> Item:
        """Parse an item from its OTBM payload."""
        raw_item_id = int(struct.unpack("<H", payload.read_escaped_bytes(2))[0])
        item_id, client_id, raw_unknown_id = self._resolve_raw_item_id(raw_item_id, tile_pos=tile_pos)

        if self._items_db is not None and int(item_id) != 0:
            try:
                known = self._items_db.get(int(item_id))
            except Exception:
                known = None
            if known is None:
                policy = self._unknown_item_policy
                if policy == "error":
                    raise OTBMParseError(f"Unknown item id {item_id}")

                if raw_unknown_id is None:
                    raw_unknown_id = int(item_id)
                if policy in {"placeholder", "skip"}:
                    item_id = 0

                if self._on_warning is not None:
                    self._on_warning(
                        code="unknown_item_id",
                        message=f"Unknown item id {raw_unknown_id}",
                        raw_id=int(raw_unknown_id),
                        tile_pos=tile_pos,
                        action=("placeholder" if policy == "placeholder" else policy),
                    )

        subtype: int | None = None
        count: int | None = None
        text: str | None = None
        description: str | None = None
        action_id: int | None = None
        unique_id: int | None = None
        destination: Position | None = None
        depot_id: int | None = None
        house_door_id: int | None = None
        attribute_map: tuple[ItemAttribute, ...] = ()

        # OTBM v1 stackable handling
        if int(self._otbm_version) == 1 and self._items_db is not None and int(item_id) != 0:
            it_type = self._items_db.get(int(item_id))
            if it_type is not None and (it_type.stackable or it_type.fluid_container or it_type.splash):
                st = payload.read_escaped_u8()
                if st is not None:
                    subtype = int(st)

        # Read attributes
        while True:
            attr_byte = payload.read_escaped_u8()
            if attr_byte is None:
                break

            attr = int(attr_byte)

            if attr == OTBM_ATTR_COUNT:
                count = payload.read_escaped_bytes(1)[0]
            elif attr == OTBM_ATTR_ACTION_ID:
                action_id = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
            elif attr == OTBM_ATTR_UNIQUE_ID:
                unique_id = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
            elif attr == OTBM_ATTR_TEXT:
                text = read_string(payload)
            elif attr == OTBM_ATTR_DESC:
                description = read_string(payload)
            elif attr == OTBM_ATTR_TELE_DEST:
                dx, dy, dz = struct.unpack("<HHB", payload.read_escaped_bytes(5))
                destination = Position(x=int(dx), y=int(dy), z=int(dz))
            elif attr == OTBM_ATTR_DEPOT_ID:
                depot_id = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
            elif attr == OTBM_ATTR_RUNE_CHARGES:
                subtype = payload.read_escaped_bytes(1)[0]
            elif attr == OTBM_ATTR_HOUSEDOORID:
                house_door_id = payload.read_escaped_bytes(1)[0]
            elif attr == OTBM_ATTR_CHARGES:
                subtype = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
            elif attr == OTBM_ATTR_ATTRIBUTE_MAP:
                attribute_map = read_attribute_map(payload)
            else:
                # Unknown attribute - emit warning for debugging
                if self._on_warning is not None:
                    self._on_warning(
                        code="unknown_item_attribute",
                        message=f"Unknown OTBM item attribute 0x{attr:02X} ({attr})",
                        raw_id=int(raw_item_id),
                        tile_pos=tile_pos,
                    )
                # Drain remaining payload to avoid corrupted parsing
                payload.drain_to_delimiter()
                break

        # Apply attribute map fields
        if attribute_map:
            (
                subtype,
                count,
                text,
                description,
                action_id,
                unique_id,
                destination,
                depot_id,
                house_door_id,
            ) = apply_known_attribute_map_fields(
                attribute_map,
                subtype=subtype,
                count=count,
                text=text,
                description=description,
                action_id=action_id,
                unique_id=unique_id,
                destination=destination,
                depot_id=depot_id,
                house_door_id=house_door_id,
            )

        if self._items_db is not None and int(item_id) != 0:
            it_type = self._items_db.get(int(item_id))
            if it_type is not None and (it_type.stackable or it_type.fluid_container or it_type.splash):
                if subtype is None and count is not None:
                    subtype = int(count)
                if count is None and subtype is not None:
                    count = int(subtype)

        return Item(
            id=int(item_id),
            client_id=int(client_id) if client_id is not None else None,
            raw_unknown_id=int(raw_unknown_id) if raw_unknown_id is not None else None,
            subtype=subtype,
            count=count,
            text=text,
            description=description,
            action_id=action_id,
            unique_id=unique_id,
            destination=destination,
            attribute_map=attribute_map,
            depot_id=depot_id,
            house_door_id=house_door_id,
        )

    def is_ground_item_id(self, server_id: int) -> bool:
        if self._items_db is None:
            return False
        it = self._items_db.get(int(server_id))
        return bool(it is not None and it.is_ground())
