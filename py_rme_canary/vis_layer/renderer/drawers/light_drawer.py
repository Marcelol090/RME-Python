from typing import TYPE_CHECKING

from py_rme_canary.logic_layer.settings.light_settings import LightMode
from py_rme_canary.vis_layer.renderer.drawers.base_drawer import Drawer

if TYPE_CHECKING:
    from py_rme_canary.core.data.tile import Tile
    from py_rme_canary.vis_layer.renderer.map_drawer import MapDrawer, RenderBackend


class LightDrawer(Drawer):
    """Handles drawing lighting effects and overlays."""

    def draw(self, drawer: "MapDrawer", backend: "RenderBackend") -> None:
        """Draw ambient and tile lights."""
        if drawer.game_map is None or not drawer.options.show_lights:
            return

        settings = drawer.options.light_settings
        if not settings.enabled or settings.mode == LightMode.OFF:
            return

        # Ambient Overlay
        ambient_color = settings.ambient_color.to_rgb_tuple()
        ambient_level = settings.ambient_level
        ambient_alpha = max(0, min(200, int((255 - ambient_level) * 0.75)))
        overlay_size = max(drawer.viewport.width_px, drawer.viewport.height_px)

        if ambient_alpha > 0:
            backend.draw_tile_color(
                0, 0, overlay_size, ambient_color[0], ambient_color[1], ambient_color[2], ambient_alpha
            )

        if settings.mode != LightMode.FULL:
            return

        # Tile Lights
        tile_size = max(1, drawer.viewport.tile_px)
        glow_radius = tile_size * 2
        glow_color = self._mix_color(ambient_color, (255, 255, 255), 0.55)

        start_x, start_y = drawer._start_x, drawer._start_y
        end_x, end_y = drawer._end_x, drawer._end_y
        start_z, end_z = drawer._start_z, drawer._end_z

        for z in range(start_z, end_z - 1, -1):
            for y in range(start_y, end_y):
                for x in range(start_x, end_x):
                    strength = self._tile_light_strength(drawer.game_map.get_tile(x, y, z))
                    if strength <= 0:
                        continue

                    glow_alpha = min(220, max(60, int(strength * 0.6)))
                    px = int((x - start_x) * tile_size - glow_radius // 2)
                    py = int((y - start_y) * tile_size - glow_radius // 2)
                    backend.draw_tile_color(
                        px, py, glow_radius, glow_color[0], glow_color[1], glow_color[2], glow_alpha
                    )

                    if drawer.options.show_light_strength:
                        text_x = int((x - start_x) * tile_size + 2)
                        text_y = int((y - start_y) * tile_size + tile_size - 4)
                        backend.draw_text(
                            text_x, text_y, str(strength), glow_color[0], glow_color[1], glow_color[2], 200
                        )

    def _tile_light_strength(self, tile: "Tile | None") -> int:
        """Estimate a normalized light strength for a given tile."""
        if tile is None:
            return 0

        strength = 0
        if tile.ground is not None:
            strength += 20

        strength += min(5, len(tile.items)) * 12

        if tile.spawn_monster is not None or tile.spawn_npc is not None:
            strength += 35

        strength += len(tile.monsters) * 8

        if tile.npc is not None:
            strength += 25

        for item in tile.items:
            for attr in item.attribute_map:
                key = attr.key.lower()
                if "light" in key or "brilho" in key or "luminosity" in key:
                    strength += 40

        return min(255, strength)

    @staticmethod
    def _mix_color(
        base: tuple[int, int, int],
        accent: tuple[int, int, int],
        ratio: float,
    ) -> tuple[int, int, int]:
        ratio = max(0.0, min(1.0, ratio))
        return tuple(int(max(0, min(255, base[i] * (1.0 - ratio) + accent[i] * ratio))) for i in range(3))
