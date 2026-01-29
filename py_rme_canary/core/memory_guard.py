from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


class MemoryGuardError(RuntimeError):
    """Raised when a hard memory limit is exceeded."""


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        return int(default)
    try:
        return int(str(v).strip())
    except ValueError:
        return int(default)


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return bool(default)
    v = str(v).strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return bool(default)


def _mb_to_bytes(mb: int) -> int:
    return int(mb) * 1024 * 1024


@dataclass(frozen=True, slots=True)
class MemoryGuardConfig:
    enabled: bool = True

    # OTBM preload
    warn_file_bytes: int = _mb_to_bytes(256)
    hard_file_bytes: int = _mb_to_bytes(1024)

    # Map growth
    warn_tiles: int = 1_000_000
    hard_tiles: int = 2_000_000
    warn_items: int = 8_000_000
    hard_items: int = 16_000_000

    # Sprite/pixmap caches
    warn_sprite_cache_entries: int = 80_000
    hard_sprite_cache_entries: int = 150_000
    warn_qt_pixmap_cache_entries: int = 20_000
    hard_qt_pixmap_cache_entries: int = 40_000

    # Eviction targets after hitting hard limits (keeps cache below hard and reduces churn)
    evict_to_sprite_cache_entries: int = 120_000
    evict_to_qt_pixmap_cache_entries: int = 30_000

    # Incremental check cadence (trade-off: overhead vs responsiveness)
    check_every_tiles: int = 4096

    @classmethod
    def load_default(cls) -> MemoryGuardConfig:
        """Load config from env vars and optional JSON override.

        Env vars (all optional):
        - PY_RME_MEMORY_GUARD: 0/1
        - PY_RME_MEM_WARN_FILE_MB / PY_RME_MEM_HARD_FILE_MB
        - PY_RME_MEM_WARN_TILES / PY_RME_MEM_HARD_TILES
        - PY_RME_MEM_WARN_ITEMS / PY_RME_MEM_HARD_ITEMS
        - PY_RME_MEM_WARN_SPRITE_CACHE / PY_RME_MEM_HARD_SPRITE_CACHE
        - PY_RME_MEM_WARN_QT_PIXMAP_CACHE / PY_RME_MEM_HARD_QT_PIXMAP_CACHE
        - PY_RME_MEM_EVICT_TO_SPRITE_CACHE
        - PY_RME_MEM_EVICT_TO_QT_PIXMAP_CACHE
        - PY_RME_MEM_CHECK_EVERY_TILES
        - PY_RME_MEMORY_GUARD_CONFIG: path to a JSON file
        """

        base = cls(
            enabled=_env_bool("PY_RME_MEMORY_GUARD", True),
            warn_file_bytes=_mb_to_bytes(_env_int("PY_RME_MEM_WARN_FILE_MB", 256)),
            hard_file_bytes=_mb_to_bytes(_env_int("PY_RME_MEM_HARD_FILE_MB", 1024)),
            warn_tiles=_env_int("PY_RME_MEM_WARN_TILES", 1_000_000),
            hard_tiles=_env_int("PY_RME_MEM_HARD_TILES", 2_000_000),
            warn_items=_env_int("PY_RME_MEM_WARN_ITEMS", 8_000_000),
            hard_items=_env_int("PY_RME_MEM_HARD_ITEMS", 16_000_000),
            warn_sprite_cache_entries=_env_int("PY_RME_MEM_WARN_SPRITE_CACHE", 80_000),
            hard_sprite_cache_entries=_env_int("PY_RME_MEM_HARD_SPRITE_CACHE", 150_000),
            warn_qt_pixmap_cache_entries=_env_int("PY_RME_MEM_WARN_QT_PIXMAP_CACHE", 20_000),
            hard_qt_pixmap_cache_entries=_env_int("PY_RME_MEM_HARD_QT_PIXMAP_CACHE", 40_000),
            evict_to_sprite_cache_entries=_env_int("PY_RME_MEM_EVICT_TO_SPRITE_CACHE", 120_000),
            evict_to_qt_pixmap_cache_entries=_env_int("PY_RME_MEM_EVICT_TO_QT_PIXMAP_CACHE", 30_000),
            check_every_tiles=max(1, _env_int("PY_RME_MEM_CHECK_EVERY_TILES", 4096)),
        )

        cfg_path = os.getenv("PY_RME_MEMORY_GUARD_CONFIG")
        if cfg_path is None or str(cfg_path).strip() == "":
            # Optional convention: data/memory_guard.json at repo root.
            default_path = Path("data") / "memory_guard.json"
            if default_path.exists():
                cfg_path = str(default_path)

        if cfg_path is None or str(cfg_path).strip() == "":
            return base

        try:
            p = Path(cfg_path)
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return base

        if not isinstance(data, dict):
            return base

        def gi(key: str, cur: int) -> int:
            v = data.get(key)
            if v is None:
                return int(cur)
            try:
                return int(v)
            except Exception:
                return int(cur)

        def gb(key: str, cur: bool) -> bool:
            v = data.get(key)
            if v is None:
                return bool(cur)
            if isinstance(v, bool):
                return bool(v)
            return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}

        return cls(
            enabled=gb("enabled", base.enabled),
            warn_file_bytes=_mb_to_bytes(gi("warn_file_mb", base.warn_file_bytes // (1024 * 1024))),
            hard_file_bytes=_mb_to_bytes(gi("hard_file_mb", base.hard_file_bytes // (1024 * 1024))),
            warn_tiles=gi("warn_tiles", base.warn_tiles),
            hard_tiles=gi("hard_tiles", base.hard_tiles),
            warn_items=gi("warn_items", base.warn_items),
            hard_items=gi("hard_items", base.hard_items),
            warn_sprite_cache_entries=gi("warn_sprite_cache_entries", base.warn_sprite_cache_entries),
            hard_sprite_cache_entries=gi("hard_sprite_cache_entries", base.hard_sprite_cache_entries),
            warn_qt_pixmap_cache_entries=gi("warn_qt_pixmap_cache_entries", base.warn_qt_pixmap_cache_entries),
            hard_qt_pixmap_cache_entries=gi("hard_qt_pixmap_cache_entries", base.hard_qt_pixmap_cache_entries),
            evict_to_sprite_cache_entries=gi("evict_to_sprite_cache_entries", base.evict_to_sprite_cache_entries),
            evict_to_qt_pixmap_cache_entries=gi(
                "evict_to_qt_pixmap_cache_entries", base.evict_to_qt_pixmap_cache_entries
            ),
            check_every_tiles=max(1, gi("check_every_tiles", base.check_every_tiles)),
        )


class MemoryGuard:
    """Lightweight, deterministic guardrail for big maps/assets.

    This intentionally does NOT depend on process RSS (platform-dependent).
    It uses deterministic proxies that correlate strongly with memory use:
    - tiles count
    - items count
    - cache entry counts
    - input file size
    """

    def __init__(self, config: MemoryGuardConfig | None = None):
        self.config = config or MemoryGuardConfig.load_default()
        self._warned: set[str] = set()

    def enabled(self) -> bool:
        return bool(self.config.enabled)

    def _warn_once(self, key: str) -> bool:
        if key in self._warned:
            return False
        self._warned.add(key)
        return True

    # ----- preload checks -----

    def check_file_size(self, *, path: str, stage: str = "preload") -> None:
        if not self.enabled():
            return

        try:
            size = Path(path).stat().st_size
        except Exception:
            return

        if size >= int(self.config.hard_file_bytes):
            raise MemoryGuardError(
                f"{stage}: input file too large ({size} bytes) >= hard limit ({self.config.hard_file_bytes} bytes)"
            )
        if size >= int(self.config.warn_file_bytes) and self._warn_once("warn_file_bytes"):
            # Warning only; caller can surface this in UI/logs.
            return

    # ----- incremental checks -----

    def check_map_counts(self, *, tiles: int, items: int, stage: str) -> str | None:
        if not self.enabled():
            return None

        tiles = int(tiles)
        items = int(items)

        if tiles >= int(self.config.hard_tiles):
            raise MemoryGuardError(
                f"{stage}: tiles >= hard limit ({tiles} >= {self.config.hard_tiles}). "
                "Reduce map size or increase limits."
            )
        if items >= int(self.config.hard_items):
            raise MemoryGuardError(
                f"{stage}: items >= hard limit ({items} >= {self.config.hard_items}). "
                "Reduce map complexity or increase limits."
            )

        if tiles >= int(self.config.warn_tiles) and self._warn_once("warn_tiles"):
            return f"{stage}: tiles high ({tiles} >= {self.config.warn_tiles})"
        if items >= int(self.config.warn_items) and self._warn_once("warn_items"):
            return f"{stage}: items high ({items} >= {self.config.warn_items})"
        return None

    def check_cache_entries(self, *, kind: str, entries: int, stage: str) -> str | None:
        if not self.enabled():
            return None

        entries = int(entries)
        kind = str(kind)
        if kind == "sprite_cache":
            warn = int(self.config.warn_sprite_cache_entries)
            hard = int(self.config.hard_sprite_cache_entries)
        elif kind == "qt_pixmap_cache":
            warn = int(self.config.warn_qt_pixmap_cache_entries)
            hard = int(self.config.hard_qt_pixmap_cache_entries)
        else:
            return None

        if entries >= hard:
            raise MemoryGuardError(f"{stage}: {kind} entries >= hard limit ({entries} >= {hard})")
        if entries >= warn and self._warn_once(f"warn_{kind}"):
            return f"{stage}: {kind} entries high ({entries} >= {warn})"
        return None


_DEFAULT_GUARD: MemoryGuard | None = None


def default_memory_guard() -> MemoryGuard:
    global _DEFAULT_GUARD
    if _DEFAULT_GUARD is None:
        _DEFAULT_GUARD = MemoryGuard(MemoryGuardConfig.load_default())
    return _DEFAULT_GUARD
