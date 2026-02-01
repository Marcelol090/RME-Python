from PyQt6.QtWidgets import QApplication
from py_rme_canary.vis_layer.ui.main_window.dialogs import FindEntityDialog

def test_find_entity_dialog_initial_tab(qtbot):
    # Case 1: Default (should be Item or first tab)
    dlg_default = FindEntityDialog(title="Find Default")
    qtbot.addWidget(dlg_default)
    assert dlg_default._tabs.currentIndex() == 0, "Default tab should be index 0 (Item)"

    # Case 2: Explicit 'item'
    dlg_item = FindEntityDialog(title="Find Item", initial_mode="item")
    qtbot.addWidget(dlg_item)
    assert dlg_item._tabs.currentIndex() == 0, "Item mode should select index 0"

    # Case 3: Explicit 'creature'
    dlg_creature = FindEntityDialog(title="Find Creature", initial_mode="creature")
    qtbot.addWidget(dlg_creature)
    assert dlg_creature._tabs.currentIndex() == 1, "Creature mode should select index 1"

    # Case 4: Explicit 'house'
    dlg_house = FindEntityDialog(title="Find House", initial_mode="house")
    qtbot.addWidget(dlg_house)
    assert dlg_house._tabs.currentIndex() == 2, "House mode should select index 2"
