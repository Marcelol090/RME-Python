"""Tests for SpawnPropertiesWindow."""
from unittest.mock import MagicMock
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton

from py_rme_canary.vis_layer.ui.dialogs.spawn_properties_window import (
    SpawnPropertiesWindow,
)
from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

def test_spawn_properties_window_inheritance(qtbot):
    """Test that SpawnPropertiesWindow inherits from ModernDialog."""
    dialog = SpawnPropertiesWindow()
    qtbot.addWidget(dialog)

    assert isinstance(dialog, ModernDialog)
    assert dialog.windowTitle() == "Edit Spawn"

def test_spawn_properties_window_defaults(qtbot):
    """Test default values."""
    dialog = SpawnPropertiesWindow()
    qtbot.addWidget(dialog)

    props = dialog.get_properties()
    assert props["radius"] == 3
    assert props["max_creatures"] == 4
    assert props["interval"] == 60

def test_spawn_properties_window_with_spawn(qtbot):
    """Test initialization with spawn object."""
    spawn = MagicMock()
    spawn.radius = 5
    spawn.max_creatures = 10
    spawn.interval = 120

    dialog = SpawnPropertiesWindow(spawn=spawn)
    qtbot.addWidget(dialog)

    props = dialog.get_properties()
    assert props["radius"] == 5
    assert props["max_creatures"] == 10
    assert props["interval"] == 120

def test_spawn_properties_window_interaction(qtbot):
    """Test interacting with the dialog."""
    spawn = MagicMock()
    spawn.radius = 3
    spawn.max_creatures = 4
    spawn.interval = 60

    dialog = SpawnPropertiesWindow(spawn=spawn)
    qtbot.addWidget(dialog)
    dialog.show()

    # Change values
    dialog._radius_spin.setValue(7)
    dialog._creatures_spin.setValue(15)

    # Find OK button
    buttons = dialog.footer.findChildren(QPushButton)
    ok_btn = next((b for b in buttons if b.text() == "OK"), None)
    assert ok_btn is not None

    # Click OK
    with qtbot.waitSignal(dialog.properties_changed) as blocker:
        qtbot.mouseClick(ok_btn, Qt.MouseButton.LeftButton)

    # Verify signal data
    data = blocker.args[0]
    assert data["radius"] == 7
    assert data["max_creatures"] == 15

    # Verify spawn object update
    assert spawn.radius == 7
    assert spawn.max_creatures == 15
