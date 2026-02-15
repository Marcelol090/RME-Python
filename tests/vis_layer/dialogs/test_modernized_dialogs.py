
import sys
from unittest.mock import MagicMock
import pytest
from PyQt6.QtWidgets import QApplication

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
    # Verify content layout is not empty (has widgets)
    assert dialog.content_layout.count() > 0
    # Verify footer is visible (since we added buttons to it)
    assert dialog.footer.isVisible()

def test_map_validator_dialog_inheritance(qapp):
    dialog = MapValidatorDialog(map_data=MagicMock())
    assert isinstance(dialog, ModernDialog)
    assert dialog.windowTitle() == "Map Validator"
    assert hasattr(dialog, "content_layout")
    # Verify content layout is not empty
    assert dialog.content_layout.count() > 0
    # Verify footer is visible
    assert dialog.footer.isVisible()
