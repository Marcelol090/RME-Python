import pytest
from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.brush_definitions import BrushManager
from py_rme_canary.logic_layer.session.editor import EditorSession

def test_smoke_core_functionality():
    # Test that we can load brushes
    try:
        mgr = BrushManager.from_json_file("data/brushes.json")
    except FileNotFoundError:
        pytest.skip("data/brushes.json not found")

    assert hasattr(mgr, '_brushes')
    assert len(mgr._brushes) > 0, "Brushes should be loaded"

    # Create MapHeader and GameMap
    header = MapHeader(otbm_version=3, width=100, height=100, description="Test Map")
    gmap = GameMap(header=header)

    assert gmap.header.width == 100
    assert gmap.header.height == 100

    # Test EditorSession
    session = EditorSession(gmap, mgr)
    assert session is not None

    # Test basic operations
    # Use set_tile_at which handles coordinates better if signature matches
    tile = Tile(x=50, y=50, z=7, ground=Item(id=4526))
    gmap.set_tile(tile)

    retrieved = gmap.get_tile(50, 50, 7)

    assert retrieved is not None
    assert retrieved.ground is not None
    assert retrieved.ground.id == 4526
