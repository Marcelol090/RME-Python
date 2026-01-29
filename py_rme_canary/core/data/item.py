# item.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ItemAttribute:
    """Raw attribute-map entry (OTBM_ATTR_ATTRIBUTE_MAP).

    Legacy reference: `source/item_attributes.*`.

    We keep `key_bytes` and `raw` as bytes to preserve roundtrip fidelity.
    """

    key_bytes: bytes
    type: int
    raw: bytes

    @property
    def key(self) -> str:
        return self.key_bytes.decode("utf-8", errors="replace")


@dataclass(frozen=True, slots=True)
class Position:
    """Map position used by some item attributes (e.g. teleport destination).

    This mirrors the common OTBM encoding (<HHB) used by RME/OTBM.
    """

    x: int
    y: int
    z: int


@dataclass(frozen=True, slots=True)
class Item:
    """Minimal item model required for strict OTBM I/O.

    C++ reference: `source/item.h`.

    In RME, `Item` is a polymorphic editor object that inherits
    `ItemAttributes`. For the Python port we keep only the persisted data
    needed to load/save OTBM.

    Persisted fields (OTBM):
    - `id`: the item id written to OTBM (ServerID / logical id).
    - `subtype`: C++ uses a single subtype for count/fluids/charges.
    - `count`: explicit stack count (OTBM_ATTR_COUNT, u8) when applicable.
    - `action_id`, `unique_id`, `text`, `description`, `destination`.
    - `items`: container contents (child ITEM nodes in OTBM).

    Visual vs logical IDs:
    - The editor may draw using ClientID but must save using ServerID.
    - `client_id` is optional metadata and is never written to OTBM.
    """

    id: int

    # Optional visual id (ClientID). Not persisted to OTBM.
    client_id: int | None = None

    # If the loader replaced an unknown id with a placeholder, keep the raw id
    # here so the editor can report and help the user repair the map.
    raw_unknown_id: int | None = None

    subtype: int | None = None
    count: int | None = None

    text: str | None = None
    description: str | None = None

    action_id: int | None = None
    unique_id: int | None = None

    destination: Position | None = None

    # Container recursion.
    items: tuple[Item, ...] = ()

    # Optional extended attributes (OTBM_ATTR_ATTRIBUTE_MAP).
    attribute_map: tuple[ItemAttribute, ...] = ()

    # Additional fixed-size OTBM attributes.
    depot_id: int | None = None
    house_door_id: int | None = None

    @property
    def server_id(self) -> int:
        """Return the logical id persisted to OTBM (alias for `id`)."""

        return int(self.id)

    def with_container_items(self, children: tuple[Item, ...]) -> Item:
        return Item(
            id=self.id,
            client_id=self.client_id,
            raw_unknown_id=self.raw_unknown_id,
            subtype=self.subtype,
            count=self.count,
            text=self.text,
            description=self.description,
            action_id=self.action_id,
            unique_id=self.unique_id,
            destination=self.destination,
            items=children,
            attribute_map=self.attribute_map,
            depot_id=self.depot_id,
            house_door_id=self.house_door_id,
        )
