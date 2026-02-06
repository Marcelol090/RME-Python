from __future__ import annotations

import contextlib
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from py_rme_canary.core.database.items_xml import ItemsXML
from py_rme_canary.core.memory_guard import MemoryGuard, MemoryGuardError, default_memory_guard
from py_rme_canary.logic_layer.sprite_system.legacy_dat import LegacyItemSpriteInfo

if TYPE_CHECKING:
    import pygame


@dataclass(frozen=True, slots=True)
class PreviewViewport:
    origin_x: int
    origin_y: int
    z: int
    tile_px: int
    tiles_wide: int
    tiles_high: int


@dataclass(frozen=True, slots=True)
class PreviewItem:
    server_id: int
    client_id: int
    count: int | None
    stackable: bool


@dataclass(frozen=True, slots=True)
class TileSnapshot:
    x: int
    y: int
    z: int
    ground: PreviewItem | None
    items: tuple[PreviewItem, ...]
    light_strength: int = 0


@dataclass(frozen=True, slots=True)
class PreviewLighting:
    enabled: bool = False
    mode: str = "off"
    ambient_level: int = 255
    ambient_color: tuple[int, int, int] = (255, 255, 255)
    show_strength: bool = False


@dataclass(frozen=True, slots=True)
class PreviewSnapshot:
    viewport: PreviewViewport
    tiles: tuple[TileSnapshot, ...]
    time_ms: int
    show_grid: bool = False
    lighting: PreviewLighting = field(default_factory=PreviewLighting)


class SpriteSurfaceCache:
    def __init__(self, sprite_provider, *, memory_guard: MemoryGuard | None = None) -> None:
        self._sprite_provider = sprite_provider
        self._cache: OrderedDict[int, pygame.Surface] = OrderedDict()
        self._memory_guard = memory_guard or default_memory_guard()

    def get_surface(self, sprite_id: int, *, placeholder_size: int = 32) -> pygame.Surface:
        import pygame

        sid = int(sprite_id)
        cached = self._cache.get(sid)
        if cached is not None:
            with contextlib.suppress(Exception):
                self._cache.move_to_end(sid)
            return cached

        if self._sprite_provider is None:
            return self._placeholder_surface(placeholder_size)

        try:
            width, height, bgra = self._sprite_provider.get_sprite_rgba(sid)
            surf = pygame.image.frombuffer(bgra, (int(width), int(height)), "BGRA").copy()
            surf = surf.convert_alpha()
        except Exception:
            return self._placeholder_surface(placeholder_size)

        self._cache[sid] = surf
        with contextlib.suppress(Exception):
            self._cache.move_to_end(sid)

        try:
            self._memory_guard.check_cache_entries(
                kind="sprite_cache",
                entries=len(self._cache),
                stage="preview_surface_cache",
            )
        except MemoryGuardError:
            target = int(self._memory_guard.config.evict_to_sprite_cache_entries)
            while len(self._cache) > max(0, target):
                self._cache.popitem(last=False)
        return surf

    def _placeholder_surface(self, size: int) -> pygame.Surface:
        import pygame

        surf = pygame.Surface((int(size), int(size)), pygame.SRCALPHA)
        surf.fill((200, 0, 200, 160))
        return surf


class IngameRenderer:
    def __init__(
        self,
        *,
        sprite_provider,
        appearance_index: Any,
        legacy_items: dict[int, LegacyItemSpriteInfo] | None,
        items_xml: ItemsXML | None,
        tile_px: int = 32,
        memory_guard: MemoryGuard | None = None,
    ) -> None:
        self._tile_px = int(tile_px)
        self._appearance_index = appearance_index
        self._legacy_items = legacy_items or {}
        self._items_xml = items_xml
        self._surface_cache = SpriteSurfaceCache(sprite_provider, memory_guard=memory_guard)
        self._font = None
        self._grid_cache_key: tuple[int, int, int] | None = None
        self._grid_cache_surface = None
        self._show_light_strength = False

    def render(self, screen: pygame.Surface, snapshot: PreviewSnapshot) -> None:
        import pygame

        if snapshot is None:
            return
        viewport = snapshot.viewport
        tile_px = int(viewport.tile_px)
        if tile_px <= 0:
            return
        self._show_light_strength = bool(getattr(snapshot.lighting, "show_strength", False))

        if self._font is None:
            self._font = pygame.font.SysFont("Arial", 12, bold=True)

        world_w = int(viewport.tiles_wide) * tile_px
        world_h = int(viewport.tiles_high) * tile_px
        world_surface = pygame.Surface((max(1, world_w), max(1, world_h)), pygame.SRCALPHA)
        world_surface.fill((0, 0, 0, 255))

        tile_lookup = {(t.x, t.y): t for t in snapshot.tiles}

        for ty in range(int(viewport.origin_y), int(viewport.origin_y) + int(viewport.tiles_high)):
            for tx in range(int(viewport.origin_x), int(viewport.origin_x) + int(viewport.tiles_wide)):
                tile = tile_lookup.get((tx, ty))
                if tile is None:
                    continue
                screen_x, screen_y = self._world_to_screen(tx, ty, viewport)
                self._draw_tile(world_surface, tile, screen_x, screen_y, time_ms=int(snapshot.time_ms))

        if bool(getattr(snapshot, "show_grid", False)):
            grid_surface = self._get_grid_surface(world_w, world_h, tile_px)
            if grid_surface is not None:
                world_surface.blit(grid_surface, (0, 0))

        self._apply_lighting(world_surface, snapshot, tile_px)

        if world_surface.get_size() != screen.get_size():
            scaled = pygame.transform.smoothscale(world_surface, screen.get_size())
            screen.blit(scaled, (0, 0))
        else:
            screen.blit(world_surface, (0, 0))

    def _draw_tile(
        self, surface: pygame.Surface, tile: TileSnapshot, screen_x: int, screen_y: int, *, time_ms: int
    ) -> None:
        ground = []
        bottom = []
        top = []

        if tile.ground is not None:
            ground.append(tile.ground)

        for item in tile.items:
            layer = self._classify_item(item)
            if layer == "top":
                top.append(item)
            elif layer == "ground":
                ground.append(item)
            else:
                bottom.append(item)

        for item in ground + bottom + top:
            self._draw_item(surface, tile, item, screen_x, screen_y, time_ms=time_ms)
        self._draw_light_strength(surface, tile, screen_x, screen_y)

    def _world_to_screen(self, x: int, y: int, viewport: PreviewViewport) -> tuple[int, int]:
        tile_px = int(viewport.tile_px)
        screen_x = (int(x) - int(viewport.origin_x)) * tile_px
        screen_y = (int(y) - int(viewport.origin_y)) * tile_px
        return screen_x, screen_y

    def _classify_item(self, item: PreviewItem) -> str:
        legacy = self._legacy_items.get(int(item.client_id))
        if legacy is not None:
            if legacy.is_ground:
                return "ground"
            if legacy.is_top:
                return "top"
        if self._items_xml is not None:
            meta = self._items_xml.get(int(item.server_id))
            if meta is not None and meta.is_ground():
                return "ground"
        return "bottom"

    def _draw_item(
        self,
        surface: pygame.Surface,
        tile: TileSnapshot,
        item: PreviewItem,
        screen_x: int,
        screen_y: int,
        *,
        time_ms: int,
    ) -> None:
        legacy = self._legacy_items.get(int(item.client_id))
        if legacy is not None:
            self._draw_legacy_sprite(surface, tile, item, legacy, screen_x, screen_y, time_ms=time_ms)
            return
        sprite_info = self._appearance_index.object_info.get(int(item.client_id)) if self._appearance_index else None
        if sprite_info is not None:
            self._draw_modern_sprite(surface, tile, item, sprite_info, screen_x, screen_y, time_ms=time_ms)
            return
        sprite = self._surface_cache.get_surface(int(item.client_id), placeholder_size=self._tile_px)
        surface.blit(sprite, (screen_x, screen_y))
        self._draw_stack_count(surface, item, screen_x, screen_y)

    def _draw_legacy_sprite(
        self,
        surface: pygame.Surface,
        tile: TileSnapshot,
        item: PreviewItem,
        info: LegacyItemSpriteInfo,
        screen_x: int,
        screen_y: int,
        *,
        time_ms: int,
    ) -> None:
        if info.animation is not None:
            frame = info.animation.frame_index_for_time(time_ms)
        else:
            frame = 0 if info.frames <= 1 else (int(time_ms) // 200) % int(info.frames)

        pattern_x = 0 if info.pattern_x <= 1 else int(tile.x) % int(info.pattern_x)
        pattern_y = 0 if info.pattern_y <= 1 else int(tile.y) % int(info.pattern_y)
        pattern_z = 0

        base_x = int(screen_x) - int(info.draw_offset_x) - int(info.draw_height)
        base_y = int(screen_y) - int(info.draw_offset_y) - int(info.draw_height)

        for cx in range(int(info.width)):
            for cy in range(int(info.height)):
                for layer in range(int(info.layers)):
                    sprite_id = info.sprite_id_at(cx, cy, layer, pattern_x, pattern_y, pattern_z, frame)
                    if sprite_id is None:
                        continue
                    sprite = self._surface_cache.get_surface(int(sprite_id), placeholder_size=self._tile_px)
                    draw_x = base_x - cx * int(self._tile_px)
                    draw_y = base_y - cy * int(self._tile_px)
                    surface.blit(sprite, (draw_x, draw_y))

        self._draw_stack_count(surface, item, screen_x, screen_y)

    def _draw_modern_sprite(
        self,
        surface: pygame.Surface,
        tile: TileSnapshot,
        item: PreviewItem,
        info: Any,
        screen_x: int,
        screen_y: int,
        *,
        time_ms: int,
    ) -> None:
        frame = info.phase_index_for_time(time_ms, seed=(int(tile.x) << 16) ^ int(tile.y))
        pattern_x = 0 if info.pattern_width <= 1 else int(tile.x) % int(info.pattern_width)
        pattern_y = 0 if info.pattern_height <= 1 else int(tile.y) % int(info.pattern_height)
        pattern_z = 0
        layers = max(1, int(info.layers))
        for layer in range(layers):
            idx = (
                ((int(frame) * int(info.pattern_depth) + int(pattern_z)) * int(info.pattern_height) + int(pattern_y))
                * int(info.pattern_width)
                + int(pattern_x)
            ) * layers + int(layer)
            if not info.sprite_ids:
                continue
            if idx >= len(info.sprite_ids):
                idx = idx % len(info.sprite_ids)
            sprite_id = int(info.sprite_ids[idx])
            sprite = self._surface_cache.get_surface(sprite_id, placeholder_size=self._tile_px)
            surface.blit(sprite, (screen_x, screen_y))

        self._draw_stack_count(surface, item, screen_x, screen_y)

    def _draw_stack_count(self, surface: pygame.Surface, item: PreviewItem, screen_x: int, screen_y: int) -> None:
        if not item.stackable:
            return
        count = int(item.count or 0)
        if count <= 1:
            return
        if self._font is None:
            return
        shadow = self._font.render(str(count), True, (0, 0, 0))
        text = self._font.render(str(count), True, (255, 255, 255))
        surface.blit(shadow, (screen_x + 3, screen_y + 3))
        surface.blit(text, (screen_x + 2, screen_y + 2))

    def _draw_light_strength(self, surface: pygame.Surface, tile: TileSnapshot, screen_x: int, screen_y: int) -> None:
        if not self._show_light_strength:
            return
        if self._font is None:
            return
        strength = int(getattr(tile, "light_strength", 0))
        if strength <= 0:
            return
        label = self._font.render(str(strength), True, (255, 255, 200))
        shadow = self._font.render(str(strength), True, (0, 0, 0))
        surface.blit(shadow, (screen_x + 3, screen_y + 15))
        surface.blit(label, (screen_x + 2, screen_y + 14))

    def _get_grid_surface(self, width: int, height: int, tile_px: int):
        import pygame

        key = (int(width), int(height), int(tile_px))
        if self._grid_cache_key == key and self._grid_cache_surface is not None:
            return self._grid_cache_surface
        if int(tile_px) <= 0:
            return None

        grid = pygame.Surface((max(1, int(width)), max(1, int(height))), pygame.SRCALPHA)
        color = (255, 255, 255, 28)

        for x in range(0, int(width) + 1, int(tile_px)):
            pygame.draw.line(grid, color, (x, 0), (x, int(height)))
        for y in range(0, int(height) + 1, int(tile_px)):
            pygame.draw.line(grid, color, (0, y), (int(width), y))

        self._grid_cache_key = key
        self._grid_cache_surface = grid
        return grid

    def _apply_lighting(self, surface: pygame.Surface, snapshot: PreviewSnapshot, tile_px: int) -> None:
        import pygame

        lighting = getattr(snapshot, "lighting", None)
        if lighting is None or not bool(getattr(lighting, "enabled", False)):
            return

        ambient_level = max(0, min(255, int(getattr(lighting, "ambient_level", 255))))
        ambient_color = tuple(int(c) for c in getattr(lighting, "ambient_color", (255, 255, 255)))
        ambient_alpha = max(0, min(220, int((255 - ambient_level) * 0.8)))

        if ambient_alpha > 0:
            ambient = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            ambient.fill((ambient_color[0], ambient_color[1], ambient_color[2], ambient_alpha))
            surface.blit(ambient, (0, 0))

        mode = str(getattr(lighting, "mode", "off"))
        if mode in ("ambient_only", "off"):
            return

        light_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        light_color = (255, 230, 180)

        for tile in snapshot.tiles:
            strength = int(getattr(tile, "light_strength", 0))
            if strength <= 0:
                continue
            alpha = min(200, max(40, int(strength * 0.6)))
            px, py = self._world_to_screen(int(tile.x), int(tile.y), snapshot.viewport)
            pygame.draw.rect(
                light_overlay,
                (light_color[0], light_color[1], light_color[2], alpha),
                (int(px), int(py), int(tile_px), int(tile_px)),
            )

        surface.blit(light_overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
