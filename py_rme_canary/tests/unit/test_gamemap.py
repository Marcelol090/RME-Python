from py_rme_canary.core.data.gamemap import GameMap, MapHeader


def test_gamemap_initialization():
    header = MapHeader(width=100, height=100, otbm_version=2)
    game_map = GameMap(header=header)
    assert game_map.header.width == 100
    assert game_map.header.height == 100
    assert not game_map.tiles
