"""Auto-border processing package.

This package provides modular components for auto-border functionality:
- neighbor_mask: Neighbor bitmask computation
- alignment: Border alignment selection
- transitions: Transition border handling
- processor: Main AutoBorderProcessor class
"""

from .alignment import (
    select_border_alignment,
    select_border_alignment_when_present,
    select_border_id_from_definition,
)
from .neighbor_mask import (
    NEIGHBOR_OFFSETS,
    compute_neighbor_mask_for_ground,
    compute_neighbor_mask_for_target_ground,
)
from .processor import (
    AutoBorderProcessor,
    apply_brush_definition_around_positions,
    paint_with_optional_autoborder,
)
from .tile_utils import (
    Placement,
    get_relevant_item_id,
    get_top_item_id,
    replace_top_item,
)

__all__ = [
    # Neighbor mask
    "NEIGHBOR_OFFSETS",
    "compute_neighbor_mask_for_ground",
    "compute_neighbor_mask_for_target_ground",
    # Alignment
    "select_border_alignment",
    "select_border_alignment_when_present",
    "select_border_id_from_definition",
    # Processor
    "AutoBorderProcessor",
    "paint_with_optional_autoborder",
    "apply_brush_definition_around_positions",
    # Tile utils
    "get_top_item_id",
    "get_relevant_item_id",
    "replace_top_item",
    "Placement",
]
