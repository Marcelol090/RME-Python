from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Position
from py_rme_canary.core.data.spawns import MonsterSpawnArea, NpcSpawnArea
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.data.zones import Zone
from py_rme_canary.core.io.otbm_loader import OTBMLoader


@dataclass(slots=True)
class ImportMapReport:
    tiles_imported: int = 0
    houses_imported: int = 0
    spawns_imported: int = 0
    zones_imported: int = 0
    skipped_out_of_bounds: int = 0
    house_id_mapping: dict[int, int] = field(default_factory=dict)
    zone_id_mapping: dict[int, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    house_id_mapping: dict[int, int] | None = None
    zone_id_mapping: dict[int, int] | None = None
    warnings: list[str] | None = None

    def __post_init__(self) -> None:
        if self.house_id_mapping is None:
            self.house_id_mapping = {}
        if self.zone_id_mapping is None:
            self.zone_id_mapping = {}
        if self.warnings is None:
            self.warnings = []


def import_map_with_offset(
    *,
    target_map: GameMap,
    source_path: str | Path,
    offset: tuple[int, int, int],
    import_tiles: bool = True,
    import_houses: bool = True,
    import_spawns: bool = True,
    import_zones: bool = False,
    merge_mode: int = 0,
) -> ImportMapReport:
    loader = OTBMLoader()
    source_map = loader.load_with_detection(str(source_path))

    report = ImportMapReport()
    offset_x, offset_y, offset_z = offset

    house_id_mapping: dict[int, int] = {}
    zone_id_mapping: dict[int, int] = {}

    if import_houses:
        house_id_mapping = _build_house_id_mapping(target_map, source_map)
        report.house_id_mapping = dict(house_id_mapping)
        _import_houses(target_map, source_map, offset_x, offset_y, offset_z, house_id_mapping, report)

    if import_zones:
        zone_id_mapping = _build_zone_id_mapping(target_map, source_map)
        report.zone_id_mapping = dict(zone_id_mapping)
        _import_zones(target_map, source_map, zone_id_mapping, report)

    if import_spawns:
        _import_spawns(target_map, source_map, offset_x, offset_y, offset_z, report)

    if import_tiles:
        _import_tiles(
            target_map,
            source_map,
            offset_x,
            offset_y,
            offset_z,
            merge_mode,
            house_id_mapping,
            zone_id_mapping,
            import_spawns,
            report,
        )

    return report


def _build_house_id_mapping(target_map: GameMap, source_map: GameMap) -> dict[int, int]:
    existing = {int(hid) for hid in target_map.houses}
    next_id = max(existing or [0]) + 1
    mapping: dict[int, int] = {}
    for house_id in source_map.houses:
        house_id = int(house_id)
        if house_id not in existing:
            mapping[house_id] = house_id
            existing.add(house_id)
            continue
        mapping[house_id] = next_id
        existing.add(next_id)
        next_id += 1
    return mapping


def _build_zone_id_mapping(target_map: GameMap, source_map: GameMap) -> dict[int, int]:
    existing = {int(zid) for zid in target_map.zones}
    next_id = max(existing or [0]) + 1
    mapping: dict[int, int] = {}
    for zone_id, zone in source_map.zones.items():
        zone_id = int(zone_id)
        if zone_id not in existing:
            mapping[zone_id] = zone_id
            existing.add(zone_id)
            continue
        if zone_id in target_map.zones and target_map.zones[zone_id].name == zone.name:
            mapping[zone_id] = zone_id
            continue
        mapping[zone_id] = next_id
        existing.add(next_id)
        next_id += 1
    return mapping


def _import_houses(
    target_map: GameMap,
    source_map: GameMap,
    offset_x: int,
    offset_y: int,
    offset_z: int,
    house_id_mapping: dict[int, int],
    report: ImportMapReport,
) -> None:
    for source_id, house in source_map.houses.items():
        new_id = house_id_mapping.get(int(source_id), int(source_id))
        entry = house.entry
        if entry is not None:
            entry = Position(
                x=int(entry.x) + int(offset_x),
                y=int(entry.y) + int(offset_y),
                z=int(entry.z) + int(offset_z),
            )
        target_map.houses[int(new_id)] = House(
            id=int(new_id),
            name=house.name,
            entry=entry,
            rent=house.rent,
            guildhall=house.guildhall,
            townid=house.townid,
            size=house.size,
            clientid=house.clientid,
            beds=house.beds,
        )
        report.houses_imported += 1


def _import_zones(
    target_map: GameMap,
    source_map: GameMap,
    zone_id_mapping: dict[int, int],
    report: ImportMapReport,
) -> None:
    for source_id, zone in source_map.zones.items():
        new_id = zone_id_mapping.get(int(source_id), int(source_id))
        if int(new_id) not in target_map.zones:
            target_map.zones[int(new_id)] = Zone(id=int(new_id), name=zone.name)
            report.zones_imported += 1


def _import_spawns(
    target_map: GameMap,
    source_map: GameMap,
    offset_x: int,
    offset_y: int,
    offset_z: int,
    report: ImportMapReport,
) -> None:
    for area in source_map.monster_spawns:
        center = Position(
            x=int(area.center.x) + int(offset_x),
            y=int(area.center.y) + int(offset_y),
            z=int(area.center.z) + int(offset_z),
        )
        target_map.monster_spawns.append(MonsterSpawnArea(center=center, radius=area.radius, monsters=area.monsters))
        report.spawns_imported += 1

    for npc_area in source_map.npc_spawns:
        center = Position(
            x=int(npc_area.center.x) + int(offset_x),
            y=int(npc_area.center.y) + int(offset_y),
            z=int(npc_area.center.z) + int(offset_z),
        )
        target_map.npc_spawns.append(NpcSpawnArea(center=center, radius=npc_area.radius, npcs=npc_area.npcs))
        report.spawns_imported += 1


def _import_tiles(
    target_map: GameMap,
    source_map: GameMap,
    offset_x: int,
    offset_y: int,
    offset_z: int,
    merge_mode: int,
    house_id_mapping: dict[int, int],
    zone_id_mapping: dict[int, int],
    import_spawns: bool,
    report: ImportMapReport,
) -> None:
    max_x = int(target_map.header.width)
    max_y = int(target_map.header.height)

    for key, tile in source_map.tiles.items():
        sx, sy, sz = key
        tx = int(sx) + int(offset_x)
        ty = int(sy) + int(offset_y)
        tz = int(sz) + int(offset_z)
        if not (0 <= tx < max_x and 0 <= ty < max_y and 0 <= tz <= 15):
            report.skipped_out_of_bounds += 1
            continue

        updated_tile = _offset_tile(tile, tx, ty, tz, house_id_mapping, zone_id_mapping, import_spawns)
        existing = target_map.get_tile(tx, ty, tz)

        if merge_mode == 1 or existing is None:
            target_map.set_tile(updated_tile)
            report.tiles_imported += 1
            continue

        if merge_mode == 2:
            merged = _merge_tiles(existing, updated_tile, skip_items=True)
            target_map.set_tile(merged)
            report.tiles_imported += 1
            continue

        merged = _merge_tiles(existing, updated_tile, skip_items=False)
        target_map.set_tile(merged)
        report.tiles_imported += 1


def _offset_tile(
    tile: Tile,
    x: int,
    y: int,
    z: int,
    house_id_mapping: dict[int, int],
    zone_id_mapping: dict[int, int],
    import_spawns: bool,
) -> Tile:
    house_id = tile.house_id
    if house_id is not None and house_id_mapping:
        house_id = house_id_mapping.get(int(house_id), int(house_id))

    zones = tile.zones
    if zones and zone_id_mapping:
        zones = frozenset(zone_id_mapping.get(int(zid), int(zid)) for zid in zones)

    spawn_monster = tile.spawn_monster if import_spawns else None
    spawn_npc = tile.spawn_npc if import_spawns else None

    return replace(
        tile,
        x=int(x),
        y=int(y),
        z=int(z),
        items=list(tile.items),
        monsters=list(tile.monsters),
        house_id=house_id,
        zones=zones,
        spawn_monster=spawn_monster,
        spawn_npc=spawn_npc,
        modified=True,
    )


def _merge_tiles(target: Tile, incoming: Tile, *, skip_items: bool) -> Tile:
    ground = target.ground or incoming.ground
    items = list(target.items)
    monsters = list(target.monsters)
    npc = target.npc

    if not skip_items:
        items.extend(list(incoming.items))
        monsters.extend(list(incoming.monsters))
        npc = npc or incoming.npc

    house_id = target.house_id if target.house_id is not None else incoming.house_id
    map_flags = int(target.map_flags) | int(incoming.map_flags)
    zones = frozenset(set(target.zones).union(set(incoming.zones)))
    spawn_monster = target.spawn_monster or incoming.spawn_monster
    spawn_npc = target.spawn_npc or incoming.spawn_npc

    return replace(
        target,
        ground=ground,
        items=items,
        monsters=monsters,
        npc=npc,
        house_id=house_id,
        map_flags=map_flags,
        zones=zones,
        spawn_monster=spawn_monster,
        spawn_npc=spawn_npc,
        modified=True,
    )
