"""OTMM loader/saver (partial MVP).

Legacy reference: source/iomap_otmm.cpp / source/iomap_otmm.h.
"""

from __future__ import annotations

import logging
import struct
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from py_rme_canary.core.constants import (
    ESCAPE_CHAR,
    MAGIC_OTBM,
    MAGIC_OTMM,
    MAGIC_WILDCARD,
    NODE_END,
    NODE_START,
    OTMM_ATTR_ACTION_ID,
    OTMM_ATTR_DEPOT_ID,
    OTMM_ATTR_DESC,
    OTMM_ATTR_DOOR_ID,
    OTMM_ATTR_SUBTYPE,
    OTMM_ATTR_TELE_DEST,
    OTMM_ATTR_TEXT,
    OTMM_ATTR_TILE_FLAGS,
    OTMM_ATTR_UNIQUE_ID,
    OTMM_DESCRIPTION,
    OTMM_EDITOR,
    OTMM_HOUSE,
    OTMM_HOUSE_DATA,
    OTMM_HOUSETILE,
    OTMM_ITEM,
    OTMM_MAP_DATA,
    OTMM_MONSTER,
    OTMM_NPC,
    OTMM_SPAWN_MONSTER_AREA,
    OTMM_SPAWN_MONSTER_DATA,
    OTMM_SPAWN_NPC_AREA,
    OTMM_SPAWN_NPC_DATA,
    OTMM_TILE,
    OTMM_TILE_DATA,
    OTMM_TOWN,
    OTMM_TOWN_DATA,
    OTMM_VERSION_1,
)
from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.spawns import (
    MonsterSpawnArea,
    MonsterSpawnEntry,
    NpcSpawnArea,
    NpcSpawnEntry,
)
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.data.towns import Town
from py_rme_canary.core.database.id_mapper import IdMapper
from py_rme_canary.core.database.items_xml import ItemsXML
from py_rme_canary.core.exceptions import OTBMParseError
from py_rme_canary.core.memory_guard import MemoryGuard, MemoryGuardError, default_memory_guard

from .otbm.streaming import (
    EscapedPayloadReader,
    begin_node,
    consume_siblings_until_end,
    read_exact,
    read_string,
    read_u8,
)
from .otbm_loader import OTBMLoader

log = logging.getLogger(__name__)


class OTMMError(ValueError):
    """Raised for OTMM-specific load/save failures."""


@dataclass(frozen=True, slots=True)
class LoadWarning:
    """Warning generated during OTMM load."""

    code: str
    message: str
    raw_id: int | None = None
    x: int | None = None
    y: int | None = None
    z: int | None = None
    action: str | None = None


@dataclass(frozen=True, slots=True)
class OTMMRootHeader:
    version: int
    width: int
    height: int
    otb_major: int
    otb_minor: int


class OTMMItemParser:
    """Parse OTMM item nodes and attributes."""

    def __init__(
        self,
        *,
        items_db: ItemsXML | None = None,
        id_mapper: IdMapper | None = None,
        unknown_item_policy: str = "placeholder",
        on_warning: Callable[..., None] | None = None,
    ) -> None:
        self._items_db = items_db
        self._id_mapper = id_mapper
        self._unknown_item_policy = str(unknown_item_policy)
        self._on_warning = on_warning

    def parse_item_payload(
        self,
        payload: EscapedPayloadReader,
        *,
        tile_pos: tuple[int, int, int] | None = None,
    ) -> Item:
        raw_item_id = int(struct.unpack("<H", payload.read_escaped_bytes(2))[0])

        client_id: int | None = None
        if self._id_mapper is not None:
            try:
                client_id = self._id_mapper.get_client_id(int(raw_item_id))
            except Exception:
                client_id = None
        elif self._items_db is not None:
            client_id = self._items_db.get_client_id(int(raw_item_id))

        item_id = int(raw_item_id)
        raw_unknown_id: int | None = None
        if self._items_db is not None:
            try:
                known = self._items_db.get(int(item_id))
            except Exception:
                known = None
            if known is None:
                policy = self._unknown_item_policy
                if policy == "error":
                    raise OTMMError(f"Unknown item id {item_id}")

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
        text: str | None = None
        description: str | None = None
        action_id: int | None = None
        unique_id: int | None = None
        destination: Position | None = None
        depot_id: int | None = None
        house_door_id: int | None = None

        while True:
            attr = payload.read_escaped_u8()
            if attr is None:
                break

            attr_id = int(attr)
            if attr_id == OTMM_ATTR_SUBTYPE:
                raw_subtype = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
                subtype = int(raw_subtype) & 0xF
            elif attr_id == OTMM_ATTR_ACTION_ID:
                action_id = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
            elif attr_id == OTMM_ATTR_UNIQUE_ID:
                unique_id = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
            elif attr_id == OTMM_ATTR_TEXT:
                text = read_string(payload)
            elif attr_id == OTMM_ATTR_DESC:
                description = read_string(payload)
            elif attr_id == OTMM_ATTR_TELE_DEST:
                dx, dy, dz = struct.unpack("<HHB", payload.read_escaped_bytes(5))
                destination = Position(x=int(dx), y=int(dy), z=int(dz))
            elif attr_id == OTMM_ATTR_DEPOT_ID:
                depot_id = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
            elif attr_id == OTMM_ATTR_DOOR_ID:
                house_door_id = payload.read_escaped_bytes(1)[0]
            else:
                if self._on_warning is not None:
                    self._on_warning(
                        code="unknown_otmm_item_attr",
                        message=f"Unknown OTMM item attribute {attr_id}",
                        raw_id=int(raw_item_id),
                        tile_pos=tile_pos,
                    )
                payload.drain_to_delimiter()
                break

        return Item(
            id=int(item_id),
            client_id=int(client_id) if client_id is not None else None,
            raw_unknown_id=int(raw_unknown_id) if raw_unknown_id is not None else None,
            subtype=subtype,
            text=text,
            description=description,
            action_id=action_id,
            unique_id=unique_id,
            destination=destination,
            depot_id=depot_id,
            house_door_id=house_door_id,
        )

    def is_ground_item_id(self, server_id: int) -> bool:
        if self._items_db is None:
            return False
        it = self._items_db.get(int(server_id))
        return bool(it is not None and it.is_ground())


def _read_payload_remainder(payload: EscapedPayloadReader) -> bytes:
    if payload.delimiter is not None or getattr(payload, "_ended", False):
        return b""

    data = bytearray()
    while True:
        b = read_u8(payload._stream)
        if b == ESCAPE_CHAR:
            data.append(read_u8(payload._stream))
            continue
        if b in (NODE_START, NODE_END):
            payload._ended = True
            payload.delimiter = b
            return bytes(data)
        data.append(b)


class OTMMLoader:
    """High-level OTMM map loader."""

    def __init__(
        self,
        *,
        items_db: ItemsXML | None = None,
        id_mapper: IdMapper | None = None,
        unknown_item_policy: str = "placeholder",
        allow_unsupported_versions: bool = False,
        memory_guard: MemoryGuard | None = None,
    ) -> None:
        self.items_db = items_db
        self.id_mapper = id_mapper
        self.unknown_item_policy = str(unknown_item_policy)
        self.allow_unsupported_versions = bool(allow_unsupported_versions)
        self._memory_guard = memory_guard or default_memory_guard()
        self.warnings: list[LoadWarning] = []
        self._tiles_seen = 0
        self._items_seen = 0
        self._item_parser: OTMMItemParser | None = None
        self._root_header: OTMMRootHeader | None = None

    def load(self, path: str | Path) -> GameMap:
        self.warnings.clear()
        self._tiles_seen = 0
        self._items_seen = 0

        p = Path(path)

        try:
            self._memory_guard.check_file_size(path=str(p), stage="otmm_preload")
        except MemoryGuardError as e:
            raise OTMMError(str(e)) from e

        tiles: dict[tuple[int, int, int], Tile] = {}
        towns: dict[int, Town] = {}
        houses: dict[int, House] = {}
        monster_spawns: list[MonsterSpawnArea] = []
        npc_spawns: list[NpcSpawnArea] = []
        description = ""

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

        self._item_parser = OTMMItemParser(
            items_db=self.items_db,
            id_mapper=self.id_mapper,
            unknown_item_policy=self.unknown_item_policy,
            on_warning=_on_item_warning,
        )

        try:
            with p.open("rb") as f:
                magic = read_exact(f, 4)
                if magic == MAGIC_OTBM:
                    log.warning("OTMM loader fallback: file has OTBM magic, delegating to OTBM loader.")
                    return OTBMLoader(items_db=self.items_db).load(str(p))

                if magic not in (MAGIC_OTMM, MAGIC_WILDCARD):
                    raise OTMMError(f"Invalid OTMM magic: {magic!r}")

                op = read_u8(f)
                if op != NODE_START:
                    raise OTMMError(f"Expected NODE_START, got 0x{op:02X}")

                _root_type, root_payload = begin_node(f)
                self._root_header = self._parse_root_payload(root_payload)

                map_type, map_payload = begin_node(f)
                if map_type != OTMM_MAP_DATA:
                    raise OTMMError(f"Expected OTMM_MAP_DATA, got {map_type}")

                map_delim = map_payload.drain_to_delimiter()
                if map_delim == NODE_START:
                    description = self._parse_map_children(
                        f,
                        tiles=tiles,
                        towns=towns,
                        houses=houses,
                        monster_spawns=monster_spawns,
                        npc_spawns=npc_spawns,
                    )

                op = read_u8(f)
                if op != NODE_END:
                    raise OTMMError(f"Invalid stream op 0x{op:02X} after OTMM_MAP_DATA")
        except OTBMParseError as e:
            raise OTMMError(str(e)) from e

        header = MapHeader(
            otbm_version=int(OTMM_VERSION_1),
            width=int(self._root_header.width) if self._root_header else 0,
            height=int(self._root_header.height) if self._root_header else 0,
            description=description,
        )

        gm = GameMap(
            header=header,
            tiles=tiles,
            towns=towns,
            houses=houses,
            monster_spawns=list(monster_spawns),
            npc_spawns=list(npc_spawns),
        )

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

        metadata: dict[str, int] = {}
        if self._root_header is not None:
            metadata = {
                "otmm_version": int(self._root_header.version),
                "otb_major": int(self._root_header.otb_major),
                "otb_minor": int(self._root_header.otb_minor),
            }

        gm.load_report = {
            "warnings": list(self.warnings),
            "unknown_ids_count": len(unknowns),
            "replaced_items": replaced_items,
            "metadata": metadata,
        }

        return gm

    def _parse_root_payload(self, payload: EscapedPayloadReader) -> OTMMRootHeader:
        version = struct.unpack("<I", payload.read_escaped_bytes(4))[0]
        if not self.allow_unsupported_versions and int(version) != OTMM_VERSION_1:
            raise OTMMError(f"Unsupported OTMM version: {version}")

        width, height = struct.unpack("<HH", payload.read_escaped_bytes(4))
        otb_major = struct.unpack("<I", payload.read_escaped_bytes(4))[0]
        otb_minor = struct.unpack("<I", payload.read_escaped_bytes(4))[0]

        delim = payload.drain_to_delimiter()
        if delim != NODE_START:
            raise OTMMError("Root node has no children")

        return OTMMRootHeader(
            version=int(version),
            width=int(width),
            height=int(height),
            otb_major=int(otb_major),
            otb_minor=int(otb_minor),
        )

    def _parse_map_children(
        self,
        stream: BinaryIO,
        *,
        tiles: dict[tuple[int, int, int], Tile],
        towns: dict[int, Town],
        houses: dict[int, House],
        monster_spawns: list[MonsterSpawnArea],
        npc_spawns: list[NpcSpawnArea],
    ) -> str:
        description = ""

        while True:
            node_type, payload = begin_node(stream)

            if node_type == OTMM_EDITOR:
                _ = read_string(payload)
                payload.drain_to_delimiter()
            elif node_type == OTMM_DESCRIPTION:
                description = read_string(payload)
                payload.drain_to_delimiter()
            elif node_type == OTMM_TILE_DATA:
                self._parse_tile_data(stream, payload, tiles=tiles, houses=houses)
            elif node_type == OTMM_SPAWN_MONSTER_DATA:
                monster_spawns.extend(self._parse_monster_spawns(stream, payload))
            elif node_type == OTMM_SPAWN_NPC_DATA:
                npc_spawns.extend(self._parse_npc_spawns(stream, payload))
            elif node_type == OTMM_TOWN_DATA:
                self._parse_towns(stream, payload, towns=towns)
            elif node_type == OTMM_HOUSE_DATA:
                self._parse_houses(stream, payload, houses=houses)
            else:
                payload.drain_to_delimiter()
                if payload.delimiter == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                return description
            raise OTMMError(f"Invalid stream op 0x{op:02X} after OTMM_MAP_DATA child")

    def _parse_tile_data(
        self,
        stream: BinaryIO,
        payload: EscapedPayloadReader,
        *,
        tiles: dict[tuple[int, int, int], Tile],
        houses: dict[int, House],
    ) -> None:
        delim = payload.drain_to_delimiter()
        if delim != NODE_START:
            return

        item_parser = self._item_parser
        if item_parser is None:
            raise OTMMError("Item parser not initialized")

        while True:
            tile_type, tile_payload = begin_node(stream)
            if tile_type in (OTMM_TILE, OTMM_HOUSETILE):
                tile = self._parse_tile_node(
                    stream,
                    tile_type=tile_type,
                    payload=tile_payload,
                    item_parser=item_parser,
                    houses=houses,
                )
                if tile is not None:
                    key = (int(tile.x), int(tile.y), int(tile.z))
                    if key in tiles:
                        self.warnings.append(
                            LoadWarning(
                                code="duplicate_tile",
                                message=f"Duplicate tile at {tile.x}:{tile.y}:{tile.z}",
                                x=int(tile.x),
                                y=int(tile.y),
                                z=int(tile.z),
                            )
                        )
                    else:
                        tiles[key] = tile

                        self._tiles_seen += 1
                        if tile.ground is not None:
                            self._items_seen += self._count_item_tree(tile.ground)
                        for it in tile.items:
                            self._items_seen += self._count_item_tree(it)

                        if (self._tiles_seen % int(self._memory_guard.config.check_every_tiles)) == 0:
                            try:
                                msg = self._memory_guard.check_map_counts(
                                    tiles=self._tiles_seen,
                                    items=self._items_seen,
                                    stage="otmm_load_incremental",
                                )
                                if msg is not None:
                                    self.warnings.append(LoadWarning(code="memory_guard_warning", message=str(msg)))
                            except MemoryGuardError as e:
                                raise OTMMError(str(e)) from e
            else:
                tile_payload.drain_to_delimiter()
                if tile_payload.delimiter == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                return
            raise OTMMError(f"Invalid stream op 0x{op:02X} after OTMM_TILE_DATA child")

    def _parse_tile_node(
        self,
        stream: BinaryIO,
        *,
        tile_type: int,
        payload: EscapedPayloadReader,
        item_parser: OTMMItemParser,
        houses: dict[int, House],
    ) -> Tile | None:
        x, y, z = struct.unpack("<HHB", payload.read_escaped_bytes(5))
        house_id: int | None = None

        if tile_type == OTMM_HOUSETILE:
            house_id = struct.unpack("<I", payload.read_escaped_bytes(4))[0]
            if house_id not in houses:
                houses[int(house_id)] = House(id=int(house_id))

        ground_id = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
        ground: Item | None = None
        if int(ground_id) != 0:
            ground = Item(id=int(ground_id))

        map_flags = 0
        attrs_complete = True

        while True:
            attr = payload.read_escaped_u8()
            if attr is None:
                break

            attr_id = int(attr)
            if attr_id == OTMM_ATTR_TILE_FLAGS:
                map_flags = struct.unpack("<I", payload.read_escaped_bytes(4))[0]
            else:
                attrs_complete = False
                self.warnings.append(
                    LoadWarning(
                        code="unknown_otmm_tile_attr",
                        message=f"Unknown OTMM tile attribute {attr_id}",
                        x=int(x),
                        y=int(y),
                        z=int(z),
                    )
                )
                payload.drain_to_delimiter()
                break

        if attrs_complete and payload.delimiter is None:
            payload.drain_to_delimiter()

        items: list[Item] = []
        tile_pos = (int(x), int(y), int(z))

        if payload.delimiter == NODE_START:
            ground_holder = [ground]
            self._parse_tile_items(
                stream,
                tile_pos=tile_pos,
                item_parser=item_parser,
                ground_out=ground_holder,
                items_out=items,
            )
            ground = ground_holder[0]

        return Tile(
            x=int(x),
            y=int(y),
            z=int(z),
            ground=ground,
            items=items,
            house_id=int(house_id) if house_id is not None else None,
            map_flags=int(map_flags),
        )

    def _parse_tile_items(
        self,
        stream: BinaryIO,
        *,
        tile_pos: tuple[int, int, int],
        item_parser: OTMMItemParser,
        ground_out: list[Item | None],
        items_out: list[Item],
    ) -> None:
        while True:
            child_type, child_payload = begin_node(stream)
            if child_type == OTMM_ITEM:
                item = item_parser.parse_item_payload(child_payload, tile_pos=tile_pos)
                children: list[Item] = []
                if child_payload.delimiter == NODE_START:
                    children = self._parse_container_children(stream, item_parser=item_parser)
                    if children:
                        item = item.with_container_items(tuple(children))

                if ground_out[0] is None and item_parser.is_ground_item_id(int(item.id)):
                    ground_out[0] = item
                else:
                    items_out.append(item)
            else:
                child_payload.drain_to_delimiter()
                if child_payload.delimiter == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                return
            raise OTMMError(f"Invalid stream op 0x{op:02X} in OTMM tile items")

    def _parse_container_children(
        self,
        stream: BinaryIO,
        *,
        item_parser: OTMMItemParser,
    ) -> list[Item]:
        children: list[Item] = []

        while True:
            child_type, child_payload = begin_node(stream)
            if child_type == OTMM_ITEM:
                item = item_parser.parse_item_payload(child_payload)
                if child_payload.delimiter == NODE_START:
                    sub_items = self._parse_container_children(stream, item_parser=item_parser)
                    if sub_items:
                        item = item.with_container_items(tuple(sub_items))
                children.append(item)
            else:
                child_payload.drain_to_delimiter()
                if child_payload.delimiter == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                return children
            raise OTMMError(f"Invalid stream op 0x{op:02X} in OTMM container")

    def _parse_monster_spawns(
        self,
        stream: BinaryIO,
        payload: EscapedPayloadReader,
    ) -> list[MonsterSpawnArea]:
        delim = payload.drain_to_delimiter()
        if delim != NODE_START:
            return []

        areas: list[MonsterSpawnArea] = []
        while True:
            node_type, node_payload = begin_node(stream)
            if node_type == OTMM_SPAWN_MONSTER_AREA:
                cx, cy, cz = struct.unpack("<HHB", node_payload.read_escaped_bytes(5))
                radius = struct.unpack("<I", node_payload.read_escaped_bytes(4))[0]
                node_delim = node_payload.drain_to_delimiter()

                monsters: list[MonsterSpawnEntry] = []
                if node_delim == NODE_START:
                    while True:
                        m_type, m_payload = begin_node(stream)
                        if m_type == OTMM_MONSTER:
                            name = read_string(m_payload)
                            spawntime = struct.unpack("<I", m_payload.read_escaped_bytes(4))[0]
                            mx, my, mz = struct.unpack("<HHB", m_payload.read_escaped_bytes(5))
                            m_payload.drain_to_delimiter()
                            monsters.append(
                                MonsterSpawnEntry(
                                    name=str(name),
                                    dx=int(mx) - int(cx),
                                    dy=int(my) - int(cy),
                                    spawntime=int(spawntime),
                                )
                            )
                        else:
                            m_payload.drain_to_delimiter()
                            if m_payload.delimiter == NODE_START:
                                consume_siblings_until_end(stream)

                        op = read_u8(stream)
                        if op == NODE_START:
                            continue
                        if op == NODE_END:
                            break
                        raise OTMMError(f"Invalid stream op 0x{op:02X} in OTMM monster spawn")

                areas.append(
                    MonsterSpawnArea(
                        center=Position(x=int(cx), y=int(cy), z=int(cz)),
                        radius=int(radius),
                        monsters=tuple(monsters),
                    )
                )
            else:
                node_payload.drain_to_delimiter()
                if node_payload.delimiter == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                return areas
            raise OTMMError(f"Invalid stream op 0x{op:02X} after OTMM_SPAWN_MONSTER_DATA child")

    def _parse_npc_spawns(
        self,
        stream: BinaryIO,
        payload: EscapedPayloadReader,
    ) -> list[NpcSpawnArea]:
        delim = payload.drain_to_delimiter()
        if delim != NODE_START:
            return []

        areas: list[NpcSpawnArea] = []
        while True:
            node_type, node_payload = begin_node(stream)
            if node_type == OTMM_SPAWN_NPC_AREA:
                cx, cy, cz = struct.unpack("<HHB", node_payload.read_escaped_bytes(5))
                radius = struct.unpack("<I", node_payload.read_escaped_bytes(4))[0]
                node_delim = node_payload.drain_to_delimiter()

                npcs: list[NpcSpawnEntry] = []
                if node_delim == NODE_START:
                    while True:
                        n_type, n_payload = begin_node(stream)
                        if n_type == OTMM_NPC:
                            name = read_string(n_payload)
                            nx, ny, nz = struct.unpack("<HHB", n_payload.read_escaped_bytes(5))
                            n_payload.drain_to_delimiter()
                            npcs.append(
                                NpcSpawnEntry(
                                    name=str(name),
                                    dx=int(nx) - int(cx),
                                    dy=int(ny) - int(cy),
                                )
                            )
                        else:
                            n_payload.drain_to_delimiter()
                            if n_payload.delimiter == NODE_START:
                                consume_siblings_until_end(stream)

                        op = read_u8(stream)
                        if op == NODE_START:
                            continue
                        if op == NODE_END:
                            break
                        raise OTMMError(f"Invalid stream op 0x{op:02X} in OTMM npc spawn")

                areas.append(
                    NpcSpawnArea(
                        center=Position(x=int(cx), y=int(cy), z=int(cz)),
                        radius=int(radius),
                        npcs=tuple(npcs),
                    )
                )
            else:
                node_payload.drain_to_delimiter()
                if node_payload.delimiter == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                return areas
            raise OTMMError(f"Invalid stream op 0x{op:02X} after OTMM_SPAWN_NPC_DATA child")

    def _parse_towns(
        self,
        stream: BinaryIO,
        payload: EscapedPayloadReader,
        *,
        towns: dict[int, Town],
    ) -> None:
        delim = payload.drain_to_delimiter()
        if delim != NODE_START:
            return

        while True:
            node_type, node_payload = begin_node(stream)
            if node_type == OTMM_TOWN:
                town_id = struct.unpack("<I", node_payload.read_escaped_bytes(4))[0]
                name = read_string(node_payload)
                tx, ty, tz = struct.unpack("<HHB", node_payload.read_escaped_bytes(5))
                node_payload.drain_to_delimiter()
                if int(town_id) in towns:
                    self.warnings.append(
                        LoadWarning(code="duplicate_town", message=f"Duplicate town id {town_id}", raw_id=int(town_id))
                    )
                else:
                    towns[int(town_id)] = Town(
                        id=int(town_id),
                        name=str(name),
                        temple_position=Position(x=int(tx), y=int(ty), z=int(tz)),
                    )
            else:
                node_payload.drain_to_delimiter()
                if node_payload.delimiter == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                return
            raise OTMMError(f"Invalid stream op 0x{op:02X} after OTMM_TOWN_DATA child")

    def _parse_houses(
        self,
        stream: BinaryIO,
        payload: EscapedPayloadReader,
        *,
        houses: dict[int, House],
    ) -> None:
        delim = payload.drain_to_delimiter()
        if delim != NODE_START:
            return

        while True:
            node_type, node_payload = begin_node(stream)
            if node_type == OTMM_HOUSE:
                house_id = struct.unpack("<I", node_payload.read_escaped_bytes(4))[0]
                name = read_string(node_payload)
                tail = _read_payload_remainder(node_payload)

                town_id = rent = beds = ex = ey = ez = 0
                if len(tail) == 11:
                    town_id, rent, beds, ex, ey, ez = struct.unpack("<HHHHHB", tail)
                elif len(tail) == 17:
                    town_id, rent, beds, ex, ey, ez = struct.unpack("<IIIHHB", tail)
                else:
                    self.warnings.append(
                        LoadWarning(
                            code="invalid_house_payload",
                            message=(f"Invalid OTMM house payload length {len(tail)} (expected 11 or 17 bytes)"),
                            raw_id=int(house_id),
                        )
                    )
                    continue

                house = houses.get(int(house_id))
                if house is None:
                    continue
                houses[int(house_id)] = House(
                    id=int(house_id),
                    name=str(name),
                    entry=Position(x=int(ex), y=int(ey), z=int(ez)),
                    rent=int(rent),
                    townid=int(town_id),
                    beds=int(beds),
                )
            else:
                node_payload.drain_to_delimiter()
                if node_payload.delimiter == NODE_START:
                    consume_siblings_until_end(stream)

            op = read_u8(stream)
            if op == NODE_START:
                continue
            if op == NODE_END:
                return
            raise OTMMError(f"Invalid stream op 0x{op:02X} after OTMM_HOUSE_DATA child")

    @staticmethod
    def _count_item_tree(item: Item) -> int:
        total = 1
        for child in item.items:
            total += OTMMLoader._count_item_tree(child)
        return total


def load_otmm(path: str | Path, *, items_db: ItemsXML | None = None) -> GameMap:
    """Load an OTMM map (partial MVP)."""

    loader = OTMMLoader(items_db=items_db)
    return loader.load(path)
