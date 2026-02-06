from typing import TYPE_CHECKING

from py_rme_canary.vis_layer.renderer.drawers.base_drawer import Drawer

if TYPE_CHECKING:
    from py_rme_canary.core.data.tile import Tile
    from py_rme_canary.vis_layer.renderer.map_drawer import MapDrawer, RenderBackend


class CreatureDrawer(Drawer):
    """Handles drawing creatures, spawns, and name overlays."""

    def draw(
        self, drawer: "MapDrawer", backend: "RenderBackend", tile: "Tile", screen_x: int, screen_y: int, size: int
    ) -> None:
        # Spawn/creature indicators
        if (drawer.options.show_spawns_monster or drawer.options.show_monsters) and tile.spawn_monster is not None:
            self._draw_spawn_indicator(backend, screen_x, screen_y, size, kind="spawn_monster")
        if (drawer.options.show_spawns_npc or drawer.options.show_npcs) and tile.spawn_npc is not None:
            self._draw_spawn_indicator(backend, screen_x, screen_y, size, kind="spawn_npc")

        # Creature name overlays
        if not drawer.is_minimap_mode():
            self._draw_creature_names(drawer, backend, tile, screen_x, screen_y, size)

    def _draw_spawn_indicator(self, backend: "RenderBackend", x: int, y: int, size: int, *, kind: str) -> None:
        """Draw a spawn/creature marker; falls back to a colored rect when icons are missing."""
        indicator_key = str(kind)
        icon_size = int(max(10, min(32, size)))
        # Try indicator icon first.
        backend.draw_indicator_icon(x, y, indicator_key, icon_size)
        # Fallback overlay rectangle for visibility.
        if indicator_key == "spawn_monster":
            backend.draw_selection_rect(x, y, size, size, 200, 60, 60, 180)
        else:
            backend.draw_selection_rect(x, y, size, size, 60, 120, 220, 180)

    def _draw_creature_names(
        self,
        drawer: "MapDrawer",
        backend: "RenderBackend",
        tile: "Tile",
        screen_x: int,
        screen_y: int,
        size: int,
    ) -> None:
        """Draw monster/NPC names on top of the tile."""
        if int(size) < 16:
            return

        labels: list[tuple[str, str]] = []

        if drawer.options.show_monsters and getattr(tile, "monsters", None):
            # MapDrawer has _format_creature_names logic, we should move it here or utility
            names = [getattr(m, "name", "") for m in tile.monsters]
            label = self._format_creature_names(names)
            if label:
                labels.append(("monster", label))

        npc = getattr(tile, "npc", None)
        if drawer.options.show_npcs and npc is not None:
            npc_name = str(getattr(npc, "name", "") or "").strip()
            if npc_name:
                labels.append(("npc", npc_name))

        if not labels:
            return

        line_height = max(10, min(14, int(size) // 2))
        base_y = int(screen_y) + line_height
        base_x = int(screen_x) + 2

        for idx, (kind, text) in enumerate(labels):
            if kind == "monster":
                r, g, b, a = 220, 80, 80, 230
            else:
                r, g, b, a = 100, 180, 255, 230
            backend.draw_text(base_x, base_y + (idx * line_height), text, r, g, b, a)

    @staticmethod
    def _format_creature_names(names: list[str]) -> str:
        cleaned = [str(n).strip() for n in names if str(n).strip()]
        if not cleaned:
            return ""
        if len(cleaned) == 1:
            return cleaned[0]
        if len(cleaned) == 2:
            return f"{cleaned[0]}, {cleaned[1]}"
        return f"{cleaned[0]} +{len(cleaned) - 1}"
