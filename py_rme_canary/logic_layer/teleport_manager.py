"""Teleport Link Manager.

This module provides tools for managing teleport destinations and links.
Essential for map designers to track and validate teleport connections.

Reference:
    - C++ Legacy: properties_window.cpp (teleport destination editing)
    - OTB: Items with destination attributes

Features:
    - TeleportLink: Single teleport with source/destination
    - TeleportManager: Track all teleports in a map
    - Link validation (broken links, circular references)
    - Bidirectional link creation
    - Export/Import of teleport data

Layer: logic_layer (no PyQt6 dependencies)
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Item

logger = logging.getLogger(__name__)


# Position type alias
Position = tuple[int, int, int]  # (x, y, z)


class TeleportType(Enum):
    """Type of teleport item."""

    MAGIC_WALL = auto()  # Temporary magic wall (not a real teleport)
    TELEPORT = auto()  # Standard teleport
    MAGIC_FIELD = auto()  # Magic field (fire, energy, etc.)
    LEVEL_DOOR = auto()  # Level-restricted door
    QUEST_DOOR = auto()  # Quest-restricted door
    LADDER_UP = auto()  # Ladder going up
    LADDER_DOWN = auto()  # Ladder going down
    STAIRS_UP = auto()  # Stairs going up
    STAIRS_DOWN = auto()  # Stairs going down
    TRAP_HOLE = auto()  # PZ-locked hole/trap
    UNKNOWN = auto()  # Unknown type


class LinkStatus(Enum):
    """Status of a teleport link."""

    VALID = auto()  # Link is valid
    BROKEN = auto()  # Destination doesn't exist or is invalid
    CIRCULAR = auto()  # Links back to itself
    NO_RETURN = auto()  # No corresponding return teleport
    MULTIPLE_DEST = auto()  # Same source has multiple destinations


@dataclass(slots=True)
class TeleportLink:
    """A teleport link between two positions.

    Attributes:
        source: Source position (where the teleport is).
        destination: Destination position.
        item_id: ID of the teleport item.
        teleport_type: Type of teleport.
        unique_id: Unique ID if any.
        action_id: Action ID if any.
        status: Link validation status.
        notes: Optional notes/description.
    """

    source: Position
    destination: Position
    item_id: int
    teleport_type: TeleportType = TeleportType.TELEPORT
    unique_id: int = 0
    action_id: int = 0
    status: LinkStatus = LinkStatus.VALID
    notes: str = ""

    @property
    def source_str(self) -> str:
        x, y, z = self.source
        return f"({x}, {y}, {z})"

    @property
    def destination_str(self) -> str:
        x, y, z = self.destination
        return f"({x}, {y}, {z})"

    @property
    def is_same_floor(self) -> bool:
        return self.source[2] == self.destination[2]

    @property
    def z_delta(self) -> int:
        return self.destination[2] - self.source[2]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source": list(self.source),
            "destination": list(self.destination),
            "item_id": self.item_id,
            "type": self.teleport_type.name,
            "unique_id": self.unique_id,
            "action_id": self.action_id,
            "status": self.status.name,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TeleportLink:
        """Create from dictionary."""
        return cls(
            source=tuple(data["source"]),
            destination=tuple(data["destination"]),
            item_id=data["item_id"],
            teleport_type=TeleportType[data.get("type", "TELEPORT")],
            unique_id=data.get("unique_id", 0),
            action_id=data.get("action_id", 0),
            status=LinkStatus[data.get("status", "VALID")],
            notes=data.get("notes", ""),
        )


@dataclass
class LinkValidationResult:
    """Result of validating teleport links.

    Attributes:
        total_links: Total number of teleport links.
        valid_links: Number of valid links.
        broken_links: List of broken links.
        circular_links: List of circular links.
        no_return_links: List of one-way links.
        duplicate_sources: Sources with multiple destinations.
    """

    total_links: int = 0
    valid_links: int = 0
    broken_links: list[TeleportLink] = field(default_factory=list)
    circular_links: list[TeleportLink] = field(default_factory=list)
    no_return_links: list[TeleportLink] = field(default_factory=list)
    duplicate_sources: list[Position] = field(default_factory=list)

    @property
    def is_all_valid(self) -> bool:
        return len(self.broken_links) == 0 and len(self.circular_links) == 0

    def summary(self) -> str:
        """Generate a summary string."""
        lines = [
            f"Total Links: {self.total_links}",
            f"Valid: {self.valid_links}",
            f"Broken: {len(self.broken_links)}",
            f"Circular: {len(self.circular_links)}",
            f"One-way: {len(self.no_return_links)}",
            f"Duplicate sources: {len(self.duplicate_sources)}",
        ]
        return "\n".join(lines)


# Item IDs that are teleports (common OT item IDs)
TELEPORT_ITEM_IDS = {
    1387,  # Standard teleport
    1946,  # Magic portal
    5734,  # Blue portal
    5735,  # Orange portal
    5736,  # Green portal
    7804,  # Quest teleport
    8058,  # Golden teleport
    10483,  # Crystal portal
    # Add more as needed
}

# Item IDs for level movers (ladders, stairs, holes)
LEVEL_MOVER_IDS = {
    # Ladders
    1386,
    3678,
    5543,
    8599,
    # Stairs
    1947,
    1948,
    1949,
    1950,
    # Holes/Traps
    462,
    469,
    476,
    7729,
}


class TeleportManager:
    """Manager for tracking and validating teleport links in a map.

    Example:
        manager = TeleportManager(game_map)

        # Scan map for teleports
        manager.scan_map()

        # Validate all links
        result = manager.validate_all()
        print(result.summary())

        # Get teleport at position
        link = manager.get_link_at((100, 100, 7))
        if link:
            print(f"Destination: {link.destination}")

        # Create bidirectional link
        manager.create_bidirectional(
            pos1=(100, 100, 7),
            pos2=(200, 200, 7)
        )
    """

    def __init__(self, game_map: GameMap | None = None) -> None:
        """Initialize the teleport manager.

        Args:
            game_map: Optional map to scan for teleports.
        """
        self._map = game_map
        self._links: dict[Position, TeleportLink] = {}
        self._destination_index: dict[Position, list[Position]] = {}

    @property
    def link_count(self) -> int:
        return len(self._links)

    def set_map(self, game_map: GameMap) -> None:
        """Set the map and rescan."""
        self._map = game_map
        self._links.clear()
        self._destination_index.clear()

    def scan_map(self) -> int:
        """Scan the entire map for teleport items.

        Returns:
            Number of teleports found.
        """
        if self._map is None:
            logger.warning("No map set for teleport scanning")
            return 0

        self._links.clear()
        self._destination_index.clear()
        count = 0

        # Iterate through all tiles
        for z in range(16):  # Standard Z range
            for y in range(self._map.header.height):
                for x in range(self._map.header.width):
                    tile = self._map.get_tile(x, y, z)
                    if tile is None:
                        continue

                    # Check items for teleports
                    for item in tile.items:
                        if self._is_teleport_item(item):
                            link = self._extract_link(item, (x, y, z))
                            if link:
                                self._add_link(link)
                                count += 1

        logger.info("Scanned map: found %d teleport links", count)
        return count

    def _is_teleport_item(self, item: Item) -> bool:
        """Check if an item is a teleport."""
        # Check by ID
        if item.id in TELEPORT_ITEM_IDS or item.id in LEVEL_MOVER_IDS:
            return True

        # Check by attributes
        if hasattr(item, "destination") and item.destination:
            return True

        # Check by type attribute
        if hasattr(item, "type_attr"):
            type_str = str(getattr(item, "type_attr", "")).lower()
            if "teleport" in type_str or "portal" in type_str:
                return True

        return False

    def _extract_link(self, item: Item, source: Position) -> TeleportLink | None:
        """Extract teleport link information from an item."""
        # Get destination
        destination: Position | None = None

        if hasattr(item, "destination"):
            dest = item.destination
            if dest:
                # Check for Position dataclass (x, y, z attributes)
                if hasattr(dest, "x") and hasattr(dest, "y") and hasattr(dest, "z"):
                    destination = (int(dest.x), int(dest.y), int(dest.z))
                else:
                    # Check for tuple/list - cast to Any to avoid Mypy complaint about Position vs tuple mismatch
                    dest_any = cast(Any, dest)
                    if isinstance(dest_any, (tuple, list)) and len(dest_any) >= 3:
                        destination = (int(dest_any[0]), int(dest_any[1]), int(dest_any[2]))

        if destination is None:
            # Try alternative attribute names
            for attr in ["teleport_dest", "dest", "target"]:
                if hasattr(item, attr):
                    dest = getattr(item, attr)
                    if dest:
                        if hasattr(dest, "x") and hasattr(dest, "y") and hasattr(dest, "z"):
                            destination = (int(dest.x), int(dest.y), int(dest.z))
                            break
                        else:
                            dest_any = cast(Any, dest)
                            if isinstance(dest_any, (tuple, list)) and len(dest_any) >= 3:
                                destination = (int(dest_any[0]), int(dest_any[1]), int(dest_any[2]))
                                break

        if destination is None:
            # Destination not set - create link with default destination
            destination = source  # Self-reference until set

        # Determine teleport type
        tp_type = self._determine_type(item)

        # Get IDs
        unique_id = getattr(item, "unique_id", 0) or 0
        action_id = getattr(item, "action_id", 0) or 0

        return TeleportLink(
            source=source,
            destination=destination,
            item_id=item.id,
            teleport_type=tp_type,
            unique_id=unique_id,
            action_id=action_id,
        )

    def _determine_type(self, item: Item) -> TeleportType:
        """Determine the type of teleport from the item."""
        item_id = item.id

        if item_id in LEVEL_MOVER_IDS:
            # Check if it's going up or down (by common ID ranges)
            if item_id in {1386, 3678, 5543}:  # Ladders up
                return TeleportType.LADDER_UP
            elif item_id in {1947, 1948}:  # Stairs up
                return TeleportType.STAIRS_UP
            elif item_id in {1949, 1950}:  # Stairs down
                return TeleportType.STAIRS_DOWN
            elif item_id in {462, 469, 476}:  # Holes
                return TeleportType.TRAP_HOLE
            return TeleportType.LADDER_DOWN

        if item_id in TELEPORT_ITEM_IDS:
            return TeleportType.TELEPORT

        return TeleportType.UNKNOWN

    def _add_link(self, link: TeleportLink) -> None:
        """Add a link to the manager."""
        self._links[link.source] = link

        # Index by destination for reverse lookups
        if link.destination not in self._destination_index:
            self._destination_index[link.destination] = []
        self._destination_index[link.destination].append(link.source)

    def get_link_at(self, pos: Position) -> TeleportLink | None:
        """Get teleport link at a position."""
        return self._links.get(pos)

    def get_links_to(self, destination: Position) -> list[TeleportLink]:
        """Get all teleports that lead to a destination."""
        sources = self._destination_index.get(destination, [])
        return [self._links[src] for src in sources if src in self._links]

    def add_link(self, link: TeleportLink) -> None:
        """Manually add a teleport link."""
        self._add_link(link)

    def remove_link(self, source: Position) -> bool:
        """Remove a teleport link by source position.

        Args:
            source: Source position.

        Returns:
            True if removed, False if not found.
        """
        if source not in self._links:
            return False

        link = self._links[source]

        # Remove from destination index
        if link.destination in self._destination_index:
            sources = self._destination_index[link.destination]
            if source in sources:
                sources.remove(source)

        del self._links[source]
        return True

    def set_destination(self, source: Position, destination: Position) -> bool:
        """Set/update destination for a teleport.

        Args:
            source: Source position.
            destination: New destination.

        Returns:
            True if updated, False if not found.
        """
        if source not in self._links:
            return False

        link = self._links[source]
        old_dest = link.destination

        # Update destination index
        if old_dest in self._destination_index:
            sources = self._destination_index[old_dest]
            if source in sources:
                sources.remove(source)

        # Update link
        link.destination = destination

        if destination not in self._destination_index:
            self._destination_index[destination] = []
        self._destination_index[destination].append(source)

        # Update actual item on map if possible
        self._update_item_destination(source, destination)

        return True

    def _update_item_destination(self, source: Position, destination: Position) -> None:
        """Update the actual item's destination on the map."""
        if self._map is None:
            return

        x, y, z = source
        tile = self._map.get_tile(x, y, z)
        if tile is None:
            return

        link = self._links.get(source)
        if link is None:
            return

        for item in tile.items:
            if item.id == link.item_id:
                # Convert tuple to Item's expected Position type if needed
                # For now, we assume Item can accept tuple or we need to import Position
                from py_rme_canary.core.data.item import Position as ItemPosition

                pos_obj = ItemPosition(x=destination[0], y=destination[1], z=destination[2])

                if hasattr(item, "destination"):
                    item.destination = pos_obj
                elif hasattr(item, "teleport_dest"):
                    # Legacy fallback might expect tuple
                    item.teleport_dest = destination
                break

    def create_bidirectional(
        self,
        pos1: Position,
        pos2: Position,
        item_id: int = 1387,
    ) -> tuple[TeleportLink, TeleportLink]:
        """Create bidirectional teleport links.

        Args:
            pos1: First position.
            pos2: Second position.
            item_id: Teleport item ID to use.

        Returns:
            Tuple of (link1, link2).
        """
        link1 = TeleportLink(
            source=pos1,
            destination=pos2,
            item_id=item_id,
            teleport_type=TeleportType.TELEPORT,
        )
        link2 = TeleportLink(
            source=pos2,
            destination=pos1,
            item_id=item_id,
            teleport_type=TeleportType.TELEPORT,
        )

        self._add_link(link1)
        self._add_link(link2)

        return (link1, link2)

    def validate_all(self) -> LinkValidationResult:
        """Validate all teleport links.

        Returns:
            LinkValidationResult with validation details.
        """
        result = LinkValidationResult(total_links=len(self._links))

        # Track sources to detect duplicates
        source_counts: dict[Position, int] = {}

        for source, link in self._links.items():
            # Check for circular (self-referencing)
            if link.source == link.destination:
                link.status = LinkStatus.CIRCULAR
                result.circular_links.append(link)
                continue

            # Check if destination exists (has a tile)
            if self._map is not None:
                dx, dy, dz = link.destination
                dest_tile = self._map.get_tile(dx, dy, dz)
                if dest_tile is None:
                    link.status = LinkStatus.BROKEN
                    result.broken_links.append(link)
                    continue

            # Check for return teleport
            if link.destination not in self._links:
                link.status = LinkStatus.NO_RETURN
                result.no_return_links.append(link)
            else:
                return_link = self._links[link.destination]
                if return_link.destination != link.source:
                    link.status = LinkStatus.NO_RETURN
                    result.no_return_links.append(link)
                else:
                    link.status = LinkStatus.VALID
                    result.valid_links += 1

        # Find duplicate sources (actually managed by dict, but check anyway)
        for src, count in source_counts.items():
            if count > 1:
                result.duplicate_sources.append(src)

        return result

    def get_all_links(self) -> list[TeleportLink]:
        """Get all teleport links."""
        return list(self._links.values())

    def get_links_on_floor(self, z: int) -> list[TeleportLink]:
        """Get all teleport links on a specific floor."""
        return [link for link in self._links.values() if link.source[2] == z]

    def get_links_by_type(self, tp_type: TeleportType) -> list[TeleportLink]:
        """Get all teleport links of a specific type."""
        return [link for link in self._links.values() if link.teleport_type == tp_type]

    def iter_links(self) -> Iterator[TeleportLink]:
        """Iterate over all links."""
        yield from self._links.values()

    def export_json(self, path: str | Path) -> None:
        """Export all links to JSON file.

        Args:
            path: Output file path.
        """
        data = {
            "version": 1,
            "total_links": len(self._links),
            "links": [link.to_dict() for link in self._links.values()],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info("Exported %d teleport links to %s", len(self._links), path)

    def import_json(self, path: str | Path) -> int:
        """Import links from JSON file.

        Args:
            path: Input file path.

        Returns:
            Number of links imported.
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for link_data in data.get("links", []):
            try:
                link = TeleportLink.from_dict(link_data)
                self._add_link(link)
                count += 1
            except Exception as e:
                logger.warning("Failed to import link: %s", e)

        logger.info("Imported %d teleport links from %s", count, path)
        return count

    def clear(self) -> None:
        """Clear all tracked links."""
        self._links.clear()
        self._destination_index.clear()


def create_teleport_manager(game_map: GameMap | None = None) -> TeleportManager:
    """Factory function to create a TeleportManager.

    Args:
        game_map: Optional map to scan.

    Returns:
        Configured TeleportManager.
    """
    manager = TeleportManager(game_map)
    if game_map is not None:
        manager.scan_map()
    return manager
