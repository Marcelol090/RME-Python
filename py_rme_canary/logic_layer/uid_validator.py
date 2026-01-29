"""UID Validator Module for RME.

Scans map for duplicate unique IDs and reports conflicts.

Layer: logic_layer (no PyQt6 imports)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class UIDConflict:
    """Represents a duplicate UID conflict."""

    unique_id: int
    positions: list[tuple[int, int, int]]  # List of (x, y, z) positions
    item_ids: list[int]  # Server IDs of conflicting items
    count: int = 0

    def __post_init__(self) -> None:
        self.count = len(self.positions)


@dataclass
class UIDValidationResult:
    """Result of UID validation scan."""

    total_items_scanned: int = 0
    total_uids_found: int = 0
    duplicate_count: int = 0
    conflicts: list[UIDConflict] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return self.duplicate_count > 0


class UIDValidator:
    """Validator for unique IDs on the map.

    Scans all tiles and items for duplicate unique_id values.

    Usage:
        validator = UIDValidator()
        result = validator.scan(game_map)
        if result.has_duplicates:
            for conflict in result.conflicts:
                print(f"UID {conflict.unique_id} found at {conflict.positions}")
    """

    def scan(self, game_map: Any) -> UIDValidationResult:
        """Scan entire map for duplicate UIDs.

        Args:
            game_map: GameMap instance to scan

        Returns:
            UIDValidationResult with conflicts list
        """
        result = UIDValidationResult()

        # uid -> list of (x, y, z, item_id)
        uid_map: dict[int, list[tuple[int, int, int, int]]] = {}

        tiles = getattr(game_map, "tiles", {})

        for key, tile in tiles.items():
            x, y, z = key if isinstance(key, tuple) else (0, 0, 0)

            # Check ground
            ground = getattr(tile, "ground", None)
            if ground:
                self._check_item(ground, x, y, z, uid_map, result)

            # Check items stack
            items = getattr(tile, "items", [])
            for item in items:
                self._check_item(item, x, y, z, uid_map, result)

        # Build conflicts list from uid_map
        for uid, locs in uid_map.items():
            if len(locs) > 1:
                result.duplicate_count += 1
                result.conflicts.append(
                    UIDConflict(
                        unique_id=uid,
                        positions=[(x, y, z) for x, y, z, _ in locs],
                        item_ids=[item_id for _, _, _, item_id in locs],
                    )
                )

        result.total_uids_found = len(uid_map)

        log.info(
            "UID validation: scanned %d items, found %d UIDs, %d duplicates",
            result.total_items_scanned,
            result.total_uids_found,
            result.duplicate_count,
        )

        return result

    def _check_item(
        self,
        item: Any,
        x: int,
        y: int,
        z: int,
        uid_map: dict[int, list[tuple[int, int, int, int]]],
        result: UIDValidationResult,
    ) -> None:
        """Check item and its containers for UIDs."""
        result.total_items_scanned += 1

        unique_id = getattr(item, "unique_id", None)
        if unique_id and unique_id > 0:
            item_id = getattr(item, "id", 0) or getattr(item, "server_id", 0)
            if unique_id not in uid_map:
                uid_map[unique_id] = []
            uid_map[unique_id].append((x, y, z, item_id))

        # Recurse into container items
        container_items = getattr(item, "items", None)
        if container_items:
            for sub_item in container_items:
                self._check_item(sub_item, x, y, z, uid_map, result)


def get_uid_validator() -> UIDValidator:
    """Get a new UID validator instance."""
    return UIDValidator()
