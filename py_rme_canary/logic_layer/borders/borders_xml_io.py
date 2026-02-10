"""Legacy borders.xml import / export.

Provides round-trip IO between the RME legacy ``borders.xml`` format::

    <materials>
      <border id="58">
        <borderitem edge="n"   item="1100"/>
        <borderitem edge="w"   item="1103"/>
        ...
      </border>
    </materials>

...and the Python ``BrushManager`` border-override system.

Edge keys in legacy XML:
    n, e, s, w           — cardinal directions
    cnw, cne, cse, csw   — convex corners
    dnw, dne, dse, dsw   — diagonal (inner/concave) corners

Mapped to our ``BrushDefinition.borders`` keys:
    NORTH, EAST, SOUTH, WEST, CORNER_NW, CORNER_NE, CORNER_SE, CORNER_SW,
    INNER_NW, INNER_NE, INNER_SE, INNER_SW

Layer: logic_layer (no PyQt6 imports)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from py_rme_canary.core.io.xml.safe import safe_etree as ET

log = logging.getLogger(__name__)

# ── Edge-key mapping ────────────────────────────────────────────────────────

LEGACY_EDGE_TO_KEY: dict[str, str] = {
    "n": "NORTH",
    "e": "EAST",
    "s": "SOUTH",
    "w": "WEST",
    "cnw": "CORNER_NW",
    "cne": "CORNER_NE",
    "cse": "CORNER_SE",
    "csw": "CORNER_SW",
    "dnw": "INNER_NW",
    "dne": "INNER_NE",
    "dse": "INNER_SE",
    "dsw": "INNER_SW",
}

KEY_TO_LEGACY_EDGE: dict[str, str] = {v: k for k, v in LEGACY_EDGE_TO_KEY.items()}


# ── Data structures ─────────────────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class LegacyBorderDef:
    """One ``<border>`` element from the legacy XML."""

    border_id: int
    group: int | None
    items: dict[str, int]  # key (e.g. "NORTH") -> server item id


# ── Import ──────────────────────────────────────────────────────────────────

def parse_borders_xml(path: str | Path) -> list[LegacyBorderDef]:
    """Parse a legacy ``borders.xml`` file and return structured definitions.

    Handles both the top-level ``<materials><include .../>`` wrapper and the
    actual ``<materials><border ...>`` payload.  When ``<include file="..."/>``
    elements are found the referenced files are resolved relative to the parent
    directory and parsed recursively.
    """

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"borders.xml not found: {path}")

    tree = ET.parse(str(path))
    root = tree.getroot()
    return _parse_root(root, base_dir=path.parent)


def _parse_root(root: Any, *, base_dir: Path) -> list[LegacyBorderDef]:
    results: list[LegacyBorderDef] = []

    # Process <include file="..."/> elements
    for inc in root.findall("include"):
        _process_include(inc, base_dir, results)

    # Process <border> elements directly
    for border_el in root.findall("border"):
        bdef = _parse_single_border(border_el)
        if bdef is not None:
            results.append(bdef)

    return results


def _process_include(inc: Any, base_dir: Path, results: list[LegacyBorderDef]) -> None:
    """Parse a single <include file="..."/> element."""
    fn = (inc.get("file") or "").strip()
    if not fn:
        return
    inc_path = base_dir / fn
    if not inc_path.exists():
        log.warning("borders.xml include not found: %s", inc_path)
        return
    try:
        sub_tree = ET.parse(str(inc_path))
        results.extend(_parse_root(sub_tree.getroot(), base_dir=inc_path.parent))
    except Exception as exc:
        log.warning("Failed to parse included borders file %s: %s", inc_path, exc)


def _parse_single_border(border_el: Any) -> LegacyBorderDef | None:
    """Parse a single <border> element into a LegacyBorderDef."""
    raw_id = border_el.get("id")
    if raw_id is None:
        return None
    try:
        border_id = int(raw_id)
    except (TypeError, ValueError):
        return None

    group = _parse_optional_int(border_el.get("group"))
    items = _parse_border_items(border_el, border_id)
    if not items:
        return None
    return LegacyBorderDef(border_id=border_id, group=group, items=items)


def _parse_optional_int(raw: str | None) -> int | None:
    """Parse an optional integer attribute, returning None on failure."""
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _parse_border_items(border_el: Any, border_id: int) -> dict[str, int]:
    """Parse all <borderitem> children of a <border> element."""
    items: dict[str, int] = {}
    for item_el in border_el.findall("borderitem"):
        edge = (item_el.get("edge") or "").strip().lower()
        raw_item = item_el.get("item")
        if not edge or raw_item is None:
            continue
        key = LEGACY_EDGE_TO_KEY.get(edge)
        if key is None:
            log.debug("Unknown border edge '%s' in border id=%d", edge, border_id)
            continue
        try:
            items[key] = int(raw_item)
        except (TypeError, ValueError):
            continue
    return items


def import_borders_into_manager(
    manager: Any,
    borders: list[LegacyBorderDef],
    *,
    border_id_to_server_id: dict[int, int] | None = None,
) -> int:
    """Apply parsed ``LegacyBorderDef`` entries to a ``BrushManager``.

    Parameters
    ----------
    manager:
        ``BrushManager`` instance (or compatible duck-type).
    borders:
        Parsed border definitions from ``parse_borders_xml``.
    border_id_to_server_id:
        Optional mapping from legacy ``border id`` to brush ``server_id``.
        When ``None`` the border_id is assumed to be the brush server_id.

    Returns
    -------
    int
        Number of brushes that were actually changed.
    """

    changed = 0
    for bdef in borders:
        server_id = bdef.border_id
        if border_id_to_server_id is not None:
            mapped = border_id_to_server_id.get(bdef.border_id)
            if mapped is not None:
                server_id = mapped

        for key, item_id in bdef.items.items():
            setter = getattr(manager, "set_border_override", None)
            if callable(setter):
                if setter(int(server_id), str(key), int(item_id)):
                    changed += 1

    return changed


# ── Export ──────────────────────────────────────────────────────────────────

def export_borders_xml(
    manager: Any,
    path: str | Path,
    *,
    server_id_to_border_id: dict[int, int] | None = None,
) -> int:
    """Export current border definitions from a ``BrushManager`` to legacy XML.

    Only brushes with at least one border entry are exported.

    Parameters
    ----------
    manager:
        ``BrushManager`` instance.
    path:
        Destination file path (will be overwritten).
    server_id_to_border_id:
        Optional reverse mapping from brush server_id to legacy border id.
        When ``None`` the server_id is used as the border id.

    Returns
    -------
    int
        Number of ``<border>`` elements written.
    """

    path = Path(path)
    root = ET.Element("materials")

    brushes = _collect_brushes(manager)

    count = 0
    for sid in sorted(brushes.keys()):
        brush = brushes[sid]
        borders = getattr(brush, "borders", {})
        if not borders:
            continue

        border_id = sid
        if server_id_to_border_id is not None:
            border_id = server_id_to_border_id.get(sid, sid)

        border_el = _build_border_element(root, border_id, brush, borders)
        if border_el is not None:
            count += 1

    path.parent.mkdir(parents=True, exist_ok=True)

    tree = ET.ElementTree(root)
    _indent_xml(root)
    tree.write(str(path), encoding="utf-8", xml_declaration=True)
    return count


def _collect_brushes(manager: Any) -> dict[int, Any]:
    """Extract the brush dict from a BrushManager."""
    raw = getattr(manager, "_brushes", None)
    if isinstance(raw, dict):
        return raw
    brushes: dict[int, Any] = {}
    if callable(getattr(manager, "all_brushes", None)):
        for b in manager.all_brushes():
            brushes[int(b.server_id)] = b
    return brushes


# Standard border keys in canonical export order.
_STANDARD_KEYS = (
    "NORTH", "EAST", "SOUTH", "WEST",
    "CORNER_NW", "CORNER_NE", "CORNER_SE", "CORNER_SW",
    "INNER_NW", "INNER_NE", "INNER_SE", "INNER_SW",
)


def _build_border_element(
    root: Any, border_id: int, brush: Any, borders: dict[str, int]
) -> Any:
    """Build a single <border> XML element."""
    border_el = ET.SubElement(root, "border")
    border_el.set("id", str(int(border_id)))

    group = getattr(brush, "border_group", None)
    if group is not None:
        border_el.set("group", str(int(group)))

    has_items = False
    for key in _STANDARD_KEYS:
        item_id = borders.get(key)
        if item_id is None:
            continue
        edge = KEY_TO_LEGACY_EDGE.get(key)
        if edge is None:
            continue
        _add_borderitem(border_el, edge, item_id)
        has_items = True

    # Also export any non-standard keys
    standard = set(KEY_TO_LEGACY_EDGE.keys())
    for key, item_id in sorted(borders.items()):
        if key in standard:
            continue
        edge_val = key.lower()
        _add_borderitem(border_el, edge_val, item_id)
        has_items = True

    return border_el if has_items else None


def _add_borderitem(parent: Any, edge: str, item_id: int) -> None:
    """Add a <borderitem> child element."""
    item_el = ET.SubElement(parent, "borderitem")
    item_el.set("edge", edge)
    item_el.set("item", str(int(item_id)))


def _indent_xml(elem: Any, level: int = 0) -> None:
    """Add pretty-print indentation to an ElementTree in-place."""
    indent = "\n" + "\t" * level
    child_indent = "\n" + "\t" * (level + 1)

    if len(elem):
        elem.text = elem.text if (elem.text and elem.text.strip()) else child_indent
        for i, child in enumerate(elem):
            _indent_xml(child, level + 1)
            is_last = i == len(elem) - 1
            child.tail = indent if is_last else child_indent
    if level:
        elem.tail = elem.tail if (elem.tail and elem.tail.strip()) else indent
