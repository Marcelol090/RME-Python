"""Canary/OpenTibia `items.xml` loader.

This module provides a minimal, IO-oriented view of the server item database.
It is used to:
- infer subtype semantics (count vs charges) for OTBM
- map ClientID <-> ServerID when `clientid` is present

It intentionally does not model the full RME `ItemType` surface area.
"""

# items_xml.py
from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path


class ItemsXMLError(ValueError):
    """Raised when `items.xml` cannot be parsed or validated."""


def _parse_bool(value: str) -> bool:
    """Parse common truthy strings used by OpenTibia-style XML."""

    v = (value or "").strip().lower()
    return v in ("1", "true", "yes", "y", "on")


def _parse_int(value: str) -> int | None:
    """Best-effort integer parsing; returns None if invalid."""

    try:
        return int((value or "").strip())
    except Exception:
        return None


@dataclass(frozen=True, slots=True)
class ItemType:
    """Minimal item type metadata from `items.xml`.

    We keep only what is useful for OTBM IO decisions:
    - stackable / fluid container / splash (subtype semantics)
    - write/read capabilities (text / description)
    - clientid mapping (optional)

    Anything else is left in `attributes` for later use.
    """

    server_id: int
    name: str = ""

    client_id: int | None = None

    stackable: bool = False
    fluid_container: bool = False
    splash: bool = False

    can_read_text: bool = False
    can_write_text: bool = False
    max_text_len: int = 0

    attributes: dict[str, str] = field(default_factory=dict)

    @property
    def kind(self) -> str:
        if not self.attributes:
            return ""
        return (self.attributes.get("type") or "").strip().lower()

    def is_ground(self) -> bool:
        # Common in OpenTibia/Canary items.xml: <attribute key="type" value="ground"/>
        # Keep this intentionally conservative to avoid misclassification.
        return self.kind == "ground"


class ItemsXML:
    """Loads and indexes Canary/OpenTibia-style `items.xml` files."""

    def __init__(
        self,
        *,
        items_by_server_id: dict[int, ItemType],
        client_to_server: dict[int, int],
        server_to_client: dict[int, int],
    ):
        self._items_by_server_id = items_by_server_id
        self._client_to_server = client_to_server
        self._server_to_client = server_to_client

    @property
    def items_by_server_id(self) -> dict[int, ItemType]:
        return self._items_by_server_id

    @property
    def client_to_server(self) -> dict[int, int]:
        return self._client_to_server

    @property
    def server_to_client(self) -> dict[int, int]:
        return self._server_to_client

    def get(self, server_id: int) -> ItemType | None:
        return self._items_by_server_id.get(int(server_id))

    def get_server_id(self, client_id: int) -> int | None:
        return self._client_to_server.get(int(client_id))

    def get_client_id(self, server_id: int) -> int | None:
        return self._server_to_client.get(int(server_id))

    @classmethod
    def load(cls, path: str | Path, *, strict_mapping: bool = True) -> ItemsXML:
        p = Path(path)
        try:
            root = ET.parse(str(p)).getroot()
        except FileNotFoundError as e:
            raise ItemsXMLError(f"items.xml not found: {p}") from e
        except ET.ParseError as e:
            raise ItemsXMLError(f"Failed to parse items.xml: {p} ({e})") from e
        except Exception as e:
            raise ItemsXMLError(f"Failed to load items.xml: {p} ({type(e).__name__}: {e})") from e

        return cls.from_root(root, strict_mapping=strict_mapping)

    @classmethod
    def from_string(cls, xml_text: str, *, strict_mapping: bool = True) -> ItemsXML:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            raise ItemsXMLError(f"Failed to parse items.xml from string ({e})") from e
        return cls.from_root(root, strict_mapping=strict_mapping)

    @classmethod
    def from_root(cls, root: ET.Element, *, strict_mapping: bool = True) -> ItemsXML:
        items_by_server_id: dict[int, ItemType] = {}
        client_to_server: dict[int, int] = {}
        server_to_client: dict[int, int] = {}

        for item_node in _iter_item_nodes(root):
            sid = _parse_int(item_node.get("id") or "")
            if sid is None:
                continue

            name = item_node.get("name") or ""
            attrs = _read_attribute_children(item_node)

            # Common OpenTibia / Canary naming patterns
            client_id = _parse_int(attrs.get("clientid", ""))

            stackable = _parse_bool(attrs.get("stackable", "0"))
            fluid_container = _parse_bool(attrs.get("fluidcontainer", "0"))
            splash = _parse_bool(attrs.get("issplash", attrs.get("splash", "0")))

            can_read_text = _parse_bool(attrs.get("canreadtext", attrs.get("canReadText", "0")))
            can_write_text = _parse_bool(attrs.get("canwritetext", attrs.get("canWriteText", "0")))
            max_text_len = _parse_int(attrs.get("maxtextlen", attrs.get("maxTextLen", "0"))) or 0

            it = ItemType(
                server_id=int(sid),
                name=name,
                client_id=client_id,
                stackable=stackable,
                fluid_container=fluid_container,
                splash=splash,
                can_read_text=can_read_text,
                can_write_text=can_write_text,
                max_text_len=int(max_text_len),
                attributes=dict(attrs),
            )

            items_by_server_id[it.server_id] = it

            if it.client_id is not None:
                prev = client_to_server.get(it.client_id)
                if prev is not None and prev != it.server_id and strict_mapping:
                    raise ItemsXMLError(
                        f"Duplicate clientid {it.client_id}: {prev} vs {it.server_id} (name={it.name!r})"
                    )
                client_to_server[it.client_id] = it.server_id

                prev2 = server_to_client.get(it.server_id)
                if prev2 is not None and prev2 != it.client_id and strict_mapping:
                    raise ItemsXMLError(
                        f"Duplicate server_id {it.server_id} clientid: {prev2} vs {it.client_id} (name={it.name!r})"
                    )
                server_to_client[it.server_id] = it.client_id

        return cls(
            items_by_server_id=items_by_server_id,
            client_to_server=client_to_server,
            server_to_client=server_to_client,
        )


def _iter_item_nodes(root: ET.Element) -> Iterable[ET.Element]:
    # Common layouts:
    # - <items><item .../></items>
    # - <item .../> (rare)
    if root.tag.lower() == "item":
        yield root
        return

    for node in root.iter():
        if node.tag.lower() == "item":
            yield node


def _read_attribute_children(item_node: ET.Element) -> dict[str, str]:
    attrs: dict[str, str] = {}

    # Some formats place data directly as item attributes; keep them too.
    for k, v in item_node.attrib.items():
        if k.lower() in ("id", "name"):
            continue
        attrs[k] = v

    # OpenTibia-style: <attribute key="..." value="..."/>
    for child in item_node:
        if child.tag.lower() != "attribute":
            continue
        key = child.get("key") or child.get("name") or ""
        val = child.get("value") or ""
        if key:
            attrs[key] = val

    return attrs
