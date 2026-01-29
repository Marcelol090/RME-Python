"""Recent Files Manager.

Manages list of recently opened files with persistence.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtCore import QSettings

logger = logging.getLogger(__name__)

# Default max recent files
MAX_RECENT_FILES = 10


class RecentFilesManager:
    """Manages recent files list with persistence.

    Usage:
        manager = RecentFilesManager()
        manager.add_file("/path/to/map.otbm")

        # Get recent files for menu
        files = manager.get_recent_files()
    """

    _instance: "RecentFilesManager | None" = None

    def __init__(
        self,
        config_path: str | None = None,
        max_files: int = MAX_RECENT_FILES
    ) -> None:
        self._max_files = max_files
        self._recent_files: list[str] = []

        # Config file path
        if config_path:
            self._config_path = config_path
        else:
            # Default to user config directory
            config_dir = Path.home() / ".py_rme_canary"
            config_dir.mkdir(exist_ok=True)
            self._config_path = str(config_dir / "recent_files.json")

        self._load()

    @classmethod
    def instance(cls) -> "RecentFilesManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_file(self, path: str) -> None:
        """Add a file to recent files list.

        Also removes duplicates and enforces max limit.

        Args:
            path: Absolute path to the file
        """
        # Normalize path
        path = os.path.abspath(path)

        # Remove if already exists (to move to top)
        if path in self._recent_files:
            self._recent_files.remove(path)

        # Add at beginning
        self._recent_files.insert(0, path)

        # Enforce max limit
        if len(self._recent_files) > self._max_files:
            self._recent_files = self._recent_files[:self._max_files]

        # Save
        self._save()

    def remove_file(self, path: str) -> None:
        """Remove a file from recent list.

        Args:
            path: Path to remove
        """
        path = os.path.abspath(path)
        if path in self._recent_files:
            self._recent_files.remove(path)
            self._save()

    def clear(self) -> None:
        """Clear all recent files."""
        self._recent_files.clear()
        self._save()

    def get_recent_files(self, valid_only: bool = True) -> list[str]:
        """Get list of recent files.

        Args:
            valid_only: If True, filter out files that no longer exist

        Returns:
            List of file paths
        """
        if valid_only:
            # Filter and update list
            valid = [p for p in self._recent_files if os.path.exists(p)]
            if len(valid) != len(self._recent_files):
                self._recent_files = valid
                self._save()
            return valid
        return self._recent_files.copy()

    def get_display_items(self) -> list[tuple[str, str]]:
        """Get recent files with display names.

        Returns:
            List of (display_name, full_path) tuples
        """
        items = []
        for path in self.get_recent_files():
            display = os.path.basename(path)
            items.append((display, path))
        return items

    def _load(self) -> None:
        """Load recent files from config."""
        try:
            if os.path.exists(self._config_path):
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._recent_files = data.get('recent_files', [])[:self._max_files]
        except Exception as e:
            logger.warning(f"Failed to load recent files: {e}")
            self._recent_files = []

    def _save(self) -> None:
        """Save recent files to config."""
        try:
            data = {'recent_files': self._recent_files}
            with open(self._config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save recent files: {e}")


def build_recent_files_menu(
    parent_menu: object,
    on_file_selected: callable
) -> None:
    """Build recent files submenu.

    Args:
        parent_menu: QMenu to add items to
        on_file_selected: Callback when file selected (receives path)
    """
    try:
        from PyQt6.QtGui import QAction
        from PyQt6.QtWidgets import QMenu

        # Clear existing
        if hasattr(parent_menu, 'clear'):
            parent_menu.clear()

        manager = RecentFilesManager.instance()
        items = manager.get_display_items()

        if not items:
            # Add disabled "No recent files" item
            no_files = QAction("No recent files", parent_menu)
            no_files.setEnabled(False)
            parent_menu.addAction(no_files)
            return

        # Add file actions (with index for shortcut)
        for i, (display, path) in enumerate(items):
            # Show index for first 9 files (Ctrl+1 to Ctrl+9)
            if i < 9:
                text = f"&{i+1}. {display}"
            else:
                text = f"    {display}"

            action = QAction(text, parent_menu)
            action.setToolTip(path)
            action.setData(path)
            action.triggered.connect(
                lambda checked, p=path: on_file_selected(p)
            )
            parent_menu.addAction(action)

        # Separator and clear action
        parent_menu.addSeparator()

        clear_action = QAction("Clear Recent Files", parent_menu)
        clear_action.triggered.connect(manager.clear)
        parent_menu.addAction(clear_action)

    except ImportError:
        logger.warning("PyQt6 not available for recent files menu")
