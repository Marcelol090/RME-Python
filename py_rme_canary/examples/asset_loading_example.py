"""Example: Complete asset loading workflow.

Demonstrates loading all assets (SPR/DAT, items.otb, items.xml) and using
them in the UI to display item names and sprite previews.
"""

from pathlib import Path

from py_rme_canary.logic_layer.asset_manager import AssetManager


def load_all_assets_example():
    """Example of loading all asset types."""

    # Get AssetManager instance
    asset_mgr = AssetManager.instance()

    # === Step 1: Load Sprites (SPR/DAT or appearances.xml) ===
    # This is the existing functionality
    assets_path = Path("C:/Tibia/assets")  # Path to client assets
    success = asset_mgr.load_assets(assets_path)

    if not success:
        print("❌ Failed to load sprites")
        return

    print("✅ Sprites loaded successfully")

    # === Step 2: Load items.otb (Server/Client ID mapping) ===
    otb_path = Path("data/1310/items.otb")  # Tibia 13.10
    success = asset_mgr.load_items_otb(otb_path)

    if success:
        print("✅ items.otb loaded - ID mapping ready")
    else:
        print("⚠️  items.otb not loaded - using 1:1 ID mapping")

    # === Step 3: Load items.xml (Item names and metadata) ===
    xml_path = Path("data/1310/items.xml")
    success = asset_mgr.load_items_xml(xml_path)

    if success:
        print("✅ items.xml loaded - Item names available")
    else:
        print("⚠️  items.xml not loaded - using generic names")

    # === Step 4: Use assets ===
    print("\n📦 Testing asset access:")

    # Get item name
    torch_id = 2050
    name = asset_mgr.get_item_name(torch_id)
    print(f"  Item #{torch_id}: {name}")

    # Get full metadata
    metadata = asset_mgr.get_item_metadata(torch_id)
    if metadata:
        print(f"    Stackable: {metadata.stackable}")
        print(f"    Can write text: {metadata.can_write_text}")

    # Get sprite
    sprite = asset_mgr.get_sprite(torch_id)
    if sprite:
        print(f"    Sprite: {sprite.width()}x{sprite.height()} pixels")
    else:
        print("    ⚠️  No sprite available")


def ui_integration_example():
    """Example of using assets in UI components."""

    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QListWidgetItem

    asset_mgr = AssetManager.instance()

    # === Browse Tile Integration ===
    # (In browse_tile_dialog.py)

    def add_item_to_list(list_widget, item_id):
        """Add item with sprite preview and name."""
        # Create list item
        list_item = QListWidgetItem()

        # Set text with name
        name = asset_mgr.get_item_name(item_id)
        list_item.setText(f"{name} (#{item_id})")

        # Add sprite icon
        pixmap = asset_mgr.get_sprite(item_id)
        if pixmap:
            icon = QIcon(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio))
            list_item.setIcon(icon)

        list_widget.addItem(list_item)
        print(f"Added: {name}")

    # === Find Items Integration ===
    # (In find_item_dialog.py)

    def search_by_name(search_term):
        """Search items by name."""
        results = []

        # Get items.xml
        if asset_mgr._items_xml:
            # Search in items.xml
            for server_id in asset_mgr._items_xml.items_by_server_id:
                item_type = asset_mgr._items_xml.get(server_id)
                if item_type and search_term.lower() in item_type.name.lower():
                    results.append(server_id)

        print(f"Found {len(results)} items matching '{search_term}'")
        return results

    # === Context Menu Integration ===
    # (In context_menus.py)

    def build_item_menu(item_id):
        """Build context menu with item name."""
        name = asset_mgr.get_item_name(item_id)

        print(f"Context Menu for: {name} (#{item_id})")
        print("  • Properties")
        print("  • Copy Server ID")
        print("  • Browse Tile")

        # Add sprite to menu header
        sprite = asset_mgr.get_sprite(item_id)
        if sprite:
            print(f"  Icon: {sprite.width()}x{sprite.height()} px")


def complete_workflow():
    """Complete workflow demonstration."""
    print("=" * 60)
    print("🎨 Complete Asset Loading Workflow")
    print("=" * 60)

    # 1. Load all assets
    print("\n1️⃣  Loading assets...")
    load_all_assets_example()

    # 2. Show UI integration examples
    print("\n2️⃣  UI Integration Examples:")
    ui_integration_example()

    print("\n" + "=" * 60)
    print("✅ Asset Loading System Ready!")
    print("=" * 60)
    print("\n💡 Next Steps:")
    print("  1. Integrate into Browse Tile Dialog")
    print("  2. Add name search to Find Items Dialog")
    print("  3. Show item names in Context Menus")


if __name__ == "__main__":
    complete_workflow()
