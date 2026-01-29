from __future__ import annotations

from io import BytesIO
from pathlib import Path

from py_rme_canary.core.constants import NODE_END
from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.database.id_mapper import IdMapper
from py_rme_canary.core.io.otbm.loader import OTBMLoader
from py_rme_canary.core.io.otbm.saver import serialize
from py_rme_canary.core.io.otbm.item_parser import ItemParser
from py_rme_canary.core.io.otbm.streaming import EscapedPayloadReader


def test_item_parser_clientid_mapping() -> None:
    id_mapper = IdMapper(client_to_server={200: 100}, server_to_client={100: 200})
    payload = BytesIO((200).to_bytes(2, "little") + bytes([NODE_END]))
    parser = ItemParser(items_db=None, id_mapper=id_mapper, otbm_version=5)

    item = parser.parse_item_payload(EscapedPayloadReader(payload))
    assert item.id == 100
    assert item.client_id == 200


def test_serialize_and_load_clientid_map(tmp_path: Path) -> None:
    id_mapper = IdMapper(client_to_server={200: 100}, server_to_client={100: 200})

    header = MapHeader(otbm_version=5, width=256, height=256)
    game_map = GameMap(header=header)
    tile = Tile(x=100, y=100, z=7, ground=Item(id=100))
    game_map.set_tile(tile)

    data = serialize(game_map, id_mapper=id_mapper)
    path = tmp_path / "clientid_map.otbm"
    path.write_bytes(data)

    loader = OTBMLoader(items_db=None, id_mapper=id_mapper)
    loaded = loader.load(str(path))

    loaded_tile = loaded.get_tile(100, 100, 7)
    assert loaded_tile is not None
    assert loaded_tile.ground is not None
    assert loaded_tile.ground.id == 100
    assert loaded_tile.ground.client_id == 200
