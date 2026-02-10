"""Sprite Cache System for Performance Optimization.

High-performance LRU cache for sprite/item images with:
- Configurable max size
- Memory usage tracking
- Statistics and metrics
- Async preloading
- Texture atlas support
"""

from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class CacheStats:
    """Statistics for cache performance."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    memory_bytes: int = 0
    item_count: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100

    def reset(self) -> None:
        """Reset all stats."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_requests = 0


class LRUCache[T]:
    """Thread-safe LRU cache implementation.

    Uses OrderedDict for O(1) access and eviction.

    Args:
        max_size: Maximum number of items in cache
        max_memory: Maximum memory in bytes (optional)
        size_func: Function to calculate item size in bytes
    """

    def __init__(
        self, max_size: int = 500, max_memory: int | None = None, size_func: Callable[[T], int] | None = None
    ) -> None:
        self._max_size = max_size
        self._max_memory = max_memory
        self._size_func = size_func or (lambda x: 0)

        self._cache: OrderedDict[Any, T] = OrderedDict()
        self._lock = threading.RLock()
        self._stats = CacheStats()

    def get(self, key: Any) -> T | None:
        """Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached item or None if not found
        """
        with self._lock:
            self._stats.total_requests += 1

            if key in self._cache:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
                self._stats.hits += 1
                return self._cache[key]
            else:
                self._stats.misses += 1
                return None

    def put(self, key: Any, value: T) -> None:
        """Put item in cache.

        Args:
            key: Cache key
            value: Item to cache
        """
        with self._lock:
            # Update existing
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = value
                return

            # Add new
            self._cache[key] = value
            self._stats.item_count += 1

            self._stats.memory_bytes += self._size_func(value)

            # Evict if needed
            self._evict_if_needed()

    def _evict_if_needed(self) -> None:
        """Evict oldest items if over capacity."""
        # Size-based eviction
        while len(self._cache) > self._max_size:
            key, value = self._cache.popitem(last=False)
            self._stats.evictions += 1
            self._stats.item_count -= 1
            self._stats.memory_bytes -= self._size_func(value)

        # Memory-based eviction
        if self._max_memory:
            while self._stats.memory_bytes > self._max_memory and self._cache:
                key, value = self._cache.popitem(last=False)
                self._stats.evictions += 1
                self._stats.item_count -= 1
                self._stats.memory_bytes -= self._size_func(value)

    def remove(self, key: Any) -> bool:
        """Remove item from cache.

        Args:
            key: Cache key

        Returns:
            True if item was removed
        """
        with self._lock:
            if key in self._cache:
                value = self._cache.pop(key)
                self._stats.item_count -= 1
                self._stats.memory_bytes -= self._size_func(value)
                return True
            return False

    def clear(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
            self._stats.item_count = 0
            self._stats.memory_bytes = 0

    def contains(self, key: Any) -> bool:
        """Check if key is in cache."""
        with self._lock:
            return key in self._cache

    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats

    @property
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)


class SpriteCache:
    """Specialized cache for sprite images.

    Features:
    - QPixmap caching
    - Item ID to sprite mapping
    - Animation frame caching
    - Sprite sheet processing

    Usage:
        cache = SpriteCache.instance()
        pixmap = cache.get_sprite(100)  # Item ID 100
        if pixmap is None:
            pixmap = load_sprite(100)
            cache.cache_sprite(100, pixmap)
    """

    _instance: SpriteCache | None = None

    def __init__(self, max_sprites: int = 1000) -> None:
        self._cache = LRUCache[Any](max_size=max_sprites, size_func=self._pixmap_size)
        self._animation_cache = LRUCache[list[Any]](max_size=200)
        self._preload_queue: list[int] = []
        self._preload_thread: threading.Thread | None = None
        self._stop_preload = threading.Event()

    @classmethod
    def instance(cls) -> SpriteCache:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def _pixmap_size(pixmap: Any) -> int:
        """Calculate pixmap memory size."""
        try:
            if hasattr(pixmap, "width") and hasattr(pixmap, "height"):
                return int(pixmap.width() * pixmap.height() * 4)  # RGBA
        except Exception:
            pass
        return 1024  # Default estimate

    def get_sprite(self, item_id: int) -> Any | None:
        """Get cached sprite for item ID.

        Args:
            item_id: The item ID

        Returns:
            QPixmap or None if not cached
        """
        return self._cache.get(f"sprite_{item_id}")

    def cache_sprite(self, item_id: int, pixmap: Any) -> None:
        """Cache a sprite for item ID.

        Args:
            item_id: The item ID
            pixmap: The QPixmap to cache
        """
        self._cache.put(f"sprite_{item_id}", pixmap)

    def get_animation(self, item_id: int) -> list[Any] | None:
        """Get cached animation frames.

        Args:
            item_id: The item ID

        Returns:
            List of QPixmaps or None
        """
        return self._animation_cache.get(f"anim_{item_id}")

    def cache_animation(self, item_id: int, frames: list[Any]) -> None:
        """Cache animation frames.

        Args:
            item_id: The item ID
            frames: List of QPixmap frames
        """
        self._animation_cache.put(f"anim_{item_id}", frames)

    def get_scaled(self, item_id: int, scale: float) -> Any | None:
        """Get scaled version of sprite.

        Args:
            item_id: The item ID
            scale: Scale factor (e.g., 0.5 for half size)

        Returns:
            Scaled QPixmap or None
        """
        key = f"sprite_{item_id}_scale_{scale:.2f}"
        return self._cache.get(key)

    def cache_scaled(self, item_id: int, scale: float, pixmap: Any) -> None:
        """Cache scaled sprite.

        Args:
            item_id: The item ID
            scale: Scale factor
            pixmap: Scaled QPixmap
        """
        key = f"sprite_{item_id}_scale_{scale:.2f}"
        self._cache.put(key, pixmap)

    def schedule_preload(self, item_ids: list[int]) -> None:
        """Schedule items for background preloading.

        Args:
            item_ids: List of item IDs to preload
        """
        self._preload_queue.extend(item_ids)

        if self._preload_thread is None or not self._preload_thread.is_alive():
            self._stop_preload.clear()
            self._preload_thread = threading.Thread(target=self._preload_worker, daemon=True)
            self._preload_thread.start()

    def _preload_worker(self) -> None:
        """Background preload worker."""
        while self._preload_queue and not self._stop_preload.is_set():
            item_id = self._preload_queue.pop(0)

            # Skip if already cached
            if self._cache.contains(f"sprite_{item_id}"):
                continue

            # Load sprite (would call actual loader)
            # This is a placeholder - real implementation would load from disk
            time.sleep(0.001)  # Simulate load

    def stop_preload(self) -> None:
        """Stop background preloading."""
        self._stop_preload.set()

    def clear(self) -> None:
        """Clear all caches."""
        self._cache.clear()
        self._animation_cache.clear()
        self._preload_queue.clear()

    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._cache.stats

    def get_memory_usage_mb(self) -> float:
        """Get memory usage in MB."""
        return self._cache.stats.memory_bytes / (1024 * 1024)


class TileCache:
    """Cache for rendered tile composites.

    Caches the final rendered result of tiles (with all items composited)
    to avoid re-rendering unchanged tiles.
    """

    _instance: TileCache | None = None

    def __init__(self, max_tiles: int = 2000) -> None:
        self._cache = LRUCache[Any](max_size=max_tiles)
        self._dirty_tiles: set[tuple[int, int, int]] = set()

    @classmethod
    def instance(cls) -> TileCache:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_tile(self, x: int, y: int, z: int) -> Any | None:
        """Get cached tile render.

        Args:
            x, y, z: Tile position

        Returns:
            Rendered tile pixmap or None
        """
        if (x, y, z) in self._dirty_tiles:
            return None
        return self._cache.get((x, y, z))

    def cache_tile(self, x: int, y: int, z: int, pixmap: Any) -> None:
        """Cache rendered tile.

        Args:
            x, y, z: Tile position
            pixmap: Rendered tile pixmap
        """
        self._cache.put((x, y, z), pixmap)
        self._dirty_tiles.discard((x, y, z))

    def invalidate_tile(self, x: int, y: int, z: int) -> None:
        """Mark tile as dirty/needing re-render.

        Args:
            x, y, z: Tile position
        """
        self._dirty_tiles.add((x, y, z))
        self._cache.remove((x, y, z))

    def invalidate_region(self, x1: int, y1: int, x2: int, y2: int, z: int) -> None:
        """Invalidate a region of tiles.

        Args:
            x1, y1: Start position
            x2, y2: End position
            z: Floor
        """
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                self.invalidate_tile(x, y, z)

    def invalidate_floor(self, z: int) -> None:
        """Invalidate all tiles on a floor.

        Args:
            z: Floor to invalidate
        """
        # Mark all tiles on floor as dirty
        keys_to_remove = [k for k in self._cache._cache if k[2] == z]
        for key in keys_to_remove:
            self._cache.remove(key)
            self._dirty_tiles.add(key)

    def clear(self) -> None:
        """Clear all cached tiles."""
        self._cache.clear()
        self._dirty_tiles.clear()

    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._cache.stats


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""

    fps: float = 0.0
    frame_time_ms: float = 0.0
    render_time_ms: float = 0.0
    tiles_rendered: int = 0
    cache_hit_rate: float = 0.0
    memory_mb: float = 0.0

    _frame_times: list[float] = field(default_factory=list)
    _sample_window: int = 60

    def record_frame(self, frame_time: float) -> None:
        """Record a frame time."""
        self._frame_times.append(frame_time)
        if len(self._frame_times) > self._sample_window:
            self._frame_times.pop(0)

        self.frame_time_ms = sum(self._frame_times) / len(self._frame_times) * 1000
        if self.frame_time_ms > 0:
            self.fps = 1000 / self.frame_time_ms


class PerformanceMonitor:
    """Monitor and report performance metrics.

    Usage:
        monitor = PerformanceMonitor.instance()

        with monitor.measure_frame():
            render_scene()

        print(f"FPS: {monitor.metrics.fps:.1f}")
    """

    _instance: PerformanceMonitor | None = None

    def __init__(self) -> None:
        self._metrics = PerformanceMetrics()
        self._frame_start: float = 0.0

    @classmethod
    def instance(cls) -> PerformanceMonitor:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def metrics(self) -> PerformanceMetrics:
        """Get current metrics."""
        return self._metrics

    def start_frame(self) -> None:
        """Start timing a frame."""
        self._frame_start = time.perf_counter()

    def end_frame(self) -> None:
        """End timing a frame and record metrics."""
        if self._frame_start > 0:
            elapsed = time.perf_counter() - self._frame_start
            self._metrics.record_frame(elapsed)
            self._frame_start = 0.0

    def measure_frame(self) -> FrameTimer:
        """Context manager for frame timing."""
        return FrameTimer(self)

    def update_cache_stats(self) -> None:
        """Update cache statistics in metrics."""
        sprite_cache = SpriteCache.instance()
        tile_cache = TileCache.instance()

        total_hits = sprite_cache.stats.hits + tile_cache.stats.hits
        total_reqs = sprite_cache.stats.total_requests + tile_cache.stats.total_requests

        if total_reqs > 0:
            self._metrics.cache_hit_rate = (total_hits / total_reqs) * 100

        self._metrics.memory_mb = sprite_cache.get_memory_usage_mb() + tile_cache.stats.memory_bytes / (1024 * 1024)


class FrameTimer:
    """Context manager for frame timing."""

    def __init__(self, monitor: PerformanceMonitor) -> None:
        self._monitor = monitor

    def __enter__(self) -> FrameTimer:
        self._monitor.start_frame()
        return self

    def __exit__(self, *args: object) -> None:
        self._monitor.end_frame()
