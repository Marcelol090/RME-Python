from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Position
from py_rme_canary.core.data.spawns import MonsterSpawnArea, NpcSpawnArea
from py_rme_canary.core.data.towns import Town
from py_rme_canary.core.data.zones import Zone


@dataclass(frozen=True, slots=True)
class WaypointAction:
    """Undoable mutation of a single waypoint entry in GameMap.waypoints."""

    name: str
    before: Position | None
    after: Position | None

    def has_changes(self) -> bool:
        return self.before != self.after

    def undo(self, game_map: GameMap) -> None:
        key = str(self.name)
        if self.before is None:
            # Defensive: keep undo robust even if waypoints was replaced.
            with suppress(Exception):
                game_map.waypoints.pop(key, None)
            return
        game_map.waypoints[key] = self.before

    def redo(self, game_map: GameMap) -> None:
        key = str(self.name)
        if self.after is None:
            with suppress(Exception):
                game_map.waypoints.pop(key, None)
            return
        game_map.waypoints[key] = self.after

    def describe(self) -> str:
        if self.after is None:
            return f"Delete waypoint: {self.name}"
        if self.before is None:
            return f"Add waypoint: {self.name}"
        return f"Set waypoint: {self.name}"


@dataclass(frozen=True, slots=True)
class TownAction:
    """Undoable mutation of a single town entry in GameMap.towns."""

    town_id: int
    before: Town | None
    after: Town | None

    def has_changes(self) -> bool:
        return self.before != self.after

    def undo(self, game_map: GameMap) -> None:
        tid = int(self.town_id)
        if self.before is None:
            with suppress(Exception):
                game_map.towns.pop(tid, None)
            return
        game_map.towns[tid] = self.before

    def redo(self, game_map: GameMap) -> None:
        tid = int(self.town_id)
        if self.after is None:
            with suppress(Exception):
                game_map.towns.pop(tid, None)
            return
        game_map.towns[tid] = self.after

    def describe(self) -> str:
        tid = int(self.town_id)
        if self.after is None:
            return f"Delete town: {tid}"
        nm = str(getattr(self.after, "name", ""))
        if self.before is None:
            return f"Add town: {tid} ({nm})"
        return f"Set town: {tid} ({nm})"


@dataclass(frozen=True, slots=True)
class HouseAction:
    """Undoable mutation of a single house entry in GameMap.houses (external XML).

    Also captures header change when we default `housefile`.
    """

    house_id: int
    before: House | None
    after: House | None
    header_before: MapHeader
    header_after: MapHeader

    def has_changes(self) -> bool:
        return (self.before != self.after) or (self.header_before != self.header_after)

    def undo(self, game_map: GameMap) -> None:
        hid = int(self.house_id)
        game_map.header = self.header_before
        if self.before is None:
            with suppress(Exception):
                game_map.houses.pop(hid, None)
            return
        game_map.houses[hid] = self.before

    def redo(self, game_map: GameMap) -> None:
        hid = int(self.house_id)
        game_map.header = self.header_after
        if self.after is None:
            with suppress(Exception):
                game_map.houses.pop(hid, None)
            return
        game_map.houses[hid] = self.after

    def describe(self) -> str:
        hid = int(self.house_id)
        if self.after is None:
            return f"Delete house: {hid}"
        nm = str(getattr(self.after, "name", ""))
        if self.before is None:
            return f"Add house: {hid} ({nm})"
        return f"Set house: {hid} ({nm})"


@dataclass(frozen=True, slots=True)
class HouseEntryAction:
    """Undoable mutation of a house entry (legacy 'house exit') position."""

    house_id: int
    before: House | None
    after: House | None
    header_before: MapHeader
    header_after: MapHeader

    def has_changes(self) -> bool:
        return (self.before != self.after) or (self.header_before != self.header_after)

    def undo(self, game_map: GameMap) -> None:
        hid = int(self.house_id)
        game_map.header = self.header_before
        if self.before is None:
            with suppress(Exception):
                game_map.houses.pop(hid, None)
            return
        game_map.houses[hid] = self.before

    def redo(self, game_map: GameMap) -> None:
        hid = int(self.house_id)
        game_map.header = self.header_after
        if self.after is None:
            with suppress(Exception):
                game_map.houses.pop(hid, None)
            return
        game_map.houses[hid] = self.after

    def describe(self) -> str:
        hid = int(self.house_id)
        if self.after is None:
            return f"Clear house entry: {hid}"
        entry = getattr(self.after, "entry", None)
        if entry is None:
            return f"Clear house entry: {hid}"
        return f"Set house entry: {hid}"


@dataclass(frozen=True, slots=True)
class ZoneAction:
    """Undoable mutation of a single zone entry in GameMap.zones (external XML).

    Also captures header change when we default `zonefile`.
    """

    zone_id: int
    before: Zone | None
    after: Zone | None
    header_before: MapHeader
    header_after: MapHeader

    def has_changes(self) -> bool:
        return (self.before != self.after) or (self.header_before != self.header_after)

    def undo(self, game_map: GameMap) -> None:
        zid = int(self.zone_id)
        game_map.header = self.header_before
        if self.before is None:
            with suppress(Exception):
                game_map.zones.pop(zid, None)
            return
        game_map.zones[zid] = self.before

    def redo(self, game_map: GameMap) -> None:
        zid = int(self.zone_id)
        game_map.header = self.header_after
        if self.after is None:
            with suppress(Exception):
                game_map.zones.pop(zid, None)
            return
        game_map.zones[zid] = self.after

    def describe(self) -> str:
        zid = int(self.zone_id)
        if self.after is None:
            return f"Delete zone: {zid}"
        nm = str(getattr(self.after, "name", ""))
        if self.before is None:
            return f"Add zone: {zid} ({nm})"
        return f"Set zone: {zid} ({nm})"


@dataclass(frozen=True, slots=True)
class MonsterSpawnsAction:
    """Undoable mutation of GameMap.monster_spawns and the spawn file header."""

    before: tuple[MonsterSpawnArea, ...]
    after: tuple[MonsterSpawnArea, ...]
    header_before: MapHeader
    header_after: MapHeader
    label: str

    def has_changes(self) -> bool:
        return (self.before != self.after) or (self.header_before != self.header_after)

    def undo(self, game_map: GameMap) -> None:
        game_map.monster_spawns = list(self.before)
        game_map.header = self.header_before

    def redo(self, game_map: GameMap) -> None:
        game_map.monster_spawns = list(self.after)
        game_map.header = self.header_after

    def describe(self) -> str:
        return str(self.label)


@dataclass(frozen=True, slots=True)
class NpcSpawnsAction:
    """Undoable mutation of GameMap.npc_spawns and the spawn file header."""

    before: tuple[NpcSpawnArea, ...]
    after: tuple[NpcSpawnArea, ...]
    header_before: MapHeader
    header_after: MapHeader
    label: str

    def has_changes(self) -> bool:
        return (self.before != self.after) or (self.header_before != self.header_after)

    def undo(self, game_map: GameMap) -> None:
        game_map.npc_spawns = list(self.before)
        game_map.header = self.header_before

    def redo(self, game_map: GameMap) -> None:
        game_map.npc_spawns = list(self.after)
        game_map.header = self.header_after

    def describe(self) -> str:
        return str(self.label)
