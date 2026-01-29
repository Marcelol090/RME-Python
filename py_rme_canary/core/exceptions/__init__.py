"""Consolidated exceptions for py_rme_canary."""

from .config import (
    ConfigurationError,
    ProjectError,
)
from .io import (
    HousesXmlError,
    ItemsOTBError,
    ItemsXMLError,
    OTBMParseError,
    SpawnXmlError,
    SpriteAppearancesError,
    ZonesXmlError,
)
from .mapping import (
    IdMappingError,
)

__all__ = [
    # IO exceptions
    "OTBMParseError",
    "ItemsOTBError",
    "ItemsXMLError",
    "SpawnXmlError",
    "HousesXmlError",
    "ZonesXmlError",
    "SpriteAppearancesError",
    # Config exceptions
    "ConfigurationError",
    "ProjectError",
    # Mapping exceptions
    "IdMappingError",
]
