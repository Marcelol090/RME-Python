"""Clipboard System for map editing.

Provides copy/cut/paste functionality with:
- Visual selection preview
- Multiple format support (tiles, items, selection)
- Clipboard history
- Paste preview overlay
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from py_rme_canary.core.data.creature import Monster, Npc, Outfit
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.spawns import MonsterSpawnArea, NpcSpawnArea
    from py_rme_canary.core.data.tile import Tile

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ClipboardEntry:
    """Single clipboard entry containing copied data."""

    entry_type: str = ""  # "tiles", "items", "selection"
    data: Any = None
    width: int = 0
    height: int = 0
    timestamp: float = 0.0
    source_position: tuple[int, int, int] | None = None
    # Compatibility fields for older tests/consumers.
    tiles: list[Any] | None = None
    origin_x: int = 0
    origin_y: int = 0
    origin_z: int = 0

    def __post_init__(self) -> None:
        if self.source_position is not None:
            self.origin_x, self.origin_y, self.origin_z = (
                int(self.source_position[0]),
                int(self.source_position[1]),
                int(self.source_position[2]),
            )
        elif self.tiles is not None:
            self.source_position = (int(self.origin_x), int(self.origin_y), int(self.origin_z))

        if self.tiles is None and isinstance(self.data, list) and self.entry_type.endswith("tiles"):
            self.tiles = self.data

        if not self.entry_type and self.tiles is not None:
            self.entry_type = "tiles"
            if self.data is None:
                self.data = self.tiles

        if self.tiles is not None and (self.width <= 0 or self.height <= 0):
            xs: list[int] = []
            ys: list[int] = []
            for tile in self.tiles:
                if hasattr(tile, "x"):
                    xs.append(int(tile.x))
                elif hasattr(tile, "rel_x"):
                    xs.append(int(tile.rel_x))
                if hasattr(tile, "y"):
                    ys.append(int(tile.y))
                elif hasattr(tile, "rel_y"):
                    ys.append(int(tile.rel_y))
            if xs and self.width <= 0:
                self.width = max(xs) - min(xs) + 1
            if ys and self.height <= 0:
                self.height = max(ys) - min(ys) + 1

    def tile_count(self) -> int:
        """Get number of tiles in this entry."""
        if self.tiles is not None:
            return len(self.tiles)
        if isinstance(self.data, (dict, list)):
            return len(self.data)
        return 0


@dataclass(slots=True)
class TileData:
    """Serialized tile data for clipboard."""

    rel_x: int  # Relative position from copy origin
    rel_y: int
    rel_z: int
    ground_id: int | None = None
    ground_name: str | None = None
    items: list[dict] = field(default_factory=list)
    monsters: list[dict] = field(default_factory=list)
    npc: dict | None = None
    spawn_monster: dict | None = None
    spawn_npc: dict | None = None
    house_id: int | None = None
    map_flags: int = 0


def _serialize_outfit(outfit: object | None) -> dict | None:
    if outfit is None:
        return None
    return {
        "looktype": getattr(outfit, "looktype", None),
        "lookitem": getattr(outfit, "lookitem", None),
        "lookhead": int(getattr(outfit, "lookhead", 0) or 0),
        "lookbody": int(getattr(outfit, "lookbody", 0) or 0),
        "looklegs": int(getattr(outfit, "looklegs", 0) or 0),
        "lookfeet": int(getattr(outfit, "lookfeet", 0) or 0),
        "lookaddons": int(getattr(outfit, "lookaddons", 0) or 0),
    }


def _serialize_creature(creature: object | None) -> dict | None:
    if creature is None:
        return None
    return {
        "name": str(getattr(creature, "name", "")),
        "direction": int(getattr(creature, "direction", 2) or 2),
        "outfit": _serialize_outfit(getattr(creature, "outfit", None)),
    }


def _serialize_spawn_monster(spawn: object | None, origin: tuple[int, int, int]) -> dict | None:
    if spawn is None:
        return None
    center = getattr(spawn, "center", None)
    if center is None:
        return None
    monsters = []
    for entry in getattr(spawn, "monsters", ()):
        monsters.append(
            {
                "name": str(getattr(entry, "name", "")),
                "dx": int(getattr(entry, "dx", 0) or 0),
                "dy": int(getattr(entry, "dy", 0) or 0),
                "spawntime": int(getattr(entry, "spawntime", 0) or 0),
                "direction": getattr(entry, "direction", None),
                "weight": getattr(entry, "weight", None),
            }
        )
    return {
        "center_rel": {
            "x": int(center.x) - int(origin[0]),
            "y": int(center.y) - int(origin[1]),
            "z": int(center.z) - int(origin[2]),
        },
        "radius": int(getattr(spawn, "radius", 0) or 0),
        "monsters": monsters,
    }


def _serialize_spawn_npc(spawn: object | None, origin: tuple[int, int, int]) -> dict | None:
    if spawn is None:
        return None
    center = getattr(spawn, "center", None)
    if center is None:
        return None
    npcs = []
    for entry in getattr(spawn, "npcs", ()):
        npcs.append(
            {
                "name": str(getattr(entry, "name", "")),
                "dx": int(getattr(entry, "dx", 0) or 0),
                "dy": int(getattr(entry, "dy", 0) or 0),
                "spawntime": int(getattr(entry, "spawntime", 0) or 0),
                "direction": getattr(entry, "direction", None),
            }
        )
    return {
        "center_rel": {
            "x": int(center.x) - int(origin[0]),
            "y": int(center.y) - int(origin[1]),
            "z": int(center.z) - int(origin[2]),
        },
        "radius": int(getattr(spawn, "radius", 0) or 0),
        "npcs": npcs,
    }


def _deserialize_outfit(data: dict | None) -> Outfit | None:
    if not data:
        return None
    from py_rme_canary.core.data.creature import Outfit

    return Outfit(
        looktype=data.get("looktype"),
        lookitem=data.get("lookitem"),
        lookhead=int(data.get("lookhead", 0) or 0),
        lookbody=int(data.get("lookbody", 0) or 0),
        looklegs=int(data.get("looklegs", 0) or 0),
        lookfeet=int(data.get("lookfeet", 0) or 0),
        lookaddons=int(data.get("lookaddons", 0) or 0),
    )


def _deserialize_monster(data: dict | None) -> Monster | None:
    if not data:
        return None
    from py_rme_canary.core.data.creature import Monster

    outfit = _deserialize_outfit(data.get("outfit"))
    return Monster(
        name=str(data.get("name", "")),
        direction=int(data.get("direction", 2) or 2),
        outfit=outfit,
    )


def _deserialize_npc(data: dict | None) -> Npc | None:
    if not data:
        return None
    from py_rme_canary.core.data.creature import Npc

    outfit = _deserialize_outfit(data.get("outfit"))
    return Npc(
        name=str(data.get("name", "")),
        direction=int(data.get("direction", 2) or 2),
        outfit=outfit,
    )


def _deserialize_spawn_monster(data: dict | None, origin: tuple[int, int, int]) -> MonsterSpawnArea | None:
    if not data:
        return None
    from py_rme_canary.core.data.item import Position
    from py_rme_canary.core.data.spawns import MonsterSpawnArea, MonsterSpawnEntry

    center_rel = data.get("center_rel") or {}
    center_abs = data.get("center") or {}
    if center_rel:
        center = Position(
            x=int(origin[0]) + int(center_rel.get("x", 0) or 0),
            y=int(origin[1]) + int(center_rel.get("y", 0) or 0),
            z=int(origin[2]) + int(center_rel.get("z", 0) or 0),
        )
    else:
        center = Position(
            x=int(center_abs.get("x", 0) or 0),
            y=int(center_abs.get("y", 0) or 0),
            z=int(center_abs.get("z", 0) or 0),
        )
    entries = []
    for entry in data.get("monsters", []) or []:
        entries.append(
            MonsterSpawnEntry(
                name=str(entry.get("name", "")),
                dx=int(entry.get("dx", 0) or 0),
                dy=int(entry.get("dy", 0) or 0),
                spawntime=int(entry.get("spawntime", 0) or 0),
                direction=entry.get("direction"),
                weight=entry.get("weight"),
            )
        )
    return MonsterSpawnArea(
        center=center,
        radius=int(data.get("radius", 0) or 0),
        monsters=tuple(entries),
    )


def _deserialize_spawn_npc(data: dict | None, origin: tuple[int, int, int]) -> NpcSpawnArea | None:
    if not data:
        return None
    from py_rme_canary.core.data.item import Position
    from py_rme_canary.core.data.spawns import NpcSpawnArea, NpcSpawnEntry

    center_rel = data.get("center_rel") or {}
    center_abs = data.get("center") or {}
    if center_rel:
        center = Position(
            x=int(origin[0]) + int(center_rel.get("x", 0) or 0),
            y=int(origin[1]) + int(center_rel.get("y", 0) or 0),
            z=int(origin[2]) + int(center_rel.get("z", 0) or 0),
        )
    else:
        center = Position(
            x=int(center_abs.get("x", 0) or 0),
            y=int(center_abs.get("y", 0) or 0),
            z=int(center_abs.get("z", 0) or 0),
        )
    entries = []
    for entry in data.get("npcs", []) or []:
        entries.append(
            NpcSpawnEntry(
                name=str(entry.get("name", "")),
                dx=int(entry.get("dx", 0) or 0),
                dy=int(entry.get("dy", 0) or 0),
                spawntime=int(entry.get("spawntime", 0) or 0),
                direction=entry.get("direction"),
            )
        )
    return NpcSpawnArea(
        center=center,
        radius=int(data.get("radius", 0) or 0),
        npcs=tuple(entries),
    )


class ClipboardManager:
    """Manages the editor clipboard with history.

    Features:
    - Copy/cut/paste tiles and items
    - Clipboard history (last N entries)
    - Paste preview
    - Rotation and flipping

    Usage:
        clipboard = ClipboardManager.instance()

        # Copy tiles
        clipboard.copy_tiles(selected_tiles, origin)

        # Paste
        if clipboard.can_paste():
            preview = clipboard.get_paste_preview(target_pos)
            clipboard.paste_at(target_pos, editor_session)
    """

    _instance: ClipboardManager | None = None
    MAX_HISTORY = 10

    def __init__(self) -> None:
        self._current: ClipboardEntry | None = None
        self._history: list[ClipboardEntry] = []
        self._rotation: int = 0  # 0, 90, 180, 270 degrees
        self._flip_horizontal: bool = False
        self._flip_vertical: bool = False

    @classmethod
    def instance(cls) -> ClipboardManager:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def copy_tiles(
        self,
        tiles: list[Tile],
        origin: tuple[int, int, int] | None = None,
        name_lookup: Any | None = None,
    ) -> bool:
        """Copy tiles to clipboard.

        Args:
            tiles: List of tiles to copy
            origin: Origin position for relative coordinates
            name_lookup: Optional callable(server_id) -> str to resolve item names
        """
        if not tiles:
            return False

        import time

        # Determine bounds
        min_x = min(t.x for t in tiles)
        max_x = max(t.x for t in tiles)
        min_y = min(t.y for t in tiles)
        max_y = max(t.y for t in tiles)
        min_z = min(t.z for t in tiles)

        if origin is None:
            origin = (min_x, min_y, min_z)

        # Serialize tiles
        tile_data_list: list[TileData] = []

        for tile in tiles:
            rel_x = tile.x - origin[0]
            rel_y = tile.y - origin[1]
            rel_z = tile.z - origin[2]

            # Serialize items
            items = []
            for item in getattr(tile, "items", []):
                item_dict = {
                    "id": item.id,
                    "count": getattr(item, "count", 1),
                    "action_id": getattr(item, "action_id", 0),
                    "unique_id": getattr(item, "unique_id", 0),
                    "text": getattr(item, "text", None),
                }
                if name_lookup:
                    item_dict["name"] = name_lookup(int(item.id))
                items.append(item_dict)

            ground_name = None
            if tile.ground and name_lookup:
                ground_name = name_lookup(int(tile.ground.id))

            monsters = []
            for creature in getattr(tile, "monsters", []) or []:
                payload = _serialize_creature(creature)
                if payload is not None:
                    monsters.append(payload)

            npc = _serialize_creature(getattr(tile, "npc", None))

            spawn_monster = _serialize_spawn_monster(getattr(tile, "spawn_monster", None), origin)
            spawn_npc = _serialize_spawn_npc(getattr(tile, "spawn_npc", None), origin)

            td = TileData(
                rel_x=rel_x,
                rel_y=rel_y,
                rel_z=rel_z,
                ground_id=tile.ground.id if tile.ground else None,
                ground_name=str(ground_name) if ground_name else None,
                items=items,
                monsters=monsters,
                npc=npc,
                spawn_monster=spawn_monster,
                spawn_npc=spawn_npc,
                house_id=getattr(tile, "house_id", None),
                map_flags=int(getattr(tile, "map_flags", 0) or 0),
            )

            tile_data_list.append(td)

        # Create entry
        entry = ClipboardEntry(
            entry_type="tiles",
            data=tile_data_list,
            tiles=tile_data_list,
            width=max_x - min_x + 1,
            height=max_y - min_y + 1,
            timestamp=time.time(),
            source_position=origin,
        )

        self._set_current(entry)
        logger.debug(f"Copied {len(tiles)} tiles to clipboard")
        return True

    def copy(self, tiles: list[Any], origin_x: int, origin_y: int, origin_z: int | None = None) -> bool:
        """Compatibility wrapper for older clipboard API."""
        if origin_z is None:
            origin_z = int(getattr(tiles[0], "z", 0)) if tiles else 0
        return self.copy_tiles(tiles, (int(origin_x), int(origin_y), int(origin_z)))

    def copy_items(
        self,
        items: list[Item],
        source_pos: tuple[int, int, int] | None = None,
        name_lookup: Any | None = None,
    ) -> bool:
        """Copy items to clipboard."""
        if not items:
            return False

        import time

        item_data = []
        for item in items:
            d = {
                "id": item.id,
                "count": getattr(item, "count", 1),
                "action_id": getattr(item, "action_id", 0),
                "unique_id": getattr(item, "unique_id", 0),
                "text": getattr(item, "text", None),
            }
            if name_lookup:
                d["name"] = name_lookup(int(item.id))
            item_data.append(d)

        entry = ClipboardEntry(entry_type="items", data=item_data, timestamp=time.time(), source_position=source_pos)

        self._set_current(entry)
        logger.debug(f"Copied {len(items)} items to clipboard")
        return True

    def cut_tiles(self, tiles: list[Tile], origin: tuple[int, int, int] | None = None) -> bool:
        """Cut tiles (copy + mark for deletion after paste).

        Args:
            tiles: Tiles to cut
            origin: Origin position

        Returns:
            True if cut successfully
        """
        # Copy first
        if not self.copy_tiles(tiles, origin):
            return False

        # Mark as cut operation
        if self._current:
            self._current.entry_type = "cut_tiles"

        return True

    def cut(self, tiles: list[Any], origin_x: int, origin_y: int, origin_z: int | None = None) -> bool:
        """Compatibility wrapper for older clipboard API."""
        if origin_z is None:
            origin_z = int(getattr(tiles[0], "z", 0)) if tiles else 0
        return self.cut_tiles(tiles, (int(origin_x), int(origin_y), int(origin_z)))

    def _set_current(self, entry: ClipboardEntry) -> None:
        """Set current clipboard entry and add to history."""
        # Add previous to history
        if self._current:
            self._history.insert(0, self._current)
            # Trim history
            if len(self._history) > self.MAX_HISTORY:
                self._history = self._history[: self.MAX_HISTORY]

        self._current = entry
        # Reset transforms
        self._rotation = 0
        self._flip_horizontal = False
        self._flip_vertical = False

    def can_paste(self) -> bool:
        """Check if clipboard has content."""
        return self._current is not None

    def is_cut_operation(self) -> bool:
        """Check if current clipboard entry is a cut operation."""
        return bool(self._current and self._current.entry_type == "cut_tiles")

    def get_paste_preview(self, target: tuple[int, int, int]) -> list[tuple[int, int, int]]:
        """Get positions that would be affected by paste.

        Args:
            target: Target paste position

        Returns:
            List of (x, y, z) positions that would be modified
        """
        if not self._current:
            return []

        positions = []

        if self._current.entry_type in ("tiles", "cut_tiles"):
            for tile_data in self._current.data:
                x = target[0] + tile_data.rel_x
                y = target[1] + tile_data.rel_y
                z = target[2] + tile_data.rel_z

                # Apply transforms
                x, y = self._apply_transform(
                    tile_data.rel_x, tile_data.rel_y, self._current.width, self._current.height
                )
                x += target[0]
                y += target[1]

                positions.append((x, y, z))

        return positions

    def get_paste_positions(self, x: int, y: int, z: int) -> list[tuple[int, int, int]]:
        """Compatibility wrapper returning paste positions."""
        return self.get_paste_preview((int(x), int(y), int(z)))

    def _apply_transform(self, rel_x: int, rel_y: int, width: int, height: int) -> tuple[int, int]:
        """Apply rotation and flip transforms."""
        x, y = rel_x, rel_y

        # Rotation
        if self._rotation == 90:
            x, y = height - 1 - y, x
        elif self._rotation == 180:
            x, y = width - 1 - x, height - 1 - y
        elif self._rotation == 270:
            x, y = y, width - 1 - x

        # Flip
        if self._flip_horizontal:
            x = width - 1 - x
        if self._flip_vertical:
            y = height - 1 - y

        return x, y

    def rotate_clockwise(self) -> None:
        """Rotate clipboard content 90 degrees clockwise."""
        self._rotation = (self._rotation + 90) % 360

    def rotate_90(self) -> None:
        """Compatibility wrapper for 90 degree rotation."""
        self.rotate_clockwise()

    def rotate_counterclockwise(self) -> None:
        """Rotate clipboard content 90 degrees counter-clockwise."""
        self._rotation = (self._rotation - 90) % 360

    def flip_horizontal(self) -> None:
        """Flip clipboard content horizontally."""
        self._flip_horizontal = not self._flip_horizontal

    def flip_vertical(self) -> None:
        """Flip clipboard content vertically."""
        self._flip_vertical = not self._flip_vertical

    def paste_at(self, target: tuple[int, int, int], session: object) -> bool:
        """Paste clipboard content at target position.

        Args:
            target: Target (x, y, z) position
            session: EditorSession for creating commands

        Returns:
            True if pasted successfully
        """
        if not self._current:
            return False

        try:
            # Implementation would create appropriate commands
            # based on entry type and apply to session

            if self._current.entry_type in ("tiles", "cut_tiles"):
                # Would create PasteCommand
                logger.info(f"Pasting {self._current.tile_count()} tiles at {target}")
                # session.paste_tiles(self._current.data, target, ...)
                return True

            elif self._current.entry_type == "items":
                # Would create AddItemsCommand
                logger.info(f"Pasting {len(self._current.data)} items at {target}")
                return True

        except Exception as e:
            logger.error(f"Paste failed: {e}")

        return False

    def get_current(self) -> ClipboardEntry | None:
        """Get current clipboard entry."""
        return self._current

    def get_history(self) -> list[ClipboardEntry]:
        """Get clipboard history."""
        if self._current is None:
            return self._history.copy()
        combined = [self._current] + self._history
        return combined[: self.MAX_HISTORY]

    def clear(self) -> None:
        """Clear clipboard."""
        self._current = None
        self._history.clear()

    def to_system_clipboard(self, client_version: str | None = None) -> bool:
        """Copy current entry to system clipboard as JSON.

        Allows copy between editor instances.
        Args:
            client_version: String identifying client version (e.g. "8.60")
        """
        if not self._current:
            return False

        try:
            from PyQt6.QtCore import QMimeData
            from PyQt6.QtWidgets import QApplication

            # Serialize to JSON
            serialized_tiles = []
            if self._current.entry_type.endswith("tiles"):
                for td in self._current.data:
                    tile_dict = {
                        "rel_x": td.rel_x,
                        "rel_y": td.rel_y,
                        "rel_z": td.rel_z,
                        "ground_id": td.ground_id,
                        "ground_name": td.ground_name,
                        "items": td.items,
                        "monsters": td.monsters,
                        "npc": td.npc,
                        "spawn_monster": td.spawn_monster,
                        "spawn_npc": td.spawn_npc,
                        "house_id": td.house_id,
                        "map_flags": td.map_flags,
                    }
                    serialized_tiles.append(tile_dict)

            origin_payload = None
            if self._current.source_position is not None:
                origin_payload = {
                    "x": int(self._current.source_position[0]),
                    "y": int(self._current.source_position[1]),
                    "z": int(self._current.source_position[2]),
                }

            data = {
                "type": self._current.entry_type,
                "version": client_version,
                "width": self._current.width,
                "height": self._current.height,
                "origin": origin_payload,
                "tiles": serialized_tiles if self._current.entry_type.endswith("tiles") else [],
                "items": self._current.data if self._current.entry_type == "items" else [],
            }

            json_str = json.dumps(data)

            # Application/x-pyrme-clipboard
            MIME_TYPE = "application/x-pyrme-clipboard"

            clipboard = QApplication.clipboard()
            if clipboard:
                mime = QMimeData()
                mime.setData(MIME_TYPE, json_str.encode())

                # Text fallback
                version_str = f" [v{client_version}]" if client_version else ""
                count_str = (
                    f"{self._current.tile_count()} tiles"
                    if self._current.entry_type.endswith("tiles")
                    else f"{len(self._current.data)} items"
                )
                mime.setText(f"[py_rme{version_str}] {count_str}")

                clipboard.setMimeData(mime)
                return True

        except Exception as e:
            logger.error(f"Failed to copy to system clipboard: {e}")

        return False

    def from_system_clipboard(
        self,
        target_version: str | None = None,
        name_resolver: Any | None = None,
    ) -> bool:
        """Import from system clipboard if compatible.

        Args:
            target_version: Version of the target map/session
            name_resolver: Optional callable(name) -> server_id to resolve IDs

        Returns:
            True if imported successfully
        """
        try:
            from PyQt6.QtWidgets import QApplication

            clipboard = QApplication.clipboard()
            if not clipboard:
                return False

            mime = clipboard.mimeData()
            if not mime:
                return False

            MIME_TYPE = "application/x-pyrme-clipboard"
            # Check for our format
            if mime.hasFormat(MIME_TYPE):
                data_bytes = mime.data(MIME_TYPE)
                json_str = data_bytes.data().decode()
                data = json.loads(json_str)

                source_version = data.get("version")

                # Check for version mismatch
                if source_version and target_version and source_version != target_version:
                    logger.warning(f"Clipboard version mismatch: Source {source_version} -> Target {target_version}")
                    self._convert_data(data, source_version, target_version, name_resolver)

                # Reconstruct entry
                import time

                if data.get("type", "").endswith("tiles"):
                    tile_data_list = [
                        TileData(
                            rel_x=td["rel_x"],
                            rel_y=td["rel_y"],
                            rel_z=td["rel_z"],
                            ground_id=td.get("ground_id"),
                            ground_name=td.get("ground_name"),
                            items=td.get("items", []),
                            monsters=td.get("monsters", []) or [],
                            npc=td.get("npc"),
                            spawn_monster=td.get("spawn_monster"),
                            spawn_npc=td.get("spawn_npc"),
                            house_id=td.get("house_id"),
                            map_flags=td.get("map_flags", 0),
                        )
                        for td in data.get("tiles", [])
                    ]

                    origin = data.get("origin") or {}
                    source_position = None
                    if origin:
                        source_position = (
                            int(origin.get("x", 0) or 0),
                            int(origin.get("y", 0) or 0),
                            int(origin.get("z", 0) or 0),
                        )

                    entry = ClipboardEntry(
                        entry_type=data["type"],
                        data=tile_data_list,
                        width=data.get("width", 0),
                        height=data.get("height", 0),
                        timestamp=time.time(),
                        source_position=source_position,
                    )
                    self._set_current(entry)
                    return True

                elif data.get("type") == "items":
                    items_data = data.get("items", [])
                    entry = ClipboardEntry(
                        entry_type="items",
                        data=items_data,
                        timestamp=time.time(),
                    )
                    self._set_current(entry)
                    return True

        except Exception as e:
            logger.debug(f"System clipboard import failed: {e}")

        return False

    def _convert_data(
        self,
        data: dict,
        source_v: str,
        target_v: str,
        name_resolver: Any | None = None,
    ) -> None:
        """Convert clipboard data between versions."""
        if not name_resolver:
            logger.warning("No name resolver provided for version conversion.")
            return

        logger.info(f"Converting clipboard data from {source_v} to {target_v}...")

        # Helper to convert a single item dict
        def convert_item(item_dict: dict) -> None:
            nm = item_dict.get("name")
            if nm:
                new_id = name_resolver(str(nm))
                if new_id is not None:
                    item_dict["id"] = int(new_id)

        # Convert tiles
        tiles = data.get("tiles", [])
        for tile in tiles:
            # Ground
            ground_name = tile.get("ground_name")
            if ground_name:
                resolved = name_resolver(str(ground_name))
                if resolved is not None:
                    tile["ground_id"] = int(resolved)

            # Stack items
            for item in tile.get("items", []):
                convert_item(item)

        # Convert simple item list (if type==items)
        items_list = data.get("items", [])
        if isinstance(items_list, list):
            for item in items_list:
                convert_item(item)


def tiles_from_entry(entry: ClipboardEntry) -> tuple[list[Tile], tuple[int, int, int]] | None:
    """Convert a clipboard entry into concrete Tile objects.

    Returns:
        Tuple of (tiles, origin) or None if entry is not tile-based.
    """
    if entry is None or not entry.entry_type.endswith("tiles"):
        return None

    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.tile import Tile

    origin = entry.source_position or (0, 0, 0)
    tiles: list[Tile] = []

    for td in entry.data:
        x = int(origin[0]) + int(td.rel_x)
        y = int(origin[1]) + int(td.rel_y)
        z = int(origin[2]) + int(td.rel_z)

        ground = Item(id=int(td.ground_id)) if td.ground_id is not None else None
        items: list[Item] = []
        for item in td.items:
            items.append(
                Item(
                    id=int(item.get("id", 0) or 0),
                    count=item.get("count"),
                    action_id=item.get("action_id"),
                    unique_id=item.get("unique_id"),
                    text=item.get("text"),
                )
            )

        monsters = []
        for payload in td.monsters:
            monster = _deserialize_monster(payload)
            if monster is not None:
                monsters.append(monster)

        npc = _deserialize_npc(td.npc)
        spawn_monster = _deserialize_spawn_monster(td.spawn_monster, origin)
        spawn_npc = _deserialize_spawn_npc(td.spawn_npc, origin)

        tiles.append(
            Tile(
                x=int(x),
                y=int(y),
                z=int(z),
                ground=ground,
                items=items,
                house_id=td.house_id,
                map_flags=int(td.map_flags),
                monsters=monsters,
                npc=npc,
                spawn_monster=spawn_monster,
                spawn_npc=spawn_npc,
            )
        )

    return tiles, (int(origin[0]), int(origin[1]), int(origin[2]))
