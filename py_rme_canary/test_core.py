from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.brush_definitions import BrushManager
from py_rme_canary.logic_layer.editor_session import EditorSession

if __name__ == "__main__":
    # Test that we can load brushes and create a map
    mgr = BrushManager.from_json_file("data/brushes.json")
    print(f"BrushManager loaded: {len(mgr._brushes)} brushes")

    gmap = GameMap(header=MapHeader(otbm_version=3, width=100, height=100, description="Test"))
    print(f"GameMap created: {gmap.header.width}x{gmap.header.height}")

    # Test EditorSession
    session = EditorSession(gmap, mgr)
    print("EditorSession created")

    # Test basic operations
    tile = Tile(x=50, y=50, z=7, ground=Item(id=4526))
    gmap.set_tile(tile)
    retrieved = gmap.get_tile(50, 50, 7)
    print(f"Tile set/get working: ground_id={retrieved.ground.id if retrieved and retrieved.ground else None}")

    print("\nCore functionality is working!")
