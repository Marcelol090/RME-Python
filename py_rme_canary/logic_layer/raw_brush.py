"""Raw Brush Implementation for py_rme_canary.

Places items directly by their ID, without any automatic processing.
Mirrors legacy C++ RAWBrush from source/raw_brush.cpp.

This brush is essential for:
- Placing items by their exact server ID
- Testing with specific item IDs
- Advanced users who need direct item control
- Debugging item placement

Reference:
    - C++ RAWBrush: source/raw_brush.cpp
    - GAP_ANALYSIS.md: Missing brush implementations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Position


@dataclass(frozen=True, slots=True)
class RawBrushConfig:
    """Configuration for raw brush behavior.

    Attributes:
        like_simone: Replace same top-order items (legacy behavior).
        auto_stack: Allow stacking multiple items.
        max_stack: Maximum items to allow per tile.
    """

    like_simone: bool = False
    auto_stack: bool = True
    max_stack: int = 100


@dataclass(slots=True)
class RawBrush:
    """Places items directly by ID without automatic processing.

    Unlike specialized brushes (ground, wall, etc.), the RAW brush
    places items exactly as specified by their server ID. No auto-bordering,
    no special handling - just direct item placement.

    Mirrors legacy C++ RAWBrush from source/raw_brush.cpp.

    Attributes:
        item_id: The server item ID to place.
        config: Brush behavior settings.
        _item_type: Cached item type information.

    Example:
        >>> brush = RawBrush(item_id=2148)  # Gold coin
        >>> changes = brush.draw(game_map, pos)
        >>>
        >>> # With configuration
        >>> brush = RawBrush(
        ...     item_id=1234,
        ...     config=RawBrushConfig(like_simone=True)
        ... )
    """

    item_id: int
    config: RawBrushConfig = field(default_factory=RawBrushConfig)
    _item_type: Any = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Validate item ID."""
        if self.item_id <= 0:
            raise ValueError(f"Invalid item ID: {self.item_id}")

    def get_look_id(self) -> int:
        """Get the visual appearance ID for this brush.

        Returns:
            Item ID for visual display in palette.
        """
        return self.item_id

    def get_item_id(self) -> int:
        """Get the server item ID.

        Returns:
            Server item ID.
        """
        return self.item_id

    def get_name(self) -> str:
        """Get brush display name.

        Returns name in format:
        - "ID - Name" for known items
        - "ID - Name (Hook South/East)" for hookable items
        - "RAWBrush {ID}" for unknown items

        Mirrors C++ RAWBrush::getName().
        """
        # Try to get item type info
        if self._item_type is not None:
            name = getattr(self._item_type, "name", "")
            editor_suffix = getattr(self._item_type, "editor_suffix", "")

            # Check for hooks (like C++ version)
            hook_south = getattr(self._item_type, "hook_south", False)
            hook_east = getattr(self._item_type, "hook_east", False)

            base_name = f"{self.item_id} - {name}" if name else f"RAWBrush {self.item_id}"

            if hook_south:
                return f"{base_name} (Hook South)"
            elif hook_east:
                return f"{base_name} (Hook East)"
            elif editor_suffix:
                return f"{base_name}{editor_suffix}"
            return base_name

        return f"RAWBrush {self.item_id}"

    def set_item_type(self, item_type: Any) -> None:
        """Set cached item type for display purposes.

        Args:
            item_type: Item type object from item database.
        """
        object.__setattr__(self, "_item_type", item_type)

    def can_draw(self, game_map: GameMap, pos: Position) -> bool:
        """Check if we can draw at this position.

        RAW brush can draw anywhere there's a valid position.
        The tile will be created if it doesn't exist.

        Args:
            game_map: The map to draw on.
            pos: Position to check.

        Returns:
            True if drawing is possible.
        """
        # Can draw anywhere within map bounds
        if pos.x < 0 or pos.y < 0 or pos.z < 0:
            return False
        if pos.z > 15:  # Max floor
            return False
        return True

    def draw(
        self,
        game_map: GameMap,
        pos: Position,
        force: bool = False,
    ) -> list[tuple[Position, Any]]:
        """Draw item at position.

        Places item with the configured ID at the given position.
        If like_simone mode is enabled and item is always-on-top,
        replaces existing items with same top order.

        Mirrors C++ RAWBrush::draw().

        Args:
            game_map: Map to draw on.
            pos: Position to draw at.
            force: Force placement without like_simone behavior.

        Returns:
            List of (position, modified_tile) tuples.
        """
        from py_rme_canary.core.data.tile import Tile

        # Get or create tile
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            tile = Tile(pos.x, pos.y, pos.z)

        # Create new item
        new_item = self._create_item()
        if new_item is None:
            return []

        # Handle like_simone behavior (from C++ RAW_LIKE_SIMONE setting)
        # If enabled and item is always-on-bottom with top_order=2,
        # remove existing items with same top order first
        items_to_keep = list(tile.items) if tile.items else []

        if self.config.like_simone and not force and self._item_type is not None:
            always_on_bottom = getattr(self._item_type, "always_on_bottom", False)
            top_order = getattr(self._item_type, "always_on_top_order", 0)

            if always_on_bottom and top_order == 2:
                items_to_keep = [item for item in items_to_keep if getattr(item, "top_order", 0) != top_order]

        # Check stack limit
        if len(items_to_keep) >= self.config.max_stack and not force:
            return []  # Too many items

        # Determine if this is a ground item
        if self._is_ground_item():
            # Replace ground
            new_tile = Tile(
                x=pos.x,
                y=pos.y,
                z=pos.z,
                ground=new_item,
                items=items_to_keep,
                map_flags=tile.map_flags if hasattr(tile, "map_flags") else 0,
            )
        else:
            # Add to items
            items_to_keep.append(new_item)
            new_tile = Tile(
                x=pos.x,
                y=pos.y,
                z=pos.z,
                ground=tile.ground,
                items=items_to_keep,
                map_flags=tile.map_flags if hasattr(tile, "map_flags") else 0,
            )

        # Update map
        game_map.set_tile(new_tile)

        return [(pos, new_tile)]

    def undraw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Any]]:
        """Remove items with this ID from tile.

        Removes all items matching the brush's item ID from the tile.
        If the item is ground, removes ground. Otherwise removes from
        the items list.

        Mirrors C++ RAWBrush::undraw().

        Args:
            game_map: Map to modify.
            pos: Position to remove from.

        Returns:
            List of (position, modified_tile) tuples.
        """
        from py_rme_canary.core.data.tile import Tile

        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return []

        modified = False
        new_ground = tile.ground
        new_items = list(tile.items) if tile.items else []

        # Remove ground if matches
        if tile.ground is not None:
            ground_id = getattr(tile.ground, "id", None) or getattr(tile.ground, "item_id", None)
            if ground_id == self.item_id:
                new_ground = None
                modified = True

        # Remove matching items
        original_count = len(new_items)
        new_items = [
            item for item in new_items if (getattr(item, "id", None) or getattr(item, "item_id", None)) != self.item_id
        ]
        if len(new_items) != original_count:
            modified = True

        if not modified:
            return []

        new_tile = Tile(
            x=pos.x,
            y=pos.y,
            z=pos.z,
            ground=new_ground,
            items=new_items,
            map_flags=tile.map_flags if hasattr(tile, "map_flags") else 0,
        )

        game_map.set_tile(new_tile)

        return [(pos, new_tile)]

    def _create_item(self) -> Any:
        """Create a new item instance.

        Returns:
            New Item instance or None if creation fails.
        """
        try:
            from py_rme_canary.core.data.item import Item

            return Item(id=self.item_id)
        except Exception:
            # Fallback: return a simple item-like object
            return _SimpleItem(self.item_id)

    def _is_ground_item(self) -> bool:
        """Check if this item should be placed as ground.

        Returns:
            True if item is a ground type.
        """
        if self._item_type is None:
            return False
        return getattr(self._item_type, "is_ground", False)


class _SimpleItem:
    """Minimal item representation for fallback."""

    __slots__ = ("item_id", "id")

    def __init__(self, item_id: int) -> None:
        self.item_id = item_id
        self.id = item_id


class RawBrushManager:
    """Manager for RAW brushes.

    Caches RawBrush instances by item ID and provides item type
    lookups for proper display names.

    Example:
        >>> mgr = RawBrushManager(items_db)
        >>> brush = mgr.get_brush(2148)
        >>> print(brush.get_name())  # "2148 - gold coin"
    """

    def __init__(self, items_database: Any = None) -> None:
        """Initialize manager.

        Args:
            items_database: Optional item database for type lookups.
        """
        self._cache: dict[int, RawBrush] = {}
        self._items_db = items_database

    def get_brush(self, item_id: int, config: RawBrushConfig | None = None) -> RawBrush:
        """Get or create a RawBrush for the given item ID.

        Args:
            item_id: Server item ID.
            config: Optional brush configuration.

        Returns:
            RawBrush instance.
        """
        # Check cache (only for default config)
        if config is None and item_id in self._cache:
            return self._cache[item_id]

        # Create new brush
        brush_config = config or RawBrushConfig()
        brush = RawBrush(item_id=item_id, config=brush_config)

        # Try to set item type
        if self._items_db is not None:
            try:
                item_type = self._get_item_type(item_id)
                if item_type is not None:
                    brush.set_item_type(item_type)
            except Exception:
                pass

        # Cache if default config
        if config is None:
            self._cache[item_id] = brush

        return brush

    def clear_cache(self) -> None:
        """Clear the brush cache."""
        self._cache.clear()

    def _get_item_type(self, item_id: int) -> Any:
        """Get item type from database.

        Args:
            item_id: Server item ID.

        Returns:
            Item type object or None.
        """
        if self._items_db is None:
            return None

        # Try different attribute names
        if hasattr(self._items_db, "get_raw_item_type"):
            return self._items_db.get_raw_item_type(item_id)
        if hasattr(self._items_db, "get_item_type"):
            return self._items_db.get_item_type(item_id)
        if hasattr(self._items_db, "__getitem__"):
            try:
                return self._items_db[item_id]
            except (KeyError, IndexError):
                return None
        return None


__all__ = ["RawBrush", "RawBrushConfig", "RawBrushManager"]
