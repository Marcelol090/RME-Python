"""Main auto-border processor class.

Provides the AutoBorderProcessor that calculates neighbor bitmasks
and applies brush rules for auto-connecting tiles.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from typing import Any

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile

from ..brush_definitions import BrushDefinition

from .alignment import (
    select_border_alignment_when_present,
    select_border_id_from_definition,
    transition_alignment_weight,
)
from .neighbor_mask import (
    NEIGHBOR_OFFSETS,
    compute_neighbor_mask_for_ground,
    compute_neighbor_mask_for_target_ground,
)
from .tile_utils import (
    Placement,
    get_relevant_item_id,
    replace_top_item,
)


class AutoBorderProcessor:
    """Calculates 4-direction neighbor bitmasks and applies brush rules.

    This is the structured "bitmasking" approach used commonly for walls and
    similar auto-connecting brushes.
    """

    # 4-direction mask constants
    MASK_NORTH = 1
    MASK_EAST = 2
    MASK_SOUTH = 4
    MASK_WEST = 8

    # Mask to alignment key mapping
    MASK_TO_KEY: dict[int, str] = {
        0: "SOLITARY",
        1: "END_SOUTH",
        2: "END_WEST",
        3: "CORNER_NE",
        4: "END_NORTH",
        5: "VERTICAL",
        6: "CORNER_SE",
        7: "T_WEST",
        8: "END_EAST",
        9: "CORNER_NW",
        10: "HORIZONTAL",
        11: "T_SOUTH",
        12: "CORNER_SW",
        13: "T_EAST",
        14: "T_NORTH",
        15: "CROSS",
    }

    # Some brush definitions (notably `carpet` in data/brushes.json) use
    # direction keys (NORTH/EAST/SOUTH/WEST) instead of END_*.
    # Map END_* -> direction key that indicates the neighbor that exists.
    _END_TO_DIR: dict[str, str] = {
        "END_SOUTH": "NORTH",
        "END_WEST": "EAST",
        "END_NORTH": "SOUTH",
        "END_EAST": "WEST",
    }

    def _candidate_border_keys(self, key_name: str) -> list[str]:
        """Return an ordered list of border keys to try.

        Goal: be compatible with multiple brush JSON conventions.
        - Legacy wall logic uses END_*/T_*/CROSS/HORIZONTAL/VERTICAL.
        - Many carpet/table-like definitions use NORTH/EAST/SOUTH/WEST + CORNER_* + SOLITARY.
        """

        key_name = str(key_name)
        out: list[str] = []

        def add(k: str) -> None:
            k = str(k)
            if k and k not in out:
                out.append(k)

        add(key_name)

        # Alias END_* to direction keys when available.
        if key_name in self._END_TO_DIR:
            add(self._END_TO_DIR[key_name])

        # CROSS/T shapes: try more generic keys; for direction-only brushes
        # this degrades gracefully into any existing direction/corner key.
        if key_name == "CROSS":
            for k in ("T_NORTH", "T_EAST", "T_SOUTH", "T_WEST"):
                add(k)
            add("HORIZONTAL")
            add("VERTICAL")
            for k in ("NORTH", "EAST", "SOUTH", "WEST"):
                add(k)

        elif key_name.startswith("T_"):
            # Missing arm direction = key_name[2:]. For direction-only sets, pick a stable fallback.
            add("HORIZONTAL")
            add("VERTICAL")
            for k in ("NORTH", "EAST", "SOUTH", "WEST"):
                add(k)

        elif key_name.startswith("CORNER_"):
            add("HORIZONTAL")
            add("VERTICAL")
            suffix = key_name.split("_", 1)[-1]
            if suffix == "NE":
                add("NORTH")
                add("EAST")
            elif suffix == "NW":
                add("NORTH")
                add("WEST")
            elif suffix == "SE":
                add("SOUTH")
                add("EAST")
            elif suffix == "SW":
                add("SOUTH")
                add("WEST")

        elif key_name.startswith("END_"):
            # Prefer the axis-aligned generic keys too.
            if key_name in ("END_NORTH", "END_SOUTH"):
                add("VERTICAL")
            elif key_name in ("END_EAST", "END_WEST"):
                add("HORIZONTAL")

        add("SOLITARY")
        return out

    def __init__(self, game_map: GameMap, brush_manager: Any, *, change_recorder: Any | None = None) -> None:
        self.game_map = game_map
        self.brush_mgr = brush_manager
        self._change_recorder = change_recorder

    def _set_tile(self, tile: Tile) -> None:
        """Set tile and record change if recorder is present."""
        old = self.game_map.get_tile(int(tile.x), int(tile.y), int(tile.z))
        if old == tile:
            return

        tile = replace(tile, modified=True)
        old = self.game_map.get_tile(int(tile.x), int(tile.y), int(tile.z))
        if old == tile:
            return
        if self._change_recorder is not None:
            self._change_recorder.record_tile_change((int(tile.x), int(tile.y), int(tile.z)), old, tile)
        self.game_map.set_tile(tile)

    def _tile_has_family_item(self, tile: Tile | None, brush_def: BrushDefinition) -> bool:
        if tile is None:
            return False
        fam = brush_def.family_ids
        if tile.ground is not None and int(tile.ground.id) in fam:
            return True
        return any(int(it.id) in fam for it in tile.items)

    def _replace_family_item(self, tile: Tile, *, brush_def: BrushDefinition, new_server_id: int) -> Tile:
        """Replace any items belonging to brush family without clobbering unrelated stack.

        Key requirement for carpets: painting/borderizing must not overwrite the top-most item
        (carpets are floor decorations and should coexist with items above them).
        """

        new_server_id = int(new_server_id)
        fam = {int(x) for x in brush_def.family_ids}

        # Only touches items (not ground) for wall-like families.
        kept = [it for it in tile.items if int(it.id) not in fam]

        if str(brush_def.brush_type).lower() == "carpet":
            # Place below other items (so other items render above the carpet).
            kept.insert(0, Item(id=int(new_server_id)))
        else:
            # Default wall-like: place on top.
            kept.append(Item(id=int(new_server_id)))

        if kept == list(tile.items):
            return tile
        return replace(tile, items=kept)

    def update_positions(self, positions: Iterable[tuple[int, int, int]], brush_id: int) -> None:
        """Batch update many positions.

        Designed for editor "stroke" workflows: place base tiles during mouse-move,
        then run auto-border once on mouse-up for all dirty tiles and neighbors.
        """
        brush_def = self.brush_mgr.get_brush(int(brush_id))
        if brush_def is None:
            return

        brush_type_norm = str(brush_def.brush_type).strip().lower()

        if brush_type_norm in ("wall", "carpet", "table"):
            expanded_wall: set[tuple[int, int, int]] = set()
            for x, y, z in positions:
                x, y, z = int(x), int(y), int(z)
                expanded_wall.add((x, y, z))
                expanded_wall.add((x, y - 1, z))
                expanded_wall.add((x + 1, y, z))
                expanded_wall.add((x, y + 1, z))
                expanded_wall.add((x - 1, y, z))
            for px, py, pz in sorted(expanded_wall):
                self._process_wall_logic(px, py, pz, brush_def)
            return

        elif brush_type_norm in ("ground", "terrain"):
            expanded_neighbors: set[tuple[int, int, int]] = set()
            for x, y, z in positions:
                x, y, z = int(x), int(y), int(z)
                expanded_neighbors.add((x, y, z))
                for dx, dy in NEIGHBOR_OFFSETS:
                    expanded_neighbors.add((x + dx, y + dy, z))
            for px, py, pz in sorted(expanded_neighbors):
                if brush_type_norm == "ground":
                    self._process_ground_border_logic(px, py, pz, brush_def)
                else:
                    self._process_terrain_logic(px, py, pz, brush_def)
            return

        # Fallback: treat as wall-like.
        for px, py, pz in positions:
            self._process_wall_logic(int(px), int(py), int(pz), brush_def)

    def update_tile(self, x: int, y: int, z: int, brush_id: int) -> None:
        """Update tile and local neighborhood based on brush type."""
        brush_def = self.brush_mgr.get_brush(int(brush_id))
        if brush_def is None:
            return

        brush_type_norm = str(brush_def.brush_type).strip().lower()

        if brush_type_norm in ("wall", "carpet", "table"):
            positions = (
                (int(x), int(y), int(z)),
                (int(x), int(y - 1), int(z)),
                (int(x + 1), int(y), int(z)),
                (int(x), int(y + 1), int(z)),
                (int(x - 1), int(y), int(z)),
            )
            for px, py, pz in positions:
                self._process_wall_logic(px, py, pz, brush_def)
            return

        if brush_type_norm == "ground":
            expanded_ground: set[tuple[int, int, int]] = {(int(x), int(y), int(z))}
            for dx, dy in NEIGHBOR_OFFSETS:
                expanded_ground.add((int(x + dx), int(y + dy), int(z)))
            for px, py, pz in sorted(expanded_ground):
                self._process_ground_border_logic(px, py, pz, brush_def)
            return

        elif brush_type_norm == "terrain":
            expanded_terrain: set[tuple[int, int, int]] = {(int(x), int(y), int(z))}
            for dx, dy in NEIGHBOR_OFFSETS:
                expanded_terrain.add((int(x + dx), int(y + dy), int(z)))
            for px, py, pz in sorted(expanded_terrain):
                self._process_terrain_logic(px, py, pz, brush_def)
            return

        # Fallback: treat as wall-like.
        self._process_wall_logic(int(x), int(y), int(z), brush_def)

    # Back-compat: older call site name.
    def update_tile_and_neighbors(self, x: int, y: int, z: int, brush_server_id: int) -> None:
        self.update_tile(int(x), int(y), int(z), int(brush_server_id))

    def _process_wall_logic(self, x: int, y: int, z: int, brush_def: BrushDefinition) -> None:
        """Process wall auto-connect logic."""
        tile = self.game_map.get_tile(int(x), int(y), int(z))
        if tile is None:
            return

        # Family-aware: carpets may not be the top-most item.
        if not self._tile_has_family_item(tile, brush_def):
            return

        mask_value = 0
        if self._check_neighbor(int(x), int(y - 1), int(z), brush_def):
            mask_value |= self.MASK_NORTH
        if self._check_neighbor(int(x + 1), int(y), int(z), brush_def):
            mask_value |= self.MASK_EAST
        if self._check_neighbor(int(x), int(y + 1), int(z), brush_def):
            mask_value |= self.MASK_SOUTH
        if self._check_neighbor(int(x - 1), int(y), int(z), brush_def):
            mask_value |= self.MASK_WEST

        key_name = self.MASK_TO_KEY.get(int(mask_value))
        if not key_name:
            return

        candidates = self._candidate_border_keys(key_name)

        new_sprite_id: int | None = None
        for k in candidates:
            v = brush_def.get_border(k)
            if v:
                new_sprite_id = int(v)
                break
        if not new_sprite_id:
            return

        # For non-ground/terrain, use family replacement to avoid clobbering unrelated items.
        if str(brush_def.brush_type).lower() in ("wall", "carpet", "table"):
            new_tile = self._replace_family_item(tile, brush_def=brush_def, new_server_id=int(new_sprite_id))
        else:
            new_tile = replace_top_item(tile, new_server_id=int(new_sprite_id), brush_type=brush_def.brush_type)
        self._set_tile(new_tile)

    def _process_terrain_logic(self, x: int, y: int, z: int, brush_def: BrushDefinition) -> None:
        """Process terrain auto-connect logic."""
        tile = self.game_map.get_tile(int(x), int(y), int(z))
        if tile is None or tile.ground is None:
            return

        current_id = get_relevant_item_id(tile, brush_type="terrain")
        if not brush_def.contains_id(current_id):
            return

        # Neighbor presence for the same terrain
        n = self._check_neighbor(int(x), int(y - 1), int(z), brush_def, brush_type="terrain")
        e = self._check_neighbor(int(x + 1), int(y), int(z), brush_def, brush_type="terrain")
        s = self._check_neighbor(int(x), int(y + 1), int(z), brush_def, brush_type="terrain")
        w = self._check_neighbor(int(x - 1), int(y), int(z), brush_def, brush_type="terrain")
        ne = self._check_neighbor(int(x + 1), int(y - 1), int(z), brush_def, brush_type="terrain")
        nw = self._check_neighbor(int(x - 1), int(y - 1), int(z), brush_def, brush_type="terrain")
        se = self._check_neighbor(int(x + 1), int(y + 1), int(z), brush_def, brush_type="terrain")
        sw = self._check_neighbor(int(x - 1), int(y + 1), int(z), brush_def, brush_type="terrain")

        # Decision hierarchy
        key: str

        # A) Inner corners (concave)
        if n and e and (not ne):
            key = "INNER_CORNER_NE"
        elif s and e and (not se):
            key = "INNER_CORNER_SE"
        elif s and w and (not sw):
            key = "INNER_CORNER_SW"
        elif n and w and (not nw):
            key = "INNER_CORNER_NW"
        # B) Fully surrounded center
        elif n and e and s and w:
            key = "SOLITARY"
        # C) T-shapes
        elif n and e and w and (not s):
            key = "T_SOUTH"
        elif s and e and w and (not n):
            key = "T_NORTH"
        elif n and s and w and (not e):
            key = "T_EAST"
        elif n and s and e and (not w):
            key = "T_WEST"
        # D) Outer corners
        elif n and e and (not s) and (not w):
            key = "CORNER_NE"
        elif s and e and (not n) and (not w):
            key = "CORNER_SE"
        elif s and w and (not n) and (not e):
            key = "CORNER_SW"
        elif n and w and (not s) and (not e):
            key = "CORNER_NW"
        # E) Corridors
        elif n and s and (not e) and (not w):
            key = "VERTICAL"
        elif e and w and (not n) and (not s):
            key = "HORIZONTAL"
        # F) Simple edges
        elif n:
            key = "NORTH"
        elif e:
            key = "EAST"
        elif s:
            key = "SOUTH"
        elif w:
            key = "WEST"
        else:
            key = "SOLITARY"

        # Fallback chain
        candidates: list[str] = [key]
        if key.startswith("INNER_CORNER_"):
            candidates.append(key.replace("INNER_CORNER_", "CORNER_"))
        if key.startswith("CORNER_"):
            if key.endswith("NE"):
                candidates.extend(["NORTH", "EAST"])
            elif key.endswith("NW"):
                candidates.extend(["NORTH", "WEST"])
            elif key.endswith("SE"):
                candidates.extend(["SOUTH", "EAST"])
            elif key.endswith("SW"):
                candidates.extend(["SOUTH", "WEST"])
        if key == "VERTICAL":
            candidates.extend(["NORTH", "SOUTH"])
        if key == "HORIZONTAL":
            candidates.extend(["EAST", "WEST"])
        if key.startswith("T_"):
            candidates.extend(["HORIZONTAL", "VERTICAL"])
        candidates.append("SOLITARY")

        new_id: int | None = None
        for k in candidates:
            v = brush_def.get_border(k)
            if v:
                new_id = int(v)
                break
        if not new_id:
            return

        border_ids = {int(v) for v in brush_def.borders.values()}
        new_items = [it for it in tile.items if int(it.id) not in border_ids]
        new_items.insert(0, Item(id=int(new_id)))
        if new_items == tile.items:
            return

        self._set_tile(replace(tile, items=new_items))

    def _process_ground_border_logic(self, x: int, y: int, z: int, brush_def: BrushDefinition) -> None:
        """Apply classic border-set behavior for `ground` brushes."""
        tile = self.game_map.get_tile(int(x), int(y), int(z))
        if tile is None or tile.ground is None:
            return
        if int(tile.ground.id) != int(brush_def.server_id):
            return

        mask = compute_neighbor_mask_for_ground(
            self.game_map,
            x=int(x),
            y=int(y),
            z=int(z),
            same_ground_ids=(int(brush_def.server_id),),
        )

        # 1) Prefer an inner transition border if any target neighbors exist.
        transition_selected_id: int | None = None
        transition_best_score: int = -1
        for to_server_id, tborders in brush_def.transition_borders.items():
            to_server_id = int(to_server_id)
            mask_t = compute_neighbor_mask_for_target_ground(
                self.game_map,
                x=int(x),
                y=int(y),
                z=int(z),
                target_ground_ids=(to_server_id,),
            )
            if mask_t == 0:
                continue
            alignment_t = select_border_alignment_when_present(mask_t, borders=tborders)
            if alignment_t is None:
                continue
            candidate = tborders.get(alignment_t)
            if candidate is None:
                continue
            strength = int(mask_t).bit_count()
            score = strength * 10 + transition_alignment_weight(alignment_t)
            if score > transition_best_score:
                transition_selected_id = int(candidate)
                transition_best_score = score

        # 2) Otherwise, use the default (outer) border-set selection.
        selected_id = transition_selected_id
        if selected_id is None:
            selected_id = select_border_id_from_definition(mask, brush_def)
            if selected_id is None:
                return

        border_ids = {int(v) for v in brush_def.family_ids}
        border_ids.discard(int(brush_def.server_id))
        new_items = [it for it in tile.items if int(it.id) not in border_ids]
        new_items.insert(0, Item(id=int(selected_id)))
        if new_items == tile.items:
            return
        self._set_tile(replace(tile, items=new_items))

    def _check_neighbor(
        self, nx: int, ny: int, nz: int, brush_def: BrushDefinition, *, brush_type: str = "wall"
    ) -> bool:
        """Check if neighbor tile belongs to the same brush family."""
        neighbor_tile = self.game_map.get_tile(int(nx), int(ny), int(nz))
        # Family-aware check (important for carpets under other items).
        return self._tile_has_family_item(neighbor_tile, brush_def)


# =============================================================================
# Convenience functions
# =============================================================================


def paint_with_optional_autoborder(
    game_map: GameMap,
    *,
    brush_manager: Any,
    x: int,
    y: int,
    z: int,
    selected_server_id: int,
) -> None:
    """Paint a tile, and if it's a smart brush, update neighbors."""
    selected_server_id = int(selected_server_id)
    brush_def = brush_manager.get_brush(selected_server_id)

    tile = game_map.get_tile(int(x), int(y), int(z))
    if tile is None:
        tile = game_map.ensure_tile(int(x), int(y), int(z))

    if brush_def is None:
        new_tile = replace_top_item(tile, new_server_id=selected_server_id, brush_type="wall")
        game_map.set_tile(replace(new_tile, modified=True))
        return

    new_tile = replace_top_item(tile, new_server_id=selected_server_id, brush_type=brush_def.brush_type)
    game_map.set_tile(replace(new_tile, modified=True))

    AutoBorderProcessor(game_map, brush_manager).update_tile(int(x), int(y), int(z), selected_server_id)





def apply_brush_definition_around_positions(
    game_map: GameMap,
    *,
    brush: BrushDefinition,
    positions: Iterable[tuple[int, int, int]],
    placement: Placement = "border_item",
    clean_existing: bool = True,
) -> list[tuple[int, int, int]]:
    """Apply a `BrushDefinition` (from brushes.json) to positions and neighbors."""
    expanded: set[tuple[int, int, int]] = set()
    for x, y, z in positions:
        expanded.add((int(x), int(y), int(z)))
        for dx, dy in NEIGHBOR_OFFSETS:
            expanded.add((int(x + dx), int(y + dy), int(z)))

    same_ids = (int(brush.server_id),)
    border_ids = {int(v) for v in brush.family_ids}
    border_ids.discard(int(brush.server_id))

    modified: list[tuple[int, int, int]] = []
    for x, y, z in sorted(expanded):
        tile = game_map.get_tile(int(x), int(y), int(z))
        if tile is None or tile.ground is None:
            continue
        if int(tile.ground.id) != int(brush.server_id):
            continue

        mask = compute_neighbor_mask_for_ground(game_map, x=int(x), y=int(y), z=int(z), same_ground_ids=same_ids)

        selected_id: int | None = None
        transition_best_score: int = -1
        for to_server_id, tborders in brush.transition_borders.items():
            mask_t = compute_neighbor_mask_for_target_ground(
                game_map,
                x=int(x),
                y=int(y),
                z=int(z),
                target_ground_ids=(int(to_server_id),),
            )
            if mask_t == 0:
                continue
            alignment_t = select_border_alignment_when_present(mask_t, borders=tborders)
            if alignment_t is None:
                continue
            candidate = tborders.get(alignment_t)
            if candidate is None:
                continue
            score = int(mask_t).bit_count() * 10 + transition_alignment_weight(alignment_t)
            if score > transition_best_score:
                transition_best_score = score
                selected_id = int(candidate)

        if selected_id is None:
            selected_id = select_border_id_from_definition(mask, brush)
            if selected_id is None:
                continue

        if placement == "ground":
            if int(tile.ground.id) == int(selected_id):
                continue
            new_tile = replace(tile, ground=Item(id=int(selected_id)), modified=True)
            game_map.set_tile(new_tile)
            modified.append((int(x), int(y), int(z)))
            continue

        new_items = list(tile.items)
        if clean_existing and border_ids:
            new_items = [it for it in new_items if int(it.id) not in border_ids]
        if int(selected_id) != 0:
            new_items.insert(0, Item(id=int(selected_id)))
        if new_items == tile.items:
            continue
        new_tile = replace(tile, items=new_items)
        game_map.set_tile(replace(new_tile, modified=True))
        modified.append((int(x), int(y), int(z)))

    return modified
