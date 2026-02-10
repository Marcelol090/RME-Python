from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from py_rme_canary.core.data.zones import Zone
from py_rme_canary.core.exceptions.io import ZonesXmlError
from py_rme_canary.core.io.xml.base import as_int
from py_rme_canary.core.io.xml.safe import Element
from py_rme_canary.core.io.xml.safe import safe_etree as ET


def parse_zones_xml(xml_text: str) -> dict[int, Zone]:
    root = ET.fromstring(xml_text)
    if (root.tag or "").strip().lower() != "zones":
        raise ZonesXmlError("Invalid root tag: expected <zones>")

    out: dict[int, Zone] = {}

    for node in list(root):
        if (node.tag or "").strip().lower() != "zone":
            continue

        zid = as_int(node.get("zoneid"), 0)
        if zid <= 0:
            continue

        name = node.get("name") or ""
        out[int(zid)] = Zone(id=int(zid), name=str(name))

    return out


def _indent(elem: Element, level: int = 0) -> None:
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


def build_zones_xml(zones: Iterable[Zone]) -> str:
    root = ET.Element("zones")

    for zone in sorted(zones, key=lambda z: int(z.id)):
        if int(zone.id) <= 0:
            continue
        node = ET.SubElement(root, "zone")
        node.set("name", str(zone.name))
        node.set("zoneid", str(int(zone.id)))

    _indent(root)
    return str(ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8"))


def load_zones(path: str | Path) -> dict[int, Zone]:
    xml_text = Path(path).read_text(encoding="utf-8", errors="replace")
    return parse_zones_xml(xml_text)


def save_zones(path: str | Path, zones: Iterable[Zone]) -> None:
    Path(path).write_text(build_zones_xml(zones), encoding="utf-8")
