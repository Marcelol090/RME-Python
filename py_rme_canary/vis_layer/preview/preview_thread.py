from __future__ import annotations

import queue
import threading
from typing import Optional

from py_rme_canary.core.assets.appearances_dat import AppearanceIndex
from py_rme_canary.core.database.items_xml import ItemsXML
from py_rme_canary.core.memory_guard import MemoryGuard, default_memory_guard
from py_rme_canary.logic_layer.sprite_system.legacy_dat import LegacyItemSpriteInfo
from py_rme_canary.vis_layer.preview.preview_renderer import IngameRenderer, PreviewSnapshot


class PreviewThread(threading.Thread):
    def __init__(
        self,
        *,
        sprite_provider,
        appearance_index: AppearanceIndex | None,
        legacy_items: dict[int, LegacyItemSpriteInfo] | None,
        items_xml: ItemsXML | None,
        memory_guard: MemoryGuard | None = None,
        initial_size: tuple[int, int] = (640, 480),
    ) -> None:
        super().__init__(daemon=True)
        self._queue: queue.Queue[PreviewSnapshot] = queue.Queue(maxsize=2)
        self._stop_event = threading.Event()
        self._renderer = IngameRenderer(
            sprite_provider=sprite_provider,
            appearance_index=appearance_index,
            legacy_items=legacy_items,
            items_xml=items_xml,
            memory_guard=memory_guard or default_memory_guard(),
        )
        self._initial_size = (int(initial_size[0]), int(initial_size[1]))
        self._current_snapshot: PreviewSnapshot | None = None

    def submit_snapshot(self, snapshot: PreviewSnapshot) -> None:
        if self._stop_event.is_set():
            return
        try:
            self._queue.put_nowait(snapshot)
        except queue.Full:
            try:
                _ = self._queue.get_nowait()
            except queue.Empty:
                return
            try:
                self._queue.put_nowait(snapshot)
            except queue.Full:
                return

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        import pygame

        pygame.init()
        screen = pygame.display.set_mode(self._initial_size, pygame.RESIZABLE)
        pygame.display.set_caption("In-Game Preview - RME")
        clock = pygame.time.Clock()

        while not self._stop_event.is_set():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._stop_event.set()
                elif event.type == pygame.VIDEORESIZE:
                    screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)

            try:
                self._current_snapshot = self._queue.get_nowait()
            except queue.Empty:
                pass

            if self._current_snapshot is not None:
                self._renderer.render(screen, self._current_snapshot)
                pygame.display.flip()

            clock.tick(60)

        pygame.quit()