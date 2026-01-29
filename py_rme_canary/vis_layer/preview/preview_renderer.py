from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from py_rme_canary.core.assets.appearances_dat import AppearanceIndex, SpriteInfo
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


@dataclass(frozen=True, slots=True)
class PreviewSnapshot:
    viewport: PreviewViewport
    tiles: tuple[TileSnapshot, ...]
    time_ms: int


class SpriteSurfaceCache:
    def __init__(self, sprite_provider, *, memory_guard: MemoryGuard | None = None) -> None:
        self._sprite_provider = sprite_provider
        self._cache: OrderedDict[int, "pygame.Surface"] = OrderedDict()
        self._memory_guard = memory_guard or default_memory_guard()

    def get_surface(self, sprite_id: int, *, placeholder_size: int = 32) -> "pygame.Surface":
        import pygame

        sid = int(sprite_id)
        cached = self._cache.get(sid)
        if cached is not None:
            try:
                self._cache.move_to_end(sid)
            except Exception:
                pass
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
        try:
            self._cache.move_to_end(sid)
        except Exception:
            pass

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

    def _placeholder_surface(self, size: int) -> "pygame.Surface":
        import pygame

        surf = pygame.Surface((int(size), int(size)), pygame.SRCALPHA)
        surf.fill((200, 0, 200, 160))
        return surf


class IngameRenderer:
    def __init__(
        self,
        *,
        sprite_provider,
        appearance_index: AppearanceIndex | None,
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

    def render(self, screen: "pygame.Surface", snapshot: PreviewSnapshot) -> None:
        import pygame

        if snapshot is None:
            return
        viewport = snapshot.viewport
        tile_px = int(viewport.tile_px)
        if tile_px <= 0:
            return

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
                screen_x = (int(tx) - int(viewport.origin_x)) * tile_px
                screen_y = (int(ty) - int(viewport.origin_y)) * tile_px
                self._draw_tile(world_surface, tile, screen_x, screen_y, time_ms=int(snapshot.time_ms))

        if world_surface.get_size() != screen.get_size():
            scaled = pygame.transform.smoothscale(world_surface, screen.get_size())
            screen.blit(scaled, (0, 0))
        else:
            screen.blit(world_surface, (0, 0))

    def _draw_tile(self, surface: "pygame.Surface", tile: TileSnapshot, screen_x: int, screen_y: int, *, time_ms: int) -> None:
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
        surface: "pygame.Surface",
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
        surface: "pygame.Surface",
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
        surface: "pygame.Surface",
        tile: TileSnapshot,
        item: PreviewItem,
        info: SpriteInfo,
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
                (((int(frame) * int(info.pattern_depth) + int(pattern_z)) * int(info.pattern_height) + int(pattern_y))
                * int(info.pattern_width) + int(pattern_x)) * layers + int(layer)
            )
            if not info.sprite_ids:
                continue
            if idx >= len(info.sprite_ids):
                idx = idx % len(info.sprite_ids)
            sprite_id = int(info.sprite_ids[idx])
            sprite = self._surface_cache.get_surface(sprite_id, placeholder_size=self._tile_px)
            surface.blit(sprite, (screen_x, screen_y))

        self._draw_stack_count(surface, item, screen_x, screen_y)

    def _draw_stack_count(self, surface: "pygame.Surface", item: PreviewItem, screen_x: int, screen_y: int) -> None:
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