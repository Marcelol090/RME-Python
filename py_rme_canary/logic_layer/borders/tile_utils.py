"""Tile utility functions for auto-border processing.

Provides helpers for reading and modifying tile item contents.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Literal

from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile

Placement = Literal["border_item", "ground"]


def get_top_item_id(tile: Tile | None) -> int | None:
    """Get the ID of the topmost item on a tile.

    Args:
        tile: The tile to inspect.

    Returns:
        Item ID or None if tile is empty.
    """
    if tile is None:
        return None

    if tile.items:
        return int(tile.items[-1].id)
    if tile.ground is not None:
        return int(tile.ground.id)
    return None


def get_relevant_item_id(tile: Tile | None, *, brush_type: str) -> int | None:
    """Return the item id used for connectivity checks.

    - walls: use top-most item id
    - terrain/ground: use ground id (borders are additional items)

    Args:
        tile: The tile to inspect.
        brush_type: Type of brush ("terrain", "ground", "wall", etc.)

    Returns:
        Item ID or None.
    """
    brush_type = str(brush_type)
    if tile is None:
        return None
    if brush_type in ("terrain", "ground"):
        if tile.ground is None:
            return None
        return int(tile.ground.id)
    return get_top_item_id(tile)


def replace_top_item(tile: Tile, *, new_server_id: int, brush_type: str) -> Tile:
    """Replace the top item on a tile with a new item.

    Args:
        tile: The tile to modify.
        new_server_id: Server ID of the new item.
        brush_type: Type of brush determining placement behavior.

    Returns:
        Modified tile.
    """
    new_server_id = int(new_server_id)
    brush_type = str(brush_type)

    if brush_type in ("eraser", "erase"):
        # Remove the top-most element.
        if tile.items:
            new_items = list(tile.items)
            new_items.pop()
            return replace(tile, items=new_items)
        return replace(tile, ground=None)

    if brush_type in ("ground", "terrain"):
        return replace(tile, ground=Item(id=new_server_id))

    # Default to "item" placement (walls/carpets/etc.)
    new_items = list(tile.items)
    if new_items:
        new_items[-1] = Item(id=new_server_id)
    else:
        new_items.append(Item(id=new_server_id))
    return replace(tile, items=new_items)


def remove_border_items(tile: Tile, border_ids: set[int]) -> list[Item]:
    """Remove items matching border IDs from tile items list.

    Args:
        tile: The tile to process.
        border_ids: Set of item IDs to remove.

    Returns:
        New items list with border items removed.
    """
    return [it for it in tile.items if int(it.id) not in border_ids]
