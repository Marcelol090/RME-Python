from __future__ import annotations

import json
import logging
import os
import re
import zlib
from collections.abc import Iterable
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

from py_rme_canary.core.io.creatures_xml import load_monster_names, load_npc_names

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

    # Optional: ground brush randomization variants.
    # If present, `randomize_ids` defines a set of candidate ground server_ids
    # to re-roll between for Randomize Selection/Map.
    randomize_ids: tuple[int, ...] = ()

    # Optional: richer doodad brush spec parsed from RME materials XML.
    doodad_spec: DoodadBrushSpec | None = None

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

    # Optional doodad specs from RME materials XML.
    # Keyed by real server id (lookid/server_lookid).
    _doodads: dict[int, DoodadBrushSpec] = field(default_factory=dict)
    _doodads_loaded: bool = False
    _doodads_source_path: str | None = None
    _doodads_warnings: list[str] = field(default_factory=list)

    @classmethod
    def from_json_file(cls, json_path: str) -> BrushManager:
        mgr = cls()
        mgr.load_from_file(json_path)
        return mgr

    def load_from_file(self, json_path: str) -> None:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        brushes = data.get("brushes", [])
        if not isinstance(brushes, list):
            raise ValueError("Invalid brushes.json: 'brushes' must be a list")

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
                if not isinstance(randomize_raw, (list, tuple)):
                    raise ValueError(f"Invalid brushes.json: randomize_ids for {name!r} must be a list")
                randomize_ids = tuple(int(v) for v in randomize_raw if int(v) != 0)

            brush = BrushDefinition(
                name=name,
                server_id=server_id,
                brush_type=brush_type,
                borders=borders,
                transition_borders=transition_borders,
                randomize_ids=randomize_ids,
            )
            self._brushes[server_id] = brush

            # Reverse lookup: allow finding a brush by any id in its family.
            # If collisions exist, first loaded wins (stable + predictable).
            for fid in brush.family_ids:
                self._family_index.setdefault(int(fid), int(server_id))

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


_XML_AMPERSAND_RE = re.compile(r"&(?!#\d+;|#x[0-9A-Fa-f]+;|\w+;)")


def _strip_invalid_xml_chars(text: str) -> str:
    return "".join(ch for ch in text if ch in ("\t", "\n", "\r") or ord(ch) >= 0x20)


def _parse_xml_root_tolerant(xml_path: str) -> ET.Element:
    with open(xml_path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    raw = _strip_invalid_xml_chars(raw)
    raw = _XML_AMPERSAND_RE.sub("&amp;", raw)
    return ET.fromstring(raw)


def _int_attr(elem: ET.Element, name: str) -> int | None:
    v = elem.get(name)
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


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


def _parse_doodad_items(parent: ET.Element) -> tuple[DoodadItemChoice, ...]:
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


def _parse_doodad_composite_tile_items(tile: ET.Element) -> tuple[DoodadItemChoice, ...]:
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


def _parse_doodad_composites(parent: ET.Element) -> tuple[DoodadCompositeChoice, ...]:
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


def _parse_doodad_alternative(parent: ET.Element) -> DoodadAlternative:
    items = _parse_doodad_items(parent)
    composites = _parse_doodad_composites(parent)
    return DoodadAlternative(items=items, composites=composites)


def _brush_primary_server_id(brush: ET.Element) -> int | None:
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


def _parse_doodad_brush(brush: ET.Element) -> DoodadBrushSpec | None:
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
