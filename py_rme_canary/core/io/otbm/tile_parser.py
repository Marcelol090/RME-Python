"""Tile parsing utilities for OTBM format.

Handles parsing of OTBM_TILE and OTBM_HOUSETILE nodes.
"""

from __future__ import annotations

import struct
from typing import BinaryIO

from py_rme_canary.core.constants import (
    NODE_END,
    NODE_START,
    OTBM_ATTR_ITEM,
    OTBM_ATTR_TILE_FLAGS,
    OTBM_HOUSETILE,
    OTBM_ITEM,
    OTBM_TILE_ZONE,
)
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.exceptions import OTBMParseError

from .item_parser import ItemParser
from .streaming import (
    EscapedPayloadReader,
    begin_node,
    consume_siblings_until_end,
    read_u8,
)


class TileParser:
    """Parses OTBM tile nodes and their children."""

    def __init__(
        self,
        *,
        item_parser: ItemParser,
        otbm_version: int = 2,
    ) -> None:
        self._item_parser = item_parser
        self._otbm_version = otbm_version

    def parse_tile_node(
        self,
        stream: BinaryIO,
        node_type: int,
        payload: EscapedPayloadReader,
        *,
        area_base_x: int,
        area_base_y: int,
        area_z: int,
    ) -> Tile | None:
        """Parse a tile node (OTBM_TILE or OTBM_HOUSETILE)."""

        # Read tile offset within area
        offset_x = payload.read_escaped_bytes(1)[0]
        offset_y = payload.read_escaped_bytes(1)[0]

        tile_x = int(area_base_x) + int(offset_x)
        tile_y = int(area_base_y) + int(offset_y)
        tile_z = int(area_z)
        tile_pos = (tile_x, tile_y, tile_z)

        house_id: int | None = None
        map_flags: int = 0
        ground: Item | None = None
        items: list[Item] = []
        zones: set[int] = set()

        # House tile has house_id in payload
        if node_type == OTBM_HOUSETILE:
            house_id = struct.unpack("<I", payload.read_escaped_bytes(4))[0]

        # Read tile attributes
        while True:
            attr_byte = payload.read_escaped_u8()
            if attr_byte is None:
                break

            attr = int(attr_byte)

            if attr == OTBM_ATTR_TILE_FLAGS:
                map_flags = struct.unpack("<I", payload.read_escaped_bytes(4))[0]
            elif attr == OTBM_ATTR_ITEM:
                # Compact item (just item id)
                item_id = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
                item = Item(id=int(item_id))
                if ground is None:
                    ground = item
                else:
                    items.append(item)
            else:
                # Unknown attribute - try to continue
                pass

        # Read child nodes (items, zones)
        delim = payload.delimiter
        if delim == NODE_START:
            ground_holder = [ground]
            self._parse_tile_children(
                stream,
                tile_pos=tile_pos,
                ground_out=ground_holder,
                items_out=items,
                zones_out=zones,
            )

            ground = ground_holder[0]

        return Tile(
            x=tile_x,
            y=tile_y,
            z=tile_z,
            ground=ground,
            items=items,
            house_id=house_id,
            map_flags=int(map_flags),
            zones=frozenset(int(z) for z in zones if int(z) != 0),
        )

    def _parse_tile_children(
        self,
        stream: BinaryIO,
        *,
        tile_pos: tuple[int, int, int],
        ground_out: list[Item | None],
        items_out: list[Item],
        zones_out: set[int],
    ) -> None:
        """Parse child nodes of a tile (items and zones)."""

        while True:
            child_type, child_payload = begin_node(stream)

            if child_type == OTBM_ITEM:
                item = self._item_parser.parse_item_payload(
                    child_payload,
                    tile_pos=tile_pos,
                )

                if ground_out[0] is None and self._item_parser.is_ground_item_id(int(item.id)):
                    ground_out[0] = item
                else:
                    items_out.append(item)

                # Handle container children
                if child_payload.delimiter == NODE_START:
                    container_items = self._parse_container_children(stream)
                    if container_items:
                        # Update item with container contents
                        item = item.with_container_items(tuple(container_items))
                        if ground_out[0] is item:
                            ground_out[0] = item
                        elif items_out and items_out[-1].id == item.id:
                            items_out[-1] = item

            elif child_type == OTBM_TILE_ZONE:
                # Zone payload is: u16 count, then count * u16 zone_ids
                n = struct.unpack("<H", child_payload.read_escaped_bytes(2))[0]
                for _ in range(int(n)):
                    zid = struct.unpack("<H", child_payload.read_escaped_bytes(2))[0]
                    zones_out.add(int(zid))
                child_payload.drain_to_delimiter()

            else:
                # Unknown child type - skip
                child_payload.drain_to_delimiter()
                if child_payload.delimiter == NODE_START:
                    consume_siblings_until_end(stream)

            # Check for more siblings or end
            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                return
            raise OTBMParseError(f"Invalid stream op 0x{op:02X} in tile children")

    def _parse_container_children(self, stream: BinaryIO) -> list[Item]:
        """Parse container item children."""
        children: list[Item] = []

        while True:
            child_type, child_payload = begin_node(stream)

            if child_type == OTBM_ITEM:
                item = self._item_parser.parse_item_payload(child_payload)
                children.append(item)

                # Recursive container
                if child_payload.delimiter == NODE_START:
                    sub_items = self._parse_container_children(stream)
                    if sub_items:
                        item = item.with_container_items(tuple(sub_items))
                        children[-1] = item
            else:
                child_payload.drain_to_delimiter()
                if child_payload.delimiter == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                return children
            raise OTBMParseError(f"Invalid stream op 0x{op:02X} in container children")
