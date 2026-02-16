
import sys
from unittest.mock import MagicMock
import pytest
from PyQt6.QtWidgets import QApplication, QPushButton

# Mock dependencies
sys.modules["py_rme_canary.core.data.gamemap"] = MagicMock()
sys.modules["py_rme_canary.core.data.item"] = MagicMock()
sys.modules["py_rme_canary.logic_layer.asset_manager"] = MagicMock()
sys.modules["py_rme_canary.logic_layer.item_type_detector"] = MagicMock()
sys.modules["py_rme_canary.core.io.map_validator"] = MagicMock()

from py_rme_canary.vis_layer.ui.dialogs.find_item_dialog import FindItemDialog
from py_rme_canary.vis_layer.ui.dialogs.map_validator_dialog import MapValidatorDialog
from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

def test_find_item_dialog_inheritance(qapp):
    dialog = FindItemDialog(game_map=MagicMock())
    assert isinstance(dialog, ModernDialog)
    assert dialog.windowTitle() == "Find Items"
    assert hasattr(dialog, "content_layout")

    # Check footer content instead of visibility
    footer_buttons = dialog.footer.findChildren(QPushButton)
    assert len(footer_buttons) >= 2 # Replace All + Close

    # Verify specific buttons
    texts = [btn.text() for btn in footer_buttons]
    assert "Replace All..." in texts
    assert "Close" in texts

def test_map_validator_dialog_inheritance(qapp):
    dialog = MapValidatorDialog(map_data=MagicMock())
    assert isinstance(dialog, ModernDialog)
    assert dialog.windowTitle() == "Map Validator"

    # Check footer content
    footer_buttons = dialog.footer.findChildren(QPushButton)
    assert len(footer_buttons) >= 2 # Validate + Close

    texts = [btn.text() for btn in footer_buttons]
    assert "Validate" in texts
    assert "Close" in texts
