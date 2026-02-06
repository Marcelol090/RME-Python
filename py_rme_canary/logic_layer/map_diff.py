"""Map Compare/Diff System.

This module provides tools for comparing two maps and finding differences.
Essential for version control, backup verification, and collaborative editing.

Reference:
    - Common feature in diff tools (git diff, WinMerge)
    - Map versioning workflows

Features:
    - MapDiff: Compare two GameMap instances
    - TileDiff: Detailed tile-level differences
    - DiffReport: Summary and detailed change report
    - Patch generation for applying changes

Layer: logic_layer (no PyQt6 dependencies)
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.tile import Tile

logger = logging.getLogger(__name__)


# Position type alias
Position = tuple[int, int, int]  # (x, y, z)


class ChangeType(Enum):
    """Type of change detected."""

    ADDED = auto()  # New tile/item added
    REMOVED = auto()  # Tile/item removed
    MODIFIED = auto()  # Tile/item modified
    UNCHANGED = auto()  # No change


class DiffLevel(Enum):
    """Level of detail for diff comparison."""

    TILE_EXISTS = auto()  # Only check if tiles exist
    GROUND_ONLY = auto()  # Compare ground items only
    ITEMS_SHALLOW = auto()  # Compare item IDs only
    ITEMS_DEEP = auto()  # Compare all item attributes
    FULL = auto()  # Compare everything including flags


@dataclass(slots=True)
class ItemChange:
    """Represents a change to an item.

    Attributes:
        change_type: Type of change.
        item_id: Item ID.
        position: Position on tile.
        old_value: Previous state (None if added).
        new_value: New state (None if removed).
        attribute_changes: Map of changed attributes.
    """

    change_type: ChangeType
    item_id: int
    position: int  # Index in item list
    old_value: dict | None = None
    new_value: dict | None = None
    attribute_changes: dict[str, tuple] = field(default_factory=dict)

    def summary(self) -> str:
        """Get a summary string."""
        if self.change_type == ChangeType.ADDED:
            return f"+Item {self.item_id}"
        elif self.change_type == ChangeType.REMOVED:
            return f"-Item {self.item_id}"
        elif self.change_type == ChangeType.MODIFIED:
            attrs = ", ".join(self.attribute_changes.keys())
            return f"~Item {self.item_id} [{attrs}]"
        return f"Item {self.item_id}"


@dataclass
class TileDiff:
    """Detailed differences for a single tile.

    Attributes:
        position: Tile position.
        change_type: Overall change type.
        ground_change: Change to ground item.
        item_changes: List of item changes.
        flag_changes: Changes to tile flags.
        house_id_change: Change in house ID.
    """

    position: Position
    change_type: ChangeType = ChangeType.UNCHANGED
    ground_change: ItemChange | None = None
    item_changes: list[ItemChange] = field(default_factory=list)
    flag_changes: dict[str, tuple] = field(default_factory=dict)
    house_id_change: tuple[int, int] | None = None  # (old, new)

    @property
    def has_changes(self) -> bool:
        return self.change_type != ChangeType.UNCHANGED

    @property
    def total_changes(self) -> int:
        count = 0
        if self.ground_change:
            count += 1
        count += len(self.item_changes)
        count += len(self.flag_changes)
        if self.house_id_change:
            count += 1
        return count

    def summary(self) -> str:
        """Get a summary string."""
        x, y, z = self.position
        prefix = {
            ChangeType.ADDED: "+",
            ChangeType.REMOVED: "-",
            ChangeType.MODIFIED: "~",
            ChangeType.UNCHANGED: " ",
        }.get(self.change_type, "?")
        return f"{prefix}Tile ({x}, {y}, {z}): {self.total_changes} changes"


@dataclass
class DiffStatistics:
    """Statistics about the differences found.

    Attributes:
        tiles_compared: Total tiles compared.
        tiles_added: Tiles that exist only in new map.
        tiles_removed: Tiles that exist only in old map.
        tiles_modified: Tiles with changes.
        tiles_unchanged: Tiles without changes.
        items_added: Total items added.
        items_removed: Total items removed.
        items_modified: Total items modified.
    """

    tiles_compared: int = 0
    tiles_added: int = 0
    tiles_removed: int = 0
    tiles_modified: int = 0
    tiles_unchanged: int = 0
    items_added: int = 0
    items_removed: int = 0
    items_modified: int = 0

    @property
    def tiles_changed(self) -> int:
        return self.tiles_added + self.tiles_removed + self.tiles_modified

    @property
    def change_percentage(self) -> float:
        if self.tiles_compared == 0:
            return 0.0
        return (self.tiles_changed / self.tiles_compared) * 100


@dataclass
class DiffReport:
    """Complete diff report between two maps.

    Attributes:
        old_map_info: Info about the original map.
        new_map_info: Info about the new map.
        statistics: Diff statistics.
        tile_diffs: List of tile differences.
        floor_stats: Per-floor change counts.
    """

    old_map_info: dict = field(default_factory=dict)
    new_map_info: dict = field(default_factory=dict)
    statistics: DiffStatistics = field(default_factory=DiffStatistics)
    tile_diffs: list[TileDiff] = field(default_factory=list)
    floor_stats: dict[int, dict[str, int]] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return self.statistics.tiles_changed > 0

    def get_diffs_by_floor(self, z: int) -> list[TileDiff]:
        """Get all diffs for a specific floor."""
        return [d for d in self.tile_diffs if d.position[2] == z]

    def get_diffs_by_type(self, change_type: ChangeType) -> list[TileDiff]:
        """Get all diffs of a specific type."""
        return [d for d in self.tile_diffs if d.change_type == change_type]

    def summary(self) -> str:
        """Generate a summary string."""
        lines = [
            "=== Map Diff Report ===",
            f"Tiles Compared: {self.statistics.tiles_compared}",
            f"Changed: {self.statistics.tiles_changed} ({self.statistics.change_percentage:.1f}%)",
            f"  - Added: {self.statistics.tiles_added}",
            f"  - Removed: {self.statistics.tiles_removed}",
            f"  - Modified: {self.statistics.tiles_modified}",
            f"Items: +{self.statistics.items_added} / -{self.statistics.items_removed} / ~{self.statistics.items_modified}",
        ]
        return "\n".join(lines)


class MapDiffEngine:
    """Engine for comparing two maps.

    Example:
        engine = MapDiffEngine()

        # Compare two maps
        report = engine.compare(old_map, new_map)

        print(report.summary())

        # Get changes for a specific floor
        floor_7_changes = report.get_diffs_by_floor(7)
        for diff in floor_7_changes:
            print(diff.summary())
    """

    def __init__(self, level: DiffLevel = DiffLevel.ITEMS_SHALLOW) -> None:
        """Initialize the diff engine.

        Args:
            level: Level of detail for comparison.
        """
        self._level = level
        self._ignore_empty_tiles = True
        self._ignore_flags: set[str] = set()

    def set_level(self, level: DiffLevel) -> None:
        """Set comparison detail level."""
        self._level = level

    def set_ignore_empty(self, ignore: bool) -> None:
        """Set whether to ignore empty tiles."""
        self._ignore_empty_tiles = ignore

    def add_ignore_flag(self, flag_name: str) -> None:
        """Add a flag to ignore during comparison."""
        self._ignore_flags.add(flag_name)

    def compare(
        self,
        old_map: GameMap,
        new_map: GameMap,
        region: tuple[int, int, int, int] | None = None,
        floors: Sequence[int] | None = None,
    ) -> DiffReport:
        """Compare two maps and generate a diff report.

        Args:
            old_map: Original map.
            new_map: New/modified map.
            region: Optional (min_x, min_y, max_x, max_y) to compare.
            floors: Optional list of floors to compare.

        Returns:
            DiffReport with all differences.
        """
        report = DiffReport()

        # Map info
        report.old_map_info = self._extract_map_info(old_map, "old")
        report.new_map_info = self._extract_map_info(new_map, "new")

        # Determine bounds
        if region:
            min_x, min_y, max_x, max_y = region
        else:
            min_x = min_y = 0
            max_x = max(old_map.width, new_map.width)
            max_y = max(old_map.height, new_map.height)

        if floors is None:
            floors = range(16)

        # Compare tiles
        stats = report.statistics
        floor_stats: dict[int, dict[str, int]] = {}

        for z in floors:
            floor_stats[z] = {"added": 0, "removed": 0, "modified": 0}

            for y in range(min_y, max_y):
                for x in range(min_x, max_x):
                    old_tile = old_map.get_tile(x, y, z)
                    new_tile = new_map.get_tile(x, y, z)

                    stats.tiles_compared += 1

                    # Both tiles empty
                    if old_tile is None and new_tile is None:
                        if not self._ignore_empty_tiles:
                            stats.tiles_unchanged += 1
                        continue

                    # Tile added
                    if old_tile is None and new_tile is not None:
                        diff = TileDiff(
                            position=(x, y, z),
                            change_type=ChangeType.ADDED,
                        )
                        diff.item_changes = self._items_to_changes(new_tile, ChangeType.ADDED)
                        report.tile_diffs.append(diff)
                        stats.tiles_added += 1
                        stats.items_added += len(diff.item_changes)
                        floor_stats[z]["added"] += 1
                        continue

                    # Tile removed
                    if old_tile is not None and new_tile is None:
                        diff = TileDiff(
                            position=(x, y, z),
                            change_type=ChangeType.REMOVED,
                        )
                        diff.item_changes = self._items_to_changes(old_tile, ChangeType.REMOVED)
                        report.tile_diffs.append(diff)
                        stats.tiles_removed += 1
                        stats.items_removed += len(diff.item_changes)
                        floor_stats[z]["removed"] += 1
                        continue

                    # Both tiles exist - compare them
                    diff = self._compare_tiles(old_tile, new_tile, (x, y, z))

                    if diff.has_changes:
                        report.tile_diffs.append(diff)
                        stats.tiles_modified += 1
                        floor_stats[z]["modified"] += 1

                        # Count item changes
                        for ic in diff.item_changes:
                            if ic.change_type == ChangeType.ADDED:
                                stats.items_added += 1
                            elif ic.change_type == ChangeType.REMOVED:
                                stats.items_removed += 1
                            elif ic.change_type == ChangeType.MODIFIED:
                                stats.items_modified += 1
                    else:
                        stats.tiles_unchanged += 1

        report.floor_stats = floor_stats
        return report

    def _extract_map_info(self, game_map: GameMap, label: str) -> dict:
        """Extract basic info from a map."""
        return {
            "label": label,
            "width": game_map.width,
            "height": game_map.height,
            "description": getattr(game_map, "description", ""),
        }

    def _items_to_changes(
        self,
        tile: Tile,
        change_type: ChangeType,
    ) -> list[ItemChange]:
        """Convert all items on a tile to item changes."""
        changes: list[ItemChange] = []

        # Ground item
        if tile.ground:
            changes.append(
                ItemChange(
                    change_type=change_type,
                    item_id=tile.ground.id,
                    position=0,
                    old_value=self._item_to_dict(tile.ground) if change_type == ChangeType.REMOVED else None,
                    new_value=self._item_to_dict(tile.ground) if change_type == ChangeType.ADDED else None,
                )
            )

        # Other items
        for i, item in enumerate(tile.items):
            changes.append(
                ItemChange(
                    change_type=change_type,
                    item_id=item.id,
                    position=i + 1,
                    old_value=self._item_to_dict(item) if change_type == ChangeType.REMOVED else None,
                    new_value=self._item_to_dict(item) if change_type == ChangeType.ADDED else None,
                )
            )

        return changes

    def _compare_tiles(
        self,
        old_tile: Tile,
        new_tile: Tile,
        pos: Position,
    ) -> TileDiff:
        """Compare two tiles in detail."""
        diff = TileDiff(position=pos)

        # Compare ground
        diff.ground_change = self._compare_ground(old_tile, new_tile)
        if diff.ground_change:
            diff.change_type = ChangeType.MODIFIED

        # Compare items
        if self._level in (DiffLevel.ITEMS_SHALLOW, DiffLevel.ITEMS_DEEP, DiffLevel.FULL):
            diff.item_changes = self._compare_items(old_tile, new_tile)
            if diff.item_changes:
                diff.change_type = ChangeType.MODIFIED

        # Compare flags
        if self._level == DiffLevel.FULL:
            diff.flag_changes = self._compare_flags(old_tile, new_tile)
            if diff.flag_changes:
                diff.change_type = ChangeType.MODIFIED

            # Compare house ID
            old_house = getattr(old_tile, "house_id", 0) or 0
            new_house = getattr(new_tile, "house_id", 0) or 0
            if old_house != new_house:
                diff.house_id_change = (old_house, new_house)
                diff.change_type = ChangeType.MODIFIED

        return diff

    def _compare_ground(
        self,
        old_tile: Tile,
        new_tile: Tile,
    ) -> ItemChange | None:
        """Compare ground items."""
        old_ground = old_tile.ground
        new_ground = new_tile.ground

        old_id = old_ground.id if old_ground else 0
        new_id = new_ground.id if new_ground else 0

        if old_id == new_id == 0:
            return None

        if old_id == 0:
            return ItemChange(
                change_type=ChangeType.ADDED,
                item_id=new_id,
                position=0,
                new_value=self._item_to_dict(new_ground),
            )

        if new_id == 0:
            return ItemChange(
                change_type=ChangeType.REMOVED,
                item_id=old_id,
                position=0,
                old_value=self._item_to_dict(old_ground),
            )

        if old_id != new_id:
            return ItemChange(
                change_type=ChangeType.MODIFIED,
                item_id=new_id,
                position=0,
                old_value=self._item_to_dict(old_ground),
                new_value=self._item_to_dict(new_ground),
                attribute_changes={"id": (old_id, new_id)},
            )

        # Same ID - check attributes if deep comparison
        if self._level in (DiffLevel.ITEMS_DEEP, DiffLevel.FULL):
            attr_changes = self._compare_item_attributes(old_ground, new_ground)
            if attr_changes:
                return ItemChange(
                    change_type=ChangeType.MODIFIED,
                    item_id=new_id,
                    position=0,
                    old_value=self._item_to_dict(old_ground),
                    new_value=self._item_to_dict(new_ground),
                    attribute_changes=attr_changes,
                )

        return None

    def _compare_items(
        self,
        old_tile: Tile,
        new_tile: Tile,
    ) -> list[ItemChange]:
        """Compare item lists on two tiles."""
        changes: list[ItemChange] = []

        old_items = list(old_tile.items)
        new_items = list(new_tile.items)

        # Build ID -> items mapping for matching
        old_by_id: dict[int, list[Item]] = {}
        for item in old_items:
            if item.id not in old_by_id:
                old_by_id[item.id] = []
            old_by_id[item.id].append(item)

        new_by_id: dict[int, list[Item]] = {}
        for item in new_items:
            if item.id not in new_by_id:
                new_by_id[item.id] = []
            new_by_id[item.id].append(item)

        all_ids = set(old_by_id.keys()) | set(new_by_id.keys())

        pos = 1  # Position counter (0 is ground)

        for item_id in sorted(all_ids):
            old_list = old_by_id.get(item_id, [])
            new_list = new_by_id.get(item_id, [])

            old_count = len(old_list)
            new_count = len(new_list)

            # Added items
            if new_count > old_count:
                for i in range(old_count, new_count):
                    changes.append(
                        ItemChange(
                            change_type=ChangeType.ADDED,
                            item_id=item_id,
                            position=pos,
                            new_value=self._item_to_dict(new_list[i]),
                        )
                    )
                    pos += 1

            # Removed items
            elif old_count > new_count:
                for i in range(new_count, old_count):
                    changes.append(
                        ItemChange(
                            change_type=ChangeType.REMOVED,
                            item_id=item_id,
                            position=pos,
                            old_value=self._item_to_dict(old_list[i]),
                        )
                    )
                    pos += 1

            # Compare matching items
            for i in range(min(old_count, new_count)):
                if self._level in (DiffLevel.ITEMS_DEEP, DiffLevel.FULL):
                    attr_changes = self._compare_item_attributes(old_list[i], new_list[i])
                    if attr_changes:
                        changes.append(
                            ItemChange(
                                change_type=ChangeType.MODIFIED,
                                item_id=item_id,
                                position=pos,
                                old_value=self._item_to_dict(old_list[i]),
                                new_value=self._item_to_dict(new_list[i]),
                                attribute_changes=attr_changes,
                            )
                        )
                pos += 1

        return changes

    def _compare_item_attributes(
        self,
        old_item: Item,
        new_item: Item,
    ) -> dict[str, tuple]:
        """Compare attributes of two items."""
        changes: dict[str, tuple] = {}

        # Attributes to compare
        attrs = ["count", "action_id", "unique_id", "destination", "text", "charges"]

        for attr in attrs:
            old_val = getattr(old_item, attr, None)
            new_val = getattr(new_item, attr, None)

            if old_val != new_val:
                changes[attr] = (old_val, new_val)

        return changes

    def _compare_flags(
        self,
        old_tile: Tile,
        new_tile: Tile,
    ) -> dict[str, tuple]:
        """Compare tile flags."""
        changes: dict[str, tuple] = {}

        # Flag attributes to compare
        flag_attrs = ["flags", "pz", "no_logout", "pvp_zone", "no_pvp"]

        for attr in flag_attrs:
            if attr in self._ignore_flags:
                continue

            old_val = getattr(old_tile, attr, None)
            new_val = getattr(new_tile, attr, None)

            if old_val != new_val:
                changes[attr] = (old_val, new_val)

        return changes

    def _item_to_dict(self, item: Item | None) -> dict | None:
        """Convert an item to a dictionary."""
        if item is None:
            return None

        return {
            "id": item.id,
            "count": getattr(item, "count", 1),
            "action_id": getattr(item, "action_id", 0),
            "unique_id": getattr(item, "unique_id", 0),
        }

    def quick_compare(
        self,
        old_map: GameMap,
        new_map: GameMap,
    ) -> bool:
        """Quick check if two maps are identical.

        Args:
            old_map: First map.
            new_map: Second map.

        Returns:
            True if maps appear identical, False otherwise.
        """
        # Quick size check
        if old_map.width != new_map.width or old_map.height != new_map.height:
            return False

        # Sample some tiles
        sample_positions = [
            (0, 0, 7),
            (old_map.width // 2, old_map.height // 2, 7),
            (old_map.width - 1, old_map.height - 1, 7),
        ]

        for x, y, z in sample_positions:
            old_tile = old_map.get_tile(x, y, z)
            new_tile = new_map.get_tile(x, y, z)

            if (old_tile is None) != (new_tile is None):
                return False

            if old_tile and new_tile:
                if self._tiles_differ(old_tile, new_tile):
                    return False

        return True

    def _tiles_differ(self, old_tile: Tile, new_tile: Tile) -> bool:
        """Quick check if two tiles differ."""
        # Ground check
        old_gid = old_tile.ground.id if old_tile.ground else 0
        new_gid = new_tile.ground.id if new_tile.ground else 0
        if old_gid != new_gid:
            return True

        # Item count
        if len(list(old_tile.items)) != len(list(new_tile.items)):
            return True

        return False


def create_map_diff_engine(level: DiffLevel = DiffLevel.ITEMS_SHALLOW) -> MapDiffEngine:
    """Factory function to create a MapDiffEngine.

    Args:
        level: Comparison detail level.

    Returns:
        Configured MapDiffEngine.
    """
    return MapDiffEngine(level)
