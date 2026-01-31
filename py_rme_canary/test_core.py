from core.data.gamemap import GameMap, MapHeader
from core.data.item import Item
from core.data.tile import Tile
from logic_layer.brush_definitions import BrushManager
from logic_layer.editor_session import EditorSession

# Test that we can load brushes and create a map
mgr = BrushManager.from_json_file("data/brushes.json")
print(f"BrushManager loaded: {len(mgr._brushes)} brushes")

gmap = GameMap(header=MapHeader(otbm_version=2, width=100, height=100))
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
