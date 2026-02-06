from typing import TYPE_CHECKING

from py_rme_canary.vis_layer.renderer.drawers.base_drawer import Drawer

if TYPE_CHECKING:
    from py_rme_canary.core.data.tile import Tile
    from py_rme_canary.vis_layer.renderer.map_drawer import MapDrawer, RenderBackend


class FloorDrawer(Drawer):
    """Handles drawing ground tiles."""

    def draw(
        self, drawer: "MapDrawer", backend: "RenderBackend", tile: "Tile", screen_x: int, screen_y: int, size: int
    ) -> None:
        if tile.ground is not None and drawer.options.show_items:
            backend.draw_tile_sprite(screen_x, screen_y, size, tile.ground.id)
