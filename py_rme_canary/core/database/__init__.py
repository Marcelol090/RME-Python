"""Item database + ID mapping.

Phase 2 provides:
- Parsing of Canary/OpenTibia-style `items.xml`
- Mapping between client-facing IDs and OTBM/server IDs
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .id_mapper import IdMapper
    from .items_otb import ItemsOTB
    from .items_xml import ItemsXML, ItemType

__all__ = ["IdMapper", "ItemType", "ItemsOTB", "ItemsXML"]


def __getattr__(name: str) -> Any:
    if name == "IdMapper":
        from .id_mapper import IdMapper

        return IdMapper
    if name == "ItemsOTB":
        from .items_otb import ItemsOTB

        return ItemsOTB
    if name == "ItemsXML":
        from .items_xml import ItemsXML

        return ItemsXML
    if name == "ItemType":
        from .items_xml import ItemType

        return ItemType
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
