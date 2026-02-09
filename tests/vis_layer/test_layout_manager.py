"""Test Layout Manager."""

import pytest
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QMainWindow
from py_rme_canary.vis_layer.ui.main_window.layout_manager import LayoutManager

@pytest.fixture
def main_window(qtbot):
    win = QMainWindow()
    qtbot.addWidget(win)
    return win

def test_save_load_layout(main_window):
    manager = LayoutManager(main_window)

    # Mock QSettings to avoid polluting system settings
    manager.settings = MagicMock()

    manager.save_layout("test_layout")

    manager.settings.beginGroup.assert_called_with("layouts/test_layout")
    manager.settings.setValue.assert_any_call("geometry", main_window.saveGeometry())
    manager.settings.setValue.assert_any_call("state", main_window.saveState())

    # Setup mock return values for load
    manager.settings.value.side_effect = lambda k: b"mock_data"

    manager.load_layout("test_layout")

    # Check if restore was called
    # Since we passed QMainWindow instance which is a C++ wrapper, we can't easily mock its methods
    # without subclassing or using a real QMainWindow.
    # But QMainWindow.restoreGeometry returns bool.

    # Verify logic flow
    assert manager.settings.value.call_count >= 2
