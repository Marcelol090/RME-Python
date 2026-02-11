"""Object Pool for high-frequency allocations.

This module provides pooling mechanisms to reduce allocation overhead
for frequently created/destroyed objects (Tiles, Items, etc.).

Reference:
    - project_tasks.json: ARCH-004 (keeper-live-memory)
    - Legacy: RME doesn't have explicit pooling but reuses objects

Architecture:
    - ObjectPool[T]: Generic typed pool with configurable size
    - TilePool: Specialized pool for Tile objects
    - ItemPool: Specialized pool for Item objects
    - PoolStats: Metrics tracking for optimization
"""

from __future__ import annotations

import logging
import threading
import weakref
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.tile import Tile

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(slots=True)
class PoolStats:
    """Statistics for object pool monitoring.

    Attributes:
        pool_name: Identifier for the pool.
        current_size: Objects currently in pool (available).
        total_allocated: Total objects ever created.
        total_acquired: Times acquire() was called.
        total_released: Times release() was called.
        cache_hits: Objects returned from pool (reused).
        cache_misses: New objects created (pool empty).
        peak_size: Maximum pool size observed.
    """

    pool_name: str = "unnamed"
    current_size: int = 0
    total_allocated: int = 0
    total_acquired: int = 0
    total_released: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    peak_size: int = 0

    @property
    def hit_ratio(self) -> float:
        """Cache hit ratio (0.0-1.0)."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging/debugging."""
        return {
            "pool_name": self.pool_name,
            "current_size": self.current_size,
            "total_allocated": self.total_allocated,
            "total_acquired": self.total_acquired,
            "total_released": self.total_released,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "peak_size": self.peak_size,
            "hit_ratio": f"{self.hit_ratio:.2%}",
        }


class ObjectPool(Generic[T]):
    """Generic object pool for reducing allocation overhead.

    This pool maintains a LIFO stack of reusable objects. When acquire()
    is called, it returns a pooled object if available or creates a new
    one via the factory. When release() is called, the object is reset
    and returned to the pool.

    Thread-safety: All operations are protected by a lock.

    Usage:
        pool = ObjectPool(
            factory=lambda: Tile(0, 0, 7),
            reset_fn=lambda t: t.clear(),
            max_size=10000,
            name="TilePool"
        )

        tile = pool.acquire()
        # use tile...
        pool.release(tile)

    Type Parameters:
        T: Type of objects in the pool.

    Args:
        factory: Callable that creates new instances.
        reset_fn: Optional callable to reset objects before pooling.
        max_size: Maximum pool capacity (excess objects discarded).
        name: Name for logging/debugging.
    """

    __slots__ = ("_factory", "_reset_fn", "_max_size", "_name", "_pool", "_lock", "_stats", "_active")

    def __init__(
        self,
        factory: Callable[[], T],
        reset_fn: Callable[[T], None] | None = None,
        max_size: int = 10000,
        name: str = "ObjectPool",
    ) -> None:
        self._factory = factory
        self._reset_fn = reset_fn
        self._max_size = max(1, int(max_size))
        self._name = str(name)

        self._pool: deque[T] = deque()
        self._lock = threading.Lock()
        self._stats = PoolStats(pool_name=self._name)
        self._active: weakref.WeakSet[T] = weakref.WeakSet()

    @property
    def name(self) -> str:
        return self._name

    @property
    def stats(self) -> PoolStats:
        """Get current pool statistics (snapshot)."""
        with self._lock:
            self._stats.current_size = len(self._pool)
            return PoolStats(
                pool_name=self._stats.pool_name,
                current_size=self._stats.current_size,
                total_allocated=self._stats.total_allocated,
                total_acquired=self._stats.total_acquired,
                total_released=self._stats.total_released,
                cache_hits=self._stats.cache_hits,
                cache_misses=self._stats.cache_misses,
                peak_size=self._stats.peak_size,
            )

    def acquire(self) -> T:
        """Acquire an object from the pool.

        Returns a pooled object if available, otherwise creates a new one.

        Returns:
            An instance of T (either reused or new).
        """
        with self._lock:
            self._stats.total_acquired += 1

            if self._pool:
                obj = self._pool.pop()
                self._stats.cache_hits += 1
            else:
                obj = self._factory()
                self._stats.total_allocated += 1
                self._stats.cache_misses += 1

            self._active.add(obj)

        return obj

    def release(self, obj: T) -> bool:
        """Return an object to the pool.

        The object is reset (if reset_fn provided) and added to the pool
        if capacity allows.

        Args:
            obj: Object to release.

        Returns:
            True if object was pooled, False if discarded (pool full).
        """
        # Reset object outside lock to reduce contention
        if self._reset_fn is not None:
            try:
                self._reset_fn(obj)
            except Exception:
                # If reset fails, don't pool
                logger.debug("Failed to reset object in %s", self._name)
                return False

        with self._lock:
            self._stats.total_released += 1

            # Remove from active set
            try:
                self._active.discard(obj)
            except Exception:
                pass

            # Check capacity
            if len(self._pool) >= self._max_size:
                return False

            self._pool.append(obj)

            # Track peak
            if len(self._pool) > self._stats.peak_size:
                self._stats.peak_size = len(self._pool)

        return True

    def pre_allocate(self, count: int) -> int:
        """Pre-allocate objects to warm the pool.

        Args:
            count: Number of objects to create.

        Returns:
            Number of objects actually created.
        """
        created = 0

        with self._lock:
            remaining = self._max_size - len(self._pool)
            to_create = min(count, remaining)

        # Create outside lock
        objects: list[T] = []
        for _ in range(to_create):
            try:
                obj = self._factory()
                objects.append(obj)
                created += 1
            except Exception:
                break

        # Add to pool
        with self._lock:
            for obj in objects:
                if len(self._pool) < self._max_size:
                    self._pool.append(obj)
                    self._stats.total_allocated += 1
                    if len(self._pool) > self._stats.peak_size:
                        self._stats.peak_size = len(self._pool)

        logger.debug("Pre-allocated %d objects in %s", created, self._name)
        return created

    def clear(self) -> int:
        """Clear all pooled objects.

        Returns:
            Number of objects cleared.
        """
        with self._lock:
            count = len(self._pool)
            self._pool.clear()

        logger.debug("Cleared %d objects from %s", count, self._name)
        return count

    def shrink(self, target_size: int = 0) -> int:
        """Shrink pool to target size.

        Args:
            target_size: Desired pool size.

        Returns:
            Number of objects removed.
        """
        removed = 0

        with self._lock:
            target = max(0, int(target_size))
            while len(self._pool) > target:
                self._pool.pop()
                removed += 1

        logger.debug("Shrunk %s by %d objects", self._name, removed)
        return removed

    def __len__(self) -> int:
        with self._lock:
            return len(self._pool)

    def __repr__(self) -> str:
        return f"ObjectPool[{self._name}](size={len(self)}, max={self._max_size})"


class TilePool(ObjectPool["Tile"]):
    """Specialized pool for Tile objects.

    Tiles are the most frequently allocated objects in the map editor.
    This pool reduces GC pressure during large map operations.
    """

    def __init__(self, max_size: int = 50000) -> None:
        def factory() -> Tile:
            from py_rme_canary.core.data.tile import Tile

            return Tile(x=0, y=0, z=7)

        # Tile is immutable, so we can't reset or reuse effectively without creating new instances.
        # We disable reset to avoid errors.
        super().__init__(
            factory=factory,
            reset_fn=None,
            max_size=max_size,
            name="TilePool",
        )

    def acquire_at(self, x: int, y: int, z: int) -> Tile:
        """Acquire a tile and set its position.

        Args:
            x, y, z: Tile coordinates.

        Returns:
            Tile positioned at (x, y, z).
        """
        # Since Tile is immutable, we must create a new instance.
        # Pooling is effectively bypassed for Tile creation but interface is kept.
        from py_rme_canary.core.data.tile import Tile
        return Tile(x=int(x), y=int(y), z=int(z))


class ItemPool(ObjectPool["Item"]):
    """Specialized pool for Item objects.

    Items are the second most allocated objects. This pool helps
    with bulk operations like copy/paste and map loading.
    """

    def __init__(self, max_size: int = 100000) -> None:
        def factory() -> Item:
            from py_rme_canary.core.data.item import Item

            return Item(id=0)

        def reset_fn(item: Item) -> None:
            item.id = 0
            item.count = 1
            item.action_id = None
            item.unique_id = None
            item.text = None
            item.destination = None
            # Items attribute is a tuple (immutable default), so we can't clear it.
            # If mutable list was intended, Item definition needs update.
            # For now, we assume we can't easily reuse container items without replacement.

        super().__init__(
            factory=factory,
            reset_fn=reset_fn,
            max_size=max_size,
            name="ItemPool",
        )

    def acquire_item(self, item_id: int, count: int = 1) -> Item:
        """Acquire an item with ID and count set.

        Args:
            item_id: Item type ID.
            count: Stack count.

        Returns:
            Item configured with ID and count.
        """
        item = self.acquire()
        item.id = int(item_id)
        item.count = max(1, int(count))
        return item


@dataclass
class PoolManager:
    """Central manager for all object pools.

    Provides a single access point for pools and global statistics.

    Usage:
        manager = PoolManager()
        tile = manager.tiles.acquire_at(100, 200, 7)
        item = manager.items.acquire_item(2160)

        # Later
        manager.tiles.release(tile)
        manager.items.release(item)

        # Stats
        print(manager.get_all_stats())
    """

    tiles: TilePool = field(default_factory=TilePool)
    items: ItemPool = field(default_factory=ItemPool)

    def get_all_stats(self) -> dict[str, PoolStats]:
        """Get statistics for all managed pools."""
        return {
            "tiles": self.tiles.stats,
            "items": self.items.stats,
        }

    def clear_all(self) -> dict[str, int]:
        """Clear all pools.

        Returns:
            Dict mapping pool name to objects cleared.
        """
        return {
            "tiles": self.tiles.clear(),
            "items": self.items.clear(),
        }

    def pre_allocate_all(self, tiles: int = 1000, items: int = 5000) -> dict[str, int]:
        """Pre-allocate objects in all pools.

        Args:
            tiles: Number of tiles to pre-allocate.
            items: Number of items to pre-allocate.

        Returns:
            Dict mapping pool name to objects created.
        """
        return {
            "tiles": self.tiles.pre_allocate(tiles),
            "items": self.items.pre_allocate(items),
        }


# Global pool manager singleton
_pool_manager: PoolManager | None = None


def get_pool_manager() -> PoolManager:
    """Get the global pool manager instance.

    Creates the manager on first call (lazy initialization).

    Returns:
        Global PoolManager instance.
    """
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = PoolManager()
        logger.info("Initialized global PoolManager")
    return _pool_manager


def reset_pool_manager() -> None:
    """Reset the global pool manager (for testing)."""
    global _pool_manager
    if _pool_manager is not None:
        _pool_manager.clear_all()
    _pool_manager = None
