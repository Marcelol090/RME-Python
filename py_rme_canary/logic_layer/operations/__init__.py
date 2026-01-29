"""High-level map operations (new module path).

These modules group pure logic operations that can be used by UI/controllers.
They are thin wrappers over existing logic-layer functions for compatibility.
"""

from .remove import remove_items_in_map
from .replace import replace_items_in_map
from .search import find_item_positions, find_waypoints
from .selection_operations import (
    count_monsters_in_selection,
    remove_duplicates_in_selection,
    search_items_in_selection,
    MonsterCountResult,
    RemoveDuplicatesResult,
    SelectionSearchResult,
    CreatureSearchResult,
)
from .statistics import compute_map_statistics, format_map_statistics_report
from .map_import import import_map_with_offset, ImportMapReport
from ..map_format_conversion import analyze_map_format_conversion, apply_map_format_version

__all__ = [
    "analyze_map_format_conversion",
    "apply_map_format_version",
    "compute_map_statistics",
    "count_monsters_in_selection",
    "find_item_positions",
    "find_waypoints",
    "format_map_statistics_report",
    "import_map_with_offset",
    "ImportMapReport",
    "remove_duplicates_in_selection",
    "remove_items_in_map",
    "replace_items_in_map",
    "search_items_in_selection",
    "CreatureSearchResult",
    "MonsterCountResult",
    "RemoveDuplicatesResult",
    "SelectionSearchResult",
]
