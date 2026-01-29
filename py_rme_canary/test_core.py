from core.data.gamemap import GameMap
from core.data.item import Item
from core.data.tile import Tile
from logic_layer.brush_definitions import BrushManager
from logic_layer.editor_session import EditorSession

# Test that we can load brushes and create a map
mgr = BrushManager.from_json_file("data/brushes.json")
print(f"BrushManager loaded: {len(mgr.brushes)} brushes")

gmap = GameMap(width=100, height=100, name="Test")
print(f"GameMap created: {gmap.width}x{gmap.height}")

# Test EditorSession
session = EditorSession(gmap, mgr)
print("EditorSession created")

# Test basic operations
tile = Tile(ground=Item(id=4526))
gmap.set_tile(50, 50, 7, tile)
retrieved = gmap.get_tile(50, 50, 7)
print(f"Tile set/get working: ground_id={retrieved.ground.id if retrieved and retrieved.ground else None}")

print("\nCore functionality is working!")
