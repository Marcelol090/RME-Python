from typing import TYPE_CHECKING

from py_rme_canary.vis_layer.renderer.drawers.base_drawer import Drawer

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.renderer.map_drawer import MapDrawer, RenderBackend


class GridDrawer(Drawer):
    """Handles drawing the tile grid."""

    def draw(self, drawer: "MapDrawer", backend: "RenderBackend") -> None:
        """Draw the grid using the drawer's viewport state."""
        tile_size = drawer.viewport.tile_px
        grid_color = (58, 58, 58, 255)  # Dark gray

        # Access protected members of MapDrawer - strictly for refactoring parity
        # In a cleaner architecture, these would be public properties of Viewport or similar
        start_y = drawer._start_y
        end_y = drawer._end_y
        start_x = drawer._start_x
        end_x = drawer._end_x

        for y in range(start_y, end_y + 1):
            py = (y - start_y) * tile_size
            for x in range(start_x, end_x + 1):
                px = (x - start_x) * tile_size
                backend.draw_grid_rect(px, py, tile_size, tile_size, *grid_color)
