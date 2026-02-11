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
            draw_id = int(getattr(tile.ground, "id", 0))
            if draw_id <= 0:
                client_id = getattr(tile.ground, "client_id", None)
                with_client = int(client_id) if client_id is not None else 0
                if with_client > 0:
                    # Negative id encodes "raw ClientID" for sprite lookup path.
                    draw_id = -int(with_client)
            if draw_id != 0:
                backend.draw_tile_sprite(screen_x, screen_y, size, draw_id)
