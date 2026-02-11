from __future__ import annotations

import contextlib
import logging
import queue
import threading
import time

from py_rme_canary.core.assets.appearances_dat import AppearanceIndex
from py_rme_canary.core.database.items_xml import ItemsXML
from py_rme_canary.core.memory_guard import MemoryGuard, default_memory_guard
from py_rme_canary.logic_layer.sprite_system.legacy_dat import LegacyItemSpriteInfo
from py_rme_canary.vis_layer.preview.preview_renderer import IngameRenderer, PreviewSnapshot

log = logging.getLogger(__name__)


class PreviewMetrics:
    """Lightweight frame-time tracker for the preview window."""

    __slots__ = ("_times", "_max_samples")

    def __init__(self, max_samples: int = 120) -> None:
        self._times: list[float] = []
        self._max_samples = int(max_samples)

    def record(self, frame_ms: float) -> None:
        self._times.append(float(frame_ms))
        if len(self._times) > self._max_samples:
            self._times = self._times[-self._max_samples:]

    @property
    def avg_ms(self) -> float:
        return sum(self._times) / max(1, len(self._times)) if self._times else 0.0

    @property
    def fps(self) -> float:
        avg = self.avg_ms
        return 1000.0 / avg if avg > 0 else 0.0

    @property
    def max_ms(self) -> float:
        return max(self._times) if self._times else 0.0


class PreviewThread(threading.Thread):
    """Background thread running the pygame-based In-Game Preview window.

    Phase 8 improvements:
    - FPS/frame-time debug overlay (toggle with F3)
    - Grid toggle via F5
    - Esc closes the preview window
    - Graceful error recovery for pygame init failures
    - Performance metrics tracking
    """

    def __init__(
        self,
        *,
        sprite_provider: object,
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
        self._show_debug_overlay: bool = False
        self._metrics = PreviewMetrics()
        self._error: str | None = None

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

    @property
    def last_error(self) -> str | None:
        """Return the last error message if the thread failed to start."""
        return self._error

    @property
    def metrics(self) -> PreviewMetrics:
        return self._metrics

    def run(self) -> None:
        try:
            self._run_loop()
        except Exception as exc:
            self._error = str(exc)
            log.error("Preview thread crashed: %s", exc, exc_info=True)
        finally:
            self._cleanup_pygame()

    def _run_loop(self) -> None:
        import pygame

        try:
            pygame.init()
        except Exception as exc:
            self._error = f"pygame.init() failed: {exc}"
            log.error(self._error)
            return

        try:
            screen = pygame.display.set_mode(self._initial_size, pygame.RESIZABLE)
        except Exception as exc:
            self._error = f"pygame.display.set_mode() failed: {exc}"
            log.error(self._error)
            pygame.quit()
            return

        pygame.display.set_caption("In-Game Preview - RME")
        clock = pygame.time.Clock()
        debug_font = None

        while not self._stop_event.is_set():
            frame_start = time.perf_counter()

            screen = self._process_events(pygame, screen)
            if self._stop_event.is_set():
                break

            with contextlib.suppress(queue.Empty):
                self._current_snapshot = self._queue.get_nowait()

            if self._current_snapshot is not None:
                self._renderer.render(screen, self._current_snapshot)

                if self._show_debug_overlay:
                    debug_font = self._draw_debug_overlay(pygame, screen, debug_font, clock)

                pygame.display.flip()

            clock.tick(60)

            frame_ms = (time.perf_counter() - frame_start) * 1000.0
            self._metrics.record(frame_ms)

    def _process_events(self, pygame: object, screen: object) -> object:
        """Process pygame events. Returns (potentially new) screen surface."""
        import pygame as pg

        for event in pg.event.get():
            if event.type == pg.QUIT:
                self._stop_event.set()
            elif event.type == pg.VIDEORESIZE:
                screen = pg.display.set_mode(event.size, pg.RESIZABLE)
            elif event.type == pg.KEYDOWN:
                screen = self._handle_keydown(pg, event, screen)
        return screen

    def _handle_keydown(self, _pg: object, event: object, screen: object) -> object:
        """Handle keyboard shortcuts in the preview window."""
        import pygame

        key = getattr(event, "key", 0)

        # Esc → close preview
        if key == pygame.K_ESCAPE:
            self._stop_event.set()

        # F3 → toggle debug overlay
        elif key == pygame.K_F3:
            self._show_debug_overlay = not self._show_debug_overlay

        # F5 → toggle grid (modify current snapshot in place)
        elif key == pygame.K_F5:
            if self._current_snapshot is not None:
                from dataclasses import replace
                self._current_snapshot = replace(
                    self._current_snapshot,
                    show_grid=not self._current_snapshot.show_grid,
                )

        # F11 → toggle fullscreen
        elif key == pygame.K_F11:
            pygame.display.toggle_fullscreen()

        return screen

    def _draw_debug_overlay(
        self, _pygame_mod: object, screen: object, font: object, _clock: object
    ) -> object:
        """Draw FPS and performance metrics overlay."""
        import pygame

        if font is None:
            font = pygame.font.SysFont("Consolas", 14, bold=True)

        fps = self._metrics.fps
        avg_ms = self._metrics.avg_ms
        max_ms = self._metrics.max_ms
        tile_count = 0
        if self._current_snapshot is not None:
            tile_count = len(self._current_snapshot.tiles)

        lines = [
            f"FPS: {fps:.1f}",
            f"Frame: {avg_ms:.1f}ms (max {max_ms:.1f}ms)",
            f"Tiles: {tile_count}",
        ]

        bg_surface = pygame.Surface((200, len(lines) * 18 + 8), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 160))
        screen.blit(bg_surface, (4, 4))  # type: ignore[union-attr]

        y = 8
        for line in lines:
            shadow = font.render(line, True, (0, 0, 0))  # type: ignore[union-attr]
            text = font.render(line, True, (0, 255, 128))  # type: ignore[union-attr]
            screen.blit(shadow, (9, y + 1))  # type: ignore[union-attr]
            screen.blit(text, (8, y))  # type: ignore[union-attr]
            y += 18

        return font

    @staticmethod
    def _cleanup_pygame() -> None:
        """Safely quit pygame, ignoring errors."""
        try:
            import pygame
            pygame.quit()
        except Exception:
            pass
