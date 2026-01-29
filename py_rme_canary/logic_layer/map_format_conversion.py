from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.database.id_mapper import IdMapper


@dataclass(frozen=True, slots=True)
class MapFormatConversionReport:
    current_version: int
    target_version: int
    total_items: int
    placeholder_items: int
    missing_mappings: tuple[int, ...]
    id_mapper_missing: bool

    @property
    def ok(self) -> bool:
        if int(self.target_version) >= 5:
            return not self.id_mapper_missing and not self.missing_mappings and self.placeholder_items == 0
        return True


def analyze_map_format_conversion(
    game_map: GameMap,
    *,
    target_version: int,
    id_mapper: IdMapper | None,
) -> MapFormatConversionReport:
    target = int(target_version)
    missing_ids: set[int] = set()
    total_items = 0
    placeholders = 0

    if target >= 5 and id_mapper is None:
        return MapFormatConversionReport(
            current_version=int(game_map.header.otbm_version),
            target_version=target,
            total_items=0,
            placeholder_items=0,
            missing_mappings=(),
            id_mapper_missing=True,
        )

    for item in _iter_items_in_map(game_map):
        total_items += 1
        if int(item.id) <= 0:
            placeholders += 1
            continue
        if target >= 5:
            mapped = id_mapper.get_client_id(int(item.id)) if id_mapper is not None else None
            if mapped is None:
                missing_ids.add(int(item.id))

    return MapFormatConversionReport(
        current_version=int(game_map.header.otbm_version),
        target_version=target,
        total_items=int(total_items),
        placeholder_items=int(placeholders),
        missing_mappings=tuple(sorted(missing_ids)),
        id_mapper_missing=False,
    )


def apply_map_format_version(game_map: GameMap, *, target_version: int) -> None:
    """Update MapHeader otbm_version to the target value."""
    game_map.header = replace(game_map.header, otbm_version=int(target_version))


def _iter_items_in_map(game_map: GameMap) -> Iterable[Item]:
    for tile in game_map.iter_tiles():
        ground = getattr(tile, "ground", None)
        if ground is not None:
            yield from _iter_item_tree(ground)
        items = getattr(tile, "items", None) or []
        for top in items:
            yield from _iter_item_tree(top)


def _iter_item_tree(root: Item) -> Iterable[Item]:
    stack: list[Item] = [root]
    while stack:
        it = stack.pop()
        yield it
        children = getattr(it, "items", None) or ()
        for child in reversed(tuple(children)):
            stack.append(child)
