#!/usr/bin/env python3
"""
Worker Pool Manager - v2.2.0
Parallel execution with Redis coordination (optional)
Future: Rust worker backend (v3.0)
"""

import argparse
import hashlib
import logging
import multiprocessing as mp
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


@dataclass
class WorkerTask:
    """Task representation for worker pool"""

    task_id: str
    module: str
    target: Path
    config: dict[str, Any]
    priority: int = 0


@dataclass
class WorkerResult:
    """Result from worker execution"""

    task_id: str
    success: bool
    duration: float
    output: dict[str, Any]
    error: str | None = None


class CacheBackend(ABC):
    """Abstract cache layer - supports local and Redis"""

    @abstractmethod
    def get(self, key: str) -> str | None:
        pass

    @abstractmethod
    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        pass

    @abstractmethod
    def invalidate(self, pattern: str) -> int:
        pass


class LocalCache(CacheBackend):
    """In-memory cache (single-process)"""

    def __init__(self):
        self._cache: dict[str, tuple[str, float]] = {}

    def get(self, key: str) -> str | None:
        if key not in self._cache:
            return None

        value, expires = self._cache[key]
        if time.time() > expires:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        expires = time.time() + ttl
        self._cache[key] = (value, expires)
        return True

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def invalidate(self, pattern: str) -> int:
        """Simple prefix matching (not regex for performance)"""
        to_remove = [k for k in self._cache if k.startswith(pattern.rstrip("*"))]
        for key in to_remove:
            del self._cache[key]
        return len(to_remove)


class RedisCache(CacheBackend):
    """Distributed Redis cache (multi-process/machine)"""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        if not REDIS_AVAILABLE:
            raise RuntimeError("redis package not installed")

        self.client = redis.Redis(
            host=host, port=port, db=db, decode_responses=True, socket_connect_timeout=5, socket_timeout=5
        )

        # Test connection
        try:
            self.client.ping()
            log.info(f"Redis connected: {host}:{port}")
        except redis.ConnectionError as err:
            raise RuntimeError(f"Redis connection failed: {host}:{port}") from err

    def get(self, key: str) -> str | None:
        try:
            return self.client.get(key)
        except redis.RedisError as e:
            log.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        try:
            return bool(self.client.setex(key, ttl, value))
        except redis.RedisError as e:
            log.error(f"Redis set error: {e}")
            return False

    def exists(self, key: str) -> bool:
        try:
            return bool(self.client.exists(key))
        except redis.RedisError as e:
            log.error(f"Redis exists error: {e}")
            return False

    def invalidate(self, pattern: str) -> int:
        """Delete keys matching pattern (Redis SCAN)"""
        try:
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = self.client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted += self.client.delete(*keys)
                if cursor == 0:
                    break
            return deleted
        except redis.RedisError as e:
            log.error(f"Redis invalidate error: {e}")
            return 0


class WorkerPool:
    """Parallel execution manager with cache integration"""

    def __init__(self, max_workers: int | None = None, cache: CacheBackend | None = None):
        self.max_workers = max_workers or mp.cpu_count()
        self.cache = cache or LocalCache()

        log.info(f"Worker pool: {self.max_workers} workers")
        log.info(f"Cache backend: {type(self.cache).__name__}")

    def execute_tasks(
        self, tasks: list[WorkerTask], worker_func: Callable[[WorkerTask], WorkerResult]
    ) -> list[WorkerResult]:
        """Execute tasks in parallel with cache checking"""

        log.info(f"Executing {len(tasks)} task(s) in parallel")

        # Sort by priority (higher first)
        tasks.sort(key=lambda t: t.priority, reverse=True)

        # Filter cached tasks
        uncached_tasks = []
        cached_results = []

        for task in tasks:
            cache_key = self._task_cache_key(task)

            if self.cache.exists(cache_key):
                log.info(f"Cache hit: {task.task_id}")
                # Reconstruct result from cache
                cached_results.append(
                    WorkerResult(task_id=task.task_id, success=True, duration=0.0, output={"cached": True}, error=None)
                )
            else:
                uncached_tasks.append(task)

        if not uncached_tasks:
            log.info("All tasks cached, skipping execution")
            return cached_results

        # Execute uncached tasks
        results = []

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_task = {executor.submit(worker_func, task): task for task in uncached_tasks}

            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]

                try:
                    result = future.result()
                    results.append(result)

                    # Cache successful results
                    if result.success:
                        cache_key = self._task_cache_key(task)
                        self.cache.set(cache_key, "success", ttl=86400)  # 24h

                    log.info(f"Task {task.task_id}: {'✓' if result.success else '✗'} ({result.duration:.2f}s)")

                except Exception as e:
                    log.error(f"Task {task.task_id} failed: {e}")
                    results.append(
                        WorkerResult(task_id=task.task_id, success=False, duration=0.0, output={}, error=str(e))
                    )

        # Combine cached + executed
        all_results = cached_results + results

        # Summary
        success_count = sum(1 for r in all_results if r.success)
        total_duration = sum(r.duration for r in all_results)

        log.info(f"Results: {success_count}/{len(all_results)} success, {total_duration:.2f}s total")

        return all_results

    def _task_cache_key(self, task: WorkerTask) -> str:
        """Generate cache key from task"""
        # Include file hash for cache invalidation
        file_hash = self._hash_file(task.target)
        return f"quality:task:{task.module}:{file_hash}"

    def _hash_file(self, path: Path) -> str:
        """Fast file hash for cache invalidation"""
        if not path.exists():
            return "missing"

        # Use mtime + size (fast) instead of content hash
        stat = path.stat()
        signature = f"{stat.st_mtime}:{stat.st_size}"

        return hashlib.sha256(signature.encode()).hexdigest()[:8]


# Example worker function (v2.2 - Python)
# v3.0 will call Rust binary via subprocess
def example_worker(task: WorkerTask) -> WorkerResult:
    """Example worker - analyze single file"""

    start_time = time.time()

    try:
        # Simulate work
        log.info(f"Worker processing: {task.target}")

        # Real implementation would call module
        # For now, just validate file exists
        if not task.target.exists():
            raise FileNotFoundError(f"File not found: {task.target}")

        # Simulate analysis
        time.sleep(0.1)  # Remove in production

        output = {
            "file": str(task.target),
            "module": task.module,
            "timestamp": datetime.now().isoformat(),
            "issues": [],
        }

        duration = time.time() - start_time

        return WorkerResult(task_id=task.task_id, success=True, duration=duration, output=output)

    except Exception as e:
        duration = time.time() - start_time
        return WorkerResult(task_id=task.task_id, success=False, duration=duration, output={}, error=str(e))


def create_cache_backend(config: dict[str, Any]) -> CacheBackend:
    """Factory for cache backends"""

    if config.get("redis", {}).get("enabled"):
        if not REDIS_AVAILABLE:
            log.warning("Redis requested but package not installed, using local cache")
            return LocalCache()

        try:
            return RedisCache(
                host=config["redis"].get("host", "localhost"),
                port=config["redis"].get("port", 6379),
                db=config["redis"].get("db", 0),
            )
        except RuntimeError as e:
            log.warning(f"Redis connection failed, using local cache: {e}")
            return LocalCache()

    return LocalCache()


def main():
    """Demo: parallel file analysis"""

    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--module", default="ruff")
    parser.add_argument("--workers", type=int, default=mp.cpu_count())
    parser.add_argument("--use-redis", action="store_true")

    args = parser.parse_args()

    # Find Python files
    py_files = [p for p in args.project.rglob("*.py") if ".venv" not in str(p)]

    log.info(f"Found {len(py_files)} Python files")

    # Create tasks
    tasks = [
        WorkerTask(task_id=f"task_{i}", module=args.module, target=file_path, config={}, priority=0)
        for i, file_path in enumerate(py_files)
    ]

    # Configure cache
    cache_config = {"redis": {"enabled": args.use_redis, "host": "localhost", "port": 6379, "db": 0}}

    cache = create_cache_backend(cache_config)

    # Execute
    pool = WorkerPool(max_workers=args.workers, cache=cache)
    results = pool.execute_tasks(tasks, example_worker)

    # Report
    print(f"\n{'=' * 60}")
    print("Execution Summary:")
    print(f"  Total tasks: {len(results)}")
    print(f"  Successful: {sum(1 for r in results if r.success)}")
    print(f"  Failed: {sum(1 for r in results if not r.success)}")
    print(f"  Total time: {sum(r.duration for r in results):.2f}s")
    print(f"  Avg per task: {sum(r.duration for r in results) / len(results):.2f}s")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
