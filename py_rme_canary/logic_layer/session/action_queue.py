from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

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


@dataclass(slots=True)
class SessionActionQueue:
    """Small, local-only action queue.

    This mirrors the legacy notion of an action queue/types, and provides a
    deterministic place to later hook network replication.
    """

    items: list[SessionAction] = field(default_factory=list)

    def push(self, entry: SessionAction) -> None:
        self.items.append(entry)

    def clear(self) -> None:
        self.items.clear()

    def latest(self) -> SessionAction | None:
        if not self.items:
            return None
        return self.items[-1]
