"""Example: Context Menu Integration with Action Handlers.

Shows how to wire up ItemContextMenu with ContextMenuActionHandlers
for a fully functional context menu system.
"""

import sys

from PyQt6.QtWidgets import QApplication

from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.context_menu_handlers import ContextMenuActionHandlers
from py_rme_canary.vis_layer.ui.menus.context_menus import ItemContextMenu


def example_item_context_menu():
    """Example: Show context menu for an item with functional handlers."""
    app = QApplication(sys.argv)

    # Create sample tile with door item
    tile = Tile(x=1024, y=1024, z=7)
    tile.ground = Item(id=102)  # Grass

    door = Item(id=1209)  # Closed wooden door
    door.action_id = 1001
    tile.items = [door]

    # Create action handlers
    handlers = ContextMenuActionHandlers(
        editor_session=None,  # Would be actual EditorSession
        canvas=None,  # Would be actual MapCanvas
        palette=None,  # Would be actual BrushPalette
    )

    # Get callbacks for this item
    callbacks = handlers.get_item_context_callbacks(item=door, tile=tile, position=(1024, 1024, 7))

    # Create and setup context menu
    context_menu = ItemContextMenu()
    context_menu.set_callbacks(callbacks)

    # Show menu (would normally be triggered by right-click)
    print("=== Context Menu for Door (ID 1209) ===")
    print("Available actions:")
    print("  ✨ Select Door Brush")
    print("  🚪 Open Door")
    print("  📝 Properties...")
    print("  🔍 Browse Tile...")
    print("  📋 Copy Data")
    print("     └─ Server ID (1209)")
    print("     └─ Item Name")
    print("     └─ Position (1024, 1024, 7)")
    print()

    # Simulate clicking actions
    print("=== Testing Actions ===")

    print("\n1. Copy Server ID:")
    callbacks["copy_server_id"]()

    print("\n2. Copy Position:")
    callbacks["copy_position"]()

    print("\n3. Toggle Door:")
    callbacks["toggle_door"]()
    print(f"   Door is now ID {door.id}")

    print("\n4. Toggle Door again:")
    callbacks["toggle_door"]()
    print(f"   Door is now ID {door.id}")

    print("\n5. Select Brush:")
    callbacks["select_brush"]()

    app.quit()


def example_rotatable_item():
    """Example: Test rotation on a torch."""
    app = QApplication(sys.argv)

    torch = Item(id=2050)  # Torch facing east

    handlers = ContextMenuActionHandlers()

    print("=== Torch Rotation Test ===")
    print(f"Initial ID: {torch.id}")

    for i in range(5):
        handlers.rotate_item(torch)
        print(f"After rotation {i + 1}: {torch.id}")

    app.quit()


def example_teleport_navigation():
    """Example: Navigate to teleport destination."""
    app = QApplication(sys.argv)

    teleport = Item(id=1387)
    # In a real scenario, destination would be loaded from map
    teleport.destination = (2000, 2000, 10)

    handlers = ContextMenuActionHandlers()

    print("=== Teleport Navigation Test ===")
    handlers.goto_teleport_destination(teleport)

    app.quit()


def integration_with_editor():
    """Pseudocode showing full integration with editor.

    This demonstrates how the context menu system would be
    integrated into the actual QtMapEditor.
    """
    # In QtMapEditor.__init__:
    #
    # self.context_handlers = ContextMenuActionHandlers(
    #     editor_session=self.session,
    #     canvas=self.canvas_widget,
    #     palette=self.palette_dock
    # )
    #
    # self.item_context_menu = ItemContextMenu(parent=self)

    # In canvas right-click handler:
    #
    # def on_canvas_right_click(self, pos: QPoint):
    #     # Get tile and item at position
    #     map_pos = canvas.screen_to_map(pos)
    #     tile = self.session.game_map.get_tile(*map_pos)
    #
    #     if not tile:
    #         return
    #
    #     # Get top item
    #     item = tile.get_top_item()
    #
    #     if item:
    #         # Show item context menu
    #         callbacks = self.context_handlers.get_item_context_callbacks(
    #             item=item,
    #             tile=tile,
    #             position=map_pos
    #         )
    #         self.item_context_menu.set_callbacks(callbacks)
    #         self.item_context_menu.show_for_item(item, tile)
    #     else:
    #         # Show tile context menu
    #         # ... (similar pattern)
    pass


if __name__ == "__main__":
    print("=" * 60)
    example_item_context_menu()

    print("\n" + "=" * 60)
    example_rotatable_item()

    print("\n" + "=" * 60)
    example_teleport_navigation()

    print("\n" + "=" * 60)
    print("\nAll examples completed!")
