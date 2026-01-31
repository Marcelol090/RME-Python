"""Example script to demonstrate Browse Tile Dialog.

This shows how to integrate the Browse Tile Dialog into the main editor.
"""

import sys

from PyQt6.QtWidgets import QApplication

from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.vis_layer.ui.dialogs.browse_tile_dialog import BrowseTileDialog


def test_browse_tile_dialog():
    """Test the Browse Tile Dialog with sample data."""
    app = QApplication(sys.argv)

    # Create a sample tile with multiple items
    tile = Tile(x=1024, y=1024, z=7)

    # Add ground
    tile.ground = Item(id=102)  # Grass

    # Add items
    tree = Item(id=2700)  # Tree
    stone = Item(id=1285)  # Stone

    torch = Item(id=2050)  # Torch
    torch.action_id = 1001

    container = Item(id=1987)  # Container
    container.unique_id = 5000
    container.text = "Magic Chest"

    tile.items = [tree, stone, torch, container]

    # Show dialog
    dialog = BrowseTileDialog(
        tile=tile,
        position=(1024, 1024, 7),
        asset_manager=None,  # AssetManager optional for testing
    )

    result = dialog.exec()

    if result:
        # User clicked OK - get modified items
        ground, items = dialog.get_modified_items()
        print("Modified tile:")
        print(f"  Ground: {ground.id if ground else 'None'}")
        print(f"  Items ({len(items)}):")
        for i, item in enumerate(items):
            print(f"    {i}: ID {item.id} - AID:{item.action_id or 0}, UID:{item.unique_id or 0}")
    else:
        print("User cancelled")

    app.quit()


def integration_example_with_editor_session():
    """Example of how to integrate Browse Tile with EditorSession.

    This is pseudocode showing the integration pattern.
    """
    # In the actual editor, you would:

    # 1. Add callback to context menu
    def on_browse_tile():
        # Get current tile from click position
        tile = editor_session.get_tile_at(click_pos)
        if not tile:
            return

        # Open dialog
        dialog = BrowseTileDialog(tile=tile, position=click_pos, asset_manager=editor.asset_manager, parent=editor)

        if dialog.exec():
            # Apply changes via undoable action
            ground, items = dialog.get_modified_items()

            action = ModifyTileItemsAction(position=click_pos, new_ground=ground, new_items=items)

            editor_session.execute_action(action)

    # 2. RegisterCallback
    context_menu.set_callbacks(
        {
            # ... other callbacks ...
            "browse_tile": on_browse_tile,
        }
    )


if __name__ == "__main__":
    test_browse_tile_dialog()
