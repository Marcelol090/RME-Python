"""Templates package for map creation presets."""

from .map_templates import (
    ALL_TEMPLATES,
    COMMON_MAP_SIZES,
    # Individual templates
    TEMPLATE_7_4,
    TEMPLATE_7_72,
    TEMPLATE_8_6,
    TEMPLATE_10_0,
    TEMPLATE_10_98,
    TEMPLATE_12_0,
    TEMPLATE_CUSTOM,
    MapSize,
    MapTemplate,
    TibiaVersion,
    get_template_by_name,
    get_template_by_version,
)

__all__ = [
    "MapTemplate",
    "TibiaVersion",
    "MapSize",
    "ALL_TEMPLATES",
    "COMMON_MAP_SIZES",
    "get_template_by_version",
    "get_template_by_name",
    "TEMPLATE_7_4",
    "TEMPLATE_7_72",
    "TEMPLATE_8_6",
    "TEMPLATE_10_0",
    "TEMPLATE_10_98",
    "TEMPLATE_12_0",
    "TEMPLATE_CUSTOM",
]
