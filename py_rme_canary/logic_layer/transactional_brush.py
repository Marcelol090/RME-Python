"""Transactional brush stroke + atomic undo/redo.

This module implements a UI-free command pattern for editor operations.

Key idea: a mouse interaction (down/move/up) becomes a single command that:
- applies the base brush quickly during the stroke (no auto-border per pixel)
- runs auto-border once on finalize over dirty tiles + neighbors
- records *all* tile mutations (including auto-border) into the same action

This avoids common Tibia editor issues where undo removes a wall but leaves
neighbor borders "floating", and it prevents performance cliffs from running
auto-border hundreds of times per drag.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field, replace
from typing import Protocol, runtime_checkable

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile

from .auto_border import AutoBorderProcessor, replace_top_item
from .brush_definitions import (
    DEFAULT_OPTIONAL_BORDER_CARPET_ID,
    VIRTUAL_FLAG_BASE,
    VIRTUAL_FLAG_BITS,
    VIRTUAL_HOUSE_BASE,
    VIRTUAL_HOUSE_MAX,
    VIRTUAL_OPTIONAL_BORDER_ID,
    VIRTUAL_ZONE_BASE,
    VIRTUAL_ZONE_MAX,
    BrushManager,
    DoodadAlternative,
    DoodadBrushSpec,
    DoodadCompositeChoice,
    DoodadItemChoice,
    DoodadTilePlacement,
)

TileKey = tuple[int, int, int]


class TileChangeRecorder(Protocol):
    """Records tile-level changes produced by painting or processors."""

    def record_tile_change(self, key: TileKey, before: Tile | None, after: Tile | None) -> None:
        raise NotImplementedError


@runtime_checkable
class EditorAction(Protocol):
    """UI-free command for undo/redo.

    `PaintAction` is the common tile action. Some tools (e.g. waypoints) mutate
    map-level metadata instead and still need to participate in undo/redo.
    """

    def has_changes(self) -> bool:
        raise NotImplementedError

    def undo(self, game_map: GameMap) -> None:
        raise NotImplementedError

    def redo(self, game_map: GameMap) -> None:
        raise NotImplementedError

    def describe(self) -> str:
        """Short human-readable label for history UI."""
        return self.__class__.__name__


@dataclass(slots=True)
class PaintAction(TileChangeRecorder):
    """A single atomic editor action.

    Stores the original tile state the first time a coordinate is touched,
    and the latest resulting tile state after all modifications.

    Snapshots are `Tile` objects (frozen dataclass) or `None` if the tile
    did not exist.
    """

    brush_id: int
    tiles_before: dict[TileKey, Tile | None] = field(default_factory=dict)
    tiles_after: dict[TileKey, Tile | None] = field(default_factory=dict)

    def describe(self) -> str:
        return "Paint"

    def record_tile_change(self, key: TileKey, before: Tile | None, after: Tile | None) -> None:
        key = (int(key[0]), int(key[1]), int(key[2]))
        if key not in self.tiles_before:
            self.tiles_before[key] = before
        self.tiles_after[key] = after

    def has_changes(self) -> bool:
        return bool(self.tiles_after)

    def undo(self, game_map: GameMap) -> None:
        for (x, y, z), before in self.tiles_before.items():
            if before is None:
                game_map.delete_tile(int(x), int(y), int(z))
            else:
                game_map.set_tile_at(int(x), int(y), int(z), before)

    def redo(self, game_map: GameMap) -> None:
        for (x, y, z), after in self.tiles_after.items():
            if after is None:
                game_map.delete_tile(int(x), int(y), int(z))
            else:
                game_map.set_tile_at(int(x), int(y), int(z), after)


@dataclass(slots=True)
class LabeledPaintAction(PaintAction):
    """A PaintAction with a stable label for the history UI."""

    label: str = "Action"

    def describe(self) -> str:
        return str(self.label or "Action")


@dataclass(slots=True)
class HistoryManager:
    """Undo/redo stacks of editor actions."""

    undo_stack: list[EditorAction] = field(default_factory=list)
    redo_stack: list[EditorAction] = field(default_factory=list)

    def commit_action(self, action: EditorAction) -> None:
        if not action.has_changes():
            return
        self.undo_stack.append(action)
        self.redo_stack.clear()

    def undo(self, game_map: GameMap) -> EditorAction | None:
        if not self.undo_stack:
            return None
        action = self.undo_stack.pop()
        action.undo(game_map)
        self.redo_stack.append(action)
        return action

    def redo(self, game_map: GameMap) -> EditorAction | None:
        if not self.redo_stack:
            return None
        action = self.redo_stack.pop()
        action.redo(game_map)
        self.undo_stack.append(action)
        return action


@dataclass(slots=True)
class TransactionalBrushStroke:
    """Buffers a brush stroke and finalizes auto-border once."""

    game_map: GameMap
    brush_manager: BrushManager
    history: HistoryManager
    auto_border_enabled: bool = True

    # Legacy-inspired brush variation index.
    # MVP: used as a deterministic selector for brushes that define `randomize_ids`.
    brush_variation: int = 0

    # Legacy-inspired: doodad brush thickness.
    # In legacy, thickness controls the density (object count) in the doodad stamp.
    # MVP (Python): treat thickness as a placement probability over the brush footprint.
    doodad_use_custom_thickness: bool = False
    doodad_custom_thickness_low: int = 1
    doodad_custom_thickness_ceil: int = 100

    action: PaintAction | None = None
    dirty: set[TileKey] = field(default_factory=set)
    autoborder_runs: int = 0

    # Replace context is meaningful only for ground brushes, and is applied
    # only when Alt is currently held (legacy behavior).
    _replace_context_enabled: bool = False
    _replace_source_ground_id: int | None = None

    _stroke_origin: TileKey | None = None

    def _doodad_pick_alternative(self, spec: DoodadBrushSpec) -> DoodadAlternative:
        alts = tuple(spec.alternatives or ())
        if not alts:
            return DoodadAlternative()
        idx = int(self.brush_variation) % len(alts)
        return alts[int(idx)]

    def _doodad_owned_ids(self, spec: DoodadBrushSpec) -> frozenset[int]:
        ids: set[int] = set()
        for alt in tuple(spec.alternatives or ()):
            for it in tuple(alt.items or ()):
                if int(it.id) > 0:
                    ids.add(int(it.id))
            for comp in tuple(alt.composites or ()):
                for pl in tuple(comp.tiles or ()):
                    for it in tuple(pl.items or ()):
                        if int(it.id) > 0:
                            ids.add(int(it.id))
        return frozenset(ids)

    def _hash_u32(self, payload: bytes) -> int:
        return int(zlib.crc32(payload) & 0xFFFFFFFF)

    def _weighted_pick_index(self, *, weights: tuple[int, ...], seed: bytes) -> int | None:
        if not weights:
            return None
        total = 0
        for w in weights:
            if int(w) > 0:
                total += int(w)
        if total <= 0:
            return 0
        roll = int(self._hash_u32(seed) % int(total))
        acc = 0
        for i, w in enumerate(weights):
            ww = int(w)
            if ww <= 0:
                continue
            acc += ww
            if roll < acc:
                return int(i)
        return int(len(weights) - 1)

    def _choose_doodad_candidate(
        self,
        *,
        alt: DoodadAlternative,
        seed: bytes,
    ) -> tuple[str, object] | tuple[None, None]:
        items = tuple(alt.items or ())
        comps = tuple(alt.composites or ())

        # Flatten candidates: items + composites.
        cand_kinds: list[str] = []
        cand_objs: list[object] = []
        cand_weights: list[int] = []

        for it in items:
            cand_kinds.append("item")
            cand_objs.append(it)
            cand_weights.append(max(0, int(getattr(it, "chance", 0) or 0)))
        for c in comps:
            cand_kinds.append("composite")
            cand_objs.append(c)
            cand_weights.append(max(0, int(getattr(c, "chance", 0) or 0)))

        if not cand_kinds:
            return None, None

        idx = self._weighted_pick_index(weights=tuple(cand_weights), seed=seed)
        if idx is None:
            return None, None
        return cand_kinds[int(idx)], cand_objs[int(idx)]

    def _tile_contains_item_id(self, tile: Tile, item_id: int) -> bool:
        return any(int(it.id) == int(item_id) for it in tile.items)

    def _tile_contains_any_item_id(self, tile: Tile, item_ids: frozenset[int]) -> bool:
        if not item_ids:
            return False
        return any(int(it.id) in item_ids for it in tile.items)

    def _apply_doodad_add(
        self,
        *,
        x: int,
        y: int,
        z: int,
        item_id: int,
        allow_duplicates: bool,
        owned_ids: frozenset[int] | None = None,
    ) -> None:
        before = self.game_map.get_tile(int(x), int(y), int(z))
        tile = before
        if tile is None:
            tile = self.game_map.ensure_tile(int(x), int(y), int(z))

        if not allow_duplicates:
            # Legacy semantics: on_duplicate=false prevents adding any item from this
            # doodad brush if the tile already contains *any* item owned by the brush.
            if owned_ids is not None and self._tile_contains_any_item_id(tile, owned_ids):
                return
            if self._tile_contains_item_id(tile, int(item_id)):
                return

        new_items = list(tile.items)
        new_items.append(Item(id=int(item_id)))
        after = replace(tile, items=new_items)
        after = replace(after, modified=True)
        if before == after:
            return
        assert self.action is not None
        self.action.record_tile_change((int(x), int(y), int(z)), before, after)
        self.game_map.set_tile(after)
        self.dirty.add((int(x), int(y), int(z)))

    def _apply_doodad_remove_one(self, *, x: int, y: int, z: int, item_id: int) -> None:
        before = self.game_map.get_tile(int(x), int(y), int(z))
        if before is None:
            return
        tile = before

        removed = False
        new_items: list[Item] = []
        # Remove only one instance, preferring the topmost.
        for it in reversed(tile.items):
            if (not removed) and int(it.id) == int(item_id):
                removed = True
                continue
            new_items.append(it)
        if not removed:
            return
        new_items.reverse()
        after = replace(tile, items=new_items)
        after = replace(after, modified=True)
        if before == after:
            return
        assert self.action is not None
        self.action.record_tile_change((int(x), int(y), int(z)), before, after)
        self.game_map.set_tile(after)
        self.dirty.add((int(x), int(y), int(z)))

    def _apply_doodad_remove_owned_one(
        self,
        *,
        x: int,
        y: int,
        z: int,
        preferred_item_id: int | None,
        owned_ids: frozenset[int],
    ) -> None:
        """Remove one item owned by this doodad brush.

        Prefers removing `preferred_item_id` (topmost) when present; otherwise
        removes the topmost item that belongs to the doodad brush.
        """

        before = self.game_map.get_tile(int(x), int(y), int(z))
        if before is None or not before.items:
            return

        pref = None if preferred_item_id is None else int(preferred_item_id)
        removed = False
        new_items: list[Item] = []
        for it in reversed(before.items):
            it_id = int(it.id)
            if not removed:
                if pref is not None and it_id == pref:
                    removed = True
                    continue
                if pref is None and it_id in owned_ids:
                    removed = True
                    continue
                if pref is not None and it_id in owned_ids:
                    # If preferred isn't found higher in the stack, allow any owned id.
                    removed = True
                    continue
            new_items.append(it)

        if not removed:
            return

        new_items.reverse()
        after = replace(before, items=new_items, modified=True)
        if before == after:
            return
        assert self.action is not None
        self.action.record_tile_change((int(x), int(y), int(z)), before, after)
        self.game_map.set_tile(after)
        self.dirty.add((int(x), int(y), int(z)))

    def _choose_tile_items(self, *, placement: DoodadTilePlacement, seed: bytes) -> tuple[int, ...]:
        items = tuple(placement.items or ())
        if not items:
            return ()
        if not bool(getattr(placement, "choose_one", False)):
            return tuple(int(i.id) for i in items if int(i.id) > 0)
        weights = tuple(max(0, int(getattr(i, "chance", 0) or 0)) for i in items)
        idx = self._weighted_pick_index(weights=weights, seed=seed)
        if idx is None:
            return ()
        chosen = items[int(idx)]
        return (int(chosen.id),) if int(chosen.id) > 0 else ()

    def _should_place_doodad_at(
        self,
        *,
        x: int,
        y: int,
        z: int,
        selected_server_id: int,
        spec: DoodadBrushSpec | None,
    ) -> bool:
        origin = self._stroke_origin
        if origin is not None and (int(x), int(y), int(z)) == (int(origin[0]), int(origin[1]), int(origin[2])):
            return True

        # Effective thickness combines the brush definition + toolbar override.
        # Legacy: `thickness="a/b"` controls doodad density in the buffer.
        # Python: treat it as a per-tile placement probability.
        base_low = 100
        base_ceil = 100
        if spec is not None:
            base_low = max(0, int(getattr(spec, "thickness_low", 100) or 0))
            base_ceil = max(1, int(getattr(spec, "thickness_ceil", 100) or 1))

        low = int(base_low)
        ceil = int(base_ceil)

        if bool(self.doodad_use_custom_thickness):
            ov_low = max(0, int(self.doodad_custom_thickness_low))
            ov_ceil = max(1, int(self.doodad_custom_thickness_ceil))
            low = int(low * ov_low)
            ceil = int(ceil * ov_ceil)

        if low <= 0:
            return False
        if low >= ceil:
            return True

        p = float(low) / float(ceil)
        # Deterministic per-position to keep results stable during drag.
        payload = (
            f"{int(x)},{int(y)},{int(z)},{int(selected_server_id)},{int(self.brush_variation)},{low},{ceil}".encode()
        )
        h = int(zlib.crc32(payload) & 0xFFFFFFFF)
        return int(h % 10_000) < int(p * 10_000)

    def mark_autoborder_position(self, *, x: int, y: int, z: int) -> None:
        """Mark a position to be included in the finalize auto-border pass.

        Used to mimic the legacy RME concept of `tilestoborder` (a perimeter area
        around the brush) without applying the base brush on those tiles.
        """
        if self.action is None:
            raise RuntimeError("Stroke not started. Call begin() first.")
        self.dirty.add((int(x), int(y), int(z)))

    def begin(
        self,
        *,
        x: int,
        y: int,
        z: int,
        selected_server_id: int,
        replace_enabled: bool = False,
        replace_source_ground_id: int | None = None,
        alt: bool = False,
    ) -> None:
        self.action = PaintAction(brush_id=int(selected_server_id))
        self.dirty.clear()
        self.autoborder_runs = 0
        self._replace_context_enabled = bool(replace_enabled)
        self._replace_source_ground_id = None if replace_source_ground_id is None else int(replace_source_ground_id)
        self._stroke_origin = (int(x), int(y), int(z))
        self.paint(x=x, y=y, z=z, selected_server_id=int(selected_server_id), alt=bool(alt))

    def paint(self, *, x: int, y: int, z: int, selected_server_id: int, alt: bool = False) -> None:
        """Apply the base brush silently and record tile change.

        This does NOT run auto-border. Auto-border is applied only on `end()`.
        """

        if self.action is None:
            raise RuntimeError("Stroke not started. Call begin() first.")

        x, y, z = int(x), int(y), int(z)
        selected_server_id = int(selected_server_id)

        brush_def = self.brush_manager.get_brush(selected_server_id)
        before = self.game_map.get_tile(x, y, z)
        brush_type = brush_def.brush_type if brush_def is not None else "wall"
        brush_type_norm = str(brush_type).strip().lower()

        # Legacy-inspired Variation (MVP): if the brush defines `randomize_ids`,
        # treat variation as a deterministic selector over (main_id + randomize_ids).
        effective_server_id = int(selected_server_id)
        if brush_def is not None and brush_type_norm == "ground":
            variants = (int(getattr(brush_def, "server_id", selected_server_id)),) + tuple(
                int(v) for v in getattr(brush_def, "randomize_ids", ())
            )
            variants = tuple(v for v in variants if int(v) > 0)
            if len(variants) > 1:
                idx = int(self.brush_variation) % len(variants)
                effective_server_id = int(variants[idx])

        # Legacy Replace tool (Alt) for ground brushes:
        # - If replace_source_ground_id is None: only apply to empty tiles (no ground).
        # - Else: only apply to tiles whose current ground matches replace_source_ground_id.
        # IMPORTANT: this filter is applied only while Alt is currently held.
        if bool(alt) and self._replace_context_enabled and str(brush_type).lower() == "ground":
            current_ground_id = None if before is None or before.ground is None else int(before.ground.id)

            if self._replace_source_ground_id is None:
                if current_ground_id is not None:
                    return
            elif current_ground_id != int(self._replace_source_ground_id):
                return

        tile = before
        if tile is None:
            tile = self.game_map.ensure_tile(x, y, z)

        if brush_type_norm == "flag":
            sid = int(selected_server_id)
            if VIRTUAL_FLAG_BASE <= sid < VIRTUAL_FLAG_BASE + VIRTUAL_FLAG_BITS:
                bit = int(sid - VIRTUAL_FLAG_BASE)
                mask = int(1 << bit)
            else:
                # Allow explicit bitmask ids if user defines custom flag brushes.
                mask = int(sid)

            cur = int(getattr(tile, "map_flags", 0) or 0)
            new_flags = (cur & ~mask) if bool(alt) else (cur | mask)
            after = replace(tile, map_flags=int(new_flags))

        elif brush_type_norm == "zone":
            sid = int(selected_server_id)
            if VIRTUAL_ZONE_BASE <= sid < VIRTUAL_ZONE_BASE + VIRTUAL_ZONE_MAX:
                zone_id = int(sid - VIRTUAL_ZONE_BASE)
            else:
                zone_id = int(sid)

            cur_zones = set(getattr(tile, "zones", frozenset()) or frozenset())
            if bool(alt):
                cur_zones.discard(int(zone_id))
            elif int(zone_id) != 0:
                cur_zones.add(int(zone_id))
            after = replace(tile, zones=frozenset(int(z) for z in cur_zones if int(z) != 0))

        elif brush_type_norm == "house":
            sid = int(selected_server_id)
            if VIRTUAL_HOUSE_BASE <= sid < VIRTUAL_HOUSE_BASE + VIRTUAL_HOUSE_MAX:
                house_id = int(sid - VIRTUAL_HOUSE_BASE)
            else:
                house_id = int(sid)

            if bool(alt):
                after = replace(tile, house_id=None)
            else:
                if int(house_id) <= 0:
                    return
                after = replace(tile, house_id=int(house_id))

        elif brush_type_norm == "optional_border":
            # MVP: legacy "Optional Border" behaves like a gravel tool.
            # Implement as paint/erase of the default gravel carpet brush.
            sid = int(selected_server_id)
            if sid != int(VIRTUAL_OPTIONAL_BORDER_ID):
                return

            gravel_id = int(DEFAULT_OPTIONAL_BORDER_CARPET_ID)
            gravel_def = self.brush_manager.get_brush(int(gravel_id))
            if gravel_def is None:
                return

            fam = {int(v) for v in gravel_def.family_ids}
            kept = [it for it in tile.items if int(it.id) not in fam]
            if bool(alt):
                after = replace(tile, items=kept)
            else:
                kept.insert(0, Item(id=int(gravel_id)))
                after = replace(tile, items=kept)

        elif brush_type_norm == "doodad" and brush_def is not None:
            target_id = int(getattr(brush_def, "server_id", selected_server_id))
            if target_id <= 0:
                return

            spec = getattr(brush_def, "doodad_spec", None)

            # Legacy: canSmear is gated by `draggable`.
            if spec is not None and (not bool(getattr(spec, "draggable", True))):
                origin = self._stroke_origin
                if origin is None or (int(x), int(y), int(z)) != (int(origin[0]), int(origin[1]), int(origin[2])):
                    return

            # Legacy: if on_blocking is false, only place on non-blocking tiles.
            # We don't have full movement flagging yet, so use a conservative
            # approximation: require a tile with ground.
            if (
                spec is not None
                and (not bool(getattr(spec, "on_blocking", False)))
                and (before is None or before.ground is None)
            ):
                return

            # If the brush declares one_size, only apply on the origin tile.
            if spec is not None and bool(getattr(spec, "one_size", False)):
                origin = self._stroke_origin
                if origin is None or (int(x), int(y), int(z)) != (int(origin[0]), int(origin[1]), int(origin[2])):
                    return

            if not self._should_place_doodad_at(
                x=int(x),
                y=int(y),
                z=int(z),
                selected_server_id=int(selected_server_id),
                spec=spec,
            ) and not bool(alt):
                return

            if spec is None:
                # Fallback behavior (MVP): treat doodad as a simple decoration item id.
                if bool(alt):
                    self._apply_doodad_remove_one(x=int(x), y=int(y), z=int(z), item_id=int(target_id))
                else:
                    self._apply_doodad_add(x=int(x), y=int(y), z=int(z), item_id=int(target_id), allow_duplicates=True)
                return

            owned_ids = self._doodad_owned_ids(spec)

            alt_spec = self._doodad_pick_alternative(spec)
            seed = f"doodad:{int(x)},{int(y)},{int(z)}:{int(target_id)}:{int(self.brush_variation)}".encode()
            kind, obj = self._choose_doodad_candidate(alt=alt_spec, seed=seed)
            if kind is None or obj is None:
                return

            allow_dupes = bool(getattr(spec, "on_duplicate", False))

            if kind == "item":
                it = obj
                assert isinstance(it, DoodadItemChoice)
                if bool(alt):
                    self._apply_doodad_remove_owned_one(
                        x=int(x),
                        y=int(y),
                        z=int(z),
                        preferred_item_id=int(it.id),
                        owned_ids=owned_ids,
                    )
                else:
                    self._apply_doodad_add(
                        x=int(x),
                        y=int(y),
                        z=int(z),
                        item_id=int(it.id),
                        allow_duplicates=bool(allow_dupes),
                        owned_ids=owned_ids,
                    )
                return

            comp = obj
            assert isinstance(comp, DoodadCompositeChoice)
            for placement in tuple(comp.tiles or ()):
                assert isinstance(placement, DoodadTilePlacement)
                tx = int(x) + int(placement.dx)
                ty = int(y) + int(placement.dy)
                tz = int(z) + int(placement.dz)

                # Respect on_blocking=false for each composite tile too.
                if spec is not None and (not bool(getattr(spec, "on_blocking", False))):
                    dest_before = self.game_map.get_tile(int(tx), int(ty), int(tz))
                    if dest_before is None or dest_before.ground is None:
                        continue

                item_seed = f"tile:{int(tx)},{int(ty)},{int(tz)}:{int(target_id)}:{int(self.brush_variation)}".encode()
                chosen_ids = self._choose_tile_items(placement=placement, seed=item_seed)
                for iid in chosen_ids:
                    if int(iid) <= 0:
                        continue
                    if bool(alt):
                        self._apply_doodad_remove_owned_one(
                            x=int(tx),
                            y=int(ty),
                            z=int(tz),
                            preferred_item_id=int(iid),
                            owned_ids=owned_ids,
                        )
                    else:
                        self._apply_doodad_add(
                            x=int(tx),
                            y=int(ty),
                            z=int(tz),
                            item_id=int(iid),
                            allow_duplicates=bool(allow_dupes),
                            owned_ids=owned_ids,
                        )
            return

        elif brush_type_norm == "carpet" and brush_def is not None:
            # Carpets are floor decorations: never clobber unrelated top items.
            fam = {int(v) for v in brush_def.family_ids}
            kept = [it for it in tile.items if int(it.id) not in fam]
            # Insert at bottom (rendered below other items).
            kept.insert(0, Item(id=int(effective_server_id)))
            after = replace(tile, items=kept)

        elif brush_type_norm == "table" and brush_def is not None:
            # Tables/counters: behave like wall-like items, but never clobber unrelated stack.
            fam = {int(v) for v in brush_def.family_ids}
            kept = [it for it in tile.items if int(it.id) not in fam]
            # Place on top.
            kept.append(Item(id=int(effective_server_id)))
            after = replace(tile, items=kept)

        else:
            after = replace_top_item(tile, new_server_id=int(effective_server_id), brush_type=brush_type)

        if after is not None:
            after = replace(after, modified=True)

        if before == after:
            return

        self.action.record_tile_change((x, y, z), before, after)
        self.game_map.set_tile(after)
        self.dirty.add((x, y, z))

    def end(self) -> PaintAction | None:
        """Finalize the stroke.

        Runs auto-border once over dirty tiles and their immediate neighbors,
        records any generated borders into the same `PaintAction`, then commits
        the action into history.
        """

        if self.action is None:
            return None

        selected_server_id = int(self.action.brush_id)
        brush_def = self.brush_manager.get_brush(selected_server_id)
        brush_type_norm = str(brush_def.brush_type).strip().lower() if brush_def is not None else "wall"

        if self.dirty and self.auto_border_enabled and brush_type_norm not in ("flag", "zone", "doodad"):
            # `AutoBorderProcessor.update_positions()` already expands to the needed
            # neighborhood per brush-type. Passing expanded positions here would
            # over-expand and increase work.
            proc = AutoBorderProcessor(self.game_map, self.brush_manager, change_recorder=self.action)
            proc.update_positions(self.dirty, selected_server_id)
            self.autoborder_runs += 1

        # Legacy doodads can request a reborder pass.
        if (
            self.dirty
            and self.auto_border_enabled
            and brush_type_norm == "doodad"
            and brush_def is not None
            and bool(getattr(getattr(brush_def, "doodad_spec", None), "redo_borders", False))
        ):
            expanded: set[TileKey] = set()
            for x, y, z in set(self.dirty):
                t = self.game_map.get_tile(int(x), int(y), int(z))
                expanded.add((int(x), int(y), int(z)))
                if t is not None and t.ground is not None:
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            expanded.add((int(x + dx), int(y + dy), int(z)))
                elif t is not None and getattr(t, "items", None):
                    expanded.add((int(x), int(y - 1), int(z)))
                    expanded.add((int(x - 1), int(y), int(z)))
                    expanded.add((int(x + 1), int(y), int(z)))
                    expanded.add((int(x), int(y + 1), int(z)))

            # Collect brush ids present in the affected area (like borderize_selection).
            brush_ids: set[int] = set()
            for px, py, pz in expanded:
                tt = self.game_map.get_tile(int(px), int(py), int(pz))
                if tt is None:
                    continue
                if tt.ground is not None:
                    b = self.brush_manager.get_brush_any(int(tt.ground.id))
                    if b is not None:
                        brush_ids.add(int(b.server_id))
                for it in getattr(tt, "items", []) or []:
                    b = self.brush_manager.get_brush_any(int(it.id))
                    if b is not None:
                        brush_ids.add(int(b.server_id))

            if brush_ids:
                proc = AutoBorderProcessor(self.game_map, self.brush_manager, change_recorder=self.action)
                for bid in sorted(brush_ids):
                    proc.update_positions(expanded, int(bid))
                self.autoborder_runs += 1

        action = self.action
        self.action = None
        self.dirty.clear()
        self._replace_context_enabled = False
        self._replace_source_ground_id = None
        self._stroke_origin = None

        self.history.commit_action(action)
        return action

    def cancel(self) -> None:
        """Cancel an in-progress stroke without committing history."""

        self.action = None
        self.dirty.clear()
        self.autoborder_runs = 0
        self._replace_context_enabled = False
        self._replace_source_ground_id = None
        self._stroke_origin = None

    def _expanded_dirty_with_neighbors(self) -> set[TileKey]:
        expanded: set[TileKey] = set(self.dirty)
        for x, y, z in list(self.dirty):
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    expanded.add((int(x + dx), int(y + dy), int(z)))
        return expanded
