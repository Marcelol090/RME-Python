
import sys
from unittest.mock import MagicMock
from PyQt6.QtWidgets import QApplication

# Mocking modules that might be missing or hard to initialize
sys.modules["py_rme_canary.core.data.gamemap"] = MagicMock()
sys.modules["py_rme_canary.core.data.item"] = MagicMock()
sys.modules["py_rme_canary.logic_layer.asset_manager"] = MagicMock()
sys.modules["py_rme_canary.logic_layer.item_type_detector"] = MagicMock()
sys.modules["py_rme_canary.core.io.map_validator"] = MagicMock()

# Ensure we can import FindItemDialog and MapValidatorDialog
# They might import other things at module level

from py_rme_canary.vis_layer.ui.dialogs.find_item_dialog import FindItemDialog
from py_rme_canary.vis_layer.ui.dialogs.map_validator_dialog import MapValidatorDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager

def main():
    app = QApplication(sys.argv)

    # Initialize theme manager
    tm = get_theme_manager()
    print(f"Theme Manager initialized with theme: {tm.current_theme}")

    print("Instantiating FindItemDialog...")
    try:
        dialog1 = FindItemDialog(game_map=MagicMock())
        print("FindItemDialog instantiated successfully.")
    except Exception as e:
        print(f"Failed to instantiate FindItemDialog: {e}")
        import traceback
        traceback.print_exc()

    print("Instantiating MapValidatorDialog...")
    try:
        dialog2 = MapValidatorDialog(map_data=MagicMock())
        print("MapValidatorDialog instantiated successfully.")
    except Exception as e:
        print(f"Failed to instantiate MapValidatorDialog: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
