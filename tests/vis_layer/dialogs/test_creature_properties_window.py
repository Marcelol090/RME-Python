"""Tests for CreaturePropertiesWindow."""
import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton

from py_rme_canary.vis_layer.ui.dialogs.creature_properties_window import (
    CreatureData,
    CreaturePropertiesWindow,
    Direction,
)
from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

def test_creature_properties_window_inheritance(qtbot):
    """Test that CreaturePropertiesWindow inherits from ModernDialog."""
    dialog = CreaturePropertiesWindow()
    qtbot.addWidget(dialog)

    assert isinstance(dialog, ModernDialog)
    assert dialog.windowTitle() == "Creature Properties"

def test_creature_properties_window_defaults(qtbot):
    """Test default values."""
    dialog = CreaturePropertiesWindow()
    qtbot.addWidget(dialog)

    assert dialog.get_spawn_time() == 60
    assert dialog.get_direction() == Direction.SOUTH

    data = dialog.get_data()
    assert data.spawn_time == 60
    assert data.direction == Direction.SOUTH

def test_creature_properties_window_custom_data(qtbot):
    """Test initialization with custom data."""
    data = CreatureData(name="Demon", spawn_time=120, direction=Direction.NORTH)
    dialog = CreaturePropertiesWindow(data=data)
    qtbot.addWidget(dialog)

    assert dialog.get_spawn_time() == 120
    assert dialog.get_direction() == Direction.NORTH

    # Check UI elements match
    assert dialog.spawn_time_spin.value() == 120
    assert dialog.direction_combo.currentIndex() == Direction.NORTH

def test_creature_properties_window_interaction(qtbot):
    """Test interacting with the dialog."""
    dialog = CreaturePropertiesWindow()
    qtbot.addWidget(dialog)
    dialog.show()

    # Change values
    dialog.spawn_time_spin.setValue(300)
    dialog.direction_combo.setCurrentIndex(Direction.EAST)

    # Find OK button
    buttons = dialog.footer.findChildren(QPushButton)
    ok_btn = next((b for b in buttons if b.text() == "OK"), None)
    assert ok_btn is not None

    # Click OK
    with qtbot.waitSignal(dialog.properties_changed) as blocker:
        qtbot.mouseClick(ok_btn, Qt.MouseButton.LeftButton)

    # Verify signal data
    data = blocker.args[0]
    assert data.spawn_time == 300
    assert data.direction == Direction.EAST
