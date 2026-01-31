"""Main OTBM loader - orchestrates modular parsers.

This module provides the high-level API for loading OTBM map files.
It coordinates the streaming reader, header parser, tile parser, and item parser
to construct the full GameMap data structure.
"""

from __future__ import annotations

import logging
import os
import struct
from dataclasses import dataclass
from typing import BinaryIO

from ...constants.otbm import (
    NODE_END,
    NODE_START,
    OTBM_ATTR_DESCRIPTION,
    OTBM_ATTR_EXT_HOUSE_FILE,
    OTBM_ATTR_EXT_SPAWN_MONSTER_FILE,
    OTBM_ATTR_EXT_SPAWN_NPC_FILE,
    OTBM_ATTR_EXT_ZONE_FILE,
    OTBM_HOUSETILE,
    OTBM_MAP_DATA,
    OTBM_TILE,
    OTBM_TILE_AREA,
    OTBM_TOWN,
    OTBM_TOWNS,
    OTBM_WAYPOINT,
    OTBM_WAYPOINTS,
)
from ...data.gamemap import GameMap
from ...data.map_header import MapHeader
from ...data.position import Position
from ...data.tile import Tile
from ...data.towns import Town
from ...database.id_mapper import IdMapper
from ...database.items_xml import ItemsXML
from ...exceptions.io import OTBMParseError
from ...memory_guard import MemoryGuard, MemoryGuardError, default_memory_guard
from ..xml.spawns_loader import load_spawns_xml
from .header_parser import RootHeader, read_root_header
from .item_parser import ItemParser
from .streaming import (
    EscapedPayloadReader,
    begin_node,
    consume_siblings_until_end,
    read_string,
    read_u8,
)
from .tile_parser import TileParser

logger = logging.getLogger(__name__)


from typing import TypedDict

class ItemConversion(TypedDict):
    from_id: int
    to_id: int
    count: int


class LoadReport(TypedDict):
    """Structured report of the map loading process."""

    filename: str
    version: int
    width: int
    height: int
    items_count: int
    tiles_count: int
    duration_ms: float
    errors: list[str]
    warnings: list[str]
    dynamic_id_conversions: list[ItemConversion]


@dataclass(frozen=True, slots=True)
class LoadWarning:
    """Warning generated during map loading."""

    code: str
    message: str
    raw_id: int | None = None
    x: int | None = None
    y: int | None = None
    z: int | None = None
    action: str | None = None


class OTBMLoader:
    """High-level OTBM map loader.

    Orchestrates the modular parsers to load a complete GameMap from an OTBM file.
    """

    def __init__(
        self,
        *,
        items_db: ItemsXML | None = None,
        id_mapper: IdMapper | None = None,
        unknown_item_policy: str = "placeholder",
        allow_unsupported_versions: bool = False,
        memory_guard: MemoryGuard | None = None,
    ):
        self.items_db = items_db
        self.id_mapper = id_mapper
        self.unknown_item_policy = self._validate_policy(unknown_item_policy)
        self.allow_unsupported_versions = allow_unsupported_versions
        self.warnings: list[LoadWarning] = []

        self._memory_guard: MemoryGuard = memory_guard or default_memory_guard()
        self._tiles_seen: int = 0
        self._items_seen: int = 0

        self._item_parser: ItemParser | None = None
        self._tile_parser: TileParser | None = None
        self._header: RootHeader | None = None

    @staticmethod
    def _validate_policy(policy: str) -> str:
        """Validate unknown item policy."""
        valid = {"placeholder", "skip", "error"}
        if policy not in valid:
            raise ValueError(f"unknown_item_policy must be one of {valid}, got {policy!r}")
        return policy

    def load(self, path: str) -> GameMap:
        """Load a complete GameMap from an OTBM file."""
        self.warnings.clear()

        # Pre-load guardrail (file size). This is deterministic and cheap.
        try:
            self._memory_guard.check_file_size(path=str(path), stage="otbm_preload")
        except MemoryGuardError as e:
            raise OTBMParseError(str(e)) from e

        tiles: dict[tuple[int, int, int], Tile] = {}
        waypoints: dict[str, Position] = {}
        towns: dict[int, Town] = {}

        description = ""
        spawnmonsterfile = ""
        spawnnpcfile = ""
        housefile = ""
        zonefile = ""

        with open(path, "rb") as f:
            # Read root header
            self._header = read_root_header(f, allow_unsupported_versions=self.allow_unsupported_versions)

            # Pre-load guardrail (header sanity). Avoid absurd address-space growth.
            try:
                # A very large width/height indicates a map that can explode in memory once edited.
                warn = self._memory_guard.check_map_counts(
                    tiles=0,
                    items=0,
                    stage=f"otbm_header width={self._header.width} height={self._header.height}",
                )
                if warn is not None:
                    self.warnings.append(LoadWarning(code="memory_guard_warning", message=str(warn)))
            except MemoryGuardError as e:
                raise OTBMParseError(str(e)) from e

            def _on_item_warning(
                *,
                code: str,
                message: str,
                raw_id: int | None = None,
                tile_pos: tuple[int, int, int] | None = None,
                action: str | None = None,
            ) -> None:
                x = y = z = None
                if tile_pos is not None:
                    try:
                        x, y, z = tile_pos
                    except Exception:
                        x = y = z = None
                self.warnings.append(
                    LoadWarning(
                        code=str(code),
                        message=str(message),
                        raw_id=int(raw_id) if raw_id is not None else None,
                        x=int(x) if x is not None else None,
                        y=int(y) if y is not None else None,
                        z=int(z) if z is not None else None,
                        action=str(action) if action is not None else None,
                    )
                )

            # Initialize parsers with header info
            self._item_parser = ItemParser(
                otbm_version=self._header.otbm_version,
                items_db=self.items_db,
                id_mapper=self.id_mapper,
                unknown_item_policy=self.unknown_item_policy,
                on_warning=_on_item_warning,
            )
            self._tile_parser = TileParser(
                item_parser=self._item_parser,
                otbm_version=self._header.otbm_version,
            )

            # Parse root children
            while True:
                child_type, child_payload = begin_node(f)

                if child_type == OTBM_MAP_DATA:
                    # Parse map data attributes
                    map_attrs = self._parse_map_data_attributes(child_payload)
                    description = map_attrs.get("description", "")
                    spawnmonsterfile = map_attrs.get("spawnmonsterfile", "")
                    spawnnpcfile = map_attrs.get("spawnnpcfile", "")
                    housefile = map_attrs.get("housefile", "")
                    zonefile = map_attrs.get("zonefile", "")

                    if child_payload.delimiter is None:
                        raise OTBMParseError("MAP_DATA missing delimiter")

                    if child_payload.delimiter == NODE_START:
                        # Parse MAP_DATA children (tile areas, towns, waypoints)
                        self._parse_map_data_children(f, tiles, waypoints, towns)
                else:
                    d = child_payload.drain_to_delimiter()
                    if d == NODE_START:
                        consume_siblings_until_end(f)

                op = read_u8(f)
                if op == NODE_START:
                    continue
                if op == NODE_END:
                    break
                raise OTBMParseError(f"Invalid stream op 0x{op:02X} after root child")

        # Build final GameMap
        header = MapHeader(
            otbm_version=self._header.otbm_version,
            width=self._header.width,
            height=self._header.height,
            description=description,
            spawnmonsterfile=spawnmonsterfile,
            spawnnpcfile=spawnnpcfile,
            housefile=housefile,
            zonefile=zonefile,
        )

        km = GameMap(header=header, tiles=tiles, waypoints=waypoints, towns=towns)

        # Legacy Parity: Load spawns from XML if defined
        map_dir = os.path.dirname(path)
        if spawnmonsterfile:
            # Try to resolve path relative to map file
            spawn_path = os.path.join(map_dir, spawnmonsterfile)
            load_spawns_xml(km, spawn_path, is_npc=False)

        if spawnnpcfile:
            spawn_path = os.path.join(map_dir, spawnnpcfile)
            load_spawns_xml(km, spawn_path, is_npc=True)

        gm = km

        # Dynamic ID conversion metrics
        dyn_server_in_client = sum(1 for w in self.warnings if w.code == "server_id_in_client_map")
        dyn_client_in_server = sum(1 for w in self.warnings if w.code == "client_id_in_server_map")
        dyn_total = int(dyn_server_in_client) + int(dyn_client_in_server)
        if dyn_total > 0:
            summary = (
                "Dynamic ID conversions: "
                f"server_id_in_client_map={dyn_server_in_client}, "
                f"client_id_in_server_map={dyn_client_in_server}"
            )
            self.warnings.append(LoadWarning(code="dynamic_id_conversion_summary", message=summary))
            logger.warning(summary)

        # Build load report
        unknowns = [w for w in self.warnings if w.code == "unknown_item_id" and w.raw_id is not None]
        replaced_items = [
            (int(w.x), int(w.y), int(w.z), int(w.raw_id))
            for w in unknowns
            if w.action == "placeholder"
            and w.raw_id is not None
            and w.x is not None
            and w.y is not None
            and w.z is not None
        ]

        gm.load_report = {
            "warnings": list(self.warnings),
            "unknown_ids_count": len(unknowns),
            "replaced_items": replaced_items,
            "dynamic_id_conversions": {
                "server_id_in_client_map": int(dyn_server_in_client),
                "client_id_in_server_map": int(dyn_client_in_server),
                "total": int(dyn_total),
            },
        }

        return gm

    def _parse_map_data_attributes(self, payload: EscapedPayloadReader) -> dict[str, str]:
        """Parse MAP_DATA node attributes."""
        result: dict[str, str] = {}

        while True:
            attr = payload.read_escaped_u8()
            if attr is None:
                break

            if attr == OTBM_ATTR_DESCRIPTION:
                result["description"] = read_string(payload)
            elif attr == OTBM_ATTR_EXT_SPAWN_MONSTER_FILE:
                result["spawnmonsterfile"] = read_string(payload)
            elif attr == OTBM_ATTR_EXT_SPAWN_NPC_FILE:
                result["spawnnpcfile"] = read_string(payload)
            elif attr == OTBM_ATTR_EXT_HOUSE_FILE:
                result["housefile"] = read_string(payload)
            elif attr == OTBM_ATTR_EXT_ZONE_FILE:
                result["zonefile"] = read_string(payload)
            else:
                raise OTBMParseError(f"Unknown MAP_DATA attribute {attr}")

        return result

    def _parse_map_data_children(
        self,
        stream: BinaryIO,
        tiles: dict[tuple[int, int, int], Tile],
        waypoints: dict[str, Position],
        towns: dict[int, Town],
    ) -> None:
        """Parse MAP_DATA child nodes (tile areas, towns, waypoints)."""
        while True:
            map_child_type, map_child_payload = begin_node(stream)

            if map_child_type == OTBM_TILE_AREA:
                self._parse_tile_area(stream, map_child_payload, tiles)
            elif map_child_type == OTBM_TOWNS:
                self._parse_towns(stream, map_child_payload, towns)
            elif map_child_type == OTBM_WAYPOINTS:
                self._parse_waypoints(stream, map_child_payload, waypoints)
            else:
                d = map_child_payload.drain_to_delimiter()
                if d == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                break
            raise OTBMParseError(f"Invalid op 0x{op:02X} after MAP_DATA child")

    def _parse_towns(
        self,
        stream: BinaryIO,
        payload: EscapedPayloadReader,
        towns: dict[int, Town],
    ) -> None:
        """Parse OTBM_TOWNS node."""
        d: int | None = payload.delimiter
        if d is None:
            d = payload.drain_to_delimiter()

        if d != NODE_START:
            return

        while True:
            town_type, town_payload = begin_node(stream)
            town_delim: int | None

            if town_type != OTBM_TOWN:
                town_delim = town_payload.drain_to_delimiter()
                if town_delim == NODE_START:
                    consume_siblings_until_end(stream)
            else:
                town_id_raw = struct.unpack("<I", town_payload.read_escaped_bytes(4))[0]
                name = read_string(town_payload)
                x_raw, y_raw, z_raw = struct.unpack("<HHB", town_payload.read_escaped_bytes(5))

                tid = int(town_id_raw)
                towns[tid] = Town(
                    id=tid,
                    name=str(name),
                    temple_position=Position(x=int(x_raw), y=int(y_raw), z=int(z_raw)),
                )

                town_delim = town_payload.delimiter
                if town_delim is None:
                    town_delim = town_payload.drain_to_delimiter()
                if town_delim == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                break
            raise OTBMParseError(f"Invalid op 0x{op:02X} after town")

    def _parse_tile_area(
        self,
        stream: BinaryIO,
        payload: EscapedPayloadReader,
        tiles: dict[tuple[int, int, int], Tile],
    ) -> None:
        """Parse OTBM_TILE_AREA node."""
        tile_parser = self._tile_parser
        if tile_parser is None:
            raise OTBMParseError("TileParser not initialized")
        base_x, base_y, base_z = struct.unpack("<HHB", payload.read_escaped_bytes(5))
        area_delim = payload.drain_to_delimiter()

        if area_delim != NODE_START:
            return

        while True:
            tile_type, tile_payload = begin_node(stream)

            if tile_type in (OTBM_TILE, OTBM_HOUSETILE):
                tile = tile_parser.parse_tile_node(
                    stream,
                    tile_type,
                    tile_payload,
                    area_base_x=int(base_x),
                    area_base_y=int(base_y),
                    area_z=int(base_z),
                )
                if tile is not None:
                    tiles[(tile.x, tile.y, tile.z)] = tile

                    # Incremental memory guard: track tiles/items while loading.
                    self._tiles_seen += 1
                    if tile.ground is not None:
                        self._items_seen += 1
                    self._items_seen += len(tile.items)

                    if (self._tiles_seen % int(self._memory_guard.config.check_every_tiles)) == 0:
                        try:
                            msg = self._memory_guard.check_map_counts(
                                tiles=self._tiles_seen,
                                items=self._items_seen,
                                stage="otbm_load_incremental",
                            )
                            if msg is not None:
                                self.warnings.append(LoadWarning(code="memory_guard_warning", message=str(msg)))
                        except MemoryGuardError as e:
                            raise OTBMParseError(str(e)) from e
            else:
                d = tile_payload.drain_to_delimiter()
                if d == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                break
            raise OTBMParseError(f"Invalid op 0x{op:02X} after tile")

    def _parse_waypoints(
        self,
        stream: BinaryIO,
        payload: EscapedPayloadReader,
        waypoints: dict[str, Position],
    ) -> None:
        """Parse OTBM_WAYPOINTS node."""
        d: int | None = payload.delimiter
        if d is None:
            d = payload.drain_to_delimiter()

        if d != NODE_START:
            return

        while True:
            wp_type, wp_payload = begin_node(stream)
            wp_delim: int | None

            if wp_type != OTBM_WAYPOINT:
                wp_delim = wp_payload.drain_to_delimiter()
                if wp_delim == NODE_START:
                    consume_siblings_until_end(stream)
            else:
                name = read_string(wp_payload)
                x_raw, y_raw, z_raw = struct.unpack("<HHB", wp_payload.read_escaped_bytes(5))
                waypoints[str(name)] = Position(x=int(x_raw), y=int(y_raw), z=int(z_raw))

                wp_delim = wp_payload.delimiter
                if wp_delim is None:
                    wp_delim = wp_payload.drain_to_delimiter()
                if wp_delim == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                break
            raise OTBMParseError(f"Invalid op 0x{op:02X} after waypoint")


# Convenience functions for backward compatibility


def load_game_map(path: str, *, allow_unsupported_versions: bool = False) -> GameMap:
    """Load an OTBM file into a GameMap.

    This is the simplest loading function - no items database,
    unknown items get placeholder IDs.
    """
    loader = OTBMLoader(
        items_db=None,
        id_mapper=None,
        unknown_item_policy="placeholder",
        allow_unsupported_versions=allow_unsupported_versions,
        memory_guard=default_memory_guard(),
    )
    return loader.load(path)


def load_game_map_with_items_db(
    path: str,
    *,
    items_db: ItemsXML | None = None,
    id_mapper: IdMapper | None = None,
    unknown_item_policy: str = "placeholder",
    warnings: list[LoadWarning] | None = None,
    allow_unsupported_versions: bool = False,
) -> GameMap:
    """Load an OTBM file with items database for semantic interpretation.

    If `items_db` is provided:
    - Ground items are identified and placed in Tile.ground
    - Stackable/fluid/splash items get proper count handling
    """
    loader = OTBMLoader(
        items_db=items_db,
        id_mapper=id_mapper,
        unknown_item_policy=unknown_item_policy,
        allow_unsupported_versions=allow_unsupported_versions,
        memory_guard=default_memory_guard(),
    )

    gm = loader.load(path)

    # Transfer warnings if caller provided a list
    if warnings is not None:
        warnings.extend(loader.warnings)

    return gm
