"""Map validation utilities."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Literal

from py_rme_canary.core.data.gamemap import GameMap, TileKey
from py_rme_canary.core.data.item import Position

ValidationSeverity = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    severity: ValidationSeverity
    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class MapValidationResult:
    issues: list[ValidationIssue] = field(default_factory=list)

    def add(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)

    def extend(self, issues: Iterable[ValidationIssue]) -> None:
        self.issues.extend(list(issues))

    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)


class MapValidator:
    """Validate structural consistency of a GameMap."""

    def __init__(self, game_map: GameMap, *, max_z: int = 15) -> None:
        self._map: GameMap = game_map
        self._max_z: int = int(max_z)
        self._result = MapValidationResult()

    def validate(self) -> MapValidationResult:
        self._validate_header()
        self._validate_tiles()
        self._validate_waypoints()
        self._validate_towns()
        self._validate_houses()
        self._validate_zones()
        self._validate_spawns()
        return self._result

    def _add(self, severity: ValidationSeverity, code: str, message: str, **context: Any) -> None:
        self._result.add(
            ValidationIssue(
                severity=severity,
                code=str(code),
                message=str(message),
                context={k: v for k, v in context.items() if v is not None},
            )
        )

    def _in_bounds(self, x: int, y: int, z: int) -> bool:
        h = self._map.header
        return 0 <= int(x) < int(h.width) and 0 <= int(y) < int(h.height) and 0 <= int(z) <= self._max_z

    def _validate_header(self) -> None:
        h = self._map.header
        if int(h.width) <= 0 or int(h.height) <= 0:
            self._add(
                "error",
                "MAP_DIMENSIONS_INVALID",
                "Map dimensions must be positive.",
                width=h.width,
                height=h.height,
            )

    def _validate_tiles(self) -> None:
        used_house_ids: set[int] = set()
        used_zone_ids: set[int] = set()
        invalid_positions: list[TileKey] = []

        for tile in self._map.iter_tiles():
            x, y, z = int(tile.x), int(tile.y), int(tile.z)
            if not self._in_bounds(x, y, z):
                invalid_positions.append((x, y, z))
                continue

            if tile.house_id is not None:
                used_house_ids.add(int(tile.house_id))
                if int(tile.house_id) not in self._map.houses:
                    self._add(
                        "error",
                        "HOUSE_ID_MISSING",
                        "Tile references a house id that is not defined.",
                        house_id=int(tile.house_id),
                        position=(x, y, z),
                    )

            for zid in tile.zones:
                used_zone_ids.add(int(zid))
                if int(zid) not in self._map.zones:
                    self._add(
                        "warning",
                        "ZONE_ID_MISSING",
                        "Tile references a zone id that is not defined.",
                        zone_id=int(zid),
                        position=(x, y, z),
                    )

        if invalid_positions:
            self._add(
                "error",
                "TILE_OUT_OF_BOUNDS",
                "One or more tiles are outside map bounds.",
                count=len(invalid_positions),
                sample=invalid_positions[:5],
            )

        self._used_house_ids = used_house_ids
        self._used_zone_ids = used_zone_ids

    def _validate_waypoints(self) -> None:
        for name, pos in self._map.waypoints.items():
            if not name:
                self._add("warning", "WAYPOINT_EMPTY_NAME", "Waypoint name is empty.")
            if not self._in_bounds(int(pos.x), int(pos.y), int(pos.z)):
                self._add(
                    "warning",
                    "WAYPOINT_OUT_OF_BOUNDS",
                    "Waypoint position is outside map bounds.",
                    name=str(name),
                    position=(int(pos.x), int(pos.y), int(pos.z)),
                )

    def _validate_towns(self) -> None:
        for town_id, town in self._map.towns.items():
            if int(town_id) <= 0:
                self._add("error", "TOWN_ID_INVALID", "Town id must be positive.", town_id=int(town_id))
            pos = town.temple_position
            if not self._in_bounds(int(pos.x), int(pos.y), int(pos.z)):
                self._add(
                    "error",
                    "TOWN_TEMPLE_OUT_OF_BOUNDS",
                    "Town temple position is outside map bounds.",
                    town_id=int(town_id),
                    position=(int(pos.x), int(pos.y), int(pos.z)),
                )

    def _validate_houses(self) -> None:
        used_house_ids: set[int] = getattr(self, "_used_house_ids", set())
        town_ids = {int(tid) for tid in self._map.towns}

        for house_id, house in self._map.houses.items():
            if int(house_id) <= 0:
                self._add("error", "HOUSE_ID_INVALID", "House id must be positive.", house_id=int(house_id))

            if int(house_id) not in used_house_ids:
                self._add(
                    "warning",
                    "HOUSE_UNUSED",
                    "House is defined but no tile references it.",
                    house_id=int(house_id),
                )

            if int(house.townid) != 0 and int(house.townid) not in town_ids:
                self._add(
                    "warning",
                    "HOUSE_TOWN_MISSING",
                    "House references a town id that is not defined.",
                    house_id=int(house_id),
                    town_id=int(house.townid),
                )

            if house.entry is not None:
                pos = house.entry
                if not self._in_bounds(int(pos.x), int(pos.y), int(pos.z)):
                    self._add(
                        "warning",
                        "HOUSE_ENTRY_OUT_OF_BOUNDS",
                        "House entry position is outside map bounds.",
                        house_id=int(house_id),
                        position=(int(pos.x), int(pos.y), int(pos.z)),
                    )
                else:
                    tile = self._map.get_tile(int(pos.x), int(pos.y), int(pos.z))
                    if tile is None:
                        self._add(
                            "warning",
                            "HOUSE_ENTRY_MISSING_TILE",
                            "House entry position has no tile.",
                            house_id=int(house_id),
                            position=(int(pos.x), int(pos.y), int(pos.z)),
                        )

    def _validate_zones(self) -> None:
        used_zone_ids: set[int] = getattr(self, "_used_zone_ids", set())
        for zone_id, zone in self._map.zones.items():
            if int(zone_id) <= 0:
                self._add("error", "ZONE_ID_INVALID", "Zone id must be positive.", zone_id=int(zone_id))
            if not zone.name:
                self._add("warning", "ZONE_EMPTY_NAME", "Zone name is empty.", zone_id=int(zone_id))
            if int(zone_id) not in used_zone_ids:
                self._add(
                    "warning",
                    "ZONE_UNUSED",
                    "Zone is defined but not referenced by any tile.",
                    zone_id=int(zone_id),
                )

    def _validate_spawns(self) -> None:
        def check_position(kind: str, pos: Position) -> None:
            if not self._in_bounds(int(pos.x), int(pos.y), int(pos.z)):
                kind_code = str(kind).upper()
                kind_label = str(kind).replace("_", " ").title()
                self._add(
                    "error",
                    f"{kind_code}_OUT_OF_BOUNDS",
                    f"{kind_label} spawn center is outside map bounds.",
                    position=(int(pos.x), int(pos.y), int(pos.z)),
                )

        for monster_area in self._map.monster_spawns:
            check_position("monster_spawn", monster_area.center)
            if int(monster_area.radius) < 0:
                self._add(
                    "error",
                    "MONSTER_SPAWN_RADIUS_INVALID",
                    "Monster spawn radius must be non-negative.",
                    radius=int(monster_area.radius),
                    position=(int(monster_area.center.x), int(monster_area.center.y), int(monster_area.center.z)),
                )
            for monster_entry in monster_area.monsters:
                if not monster_entry.name:
                    self._add(
                        "warning",
                        "MONSTER_SPAWN_EMPTY_NAME",
                        "Monster spawn entry has empty name.",
                        position=(int(monster_area.center.x), int(monster_area.center.y), int(monster_area.center.z)),
                    )

        for npc_area in self._map.npc_spawns:
            check_position("npc_spawn", npc_area.center)
            if int(npc_area.radius) < 0:
                self._add(
                    "error",
                    "NPC_SPAWN_RADIUS_INVALID",
                    "NPC spawn radius must be non-negative.",
                    radius=int(npc_area.radius),
                    position=(int(npc_area.center.x), int(npc_area.center.y), int(npc_area.center.z)),
                )
            for npc_entry in npc_area.npcs:
                if not npc_entry.name:
                    self._add(
                        "warning",
                        "NPC_SPAWN_EMPTY_NAME",
                        "NPC spawn entry has empty name.",
                        position=(int(npc_area.center.x), int(npc_area.center.y), int(npc_area.center.z)),
                    )


def validate_game_map(game_map: GameMap) -> MapValidationResult:
    return MapValidator(game_map).validate()
