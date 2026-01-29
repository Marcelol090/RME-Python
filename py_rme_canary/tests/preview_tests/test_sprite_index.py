from __future__ import annotations

from py_rme_canary.logic_layer.sprite_system.legacy_dat import LegacyItemSpriteInfo


def test_sprite_index_order() -> None:
    info = LegacyItemSpriteInfo(
        item_id=100,
        sprite_ids=(1, 2, 3, 4),
        width=2,
        height=2,
        layers=1,
        pattern_x=1,
        pattern_y=1,
        pattern_z=1,
        frames=1,
    )

    assert info.sprite_id_at(0, 0, 0, 0, 0, 0, 0) == 1
    assert info.sprite_id_at(1, 0, 0, 0, 0, 0, 0) == 2
    assert info.sprite_id_at(0, 1, 0, 0, 0, 0, 0) == 3
    assert info.sprite_id_at(1, 1, 0, 0, 0, 0, 0) == 4
