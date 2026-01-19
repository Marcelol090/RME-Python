"""Door pairing helper (MVP).

Legacy RME has a DoorBrush that can switch doors (open <-> closed) based on
brush metadata and wall alignment.

In the Python port we don't yet have full DoorBrush parity. This module
implements a best-effort, Qt-free mapping from a server-side `items.xml` into
open/closed pairs so the UI can provide an undoable "Switch Door" tool.

Heuristic:
- Treat items with `<attribute key="type" value="door"/>` as doors.
- Treat doors with blockProjectile=1 (or name contains "closed") as closed.
- Treat doors with name containing "open" as open.
- Pair each encountered open door with the most recent unmatched closed door.

This reliably pairs many canonical sequences like:
  locked-closed, closed, open
so the open variant pairs with the plain closed door.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def load_door_pairs(items_xml_path: str | Path) -> dict[int, int]:
    """Return a mapping server_id -> paired_server_id for door toggling."""

    p = Path(items_xml_path)
    pairs: dict[int, int] = {}
    pending_closed: list[int] = []

    if not p.exists():
        return pairs

    # Use iterparse to preserve encounter order and avoid keeping the whole tree.
    try:
        for _event, elem in ET.iterparse(str(p), events=("end",)):
            if (elem.tag or "").lower() != "item":
                continue

            sid = elem.attrib.get("id")
            if not sid:
                elem.clear()
                continue

            try:
                server_id = int(sid)
            except Exception:
                elem.clear()
                continue

            # Read attributes from both the <item> node and nested <attribute> children.
            attrs: dict[str, str] = {}
            for k, v in (elem.attrib or {}).items():
                if k.lower() in ("id", "name"):
                    continue
                attrs[str(k)] = str(v)
            for child in list(elem):
                if (child.tag or "").lower() != "attribute":
                    continue
                key = (child.attrib.get("key") or child.attrib.get("name") or "").strip()
                val = (child.attrib.get("value") or "").strip()
                if key:
                    attrs[key] = val

            kind = (attrs.get("type") or "").strip().lower()
            if kind != "door":
                elem.clear()
                continue

            name = (elem.attrib.get("name") or "").strip().lower()
            block_projectile = (attrs.get("blockProjectile") or attrs.get("blockprojectile") or "").strip().lower()
            is_blocking = block_projectile in ("1", "true", "yes", "y", "on")

            is_open = ("open" in name) and (not is_blocking)
            is_closed = is_blocking or ("closed" in name)

            if is_closed and not is_open:
                pending_closed.append(int(server_id))
            elif is_open and pending_closed:
                closed_id = int(pending_closed.pop())
                pairs[closed_id] = int(server_id)
                pairs[int(server_id)] = closed_id

            # Keep memory low.
            elem.clear()

    except ET.ParseError:
        return {}
    except Exception:
        return {}

    return pairs
