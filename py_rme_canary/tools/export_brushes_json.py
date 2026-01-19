"""Export a simplified brushes.json from RME materials XML.

Goal
- Convert a subset of RME brush definitions in `data/materials/brushs/*.xml` into
  the JSON schema consumed by `py_rme_canary.logic_layer.brush_definitions`.

Scope (intentional)
- Supports `wall` and `carpet` brushes first, because they contain direct item
  ids in a way that maps cleanly to the current Python auto-border model.
- Other brush types (e.g. `ground` with `<border align="outer" id="..."/>`) use
  RME's richer border system and need a dedicated parser; this exporter will
  skip them for now.

Output schema (current)
{
  "brushes": [
    {
      "name": "Stone Wall",
      "server_id": 1295,
      "type": "wall",
      "borders": {"HORIZONTAL": 1295, "VERTICAL": 1294, ...}
    },
    ...
  ]
}

Run
- `python -m py_rme_canary.tools.export_brushes_json --out data/brushes.json`
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree


@dataclass(frozen=True, slots=True)
class ExportBrush:
    name: str
    server_id: int
    brush_type: str
    borders: dict[str, int]
    transitions: tuple[dict, ...] = ()


def _int_attr(elem: ElementTree.Element, name: str) -> int | None:
    v = elem.get(name)
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def _pick_best_item_id(parent: ElementTree.Element) -> int | None:
    """Pick an item id from children like `<item id="..." chance="..."/>`.

    Strategy: choose max(chance), tie-breaker by first occurrence.
    """

    best_id: int | None = None
    best_chance: int = -1

    for child in parent.findall("item"):
        item_id = _int_attr(child, "id")
        if item_id is None:
            continue
        chance = _int_attr(child, "chance")
        if chance is None:
            chance = 0
        if chance > best_chance:
            best_chance = chance
            best_id = int(item_id)

    return best_id


_BORDER_EDGE_TO_KEY: dict[str, str] = {
    "n": "NORTH",
    "e": "EAST",
    "s": "SOUTH",
    "w": "WEST",
    # Outer corners (RME borderitem edge="c??")
    "cnw": "NORTH_WEST",
    "cne": "NORTH_EAST",
    "cse": "SOUTH_EAST",
    "csw": "SOUTH_WEST",
    "dnw": "INNER_CORNER_NW",
    "dne": "INNER_CORNER_NE",
    "dse": "INNER_CORNER_SE",
    "dsw": "INNER_CORNER_SW",
}


_CARDINAL_EDGE_TO_KEY: dict[str, str] = {
    "n": "NORTH",
    "e": "EAST",
    "s": "SOUTH",
    "w": "WEST",
}


def _load_border_sets(borders_xml_path: Path) -> dict[int, dict[str, int]]:
    """Load border sets from `data/materials/borders/borders.xml`."""

    tree = ElementTree.parse(borders_xml_path)
    root = tree.getroot()

    out: dict[int, dict[str, int]] = {}
    for border in root.findall("border"):
        border_id = _int_attr(border, "id")
        if border_id is None:
            continue
        items: dict[str, int] = {}
        for bi in border.findall("borderitem"):
            edge = (bi.get("edge") or "").strip().lower()
            item_id = _int_attr(bi, "item")
            if not edge or item_id is None:
                continue
            key = _BORDER_EDGE_TO_KEY.get(edge)
            if key is None:
                continue
            items[key] = int(item_id)
        if items:
            out[int(border_id)] = items
    return out


_XML_AMPERSAND_RE = re.compile(r"&(?!#\d+;|#x[0-9A-Fa-f]+;|\w+;)")


def _strip_invalid_xml_chars(text: str) -> str:
    """Remove characters that are invalid in XML 1.0.

    Keeps: tab, newline, carriage return, and all characters >= 0x20.
    """

    return "".join(ch for ch in text if ch in ("\t", "\n", "\r") or ord(ch) >= 0x20)


def _parse_xml_root_tolerant(xml_path: Path) -> ElementTree.Element:
    """Parse XML, fixing common real-world RME data issues.

    RME material XMLs sometimes contain unescaped ampersands in attribute values
    (e.g. brush names like "rock soil & cave ground"), which is not well-formed
    XML. This parser escapes bare ampersands and strips invalid control chars.
    """

    raw = xml_path.read_text(encoding="utf-8", errors="replace")
    raw = _strip_invalid_xml_chars(raw)
    raw = _XML_AMPERSAND_RE.sub("&amp;", raw)
    return ElementTree.fromstring(raw)


_CARPET_ALIGN_TO_KEY: dict[str, str] = {
    "n": "NORTH",
    "e": "EAST",
    "s": "SOUTH",
    "w": "WEST",
    "cnw": "CORNER_NW",
    "cne": "CORNER_NE",
    "cse": "CORNER_SE",
    "csw": "CORNER_SW",
}


def _export_carpet_brush(brush: ElementTree.Element) -> ExportBrush | None:
    name = (brush.get("name") or "").strip()
    server_id = _int_attr(brush, "server_lookid")
    if server_id is None:
        server_id = _int_attr(brush, "lookid")
    if server_id is None:
        server_id = _pick_best_item_id(brush)
    if server_id is None:
        return None

    borders: dict[str, int] = {"SOLITARY": int(server_id)}
    for carpet in brush.findall("carpet"):
        align = (carpet.get("align") or "").strip().lower()
        item_id = _int_attr(carpet, "id")
        if not align or item_id is None:
            continue
        key = _CARPET_ALIGN_TO_KEY.get(align)
        if key is None:
            continue
        borders[key] = int(item_id)

    # Only export if we got at least one directional entry.
    if len(borders) <= 1:
        return None

    return ExportBrush(
        name=name or f"carpet:{server_id}", server_id=int(server_id), brush_type="carpet", borders=borders
    )


def _export_wall_brush(brush: ElementTree.Element) -> ExportBrush | None:
    name = (brush.get("name") or "").strip()
    server_id = _int_attr(brush, "server_lookid")
    if server_id is None:
        server_id = _int_attr(brush, "lookid")
    if server_id is None:
        server_id = _pick_best_item_id(brush)
    if server_id is None:
        return None

    borders: dict[str, int] = {}

    # RME walls contain `<wall type="horizontal|vertical|corner|pole">` blocks.
    wall_blocks = list(brush.findall("wall"))
    for block in wall_blocks:
        t = (block.get("type") or "").strip().lower()
        best_item = _pick_best_item_id(block)
        if best_item is None:
            continue

        if t == "horizontal":
            borders["HORIZONTAL"] = int(best_item)
        elif t == "vertical":
            borders["VERTICAL"] = int(best_item)
        elif t == "corner":
            # The XML doesn't encode direction. Use same id for all corners.
            borders["CORNER_NE"] = int(best_item)
            borders["CORNER_NW"] = int(best_item)
            borders["CORNER_SE"] = int(best_item)
            borders["CORNER_SW"] = int(best_item)
        elif t == "pole":
            borders["SOLITARY"] = int(best_item)
            borders["END_NORTH"] = int(best_item)
            borders["END_SOUTH"] = int(best_item)
            borders["END_EAST"] = int(best_item)
            borders["END_WEST"] = int(best_item)

    # Ensure SOLITARY exists to make fallback deterministic.
    if "SOLITARY" not in borders:
        borders["SOLITARY"] = int(server_id)

    # Only export if we have something useful.
    if len(borders) <= 1:
        return None

    return ExportBrush(name=name or f"wall:{server_id}", server_id=int(server_id), brush_type="wall", borders=borders)


def _export_ground_brush(
    brush: ElementTree.Element,
    *,
    border_sets: dict[int, dict[str, int]],
    name_to_server_id: dict[str, int],
    border_set_to_server_ids: dict[int, list[int]],
) -> ExportBrush | None:
    """Export a `type="ground"` brush using a simple outer border set.

    This handles the common pattern:
    - `<item id="..." chance="..."/>` variants
    - `<border align="outer" id="X"/>`

    It intentionally skips advanced cases where `<border>` contains child
    match rules (`<match_border .../>`).
    """

    name = (brush.get("name") or "").strip()
    server_id = _int_attr(brush, "server_lookid")
    if server_id is None:
        server_id = _int_attr(brush, "lookid")
    if server_id is None:
        server_id = _pick_best_item_id(brush)
    if server_id is None:
        return None

    outer_border_id: int | None = None
    for b in brush.findall("border"):
        align = (b.get("align") or "").strip().lower()
        if align != "outer":
            continue
        outer_border_id = _int_attr(b, "id")
        if outer_border_id is not None:
            break

    if outer_border_id is None:
        return None
    border_items = border_sets.get(int(outer_border_id))
    if not border_items:
        return None

    borders: dict[str, int] = {"SOLITARY": int(server_id)}
    borders.update({k: int(v) for k, v in border_items.items()})

    transitions_by_to: dict[int, dict[str, int]] = {}

    # 1) Explicit inner transitions: <border align="inner" to="..." id="..."/>
    for b in brush.findall("border"):
        align = (b.get("align") or "").strip().lower()
        if align != "inner":
            continue
        if list(b):
            continue
        to_name = (b.get("to") or "").strip()
        if not to_name or to_name.lower() == "none":
            continue
        to_server_id = name_to_server_id.get(to_name)
        if to_server_id is None:
            continue
        inner_border_id = _int_attr(b, "id")
        if inner_border_id is None:
            continue
        inner_items = border_sets.get(int(inner_border_id))
        if not inner_items:
            continue
        transitions_by_to[int(to_server_id)] = {k: int(v) for k, v in inner_items.items()}

    # 2) match_border / replace_border rule blocks inside an outer border.
    #
    # RME uses these for special-case overrides when two border systems meet.
    # We approximate by converting them into transition border overrides keyed
    # by the neighboring ground's *outer border set id*.
    for outer in brush.findall("border"):
        align = (outer.get("align") or "").strip().lower()
        if align != "outer":
            continue
        outer_id = _int_attr(outer, "id")
        if outer_id is None:
            continue
        if not list(outer):
            continue

        for spec in outer.findall("specific"):
            cond = spec.find("conditions")
            act = spec.find("actions")
            if cond is None or act is None:
                continue

            matches = list(cond.findall("match_border"))
            replaces = list(act.findall("replace_border"))
            if not matches or not replaces:
                continue

            # Pick the "other" border set id involved in this rule.
            other_border_id: int | None = None
            other_edge: str | None = None
            for m in matches:
                mid = _int_attr(m, "id")
                edge = (m.get("edge") or "").strip().lower()
                if mid is None or not edge:
                    continue
                if int(mid) == int(outer_id):
                    continue
                other_border_id = int(mid)
                other_edge = edge
                break
            if other_border_id is None:
                continue

            # Action must replace a border from the other border set.
            rep = None
            for r in replaces:
                rid = _int_attr(r, "id")
                if rid is None or int(rid) != int(other_border_id):
                    continue
                rep = r
                break
            if rep is None:
                continue

            rep_edge = (rep.get("edge") or "").strip().lower()
            with_item = _int_attr(rep, "with")
            if not rep_edge or with_item is None:
                continue

            # Only handle simple cardinal overrides.
            key = _CARDINAL_EDGE_TO_KEY.get(rep_edge)
            if key is None:
                continue

            # Resolve which ground(s) use this other border set.
            server_ids = border_set_to_server_ids.get(int(other_border_id))
            if not server_ids:
                continue

            base_items = border_sets.get(int(other_border_id))
            if not base_items:
                continue
            base = {k: int(v) for k, v in base_items.items()}
            base[key] = int(with_item)

            for to_sid in server_ids:
                existing = transitions_by_to.get(int(to_sid))
                if existing is None:
                    transitions_by_to[int(to_sid)] = dict(base)
                else:
                    existing[key] = int(with_item)

    return ExportBrush(
        name=name or f"ground:{server_id}",
        server_id=int(server_id),
        brush_type="ground",
        borders=borders,
        transitions=tuple({"to_server_id": int(k), "borders": v} for k, v in transitions_by_to.items()),
    )


def _brush_primary_server_id(brush: ElementTree.Element) -> int | None:
    server_id = _int_attr(brush, "server_lookid")
    if server_id is None:
        server_id = _int_attr(brush, "lookid")
    if server_id is None:
        server_id = _pick_best_item_id(brush)
    if server_id is None:
        return None
    return int(server_id)


def iter_exported_brushes(materials_dir: Path, *, borders_dir: Path | None = None) -> Iterable[ExportBrush]:
    borders_xml = None
    if borders_dir is not None:
        borders_xml = borders_dir / "borders.xml"
    else:
        borders_xml = Path("data") / "materials" / "borders" / "borders.xml"

    border_sets = {}
    if borders_xml.exists():
        border_sets = _load_border_sets(borders_xml)

    # Build a name->server_id index for ground brushes to resolve `<border align="inner" to="..."/>`.
    name_to_server_id: dict[str, int] = {}
    # Also build border-set-id -> ground server_ids mapping (used to approximate
    # match_border/replace_border blocks into per-target transitions).
    border_set_to_server_ids: dict[int, list[int]] = {}
    xml_files = sorted(materials_dir.glob("*.xml"))
    for xml_path in xml_files:
        try:
            root = _parse_xml_root_tolerant(xml_path)
        except ElementTree.ParseError:
            continue
        for brush in root.findall("brush"):
            brush_type = (brush.get("type") or "").strip().lower()
            if brush_type != "ground":
                continue
            nm = (brush.get("name") or "").strip()
            sid = _brush_primary_server_id(brush)
            if not nm or sid is None:
                continue
            if nm not in name_to_server_id:
                name_to_server_id[nm] = int(sid)

            # Record the outer border set id if present.
            for b in brush.findall("border"):
                align = (b.get("align") or "").strip().lower()
                if align != "outer":
                    continue
                bid = _int_attr(b, "id")
                if bid is None:
                    continue
                border_set_to_server_ids.setdefault(int(bid), []).append(int(sid))
                break

    for xml_path in xml_files:
        try:
            root = _parse_xml_root_tolerant(xml_path)
        except ElementTree.ParseError:
            continue
        for brush in root.findall("brush"):
            brush_type = (brush.get("type") or "").strip().lower()
            if brush_type == "wall":
                exported = _export_wall_brush(brush)
                if exported is not None:
                    yield exported
            elif brush_type == "carpet":
                exported = _export_carpet_brush(brush)
                if exported is not None:
                    yield exported
            elif brush_type == "ground":
                exported = _export_ground_brush(
                    brush,
                    border_sets=border_sets,
                    name_to_server_id=name_to_server_id,
                    border_set_to_server_ids=border_set_to_server_ids,
                )
                if exported is not None:
                    yield exported


def export_to_json(materials_dir: Path, out_path: Path) -> dict:
    brushes: list[dict] = []
    seen: set[int] = set()

    for b in iter_exported_brushes(materials_dir):
        if b.server_id in seen:
            # Keep first occurrence (deterministic order by filename).
            continue
        seen.add(b.server_id)
        brushes.append(
            {
                "name": b.name,
                "server_id": int(b.server_id),
                "type": b.brush_type,
                "borders": {k: int(v) for k, v in b.borders.items()},
                "transitions": list(b.transitions),
            }
        )

    payload = {"brushes": brushes}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export simplified brushes.json from RME materials XML")
    parser.add_argument(
        "--materials-dir",
        default=str(Path("data") / "materials" / "brushs"),
        help="Directory with RME materials brush XML files (default: data/materials/brushs)",
    )
    parser.add_argument(
        "--out",
        default=str(Path("data") / "brushes.json"),
        help="Output JSON path (default: data/brushes.json)",
    )

    args = parser.parse_args(argv)
    materials_dir = Path(os.fspath(args.materials_dir))
    out_path = Path(os.fspath(args.out))

    export_to_json(materials_dir, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
