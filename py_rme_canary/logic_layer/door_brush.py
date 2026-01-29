"""Door brush implementation for py_rme_canary.

Converts wall items to door variants based on wall alignment.
Mirrors legacy C++ DoorBrush from brush.cpp lines 302-590.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from py_rme_canary.core.data.door import DoorType
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.brush_definitions import BrushDefinition, BrushManager, DoorBrushSpec

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Position


_ORIENTATION_FROM_BORDER_KEY: dict[str, str] = {
    "HORIZONTAL": "HORIZONTAL",
    "VERTICAL": "VERTICAL",
    "END_EAST": "HORIZONTAL",
    "END_WEST": "HORIZONTAL",
    "END_NORTH": "VERTICAL",
    "END_SOUTH": "VERTICAL",
    "T_EAST": "HORIZONTAL",
    "T_WEST": "HORIZONTAL",
    "T_NORTH": "VERTICAL",
    "T_SOUTH": "VERTICAL",
    "EAST": "HORIZONTAL",
    "WEST": "HORIZONTAL",
    "NORTH": "VERTICAL",
    "SOUTH": "VERTICAL",
}


def _orientation_from_border_key(key: str) -> str | None:
    k = str(key or "").strip().upper()
    return _ORIENTATION_FROM_BORDER_KEY.get(k)


def _alignment_from_item_id(brush_def: BrushDefinition, item_id: int) -> str | None:
    iid = int(item_id)
    for key, val in brush_def.borders.items():
        if int(val) == iid:
            orient = _orientation_from_border_key(key)
            if orient:
                return orient
    for tb in brush_def.transition_borders.values():
        for key, val in tb.items():
            if int(val) == iid:
                orient = _orientation_from_border_key(key)
                if orient:
                    return orient
    return None


def _orientation_from_neighbors(game_map: GameMap, pos: Position, brush_def: BrushDefinition) -> str | None:
    x, y, z = int(pos.x), int(pos.y), int(pos.z)

    def has_wall(dx: int, dy: int) -> bool:
        tile = game_map.get_tile(int(x + dx), int(y + dy), int(z))
        if tile is None:
            return False
        return any(brush_def.contains_id(int(it.id)) for it in tile.items)

    north = has_wall(0, -1)
    south = has_wall(0, 1)
    east = has_wall(1, 0)
    west = has_wall(-1, 0)

    if (north or south) and not (east or west):
        return "VERTICAL"
    if (east or west) and not (north or south):
        return "HORIZONTAL"
    return None


def _resolve_alignment(
    *,
    game_map: GameMap,
    pos: Position,
    item: Item,
    brush_def: BrushDefinition,
    door_spec: DoorBrushSpec,
) -> str | None:
    align = door_spec.alignment_for_item(int(item.id))
    if align is not None and align in door_spec.items_by_alignment:
        return str(align)

    align = _alignment_from_item_id(brush_def, int(item.id))
    if align is not None and align in door_spec.items_by_alignment:
        return str(align)

    orient = _orientation_from_neighbors(game_map, pos, brush_def)
    if orient is not None and orient in door_spec.items_by_alignment:
        return str(orient)

    if len(door_spec.items_by_alignment) == 1:
        return next(iter(door_spec.items_by_alignment.keys()))

    return None


def _clone_item_with_id(old_item: Item, new_id: int) -> Item:
    return Item(
        id=int(new_id),
        client_id=old_item.client_id,
        raw_unknown_id=old_item.raw_unknown_id,
        subtype=old_item.subtype,
        count=old_item.count,
        text=old_item.text,
        description=old_item.description,
        action_id=old_item.action_id,
        unique_id=old_item.unique_id,
        destination=old_item.destination,
        items=old_item.items,
        attribute_map=old_item.attribute_map,
        depot_id=old_item.depot_id,
        house_door_id=old_item.house_door_id,
    )


def _find_wall_candidate(
    tile: Tile,
    brush_manager: BrushManager,
) -> tuple[int, Item, BrushDefinition, DoorBrushSpec] | None:
    for idx in range(len(tile.items) - 1, -1, -1):
        item = tile.items[idx]
        brush_def = brush_manager.get_brush_any(int(item.id))
        if brush_def is None or brush_def.door_spec is None:
            continue
        return int(idx), item, brush_def, brush_def.door_spec
    return None


@dataclass(frozen=True, slots=True)
class DoorBrush:
    """Converts walls to doors based on wall alignment.

    DoorBrush requires an existing wall on the tile. It doesn't place
    doors standalone - it transforms a wall item into its door variant.

    The wall must have door definitions in the loaded materials.
    """

    door_type: DoorType

    def get_name(self) -> str:
        """Get human-readable brush name."""
        return f"{self.door_type.get_name()} brush"

    def can_draw(self, game_map: GameMap, pos: Position, *, brush_manager: BrushManager | None = None) -> bool:
        """Check if door can be placed at position."""
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return False

        if brush_manager is None:
            wall_item = self._find_wall_item(tile)
            return bool(wall_item and self._has_door_variant(wall_item))

        candidate = _find_wall_candidate(tile, brush_manager)
        if candidate is None:
            return False
        _, item, brush_def, door_spec = candidate
        align = _resolve_alignment(
            game_map=game_map,
            pos=pos,
            item=item,
            brush_def=brush_def,
            door_spec=door_spec,
        )
        if align is None:
            return False

        entry = door_spec.entry_for_item(int(item.id))
        desired_open = bool(entry.is_open) if entry is not None else False
        if door_spec.choose_item_id(align, self.door_type, is_open=desired_open) is not None:
            return True
        return door_spec.choose_any_item_id(align, self.door_type) is not None

    def draw(
        self,
        game_map: GameMap,
        pos: Position,
        *,
        open_state: bool = False,
        brush_manager: BrushManager | None = None,
    ) -> list[tuple[Position, Tile]]:
        """Draw door at position by converting wall to door.

        Args:
            game_map: Target game map
            pos: Position to place door
            open_state: Initial door state (open or closed)
            brush_manager: Brush manager providing wall door definitions
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return []

        if brush_manager is None:
            wall_item = self._find_wall_item(tile)
            if wall_item is None:
                return []
            door_item_id = self._get_door_variant(wall_item, open_state)
            if door_item_id is None:
                return []
            new_items = []
            for item in tile.items:
                if self._is_wall_item(item):
                    new_items.append(Item(id=door_item_id))
                else:
                    new_items.append(item)
            new_tile = replace(tile, items=new_items, modified=True)
            return [(pos, new_tile)]

        candidate = _find_wall_candidate(tile, brush_manager)
        if candidate is None:
            return []
        idx, item, brush_def, door_spec = candidate

        align = _resolve_alignment(
            game_map=game_map,
            pos=pos,
            item=item,
            brush_def=brush_def,
            door_spec=door_spec,
        )
        if align is None:
            return []

        entry = door_spec.entry_for_item(int(item.id))
        desired_open = bool(entry.is_open) if entry is not None else bool(open_state)

        door_item_id = door_spec.choose_item_id(align, self.door_type, is_open=desired_open)
        if door_item_id is None:
            door_item_id = door_spec.choose_any_item_id(align, self.door_type)
        if door_item_id is None:
            return []

        new_items = list(tile.items)
        new_items[int(idx)] = _clone_item_with_id(item, int(door_item_id))
        new_tile = replace(tile, items=new_items, modified=True)
        return [(pos, new_tile)]

    def _find_wall_item(self, tile: Tile) -> Item | None:
        """Find wall item on tile (fallback heuristic)."""
        for item in tile.items:
            if self._is_wall_item(item):
                return item
        return None

    def _is_wall_item(self, item: Item) -> bool:
        """Check if item is a wall (heuristic fallback)."""
        wall_ranges = [(400, 600), (1200, 1600), (5500, 6500)]
        return any(start <= int(item.id) <= end for start, end in wall_ranges)

    def _has_door_variant(self, wall_item: Item) -> bool:
        """Check if wall has door variants defined (fallback heuristic)."""
        return True

    def _get_door_variant(self, wall_item: Item, open_state: bool) -> int | None:
        """Get door item ID for wall alignment (fallback heuristic)."""
        base_doors = {
            DoorType.NORMAL: 1209,
            DoorType.LOCKED: 1210,
            DoorType.MAGIC: 1211,
            DoorType.QUEST: 1212,
            DoorType.HATCH: 1215,
            DoorType.WINDOW: 1216,
        }
        return base_doors.get(self.door_type)

    @staticmethod
    def switch_door(item: Item, *, door_spec: DoorBrushSpec | None = None) -> Item:
        """Toggle door between open and closed state."""
        if door_spec is not None:
            new_id = door_spec.toggle_item_id(int(item.id))
            if new_id is not None and int(new_id) != int(item.id):
                return _clone_item_with_id(item, int(new_id))

        new_id = int(item.id) + 1 if int(item.id) % 2 == 0 else int(item.id) - 1
        return _clone_item_with_id(item, int(new_id))
