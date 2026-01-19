"""High-level map operations (new module path).

These modules group pure logic operations that can be used by UI/controllers.
They are thin wrappers over existing logic-layer functions for compatibility.
"""

from .remove import remove_items_in_map
from .replace import replace_items_in_map
from .search import find_item_positions, find_waypoints
from .statistics import compute_map_statistics, format_map_statistics_report

__all__ = [
    "compute_map_statistics",
    "find_item_positions",
    "find_waypoints",
    "format_map_statistics_report",
    "remove_items_in_map",
    "replace_items_in_map",
]
