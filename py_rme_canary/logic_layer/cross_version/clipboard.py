"""Cross-version clipboard for copying/pasting between different client versions.

This module enables copying map areas from one RME instance and pasting into another
instance running a different Tibia client version. Item IDs are automatically translated
using sprite hash matching to find equivalent sprites across versions.

Workflow:
    1. Copy tiles from source version (e.g., Client 13.x)
    2. Sprite IDs are stored with the tiles
    3. When pasting to target version (e.g., Client 7.4):
       a. Look up each sprite hash in source version
       b. Find matching sprite in target version
       c. Replace IDs with target version equivalents
       d. Keep original ID if no match found

See features.md "Cross-Version Copy/Paste" for complete documentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from py_rme_canary.core.data import Item, Tile
from py_rme_canary.core.data.creature import Monster, Npc

if TYPE_CHECKING:
    from py_rme_canary.logic_layer.cross_version.sprite_hash import SpriteHashMatcher


@dataclass
class ClipboardData:
    """Internal clipboard storage for copied tiles."""

    tiles: list[Tile]
    source_version: str
    tile_count: int


@dataclass
class TranslationResult:
    """Result of a copy operation."""

    success: bool
    tile_count: int
    error_message: str = ""


def _clone_item_with_id(old_item: Item, new_id: int) -> Item:
    """Create a copy of item with new ID (preserving all other attributes)."""
    return Item(
        id=int(new_id),
        client_id=old_item.client_id,
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


def _translate_item(item: Item, matcher: SpriteHashMatcher | None) -> Item:
    """Translate item ID using sprite matcher, or keep original if no match."""
    if matcher is None:
        return item

    # Get hash for current item ID
    item_hash = matcher.get_hash(item.id)
    if item_hash is None:
        # No hash registered for this ID, keep original
        return item

    # Find matching IDs in target version
    matching_ids = matcher.find_by_hash(item_hash)
    if not matching_ids:
        # No match found, keep original
        return item

    # Filter out current ID to find alternatives
    alternative_ids = [mid for mid in matching_ids if mid != item.id]
    if not alternative_ids:
        # Only matches itself, keep original
        return item

    # Use first alternative ID (preference could be configurable)
    new_id = alternative_ids[0]

    # Recursively translate container items
    if item.items:
        translated_children = tuple(
            _translate_item(child, matcher) for child in item.items
        )
        item = item.with_container_items(translated_children)

    return _clone_item_with_id(item, new_id)


def _translate_creature(creature: Monster | Npc, matcher: SpriteHashMatcher | None) -> Monster | Npc:
    """Translate creature outfit ID using sprite matcher.

    Note: Currently creatures don't have outfit IDs in the data model,
    so this function just returns the creature as-is. This is a placeholder
    for future enhancement when outfit translation is needed.
    """
    # Placeholder for future outfit translation
    # When Creature data model adds outfit field, implement translation here
    return creature


def _translate_tile(
    tile: Tile,
    matcher: SpriteHashMatcher | None,
) -> Tile:
    """Translate all item and creature IDs in a tile."""
    # Translate ground
    new_ground = tile.ground
    if new_ground is not None and matcher is not None:
        new_ground = _translate_item(new_ground, matcher)

    # Translate items
    new_items = [_translate_item(item, matcher) for item in tile.items]

    # Translate creatures (currently just preserves them)
    # Type narrowing: all monsters are Monster type
    new_monsters: list[Monster] = [cast(Monster, _translate_creature(m, matcher)) for m in tile.monsters]
    # Type narrowing: npc is Npc | None
    new_npc: Npc | None = cast(Npc, _translate_creature(tile.npc, matcher)) if tile.npc else None

    # Create new tile with translated content
    return Tile(
        x=tile.x,
        y=tile.y,
        z=tile.z,
        ground=new_ground,
        items=new_items,
        house_id=tile.house_id,
        map_flags=tile.map_flags,
        zones=tile.zones,
        modified=True,  # Mark as modified since IDs changed
        monsters=new_monsters,
        npc=new_npc,
        spawn_monster=tile.spawn_monster,
        spawn_npc=tile.spawn_npc,
    )


class CrossVersionClipboard:
    """Clipboard that supports copy/paste across different client versions.

    This clipboard stores tiles along with their source version metadata.
    When pasting, it can automatically translate item/creature IDs using
    sprite hash matching to find equivalent sprites in the target version.

    Usage:
        # Copy from version 13.x
        clipboard = CrossVersionClipboard()
        clipboard.copy(selected_tiles, source_version='13.x')

        # Paste to version 7.4 with translation
        pasted_tiles = clipboard.paste(
            target_version='7.4',
            sprite_matcher=matcher,
        )

    Thread safety: Not thread-safe. Use external synchronization if needed.
    """

    def __init__(self) -> None:
        """Initialize empty clipboard."""
        self._data: ClipboardData | None = None

    def copy(self, tiles: list[Tile], source_version: str) -> TranslationResult:
        """Copy tiles to clipboard.

        Args:
            tiles: List of tiles to copy
            source_version: Client version identifier (e.g., '7.4', '13.x')

        Returns:
            TranslationResult with success status and tile count
        """
        if not tiles:
            return TranslationResult(
                success=False,
                tile_count=0,
                error_message="No tiles to copy",
            )

        # Deep copy tiles to prevent external modifications
        copied_tiles = [
            Tile(
                x=t.x,
                y=t.y,
                z=t.z,
                ground=t.ground,
                items=list(t.items),
                house_id=t.house_id,
                map_flags=t.map_flags,
                zones=t.zones,
                modified=t.modified,
                monsters=list(t.monsters),
                npc=t.npc,
                spawn_monster=t.spawn_monster,
                spawn_npc=t.spawn_npc,
            )
            for t in tiles
        ]

        self._data = ClipboardData(
            tiles=copied_tiles,
            source_version=source_version,
            tile_count=len(copied_tiles),
        )

        return TranslationResult(success=True, tile_count=len(copied_tiles))

    def paste(
        self,
        target_version: str,
        sprite_matcher: SpriteHashMatcher | None = None,
    ) -> list[Tile]:
        """Paste tiles with optional ID translation.

        Args:
            target_version: Client version identifier for paste target
            sprite_matcher: Optional sprite hash matcher for ID translation.
                           If None or same version, no translation occurs.

        Returns:
            List of pasted tiles (with translated IDs if applicable)

        Raises:
            RuntimeError: If clipboard is empty
        """
        if self._data is None:
            raise RuntimeError("Clipboard is empty")

        # If same version or no matcher, return copies without translation
        if sprite_matcher is None or self._data.source_version == target_version:
            return [
                Tile(
                    x=t.x,
                    y=t.y,
                    z=t.z,
                    ground=t.ground,
                    items=list(t.items),
                    house_id=t.house_id,
                    map_flags=t.map_flags,
                    zones=t.zones,
                    modified=t.modified,
                    monsters=list(t.monsters),
                    npc=t.npc,
                    spawn_monster=t.spawn_monster,
                    spawn_npc=t.spawn_npc,
                )
                for t in self._data.tiles
            ]

        # Translate all tiles using sprite matcher
        return [_translate_tile(t, sprite_matcher) for t in self._data.tiles]

    def has_data(self) -> bool:
        """Check if clipboard contains data.

        Returns:
            True if clipboard has tiles, False otherwise
        """
        return self._data is not None and len(self._data.tiles) > 0

    def clear(self) -> None:
        """Clear all clipboard data."""
        self._data = None

    def get_stats(self) -> dict[str, int | str | bool]:
        """Get clipboard statistics.

        Returns:
            Dictionary with tile_count, source_version, and has_data
        """
        if self._data is None:
            return {
                "tile_count": 0,
                "source_version": "",
                "has_data": False,
            }

        return {
            "tile_count": self._data.tile_count,
            "source_version": self._data.source_version,
            "has_data": True,
        }
