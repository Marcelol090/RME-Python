from __future__ import annotations

from py_rme_canary.vis_layer.preview.preview_renderer import IngameRenderer, PreviewViewport


def test_world_to_screen() -> None:
    renderer = IngameRenderer(
        sprite_provider=None,
        appearance_index=None,
        legacy_items=None,
        items_xml=None,
    )
    viewport = PreviewViewport(origin_x=10, origin_y=20, z=7, tile_px=32, tiles_wide=1, tiles_high=1)
    assert renderer._world_to_screen(11, 21, viewport) == (32, 32)
