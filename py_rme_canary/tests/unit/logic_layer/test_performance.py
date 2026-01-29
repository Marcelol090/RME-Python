"""Unit tests for performance optimization systems."""

from __future__ import annotations

import time
from unittest.mock import MagicMock


class TestLRUCache:
    """Tests for LRU cache."""

    def test_cache_creation(self):
        """Test creating LRU cache."""
        from py_rme_canary.logic_layer.sprite_cache import LRUCache

        cache = LRUCache[int](max_size=100)
        assert cache is not None
        assert cache.size == 0

    def test_put_and_get(self):
        """Test putting and getting values."""
        from py_rme_canary.logic_layer.sprite_cache import LRUCache

        cache = LRUCache[str](max_size=100)
        cache.put("key1", "value1")

        assert cache.get("key1") == "value1"
        assert cache.size == 1

    def test_get_missing(self):
        """Test getting missing key."""
        from py_rme_canary.logic_layer.sprite_cache import LRUCache

        cache = LRUCache[str](max_size=100)

        assert cache.get("missing") is None

    def test_lru_eviction(self):
        """Test LRU eviction happens."""
        from py_rme_canary.logic_layer.sprite_cache import LRUCache

        cache = LRUCache[int](max_size=3)

        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        cache.put("d", 4)  # Should evict "a"

        assert cache.get("a") is None
        assert cache.get("b") == 2

    def test_access_updates_lru(self):
        """Test accessing an item moves it to end."""
        from py_rme_canary.logic_layer.sprite_cache import LRUCache

        cache = LRUCache[int](max_size=3)

        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)

        # Access "a" to make it recently used
        cache.get("a")

        # Add new item - should evict "b" (now oldest)
        cache.put("d", 4)

        assert cache.get("a") == 1
        assert cache.get("b") is None

    def test_statistics(self):
        """Test cache statistics."""
        from py_rme_canary.logic_layer.sprite_cache import LRUCache

        cache = LRUCache[int](max_size=10)

        cache.put("a", 1)
        cache.get("a")  # Hit
        cache.get("b")  # Miss

        assert cache.stats.hits == 1
        assert cache.stats.misses == 1
        assert cache.stats.total_requests == 2

    def test_remove(self):
        """Test removing item."""
        from py_rme_canary.logic_layer.sprite_cache import LRUCache

        cache = LRUCache[str](max_size=10)
        cache.put("key", "value")

        assert cache.remove("key") is True
        assert cache.get("key") is None

    def test_clear(self):
        """Test clearing cache."""
        from py_rme_canary.logic_layer.sprite_cache import LRUCache

        cache = LRUCache[int](max_size=10)
        cache.put("a", 1)
        cache.put("b", 2)

        cache.clear()

        assert cache.size == 0


class TestSpriteCache:
    """Tests for sprite cache."""

    def test_singleton(self):
        """Test singleton instance."""
        from py_rme_canary.logic_layer.sprite_cache import SpriteCache

        cache1 = SpriteCache.instance()
        cache2 = SpriteCache.instance()

        assert cache1 is cache2

    def test_cache_sprite(self):
        """Test caching sprite."""
        from py_rme_canary.logic_layer.sprite_cache import SpriteCache

        cache = SpriteCache.instance()
        cache.clear()

        mock_pixmap = MagicMock()
        mock_pixmap.width.return_value = 32
        mock_pixmap.height.return_value = 32

        cache.cache_sprite(100, mock_pixmap)

        assert cache.get_sprite(100) is mock_pixmap

    def test_cache_animation(self):
        """Test caching animation."""
        from py_rme_canary.logic_layer.sprite_cache import SpriteCache

        cache = SpriteCache.instance()
        cache.clear()

        frames = [MagicMock() for _ in range(4)]
        cache.cache_animation(100, frames)

        cached = cache.get_animation(100)
        assert len(cached) == 4

    def test_scaled_sprite(self):
        """Test caching scaled sprite."""
        from py_rme_canary.logic_layer.sprite_cache import SpriteCache

        cache = SpriteCache.instance()
        cache.clear()

        mock_pixmap = MagicMock()
        cache.cache_scaled(100, 0.5, mock_pixmap)

        assert cache.get_scaled(100, 0.5) is mock_pixmap
        assert cache.get_scaled(100, 1.0) is None


class TestTileCache:
    """Tests for tile cache."""

    def test_singleton(self):
        """Test singleton instance."""
        from py_rme_canary.logic_layer.sprite_cache import TileCache

        cache1 = TileCache.instance()
        cache2 = TileCache.instance()

        assert cache1 is cache2

    def test_cache_tile(self):
        """Test caching tile."""
        from py_rme_canary.logic_layer.sprite_cache import TileCache

        cache = TileCache.instance()
        cache.clear()

        mock_pixmap = MagicMock()
        cache.cache_tile(10, 20, 7, mock_pixmap)

        assert cache.get_tile(10, 20, 7) is mock_pixmap

    def test_invalidate_tile(self):
        """Test invalidating tile."""
        from py_rme_canary.logic_layer.sprite_cache import TileCache

        cache = TileCache.instance()
        cache.clear()

        mock_pixmap = MagicMock()
        cache.cache_tile(10, 20, 7, mock_pixmap)

        cache.invalidate_tile(10, 20, 7)

        assert cache.get_tile(10, 20, 7) is None

    def test_invalidate_region(self):
        """Test invalidating region."""
        from py_rme_canary.logic_layer.sprite_cache import TileCache

        cache = TileCache.instance()
        cache.clear()

        # Cache some tiles
        for x in range(5):
            for y in range(5):
                cache.cache_tile(x, y, 7, MagicMock())

        # Invalidate 3x3 region
        cache.invalidate_region(1, 1, 3, 3, 7)

        # Tiles in region should be invalid
        assert cache.get_tile(2, 2, 7) is None
        # Tiles outside should be valid
        assert cache.get_tile(0, 0, 7) is not None


class TestPerformanceMonitor:
    """Tests for performance monitor."""

    def test_singleton(self):
        """Test singleton instance."""
        from py_rme_canary.logic_layer.sprite_cache import PerformanceMonitor

        mon1 = PerformanceMonitor.instance()
        mon2 = PerformanceMonitor.instance()

        assert mon1 is mon2

    def test_frame_timing(self):
        """Test frame timing."""
        from py_rme_canary.logic_layer.sprite_cache import PerformanceMonitor

        monitor = PerformanceMonitor.instance()

        monitor.start_frame()
        time.sleep(0.01)  # 10ms
        monitor.end_frame()

        assert monitor.metrics.frame_time_ms > 0

    def test_frame_timer_context(self):
        """Test frame timer as context manager."""
        from py_rme_canary.logic_layer.sprite_cache import PerformanceMonitor

        monitor = PerformanceMonitor.instance()

        with monitor.measure_frame():
            time.sleep(0.005)

        assert monitor.metrics.frame_time_ms > 0


class TestViewportCuller:
    """Tests for viewport culling."""

    def test_culler_creation(self):
        """Test creating culler."""
        from py_rme_canary.logic_layer.render_optimizer import ViewportCuller

        culler = ViewportCuller()
        assert culler is not None

    def test_is_visible(self):
        """Test visibility check."""
        from py_rme_canary.logic_layer.render_optimizer import ViewportCuller

        culler = ViewportCuller()
        culler.set_viewport(0, 0, 320, 240, 32)  # 10x7.5 tiles

        assert culler.is_visible(0, 0)
        assert culler.is_visible(9, 6)
        assert not culler.is_visible(100, 100)

    def test_get_visible_tiles(self):
        """Test getting visible tiles."""
        from py_rme_canary.logic_layer.render_optimizer import ViewportCuller

        culler = ViewportCuller()
        culler.set_viewport(0, 0, 96, 96, 32)  # 3x3 tiles + margin

        tiles = list(culler.get_visible_tiles())

        assert len(tiles) > 0
        # All tiles should be in valid range
        for x, y in tiles:
            assert culler.is_visible(x, y)


class TestDirtyRectTracker:
    """Tests for dirty rectangle tracking."""

    def test_tracker_creation(self):
        """Test creating tracker."""
        from py_rme_canary.logic_layer.render_optimizer import DirtyRectTracker

        tracker = DirtyRectTracker()
        assert tracker is not None
        assert tracker.dirty_count == 0

    def test_mark_dirty(self):
        """Test marking dirty."""
        from py_rme_canary.logic_layer.render_optimizer import DirtyRectTracker

        tracker = DirtyRectTracker()
        tracker.mark_dirty(0, 0, 32, 32)

        assert tracker.dirty_count >= 1

    def test_clear(self):
        """Test clearing."""
        from py_rme_canary.logic_layer.render_optimizer import DirtyRectTracker

        tracker = DirtyRectTracker()
        tracker.mark_dirty(0, 0, 32, 32)
        tracker.clear()

        assert tracker.dirty_count == 0

    def test_merge_nearby(self):
        """Test merging nearby rectangles."""
        from py_rme_canary.logic_layer.render_optimizer import DirtyRectTracker

        tracker = DirtyRectTracker(merge_threshold=16)

        # Add two adjacent rectangles
        tracker.mark_dirty(0, 0, 32, 32)
        tracker.mark_dirty(40, 0, 32, 32)  # 8px gap

        # Should merge into one
        rects = tracker.get_dirty_rects()
        assert len(rects) == 1


class TestLODManager:
    """Tests for level of detail."""

    def test_lod_creation(self):
        """Test creating LOD manager."""
        from py_rme_canary.logic_layer.render_optimizer import LODManager

        lod = LODManager()
        assert lod is not None

    def test_lod_at_100_percent(self):
        """Test LOD at 100% zoom."""
        from py_rme_canary.logic_layer.render_optimizer import LODManager

        lod = LODManager()
        settings = lod.get_lod(1.0)

        assert settings.show_items is True
        assert settings.show_creatures is True

    def test_lod_at_low_zoom(self):
        """Test LOD at low zoom."""
        from py_rme_canary.logic_layer.render_optimizer import LODManager

        lod = LODManager()
        settings = lod.get_lod(0.1)

        # At very low zoom, should hide some details
        # This depends on default levels
        assert isinstance(settings.show_items, bool)


class TestBatchRenderer:
    """Tests for batch renderer."""

    def test_batch_creation(self):
        """Test creating batch renderer."""
        from py_rme_canary.logic_layer.render_optimizer import BatchRenderer

        batch = BatchRenderer()
        assert batch is not None
        assert batch.total_count == 0

    def test_add_items(self):
        """Test adding items to batch."""
        from py_rme_canary.logic_layer.render_optimizer import BatchRenderer

        batch = BatchRenderer()
        batch.add_ground(0, 0, 100)
        batch.add_item(0, 0, 200)
        batch.add_creature(0, 0, 300)

        assert batch.total_count == 3

    def test_flush(self):
        """Test flushing batch."""
        from py_rme_canary.logic_layer.render_optimizer import BatchRenderer

        batch = BatchRenderer()
        batch.add_ground(0, 0, 100)
        batch.add_item(0, 0, 200)

        ground, items, creatures = batch.flush()

        assert len(ground) == 1
        assert len(items) == 1
        assert len(creatures) == 0
        assert batch.total_count == 0  # Should be cleared


class TestRenderOptimizer:
    """Tests for combined render optimizer."""

    def test_optimizer_creation(self):
        """Test creating optimizer."""
        from py_rme_canary.logic_layer.render_optimizer import RenderOptimizer

        optimizer = RenderOptimizer()
        assert optimizer is not None

    def test_should_render(self):
        """Test should_render check."""
        from py_rme_canary.logic_layer.render_optimizer import RenderOptimizer

        optimizer = RenderOptimizer()
        optimizer.set_viewport(0, 0, 320, 240, 32)

        assert optimizer.should_render(0, 0) is True
        assert optimizer.should_render(1000, 1000) is False

    def test_full_workflow(self):
        """Test full render workflow."""
        from py_rme_canary.logic_layer.render_optimizer import RenderOptimizer

        optimizer = RenderOptimizer()
        optimizer.set_viewport(0, 0, 320, 240, 32)
        optimizer.set_zoom(1.0)

        optimizer.begin_frame()

        for x, y in optimizer.get_visible_tiles():
            if optimizer.should_render(x, y):
                optimizer.batch.add_ground(x, y, 100)

        ground, items, creatures = optimizer.end_frame()

        assert len(ground) > 0
