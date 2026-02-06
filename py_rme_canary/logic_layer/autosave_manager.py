"""AutoSave Manager for automatic map backup.

This module provides automatic periodic saving of the map to prevent
data loss. It runs in a background thread and creates timestamped
backup files.

Architecture:
    - AutoSaveManager: Main class handling scheduling and execution
    - AutoSaveConfig: Settings dataclass
    - Uses QTimer integration for PyQt6 compatibility

Layer: logic_layer (signals are Qt-free, use callbacks)
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass
class AutoSaveConfig:
    """Configuration for autosave behavior.

    Attributes:
        enabled: Whether autosave is active.
        interval_seconds: Time between saves (default 5 minutes).
        max_backups: Maximum backup files to keep (oldest deleted).
        backup_dir: Directory for backups (None = same as map).
        compress: Whether to use GZIP compression.
        save_on_exit: Prompt for backup on exit.
        min_changes: Minimum changes before autosave triggers.
    """

    enabled: bool = True
    interval_seconds: int = 300  # 5 minutes
    max_backups: int = 10
    backup_dir: Path | None = None
    compress: bool = True
    save_on_exit: bool = True
    min_changes: int = 10

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AutoSaveConfig:
        """Create config from dictionary."""
        backup_dir = data.get("backup_dir")
        if backup_dir is not None:
            backup_dir = Path(backup_dir)

        return cls(
            enabled=bool(data.get("enabled", True)),
            interval_seconds=int(data.get("interval_seconds", 300)),
            max_backups=int(data.get("max_backups", 10)),
            backup_dir=backup_dir,
            compress=bool(data.get("compress", True)),
            save_on_exit=bool(data.get("save_on_exit", True)),
            min_changes=int(data.get("min_changes", 10)),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "interval_seconds": self.interval_seconds,
            "max_backups": self.max_backups,
            "backup_dir": str(self.backup_dir) if self.backup_dir else None,
            "compress": self.compress,
            "save_on_exit": self.save_on_exit,
            "min_changes": self.min_changes,
        }


@dataclass
class AutoSaveState:
    """Runtime state for autosave manager.

    Attributes:
        last_save_time: Timestamp of last autosave.
        changes_since_save: Number of modifications since last save.
        total_autosaves: Total autosaves this session.
        last_backup_path: Path of most recent backup.
        is_saving: Whether a save is in progress.
    """

    last_save_time: float = 0.0
    changes_since_save: int = 0
    total_autosaves: int = 0
    last_backup_path: Path | None = None
    is_saving: bool = False


class AutoSaveManager:
    """Manages automatic periodic map backups.

    The manager monitors map changes and periodically creates backup
    files. It integrates with the editor session to track modifications.

    Usage:
        manager = AutoSaveManager(config)
        manager.set_save_callback(lambda path: save_map_to_file(path))
        manager.start()

        # When map changes:
        manager.notify_change()

        # On exit:
        manager.stop()

    Callbacks:
        on_save_start: Called before save begins
        on_save_complete: Called after successful save (path, elapsed)
        on_save_error: Called on save failure (error message)
    """

    def __init__(self, config: AutoSaveConfig | None = None) -> None:
        """Initialize autosave manager.

        Args:
            config: AutoSaveConfig (uses defaults if None).
        """
        self._config = config or AutoSaveConfig()
        self._state = AutoSaveState()

        # Threading
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

        # Callbacks
        self._save_callback: Callable[[Path], bool] | None = None
        self._on_save_start: Callable[[], None] | None = None
        self._on_save_complete: Callable[[Path, float], None] | None = None
        self._on_save_error: Callable[[str], None] | None = None

        # Map info
        self._map_path: Path | None = None
        self._map_name: str = "untitled"

    @property
    def config(self) -> AutoSaveConfig:
        return self._config

    @config.setter
    def config(self, value: AutoSaveConfig) -> None:
        self._config = value

    @property
    def state(self) -> AutoSaveState:
        """Get current state snapshot."""
        with self._lock:
            return AutoSaveState(
                last_save_time=self._state.last_save_time,
                changes_since_save=self._state.changes_since_save,
                total_autosaves=self._state.total_autosaves,
                last_backup_path=self._state.last_backup_path,
                is_saving=self._state.is_saving,
            )

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def set_save_callback(self, callback: Callable[[Path], bool]) -> None:
        """Set the function that performs the actual save.

        Args:
            callback: Function that takes path and returns True on success.
        """
        self._save_callback = callback

    def set_map_info(self, path: Path | None, name: str = "untitled") -> None:
        """Set current map information.

        Args:
            path: Path to the map file (or None if unsaved).
            name: Display name for the map.
        """
        self._map_path = path
        self._map_name = str(name or "untitled")

    def notify_change(self, count: int = 1) -> None:
        """Notify that the map has been modified.

        Args:
            count: Number of changes (default 1).
        """
        with self._lock:
            self._state.changes_since_save += max(1, int(count))

    def reset_changes(self) -> None:
        """Reset the change counter (e.g., after manual save)."""
        with self._lock:
            self._state.changes_since_save = 0

    def start(self) -> bool:
        """Start the autosave background thread.

        Returns:
            True if started, False if already running or disabled.
        """
        if not self._config.enabled:
            logger.info("AutoSave disabled in config")
            return False

        if self.is_running:
            logger.debug("AutoSave already running")
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="AutoSaveThread",
            daemon=True,
        )
        self._thread.start()

        logger.info(
            "AutoSave started (interval=%ds, max_backups=%d)",
            self._config.interval_seconds,
            self._config.max_backups,
        )
        return True

    def stop(self) -> None:
        """Stop the autosave thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

        logger.info("AutoSave stopped")

    def force_save(self) -> bool:
        """Force an immediate autosave.

        Returns:
            True if save succeeded.
        """
        return self._do_autosave()

    def _run_loop(self) -> None:
        """Background thread main loop."""
        logger.debug("AutoSave loop started")

        while not self._stop_event.is_set():
            # Sleep in small increments for responsive shutdown
            elapsed = 0.0
            while elapsed < self._config.interval_seconds:
                if self._stop_event.wait(timeout=1.0):
                    return
                elapsed += 1.0

            # Check if we should save
            with self._lock:
                changes = self._state.changes_since_save
                is_saving = self._state.is_saving

            if is_saving:
                continue

            if changes >= self._config.min_changes:
                self._do_autosave()

        logger.debug("AutoSave loop ended")

    def _do_autosave(self) -> bool:
        """Perform the autosave operation.

        Returns:
            True if successful.
        """
        if self._save_callback is None:
            logger.warning("AutoSave: No save callback configured")
            return False

        with self._lock:
            if self._state.is_saving:
                return False
            self._state.is_saving = True

        start_time = time.perf_counter()
        backup_path: Path | None = None
        success = False

        try:
            # Notify start
            if self._on_save_start:
                try:
                    self._on_save_start()
                except Exception:
                    pass

            # Generate backup path
            backup_path = self._generate_backup_path()

            # Ensure directory exists
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Perform save
            logger.info("AutoSave: Saving to %s", backup_path)
            success = self._save_callback(backup_path)

            if success:
                elapsed = time.perf_counter() - start_time

                with self._lock:
                    self._state.last_save_time = time.time()
                    self._state.changes_since_save = 0
                    self._state.total_autosaves += 1
                    self._state.last_backup_path = backup_path

                # Cleanup old backups
                self._cleanup_old_backups()

                logger.info("AutoSave complete in %.2fs", elapsed)

                if self._on_save_complete:
                    try:
                        self._on_save_complete(backup_path, elapsed)
                    except Exception:
                        pass
            else:
                raise RuntimeError("Save callback returned False")

        except Exception as e:
            logger.error("AutoSave failed: %s", e)

            if self._on_save_error:
                try:
                    self._on_save_error(str(e))
                except Exception:
                    pass

        finally:
            with self._lock:
                self._state.is_saving = False

        return success

    def _generate_backup_path(self) -> Path:
        """Generate a timestamped backup file path.

        Returns:
            Path for the backup file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Base name from map
        base_name = self._map_name.replace(" ", "_")
        if not base_name or base_name == "untitled":
            base_name = "map"

        # Extension
        ext = ".otbm.gz" if self._config.compress else ".otbm"

        # Filename
        filename = f"{base_name}_autosave_{timestamp}{ext}"

        # Directory
        if self._config.backup_dir:
            backup_dir = self._config.backup_dir
        elif self._map_path:
            backup_dir = self._map_path.parent / "autosave"
        else:
            backup_dir = Path.home() / ".py_rme_canary" / "autosave"

        return backup_dir / filename

    def _cleanup_old_backups(self) -> int:
        """Remove old backup files exceeding max_backups.

        Returns:
            Number of files deleted.
        """
        if self._config.max_backups <= 0:
            return 0

        # Find backup directory
        if self._config.backup_dir:
            backup_dir = self._config.backup_dir
        elif self._map_path:
            backup_dir = self._map_path.parent / "autosave"
        else:
            backup_dir = Path.home() / ".py_rme_canary" / "autosave"

        if not backup_dir.exists():
            return 0

        # Find all autosave files
        pattern = f"{self._map_name.replace(' ', '_')}_autosave_*"
        backups = sorted(backup_dir.glob(pattern), key=lambda p: p.stat().st_mtime)

        # Delete oldest files
        deleted = 0
        while len(backups) > self._config.max_backups:
            oldest = backups.pop(0)
            try:
                oldest.unlink()
                deleted += 1
                logger.debug("Deleted old backup: %s", oldest.name)
            except Exception as e:
                logger.warning("Failed to delete old backup %s: %s", oldest, e)

        return deleted

    def get_backup_list(self) -> list[tuple[Path, float, int]]:
        """Get list of available backups.

        Returns:
            List of (path, timestamp, size_bytes) tuples, newest first.
        """
        # Find backup directory
        if self._config.backup_dir:
            backup_dir = self._config.backup_dir
        elif self._map_path:
            backup_dir = self._map_path.parent / "autosave"
        else:
            backup_dir = Path.home() / ".py_rme_canary" / "autosave"

        if not backup_dir.exists():
            return []

        backups: list[tuple[Path, float, int]] = []

        for path in backup_dir.glob("*_autosave_*"):
            try:
                stat = path.stat()
                backups.append((path, stat.st_mtime, stat.st_size))
            except Exception:
                pass

        # Sort newest first
        backups.sort(key=lambda x: x[1], reverse=True)
        return backups

    # Callback setters
    def on_save_start(self, callback: Callable[[], None]) -> None:
        """Register callback for save start."""
        self._on_save_start = callback

    def on_save_complete(self, callback: Callable[[Path, float], None]) -> None:
        """Register callback for save completion."""
        self._on_save_complete = callback

    def on_save_error(self, callback: Callable[[str], None]) -> None:
        """Register callback for save errors."""
        self._on_save_error = callback


# Global instance
_autosave_manager: AutoSaveManager | None = None


def get_autosave_manager() -> AutoSaveManager:
    """Get the global autosave manager instance."""
    global _autosave_manager
    if _autosave_manager is None:
        _autosave_manager = AutoSaveManager()
    return _autosave_manager


def reset_autosave_manager() -> None:
    """Reset the global autosave manager (for testing)."""
    global _autosave_manager
    if _autosave_manager is not None:
        _autosave_manager.stop()
    _autosave_manager = None
