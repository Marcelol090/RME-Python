from __future__ import annotations

import json
import logging
import os
import re
import sys
import zlib
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from importlib import resources
from pathlib import Path

from py_rme_canary.core.data.door import DoorType
from py_rme_canary.core.io.creatures_xml import load_monster_names, load_npc_names
from py_rme_canary.core.io.xml.safe import Element
from py_rme_canary.core.io.xml.safe import safe_etree as ET
from py_rme_canary.logic_layer.borders.border_friends import FRIEND_ALL
from py_rme_canary.logic_layer.borders.border_groups import BorderGroupRegistry
from py_rme_canary.logic_layer.borders.ground_equivalents import GroundEquivalentRegistry

logger = logging.getLogger(__name__)


# Virtual (non-item) brushes for metadata painting.
# These IDs are intentionally far above typical client item ids to avoid collisions.
VIRTUAL_DOODAD_BASE = 800_000
VIRTUAL_DOODAD_MAX = 100_000
VIRTUAL_FLAG_BASE = 900_000
VIRTUAL_FLAG_BITS = 64
VIRTUAL_ZONE_BASE = 910_000
VIRTUAL_ZONE_MAX = 256
VIRTUAL_HOUSE_BASE = 920_000
VIRTUAL_HOUSE_MAX = 65_535
# House Exit is separate from the House tile painter range.
# Must not overlap VIRTUAL_HOUSE_BASE..VIRTUAL_HOUSE_BASE+VIRTUAL_HOUSE_MAX
# nor any other virtual ranges.
VIRTUAL_HOUSE_EXIT_BASE = 1_000_000
VIRTUAL_HOUSE_EXIT_MAX = 65_535

# Waypoint brush (metadata-only) uses a virtual id range so we can expose existing
# waypoints as palette entries (legacy WaypointBrush does not paint tiles).
# Must not overlap any other virtual ranges.
VIRTUAL_WAYPOINT_BASE = 1_100_000
VIRTUAL_WAYPOINT_MAX = 200_000

# Creature/NPC brushes are metadata-like in the Python port (spawns.xml entries)
# and are exposed via virtual ranges so we don't need to edit brushes.json.
# Must not overlap any other virtual ranges.
VIRTUAL_MONSTER_BASE = 1_200_000
VIRTUAL_MONSTER_MAX = 200_000

VIRTUAL_NPC_BASE = 1_400_000
VIRTUAL_NPC_MAX = 200_000

# Spawn-area tools (create/delete spawn areas) exposed as single virtual ids.
# Must not overlap any other virtual ranges.
VIRTUAL_SPAWN_MONSTER_TOOL_ID = 1_600_000
VIRTUAL_SPAWN_NPC_TOOL_ID = 1_600_001

# DoorBrush tools (legacy: normal/locked/magic/quest/window/hatch).
# Implemented as virtual ids so we don't need brushes.json entries.
# Must not overlap any other virtual ranges.
VIRTUAL_DOOR_TOOL_BASE = 1_650_000
VIRTUAL_DOOR_TOOL_NORMAL = 1_650_000
VIRTUAL_DOOR_TOOL_LOCKED = 1_650_001
VIRTUAL_DOOR_TOOL_MAGIC = 1_650_002
VIRTUAL_DOOR_TOOL_QUEST = 1_650_003
VIRTUAL_DOOR_TOOL_WINDOW = 1_650_004
VIRTUAL_DOOR_TOOL_HATCH = 1_650_005

# Optional Border Tool (legacy 'gravel' tool). Implemented as a virtual brush.
# NOTE: must not overlap any virtual ranges (flags/zones/houses).
VIRTUAL_OPTIONAL_BORDER_ID = 990_000

# Default carpet brush used for optional borders in our dataset.
# ("loose gravel" exists in data/brushes.json)
DEFAULT_OPTIONAL_BORDER_CARPET_ID = 6373


def waypoint_virtual_id(name: str, *, used: set[int] | None = None) -> int:
    """Compute a deterministic virtual brush id for a waypoint name.

    We map `name` -> VIRTUAL_WAYPOINT_BASE + offset, using crc32 with linear probing
    to avoid collisions within the current set.

    NOTE: The optional `used` set must be populated in a stable order (e.g. sorted
    waypoint names) to guarantee consistent results.
    """

    nm = str(name).strip()
    if not nm:
        raise ValueError("Waypoint name must be non-empty")

    h = int(zlib.crc32(nm.encode("utf-8")) & 0xFFFFFFFF)
    base = int(VIRTUAL_WAYPOINT_BASE)
    maxn = int(VIRTUAL_WAYPOINT_MAX)
    off = int(h % maxn)
    cand = int(base + off)
    if used is None:
        return cand

    # Linear probing, bounded.
    for _ in range(maxn):
        if cand not in used:
            used.add(int(cand))
            return int(cand)
        off = int((off + 1) % maxn)
        cand = int(base + off)

    raise RuntimeError("Waypoint virtual id space exhausted")


def monster_virtual_id(name: str, *, used: set[int] | None = None) -> int:
    """Compute a deterministic virtual brush id for a monster name."""

    nm = str(name).strip()
    if not nm:
        raise ValueError("Monster name must be non-empty")

    h = int(zlib.crc32(nm.encode("utf-8")) & 0xFFFFFFFF)
    base = int(VIRTUAL_MONSTER_BASE)
    maxn = int(VIRTUAL_MONSTER_MAX)
    off = int(h % maxn)
    cand = int(base + off)
    if used is None:
        return cand

    for _ in range(maxn):
        if cand not in used:
            used.add(int(cand))
            return int(cand)
        off = int((off + 1) % maxn)
        cand = int(base + off)
    raise RuntimeError("Monster virtual id space exhausted")


def npc_virtual_id(name: str, *, used: set[int] | None = None) -> int:
    """Compute a deterministic virtual brush id for an NPC name."""

    nm = str(name).strip()
    if not nm:
        raise ValueError("NPC name must be non-empty")

    h = int(zlib.crc32(nm.encode("utf-8")) & 0xFFFFFFFF)
    base = int(VIRTUAL_NPC_BASE)
    maxn = int(VIRTUAL_NPC_MAX)
    off = int(h % maxn)
    cand = int(base + off)
    if used is None:
        return cand

    for _ in range(maxn):
        if cand not in used:
            used.add(int(cand))
            return int(cand)
        off = int((off + 1) % maxn)
        cand = int(base + off)
    raise RuntimeError("NPC virtual id space exhausted")


def _parse_border_group_value(value: object | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float)):
        try:
            return int(value)
        except (TypeError, ValueError):
            raw = str(value).strip()
            if not raw:
                return None
            return int(zlib.crc32(raw.encode("utf-8")) & 0xFFFFFFFF)
    raw = str(value).strip()
    if not raw:
        return None
    return int(zlib.crc32(raw.encode("utf-8")) & 0xFFFFFFFF)


def monster_name_for_virtual_id(server_id: int) -> str | None:
    """Reverse-map a monster virtual id back to a known monster name."""

    sid = int(server_id)
    if not (VIRTUAL_MONSTER_BASE <= sid < VIRTUAL_MONSTER_BASE + VIRTUAL_MONSTER_MAX):
        return None

    names = load_monster_names()
    used: set[int] = set()
    id_to_name: dict[int, str] = {}
    for nm in names:
        try:
            vid = int(monster_virtual_id(nm, used=used))
        except Exception:
            continue
        id_to_name[int(vid)] = str(nm)
    return id_to_name.get(int(sid))


def npc_name_for_virtual_id(server_id: int) -> str | None:
    """Reverse-map an NPC virtual id back to a known NPC name."""

    sid = int(server_id)
    if not (VIRTUAL_NPC_BASE <= sid < VIRTUAL_NPC_BASE + VIRTUAL_NPC_MAX):
        return None

    names = load_npc_names()
    used: set[int] = set()
    id_to_name: dict[int, str] = {}
    for nm in names:
        try:
            vid = int(npc_virtual_id(nm, used=used))
        except Exception:
            continue
        id_to_name[int(vid)] = str(nm)
    return id_to_name.get(int(sid))


def _virtual_brush_for_id(server_id: int) -> BrushDefinition | None:
    sid = int(server_id)

    # NOTE: Doodad virtual brush ids are handled by `BrushManager.get_brush*`
    # because the Python port can optionally attach richer doodad metadata
    # parsed from materials XML.

    if VIRTUAL_FLAG_BASE <= sid < VIRTUAL_FLAG_BASE + VIRTUAL_FLAG_BITS:
        bit = int(sid - VIRTUAL_FLAG_BASE)
        return BrushDefinition(
            name=f"flag bit {bit}",
            server_id=sid,
            brush_type="flag",
            borders={},
            transition_borders={},
            family_ids=frozenset({sid}),
        )

    if VIRTUAL_ZONE_BASE <= sid < VIRTUAL_ZONE_BASE + VIRTUAL_ZONE_MAX:
        zone_id = int(sid - VIRTUAL_ZONE_BASE)
        return BrushDefinition(
            name=f"zone {zone_id}",
            server_id=sid,
            brush_type="zone",
            borders={},
            transition_borders={},
            family_ids=frozenset({sid}),
        )

    if VIRTUAL_HOUSE_BASE <= sid < VIRTUAL_HOUSE_BASE + VIRTUAL_HOUSE_MAX:
        house_id = int(sid - VIRTUAL_HOUSE_BASE)
        return BrushDefinition(
            name=f"house {house_id}",
            server_id=sid,
            brush_type="house",
            borders={},
            transition_borders={},
            family_ids=frozenset({sid}),
        )

    if VIRTUAL_HOUSE_EXIT_BASE <= sid < VIRTUAL_HOUSE_EXIT_BASE + VIRTUAL_HOUSE_EXIT_MAX:
        house_id = int(sid - VIRTUAL_HOUSE_EXIT_BASE)
        return BrushDefinition(
            name=f"house exit {house_id}",
            server_id=sid,
            brush_type="house_exit",
            borders={},
            transition_borders={},
            family_ids=frozenset({sid}),
        )

    if int(sid) == int(VIRTUAL_OPTIONAL_BORDER_ID):
        return BrushDefinition(
            name="Optional Border Tool",
            server_id=int(sid),
            brush_type="optional_border",
        )

    if VIRTUAL_WAYPOINT_BASE <= sid < VIRTUAL_WAYPOINT_BASE + VIRTUAL_WAYPOINT_MAX:
        return BrushDefinition(
            name=f"waypoint {int(sid - VIRTUAL_WAYPOINT_BASE)}",
            server_id=int(sid),
            brush_type="waypoint",
            borders={},
            transition_borders={},
            family_ids=frozenset({int(sid)}),
        )

    if int(sid) == int(VIRTUAL_SPAWN_MONSTER_TOOL_ID):
        return BrushDefinition(
            name="Spawn Monster Area",
            server_id=int(sid),
            brush_type="spawn_monster",
            borders={},
            transition_borders={},
            family_ids=frozenset({int(sid)}),
        )

    if int(sid) == int(VIRTUAL_SPAWN_NPC_TOOL_ID):
        return BrushDefinition(
            name="Spawn NPC Area",
            server_id=int(sid),
            brush_type="spawn_npc",
            borders={},
            transition_borders={},
            family_ids=frozenset({int(sid)}),
        )

    if int(sid) in (
        int(VIRTUAL_DOOR_TOOL_NORMAL),
        int(VIRTUAL_DOOR_TOOL_LOCKED),
        int(VIRTUAL_DOOR_TOOL_MAGIC),
        int(VIRTUAL_DOOR_TOOL_QUEST),
        int(VIRTUAL_DOOR_TOOL_WINDOW),
        int(VIRTUAL_DOOR_TOOL_HATCH),
    ):
        name_by_id = {
            int(VIRTUAL_DOOR_TOOL_NORMAL): "Door Tool: Normal",
            int(VIRTUAL_DOOR_TOOL_LOCKED): "Door Tool: Locked",
            int(VIRTUAL_DOOR_TOOL_MAGIC): "Door Tool: Magic",
            int(VIRTUAL_DOOR_TOOL_QUEST): "Door Tool: Quest",
            int(VIRTUAL_DOOR_TOOL_WINDOW): "Door Tool: Window",
            int(VIRTUAL_DOOR_TOOL_HATCH): "Door Tool: Hatch",
        }
        return BrushDefinition(
            name=str(name_by_id.get(int(sid), "Door Tool")),
            server_id=int(sid),
            brush_type="door",
            borders={},
            transition_borders={},
            family_ids=frozenset({int(sid)}),
        )

    if VIRTUAL_MONSTER_BASE <= sid < VIRTUAL_MONSTER_BASE + VIRTUAL_MONSTER_MAX:
        nm = monster_name_for_virtual_id(int(sid))
        return BrushDefinition(
            name=str(nm or f"monster {int(sid - VIRTUAL_MONSTER_BASE)}"),
            server_id=int(sid),
            brush_type="monster",
            borders={},
            transition_borders={},
            family_ids=frozenset({int(sid)}),
        )

    if VIRTUAL_NPC_BASE <= sid < VIRTUAL_NPC_BASE + VIRTUAL_NPC_MAX:
        nm = npc_name_for_virtual_id(int(sid))
        return BrushDefinition(
            name=str(nm or f"npc {int(sid - VIRTUAL_NPC_BASE)}"),
            server_id=int(sid),
            brush_type="npc",
            borders={},
            transition_borders={},
            family_ids=frozenset({int(sid)}),
        )

    return None


@dataclass(frozen=True, slots=True)
class BrushDefinition:
    """Logical brush definition loaded from `brushes.json`.

    This does not draw anything; it only defines how to choose border items.

    `server_id` is the primary (painted) item id.
    `borders` maps human-readable alignment keys to border item ids.

    Common keys supported by the auto-border selector:
    - "NORTH", "EAST", "SOUTH", "WEST"
    - "NORTH_EAST", "NORTH_WEST", "SOUTH_EAST", "SOUTH_WEST"
    - "INNER_NE", "INNER_NW", "INNER_SE", "INNER_SW"

    Other keys can exist and will be preserved, but may be ignored unless
    additional rules are implemented.
    """

    name: str
    server_id: int
    brush_type: str = "ground"  # ground, wall, carpet, ...
    borders: dict[str, int] = field(default_factory=dict)
    transition_borders: dict[int, dict[str, int]] = field(default_factory=dict)
    family_ids: frozenset[int] = field(default_factory=frozenset)

    border_group: int | None = None
    friends: tuple[int, ...] = ()
    hate_friends: bool = False
    ground_equivalents: dict[int, int] = field(default_factory=dict)

    # Optional: ground brush randomization variants.
    # If present, `randomize_ids` defines a set of candidate ground server_ids
    # to re-roll between for Randomize Selection/Map.
    randomize_ids: tuple[int, ...] = ()

    # Optional: richer doodad brush spec parsed from RME materials XML.
    doodad_spec: DoodadBrushSpec | None = None
    # Optional: table brush spec parsed from RME materials XML.
    table_spec: TableBrushSpec | None = None
    # Optional: carpet brush spec parsed from RME materials XML.
    carpet_spec: CarpetBrushSpec | None = None
    # Optional: door brush spec parsed from RME materials XML (wall doors).
    door_spec: DoorBrushSpec | None = None

    def __post_init__(self) -> None:
        # Cache reverso: IDs que pertencem à família desse brush.
        # Inclui o id principal e todos os ids de borda.
        if self.family_ids:
            return
        ids = {int(self.server_id)}
        for v in self.borders.values():
            ids.add(int(v))
        for tb in self.transition_borders.values():
            for v in tb.values():
                ids.add(int(v))
        if self.table_spec is not None:
            ids.update(int(v) for v in self.table_spec.item_ids())
        if self.carpet_spec is not None:
            ids.update(int(v) for v in self.carpet_spec.item_ids())
        if self.door_spec is not None:
            ids.update(int(v) for v in self.door_spec.item_ids())
        object.__setattr__(self, "family_ids", frozenset(ids))

    def get_border(self, alignment: str) -> int | None:
        return self.borders.get(str(alignment))

    def contains_id(self, server_id: int | None) -> bool:
        if server_id is None:
            return False
        return int(server_id) in self.family_ids


@dataclass(slots=True)
class BrushManager:
    """Loads and stores brush definitions keyed by primary server_id."""

    _brushes: dict[int, BrushDefinition] = field(default_factory=dict)
    _family_index: dict[int, int] = field(default_factory=dict)
    _border_groups: BorderGroupRegistry = field(default_factory=BorderGroupRegistry)
    _ground_equivalents: GroundEquivalentRegistry = field(default_factory=GroundEquivalentRegistry)

    # Optional doodad specs from RME materials XML.
    # Keyed by real server id (lookid/server_lookid).
    _doodads: dict[int, DoodadBrushSpec] = field(default_factory=dict)
    _doodads_loaded: bool = False
    _doodads_source_path: str | None = None
    _doodads_warnings: list[str] = field(default_factory=list)
    _doodad_owned_ids_cache: frozenset[int] | None = None

    # Optional table specs from RME materials XML.
    _table_brushes: dict[int, TableBrushSpec] = field(default_factory=dict)
    _table_brushes_loaded: bool = False
    _table_brushes_source_path: str | None = None
    _table_brushes_warnings: list[str] = field(default_factory=list)

    # Optional carpet specs from RME materials XML.
    _carpet_brushes: dict[int, CarpetBrushSpec] = field(default_factory=dict)
    _carpet_brushes_loaded: bool = False
    _carpet_brushes_source_path: str | None = None
    _carpet_brushes_warnings: list[str] = field(default_factory=list)

    # Optional door specs from RME materials XML (wall door definitions).
    _door_brushes: dict[int, DoorBrushSpec] = field(default_factory=dict)
    _door_brushes_loaded: bool = False
    _door_brushes_source_path: str | None = None
    _door_brushes_warnings: list[str] = field(default_factory=list)

    @staticmethod
    def _resolve_brushes_path(json_path: str) -> Path:
        """Resolve brushes.json path robustly for both source and PyInstaller builds."""
        candidate_paths: list[Path] = []
        raw = Path(json_path)

        # 1) Absolute or direct relative to CWD
        candidate_paths.append(raw if raw.is_absolute() else Path.cwd() / raw)

        # 2) Relative to project root (py_rme_canary/..)
        repo_root = Path(__file__).resolve().parent.parent.parent
        candidate_paths.append(repo_root / raw)

        # 3) Package data inside py_rme_canary/data
        candidate_paths.append(Path(__file__).resolve().parent.parent / "data" / "brushes.json")

        # 4) PyInstaller bundle paths (sys._MEIPASS)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            base = Path(meipass)
            candidate_paths.extend(
                [
                    base / "data" / "brushes.json",
                    base / "py_rme_canary" / "data" / "brushes.json",
                ]
            )

        # 5) importlib.resources (if package available)
        try:
            pkg_path = resources.files("py_rme_canary.data") / "brushes.json"
            if isinstance(pkg_path, Path):
                candidate_paths.append(pkg_path)
            else:
                candidate_paths.append(Path(str(pkg_path)))
        except Exception:
            pass

        for path in candidate_paths:
            if path.exists():
                return path

        raise FileNotFoundError(f"Could not locate brushes.json. Tried: {candidate_paths}")

    @classmethod
    def from_json_file(cls, json_path: str) -> BrushManager:
        mgr = cls()
        mgr.load_from_file(json_path)
        return mgr

    def load_from_file(self, json_path: str) -> None:
        resolved = self._resolve_brushes_path(json_path)
        with resolved.open(encoding="utf-8") as f:
            data = json.load(f)

        brushes = data.get("brushes", [])
        if not isinstance(brushes, list):
            raise ValueError("Invalid brushes.json: 'brushes' must be a list")

        name_to_id: dict[str, int] = {}
        pending_friend_refs: dict[int, dict[str, object]] = {}

        for entry in brushes:
            if not isinstance(entry, dict):
                raise ValueError("Invalid brushes.json: each brush entry must be an object")

            name = str(entry["name"])
            # Accept both `server_id` and `main_server_id` (alias).
            server_id = int(entry["server_id"]) if "server_id" in entry else int(entry["main_server_id"])
            brush_type = str(entry.get("type", "ground"))
            borders_raw = entry.get("borders", {})
            if not isinstance(borders_raw, dict):
                raise ValueError(f"Invalid brushes.json: borders for {name!r} must be an object")

            borders: dict[str, int] = {str(k): int(v) for k, v in borders_raw.items()}

            transitions_raw = entry.get("transitions", [])
            transition_borders: dict[int, dict[str, int]] = {}
            if transitions_raw is None:
                transitions_raw = []
            if not isinstance(transitions_raw, list):
                raise ValueError(f"Invalid brushes.json: transitions for {name!r} must be a list")
            for t in transitions_raw:
                if not isinstance(t, dict):
                    raise ValueError(f"Invalid brushes.json: each transition for {name!r} must be an object")
                to_id = t.get("to_server_id")
                if to_id is None:
                    raise ValueError(f"Invalid brushes.json: transition for {name!r} missing to_server_id")
                try:
                    to_server_id = int(to_id)
                except (TypeError, ValueError) as err:
                    raise ValueError(f"Invalid brushes.json: transition to_server_id for {name!r} must be int") from err
                tb = t.get("borders", {})
                if not isinstance(tb, dict):
                    raise ValueError(f"Invalid brushes.json: transition borders for {name!r} must be an object")
                transition_borders[to_server_id] = {str(k): int(v) for k, v in tb.items()}

            randomize_raw = entry.get("randomize_ids")
            if randomize_raw is None:
                randomize_ids: tuple[int, ...] = ()
            else:
                if not isinstance(randomize_raw, list | tuple):
                    raise ValueError(f"Invalid brushes.json: randomize_ids for {name!r} must be a list")
                randomize_ids = tuple(int(v) for v in randomize_raw if int(v) != 0)

            border_group = _parse_border_group_value(entry.get("border_group"))

            friends_raw = entry.get("friends")
            enemies_raw = entry.get("enemies")
            friend_entries = friends_raw if friends_raw is not None else enemies_raw
            hate_friends = enemies_raw is not None

            friend_ids: list[int] = []
            friend_names: list[str] = []
            if friend_entries is not None:
                if not isinstance(friend_entries, list):
                    raise ValueError(f"Invalid brushes.json: friends/enemies for {name!r} must be a list")
                for ref in friend_entries:
                    if isinstance(ref, bool):
                        raise ValueError(f"Invalid friends/enemies entry for {name!r}: {ref!r}")
                    if isinstance(ref, int | float):
                        friend_ids.append(int(ref))
                        continue
                    if isinstance(ref, str):
                        token = ref.strip()
                        if not token:
                            continue
                        if token.lower() == "all":
                            friend_ids.append(int(FRIEND_ALL))
                        else:
                            friend_names.append(token)
                        continue
                    raise ValueError(f"Invalid friends/enemies entry for {name!r}: {ref!r}")

            ground_equivalents_raw = entry.get("ground_equivalents")
            ground_equivalents: dict[int, int] = {}
            if ground_equivalents_raw is None:
                ground_equivalents = {}
            elif isinstance(ground_equivalents_raw, dict):
                for k, v in ground_equivalents_raw.items():
                    ground_equivalents[int(k)] = int(v)
            elif isinstance(ground_equivalents_raw, list | tuple):
                for item_id in ground_equivalents_raw:
                    ground_equivalents[int(item_id)] = int(server_id)
            else:
                raise ValueError(f"Invalid brushes.json: ground_equivalents for {name!r} must be map or list")

            brush = BrushDefinition(
                name=name,
                server_id=server_id,
                brush_type=brush_type,
                borders=borders,
                transition_borders=transition_borders,
                border_group=border_group,
                friends=tuple(friend_ids),
                hate_friends=bool(hate_friends),
                ground_equivalents=ground_equivalents,
                randomize_ids=randomize_ids,
            )
            self._brushes[server_id] = brush

            name_to_id[name] = int(server_id)
            if friend_names:
                pending_friend_refs[int(server_id)] = {
                    "names": friend_names,
                    "ids": friend_ids,
                    "hate": bool(hate_friends),
                }

            # Reverse lookup: allow finding a brush by any id in its family.
            # If collisions exist, first loaded wins (stable + predictable).
            for fid in brush.family_ids:
                self._family_index.setdefault(int(fid), int(server_id))

        if pending_friend_refs:
            for sid, payload in pending_friend_refs.items():
                pending_brush = self._brushes.get(int(sid))
                if pending_brush is None:
                    continue
                raw_ids = payload.get("ids", [])
                ids: list[int] = []
                if isinstance(raw_ids, list):
                    for ref in raw_ids:
                        try:
                            ids.append(int(ref))
                        except (TypeError, ValueError):
                            continue

                raw_names = payload.get("names", [])
                names = list(raw_names) if isinstance(raw_names, list) else []
                for fname in names:
                    resolved_id = name_to_id.get(str(fname))
                    if resolved_id is None:
                        logger.warning("Unknown friend/enemy brush name %r referenced by %r", fname, pending_brush.name)
                        continue
                    ids.append(int(resolved_id))
                if ids or payload.get("hate", False):
                    self._brushes[int(sid)] = replace(
                        pending_brush,
                        friends=tuple(sorted({int(x) for x in ids})),
                        hate_friends=bool(payload.get("hate", False)),
                    )

        self._rebuild_registries()

    def _rebuild_registries(self) -> None:
        self._border_groups.clear()
        self._ground_equivalents.clear()

        for brush in self._brushes.values():
            if brush.border_group is not None:
                item_ids: set[int] = {int(v) for v in brush.borders.values()}
                for tb in brush.transition_borders.values():
                    item_ids.update(int(v) for v in tb.values())
                self._border_groups.register_group(int(brush.border_group), item_ids)

            brush_type_norm = str(brush.brush_type).strip().lower()
            if brush_type_norm in ("ground", "terrain"):
                border_item_ids: set[int] = {int(v) for v in brush.borders.values()}
                for tb in brush.transition_borders.values():
                    border_item_ids.update(int(v) for v in tb.values())
                self._ground_equivalents.register_many(int(brush.server_id), border_item_ids)

            for item_id, ground_id in brush.ground_equivalents.items():
                self._ground_equivalents.register(int(item_id), int(ground_id))

    def load_doodads_from_materials(self, materials_brushs_xml_path: str) -> None:
        """Load RME `type="doodad"` brush definitions from materials XML.

        This is intentionally Qt-free and keeps the runtime editor independent of
        the exporter scripts.

        Input expected to be `data/materials/brushs.xml` (the include list).
        """

        root_path = os.fspath(materials_brushs_xml_path)
        base_dir = os.path.dirname(root_path)

        self._doodads.clear()
        self._doodads_warnings.clear()
        self._doodads_loaded = False
        self._doodads_source_path = str(root_path)
        self._doodad_owned_ids_cache = None

        try:
            root = _parse_xml_root_tolerant(root_path)
        except Exception as e:
            msg = f"Failed to parse doodad materials include list: {root_path} ({type(e).__name__}: {e})"
            self._doodads_warnings.append(msg)
            logger.warning(msg)
            return

        # Resolve includes in brushs.xml (legacy file name is "brushs.xml").
        include_files: list[str] = []
        for inc in root.findall("include"):
            fn = (inc.get("file") or "").strip()
            if not fn:
                continue
            include_files.append(os.path.join(base_dir, fn))

        if not include_files:
            self._doodads_warnings.append(f"No <include> entries found in {root_path}")

        for xml_path in include_files:
            try:
                sub_root = _parse_xml_root_tolerant(xml_path)
            except Exception as e:
                self._doodads_warnings.append(
                    f"Failed to parse doodad materials file: {xml_path} ({type(e).__name__}: {e})"
                )
                continue

            for brush in sub_root.findall("brush"):
                if str(brush.get("type") or "").strip().lower() != "doodad":
                    continue
                spec = _parse_doodad_brush(brush)
                if spec is None:
                    continue
                self._doodads[int(spec.server_id)] = spec

        self._doodads_loaded = True

        if self._doodads_warnings:
            logger.warning(
                "Doodad materials loaded with %d warning(s) (first: %s)",
                len(self._doodads_warnings),
                self._doodads_warnings[0],
            )

    def ensure_doodads_loaded(self, materials_brushs_xml_path: str) -> bool:
        """Idempotently load doodads from materials XML.

        Returns True if doodads are available (loaded + non-empty).
        """

        path = os.fspath(materials_brushs_xml_path)
        if bool(self._doodads_loaded) and str(self._doodads_source_path or "") == str(path):
            return bool(self._doodads)

        self.load_doodads_from_materials(str(path))
        return bool(self._doodads)

    def iter_doodad_brushes(self) -> Iterable[tuple[int, str]]:
        for sid, spec in self._doodads.items():
            yield int(sid), str(spec.name)

    def doodad_owned_ids(self) -> frozenset[int]:
        """Return the set of item ids owned by any doodad brush."""

        cached = self._doodad_owned_ids_cache
        if cached is not None:
            return cached

        ids: set[int] = set()
        for spec in self._doodads.values():
            for alt in tuple(spec.alternatives or ()):
                for it in tuple(alt.items or ()):
                    if int(it.id) > 0:
                        ids.add(int(it.id))
                for comp in tuple(alt.composites or ()):
                    for placement in tuple(comp.tiles or ()):
                        for it in tuple(placement.items or ()):
                            if int(it.id) > 0:
                                ids.add(int(it.id))

        frozen = frozenset(int(v) for v in ids if int(v) > 0)
        self._doodad_owned_ids_cache = frozen
        return frozen

    def load_table_brushes_from_materials(self, materials_brushs_xml_path: str) -> None:
        """Load RME `type="table"` brush definitions from materials XML."""

        root_path = os.fspath(materials_brushs_xml_path)
        base_dir = os.path.dirname(root_path)

        self._table_brushes.clear()
        self._table_brushes_warnings.clear()
        self._table_brushes_loaded = False
        self._table_brushes_source_path = str(root_path)

        try:
            root = _parse_xml_root_tolerant(root_path)
        except Exception as e:
            msg = f"Failed to parse table materials include list: {root_path} ({type(e).__name__}: {e})"
            self._table_brushes_warnings.append(msg)
            logger.warning(msg)
            return

        include_files: list[str] = []
        for inc in root.findall("include"):
            fn = (inc.get("file") or "").strip()
            if not fn:
                continue
            include_files.append(os.path.join(base_dir, fn))

        if not include_files:
            self._table_brushes_warnings.append(f"No <include> entries found in {root_path}")

        for xml_path in include_files:
            try:
                sub_root = _parse_xml_root_tolerant(xml_path)
            except Exception as e:
                self._table_brushes_warnings.append(
                    f"Failed to parse table materials file: {xml_path} ({type(e).__name__}: {e})"
                )
                continue

            for brush in sub_root.findall("brush"):
                if str(brush.get("type") or "").strip().lower() != "table":
                    continue
                spec = _parse_table_brush(brush, self._table_brushes_warnings)
                if spec is None:
                    continue
                sid = int(spec.server_id)
                if sid <= 0:
                    continue

                existing = self._brushes.get(int(sid))
                if existing is not None and str(existing.brush_type).strip().lower() != "table":
                    self._table_brushes_warnings.append(
                        f"Table brush {spec.name!r} server_id {sid} collides with {existing.name!r}"
                    )
                    continue
                if existing is not None and existing.table_spec is not None:
                    self._table_brushes_warnings.append(f"Table brush {spec.name!r} server_id {sid} already loaded")
                    continue
                conflict_ids = []
                for item_id in spec.item_ids():
                    owner = self._family_index.get(int(item_id))
                    if owner is not None and int(owner) != int(sid):
                        conflict_ids.append(int(item_id))
                if conflict_ids:
                    self._table_brushes_warnings.append(
                        f"Table brush {spec.name!r} item id collision(s): {sorted(conflict_ids)[:5]}"
                    )
                    continue

                if existing is not None:
                    brush_def = replace(
                        existing,
                        brush_type="table",
                        table_spec=spec,
                        family_ids=frozenset(),
                    )
                else:
                    brush_def = BrushDefinition(
                        name=str(spec.name),
                        server_id=int(sid),
                        brush_type="table",
                        borders={},
                        transition_borders={},
                        table_spec=spec,
                    )

                self._brushes[int(sid)] = brush_def
                self._table_brushes[int(sid)] = spec
                for fid in brush_def.family_ids:
                    self._family_index.setdefault(int(fid), int(brush_def.server_id))

        self._table_brushes_loaded = True
        self._rebuild_registries()

        if self._table_brushes_warnings:
            logger.warning(
                "Table materials loaded with %d warning(s) (first: %s)",
                len(self._table_brushes_warnings),
                self._table_brushes_warnings[0],
            )

    def ensure_table_brushes_loaded(self, materials_brushs_xml_path: str) -> bool:
        """Idempotently load table brushes from materials XML."""

        path = os.fspath(materials_brushs_xml_path)
        if bool(self._table_brushes_loaded) and str(self._table_brushes_source_path or "") == str(path):
            return bool(self._table_brushes)

        self.load_table_brushes_from_materials(str(path))
        return bool(self._table_brushes)

    def iter_table_brushes(self) -> Iterable[tuple[int, str]]:
        for sid, spec in self._table_brushes.items():
            yield int(sid), str(spec.name)

    def load_carpet_brushes_from_materials(self, materials_brushs_xml_path: str) -> None:
        """Load RME `type="carpet"` brush definitions from materials XML."""

        root_path = os.fspath(materials_brushs_xml_path)
        base_dir = os.path.dirname(root_path)

        self._carpet_brushes.clear()
        self._carpet_brushes_warnings.clear()
        self._carpet_brushes_loaded = False
        self._carpet_brushes_source_path = str(root_path)

        try:
            root = _parse_xml_root_tolerant(root_path)
        except Exception as e:
            msg = f"Failed to parse carpet materials include list: {root_path} ({type(e).__name__}: {e})"
            self._carpet_brushes_warnings.append(msg)
            logger.warning(msg)
            return

        include_files: list[str] = []
        for inc in root.findall("include"):
            fn = (inc.get("file") or "").strip()
            if not fn:
                continue
            include_files.append(os.path.join(base_dir, fn))

        if not include_files:
            self._carpet_brushes_warnings.append(f"No <include> entries found in {root_path}")

        for xml_path in include_files:
            try:
                sub_root = _parse_xml_root_tolerant(xml_path)
            except Exception as e:
                self._carpet_brushes_warnings.append(
                    f"Failed to parse carpet materials file: {xml_path} ({type(e).__name__}: {e})"
                )
                continue

            for brush in sub_root.findall("brush"):
                if str(brush.get("type") or "").strip().lower() != "carpet":
                    continue
                spec = _parse_carpet_brush(brush, self._carpet_brushes_warnings)
                if spec is None:
                    continue
                sid = int(spec.server_id)
                if sid <= 0:
                    continue

                existing = self._brushes.get(int(sid))
                if existing is not None and str(existing.brush_type).strip().lower() != "carpet":
                    self._carpet_brushes_warnings.append(
                        f"Carpet brush {spec.name!r} server_id {sid} collides with {existing.name!r}"
                    )
                    continue
                if existing is not None and existing.carpet_spec is not None:
                    self._carpet_brushes_warnings.append(f"Carpet brush {spec.name!r} server_id {sid} already loaded")
                    continue
                conflict_ids = []
                for item_id in spec.item_ids():
                    owner = self._family_index.get(int(item_id))
                    if owner is not None and int(owner) != int(sid):
                        conflict_ids.append(int(item_id))
                if conflict_ids:
                    self._carpet_brushes_warnings.append(
                        f"Carpet brush {spec.name!r} item id collision(s): {sorted(conflict_ids)[:5]}"
                    )
                    continue

                if existing is not None:
                    brush_def = replace(
                        existing,
                        brush_type="carpet",
                        carpet_spec=spec,
                        family_ids=frozenset(),
                    )
                else:
                    brush_def = BrushDefinition(
                        name=str(spec.name),
                        server_id=int(sid),
                        brush_type="carpet",
                        borders={},
                        transition_borders={},
                        carpet_spec=spec,
                    )

                self._brushes[int(sid)] = brush_def
                self._carpet_brushes[int(sid)] = spec
                for fid in brush_def.family_ids:
                    self._family_index.setdefault(int(fid), int(brush_def.server_id))

        self._carpet_brushes_loaded = True
        self._rebuild_registries()

        if self._carpet_brushes_warnings:
            logger.warning(
                "Carpet materials loaded with %d warning(s) (first: %s)",
                len(self._carpet_brushes_warnings),
                self._carpet_brushes_warnings[0],
            )

    def ensure_carpet_brushes_loaded(self, materials_brushs_xml_path: str) -> bool:
        """Idempotently load carpet brushes from materials XML."""

        path = os.fspath(materials_brushs_xml_path)
        if bool(self._carpet_brushes_loaded) and str(self._carpet_brushes_source_path or "") == str(path):
            return bool(self._carpet_brushes)

        self.load_carpet_brushes_from_materials(str(path))
        return bool(self._carpet_brushes)

    def iter_carpet_brushes(self) -> Iterable[tuple[int, str]]:
        for sid, spec in self._carpet_brushes.items():
            yield int(sid), str(spec.name)

    def load_door_brushes_from_materials(self, materials_brushs_xml_path: str) -> None:
        """Load RME wall door definitions from materials XML."""

        root_path = os.fspath(materials_brushs_xml_path)
        base_dir = os.path.dirname(root_path)

        self._door_brushes.clear()
        self._door_brushes_warnings.clear()
        self._door_brushes_loaded = False
        self._door_brushes_source_path = str(root_path)

        try:
            root = _parse_xml_root_tolerant(root_path)
        except Exception as e:
            msg = f"Failed to parse door materials include list: {root_path} ({type(e).__name__}: {e})"
            self._door_brushes_warnings.append(msg)
            logger.warning(msg)
            return

        include_files: list[str] = []
        for inc in root.findall("include"):
            fn = (inc.get("file") or "").strip()
            if not fn:
                continue
            include_files.append(os.path.join(base_dir, fn))

        if not include_files:
            self._door_brushes_warnings.append(f"No <include> entries found in {root_path}")

        for xml_path in include_files:
            try:
                sub_root = _parse_xml_root_tolerant(xml_path)
            except Exception as e:
                self._door_brushes_warnings.append(
                    f"Failed to parse door materials file: {xml_path} ({type(e).__name__}: {e})"
                )
                continue

            for brush in sub_root.findall("brush"):
                if str(brush.get("type") or "").strip().lower() != "wall":
                    continue
                spec = _parse_door_brush(brush, self._door_brushes_warnings)
                if spec is None:
                    continue
                sid = int(spec.server_id)
                if sid <= 0:
                    continue

                existing = self._brushes.get(int(sid))
                if existing is not None:
                    existing_type = str(existing.brush_type).strip().lower()
                    if existing_type not in ("wall", "wall decoration"):
                        self._door_brushes_warnings.append(
                            f"Door spec {spec.name!r} server_id {sid} collides with {existing.name!r}"
                        )
                        continue
                    if existing.door_spec is not None:
                        self._door_brushes_warnings.append(f"Door spec {spec.name!r} server_id {sid} already loaded")
                        continue

                conflict_ids = []
                for item_id in spec.item_ids():
                    owner = self._family_index.get(int(item_id))
                    if owner is not None and int(owner) != int(sid):
                        conflict_ids.append(int(item_id))
                if conflict_ids:
                    self._door_brushes_warnings.append(
                        f"Door spec {spec.name!r} item id collision(s): {sorted(conflict_ids)[:5]}"
                    )
                    continue

                if existing is not None:
                    brush_def = replace(existing, door_spec=spec, family_ids=frozenset())
                else:
                    brush_def = BrushDefinition(
                        name=str(spec.name),
                        server_id=int(sid),
                        brush_type="wall",
                        borders={},
                        transition_borders={},
                        door_spec=spec,
                    )

                self._brushes[int(sid)] = brush_def
                self._door_brushes[int(sid)] = spec
                for fid in brush_def.family_ids:
                    self._family_index.setdefault(int(fid), int(brush_def.server_id))

        self._door_brushes_loaded = True
        self._rebuild_registries()

        if self._door_brushes_warnings:
            logger.warning(
                "Door materials loaded with %d warning(s) (first: %s)",
                len(self._door_brushes_warnings),
                self._door_brushes_warnings[0],
            )

    def ensure_door_brushes_loaded(self, materials_brushs_xml_path: str) -> bool:
        """Idempotently load door specs from materials XML."""

        path = os.fspath(materials_brushs_xml_path)
        if bool(self._door_brushes_loaded) and str(self._door_brushes_source_path or "") == str(path):
            return bool(self._door_brushes)

        self.load_door_brushes_from_materials(str(path))
        return bool(self._door_brushes)

    def iter_door_brushes(self) -> Iterable[tuple[int, str]]:
        for sid, spec in self._door_brushes.items():
            yield int(sid), str(spec.name)

    def border_groups(self) -> BorderGroupRegistry:
        return self._border_groups

    def ground_equivalents(self) -> GroundEquivalentRegistry:
        return self._ground_equivalents

    def get_brush(self, server_id: int) -> BrushDefinition | None:
        sid = int(server_id)

        # Doodad palette uses a virtual id range so we can apply doodad semantics.
        # If we have a parsed materials definition for this id, attach it.
        if VIRTUAL_DOODAD_BASE <= sid < VIRTUAL_DOODAD_BASE + VIRTUAL_DOODAD_MAX:
            real_id = int(sid - VIRTUAL_DOODAD_BASE)
            if real_id <= 0:
                return None
            spec = self._doodads.get(int(real_id))
            name = str(spec.name) if spec is not None else f"doodad {real_id}"
            return BrushDefinition(
                name=name,
                server_id=int(real_id),
                brush_type="doodad",
                borders={},
                transition_borders={},
                family_ids=frozenset({int(real_id)}),
                doodad_spec=spec,
            )

        b = self._brushes.get(sid)
        if b is not None:
            return b
        return _virtual_brush_for_id(sid)

    def get_brush_any(self, server_id: int) -> BrushDefinition | None:
        """Return a brush by either main id or any family id."""

        sid = int(server_id)

        if VIRTUAL_DOODAD_BASE <= sid < VIRTUAL_DOODAD_BASE + VIRTUAL_DOODAD_MAX:
            return self.get_brush(int(sid))

        b = self._brushes.get(sid)
        if b is not None:
            return b
        main = self._family_index.get(sid)
        if main is not None:
            return self._brushes.get(int(main))
        return _virtual_brush_for_id(sid)


@dataclass(frozen=True, slots=True)
class DoodadItemChoice:
    id: int
    chance: int = 10


@dataclass(frozen=True, slots=True)
class DoodadTilePlacement:
    dx: int
    dy: int
    dz: int = 0
    items: tuple[DoodadItemChoice, ...] = ()
    # Legacy: composite tiles merge/stack all items. (Per-item chance is ignored.)
    choose_one: bool = False


@dataclass(frozen=True, slots=True)
class DoodadCompositeChoice:
    chance: int = 10
    tiles: tuple[DoodadTilePlacement, ...] = ()


@dataclass(frozen=True, slots=True)
class DoodadAlternative:
    items: tuple[DoodadItemChoice, ...] = ()
    composites: tuple[DoodadCompositeChoice, ...] = ()


@dataclass(frozen=True, slots=True)
class DoodadBrushSpec:
    name: str
    server_id: int
    thickness_low: int = 100
    thickness_ceil: int = 100
    draggable: bool = True
    on_duplicate: bool = False
    on_blocking: bool = False
    redo_borders: bool = False
    one_size: bool = False
    alternatives: tuple[DoodadAlternative, ...] = ()


@dataclass(frozen=True, slots=True)
class TableItemChoice:
    id: int
    chance: int = 0


@dataclass(frozen=True, slots=True)
class TableBrushSpec:
    name: str
    server_id: int
    items_by_alignment: dict[str, tuple[TableItemChoice, ...]] = field(default_factory=dict)

    def item_ids(self) -> tuple[int, ...]:
        ids: set[int] = set()
        for choices in self.items_by_alignment.values():
            for choice in choices:
                if int(choice.id) > 0:
                    ids.add(int(choice.id))
        return tuple(sorted(ids))

    def choose_item_id(self, alignment: str, seed: bytes | None = None) -> int | None:
        key = _normalize_table_align(alignment)
        if key is None:
            return None
        choices = tuple(self.items_by_alignment.get(key, ()))
        if not choices:
            return None
        total = 0
        for choice in choices:
            if int(choice.chance) > 0:
                total += int(choice.chance)
        if total <= 0:
            return None
        if seed is None:
            seed = f"table:{self.server_id}:{key}".encode()
        roll = int(zlib.crc32(seed) & 0xFFFFFFFF) % int(total)
        acc = 0
        for choice in choices:
            chance = int(choice.chance)
            if chance <= 0:
                continue
            acc += chance
            if roll < acc:
                return int(choice.id)
        return int(choices[-1].id)


@dataclass(frozen=True, slots=True)
class CarpetItemChoice:
    id: int
    chance: int = 0


@dataclass(frozen=True, slots=True)
class CarpetBrushSpec:
    name: str
    server_id: int
    items_by_alignment: dict[str, tuple[CarpetItemChoice, ...]] = field(default_factory=dict)

    def item_ids(self) -> tuple[int, ...]:
        ids: set[int] = set()
        for choices in self.items_by_alignment.values():
            for choice in choices:
                if int(choice.id) > 0:
                    ids.add(int(choice.id))
        return tuple(sorted(ids))

    def choose_item_id(self, alignment: str, seed: bytes | None = None) -> int | None:
        key = _normalize_carpet_align(alignment) or "center"
        choices = tuple(self.items_by_alignment.get(key, ()))
        if not choices and key != "center":
            key = "center"
            choices = tuple(self.items_by_alignment.get("center", ()))

        if not choices:
            for fallback_key in _CARPET_FALLBACK_ORDER:
                choices = tuple(self.items_by_alignment.get(fallback_key, ()))
                if choices:
                    key = str(fallback_key)
                    break

        if not choices:
            return None

        total = 0
        for choice in choices:
            if int(choice.chance) > 0:
                total += int(choice.chance)
        if total <= 0:
            return None
        if seed is None:
            seed = f"carpet:{self.server_id}:{key}".encode()
        roll = int(zlib.crc32(seed) & 0xFFFFFFFF) % int(total)
        acc = 0
        for choice in choices:
            chance = int(choice.chance)
            if chance <= 0:
                continue
            acc += chance
            if roll < acc:
                return int(choice.id)
        return int(choices[-1].id)


@dataclass(frozen=True, slots=True)
class DoorItemSpec:
    id: int
    door_type: DoorType
    is_open: bool = False


@dataclass(frozen=True, slots=True)
class DoorBrushSpec:
    name: str
    server_id: int
    items_by_alignment: dict[str, tuple[DoorItemSpec, ...]] = field(default_factory=dict)

    def item_ids(self) -> tuple[int, ...]:
        ids: set[int] = set()
        for items in self.items_by_alignment.values():
            for entry in items:
                if int(entry.id) > 0:
                    ids.add(int(entry.id))
        return tuple(sorted(ids))

    def alignment_for_item(self, item_id: int) -> str | None:
        iid = int(item_id)
        for align, items in self.items_by_alignment.items():
            for entry in items:
                if int(entry.id) == iid:
                    return str(align)
        return None

    def entry_for_item(self, item_id: int) -> DoorItemSpec | None:
        iid = int(item_id)
        for items in self.items_by_alignment.values():
            for entry in items:
                if int(entry.id) == iid:
                    return entry
        return None

    def choose_item_id(
        self,
        alignment: str,
        door_type: DoorType,
        *,
        is_open: bool,
    ) -> int | None:
        key = _normalize_door_alignment(alignment)
        if key is None:
            return None
        entries = tuple(self.items_by_alignment.get(key, ()))
        if not entries:
            return None
        for entry in entries:
            if entry.door_type == door_type and bool(entry.is_open) == bool(is_open):
                return int(entry.id)
        return None

    def choose_any_item_id(self, alignment: str, door_type: DoorType) -> int | None:
        key = _normalize_door_alignment(alignment)
        if key is None:
            return None
        entries = tuple(self.items_by_alignment.get(key, ()))
        for entry in entries:
            if entry.door_type == door_type:
                return int(entry.id)
        return None

    def toggle_item_id(self, item_id: int) -> int | None:
        align = self.alignment_for_item(int(item_id))
        entry = self.entry_for_item(int(item_id))
        if align is None or entry is None:
            return None
        return self.choose_item_id(align, entry.door_type, is_open=not bool(entry.is_open))


_TABLE_ALIGNMENTS: dict[str, str] = {
    "north": "north",
    "south": "south",
    "east": "east",
    "west": "west",
    "horizontal": "horizontal",
    "vertical": "vertical",
    "alone": "alone",
    "north_end": "north",
    "south_end": "south",
    "east_end": "east",
    "west_end": "west",
}

_TABLE_TYPE_TO_ALIGN: dict[int, str] = {
    0: "north",
    1: "south",
    2: "east",
    3: "west",
    4: "horizontal",
    5: "vertical",
    6: "alone",
}

TABLE_TYPES_BY_MASK: tuple[int, ...] = (
    6,
    6,
    1,
    6,
    6,
    6,
    6,
    6,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    6,
    6,
    1,
    6,
    6,
    6,
    6,
    6,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    0,
    0,
    5,
    0,
    0,
    0,
    0,
    0,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    6,
    6,
    1,
    6,
    6,
    6,
    6,
    6,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    6,
    6,
    1,
    6,
    6,
    6,
    6,
    6,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    6,
    6,
    1,
    6,
    6,
    6,
    6,
    6,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    6,
    6,
    1,
    6,
    6,
    6,
    6,
    6,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    6,
    6,
    1,
    6,
    6,
    6,
    6,
    6,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    3,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
)


def table_alignment_for_mask(mask: int) -> str:
    idx = int(mask) & 0xFF
    if idx < 0 or idx >= len(TABLE_TYPES_BY_MASK):
        return "alone"
    table_type = int(TABLE_TYPES_BY_MASK[idx])
    return str(_TABLE_TYPE_TO_ALIGN.get(int(table_type), "alone"))


def _normalize_table_align(align: str) -> str | None:
    key = str(align or "").strip().lower()
    if not key:
        return None
    key = _TABLE_ALIGNMENTS.get(key, key)
    if key in ("north", "south", "east", "west", "horizontal", "vertical", "alone"):
        return key
    return None


_CARPET_ALIGNMENTS: dict[str, str] = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
    "cnw": "northwest",
    "cne": "northeast",
    "csw": "southwest",
    "cse": "southeast",
    "dnw": "northwest_diagonal",
    "dne": "northeast_diagonal",
    "dsw": "southwest_diagonal",
    "dse": "southeast_diagonal",
    "center": "center",
}

_CARPET_TYPE_TO_ALIGN: dict[int, str] = {
    0: "none",
    1: "north",
    2: "east",
    3: "south",
    4: "west",
    5: "northwest",
    6: "northeast",
    7: "southwest",
    8: "southeast",
    9: "northwest_diagonal",
    10: "northeast_diagonal",
    11: "southeast_diagonal",
    12: "southwest_diagonal",
    13: "center",
}

_CARPET_FALLBACK_ORDER: tuple[str, ...] = (
    "none",
    "north",
    "east",
    "south",
    "west",
    "northwest",
    "northeast",
    "southwest",
    "southeast",
    "northwest_diagonal",
    "northeast_diagonal",
    "southeast_diagonal",
)

CARPET_TYPES_BY_MASK: tuple[int, ...] = (
    13,
    13,
    13,
    5,
    6,
    1,
    6,
    1,
    13,
    4,
    5,
    5,
    13,
    13,
    5,
    5,
    13,
    6,
    6,
    6,
    6,
    6,
    6,
    6,
    13,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    7,
    4,
    7,
    6,
    6,
    5,
    6,
    1,
    7,
    7,
    5,
    5,
    7,
    13,
    5,
    5,
    13,
    13,
    6,
    6,
    13,
    6,
    6,
    6,
    7,
    13,
    13,
    13,
    13,
    13,
    13,
    1,
    7,
    5,
    13,
    5,
    6,
    1,
    6,
    1,
    7,
    4,
    4,
    5,
    7,
    5,
    5,
    1,
    8,
    8,
    2,
    2,
    8,
    8,
    2,
    2,
    3,
    3,
    13,
    13,
    3,
    3,
    13,
    1,
    7,
    7,
    7,
    4,
    7,
    13,
    13,
    4,
    7,
    7,
    4,
    4,
    7,
    7,
    4,
    4,
    8,
    8,
    2,
    13,
    8,
    8,
    2,
    2,
    3,
    3,
    13,
    13,
    3,
    3,
    13,
    9,
    8,
    5,
    8,
    5,
    2,
    1,
    6,
    1,
    3,
    5,
    5,
    5,
    2,
    1,
    5,
    5,
    3,
    8,
    6,
    6,
    2,
    2,
    6,
    6,
    3,
    3,
    1,
    1,
    2,
    1,
    1,
    1,
    3,
    13,
    3,
    4,
    13,
    13,
    6,
    1,
    7,
    4,
    5,
    5,
    7,
    4,
    5,
    5,
    8,
    8,
    6,
    6,
    2,
    2,
    6,
    6,
    3,
    3,
    1,
    1,
    3,
    13,
    13,
    1,
    8,
    8,
    2,
    13,
    8,
    8,
    2,
    2,
    7,
    7,
    4,
    4,
    7,
    7,
    4,
    4,
    8,
    8,
    2,
    2,
    8,
    8,
    2,
    2,
    3,
    3,
    13,
    13,
    3,
    3,
    13,
    10,
    3,
    3,
    13,
    4,
    3,
    13,
    2,
    13,
    7,
    7,
    4,
    4,
    7,
    7,
    4,
    4,
    8,
    8,
    2,
    2,
    8,
    8,
    2,
    2,
    3,
    3,
    13,
    12,
    3,
    3,
    11,
    13,
)


def carpet_alignment_for_mask(mask: int) -> str:
    idx = int(mask) & 0xFF
    if idx < 0 or idx >= len(CARPET_TYPES_BY_MASK):
        return "center"
    carpet_type = int(CARPET_TYPES_BY_MASK[idx])
    return str(_CARPET_TYPE_TO_ALIGN.get(int(carpet_type), "center"))


def _normalize_carpet_align(align: str) -> str | None:
    key = str(align or "").strip().lower()
    if not key:
        return None
    key = _CARPET_ALIGNMENTS.get(key, key)
    if key in (
        "north",
        "south",
        "east",
        "west",
        "northwest",
        "northeast",
        "southwest",
        "southeast",
        "northwest_diagonal",
        "northeast_diagonal",
        "southwest_diagonal",
        "southeast_diagonal",
        "center",
        "none",
    ):
        return key
    return None


_DOOR_ALIGNMENTS: dict[str, str] = {
    "horizontal": "HORIZONTAL",
    "vertical": "VERTICAL",
    "h": "HORIZONTAL",
    "v": "VERTICAL",
}


def _normalize_door_alignment(align: str) -> str | None:
    key = str(align or "").strip().lower()
    if not key:
        return None
    key = _DOOR_ALIGNMENTS.get(key, key)
    if key in ("horizontal", "vertical"):
        key = key.upper()
    if key in ("HORIZONTAL", "VERTICAL"):
        return key
    return None


_XML_AMPERSAND_RE = re.compile(r"&(?!#\d+;|#x[0-9A-Fa-f]+;|\w+;)")


def _strip_invalid_xml_chars(text: str) -> str:
    return "".join(ch for ch in text if ch in ("\t", "\n", "\r") or ord(ch) >= 0x20)


def _parse_xml_root_tolerant(xml_path: str) -> Element:
    with open(xml_path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    raw = _strip_invalid_xml_chars(raw)
    raw = _XML_AMPERSAND_RE.sub("&amp;", raw)
    return ET.fromstring(raw)


def _int_attr(elem: Element, name: str) -> int | None:
    v = elem.get(name)
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def _bool_attr(elem: Element, name: str) -> bool:
    v = elem.get(name)
    if v is None:
        return False
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "y", "on")


def _parse_thickness(value: str) -> tuple[int, int]:
    s = str(value or "").strip()
    if not s:
        return 100, 100
    if "/" not in s:
        try:
            v = int(s)
        except ValueError:
            return 100, 100
        return max(0, v), max(1, v)
    left, right = s.split("/", 1)
    try:
        low = int(left)
        ceil = int(right)
    except ValueError:
        return 100, 100
    return max(0, low), max(1, ceil)


def _parse_doodad_items(parent: Element) -> tuple[DoodadItemChoice, ...]:
    out: list[DoodadItemChoice] = []
    for it in parent.findall("item"):
        item_id = _int_attr(it, "id")
        if item_id is None or int(item_id) <= 0:
            continue
        chance = _int_attr(it, "chance")
        if chance is None:
            chance = 10
        out.append(DoodadItemChoice(id=int(item_id), chance=max(0, int(chance))))
    return tuple(out)


def _parse_doodad_composite_tile_items(tile: Element) -> tuple[DoodadItemChoice, ...]:
    """Parse items inside a composite <tile>.

    Legacy behavior merges all items in the composite tile (stack semantics).
    Some datasets still include `chance` attributes on these items; legacy ignores
    those chances.
    """

    out: list[DoodadItemChoice] = []
    for it in tile.findall("item"):
        item_id = _int_attr(it, "id")
        if item_id is None or int(item_id) <= 0:
            continue
        out.append(DoodadItemChoice(id=int(item_id), chance=1))
    return tuple(out)


def _parse_doodad_composites(parent: Element) -> tuple[DoodadCompositeChoice, ...]:
    comps: list[DoodadCompositeChoice] = []
    for comp in parent.findall("composite"):
        chance = _int_attr(comp, "chance")
        if chance is None:
            chance = 10
        tiles: list[DoodadTilePlacement] = []
        for tile in comp.findall("tile"):
            dx = _int_attr(tile, "x")
            dy = _int_attr(tile, "y")
            dz = _int_attr(tile, "z")
            if dx is None or dy is None:
                continue
            if dz is None:
                dz = 0
            items = _parse_doodad_composite_tile_items(tile)
            if not items:
                continue
            tiles.append(DoodadTilePlacement(dx=int(dx), dy=int(dy), dz=int(dz), items=items, choose_one=False))
        if tiles:
            comps.append(DoodadCompositeChoice(chance=max(0, int(chance)), tiles=tuple(tiles)))
    return tuple(comps)


def _parse_doodad_alternative(parent: Element) -> DoodadAlternative:
    items = _parse_doodad_items(parent)
    composites = _parse_doodad_composites(parent)
    return DoodadAlternative(items=items, composites=composites)


def _brush_primary_server_id(brush: Element) -> int | None:
    sid = _int_attr(brush, "server_lookid")
    if sid is None:
        sid = _int_attr(brush, "lookid")
    if sid is not None and int(sid) > 0:
        return int(sid)
    # Fallback: pick first `<item>` id.
    items = _parse_doodad_items(brush)
    if items:
        return int(items[0].id)
    return None


def _parse_doodad_brush(brush: Element) -> DoodadBrushSpec | None:
    name = str(brush.get("name") or "").strip()
    server_id = _brush_primary_server_id(brush)
    if server_id is None or int(server_id) <= 0:
        return None

    draggable = str(brush.get("draggable") or "").strip().lower() != "false"
    on_duplicate = str(brush.get("on_duplicate") or "").strip().lower() == "true"
    on_blocking = str(brush.get("on_blocking") or "").strip().lower() == "true"
    redo_borders = str(brush.get("redo_borders") or "").strip().lower() == "true"
    one_size = str(brush.get("one_size") or "").strip().lower() == "true"
    thickness_low, thickness_ceil = _parse_thickness(str(brush.get("thickness") or ""))

    # Base alternative comes from the brush node itself (excluding nested alternates).
    base_alt = _parse_doodad_alternative(brush)

    alts: list[DoodadAlternative] = []
    if base_alt.items or base_alt.composites:
        alts.append(base_alt)

    for alt_node in brush.findall("alternate"):
        alt_spec = _parse_doodad_alternative(alt_node)
        if alt_spec.items or alt_spec.composites:
            alts.append(alt_spec)

    if not alts:
        # Even empty definitions can exist; skip for now.
        return None

    return DoodadBrushSpec(
        name=name or f"doodad:{int(server_id)}",
        server_id=int(server_id),
        thickness_low=int(thickness_low),
        thickness_ceil=int(thickness_ceil),
        draggable=bool(draggable),
        on_duplicate=bool(on_duplicate),
        on_blocking=bool(on_blocking),
        redo_borders=bool(redo_borders),
        one_size=bool(one_size),
        alternatives=tuple(alts),
    )


def _parse_table_items(table_node: Element, warnings: list[str], brush_name: str) -> tuple[TableItemChoice, ...]:
    out: list[TableItemChoice] = []
    for it in table_node.findall("item"):
        item_id = _int_attr(it, "id")
        if item_id is None or int(item_id) <= 0:
            warnings.append(f"Table brush {brush_name!r} missing id for item node")
            continue
        chance = _int_attr(it, "chance")
        if chance is None:
            chance = 1
        if int(chance) < 0:
            warnings.append(f"Chance for table item {int(item_id)} is negative, defaulting to 0.")
            chance = 0
        out.append(TableItemChoice(id=int(item_id), chance=max(0, int(chance))))
    return tuple(out)


def _parse_table_brush(brush: Element, warnings: list[str]) -> TableBrushSpec | None:
    name = str(brush.get("name") or "").strip()
    server_id = _int_attr(brush, "server_lookid")
    if server_id is None:
        server_id = _int_attr(brush, "lookid")
    if server_id is not None and int(server_id) <= 0:
        server_id = None

    items_by_alignment: dict[str, list[TableItemChoice]] = {}
    for table_node in brush.findall("table"):
        align_raw = table_node.get("align") or ""
        if not str(align_raw).strip():
            warnings.append(f"Table brush {name!r} missing alignment tag")
            continue
        align = _normalize_table_align(align_raw)
        if align is None:
            warnings.append(f"Unknown table alignment {align_raw!r} on brush {name!r}")
            continue
        items = _parse_table_items(table_node, warnings, name or "table")
        if not items:
            continue
        items_by_alignment.setdefault(str(align), []).extend(items)

    if not items_by_alignment:
        return None

    if server_id is None:
        for choices in items_by_alignment.values():
            for choice in choices:
                if int(choice.id) > 0:
                    server_id = int(choice.id)
                    break
            if server_id is not None:
                break

    if server_id is None or int(server_id) <= 0:
        warnings.append(f"Table brush {name!r} missing server id")
        return None

    items_by_alignment_tuple = {k: tuple(v) for k, v in items_by_alignment.items()}
    return TableBrushSpec(
        name=name or f"table:{int(server_id)}",
        server_id=int(server_id),
        items_by_alignment=items_by_alignment_tuple,
    )


def _parse_carpet_items(
    carpet_node: Element,
    warnings: list[str],
    brush_name: str,
) -> tuple[tuple[CarpetItemChoice, ...], bool]:
    out: list[CarpetItemChoice] = []
    had_item_nodes = False
    for it in carpet_node.findall("item"):
        had_item_nodes = True
        item_id = _int_attr(it, "id")
        if item_id is None or int(item_id) <= 0:
            warnings.append(f"Carpet brush {brush_name!r} missing id for item node")
            continue
        chance = _int_attr(it, "chance")
        if chance is None:
            warnings.append(f"Carpet brush {brush_name!r} missing chance for item id {int(item_id)}")
            continue
        if int(chance) < 0:
            warnings.append(f"Chance for carpet item {int(item_id)} is negative, defaulting to 0.")
            chance = 0
        out.append(CarpetItemChoice(id=int(item_id), chance=max(0, int(chance))))
    return tuple(out), had_item_nodes


def _parse_carpet_brush(brush: Element, warnings: list[str]) -> CarpetBrushSpec | None:
    name = str(brush.get("name") or "").strip()
    server_id = _int_attr(brush, "server_lookid")
    if server_id is None:
        server_id = _int_attr(brush, "lookid")
    if server_id is not None and int(server_id) <= 0:
        server_id = None

    items_by_alignment: dict[str, list[CarpetItemChoice]] = {}
    for carpet_node in brush.findall("carpet"):
        align_raw = carpet_node.get("align") or ""
        align = _normalize_carpet_align(align_raw)
        if align is None:
            warnings.append(f"Unknown carpet alignment {align_raw!r} on brush {name!r}")
            continue

        items, had_item_nodes = _parse_carpet_items(carpet_node, warnings, name or "carpet")
        if items:
            items_by_alignment.setdefault(str(align), []).extend(items)
            continue
        if had_item_nodes:
            continue

        local_id = _int_attr(carpet_node, "id")
        if local_id is None or int(local_id) <= 0:
            warnings.append(f"Carpet brush {name!r} missing id for align {align_raw!r}")
            continue
        items_by_alignment.setdefault(str(align), []).append(CarpetItemChoice(id=int(local_id), chance=1))

    if not items_by_alignment:
        return None

    if server_id is None:
        for choices in items_by_alignment.values():
            for choice in choices:
                if int(choice.id) > 0:
                    server_id = int(choice.id)
                    break
            if server_id is not None:
                break

    if server_id is None or int(server_id) <= 0:
        warnings.append(f"Carpet brush {name!r} missing server id")
        return None

    items_by_alignment_tuple = {k: tuple(v) for k, v in items_by_alignment.items()}
    return CarpetBrushSpec(
        name=name or f"carpet:{int(server_id)}",
        server_id=int(server_id),
        items_by_alignment=items_by_alignment_tuple,
    )


_DOOR_TYPE_LABELS: dict[str, tuple[DoorType, ...]] = {
    "normal": (DoorType.NORMAL,),
    "locked": (DoorType.LOCKED,),
    "magic": (DoorType.MAGIC,),
    "quest": (DoorType.QUEST,),
    "window": (DoorType.WINDOW,),
    "hatch window": (DoorType.HATCH,),
    "archway": (DoorType.ARCHWAY,),
}

_ALL_DOOR_TYPES: tuple[DoorType, ...] = (
    DoorType.ARCHWAY,
    DoorType.NORMAL,
    DoorType.LOCKED,
    DoorType.QUEST,
    DoorType.MAGIC,
)
_ALL_WINDOW_TYPES: tuple[DoorType, ...] = (DoorType.WINDOW, DoorType.HATCH)


def _normalize_door_label(label: str) -> str:
    s = str(label or "").strip().lower().replace("_", " ")
    return " ".join(s.split())


def _door_types_from_label(label: str) -> tuple[DoorType, ...]:
    key = _normalize_door_label(label)
    if not key:
        return ()
    if key in ("any door", "any doors"):
        return _ALL_DOOR_TYPES
    if key in ("any window", "any windows"):
        return _ALL_WINDOW_TYPES
    if key == "any":
        return _ALL_DOOR_TYPES + _ALL_WINDOW_TYPES
    if key == "hatch":
        return (DoorType.HATCH,)
    if key == "hatch window":
        return (DoorType.HATCH,)
    if key == "hatchwindow":
        return (DoorType.HATCH,)
    return _DOOR_TYPE_LABELS.get(key, ())


def _parse_door_items(wall_node: Element, warnings: list[str]) -> tuple[DoorItemSpec, ...]:
    out: list[DoorItemSpec] = []
    for door_node in wall_node.findall("door"):
        item_id = _int_attr(door_node, "id")
        if item_id is None or int(item_id) <= 0:
            continue

        label = door_node.get("type") or ""
        door_types = _door_types_from_label(label)
        if not door_types:
            warnings.append(f"Unknown door type {label!r}")
            continue

        is_open = _bool_attr(door_node, "open")
        for door_type in door_types:
            out.append(DoorItemSpec(id=int(item_id), door_type=door_type, is_open=bool(is_open)))
    return tuple(out)


def _parse_door_brush(brush: Element, warnings: list[str]) -> DoorBrushSpec | None:
    name = str(brush.get("name") or "").strip()
    server_id = _int_attr(brush, "server_lookid")
    if server_id is None:
        server_id = _int_attr(brush, "lookid")
    if server_id is not None and int(server_id) <= 0:
        server_id = None

    items_by_alignment: dict[str, list[DoorItemSpec]] = {}
    for wall_node in brush.findall("wall"):
        align_raw = wall_node.get("type") or ""
        align = _normalize_door_alignment(align_raw)
        if align is None:
            continue
        items = _parse_door_items(wall_node, warnings)
        if not items:
            continue
        items_by_alignment.setdefault(str(align), []).extend(items)

    if not items_by_alignment:
        return None

    if server_id is None or int(server_id) <= 0:
        warnings.append(f"Door spec {name!r} missing server id")
        return None

    items_by_alignment_tuple = {k: tuple(v) for k, v in items_by_alignment.items()}
    return DoorBrushSpec(
        name=name or f"door:{int(server_id)}",
        server_id=int(server_id),
        items_by_alignment=items_by_alignment_tuple,
    )
