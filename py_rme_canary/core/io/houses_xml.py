from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Position
from py_rme_canary.core.exceptions.io import HousesXmlError
from py_rme_canary.core.io.xml.base import as_bool, as_int
from py_rme_canary.core.io.xml.safe import Element
from py_rme_canary.core.io.xml.safe import safe_etree as ET


def parse_houses_xml(xml_text: str) -> dict[int, House]:
    root = ET.fromstring(xml_text)
    if (root.tag or "").strip().lower() != "houses":
        raise HousesXmlError("Invalid root tag: expected <houses>")

    out: dict[int, House] = {}

    for node in list(root):
        if (node.tag or "").strip().lower() != "house":
            continue

        if node.get("houseid") is None:
            # Legacy treats this as invalid and skips.
            continue

        hid = as_int(node.get("houseid"), 0)
        if hid <= 0:
            continue

        # Legacy parity: missing/zero townid removes the house.
        if node.get("townid") is None:
            continue

        name = node.get("name") or ""

        entryx = as_int(node.get("entryx"), 0)
        entryy = as_int(node.get("entryy"), 0)
        entryz = as_int(node.get("entryz"), 0)
        entry = None
        if entryx != 0 and entryy != 0 and entryz != 0:
            entry = Position(entryx, entryy, entryz)

        rent = as_int(node.get("rent"), 0)
        guildhall = as_bool(node.get("guildhall"), False)
        townid = as_int(node.get("townid"), 0)
        if townid <= 0:
            continue
        size = as_int(node.get("size"), 0)
        clientid = as_int(node.get("clientid"), 0)
        beds = as_int(node.get("beds"), 0)

        out[int(hid)] = House(
            id=int(hid),
            name=str(name),
            entry=entry,
            rent=int(rent),
            guildhall=bool(guildhall),
            townid=int(townid),
            size=int(size),
            clientid=int(clientid),
            beds=int(beds),
        )

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


def build_houses_xml(houses: Iterable[House]) -> str:
    root = ET.Element("houses")

    for house in sorted(houses, key=lambda h: int(h.id)):
        node = ET.SubElement(root, "house")
        node.set("name", str(house.name))
        node.set("houseid", str(int(house.id)))

        entry = house.entry or Position(0, 0, 0)
        node.set("entryx", str(int(entry.x)))
        node.set("entryy", str(int(entry.y)))
        node.set("entryz", str(int(entry.z)))

        node.set("rent", str(int(house.rent)))
        if house.guildhall:
            node.set("guildhall", "true")

        node.set("townid", str(int(house.townid)))
        node.set("size", str(int(house.size)))
        node.set("clientid", str(int(house.clientid)))
        node.set("beds", str(int(house.beds)))

    _indent(root)
    return str(ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8"))


def load_houses(path: str | Path) -> dict[int, House]:
    xml_text = Path(path).read_text(encoding="utf-8", errors="replace")
    return parse_houses_xml(xml_text)


def save_houses(path: str | Path, houses: Iterable[House]) -> None:
    Path(path).write_text(build_houses_xml(houses), encoding="utf-8")
