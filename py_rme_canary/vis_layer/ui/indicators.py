from __future__ import annotations

import os

from PyQt6.QtGui import QPixmap

from py_rme_canary.core.io.xml.safe import safe_etree as ET

from .helpers import ItemProps


class IndicatorService:
    def __init__(self) -> None:
        self._item_props_loaded: bool = False
        self._item_props: dict[int, ItemProps] = {}
        self._icons: dict[str, QPixmap] = {}
        self._scaled_icons: dict[tuple[str, int], QPixmap] = {}

    @property
    def item_props(self) -> dict[int, ItemProps]:
        return self._item_props

    def ensure_loaded(self, *, items_xml_path: str = os.path.join("data", "items", "items.xml")) -> None:
        if self._item_props_loaded:
            return
        self._item_props_loaded = True

        props: dict[int, ItemProps] = {}
        try:
            if not os.path.exists(items_xml_path):
                self._item_props = props
                return

            # Streaming-ish parse: accept both <item> and <items><item> layouts.
            tree = ET.parse(items_xml_path)
            root = tree.getroot()

            for item_el in root.iter():
                if item_el.tag != "item":
                    continue
                sid = item_el.attrib.get("id")
                if sid is None:
                    continue
                try:
                    server_id = int(sid)
                except Exception:
                    continue

                ip = ItemProps()
                # Common flags used by legacy indicators.
                # Note: attributes can be on the item element or nested <attribute key=... value=...>.
                if "pickupable" in item_el.attrib:
                    ip.pickupable = str(item_el.attrib.get("pickupable")).lower() in ("1", "true", "yes")
                if "moveable" in item_el.attrib:
                    ip.moveable = str(item_el.attrib.get("moveable")).lower() in ("1", "true", "yes")
                if "blockprojectile" in item_el.attrib:
                    # best-effort: avoidable tends to be items you want to mark, but legacy uses several flags.
                    pass

                for attr in item_el.findall("attribute"):
                    key = (attr.attrib.get("key") or "").strip().lower()
                    val = (attr.attrib.get("value") or "").strip().lower()
                    truthy = val in ("1", "true", "yes")

                    if key == "pickupable":
                        ip.pickupable = truthy
                    elif key == "moveable":
                        ip.moveable = truthy
                    elif key == "avoidable":
                        ip.avoidable = truthy
                    elif key in ("hook", "haselevation", "wallhook"):
                        # Legacy hook indicator is a bit fuzzy; keep best-effort.
                        ip.hook = truthy

                props[server_id] = ip

        except Exception:
            props = {}

        self._item_props = props

    def icon(self, key: str, size: int) -> QPixmap | None:
        key = (key or "").strip().lower()
        size = int(max(6, min(64, int(size))))

        cache_key = (key, size)
        cached = self._scaled_icons.get(cache_key)
        if cached is not None:
            return cached

        base = self._icons.get(key)
        if base is None:
            # Match existing asset names used by the legacy-ish Qt UI.
            filename_map = {
                "hooks": os.path.join("icons", "toolbar_hooks.png"),
                "pickupables": os.path.join("icons", "toolbar_pickupables.png"),
                "moveables": os.path.join("icons", "toolbar_moveables.png"),
            }
            path = filename_map.get(key)
            if not path or not os.path.exists(path):
                return None
            pm = QPixmap(path)
            if pm.isNull():
                return None
            self._icons[key] = pm
            base = pm

        scaled = base.scaled(size, size)
        self._scaled_icons[cache_key] = scaled
        return scaled
