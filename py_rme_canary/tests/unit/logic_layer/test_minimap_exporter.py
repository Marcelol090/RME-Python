
import pytest
from unittest.mock import MagicMock
from py_rme_canary.logic_layer.minimap_exporter import MinimapExporter
from py_rme_canary.core.database.items_xml import ItemsXML

def test_minimap_exporter_init():
    items_db = MagicMock(spec=ItemsXML)
    exporter = MinimapExporter(items_db=items_db)
    assert exporter.items_db is items_db

def test_get_tile_minimap_color_with_attribute():
    # Setup ItemsXML mock
    items_db = MagicMock(spec=ItemsXML)
    mock_item = MagicMock()
    mock_item.attributes = {"minimapColor": "100"}
    items_db.get.return_value = mock_item

    exporter = MinimapExporter(items_db=items_db)

    # Setup Tile mock
    tile = MagicMock()
    tile.ground.server_id = 123

    color = exporter._get_tile_minimap_color(tile)

    items_db.get.assert_called_with(123)
    assert color == 100

def test_get_tile_minimap_color_fallback():
    # Setup ItemsXML mock returning None (item not found)
    items_db = MagicMock(spec=ItemsXML)
    items_db.get.return_value = None

    exporter = MinimapExporter(items_db=items_db)

    # Setup Tile mock (grass id)
    tile = MagicMock()
    tile.ground.server_id = 4526

    color = exporter._get_tile_minimap_color(tile)

    # Expect hardcoded grass color
    assert color == 24

def test_get_tile_minimap_color_no_attribute():
    # Setup ItemsXML mock returning item without minimapColor
    items_db = MagicMock(spec=ItemsXML)
    mock_item = MagicMock()
    mock_item.attributes = {}
    items_db.get.return_value = mock_item

    exporter = MinimapExporter(items_db=items_db)

    # Setup Tile mock (water id)
    tile = MagicMock()
    tile.ground.server_id = 4664

    color = exporter._get_tile_minimap_color(tile)

    # Expect hardcoded water color
    assert color == 20
