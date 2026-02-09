"""ClientID <-> ServerID mapping helpers.

This is the central “dictionary” used by the editor to translate between:
- ServerID (logical id, persisted to OTBM)
- ClientID (sprite/render id)
"""

# id_mapper.py
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from .items_otb import ItemsOTB

if TYPE_CHECKING:
    from .items_xml import ItemsXML


class _HasItemMappings(Protocol):
    client_to_server: dict[int, int]
    server_to_client: dict[int, int]


class IdMappingError(KeyError):
    """Raised when a required id mapping is missing."""


@dataclass(frozen=True, slots=True)
class IdMapper:
    """Maps between client IDs and server IDs.

    In the OTBM ecosystem, the persisted item identifier is the ServerID
    (a.k.a. logical id). ClientID is typically used for rendering/sprites.

    This class provides explicit mapping helpers so the IO layer can enforce:
    - Never persist ClientID into OTBM
    - Convert incoming ClientIDs into ServerIDs when necessary
    """

    client_to_server: dict[int, int]
    server_to_client: dict[int, int]

    @classmethod
    def identity(cls) -> IdMapper:
        return cls(client_to_server={}, server_to_client={})

    @classmethod
    def from_items_xml(cls, items: ItemsXML | _HasItemMappings) -> IdMapper:
        return cls(
            client_to_server=dict(items.client_to_server),
            server_to_client=dict(items.server_to_client),
        )

    @classmethod
    def from_items_otb(cls, items: ItemsOTB) -> IdMapper:
        return cls(
            client_to_server=dict(items.client_to_server),
            server_to_client=dict(items.server_to_client),
        )

    def get_server_id(self, client_id: int) -> int | None:
        """Return ServerID for a given ClientID, if known."""

        return self.client_to_server.get(int(client_id))

    def get_client_id(self, server_id: int) -> int | None:
        """Return ClientID for a given ServerID, if known."""

        return self.server_to_client.get(int(server_id))

    def require_server_id(self, client_id: int) -> int:
        """Return ServerID for ClientID or raise a typed error."""

        sid = self.get_server_id(client_id)
        if sid is None:
            raise IdMappingError(f"No server id mapping for client id {client_id}")
        return sid

    def require_client_id(self, server_id: int) -> int:
        """Return ClientID for ServerID or raise a typed error."""

        cid = self.get_client_id(server_id)
        if cid is None:
            raise IdMappingError(f"No client id mapping for server id {server_id}")
        return cid

    def has_server_id(self, server_id: int) -> bool:
        """True if the mapper knows a ClientID for this ServerID."""

        return int(server_id) in self.server_to_client

    def has_client_id(self, client_id: int) -> bool:
        """True if the mapper knows a ServerID for this ClientID."""

        return int(client_id) in self.client_to_server
