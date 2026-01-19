from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterable
from pathlib import Path

from py_rme_canary.core.data.item import Position
from py_rme_canary.core.data.spawns import (
    MonsterSpawnArea,
    MonsterSpawnEntry,
    NpcSpawnArea,
    NpcSpawnEntry,
)
from py_rme_canary.core.exceptions.io import SpawnXmlError
from py_rme_canary.core.io.xml.base import as_int


def _require_tag(root: ET.Element, expected_lower: str) -> None:
    if (root.tag or "").strip().lower() != expected_lower:
        raise SpawnXmlError(f"Invalid root tag: expected <{expected_lower}>")


def parse_monster_spawns_xml(xml_text: str) -> tuple[MonsterSpawnArea, ...]:
    root = ET.fromstring(xml_text)
    _require_tag(root, "monsters")

    areas: list[MonsterSpawnArea] = []

    for spawn_node in list(root):
        if (spawn_node.tag or "").strip().lower() != "monster":
            continue

        centerx = as_int(spawn_node.get("centerx"))
        centery = as_int(spawn_node.get("centery"))
        centerz = as_int(spawn_node.get("centerz"))
        if centerx == 0 or centery == 0:
            continue

        radius = as_int(spawn_node.get("radius"))
        if radius < 1:
            continue

        entries: list[MonsterSpawnEntry] = []
        max_abs_dx = 0
        max_abs_dy = 0
        for child in list(spawn_node):
            if (child.tag or "").strip().lower() != "monster":
                continue

            name = (child.get("name") or "").strip()
            if not name:
                # Legacy breaks out of this spawn block on malformed entries.
                break

            if child.get("x") is None or child.get("y") is None:
                break

            dx = as_int(child.get("x"))
            dy = as_int(child.get("y"))
            max_abs_dx = max(max_abs_dx, abs(int(dx)))
            max_abs_dy = max(max_abs_dy, abs(int(dy)))
            spawntime = as_int(child.get("spawntime"), 0)

            direction: int | None = None
            if child.get("direction") is not None:
                direction = as_int(child.get("direction"), -1)
                if direction < 0:
                    direction = None
                if direction == 0:
                    direction = None

            weight: int | None = None
            if child.get("weight") is not None:
                weight = as_int(child.get("weight"), 0)
                if weight <= 0:
                    weight = None

            # Legacy stores z, but it is effectively the spawn's z.
            _ = as_int(child.get("z"), centerz)

            entries.append(
                MonsterSpawnEntry(
                    name=name,
                    dx=int(dx),
                    dy=int(dy),
                    spawntime=int(spawntime),
                    direction=direction,
                    weight=weight,
                )
            )

        areas.append(
            MonsterSpawnArea(
                center=Position(int(centerx), int(centery), int(centerz)),
                radius=int(max(int(radius), max_abs_dx, max_abs_dy)),
                monsters=tuple(entries),
            )
        )

    return tuple(areas)


def parse_npc_spawns_xml(xml_text: str) -> tuple[NpcSpawnArea, ...]:
    root = ET.fromstring(xml_text)
    _require_tag(root, "npcs")

    areas: list[NpcSpawnArea] = []

    for spawn_node in list(root):
        if (spawn_node.tag or "").strip().lower() != "npc":
            continue

        centerx = as_int(spawn_node.get("centerx"))
        centery = as_int(spawn_node.get("centery"))
        centerz = as_int(spawn_node.get("centerz"))
        if centerx == 0 or centery == 0:
            continue

        radius = as_int(spawn_node.get("radius"))
        if radius < 1:
            continue

        entries: list[NpcSpawnEntry] = []
        max_abs_dx = 0
        max_abs_dy = 0
        for child in list(spawn_node):
            if (child.tag or "").strip().lower() != "npc":
                continue

            name = (child.get("name") or "").strip()
            if not name:
                break

            if child.get("x") is None or child.get("y") is None:
                break

            dx = as_int(child.get("x"))
            dy = as_int(child.get("y"))
            max_abs_dx = max(max_abs_dx, abs(int(dx)))
            max_abs_dy = max(max_abs_dy, abs(int(dy)))
            spawntime = as_int(child.get("spawntime"), 0)

            direction: int | None = None
            if child.get("direction") is not None:
                direction = as_int(child.get("direction"), -1)
                if direction < 0:
                    direction = None
                if direction == 0:
                    direction = None

            _ = as_int(child.get("z"), centerz)

            entries.append(
                NpcSpawnEntry(
                    name=name,
                    dx=int(dx),
                    dy=int(dy),
                    spawntime=int(spawntime),
                    direction=direction,
                )
            )

        areas.append(
            NpcSpawnArea(
                center=Position(int(centerx), int(centery), int(centerz)),
                radius=int(max(int(radius), max_abs_dx, max_abs_dy)),
                npcs=tuple(entries),
            )
        )

    return tuple(areas)


def _xml_bytes(doc: ET.ElementTree) -> bytes:
    # Matches legacy in spirit: UTF-8 + XML declaration.
    root = doc.getroot()
    if root is None:
        return b""
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _indent(elem: ET.Element, level: int = 0) -> None:
    # Pretty-print (ElementTree has no default pretty printer).
    i = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        for child in elem:
            _indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


def build_monster_spawns_xml(areas: Iterable[MonsterSpawnArea]) -> str:
    root = ET.Element("monsters")

    for area in areas:
        spawn = ET.SubElement(root, "monster")
        spawn.set("centerx", str(int(area.center.x)))
        spawn.set("centery", str(int(area.center.y)))
        spawn.set("centerz", str(int(area.center.z)))
        spawn.set("radius", str(int(area.radius)))

        for entry in area.monsters:
            m = ET.SubElement(spawn, "monster")
            m.set("name", str(entry.name))
            m.set("x", str(int(entry.dx)))
            m.set("y", str(int(entry.dy)))
            m.set("z", str(int(area.center.z)))
            m.set("spawntime", str(int(entry.spawntime)))
            if entry.direction is not None and int(entry.direction) != 0:
                m.set("direction", str(int(entry.direction)))
            if entry.weight is not None:
                m.set("weight", str(int(entry.weight)))

    _indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def build_npc_spawns_xml(areas: Iterable[NpcSpawnArea]) -> str:
    root = ET.Element("npcs")

    for area in areas:
        spawn = ET.SubElement(root, "npc")
        spawn.set("centerx", str(int(area.center.x)))
        spawn.set("centery", str(int(area.center.y)))
        spawn.set("centerz", str(int(area.center.z)))
        spawn.set("radius", str(int(area.radius)))

        for entry in area.npcs:
            n = ET.SubElement(spawn, "npc")
            n.set("name", str(entry.name))
            n.set("x", str(int(entry.dx)))
            n.set("y", str(int(entry.dy)))
            n.set("z", str(int(area.center.z)))
            n.set("spawntime", str(int(entry.spawntime)))
            if entry.direction is not None and int(entry.direction) != 0:
                n.set("direction", str(int(entry.direction)))

    _indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


def load_monster_spawns(path: str | Path) -> tuple[MonsterSpawnArea, ...]:
    xml_text = Path(path).read_text(encoding="utf-8", errors="replace")
    return parse_monster_spawns_xml(xml_text)


def load_npc_spawns(path: str | Path) -> tuple[NpcSpawnArea, ...]:
    xml_text = Path(path).read_text(encoding="utf-8", errors="replace")
    return parse_npc_spawns_xml(xml_text)


def save_monster_spawns(path: str | Path, areas: Iterable[MonsterSpawnArea]) -> None:
    Path(path).write_text(build_monster_spawns_xml(areas), encoding="utf-8")


def save_npc_spawns(path: str | Path, areas: Iterable[NpcSpawnArea]) -> None:
    Path(path).write_text(build_npc_spawns_xml(areas), encoding="utf-8")
