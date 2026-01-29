"""Pytest configuration for all tests."""

from __future__ import annotations

import importlib.util
import sys

import pytest


def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "gui: marks tests that require GUI (PyQt6)")


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    # Auto-skip GUI tests if running without display
    if sys.platform.startswith("linux") and not hasattr(sys, "ps1"):
        import os

        if "DISPLAY" not in os.environ:
            skip_gui = pytest.mark.skip(reason="No DISPLAY available")
            for item in items:
                if "gui" in item.keywords:
                    item.add_marker(skip_gui)


def _pyqt6_available() -> bool:
    try:
        from PyQt6.QtCore import Qt  # noqa: F401
        from PyQt6.QtWidgets import QApplication  # noqa: F401
    except Exception:
        return False
    return True


def _benchmark_available() -> bool:
    return importlib.util.find_spec("pytest_benchmark") is not None


def pytest_ignore_collect(collection_path, config):
    path_str = str(collection_path).replace("\\", "/")
    if not _pyqt6_available():
        if "/tests/unit/vis_layer/ui/" in path_str:
            return True
    if not _benchmark_available() and "/tests/performance/" in path_str:
        return True
    return False


@pytest.fixture
def mock_game_map():
    """Create a mock game map for testing."""
    from unittest.mock import MagicMock

    mock = MagicMock()
    mock.header.width = 256
    mock.header.height = 256
    mock.tiles = {}
    mock.houses = {}
    mock.waypoints = {}
    mock.monster_spawns = []
    mock.npc_spawns = []
    mock.zones = []
    mock.towns = []

    return mock


@pytest.fixture
def mock_tile():
    """Create a mock tile for testing."""
    from unittest.mock import MagicMock

    tile = MagicMock()
    tile.x = 100
    tile.y = 100
    tile.z = 7
    tile.ground = MagicMock()
    tile.ground.id = 100
    tile.items = []

    return tile


@pytest.fixture
def mock_brush():
    """Create a mock brush for testing."""
    from unittest.mock import MagicMock

    brush = MagicMock()
    brush.name = "TestBrush"
    brush.size = 1
    brush.shape = "square"
    brush.look_id = 100

    return brush
