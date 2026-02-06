"""Main editor session orchestrator.

This module provides the EditorSession class that coordinates all
session components: selection, clipboard, gestures, and movement.
"""

from __future__ import annotations

import os
import random
import time
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass, field, replace
from typing import Any

from py_rme_canary.core.data.door import DoorType
from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.spawns import MonsterSpawnArea, MonsterSpawnEntry, NpcSpawnArea, NpcSpawnEntry
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.data.towns import Town
from py_rme_canary.core.data.zones import Zone
from py_rme_canary.core.database.door_catalog import load_default_closed_doors
from py_rme_canary.core.database.door_pairs import load_door_pairs
from py_rme_canary.core.database.items_xml import ItemsXML
from py_rme_canary.core.protocols.live_client import LiveClient
from py_rme_canary.core.protocols.live_packets import (
    ConnectionState,
    PacketType,
    decode_chat,
    decode_client_list,
    decode_cursor,
)
from py_rme_canary.core.protocols.live_server import LiveServer
from py_rme_canary.core.protocols.tile_serializer import (
    decode_map_chunk,
    decode_tile_update,
    encode_tile_update,
)
from py_rme_canary.logic_layer.clipboard import ClipboardManager as SystemClipboardManager
from py_rme_canary.logic_layer.clipboard import tiles_from_entry

from ..brush_definitions import (
    VIRTUAL_DOOR_TOOL_HATCH,
    VIRTUAL_DOOR_TOOL_LOCKED,
    VIRTUAL_DOOR_TOOL_MAGIC,
    VIRTUAL_DOOR_TOOL_NORMAL,
    VIRTUAL_DOOR_TOOL_QUEST,
    VIRTUAL_DOOR_TOOL_WINDOW,
    VIRTUAL_HOUSE_EXIT_BASE,
    VIRTUAL_HOUSE_EXIT_MAX,
    VIRTUAL_MONSTER_BASE,
    VIRTUAL_MONSTER_MAX,
    VIRTUAL_NPC_BASE,
    VIRTUAL_NPC_MAX,
    VIRTUAL_SPAWN_MONSTER_TOOL_ID,
    VIRTUAL_SPAWN_NPC_TOOL_ID,
    VIRTUAL_WAYPOINT_BASE,
    VIRTUAL_WAYPOINT_MAX,
    BrushManager,
    monster_name_for_virtual_id,
    npc_name_for_virtual_id,
    waypoint_virtual_id,
)
from ..door_brush import DoorBrush
from ..map_metadata_actions import (
    HouseAction,
    HouseEntryAction,
    MonsterSpawnsAction,
    NpcSpawnsAction,
    TownAction,
    WaypointAction,
    ZoneAction,
)
from ..networked_action_queue import NetworkedActionQueue, decode_tile_positions
from ..remove_items import remove_items_in_map
from ..replace_items import replace_items_in_map
from ..transactional_brush import (
    EditorAction,
    HistoryManager,
    LabeledPaintAction,
    PaintAction,
)
from .action_queue import ActionType, SessionAction, SessionActionQueue
from .clipboard import ClipboardManager
from .gestures import GestureHandler
from .move import MoveHandler
from .selection import SelectionApplyMode, SelectionManager, TileKey, tile_is_nonempty
from .selection_modes import SelectionDepthMode, apply_compensation_offset

TilesChangedCallback = Callable[[set[TileKey]], None]


@dataclass(slots=True)
class BatchedPositionsGesture:
    """Accumulates visited positions for special tools.

    Some tools don't use the normal brush stroke pipeline (e.g. spawns/doors),
    but still must behave like a stroke: one undoable action per gesture.
    """

    positions: set[TileKey]
    alt: bool
    commit: Callable[[set[TileKey], bool], EditorAction | None]

    def add(self, *, x: int, y: int, z: int) -> None:
        self.positions.add((int(x), int(y), int(z)))

    def finish(self) -> EditorAction | None:
        return self.commit(set(self.positions), bool(self.alt))


def _is_invalid_item_id(item_id: int) -> bool:
    return int(item_id) == 0


def _clean_item_tree(item: Item) -> tuple[Item | None, int]:
    """Remove invalid items recursively from a container tree.

    Invalid is defined as:
    - placeholder server id 0, OR
    - loader-replaced item (raw_unknown_id set).
    """

    if _is_invalid_item_id(int(item.id)) or item.raw_unknown_id is not None:
        return None, 1

    if not item.items:
        return item, 0

    removed = 0
    out_children: list[Item] = []
    changed = False
    for child in item.items:
        cleaned, r = _clean_item_tree(child)
        removed += int(r)
        if cleaned is None:
            changed = True
            continue
        if cleaned is not child:
            changed = True
        out_children.append(cleaned)

    if not changed:
        return item, 0
    return item.with_container_items(tuple(out_children)), int(removed)


def _tile_is_truly_empty(tile: Tile) -> bool:
    return (
        tile.ground is None
        and (not tile.items)
        and tile.house_id is None
        and int(tile.map_flags) == 0
        and (not tile.zones)
    )


@dataclass(slots=True)
class EditorSession:
    """Stateful controller for editor input gestures.

    This is the main entry point for editor operations. It coordinates:
    - Selection management (box selection, toggle, etc.)
    - Clipboard operations (copy, cut, paste)
    - Paint gestures (mouse down/move/up)
    - Selection movement
    - Undo/redo history
    - Auto-border processing
    """

    game_map: GameMap
    brush_manager: BrushManager
    on_tiles_changed: TilesChangedCallback | None = None
    auto_border_enabled: bool = True
    merge_move_enabled: bool = False

    # UI-controlled brush size (radius). Kept Qt-free so non-tile tools (e.g.
    # spawn-area tools) can respect the current size.
    brush_size: int = 0

    # Legacy-inspired: brush variation index.
    # MVP: used as a deterministic selector for brushes with `randomize_ids`.
    brush_variation: int = 0

    # Legacy-inspired: doodad brush thickness (density).
    # MVP: controls a probability gate for doodad placement across the brush footprint.
    doodad_use_custom_thickness: bool = False
    doodad_custom_thickness_low: int = 1
    doodad_custom_thickness_ceil: int = 100

    # Legacy-inspired: doodad erase behavior + eraser unique protection.
    doodad_erase_like: bool = False
    eraser_leave_unique: bool = True

    # Legacy-inspired: recent brushes (most-recent-first). Updated whenever the
    # selected brush changes.
    recent_brushes: list[int] = field(default_factory=list)
    recent_brushes_max: int = 20

    # Legacy-inspired: BORDERIZE_DRAG + threshold, gated by USE_AUTOMAGIC.
    borderize_drag_enabled: bool = True
    borderize_drag_threshold: int = 6000

    # Legacy-inspired: MERGE_PASTE + BORDERIZE_PASTE (gated by USE_AUTOMAGIC).
    merge_paste_enabled: bool = False
    borderize_paste_enabled: bool = True
    borderize_paste_threshold: int = 10000

    history: HistoryManager = field(default_factory=HistoryManager)

    # Local-only queue of typed actions (legacy-inspired).
    action_queue: SessionActionQueue = field(default_factory=SessionActionQueue)

    # Component managers (initialized in __post_init__)
    _selection: SelectionManager = field(init=False)
    _clipboard: ClipboardManager = field(init=False)
    _gestures: GestureHandler = field(init=False)
    _move: MoveHandler = field(init=False)

    # Lazy-loaded door pairing map for the "Switch Door" MVP tool.
    _door_pairs: dict[int, int] | None = field(default=None, init=False, repr=False)

    # Lazy-loaded default closed door ids per door kind (DoorBrush MVP).
    _door_defaults: dict[str, int] | None = field(default=None, init=False, repr=False)

    # Lazy-loaded items.xml for best-effort item kind classification.
    _items_xml: ItemsXML | None = field(default=None, init=False, repr=False)

    # Pending one-shot House Exit brush operation (legacy: cannot drag/smear).
    # Tuple: (house_id, x, y, z, alt)
    _pending_house_exit: tuple[int, int, int, int, bool] | None = field(default=None, init=False, repr=False)

    # Pending one-shot Waypoint brush operation (legacy: cannot drag/smear).
    # Tuple: (name, x, y, z, alt)
    _pending_waypoint: tuple[str, int, int, int, bool] | None = field(default=None, init=False, repr=False)

    # Pending special-tool stroke (smear/drag). Collects multiple tiles while the mouse
    # button is down and applies a single undoable action on mouse_up.
    _pending_batched_positions: BatchedPositionsGesture | None = field(default=None, init=False, repr=False)

    # Live Editing Client (optional)
    _live_client: LiveClient | None = field(default=None, init=False, repr=False)
    _live_server: LiveServer | None = field(default=None, init=False, repr=False)
    _live_action_queue: NetworkedActionQueue = field(init=False, repr=False)
    _live_clients: dict[int, dict[str, object]] = field(default_factory=dict, init=False, repr=False)
    _live_cursors: dict[int, tuple[int, int, int]] = field(default_factory=dict, init=False, repr=False)
    _live_sync_started: bool = field(default=False, init=False, repr=False)
    _live_cursor_last_sent: float = field(default=0.0, init=False, repr=False)
    _on_live_chat: Callable[[int, str, str], None] | None = field(default=None, init=False, repr=False)
    _on_live_client_list: Callable[[list[dict[str, object]]], None] | None = field(default=None, init=False, repr=False)
    _on_live_cursor: Callable[[int, int, int, int], None] | None = field(default=None, init=False, repr=False)

    def _door_kind_for_tool_id(self, sid: int) -> str | None:
        s = int(sid)
        mapping = {
            int(VIRTUAL_DOOR_TOOL_NORMAL): "normal",
            int(VIRTUAL_DOOR_TOOL_LOCKED): "locked",
            int(VIRTUAL_DOOR_TOOL_MAGIC): "magic",
            int(VIRTUAL_DOOR_TOOL_QUEST): "quest",
            int(VIRTUAL_DOOR_TOOL_WINDOW): "window",
            int(VIRTUAL_DOOR_TOOL_HATCH): "hatch",
        }
        return mapping.get(int(s))

    def _door_type_for_kind(self, kind: str) -> DoorType | None:
        k = (kind or "").strip().lower()
        mapping = {
            "normal": DoorType.NORMAL,
            "locked": DoorType.LOCKED,
            "magic": DoorType.MAGIC,
            "quest": DoorType.QUEST,
            "window": DoorType.WINDOW,
            "hatch": DoorType.HATCH,
        }
        return mapping.get(str(k))

    def _is_door_item(self, item: Item, *, door_pairs: dict[int, int] | None = None) -> bool:
        brush = self.brush_manager.get_brush_any(int(item.id))
        spec = brush.door_spec if brush is not None else None
        if spec is not None and spec.entry_for_item(int(item.id)) is not None:
            return True
        pairs = door_pairs if door_pairs is not None else self._ensure_door_pairs_loaded()
        return int(item.id) in pairs

    def _resolve_waypoint_name_for_virtual_id(self, sid: int) -> str | None:
        """Reverse-map a waypoint virtual id back to an existing waypoint name."""

        vid = int(sid)
        if not (VIRTUAL_WAYPOINT_BASE <= vid < VIRTUAL_WAYPOINT_BASE + VIRTUAL_WAYPOINT_MAX):
            return None

        waypoints = getattr(self.game_map, "waypoints", None) or {}
        names = sorted((str(k) for k in waypoints), key=lambda s: s.lower())

        used: set[int] = set()
        id_to_name: dict[int, str] = {}
        for nm in names:
            try:
                wvid = int(waypoint_virtual_id(nm, used=used))
            except Exception:
                continue
            id_to_name[int(wvid)] = str(nm)
        return id_to_name.get(int(vid))

    def __post_init__(self) -> None:
        self._selection = SelectionManager(game_map=self.game_map)
        self._clipboard = ClipboardManager(game_map=self.game_map)
        self._gestures = GestureHandler(
            game_map=self.game_map,
            brush_manager=self.brush_manager,
            history=self.history,
            auto_border_enabled=self.auto_border_enabled,
        )
        self._gestures.set_brush_variation(int(self.brush_variation))
        self._gestures.set_doodad_custom_thickness(
            enabled=bool(self.doodad_use_custom_thickness),
            low=int(self.doodad_custom_thickness_low),
            ceil=int(self.doodad_custom_thickness_ceil),
        )
        self._gestures.set_doodad_erase_like(bool(self.doodad_erase_like))
        self._gestures.set_eraser_leave_unique(bool(self.eraser_leave_unique))
        self._move = MoveHandler(
            game_map=self.game_map,
            brush_manager=self.brush_manager,
            merge_move_enabled=self.merge_move_enabled,
        )
        self._live_action_queue = NetworkedActionQueue(session=self)
        self._live_action_queue.set_broadcast_callback(self._broadcast_live_tiles)

    def set_brush_variation(self, variation: int) -> None:
        self.brush_variation = int(variation)
        with suppress(Exception):
            self._gestures.set_brush_variation(int(self.brush_variation))

    def set_doodad_custom_thickness(self, *, enabled: bool, low: int = 1, ceil: int = 100) -> None:
        self.doodad_use_custom_thickness = bool(enabled)
        self.doodad_custom_thickness_low = int(low)
        self.doodad_custom_thickness_ceil = int(ceil)
        with suppress(Exception):
            self._gestures.set_doodad_custom_thickness(
                enabled=bool(self.doodad_use_custom_thickness),
                low=int(self.doodad_custom_thickness_low),
                ceil=int(self.doodad_custom_thickness_ceil),
            )

    def set_doodad_erase_like(self, enabled: bool) -> None:
        self.doodad_erase_like = bool(enabled)
        with suppress(Exception):
            self._gestures.set_doodad_erase_like(bool(self.doodad_erase_like))

    def set_eraser_leave_unique(self, enabled: bool) -> None:
        self.eraser_leave_unique = bool(enabled)
        with suppress(Exception):
            self._gestures.set_eraser_leave_unique(bool(self.eraser_leave_unique))

    def _ensure_door_pairs_loaded(self) -> dict[int, int]:
        if self._door_pairs is not None:
            return self._door_pairs

        # Prefer the conventional data path; keep failure non-fatal.
        path = os.path.join("data", "items", "items.xml")
        try:
            self._door_pairs = load_door_pairs(path)
        except Exception:
            self._door_pairs = {}
        return self._door_pairs

    def _ensure_items_xml_loaded(self) -> ItemsXML | None:
        if self._items_xml is not None:
            return self._items_xml

        path = os.path.join("data", "items", "items.xml")
        try:
            self._items_xml = ItemsXML.load(path, strict_mapping=False)
        except Exception:
            self._items_xml = None
        return self._items_xml

    def _ensure_door_defaults_loaded(self) -> dict[str, int]:
        if self._door_defaults is not None:
            return self._door_defaults

        path = os.path.join("data", "items", "items.xml")
        try:
            self._door_defaults = load_default_closed_doors(path)
        except Exception:
            self._door_defaults = {}
        return self._door_defaults

    def _remove_topmost_door(self, *, x: int, y: int, z: int) -> EditorAction | None:
        """Remove the topmost door-like item on a tile (undoable)."""

        pairs = self._ensure_door_pairs_loaded()
        if not pairs:
            return None

        x, y, z = int(x), int(y), int(z)
        key: TileKey = (x, y, z)

        before = self.game_map.get_tile(x, y, z)
        if before is None or not before.items:
            return None

        idx: int | None = None
        for i in range(len(before.items) - 1, -1, -1):
            it = before.items[i]
            if int(it.id) in pairs:
                idx = int(i)
                break
        if idx is None:
            return None

        new_items = list(before.items)
        removed = new_items.pop(int(idx))
        after: Tile | None = replace(before, items=new_items, modified=True)

        action = LabeledPaintAction(brush_id=0, label="Door Brush")
        action.record_tile_change(key, before, after)
        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(
                type=ActionType.SWITCH_DOOR,
                action=action,
                label="Door Brush",
                details={"x": int(x), "y": int(y), "z": int(z), "removed": int(getattr(removed, "id", 0))},
            )
        )
        self._emit_tiles_changed({key})
        return action

    def apply_door_brush_to_positions(
        self,
        *,
        positions: set[TileKey],
        door_kind: str,
        alt: bool = False,
    ) -> EditorAction | None:
        """Apply DoorBrush over multiple tiles as one undoable action."""

        if not positions:
            return None

        pairs = self._ensure_door_pairs_loaded()
        defaults = self._ensure_door_defaults_loaded()
        kind = (door_kind or "").strip().lower()
        door_type = self._door_type_for_kind(kind)
        door_brush = DoorBrush(door_type) if door_type is not None else None
        door_id: int | None = None
        if not bool(alt):
            door_id = defaults.get(kind) or defaults.get("normal")

        items_xml = self._ensure_items_xml_loaded()

        action = LabeledPaintAction(brush_id=0, label="Door Brush")
        affected: set[TileKey] = set()

        for x, y, z in sorted({(int(a), int(b), int(c)) for (a, b, c) in positions}):
            before = self.game_map.get_tile(int(x), int(y), int(z))
            if before is None:
                continue

            after: Tile | None = None

            if bool(alt):
                if not before.items:
                    continue
                idx: int | None = None
                for i in range(len(before.items) - 1, -1, -1):
                    it = before.items[i]
                    if self._is_door_item(it, door_pairs=pairs):
                        idx = int(i)
                        break
                if idx is None:
                    continue
                new_items = list(before.items)
                new_items.pop(int(idx))
                after = replace(before, items=new_items, modified=True)
            else:
                door_attempted = False
                if door_brush is not None:
                    pos = Position(x=int(x), y=int(y), z=int(z))
                    if door_brush.can_draw(self.game_map, pos, brush_manager=self.brush_manager):
                        door_attempted = True
                        changes = door_brush.draw(
                            self.game_map,
                            pos,
                            brush_manager=self.brush_manager,
                        )
                        if changes:
                            after = changes[0][1]

                if after is None and not door_attempted:
                    repl_idx: int | None = None
                    if items_xml is not None and before.items:
                        for i in range(len(before.items) - 1, -1, -1):
                            it = before.items[i]
                            meta = items_xml.get(int(it.id))
                            k = (meta.kind if meta is not None else "").strip().lower()
                            if k in ("wall", "door"):
                                repl_idx = int(i)
                                break
                    new_items = list(before.items)
                    if door_id is None:
                        continue
                    new_item = Item(id=int(door_id))
                    if repl_idx is None:
                        new_items.append(new_item)
                    else:
                        new_items[int(repl_idx)] = new_item
                    after = replace(before, items=new_items, modified=True)

            key: TileKey = (int(x), int(y), int(z))
            action.record_tile_change(key, before, after)
            affected.add(key)

        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(
                type=ActionType.SWITCH_DOOR,
                action=action,
                label="Door Brush",
                details={"count": len(affected), "alt": bool(alt), "kind": str(kind)},
            )
        )
        self._emit_tiles_changed(affected)
        return action

    def place_or_toggle_door_at(self, *, x: int, y: int, z: int, door_kind: str) -> EditorAction | None:
        """DoorBrush: place a door based on wall definitions or fall back to defaults."""

        defaults = self._ensure_door_defaults_loaded()
        if not defaults:
            defaults = {}

        kind = (door_kind or "").strip().lower()
        door_id = defaults.get(kind) or defaults.get("normal")
        if door_id is None:
            return None

        door_type = self._door_type_for_kind(kind)
        door_brush = DoorBrush(door_type) if door_type is not None else None

        x, y, z = int(x), int(y), int(z)
        key: TileKey = (x, y, z)

        before = self.game_map.get_tile(x, y, z)
        if before is None:
            return None

        door_attempted = False
        if door_brush is not None:
            pos = Position(x=int(x), y=int(y), z=int(z))
            if door_brush.can_draw(self.game_map, pos, brush_manager=self.brush_manager):
                door_attempted = True
                changes = door_brush.draw(
                    self.game_map,
                    pos,
                    brush_manager=self.brush_manager,
                )
                if changes:
                    after = changes[0][1]
                    action = LabeledPaintAction(brush_id=0, label="Door Brush")
                    action.record_tile_change(key, before, after)
                    action.redo(self.game_map)
                    self.history.commit_action(action)
                    self.action_queue.push(
                        SessionAction(
                            type=ActionType.SWITCH_DOOR,
                            action=action,
                            label="Door Brush",
                            details={"x": int(x), "y": int(y), "z": int(z), "kind": str(kind)},
                        )
                    )
                    self._emit_tiles_changed({key})
                    return action

        # Best-effort: replace the topmost wall/door-like item, otherwise append.
        if door_attempted:
            return None
        idx: int | None = None
        items_xml = self._ensure_items_xml_loaded()
        if items_xml is not None and before.items:
            for i in range(len(before.items) - 1, -1, -1):
                it = before.items[i]
                meta = items_xml.get(int(it.id))
                k = (meta.kind if meta is not None else "").strip().lower()
                if k in ("wall", "door"):
                    idx = int(i)
                    break

        new_items = list(before.items)
        new_item = Item(id=int(door_id))
        if idx is None:
            new_items.append(new_item)
        else:
            new_items[int(idx)] = new_item

        new_tile: Tile | None = replace(before, items=new_items, modified=True)
        action = LabeledPaintAction(brush_id=0, label="Door Brush")
        action.record_tile_change(key, before, new_tile)
        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(
                type=ActionType.SWITCH_DOOR,
                action=action,
                label="Door Brush",
                details={"x": int(x), "y": int(y), "z": int(z), "placed": int(door_id), "kind": str(kind)},
            )
        )
        self._emit_tiles_changed({key})
        return action

    def switch_door_at(self, *, x: int, y: int, z: int) -> EditorAction | None:
        """Toggle the topmost door item on a tile (open <-> closed), undoable."""

        pairs = self._ensure_door_pairs_loaded()

        x, y, z = int(x), int(y), int(z)
        key: TileKey = (x, y, z)

        before = self.game_map.get_tile(x, y, z)
        if before is None or not before.items:
            return None

        # Find the topmost door-like item that has a known pair.
        idx: int | None = None
        door_spec = None
        for i in range(len(before.items) - 1, -1, -1):
            it = before.items[i]
            brush = self.brush_manager.get_brush_any(int(it.id))
            spec = brush.door_spec if brush is not None else None
            if spec is not None and spec.entry_for_item(int(it.id)) is not None:
                idx = int(i)
                door_spec = spec
                break
            if int(it.id) in pairs:
                idx = int(i)
                break

        if idx is None:
            return None

        old_item = before.items[idx]
        new_id = door_spec.toggle_item_id(int(old_item.id)) if door_spec is not None else pairs.get(int(old_item.id))
        if new_id is None or int(new_id) == int(old_item.id):
            return None

        new_items = list(before.items)
        new_items[idx] = Item(
            id=int(new_id),
            client_id=None,
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

        after: Tile | None = replace(before, items=new_items, modified=True)

        action = LabeledPaintAction(brush_id=0, label="Switch Door")
        action.record_tile_change(key, before, after)
        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(
                type=ActionType.SWITCH_DOOR,
                action=action,
                label="Switch Door",
                details={"x": int(x), "y": int(y), "z": int(z), "from": int(old_item.id), "to": int(new_id)},
            )
        )

        self._emit_tiles_changed({key})
        return action

    # === Configuration ===

    def set_automagic(self, enabled: bool) -> None:
        """Enable/disable auto-border pass on stroke finalize."""
        enabled = bool(enabled)
        self.auto_border_enabled = enabled
        self._gestures.set_auto_border_enabled(enabled)

    def set_merge_move(self, enabled: bool) -> None:
        """Enable/disable legacy MERGE_MOVE behavior for selection moves."""
        self.merge_move_enabled = bool(enabled)
        self._move.merge_move_enabled = bool(enabled)

    def set_borderize_drag(self, enabled: bool, *, threshold: int | None = None) -> None:
        """Enable/disable auto-border after selection drag moves."""
        self.borderize_drag_enabled = bool(enabled)
        if threshold is not None:
            self.borderize_drag_threshold = int(threshold)

    def set_merge_paste(self, enabled: bool) -> None:
        """Enable/disable legacy MERGE_PASTE behavior."""
        self.merge_paste_enabled = bool(enabled)

    def set_borderize_paste(self, enabled: bool, *, threshold: int | None = None) -> None:
        """Enable/disable legacy BORDERIZE_PASTE behavior."""
        self.borderize_paste_enabled = bool(enabled)
        if threshold is not None:
            self.borderize_paste_threshold = int(threshold)

    def set_selected_brush(self, server_id: int) -> None:
        """Set the currently selected brush."""
        sid = int(server_id)
        self._gestures.set_selected_brush(int(sid))
        self._push_recent_brush(int(sid))

    def _push_recent_brush(self, server_id: int) -> None:
        sid = int(server_id)
        if sid <= 0:
            return
        cur = list(self.recent_brushes)
        # Dedupe: remove existing occurrence.
        cur = [int(v) for v in cur if int(v) != int(sid)]
        cur.insert(0, int(sid))
        maxn = max(1, int(self.recent_brushes_max))
        self.recent_brushes = cur[:maxn]

    # === Tile state utilities ===

    def clear_modified_state(self) -> int:
        """Clear the runtime-only 'modified' flag from all tiles.

        Mirrors the legacy editor action that makes the map appear as if it was
        just opened. This is not persisted in OTBM.

        Returns:
            Number of tiles whose state changed.
        """

        changed: set[TileKey] = set()
        for key, tile in list(self.game_map.tiles.items()):
            if bool(getattr(tile, "modified", False)):
                self.game_map.tiles[key] = replace(tile, modified=False)
                changed.add(key)

        if changed:
            self._emit_tiles_changed(changed)
        return len(changed)

    # === Waypoints (map-level) ===

    def set_waypoint(self, *, name: str, x: int, y: int, z: int) -> EditorAction | None:
        """Create/update a waypoint to the given position (undoable)."""

        nm = str(name).strip()
        if not nm:
            return None

        before = self.game_map.waypoints.get(nm)
        after = Position(x=int(x), y=int(y), z=int(z))
        action: EditorAction = WaypointAction(name=nm, before=before, after=after)
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(SessionAction(type=ActionType.SET_WAYPOINT, action=action, label=action.describe()))
        # No tile keys changed, but UI overlays/history need refresh.
        self._emit_tiles_changed(set())
        return action

    def delete_waypoint(self, *, name: str) -> EditorAction | None:
        """Delete a waypoint by name (undoable)."""

        nm = str(name).strip()
        if not nm:
            return None

        before = self.game_map.waypoints.get(nm)
        if before is None:
            return None

        action: EditorAction = WaypointAction(name=nm, before=before, after=None)
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(SessionAction(type=ActionType.DELETE_WAYPOINT, action=action, label=action.describe()))
        self._emit_tiles_changed(set())
        return action

    # === Towns (map-level) ===

    def upsert_town(
        self,
        *,
        town_id: int,
        name: str,
        temple_x: int,
        temple_y: int,
        temple_z: int,
    ) -> EditorAction | None:
        """Create/update a town entry (undoable)."""

        tid = int(town_id)
        if tid < 1:
            return None

        nm = str(name).strip()
        if not nm:
            return None

        before = (self.game_map.towns or {}).get(tid)
        after = Town(
            id=tid,
            name=nm,
            temple_position=Position(x=int(temple_x), y=int(temple_y), z=int(temple_z)),
        )

        action: EditorAction = TownAction(town_id=tid, before=before, after=after)
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.UPSERT_TOWN, action=action, label=action.describe(), details={"town_id": tid})
        )
        self._emit_tiles_changed(set())
        return action

    def delete_town(self, *, town_id: int) -> EditorAction | None:
        """Delete a town by id (undoable)."""

        tid = int(town_id)
        before = (self.game_map.towns or {}).get(tid)
        if before is None:
            return None

        action: EditorAction = TownAction(town_id=tid, before=before, after=None)
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.DELETE_TOWN, action=action, label=action.describe(), details={"town_id": tid})
        )
        self._emit_tiles_changed(set())
        return action

    def set_town_temple_position(self, *, town_id: int, x: int, y: int, z: int) -> EditorAction | None:
        """Update temple position for an existing town (undoable)."""

        tid = int(town_id)
        before = (self.game_map.towns or {}).get(tid)
        if before is None:
            return None

        after = Town(id=tid, name=str(before.name), temple_position=Position(x=int(x), y=int(y), z=int(z)))
        action: EditorAction = TownAction(town_id=tid, before=before, after=after)
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(
                type=ActionType.SET_TOWN_TEMPLE, action=action, label=action.describe(), details={"town_id": tid}
            )
        )
        self._emit_tiles_changed(set())
        return action

    # === Houses (tile-level) ===

    def set_house_id_on_selection(self, *, house_id: int | None) -> PaintAction | None:
        """Set/clear house_id on all selected tiles (undoable)."""

        if self._gestures.is_active:
            self.cancel_gesture()

        keys = sorted(self._selection.get_selection_tiles())
        if not keys:
            return None

        hid = None if house_id is None else int(house_id)

        action = PaintAction(brush_id=0)
        affected: set[TileKey] = set()
        for key in keys:
            before = self.game_map.get_tile(*key)
            if before is None:
                # Legacy-ish: selection usually implies tile exists; skip empties.
                continue
            if (before.house_id is None and hid is None) or (
                before.house_id is not None and hid is not None and int(before.house_id) == int(hid)
            ):
                continue

            after: Tile | None = replace(before, house_id=hid, modified=True)
            if after is not None and _tile_is_truly_empty(after):
                after = None

            if before == after:
                continue
            action.record_tile_change(key, before, after)
            affected.add(key)

        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        label = "Clear House ID" if hid is None else f"Set House ID: {int(hid)}"
        self.action_queue.push(
            SessionAction(type=ActionType.SET_HOUSE_ID, action=action, label=label, details={"house_id": hid})
        )
        self._emit_tiles_changed(affected)
        return action

    # === Houses metadata (external XML) ===

    def upsert_house(
        self,
        *,
        house_id: int,
        name: str,
        townid: int,
        rent: int = 0,
        guildhall: bool = False,
        size: int = 0,
        clientid: int = 0,
        beds: int = 0,
    ) -> EditorAction | None:
        """Create/update a house definition in GameMap.houses (undoable)."""

        hid = int(house_id)
        if hid < 1:
            return None

        nm = str(name).strip()
        if not nm:
            return None

        tid = int(townid)
        if tid < 1:
            return None

        before = (self.game_map.houses or {}).get(hid)

        entry = None
        if before is not None:
            entry = before.entry

        header_before = self.game_map.header
        header_after = header_before
        if not str(getattr(header_before, "housefile", "") or "").strip():
            header_after = replace(header_before, housefile="houses.xml")

        after = House(
            id=hid,
            name=nm,
            entry=entry,
            rent=max(0, int(rent)),
            guildhall=bool(guildhall),
            townid=tid,
            size=max(0, int(size)),
            clientid=max(0, int(clientid)),
            beds=max(0, int(beds)),
        )

        action: EditorAction = HouseAction(
            house_id=hid,
            before=before,
            after=after,
            header_before=header_before,
            header_after=header_after,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(
                type=ActionType.UPSERT_HOUSE, action=action, label=action.describe(), details={"house_id": hid}
            )
        )
        self._emit_tiles_changed(set())
        return action

    def delete_house(self, *, house_id: int) -> EditorAction | None:
        """Delete a house definition by id (undoable)."""

        hid = int(house_id)
        before = (self.game_map.houses or {}).get(hid)
        if before is None:
            return None

        header_before = self.game_map.header
        header_after = header_before
        action: EditorAction = HouseAction(
            house_id=hid,
            before=before,
            after=None,
            header_before=header_before,
            header_after=header_after,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(
                type=ActionType.DELETE_HOUSE, action=action, label=action.describe(), details={"house_id": hid}
            )
        )
        self._emit_tiles_changed(set())
        return action

    def set_house_entry(self, *, house_id: int, x: int, y: int, z: int) -> EditorAction | None:
        """Set the house entry position (undoable)."""

        hid = int(house_id)
        before = (self.game_map.houses or {}).get(hid)
        if before is None:
            return None

        header_before = self.game_map.header
        header_after = header_before
        if not str(getattr(header_before, "housefile", "") or "").strip():
            header_after = replace(header_before, housefile="houses.xml")

        after = House(
            id=hid,
            name=str(before.name),
            entry=Position(x=int(x), y=int(y), z=int(z)),
            rent=int(before.rent),
            guildhall=bool(before.guildhall),
            townid=int(before.townid),
            size=int(before.size),
            clientid=int(before.clientid),
            beds=int(before.beds),
        )

        action: EditorAction = HouseEntryAction(
            house_id=hid,
            before=before,
            after=after,
            header_before=header_before,
            header_after=header_after,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(
                type=ActionType.SET_HOUSE_ENTRY, action=action, label=action.describe(), details={"house_id": hid}
            )
        )
        self._emit_tiles_changed(set())
        return action

    def clear_house_entry(self, *, house_id: int) -> EditorAction | None:
        """Clear the house entry position (undoable).

        Legacy stores missing entry as (0,0,0) in houses.xml.
        """

        hid = int(house_id)
        before = (self.game_map.houses or {}).get(hid)
        if before is None:
            return None

        header_before = self.game_map.header
        header_after = header_before
        if not str(getattr(header_before, "housefile", "") or "").strip():
            header_after = replace(header_before, housefile="houses.xml")

        after = House(
            id=hid,
            name=str(before.name),
            entry=None,
            rent=int(before.rent),
            guildhall=bool(before.guildhall),
            townid=int(before.townid),
            size=int(before.size),
            clientid=int(before.clientid),
            beds=int(before.beds),
        )

        action: EditorAction = HouseEntryAction(
            house_id=hid,
            before=before,
            after=after,
            header_before=header_before,
            header_after=header_after,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(
                type=ActionType.CLEAR_HOUSE_ENTRY,
                action=action,
                label=action.describe(),
                details={"house_id": hid},
            )
        )
        self._emit_tiles_changed(set())
        return action

    # === Zones metadata (external XML) ===

    def upsert_zone(self, *, zone_id: int, name: str) -> EditorAction | None:
        """Create/update a zone definition in GameMap.zones (undoable)."""

        zid = int(zone_id)
        if zid < 1:
            return None

        nm = str(name).strip()
        if not nm:
            return None

        before = (self.game_map.zones or {}).get(zid)

        header_before = self.game_map.header
        header_after = header_before
        if not str(getattr(header_before, "zonefile", "") or "").strip():
            header_after = replace(header_before, zonefile="zones.xml")

        after = Zone(id=zid, name=nm)

        action: EditorAction = ZoneAction(
            zone_id=zid,
            before=before,
            after=after,
            header_before=header_before,
            header_after=header_after,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.UPSERT_ZONE, action=action, label=action.describe(), details={"zone_id": zid})
        )
        self._emit_tiles_changed(set())
        return action

    def delete_zone(self, *, zone_id: int) -> EditorAction | None:
        """Delete a zone definition by id (undoable)."""

        zid = int(zone_id)
        before = (self.game_map.zones or {}).get(zid)
        if before is None:
            return None

        header_before = self.game_map.header
        header_after = header_before
        action: EditorAction = ZoneAction(
            zone_id=zid,
            before=before,
            after=None,
            header_before=header_before,
            header_after=header_after,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.DELETE_ZONE, action=action, label=action.describe(), details={"zone_id": zid})
        )
        self._emit_tiles_changed(set())
        return action

    # === Spawns (map-level, external XML) ===

    def set_monster_spawn_area(self, *, x: int, y: int, z: int, radius: int) -> EditorAction | None:
        """Create/update a monster spawn area at the given center (undoable)."""

        center = Position(x=int(x), y=int(y), z=int(z))
        r = int(radius)
        if r < 1:
            return None

        before_areas = tuple(self.game_map.monster_spawns)
        header_before = self.game_map.header
        header_after = header_before
        if not str(getattr(header_before, "spawnmonsterfile", "") or "").strip():
            header_after = replace(header_before, spawnmonsterfile="spawns.xml")

        after_list: list[MonsterSpawnArea] = []
        updated = False
        for area in before_areas:
            if area.center == center:
                after_list.append(MonsterSpawnArea(center=center, radius=r, monsters=area.monsters))
                updated = True
            else:
                after_list.append(area)
        if not updated:
            after_list.append(MonsterSpawnArea(center=center, radius=r, monsters=()))

        label = f"Set monster spawn: {int(center.x)},{int(center.y)},{int(center.z)} (r={int(r)})"
        action: EditorAction = MonsterSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_after,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.SET_MONSTER_SPAWN_AREA, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def delete_monster_spawn_area(self, *, x: int, y: int, z: int) -> EditorAction | None:
        """Delete a monster spawn area by its center (undoable)."""

        center = Position(x=int(x), y=int(y), z=int(z))
        before_areas = tuple(self.game_map.monster_spawns)
        header_before = self.game_map.header

        after_list = [a for a in before_areas if a.center != center]
        if len(after_list) == len(before_areas):
            return None

        label = f"Delete monster spawn: {int(center.x)},{int(center.y)},{int(center.z)}"
        action: EditorAction = MonsterSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.DELETE_MONSTER_SPAWN_AREA, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def set_monster_spawn_areas(self, *, positions: set[TileKey], radius: int) -> EditorAction | None:
        """Create/update monster spawn areas for multiple centers as one undoable action."""

        if not positions:
            return None

        r = int(radius)
        if r < 1:
            return None

        # Legacy-inspired canDraw: require ground for creation.
        centers: list[Position] = []
        for x, y, z in sorted({(int(a), int(b), int(c)) for (a, b, c) in positions}):
            t = self.game_map.get_tile(int(x), int(y), int(z))
            if t is None or t.ground is None:
                continue
            centers.append(Position(x=int(x), y=int(y), z=int(z)))
        if not centers:
            return None

        before_areas = tuple(self.game_map.monster_spawns)
        header_before = self.game_map.header
        header_after = header_before
        if not str(getattr(header_before, "spawnmonsterfile", "") or "").strip():
            header_after = replace(header_before, spawnmonsterfile="spawns.xml")

        # Preserve original ordering where possible; update matching centers, then append new.
        by_center = {a.center: a for a in before_areas}
        for c in centers:
            existing = by_center.get(c)
            if existing is None:
                by_center[c] = MonsterSpawnArea(center=c, radius=int(r), monsters=())
            else:
                by_center[c] = MonsterSpawnArea(center=c, radius=int(r), monsters=existing.monsters)

        updated_centers = set(centers)
        after_list: list[MonsterSpawnArea] = []
        existing_centers = {a.center for a in before_areas}
        for a in before_areas:
            if a.center in by_center:
                after_list.append(by_center[a.center])
            else:
                after_list.append(a)
        for c in sorted(updated_centers, key=lambda p: (int(p.z), int(p.y), int(p.x))):
            if c not in existing_centers:
                after_list.append(by_center[c])

        label = f"Set monster spawns (smear x{len(centers)}) (r={int(r)})"
        action: EditorAction = MonsterSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_after,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.SET_MONSTER_SPAWN_AREA, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def delete_monster_spawn_areas(self, *, positions: set[TileKey]) -> EditorAction | None:
        """Delete monster spawn areas for multiple centers as one undoable action."""

        if not positions:
            return None

        centers = {
            Position(x=int(x), y=int(y), z=int(z))
            for (x, y, z) in {(int(a), int(b), int(c)) for (a, b, c) in positions}
        }
        if not centers:
            return None

        before_areas = tuple(self.game_map.monster_spawns)
        header_before = self.game_map.header
        after_list = [a for a in before_areas if a.center not in centers]
        if len(after_list) == len(before_areas):
            return None

        label = f"Delete monster spawns (smear x{len(centers)})"
        action: EditorAction = MonsterSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.DELETE_MONSTER_SPAWN_AREA, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def set_npc_spawn_area(self, *, x: int, y: int, z: int, radius: int) -> EditorAction | None:
        """Create/update an NPC spawn area at the given center (undoable)."""

        center = Position(x=int(x), y=int(y), z=int(z))
        r = int(radius)
        if r < 1:
            return None

        before_areas = tuple(self.game_map.npc_spawns)
        header_before = self.game_map.header
        header_after = header_before
        if not str(getattr(header_before, "spawnnpcfile", "") or "").strip():
            header_after = replace(header_before, spawnnpcfile="npcspawns.xml")

        after_list: list[NpcSpawnArea] = []
        updated = False
        for area in before_areas:
            if area.center == center:
                after_list.append(NpcSpawnArea(center=center, radius=r, npcs=area.npcs))
                updated = True
            else:
                after_list.append(area)
        if not updated:
            after_list.append(NpcSpawnArea(center=center, radius=r, npcs=()))

        label = f"Set NPC spawn: {int(center.x)},{int(center.y)},{int(center.z)} (r={int(r)})"
        action: EditorAction = NpcSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_after,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.SET_NPC_SPAWN_AREA, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def delete_npc_spawn_area(self, *, x: int, y: int, z: int) -> EditorAction | None:
        """Delete an NPC spawn area by its center (undoable)."""

        center = Position(x=int(x), y=int(y), z=int(z))
        before_areas = tuple(self.game_map.npc_spawns)
        header_before = self.game_map.header

        after_list = [a for a in before_areas if a.center != center]
        if len(after_list) == len(before_areas):
            return None

        label = f"Delete NPC spawn: {int(center.x)},{int(center.y)},{int(center.z)}"
        action: EditorAction = NpcSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.DELETE_NPC_SPAWN_AREA, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def set_npc_spawn_areas(self, *, positions: set[TileKey], radius: int) -> EditorAction | None:
        """Create/update NPC spawn areas for multiple centers as one undoable action."""

        if not positions:
            return None

        r = int(radius)
        if r < 1:
            return None

        centers: list[Position] = []
        for x, y, z in sorted({(int(a), int(b), int(c)) for (a, b, c) in positions}):
            t = self.game_map.get_tile(int(x), int(y), int(z))
            if t is None or t.ground is None:
                continue
            centers.append(Position(x=int(x), y=int(y), z=int(z)))
        if not centers:
            return None

        before_areas = tuple(self.game_map.npc_spawns)
        header_before = self.game_map.header
        header_after = header_before
        if not str(getattr(header_before, "spawnnpcfile", "") or "").strip():
            header_after = replace(header_before, spawnnpcfile="npcspawns.xml")

        by_center = {a.center: a for a in before_areas}
        for c in centers:
            existing = by_center.get(c)
            if existing is None:
                by_center[c] = NpcSpawnArea(center=c, radius=int(r), npcs=())
            else:
                by_center[c] = NpcSpawnArea(center=c, radius=int(r), npcs=existing.npcs)

        updated_centers = set(centers)
        after_list: list[NpcSpawnArea] = []
        existing_centers = {a.center for a in before_areas}
        for a in before_areas:
            if a.center in by_center:
                after_list.append(by_center[a.center])
            else:
                after_list.append(a)
        for c in sorted(updated_centers, key=lambda p: (int(p.z), int(p.y), int(p.x))):
            if c not in existing_centers:
                after_list.append(by_center[c])

        label = f"Set NPC spawns (smear x{len(centers)}) (r={int(r)})"
        action: EditorAction = NpcSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_after,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.SET_NPC_SPAWN_AREA, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def delete_npc_spawn_areas(self, *, positions: set[TileKey]) -> EditorAction | None:
        """Delete NPC spawn areas for multiple centers as one undoable action."""

        if not positions:
            return None

        centers = {
            Position(x=int(x), y=int(y), z=int(z))
            for (x, y, z) in {(int(a), int(b), int(c)) for (a, b, c) in positions}
        }
        if not centers:
            return None

        before_areas = tuple(self.game_map.npc_spawns)
        header_before = self.game_map.header
        after_list = [a for a in before_areas if a.center not in centers]
        if len(after_list) == len(before_areas):
            return None

        label = f"Delete NPC spawns (smear x{len(centers)})"
        action: EditorAction = NpcSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.DELETE_NPC_SPAWN_AREA, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def _find_monster_spawn_area_for(self, *, x: int, y: int, z: int) -> tuple[int, MonsterSpawnArea, int, int] | None:
        """Return (index, area, dx, dy) for the nearest area covering (x,y,z)."""

        tx, ty, tz = int(x), int(y), int(z)
        best: tuple[int, int, MonsterSpawnArea, int, int] | None = None  # (score, idx, area, dx, dy)
        for idx, area in enumerate(self.game_map.monster_spawns):
            if int(area.center.z) != tz:
                continue
            dx = int(tx - int(area.center.x))
            dy = int(ty - int(area.center.y))
            if max(abs(dx), abs(dy)) > int(area.radius):
                continue
            score = abs(dx) + abs(dy)
            if best is None or score < best[0]:
                best = (score, idx, area, dx, dy)
        if best is None:
            return None
        _, idx, area, dx, dy = best
        return int(idx), area, int(dx), int(dy)

    def _find_npc_spawn_area_for(self, *, x: int, y: int, z: int) -> tuple[int, NpcSpawnArea, int, int] | None:
        """Return (index, area, dx, dy) for the nearest area covering (x,y,z)."""

        tx, ty, tz = int(x), int(y), int(z)
        best: tuple[int, int, NpcSpawnArea, int, int] | None = None  # (score, idx, area, dx, dy)
        for idx, area in enumerate(self.game_map.npc_spawns):
            if int(area.center.z) != tz:
                continue
            dx = int(tx - int(area.center.x))
            dy = int(ty - int(area.center.y))
            if max(abs(dx), abs(dy)) > int(area.radius):
                continue
            score = abs(dx) + abs(dy)
            if best is None or score < best[0]:
                best = (score, idx, area, dx, dy)
        if best is None:
            return None
        _, idx, area, dx, dy = best
        return int(idx), area, int(dx), int(dy)

    def add_monster_spawn_entry(
        self,
        *,
        x: int,
        y: int,
        z: int,
        name: str,
        spawntime: int = 0,
        direction: int | None = None,
        weight: int | None = None,
    ) -> EditorAction | None:
        """Add a monster spawn entry at the cursor tile (undoable).

        The entry is added to the nearest monster spawn area that covers the tile.
        """

        nm = str(name).strip()
        if not nm:
            return None

        found = self._find_monster_spawn_area_for(x=int(x), y=int(y), z=int(z))
        if found is None:
            return None
        idx, area, dx, dy = found

        before_areas = tuple(self.game_map.monster_spawns)
        header_before = self.game_map.header

        new_entry = MonsterSpawnEntry(
            name=nm,
            dx=int(dx),
            dy=int(dy),
            spawntime=int(spawntime),
            direction=None if direction is None else int(direction),
            weight=None if weight is None else int(weight),
        )
        after_monsters = tuple(area.monsters) + (new_entry,)
        new_radius = max(int(area.radius), abs(int(dx)), abs(int(dy)))
        updated_area = MonsterSpawnArea(center=area.center, radius=int(new_radius), monsters=after_monsters)

        after_list = list(before_areas)
        after_list[int(idx)] = updated_area

        label = f"Add monster: {nm} @ {int(x)},{int(y)},{int(z)}"
        action: EditorAction = MonsterSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.ADD_MONSTER_SPAWN_ENTRY, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def add_monster_spawn_entries(
        self, *, positions: set[TileKey], name: str, spawntime: int = 0
    ) -> EditorAction | None:
        """Add monster spawn entries for multiple tiles as one undoable action."""

        nm = str(name).strip()
        if not nm or not positions:
            return None

        before_areas = tuple(self.game_map.monster_spawns)
        header_before = self.game_map.header
        after_list = list(before_areas)
        changed = False

        # Work on per-area mutable monsters.
        monsters_by_idx: dict[int, list[MonsterSpawnEntry]] = {}
        radius_by_idx: dict[int, int] = {}

        for x, y, z in sorted({(int(a), int(b), int(c)) for (a, b, c) in positions}):
            # Mirror MVP canDraw: require existing tile for adds.
            if self.game_map.get_tile(int(x), int(y), int(z)) is None:
                continue

            found = self._find_monster_spawn_area_for(x=int(x), y=int(y), z=int(z))
            if found is None:
                continue
            idx, area, dx, dy = found

            buf = monsters_by_idx.get(int(idx))
            if buf is None:
                buf = list(area.monsters)
                monsters_by_idx[int(idx)] = buf
                radius_by_idx[int(idx)] = int(area.radius)

            buf.append(
                MonsterSpawnEntry(
                    name=str(nm),
                    dx=int(dx),
                    dy=int(dy),
                    spawntime=int(spawntime),
                    direction=None,
                    weight=None,
                )
            )
            radius_by_idx[int(idx)] = max(int(radius_by_idx[int(idx)]), abs(int(dx)), abs(int(dy)))
            changed = True

        if not changed:
            return None

        for idx, mons in monsters_by_idx.items():
            area = before_areas[int(idx)]
            r = int(radius_by_idx.get(int(idx), int(area.radius)))
            after_list[int(idx)] = MonsterSpawnArea(center=area.center, radius=int(r), monsters=tuple(mons))

        label = f"Add monster: {nm} (smear x{len(positions)})"
        action: EditorAction = MonsterSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.ADD_MONSTER_SPAWN_ENTRY, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def delete_monster_spawn_entry_at_cursor(
        self, *, x: int, y: int, z: int, name: str | None = None
    ) -> EditorAction | None:
        """Delete one monster spawn entry at the cursor tile (undoable).

        If name is provided, deletes the first matching name at that tile.
        Otherwise deletes the last entry at that tile.
        """

        found = self._find_monster_spawn_area_for(x=int(x), y=int(y), z=int(z))
        if found is None:
            return None
        idx, area, dx, dy = found

        target_name = None if name is None else str(name).strip()

        candidates = [e for e in area.monsters if int(e.dx) == int(dx) and int(e.dy) == int(dy)]
        if not candidates:
            return None

        to_remove: MonsterSpawnEntry | None = None
        if target_name:
            for e in reversed(candidates):
                if str(e.name) == target_name:
                    to_remove = e
                    break
        if to_remove is None:
            to_remove = candidates[-1]

        new_monsters = list(area.monsters)
        removed = False
        for i in range(len(new_monsters) - 1, -1, -1):
            if new_monsters[i] == to_remove:
                new_monsters.pop(i)
                removed = True
                break
        if not removed:
            return None

        updated_area = MonsterSpawnArea(center=area.center, radius=int(area.radius), monsters=tuple(new_monsters))
        before_areas = tuple(self.game_map.monster_spawns)
        header_before = self.game_map.header
        after_list = list(before_areas)
        after_list[int(idx)] = updated_area

        label = f"Delete monster: {to_remove.name} @ {int(x)},{int(y)},{int(z)}"
        action: EditorAction = MonsterSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.DELETE_MONSTER_SPAWN_ENTRY, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def delete_monster_spawn_entries(self, *, positions: set[TileKey], name: str | None = None) -> EditorAction | None:
        """Delete one monster spawn entry per tile for multiple tiles as one undoable action."""

        if not positions:
            return None

        target_name = None if name is None else str(name).strip()

        before_areas = tuple(self.game_map.monster_spawns)
        header_before = self.game_map.header
        after_list = list(before_areas)

        monsters_by_idx: dict[int, list[MonsterSpawnEntry]] = {}
        changed = False

        for x, y, z in sorted({(int(a), int(b), int(c)) for (a, b, c) in positions}):
            found = self._find_monster_spawn_area_for(x=int(x), y=int(y), z=int(z))
            if found is None:
                continue
            idx, area, dx, dy = found

            buf = monsters_by_idx.get(int(idx))
            if buf is None:
                buf = list(area.monsters)
                monsters_by_idx[int(idx)] = buf

            candidates_idx = [
                i
                for i, e in enumerate(buf)
                if int(getattr(e, "dx", 0)) == int(dx) and int(getattr(e, "dy", 0)) == int(dy)
            ]
            if not candidates_idx:
                continue

            remove_i: int | None = None
            if target_name:
                for i in reversed(candidates_idx):
                    if str(getattr(buf[i], "name", "")) == target_name:
                        remove_i = int(i)
                        break
            if remove_i is None:
                remove_i = int(candidates_idx[-1])

            buf.pop(int(remove_i))
            changed = True

        if not changed:
            return None

        for idx, mons in monsters_by_idx.items():
            area = before_areas[int(idx)]
            after_list[int(idx)] = MonsterSpawnArea(center=area.center, radius=int(area.radius), monsters=tuple(mons))

        label = f"Delete monster: {target_name or '*'} (smear x{len(positions)})"
        action: EditorAction = MonsterSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.DELETE_MONSTER_SPAWN_ENTRY, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def add_npc_spawn_entry(
        self,
        *,
        x: int,
        y: int,
        z: int,
        name: str,
        spawntime: int = 0,
        direction: int | None = None,
    ) -> EditorAction | None:
        """Add an NPC spawn entry at the cursor tile (undoable)."""

        nm = str(name).strip()
        if not nm:
            return None

        found = self._find_npc_spawn_area_for(x=int(x), y=int(y), z=int(z))
        if found is None:
            return None
        idx, area, dx, dy = found

        before_areas = tuple(self.game_map.npc_spawns)
        header_before = self.game_map.header

        new_entry = NpcSpawnEntry(
            name=nm,
            dx=int(dx),
            dy=int(dy),
            spawntime=int(spawntime),
            direction=None if direction is None else int(direction),
        )
        after_npcs = tuple(area.npcs) + (new_entry,)
        new_radius = max(int(area.radius), abs(int(dx)), abs(int(dy)))
        updated_area = NpcSpawnArea(center=area.center, radius=int(new_radius), npcs=after_npcs)

        after_list = list(before_areas)
        after_list[int(idx)] = updated_area

        label = f"Add NPC: {nm} @ {int(x)},{int(y)},{int(z)}"
        action: EditorAction = NpcSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.ADD_NPC_SPAWN_ENTRY, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def add_npc_spawn_entries(self, *, positions: set[TileKey], name: str, spawntime: int = 0) -> EditorAction | None:
        """Add NPC spawn entries for multiple tiles as one undoable action."""

        nm = str(name).strip()
        if not nm or not positions:
            return None

        before_areas = tuple(self.game_map.npc_spawns)
        header_before = self.game_map.header
        after_list = list(before_areas)
        changed = False

        npcs_by_idx: dict[int, list[NpcSpawnEntry]] = {}
        radius_by_idx: dict[int, int] = {}

        for x, y, z in sorted({(int(a), int(b), int(c)) for (a, b, c) in positions}):
            if self.game_map.get_tile(int(x), int(y), int(z)) is None:
                continue

            found = self._find_npc_spawn_area_for(x=int(x), y=int(y), z=int(z))
            if found is None:
                continue
            idx, area, dx, dy = found

            buf = npcs_by_idx.get(int(idx))
            if buf is None:
                buf = list(area.npcs)
                npcs_by_idx[int(idx)] = buf
                radius_by_idx[int(idx)] = int(area.radius)

            buf.append(
                NpcSpawnEntry(
                    name=str(nm),
                    dx=int(dx),
                    dy=int(dy),
                    spawntime=int(spawntime),
                    direction=None,
                )
            )
            radius_by_idx[int(idx)] = max(int(radius_by_idx[int(idx)]), abs(int(dx)), abs(int(dy)))
            changed = True

        if not changed:
            return None

        for idx, npcs in npcs_by_idx.items():
            area = before_areas[int(idx)]
            r = int(radius_by_idx.get(int(idx), int(area.radius)))
            after_list[int(idx)] = NpcSpawnArea(center=area.center, radius=int(r), npcs=tuple(npcs))

        label = f"Add NPC: {nm} (smear x{len(positions)})"
        action: EditorAction = NpcSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.ADD_NPC_SPAWN_ENTRY, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def delete_npc_spawn_entry_at_cursor(
        self, *, x: int, y: int, z: int, name: str | None = None
    ) -> EditorAction | None:
        """Delete one NPC spawn entry at the cursor tile (undoable)."""

        found = self._find_npc_spawn_area_for(x=int(x), y=int(y), z=int(z))
        if found is None:
            return None
        idx, area, dx, dy = found

        target_name = None if name is None else str(name).strip()
        candidates = [e for e in area.npcs if int(e.dx) == int(dx) and int(e.dy) == int(dy)]
        if not candidates:
            return None

        to_remove: NpcSpawnEntry | None = None
        if target_name:
            for e in reversed(candidates):
                if str(e.name) == target_name:
                    to_remove = e
                    break
        if to_remove is None:
            to_remove = candidates[-1]

        new_npcs = list(area.npcs)
        removed = False
        for i in range(len(new_npcs) - 1, -1, -1):
            if new_npcs[i] == to_remove:
                new_npcs.pop(i)
                removed = True
                break
        if not removed:
            return None

        updated_area = NpcSpawnArea(center=area.center, radius=int(area.radius), npcs=tuple(new_npcs))
        before_areas = tuple(self.game_map.npc_spawns)
        header_before = self.game_map.header
        after_list = list(before_areas)
        after_list[int(idx)] = updated_area

        label = f"Delete NPC: {to_remove.name} @ {int(x)},{int(y)},{int(z)}"
        action: EditorAction = NpcSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.DELETE_NPC_SPAWN_ENTRY, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def delete_npc_spawn_entries(self, *, positions: set[TileKey], name: str | None = None) -> EditorAction | None:
        """Delete one NPC spawn entry per tile for multiple tiles as one undoable action."""

        if not positions:
            return None

        target_name = None if name is None else str(name).strip()

        before_areas = tuple(self.game_map.npc_spawns)
        header_before = self.game_map.header
        after_list = list(before_areas)

        npcs_by_idx: dict[int, list[NpcSpawnEntry]] = {}
        changed = False

        for x, y, z in sorted({(int(a), int(b), int(c)) for (a, b, c) in positions}):
            found = self._find_npc_spawn_area_for(x=int(x), y=int(y), z=int(z))
            if found is None:
                continue
            idx, area, dx, dy = found

            buf = npcs_by_idx.get(int(idx))
            if buf is None:
                buf = list(area.npcs)
                npcs_by_idx[int(idx)] = buf

            candidates_idx = [
                i
                for i, e in enumerate(buf)
                if int(getattr(e, "dx", 0)) == int(dx) and int(getattr(e, "dy", 0)) == int(dy)
            ]
            if not candidates_idx:
                continue

            remove_i: int | None = None
            if target_name:
                for i in reversed(candidates_idx):
                    if str(getattr(buf[i], "name", "")) == target_name:
                        remove_i = int(i)
                        break
            if remove_i is None:
                remove_i = int(candidates_idx[-1])

            buf.pop(int(remove_i))
            changed = True

        if not changed:
            return None

        for idx, npcs in npcs_by_idx.items():
            area = before_areas[int(idx)]
            after_list[int(idx)] = NpcSpawnArea(center=area.center, radius=int(area.radius), npcs=tuple(npcs))

        label = f"Delete NPC: {target_name or '*'} (smear x{len(positions)})"
        action: EditorAction = NpcSpawnsAction(
            before=before_areas,
            after=tuple(after_list),
            header_before=header_before,
            header_after=header_before,
            label=label,
        )
        if not action.has_changes():
            return None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.DELETE_NPC_SPAWN_ENTRY, action=action, label=action.describe())
        )
        self._emit_tiles_changed(set())
        return action

    def clear_invalid_tiles(self, *, selection_only: bool = False) -> tuple[int, PaintAction | None]:
        """Remove invalid (placeholder/unknown) items from tiles.

        This mirrors the legacy "Clean map" action (removing invalid items),
        but uses a deterministic definition without depending on an items DB:
        - Items with id==0 (loader placeholder)
        - Items with raw_unknown_id set (loader replacement)

        Args:
            selection_only: If True, only affects the current selection.

        Returns:
            (removed_items_count, action)
        """

        if self._gestures.is_active:
            self.cancel_gesture()

        if bool(selection_only):
            keys = sorted(self._selection.get_selection_tiles())
        else:
            keys = sorted(self.game_map.tiles.keys())

        action = PaintAction(brush_id=0)
        removed_total = 0
        affected: set[TileKey] = set()

        for key in keys:
            before = self.game_map.get_tile(*key)
            if before is None:
                continue

            removed_here = 0

            # Ground
            new_ground = before.ground
            if new_ground is not None:
                cleaned_ground, r = _clean_item_tree(new_ground)
                removed_here += int(r)
                new_ground = cleaned_ground

            # Stack items
            new_items: list[Item] = []
            items_changed = False
            for it in before.items:
                cleaned, r = _clean_item_tree(it)
                removed_here += int(r)
                if cleaned is None:
                    items_changed = True
                    continue
                if cleaned is not it:
                    items_changed = True
                new_items.append(cleaned)

            if removed_here == 0 and not items_changed and new_ground is before.ground:
                continue

            after: Tile | None = replace(before, ground=new_ground, items=new_items, modified=True)
            if after is not None and _tile_is_truly_empty(after):
                after = None

            action.record_tile_change(key, before, after)
            removed_total += int(removed_here)
            affected.add(key)

        if not action.has_changes():
            return 0, None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(
                type=ActionType.CLEAR_INVALID_TILES,
                action=action,
                label="Clear Invalid Tiles",
                details={"removed": int(removed_total), "selection_only": bool(selection_only)},
            )
        )

        if affected:
            self._emit_tiles_changed(affected)
        return int(removed_total), action

    def randomize_selection(self) -> tuple[int, PaintAction | None]:
        """Randomize the ground tiles in the selected area.

        Notes:
        - This only performs changes when a ground brush declares `randomize_ids`
          in `brushes.json` (optional extension; empty by default).

        Returns:
            (tiles_changed, action)
        """

        selection = self._selection.get_selection_tiles()
        if not selection:
            return 0, None

        return self._randomize_positions(selection, action_type=ActionType.RANDOMIZE_SELECTION)

    def randomize_map(self) -> tuple[int, PaintAction | None]:
        """Randomize the ground tiles in the entire map.

        Notes:
        - This only performs changes when a ground brush declares `randomize_ids`
          in `brushes.json` (optional extension; empty by default).

        Returns:
            (tiles_changed, action)
        """

        positions = set(self.game_map.tiles.keys())
        return self._randomize_positions(positions, action_type=ActionType.RANDOMIZE_MAP)

    def _randomize_positions(
        self, positions: set[TileKey], *, action_type: ActionType
    ) -> tuple[int, PaintAction | None]:
        if self._gestures.is_active:
            self.cancel_gesture()

        action = PaintAction(brush_id=0)
        affected: set[TileKey] = set()
        changed_tiles = 0

        for key in sorted(positions):
            before = self.game_map.get_tile(*key)
            if before is None or before.ground is None:
                continue

            brush = self.brush_manager.get_brush_any(int(before.ground.id))
            if brush is None or str(getattr(brush, "brush_type", "")) != "ground":
                continue

            candidates = [int(v) for v in getattr(brush, "randomize_ids", ()) if int(v) != 0]
            # Fall back to server_id as a candidate if the list exists but omitted it.
            if candidates and int(brush.server_id) not in candidates:
                candidates.append(int(brush.server_id))

            if len(candidates) < 2:
                continue

            current_id = int(before.ground.id)
            # Try to pick something different.
            new_id = int(current_id)
            for _ in range(4):
                new_id = int(random.choice(candidates))
                if new_id != current_id:
                    break

            if new_id == current_id:
                continue

            new_ground = replace(before.ground, id=int(new_id), raw_unknown_id=None)
            after = replace(before, ground=new_ground, modified=True)
            if before == after:
                continue

            action.record_tile_change(key, before, after)
            affected.add(key)
            changed_tiles += 1

        if not action.has_changes():
            return 0, None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(
                type=action_type,
                action=action,
                label="Randomize",
                details={"changed_tiles": int(changed_tiles)},
            )
        )

        if affected:
            self._emit_tiles_changed(affected)
        return int(changed_tiles), action

    # === Selection API (delegated) ===

    def has_selection(self) -> bool:
        return self._selection.has_selection()

    def get_selection_tiles(self) -> set[TileKey]:
        return self._selection.get_selection_tiles()

    def clear_selection(self) -> None:
        self._selection.clear_selection()

    def toggle_select_tile(self, *, x: int, y: int, z: int) -> None:
        self._selection.toggle_select_tile(x=x, y=y, z=z)

    def set_single_selection(self, *, x: int, y: int, z: int) -> None:
        self._selection.set_single_selection(x=x, y=y, z=z)

    def begin_box_selection(self, *, x: int, y: int, z: int) -> None:
        self._selection.begin_box_selection(x=x, y=y, z=z)

    def update_box_selection(self, *, x: int, y: int, z: int) -> None:
        self._selection.update_box_selection(x=x, y=y, z=z)

    def finish_box_selection(
        self,
        *,
        toggle_if_single: bool = False,
        mode: SelectionApplyMode | None = None,
        visible_floors: list[int] | None = None,
    ) -> None:
        self._selection.finish_box_selection(
            toggle_if_single=toggle_if_single,
            mode=SelectionApplyMode.ADD if mode is None else mode,
            visible_floors=visible_floors,
        )

    def cancel_box_selection(self) -> None:
        self._selection.cancel_box_selection()

    def get_selection_box(self) -> tuple[TileKey, TileKey] | None:
        return self._selection.get_selection_box()

    def set_selection_depth_mode(self, mode: SelectionDepthMode | str) -> None:
        if not isinstance(mode, SelectionDepthMode):
            mode = SelectionDepthMode(str(mode))
        self._selection.selection_mode = mode

    def get_selection_depth_mode(self) -> SelectionDepthMode:
        return self._selection.selection_mode

    def apply_lasso_selection(
        self,
        *,
        tiles: list[TileKey],
        mode: SelectionApplyMode | None = None,
        visible_floors: list[int] | None = None,
    ) -> None:
        """Apply a lasso selection to the current selection set."""
        if not tiles:
            return

        base_z = int(tiles[0][2])
        depth_mode = self.get_selection_depth_mode()

        floors: list[int] = [base_z]
        visible_sorted = sorted({int(z) for z in visible_floors}) if visible_floors else [base_z]

        if depth_mode is SelectionDepthMode.CURRENT:
            floors = [base_z]
        elif depth_mode is SelectionDepthMode.VISIBLE:
            floors = list(visible_sorted)
        elif depth_mode in (SelectionDepthMode.LOWER, SelectionDepthMode.COMPENSATE):
            floors = list(range(base_z, max(visible_sorted) + 1))

        selection_tiles: set[TileKey] = set()
        for x, y, _z in tiles:
            for z in floors:
                tx, ty = int(x), int(y)
                if depth_mode is SelectionDepthMode.COMPENSATE:
                    tx, ty = apply_compensation_offset(x=tx, y=ty, z=int(z), base_z=base_z)
                if not (0 <= tx < int(self.game_map.header.width) and 0 <= ty < int(self.game_map.header.height)):
                    continue
                t = self.game_map.get_tile(int(tx), int(ty), int(z))
                if not tile_is_nonempty(t):
                    continue
                selection_tiles.add((int(tx), int(ty), int(z)))

        if not isinstance(mode, SelectionApplyMode):
            mode = SelectionApplyMode.ADD if mode is None else SelectionApplyMode(str(mode))

        current = self._selection.get_selection_tiles()
        if mode is SelectionApplyMode.REPLACE:
            new_sel = set(selection_tiles)
        elif mode is SelectionApplyMode.SUBTRACT:
            new_sel = set(current)
            new_sel.difference_update(selection_tiles)
        elif mode is SelectionApplyMode.TOGGLE:
            new_sel = set(current)
            new_sel.symmetric_difference_update(selection_tiles)
        else:
            new_sel = set(current)
            new_sel.update(selection_tiles)

        self._selection.set_selection(new_sel)

    # === Clipboard API ===

    def can_paste(self) -> bool:
        return self._clipboard.can_paste()

    def copy_selection(self, client_version: str | None = None) -> bool:
        """Copy selected tiles into the internal buffer and system clipboard."""

        # Prepare name lookup
        def name_lookup(server_id: int) -> str | None:
            xml = self._ensure_items_xml_loaded()
            if xml:
                it = xml.get(server_id)
                if it:
                    return it.name
            return None

        selection_tiles = self._selection.get_selection_tiles()
        if not self._clipboard.copy_tiles(selection_tiles):
            return False

        tiles: list[Tile] = []
        for key in sorted(selection_tiles):
            t = self.game_map.get_tile(*key)
            if t is None or not tile_is_nonempty(t):
                continue
            tiles.append(t)

        if not tiles:
            return False

        # Determine origin version
        origin_x = min(int(t.x) for t in tiles)
        origin_y = min(int(t.y) for t in tiles)
        origin_z = min(int(t.z) for t in tiles)

        system_clipboard = SystemClipboardManager.instance()
        system_clipboard.copy_tiles(tiles, (origin_x, origin_y, origin_z), name_lookup=name_lookup)
        if client_version:
            system_clipboard.to_system_clipboard(client_version)
        else:
            system_clipboard.to_system_clipboard()

        return True

    def import_from_system_clipboard(self, target_version: str | None = None) -> bool:
        """Try to import content from the system clipboard."""

        def name_resolver(name: str) -> int | None:
            xml = self._ensure_items_xml_loaded()
            if xml:
                return xml.get_server_id_by_name(name)
            return None

        system_clipboard = SystemClipboardManager.instance()
        if not system_clipboard.from_system_clipboard(
            target_version=target_version,
            name_resolver=name_resolver if target_version else None,
        ):
            return False

        entry = system_clipboard.get_current()
        if entry is None:
            return False

        result = tiles_from_entry(entry)
        if result is None:
            return False

        tiles, origin = result
        return self._clipboard.load_tiles(tiles, origin)

    def cut_selection(self, client_version: str | None = None) -> PaintAction | None:
        """Cut selection into buffer and remove from map (atomic)."""
        if not self.copy_selection(client_version):
            return None
        return self.delete_selection(borderize=bool(self.auto_border_enabled))

    def delete_selection(self, *, borderize: bool = True) -> PaintAction | None:
        """Delete selected tiles (atomic)."""
        selection = self._selection.get_selection_tiles()
        if not selection:
            return None

        if self._gestures.is_active:
            self.cancel_gesture()

        action = PaintAction(brush_id=0)
        affected: set[TileKey] = set()
        for key in sorted(selection):
            before = self.game_map.get_tile(*key)
            if not tile_is_nonempty(before):
                continue
            action.record_tile_change(key, before, None)
            affected.add(key)

        if not action.has_changes():
            return None

        action.redo(self.game_map)

        if bool(borderize) and bool(self.auto_border_enabled):
            self._run_auto_border_on_area(affected, action)

        self.history.commit_action(action)
        self.action_queue.push(SessionAction(type=ActionType.DELETE_SELECTION, action=action, label="Delete Selection"))
        self._selection.clear_selection()
        self._emit_tiles_changed(affected)
        return action

    def paste_buffer(self, *, x: int, y: int, z: int) -> PaintAction | None:
        """Paste current buffer at (x,y,z) (atomic)."""
        if not self.can_paste():
            return None

        if self._gestures.is_active:
            self.cancel_gesture()

        paste_result = self._clipboard.calculate_paste_tiles(
            int(x),
            int(y),
            int(z),
            merge_enabled=self.merge_paste_enabled,
        )
        if paste_result is None:
            return None

        action = PaintAction(brush_id=0)
        affected: set[TileKey] = set()
        new_sel: set[TileKey] = set()

        for dst, (before, after) in paste_result.items():
            action.record_tile_change(dst, before, after)
            affected.add(dst)
            if tile_is_nonempty(after):
                new_sel.add(dst)

        if not action.has_changes():
            return None

        action.redo(self.game_map)

        if (
            bool(self.auto_border_enabled)
            and bool(self.borderize_paste_enabled)
            and len(self._clipboard.get_buffer_tiles()) < int(self.borderize_paste_threshold)
        ):
            self._run_auto_border_on_area(affected, action)

        self.history.commit_action(action)
        self.action_queue.push(SessionAction(type=ActionType.PASTE, action=action, label="Paste"))
        self._selection.set_selection(new_sel)
        self._emit_tiles_changed(affected)
        return action

    # === Gesture API (delegated) ===

    def mouse_down(
        self,
        *,
        x: int,
        y: int,
        z: int,
        selected_server_id: int | None = None,
        alt: bool = False,
    ) -> None:
        sid = int(selected_server_id) if selected_server_id is not None else int(self._gestures.active_brush_id)

        # House Exit brush (MVP): one-shot operation that sets/clears the entry
        # of the selected house, and does not start a stroke.
        bd = self.brush_manager.get_brush(int(sid)) if int(sid) > 0 else None
        if bd is not None and str(getattr(bd, "brush_type", "")).strip().lower() == "house_exit":
            if self._gestures.is_active:
                self.cancel_gesture()

            if not (VIRTUAL_HOUSE_EXIT_BASE <= int(sid) < VIRTUAL_HOUSE_EXIT_BASE + VIRTUAL_HOUSE_EXIT_MAX):
                raise ValueError("Invalid House Exit brush id")
            house_id = int(int(sid) - int(VIRTUAL_HOUSE_EXIT_BASE))
            if house_id <= 0:
                raise ValueError("Invalid house id for House Exit")

            self._pending_house_exit = (int(house_id), int(x), int(y), int(z), bool(alt))
            return

        # Waypoint brush (MVP): one-shot operation that moves/deletes an existing
        # waypoint, and does not start a stroke.
        if bd is not None and str(getattr(bd, "brush_type", "")).strip().lower() == "waypoint":
            if self._gestures.is_active:
                self.cancel_gesture()

            if not (VIRTUAL_WAYPOINT_BASE <= int(sid) < VIRTUAL_WAYPOINT_BASE + VIRTUAL_WAYPOINT_MAX):
                raise ValueError("Invalid Waypoint brush id")

            name = self._resolve_waypoint_name_for_virtual_id(int(sid))
            if not name:
                # Waypoint list likely changed since selection; ignore.
                self._pending_waypoint = None
                return

            self._pending_waypoint = (str(name), int(x), int(y), int(z), bool(alt))
            return

        # Spawn area tools (MVP): one-shot. In legacy these are drag tools with size.
        # In this port we map brush_size to spawn radius and apply once per gesture.
        btype = str(getattr(bd, "brush_type", "") or "").strip().lower() if bd is not None else ""
        if int(sid) in {int(VIRTUAL_SPAWN_MONSTER_TOOL_ID), int(VIRTUAL_SPAWN_NPC_TOOL_ID)} or btype in {
            "spawn_monster",
            "spawn_npc",
        }:
            if self._gestures.is_active:
                self.cancel_gesture()
            kind = "monster" if int(sid) == int(VIRTUAL_SPAWN_MONSTER_TOOL_ID) or btype == "spawn_monster" else "npc"
            radius = max(1, int(self.brush_size))

            if str(kind) == "monster":

                def _commit_spawn(pos: set[TileKey], was_alt: bool) -> EditorAction | None:
                    if bool(was_alt):
                        return self.delete_monster_spawn_areas(positions=pos)
                    return self.set_monster_spawn_areas(positions=pos, radius=int(radius))
            else:

                def _commit_spawn(pos: set[TileKey], was_alt: bool) -> EditorAction | None:
                    if bool(was_alt):
                        return self.delete_npc_spawn_areas(positions=pos)
                    return self.set_npc_spawn_areas(positions=pos, radius=int(radius))

            self._pending_batched_positions = BatchedPositionsGesture(
                positions={(int(x), int(y), int(z))},
                alt=bool(alt),
                commit=_commit_spawn,
            )
            return

        # Creature tools (MVP): smear/drag. We collect visited tiles while the mouse
        # button is down and apply a single undoable action on mouse_up.
        if bd is not None and str(getattr(bd, "brush_type", "")).strip().lower() in {"monster", "npc"}:
            if self._gestures.is_active:
                self.cancel_gesture()

            if str(getattr(bd, "brush_type", "")).strip().lower() == "monster":
                if not (VIRTUAL_MONSTER_BASE <= int(sid) < VIRTUAL_MONSTER_BASE + VIRTUAL_MONSTER_MAX):
                    raise ValueError("Invalid Monster brush id")
                nm = monster_name_for_virtual_id(int(sid))
                if not nm:
                    self._pending_batched_positions = None
                    return

                def _commit_creature(pos: set[TileKey], was_alt: bool) -> EditorAction | None:
                    if not bool(was_alt):
                        pos = {p for p in pos if self.game_map.get_tile(int(p[0]), int(p[1]), int(p[2])) is not None}
                        if not pos:
                            return None
                        return self.add_monster_spawn_entries(positions=pos, name=str(nm), spawntime=0)
                    return self.delete_monster_spawn_entries(positions=pos, name=str(nm))

                self._pending_batched_positions = BatchedPositionsGesture(
                    positions={(int(x), int(y), int(z))},
                    alt=bool(alt),
                    commit=_commit_creature,
                )
                return

            if str(getattr(bd, "brush_type", "")).strip().lower() == "npc":
                if not (VIRTUAL_NPC_BASE <= int(sid) < VIRTUAL_NPC_BASE + VIRTUAL_NPC_MAX):
                    raise ValueError("Invalid NPC brush id")
                nm = npc_name_for_virtual_id(int(sid))
                if not nm:
                    self._pending_batched_positions = None
                    return

                def _commit_creature(pos: set[TileKey], was_alt: bool) -> EditorAction | None:
                    if not bool(was_alt):
                        pos = {p for p in pos if self.game_map.get_tile(int(p[0]), int(p[1]), int(p[2])) is not None}
                        if not pos:
                            return None
                        return self.add_npc_spawn_entries(positions=pos, name=str(nm), spawntime=0)
                    return self.delete_npc_spawn_entries(positions=pos, name=str(nm))

                self._pending_batched_positions = BatchedPositionsGesture(
                    positions={(int(x), int(y), int(z))},
                    alt=bool(alt),
                    commit=_commit_creature,
                )
                return

        # DoorBrush (MVP): one-shot place/toggle; Alt removes the topmost door.
        if bd is not None and str(getattr(bd, "brush_type", "")).strip().lower() == "door":
            if self._gestures.is_active:
                self.cancel_gesture()

            door_kind = self._door_kind_for_tool_id(int(sid))
            if not door_kind:
                self._pending_batched_positions = None
                return

            def _commit_door(pos: set[TileKey], was_alt: bool) -> EditorAction | None:
                return self.apply_door_brush_to_positions(positions=pos, door_kind=str(door_kind), alt=bool(was_alt))

            self._pending_batched_positions = BatchedPositionsGesture(
                positions={(int(x), int(y), int(z))},
                alt=bool(alt),
                commit=_commit_door,
            )
            return

        self._pending_house_exit = None
        self._pending_waypoint = None
        self._pending_batched_positions = None
        self._gestures.mouse_down(x=x, y=y, z=z, selected_server_id=selected_server_id, alt=alt)

    def mouse_move(self, *, x: int, y: int, z: int, alt: bool = False) -> None:
        # House Exit brush does not drag/smear.
        if self._pending_house_exit is not None:
            return
        # Waypoint brush does not drag/smear.
        if self._pending_waypoint is not None:
            return
        if self._pending_batched_positions is not None:
            self._pending_batched_positions.add(x=int(x), y=int(y), z=int(z))
            return
        self._gestures.mouse_move(x=x, y=y, z=z, alt=alt)

    def mark_autoborder_position(self, *, x: int, y: int, z: int) -> None:
        self._gestures.mark_autoborder_position(x=x, y=y, z=z)

    def mouse_up(self) -> EditorAction | None:
        if self._pending_house_exit is not None:
            house_id, x, y, z, was_alt = self._pending_house_exit
            self._pending_house_exit = None

            # Match legacy HouseExitBrush::canDraw (MVP): require a ground tile
            # and disallow painting onto house tiles.
            if not bool(was_alt):
                t = self.game_map.get_tile(int(x), int(y), int(z))
                if t is None or t.ground is None:
                    return None
                if getattr(t, "house_id", None) is not None:
                    return None

            if bool(was_alt):
                return self.clear_house_entry(house_id=int(house_id))
            return self.set_house_entry(house_id=int(house_id), x=int(x), y=int(y), z=int(z))

        if self._pending_waypoint is not None:
            name, x, y, z, was_alt = self._pending_waypoint
            self._pending_waypoint = None

            if not bool(was_alt):
                # Match legacy WaypointBrush::canDraw (MVP): require an existing tile.
                t = self.game_map.get_tile(int(x), int(y), int(z))
                if t is None:
                    return None

            if bool(was_alt):
                return self.delete_waypoint(name=str(name))
            return self.set_waypoint(name=str(name), x=int(x), y=int(y), z=int(z))

        if self._pending_batched_positions is not None:
            g = self._pending_batched_positions
            self._pending_batched_positions = None
            return g.finish()

        action = self._gestures.mouse_up()
        if action is not None:
            self.action_queue.push(SessionAction(type=ActionType.PAINT, action=action, label="Paint"))
            self._emit_tiles_changed(self._changed_keys_for_action(action))
        return action

    def fill_ground(self, *, x: int, y: int, z: int) -> PaintAction | None:
        """Flood-fill ground within a bounded area."""
        action = self._gestures.fill_ground(x=x, y=y, z=z)
        if action is not None:
            self.action_queue.push(SessionAction(type=ActionType.PAINT, action=action, label="Fill"))
            self._emit_tiles_changed(self._changed_keys_for_action(action))
        return action

    def cancel_gesture(self) -> None:
        self._gestures.cancel()

    # === Movement API ===

    def move_selection(self, *, move_x: int, move_y: int, move_z: int = 0) -> PaintAction | None:
        """Move selected tiles."""
        selection = self._selection.get_selection_tiles()
        if not selection:
            return None

        if self._gestures.is_active:
            self.cancel_gesture()

        action, affected, new_sel = self._move.move_selection(
            selection,
            move_x=move_x,
            move_y=move_y,
            move_z=move_z,
        )

        if action is None:
            return None

        # Apply move
        action.redo(self.game_map)

        # Auto-border if enabled
        if (
            bool(self.auto_border_enabled)
            and bool(self.borderize_drag_enabled)
            and len(selection) < int(self.borderize_drag_threshold)
        ):
            self._run_auto_border_on_area(affected, action)

        self.history.commit_action(action)
        self.action_queue.push(SessionAction(type=ActionType.MOVE_SELECTION, action=action, label="Move Selection"))
        self._selection.set_selection(new_sel)
        self._emit_tiles_changed(affected)
        return action

    # === Borderize API ===

    def borderize_selection(self) -> PaintAction | None:
        """Re-run auto-border in the selected area (legacy Ctrl+B)."""
        selection = self._selection.get_selection_tiles()
        if not selection:
            return None

        if self._gestures.is_active:
            self.cancel_gesture()

        from ..auto_border import AutoBorderProcessor

        expanded = self._move.calculate_expanded_area(selection)
        action = PaintAction(brush_id=0)
        proc = AutoBorderProcessor(self.game_map, self.brush_manager, change_recorder=action)

        brush_ids = self._move.collect_brush_ids(expanded)
        for bid in sorted(brush_ids):
            proc.update_positions(expanded, int(bid))

        if not action.has_changes():
            return None

        self.history.commit_action(action)
        self.action_queue.push(
            SessionAction(type=ActionType.BORDERIZE_SELECTION, action=action, label="Borderize Selection")
        )
        self._emit_tiles_changed(expanded)
        return action

    # === Item Operations ===

    def replace_items(
        self,
        *,
        from_id: int,
        to_id: int,
        selection_only: bool = False,
        limit: int = 500,
    ) -> tuple[int, bool, PaintAction | None]:
        """Replace items by server id across the map."""
        selection_tiles = self.get_selection_tiles() if bool(selection_only) else None
        return self._replace_items_with_tiles(
            from_id=int(from_id),
            to_id=int(to_id),
            selection_tiles=set(selection_tiles) if selection_tiles is not None else None,
            limit=int(limit),
        )

    def replace_items_on_tiles(
        self,
        *,
        from_id: int,
        to_id: int,
        tiles: set[TileKey],
        limit: int = 500,
    ) -> tuple[int, bool, PaintAction | None]:
        """Replace items by server id on an explicit tile set."""
        return self._replace_items_with_tiles(
            from_id=int(from_id),
            to_id=int(to_id),
            selection_tiles=set(tiles),
            limit=int(limit),
        )

    def _replace_items_with_tiles(
        self,
        *,
        from_id: int,
        to_id: int,
        selection_tiles: set[TileKey] | None,
        limit: int,
    ) -> tuple[int, bool, PaintAction | None]:
        from_id_i = int(from_id)
        to_id_i = int(to_id)
        if from_id_i <= 0 or to_id_i <= 0 or from_id_i == to_id_i:
            return 0, False, None

        if self._gestures.is_active:
            self.cancel_gesture()

        changed_tiles, summary = replace_items_in_map(
            self.game_map,
            from_id=from_id_i,
            to_id=to_id_i,
            limit=int(limit),
            selection_only=selection_tiles is not None,
            selection_tiles=set(selection_tiles) if selection_tiles is not None else None,
        )

        if not changed_tiles:
            return int(summary.replaced), bool(summary.exceeded_limit), None

        action = PaintAction(brush_id=0)
        affected: set[TileKey] = set()
        for key, after in changed_tiles.items():
            before = self.game_map.get_tile(*key)
            if before == after:
                continue
            action.record_tile_change(key, before, after)
            affected.add(key)

        if not action.has_changes():
            return int(summary.replaced), bool(summary.exceeded_limit), None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(SessionAction(type=ActionType.REPLACE_ITEMS, action=action, label="Replace Items"))
        self._emit_tiles_changed(affected)
        return int(summary.replaced), bool(summary.exceeded_limit), action

    def remove_items(
        self,
        *,
        server_id: int,
        selection_only: bool = False,
    ) -> tuple[int, PaintAction | None]:
        """Remove items by server id."""
        sid = int(server_id)
        if sid <= 0:
            return 0, None

        if self._gestures.is_active:
            self.cancel_gesture()

        selection_tiles = self.get_selection_tiles() if bool(selection_only) else None
        changed_tiles, summary = remove_items_in_map(
            self.game_map,
            server_id=sid,
            selection_only=bool(selection_only),
            selection_tiles=set(selection_tiles) if selection_tiles is not None else None,
        )

        if not changed_tiles:
            return int(summary.removed), None

        action = PaintAction(brush_id=0)
        affected: set[TileKey] = set()
        for key, after in changed_tiles.items():
            before = self.game_map.get_tile(*key)
            if before == after:
                continue
            action.record_tile_change(key, before, after)
            affected.add(key)

        if not action.has_changes():
            return int(summary.removed), None

        action.redo(self.game_map)
        self.history.commit_action(action)
        self.action_queue.push(SessionAction(type=ActionType.REMOVE_ITEMS, action=action, label="Remove Items"))
        self._emit_tiles_changed(affected)
        return int(summary.removed), action

    # === Undo/Redo ===

    def undo(self) -> EditorAction | None:
        action = self.history.undo(self.game_map)
        if action is not None:
            self._emit_tiles_changed(self._changed_keys_for_action(action))
        return action

    def redo(self) -> EditorAction | None:
        action = self.history.redo(self.game_map)
        if action is not None:
            self._emit_tiles_changed(self._changed_keys_for_action(action))
        return action

    # === Internal helpers ===

    def _run_auto_border_on_area(self, affected: set[TileKey], action: PaintAction) -> None:
        """Run auto-border processing on an area."""
        from ..auto_border import AutoBorderProcessor

        expanded = self._move.calculate_expanded_area(affected)
        proc = AutoBorderProcessor(self.game_map, self.brush_manager, change_recorder=action)
        brush_ids = self._move.collect_brush_ids(expanded)
        for bid in sorted(brush_ids):
            proc.update_positions(expanded, int(bid))

    def _emit_tiles_changed(self, changed: set[TileKey], *, broadcast: bool = True) -> None:
        cb = self.on_tiles_changed
        if cb is not None:
            cb(set(changed))

        # Live Editing Broadcast
        if broadcast and (self._live_client or self._live_server):
            for x, y, z in changed:
                self._live_action_queue.mark_dirty(int(x), int(y), int(z))
            self._live_action_queue.broadcast_dirty()

    def set_live_chat_callback(self, callback: Callable[[int, str, str], None] | None) -> None:
        self._on_live_chat = callback

    def set_live_client_list_callback(self, callback: Callable[[list[dict[str, object]]], None] | None) -> None:
        self._on_live_client_list = callback

    def set_live_cursor_callback(self, callback: Callable[[int, int, int, int], None] | None) -> None:
        self._on_live_cursor = callback

    def _broadcast_live_tiles(self, dirty_list: object) -> None:
        if not (self._live_client or self._live_server):
            return
        positions = list(getattr(dirty_list, "positions", []) or [])
        if not positions:
            return
        tiles: list[Tile] = []
        for x, y, z in positions:
            tile = self.game_map.get_tile(int(x), int(y), int(z))
            if tile is None:
                tile = Tile(x=int(x), y=int(y), z=int(z))
            tiles.append(tile)
        payload = encode_tile_update(tiles)
        if self._live_client is not None:
            self._live_client.send_packet(PacketType.TILE_UPDATE, payload)
        if self._live_server is not None:
            self._live_server.broadcast(PacketType.TILE_UPDATE, payload)

    def _live_map_provider(self, x_min: int, y_min: int, x_max: int, y_max: int, z: int) -> list[Tile]:
        tiles: list[Tile] = []
        for (tx, ty, tz), tile in (self.game_map.tiles or {}).items():
            if int(tz) != int(z):
                continue
            if int(tx) < int(x_min) or int(tx) > int(x_max):
                continue
            if int(ty) < int(y_min) or int(ty) > int(y_max):
                continue
            tiles.append(tile)
        return tiles

    def connect_live(self, host: str, port: int, *, name: str = "", password: str = "") -> bool:
        """Connect to a Live Editing server."""
        if self._live_client is not None:
            self.disconnect_live()

        self._live_client = LiveClient(host=host, port=port)
        if name:
            self._live_client.set_name(str(name))
        if password:
            self._live_client.set_password(str(password))
        self._live_action_queue.set_live_client(self._live_client)
        self._live_sync_started = False
        return self._live_client.connect()

    def disconnect_live(self) -> None:
        """Disconnect from Live Editing server."""
        if self._live_client:
            self._live_client.disconnect()
            self._live_client = None
        self._live_action_queue.set_live_client(None)
        self._live_sync_started = False

    def start_live_server(
        self, *, host: str = "127.0.0.1", port: int = 7171, name: str = "", password: str = ""
    ) -> bool:
        """Start hosting a Live Editing server."""
        if self._live_server is not None:
            return True
        self._live_server = LiveServer(host=host, port=port)
        if name:
            self._live_server.set_name(str(name))
        if password:
            self._live_server.set_password(str(password))
        self._live_server.set_map_provider(self._live_map_provider)
        self._live_action_queue.set_live_server(self._live_server)
        ok = self._live_server.start()
        if not ok:
            self._live_action_queue.set_live_server(None)
            self._live_server = None
        return ok

    def stop_live_server(self) -> None:
        """Stop hosting a Live Editing server."""
        if self._live_server is None:
            return
        self._live_server.stop()
        self._live_server = None
        self._live_action_queue.set_live_server(None)

    def kick_live_client(self, client_id: int, *, reason: str = "Disconnected by host") -> bool:
        server = self._live_server
        if server is None:
            return False
        return bool(server.kick_client(int(client_id), reason=str(reason)))

    def ban_live_client(self, client_id: int, *, reason: str = "Banned by host") -> bool:
        server = self._live_server
        if server is None:
            return False
        return bool(server.ban_client(int(client_id), reason=str(reason)))

    def send_live_chat(self, message: str) -> bool:
        if self._live_client is None:
            return False
        return bool(self._live_client.send_chat_message(str(message)))

    def send_live_cursor_update(self, *, x: int, y: int, z: int, throttle_ms: int = 50) -> None:
        if self._live_client is None:
            return
        now = time.monotonic()
        if (now - float(self._live_cursor_last_sent)) < (int(throttle_ms) / 1000.0):
            return
        self._live_cursor_last_sent = now
        self._live_client.send_cursor_update(int(x), int(y), int(z))

    def get_live_cursor_overlays(self) -> list[dict[str, object]]:
        overlays: list[dict[str, object]] = []
        for client_id, (x, y, z) in self._live_cursors.items():
            if self._live_client and self._live_client.client_id == int(client_id):
                continue
            info = self._live_clients.get(int(client_id), {})
            name = str(info.get("name", "")) if isinstance(info, dict) else ""
            color = info.get("color", (255, 255, 255)) if isinstance(info, dict) else (255, 255, 255)
            overlays.append(
                {
                    "client_id": int(client_id),
                    "x": int(x),
                    "y": int(y),
                    "z": int(z),
                    "name": name or f"#{int(client_id)}",
                    "color": color,
                }
            )
        return overlays

    def _apply_live_tiles(self, tiles: list[dict[str, Any]]) -> set[TileKey]:
        changed: set[TileKey] = set()
        for raw in tiles:
            if not raw:
                continue
            x = int(raw.get("x", 0))
            y = int(raw.get("y", 0))
            z = int(raw.get("z", 0))
            items: list[Item] = []
            for entry in list(raw.get("items", []) or []):
                try:
                    item_id = int(entry.get("id", 0))
                except Exception:
                    continue
                if item_id <= 0:
                    continue
                subtype_val = entry.get("subtype", None)
                subtype = int(subtype_val) if subtype_val is not None else None
                items.append(Item(id=item_id, subtype=subtype))

            ground_id = int(raw.get("ground_id", 0))
            ground = Item(id=ground_id) if ground_id > 0 else None
            house_id = raw.get("house_id", None)
            house = int(house_id) if house_id is not None and int(house_id) > 0 else None
            flags = int(raw.get("flags", 0))

            tile = Tile(
                x=int(x),
                y=int(y),
                z=int(z),
                ground=ground,
                items=list(items),
                house_id=house,
                map_flags=flags,
            )

            if _tile_is_truly_empty(tile):
                self.game_map.delete_tile(int(x), int(y), int(z))
            else:
                self.game_map.set_tile(tile)
            changed.add((int(x), int(y), int(z)))
        return changed

    @staticmethod
    def _decode_live_positions(payload: bytes) -> list[TileKey]:
        if len(payload) == 5:
            x = int.from_bytes(payload[0:2], "little", signed=False)
            y = int.from_bytes(payload[2:4], "little", signed=False)
            z = int(payload[4])
            return [(int(x), int(y), int(z))]
        positions: list[TileKey] = []
        for pos in decode_tile_positions(payload):
            try:
                positions.append((int(pos[0]), int(pos[1]), int(pos[2])))
            except Exception:
                continue
        return positions

    def _handle_live_client_packet(self, pkt_type: int, payload: bytes) -> None:
        """Handle a single packet from the live client connection."""
        if int(pkt_type) == int(PacketType.LOGIN_SUCCESS):
            if self._live_client:
                if len(payload) >= 4:
                    self._live_client.client_id = int.from_bytes(payload[0:4], "little", signed=False)
                self._live_client.state = ConnectionState.AUTHENTICATED
                if not self._live_sync_started:
                    self._live_sync_started = True
                    self.game_map.tiles.clear()
                    width = max(1, int(self.game_map.header.width))
                    height = max(1, int(self.game_map.header.height))
                    for z in range(0, 16):
                        self._live_client.request_map(
                            x_min=0,
                            y_min=0,
                            x_max=width - 1,
                            y_max=height - 1,
                            z=int(z),
                        )
        elif int(pkt_type) == int(PacketType.LOGIN_ERROR) or int(pkt_type) == int(PacketType.KICK):
            if self._live_client:
                self._live_client.set_last_error(payload.decode("utf-8", errors="ignore"))
            self.disconnect_live()
        elif int(pkt_type) == int(PacketType.CLIENT_LIST):
            clients = decode_client_list(payload)
            self._live_clients = {int(c["client_id"]): dict(c) for c in clients}
            if self._on_live_client_list:
                self._on_live_client_list(list(clients))
        elif int(pkt_type) == int(PacketType.MESSAGE):
            client_id, name, message = decode_chat(payload)
            if self._on_live_chat:
                self._on_live_chat(int(client_id), str(name), str(message))
        elif int(pkt_type) == int(PacketType.CURSOR_UPDATE):
            client_id, x, y, z = decode_cursor(payload)
            self._live_cursors[int(client_id)] = (int(x), int(y), int(z))
            if self._on_live_cursor:
                self._on_live_cursor(int(client_id), int(x), int(y), int(z))
        elif int(pkt_type) == int(PacketType.TILE_UPDATE):
            tiles, ok = decode_tile_update(payload)
            if ok and tiles:
                changed = self._apply_live_tiles(tiles)
                if changed:
                    self._emit_tiles_changed(changed, broadcast=False)
            else:
                positions = self._decode_live_positions(payload)
                if positions:
                    self._emit_tiles_changed(set(positions), broadcast=False)
        elif int(pkt_type) == int(PacketType.MAP_CHUNK):
            chunk = decode_map_chunk(payload)
            tiles = chunk.get("tiles", [])
            changed = self._apply_live_tiles(list(tiles))
            if changed:
                self._emit_tiles_changed(changed, broadcast=False)

    def _handle_live_server_packet(self, pkt_type: int, payload: bytes) -> None:
        """Handle a single packet from the live server connection."""
        if int(pkt_type) == int(PacketType.MESSAGE):
            client_id, name, message = decode_chat(payload)
            if self._on_live_chat:
                self._on_live_chat(int(client_id), str(name), str(message))
        elif int(pkt_type) == int(PacketType.CLIENT_LIST):
            clients = decode_client_list(payload)
            self._live_clients = {int(c["client_id"]): dict(c) for c in clients}
            if self._on_live_client_list:
                self._on_live_client_list(list(clients))
        elif int(pkt_type) == int(PacketType.CURSOR_UPDATE):
            client_id, x, y, z = decode_cursor(payload)
            self._live_cursors[int(client_id)] = (int(x), int(y), int(z))
            if self._on_live_cursor:
                self._on_live_cursor(int(client_id), int(x), int(y), int(z))
        elif int(pkt_type) == int(PacketType.TILE_UPDATE):
            tiles, ok = decode_tile_update(payload)
            if ok and tiles:
                changed = self._apply_live_tiles(tiles)
                if changed:
                    self._emit_tiles_changed(changed, broadcast=False)
            else:
                positions = self._decode_live_positions(payload)
                if positions:
                    self._emit_tiles_changed(set(positions), broadcast=False)

    def process_live_events(self) -> int:
        """Poll incoming packets from Live Client and apply them.

        Returns:
            Number of packets processed.
        """
        if not self._live_client and not self._live_server:
            return 0

        count = 0
        if self._live_client is not None:
            while True:
                if self._live_client is None:
                    break
                pkt = self._live_client.pop_packet()
                if not pkt:
                    break
                pkt_type, payload = pkt
                self._handle_live_client_packet(int(pkt_type), payload)
                count += 1

        if self._live_server is not None:
            while True:
                if self._live_server is None:
                    break
                pkt = self._live_server.pop_packet()
                if not pkt:
                    break
                pkt_type, payload = pkt
                self._handle_live_server_packet(int(pkt_type), payload)
                count += 1

        return count
    @staticmethod
    def _changed_keys_for_action(action: EditorAction) -> set[TileKey]:
        try:
            before = getattr(action, "tiles_before", None)
            after = getattr(action, "tiles_after", None)
            if isinstance(before, dict) and isinstance(after, dict):
                keys: set[TileKey] = set(before.keys())
                keys.update(after.keys())
                return keys
        except Exception:
            pass
        return set()
