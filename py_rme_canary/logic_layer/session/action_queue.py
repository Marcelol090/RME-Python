from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from enum import Enum

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.logic_layer.transactional_brush import EditorAction


class ActionType(str, Enum):
    PAINT = "paint"
    DELETE_SELECTION = "delete_selection"
    PASTE = "paste"
    MOVE_SELECTION = "move_selection"
    BORDERIZE_SELECTION = "borderize_selection"
    REPLACE_ITEMS = "replace_items"
    REMOVE_ITEMS = "remove_items"
    CLEAR_INVALID_TILES = "clear_invalid_tiles"
    CLEAR_MODIFIED_STATE = "clear_modified_state"
    RANDOMIZE_SELECTION = "randomize_selection"
    RANDOMIZE_MAP = "randomize_map"
    SET_WAYPOINT = "set_waypoint"
    DELETE_WAYPOINT = "delete_waypoint"
    SET_HOUSE_ID = "set_house_id"
    UPSERT_HOUSE = "upsert_house"
    DELETE_HOUSE = "delete_house"
    SET_HOUSE_ENTRY = "set_house_entry"
    CLEAR_HOUSE_ENTRY = "clear_house_entry"
    UPSERT_ZONE = "upsert_zone"
    DELETE_ZONE = "delete_zone"
    SET_MONSTER_SPAWN_AREA = "set_monster_spawn_area"
    DELETE_MONSTER_SPAWN_AREA = "delete_monster_spawn_area"
    SET_NPC_SPAWN_AREA = "set_npc_spawn_area"
    DELETE_NPC_SPAWN_AREA = "delete_npc_spawn_area"
    ADD_MONSTER_SPAWN_ENTRY = "add_monster_spawn_entry"
    DELETE_MONSTER_SPAWN_ENTRY = "delete_monster_spawn_entry"
    ADD_NPC_SPAWN_ENTRY = "add_npc_spawn_entry"
    DELETE_NPC_SPAWN_ENTRY = "delete_npc_spawn_entry"
    UPSERT_TOWN = "upsert_town"
    DELETE_TOWN = "delete_town"
    SET_TOWN_TEMPLE = "set_town_temple"
    SWITCH_DOOR = "switch_door"


@dataclass(frozen=True, slots=True)
class SessionAction:
    type: ActionType
    action: EditorAction
    label: str = ""
    details: dict[str, object] | None = None
    timestamp: float = 0.0


@dataclass(frozen=True, slots=True)
class CompositeAction(EditorAction):
    """Represents a merged action for queue grouping."""

    actions: tuple[EditorAction, ...]
    label: str = "Action"

    def has_changes(self) -> bool:
        return any(action.has_changes() for action in self.actions)

    def undo(self, game_map: GameMap) -> None:
        for action in reversed(self.actions):
            action.undo(game_map)

    def redo(self, game_map: GameMap) -> None:
        for action in self.actions:
            action.redo(game_map)

    def describe(self) -> str:
        if self.label:
            return str(self.label)
        if self.actions:
            return self.actions[-1].describe()
        return "Action"


DEFAULT_STACKING_DELAY_SECONDS = 2

DEFAULT_LABELS: dict[ActionType, str] = {
    ActionType.PAINT: "Paint",
    ActionType.DELETE_SELECTION: "Delete Selection",
    ActionType.PASTE: "Paste",
    ActionType.MOVE_SELECTION: "Move Selection",
    ActionType.BORDERIZE_SELECTION: "Borderize Selection",
    ActionType.REPLACE_ITEMS: "Replace Items",
    ActionType.REMOVE_ITEMS: "Remove Items",
    ActionType.CLEAR_INVALID_TILES: "Clear Invalid Tiles",
    ActionType.CLEAR_MODIFIED_STATE: "Clear Modified State",
    ActionType.RANDOMIZE_SELECTION: "Randomize Selection",
    ActionType.RANDOMIZE_MAP: "Randomize Map",
    ActionType.SET_WAYPOINT: "Set Waypoint",
    ActionType.DELETE_WAYPOINT: "Delete Waypoint",
    ActionType.SET_HOUSE_ID: "Set House Id",
    ActionType.UPSERT_HOUSE: "Upsert House",
    ActionType.DELETE_HOUSE: "Delete House",
    ActionType.SET_HOUSE_ENTRY: "Set House Entry",
    ActionType.CLEAR_HOUSE_ENTRY: "Clear House Entry",
    ActionType.UPSERT_ZONE: "Upsert Zone",
    ActionType.DELETE_ZONE: "Delete Zone",
    ActionType.SET_MONSTER_SPAWN_AREA: "Set Monster Spawn Area",
    ActionType.DELETE_MONSTER_SPAWN_AREA: "Delete Monster Spawn Area",
    ActionType.SET_NPC_SPAWN_AREA: "Set Npc Spawn Area",
    ActionType.DELETE_NPC_SPAWN_AREA: "Delete Npc Spawn Area",
    ActionType.ADD_MONSTER_SPAWN_ENTRY: "Add Monster Spawn Entry",
    ActionType.DELETE_MONSTER_SPAWN_ENTRY: "Delete Monster Spawn Entry",
    ActionType.ADD_NPC_SPAWN_ENTRY: "Add Npc Spawn Entry",
    ActionType.DELETE_NPC_SPAWN_ENTRY: "Delete Npc Spawn Entry",
    ActionType.UPSERT_TOWN: "Upsert Town",
    ActionType.DELETE_TOWN: "Delete Town",
    ActionType.SET_TOWN_TEMPLE: "Set Town Temple",
    ActionType.SWITCH_DOOR: "Switch Door",
}

DEFAULT_STACKING_DELAYS: dict[ActionType, int] = {
    ActionType.PAINT: DEFAULT_STACKING_DELAY_SECONDS,
    ActionType.MOVE_SELECTION: DEFAULT_STACKING_DELAY_SECONDS,
    ActionType.BORDERIZE_SELECTION: DEFAULT_STACKING_DELAY_SECONDS,
    ActionType.RANDOMIZE_SELECTION: DEFAULT_STACKING_DELAY_SECONDS,
    ActionType.RANDOMIZE_MAP: DEFAULT_STACKING_DELAY_SECONDS,
    ActionType.DELETE_SELECTION: DEFAULT_STACKING_DELAY_SECONDS,
    ActionType.PASTE: DEFAULT_STACKING_DELAY_SECONDS,
    ActionType.REPLACE_ITEMS: DEFAULT_STACKING_DELAY_SECONDS,
    ActionType.REMOVE_ITEMS: DEFAULT_STACKING_DELAY_SECONDS,
}


def _label_for_type(action_type: ActionType) -> str:
    label = DEFAULT_LABELS.get(action_type)
    if label:
        return label
    raw = str(action_type.value or "")
    return raw.replace("_", " ").title() if raw else "Action"


def _merge_actions(left: EditorAction, right: EditorAction, *, label: str) -> CompositeAction:
    left_actions = left.actions if isinstance(left, CompositeAction) else (left,)
    right_actions = right.actions if isinstance(right, CompositeAction) else (right,)
    return CompositeAction(actions=tuple(left_actions + right_actions), label=label)


@dataclass(slots=True)
class SessionActionQueue:
    """Small, local-only action queue.

    This mirrors the legacy notion of an action queue/types, and provides a
    deterministic place to later hook network replication.
    """

    items: list[SessionAction] = field(default_factory=list)
    group_actions: bool = True
    clock: Callable[[], float] = time.time

    def _stacking_delay(self, action_type: ActionType) -> int:
        return int(DEFAULT_STACKING_DELAYS.get(action_type, 0))

    def push(
        self,
        entry: SessionAction,
        *,
        stacking_delay: int | None = None,
        group_actions: bool | None = None,
    ) -> None:
        delay = self._stacking_delay(entry.type) if stacking_delay is None else int(stacking_delay)
        group = self.group_actions if group_actions is None else bool(group_actions)
        now = float(self.clock())
        label = entry.label or _label_for_type(entry.type)
        entry = replace(entry, label=label, timestamp=now)

        if group and delay > 0 and self.items:
            last = self.items[-1]
            if last.type == entry.type and (now - float(delay)) < float(last.timestamp):
                merged_label = last.label or entry.label
                merged_details = last.details if last.details is not None else entry.details
                merged_action = _merge_actions(last.action, entry.action, label=merged_label)
                self.items[-1] = SessionAction(
                    type=last.type,
                    action=merged_action,
                    label=merged_label,
                    details=merged_details,
                    timestamp=now,
                )
                return

        self.items.append(entry)

    def generate_labels(self) -> None:
        if not self.items:
            return
        out: list[SessionAction] = []
        for entry in self.items:
            if entry.label:
                out.append(entry)
                continue
            out.append(replace(entry, label=_label_for_type(entry.type)))
        self.items = out

    def reset_timer(self) -> None:
        if not self.items:
            return
        last = self.items[-1]
        self.items[-1] = replace(last, timestamp=0.0)

    def clear(self) -> None:
        self.items.clear()

    def latest(self) -> SessionAction | None:
        if not self.items:
            return None
        return self.items[-1]
