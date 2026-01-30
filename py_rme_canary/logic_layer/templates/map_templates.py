"""
Map template definitions for common Tibia client versions.

This module provides predefined map templates that users can select
when creating new maps, with appropriate metadata and settings for
each Tibia client version.
"""

from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple


class TibiaVersion(str, Enum):
    """Supported Tibia client versions for map templates."""

    V7_4 = "7.4"
    V7_72 = "7.72"
    V8_6 = "8.6"
    V10_0 = "10.0"
    V10_98 = "10.98"
    V12_0 = "12.0"
    CUSTOM = "custom"


class MapSize(NamedTuple):
    """Map dimensions."""

    width: int
    height: int

    @property
    def name(self) -> str:
        """Human-readable size name."""
        if self.width == 2048 and self.height == 2048:
            return "Small (2048x2048)"
        elif self.width == 4096 and self.height == 4096:
            return "Medium (4096x4096)"
        elif self.width == 8192 and self.height == 8192:
            return "Large (8192x8192)"
        elif self.width == 16384 and self.height == 16384:
            return "Huge (16384x16384)"
        else:
            return f"Custom ({self.width}x{self.height})"


# Common map sizes
MAP_SIZE_SMALL = MapSize(2048, 2048)
MAP_SIZE_MEDIUM = MapSize(4096, 4096)
MAP_SIZE_LARGE = MapSize(8192, 8192)
MAP_SIZE_HUGE = MapSize(16384, 16384)

COMMON_MAP_SIZES = [
    MAP_SIZE_SMALL,
    MAP_SIZE_MEDIUM,
    MAP_SIZE_LARGE,
    MAP_SIZE_HUGE,
]


@dataclass(frozen=True, slots=True)
class MapTemplate:
    """
    Template for creating new maps with predefined settings.

    Attributes:
        name: Display name of template
        description: Description shown to user
        version: Tibia client version
        default_size: Recommended map size
        otbm_version: OTBM format version (1-4 for ServerID, 5-6 for ClientID)
        use_client_ids: Whether to use ClientID format
        default_description: Default map description
        spawn_file_enabled: Whether to create spawn file
        house_file_enabled: Whether to create house file
    """

    name: str
    description: str
    version: TibiaVersion
    default_size: MapSize
    otbm_version: int
    use_client_ids: bool
    default_description: str
    spawn_file_enabled: bool = True
    house_file_enabled: bool = True


# Predefined map templates
TEMPLATE_7_4 = MapTemplate(
    name="Tibia 7.4 (Classic)",
    description="Classic 7.4 map with ServerID format. Compatible with OTServ 0.6.x.",
    version=TibiaVersion.V7_4,
    default_size=MAP_SIZE_MEDIUM,
    otbm_version=2,  # ServerID format
    use_client_ids=False,
    default_description="Classic 7.4 map",
)

TEMPLATE_7_72 = MapTemplate(
    name="Tibia 7.72",
    description="Tibia 7.72 map with ServerID format. Compatible with The Forgotten Server 0.2.x.",
    version=TibiaVersion.V7_72,
    default_size=MAP_SIZE_MEDIUM,
    otbm_version=2,
    use_client_ids=False,
    default_description="Tibia 7.72 map",
)

TEMPLATE_8_6 = MapTemplate(
    name="Tibia 8.6",
    description="Tibia 8.6 map with ServerID format. Popular for mid-era servers.",
    version=TibiaVersion.V8_6,
    default_size=MAP_SIZE_LARGE,
    otbm_version=2,
    use_client_ids=False,
    default_description="Tibia 8.6 map",
)

TEMPLATE_10_0 = MapTemplate(
    name="Tibia 10.0 (Modern ServerID)",
    description="Tibia 10.x map using ServerID format. Compatible with TFS 1.x.",
    version=TibiaVersion.V10_0,
    default_size=MAP_SIZE_LARGE,
    otbm_version=2,
    use_client_ids=False,
    default_description="Tibia 10.x map",
)

TEMPLATE_10_98 = MapTemplate(
    name="Tibia 10.98 (ClientID)",
    description="Tibia 10.98+ map using ClientID format. Requires modern client.",
    version=TibiaVersion.V10_98,
    default_size=MAP_SIZE_LARGE,
    otbm_version=5,  # ClientID format
    use_client_ids=True,
    default_description="Tibia 10.98+ map (ClientID)",
)

TEMPLATE_12_0 = MapTemplate(
    name="Tibia 12.x (ClientID)",
    description="Tibia 12.x map using ClientID format. Latest protocol.",
    version=TibiaVersion.V12_0,
    default_size=MAP_SIZE_HUGE,
    otbm_version=5,
    use_client_ids=True,
    default_description="Tibia 12.x map (ClientID)",
)

TEMPLATE_CUSTOM = MapTemplate(
    name="Custom (Blank)",
    description="Empty map with custom settings. Choose your own version and size.",
    version=TibiaVersion.CUSTOM,
    default_size=MAP_SIZE_MEDIUM,
    otbm_version=2,
    use_client_ids=False,
    default_description="Custom map",
)


# All available templates in display order
ALL_TEMPLATES = [
    TEMPLATE_7_4,
    TEMPLATE_7_72,
    TEMPLATE_8_6,
    TEMPLATE_10_0,
    TEMPLATE_10_98,
    TEMPLATE_12_0,
    TEMPLATE_CUSTOM,
]


def get_template_by_version(version: TibiaVersion) -> MapTemplate:
    """
    Get template for specific Tibia version.

    Args:
        version: Tibia version enum

    Returns:
        MapTemplate for that version

    Raises:
        ValueError: If version not found
    """
    for template in ALL_TEMPLATES:
        if template.version == version:
            return template
    raise ValueError(f"No template found for version {version}")


def get_template_by_name(name: str) -> MapTemplate | None:
    """
    Get template by display name.

    Args:
        name: Template display name

    Returns:
        MapTemplate or None if not found
    """
    for template in ALL_TEMPLATES:
        if template.name == name:
            return template
    return None
