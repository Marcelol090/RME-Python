"""High-level map operations (new module path).

These modules group pure logic operations that can be used by UI/controllers.
They are thin wrappers over existing logic-layer functions for compatibility.
"""

from ..map_format_conversion import analyze_map_format_conversion, apply_map_format_version
from .map_import import ImportMapReport, import_map_with_offset
from .map_operations import (
    BorderizeResult,
    ClearHouseTilesResult,
    ClearModifiedResult,
    RandomizeResult,
    borderize_map,
    borderize_selection,
    clear_invalid_house_tiles,
    clear_modified_tile_state,
    randomize_map,
    randomize_selection,
)
from .remove import remove_items_in_map
from .replace import replace_items_in_map
from .search import find_item_positions, find_waypoints
from .selection_operations import (
    CreatureSearchResult,
    MonsterCountResult,
    RemoveDuplicatesResult,
    SelectionSearchResult,
    count_monsters_in_selection,
    remove_duplicates_in_selection,
    search_items_in_selection,
)
from .statistics import compute_map_statistics, format_map_statistics_report

__all__ = [
    "BorderizeResult",
    "ClearHouseTilesResult",
    "ClearModifiedResult",
    "CreatureSearchResult",
    "ImportMapReport",
    "MonsterCountResult",
    "RandomizeResult",
    "RemoveDuplicatesResult",
    "SelectionSearchResult",
    "analyze_map_format_conversion",
    "apply_map_format_version",
    "borderize_map",
    "borderize_selection",
    "clear_invalid_house_tiles",
    "clear_modified_tile_state",
    "compute_map_statistics",
    "count_monsters_in_selection",
    "find_item_positions",
    "find_waypoints",
    "format_map_statistics_report",
    "import_map_with_offset",
    "randomize_map",
    "randomize_selection",
    "remove_duplicates_in_selection",
    "remove_items_in_map",
    "replace_items_in_map",
    "search_items_in_selection",
]
