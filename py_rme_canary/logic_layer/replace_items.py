from __future__ import annotations

from dataclasses import dataclass

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile


@dataclass(frozen=True, slots=True)
class ReplaceItemsResult:
    replaced: int
    exceeded_limit: bool


def _replace_item_tree(*, item: Item, from_id: int, to_id: int) -> tuple[Item, int]:
    replaced = 0

    children = item.items
    if children:
        new_children: list[Item] = []
        any_child_changed = False
        for child in children:
            new_child, child_replaced = _replace_item_tree(item=child, from_id=from_id, to_id=to_id)
            replaced += int(child_replaced)
            any_child_changed = any_child_changed or (new_child is not child)
            new_children.append(new_child)
        if any_child_changed:
            item = item.with_container_items(tuple(new_children))

    if int(item.id) == int(from_id):
        replaced += 1
        # Mirrors legacy `transformItem`: change ID but keep persisted attributes.
        item = Item(
            id=int(to_id),
            client_id=item.client_id,
            raw_unknown_id=item.raw_unknown_id,
            subtype=item.subtype,
            count=item.count,
            text=item.text,
            description=item.description,
            action_id=item.action_id,
            unique_id=item.unique_id,
            destination=item.destination,
            items=item.items,
            attribute_map=item.attribute_map,
            depot_id=item.depot_id,
            house_door_id=item.house_door_id,
        )

    return item, replaced


def replace_items_in_tile(*, tile: Tile, from_id: int, to_id: int) -> tuple[Tile, int]:
    replaced = 0

    ground = tile.ground
    if ground is not None:
        new_ground, n = _replace_item_tree(item=ground, from_id=from_id, to_id=to_id)
        replaced += int(n)
        ground = new_ground

    new_items: list[Item] = []
    any_item_changed = False
    for it in tile.items:
        new_it, n = _replace_item_tree(item=it, from_id=from_id, to_id=to_id)
        replaced += int(n)
        any_item_changed = any_item_changed or (new_it is not it)
        new_items.append(new_it)

    if replaced == 0:
        return tile, 0

    # Only allocate a new list if needed.
    items_out = new_items if any_item_changed else list(tile.items)

    return (
        Tile(
            x=int(tile.x),
            y=int(tile.y),
            z=int(tile.z),
            ground=ground,
            items=items_out,
            house_id=tile.house_id,
            map_flags=int(tile.map_flags),
            zones=tile.zones,
            modified=True,
        ),
        replaced,
    )


def replace_items_in_map(
    game_map: GameMap,
    *,
    from_id: int,
    to_id: int,
    limit: int = 500,
    selection_only: bool = False,
    selection_tiles: set[tuple[int, int, int]] | None = None,
) -> tuple[dict[tuple[int, int, int], Tile], ReplaceItemsResult]:
    """Compute replaced tiles for a map.

    Mirrors legacy behavior:
    - Finds items by server id.
    - Includes ground, stack items, and container recursion.
    - Enforces a max replacement limit (legacy: REPLACE_SIZE).

    Returns a dict of changed tiles and a summary.
    """

    if selection_only and not selection_tiles:
        return {}, ReplaceItemsResult(replaced=0, exceeded_limit=False)

    selection_set: set[tuple[int, int, int]] = set(selection_tiles) if selection_tiles is not None else set()

    changed: dict[tuple[int, int, int], Tile] = {}
    replaced_total = 0
    exceeded = False

    for key, tile in game_map.tiles.items():
        if selection_only and key not in selection_set:
            continue

        if replaced_total >= int(limit):
            exceeded = True
            break

        new_tile, replaced = replace_items_in_tile(tile=tile, from_id=from_id, to_id=to_id)
        if replaced <= 0:
            continue

        # Respect the limit (stop before surpassing).
        if replaced_total + int(replaced) > int(limit):
            exceeded = True
            break

        changed[key] = new_tile
        replaced_total += int(replaced)

    return changed, ReplaceItemsResult(replaced=replaced_total, exceeded_limit=exceeded)
