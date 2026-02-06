"""Performance monitoring dock widget.

Displays real-time performance metrics:
- FPS (frames per second)
- Frame time
- Memory usage
- GPU memory (if available)
- Tile count
- Draw calls
"""

from __future__ import annotations

import time
from collections import deque
from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QDockWidget,
    QFrame,
    QGridLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


class MetricWidget(QFrame):
    """Individual metric display with label and value."""

    def __init__(
        self,
        label: str,
        unit: str = "",
        show_bar: bool = False,
        max_value: float = 100.0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._unit = unit
        self._max_value = max_value

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(2)

        # Label
        self._label = QLabel(label)
        self._label.setStyleSheet("color: #9CA3AF; font-size: 10px;")
        layout.addWidget(self._label)

        # Value
        self._value_label = QLabel("--")
        self._value_label.setStyleSheet("color: #E5E5E7; font-size: 14px; font-weight: bold;")
        layout.addWidget(self._value_label)

        # Optional progress bar
        self._bar: QProgressBar | None = None
        if show_bar:
            self._bar = QProgressBar()
            self._bar.setMaximum(100)
            self._bar.setTextVisible(False)
            self._bar.setFixedHeight(4)
            self._bar.setStyleSheet(
                """
                QProgressBar {
                    background: #2A2A3E;
                    border: none;
                    border-radius: 2px;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #8B5CF6, stop:1 #A78BFA);
                    border-radius: 2px;
                }
            """
            )
            layout.addWidget(self._bar)

        self.setStyleSheet(
            """
            MetricWidget {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 6px;
            }
        """
        )

    def set_value(self, value: float, warning_threshold: float | None = None) -> None:
        """Update the displayed value."""
        if self._unit:
            self._value_label.setText(f"{value:.1f} {self._unit}")
        else:
            self._value_label.setText(f"{value:.1f}")

        # Update bar if present
        if self._bar is not None:
            pct = min(100, int((value / self._max_value) * 100))
            self._bar.setValue(pct)

            # Color coding based on threshold
            if warning_threshold is not None:
                if value >= warning_threshold:
                    self._bar.setStyleSheet(
                        """
                        QProgressBar {
                            background: #2A2A3E;
                            border: none;
                            border-radius: 2px;
                        }
                        QProgressBar::chunk {
                            background: #EF4444;
                            border-radius: 2px;
                        }
                    """
                    )
                else:
                    self._bar.setStyleSheet(
                        """
                        QProgressBar {
                            background: #2A2A3E;
                            border: none;
                            border-radius: 2px;
                        }
                        QProgressBar::chunk {
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #8B5CF6, stop:1 #A78BFA);
                            border-radius: 2px;
                        }
                    """
                    )


class PerformanceDock(QDockWidget):
    """Dock widget for performance monitoring.

    Usage:
        dock = PerformanceDock()
        main_window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

        # Update metrics
        dock.update_fps(60.0)
        dock.update_memory(150.5)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Performance", parent)

        self._fps_history: deque[float] = deque(maxlen=60)
        self._last_frame_time = time.perf_counter()

        self._setup_ui()
        self._start_timer()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Grid for metrics
        grid = QGridLayout()
        grid.setSpacing(8)

        # FPS
        self._fps_widget = MetricWidget("FPS", "", show_bar=True, max_value=120.0)
        grid.addWidget(self._fps_widget, 0, 0)

        # Frame time
        self._frame_time_widget = MetricWidget("Frame Time", "ms", show_bar=True, max_value=50.0)
        grid.addWidget(self._frame_time_widget, 0, 1)

        # Memory
        self._memory_widget = MetricWidget("Memory", "MB", show_bar=True, max_value=2048.0)
        grid.addWidget(self._memory_widget, 1, 0)

        # Tile count
        self._tiles_widget = MetricWidget("Tiles", "")
        grid.addWidget(self._tiles_widget, 1, 1)

        # Draw calls
        self._draw_calls_widget = MetricWidget("Draw Calls", "")
        grid.addWidget(self._draw_calls_widget, 2, 0)

        # GPU Memory (placeholder)
        self._gpu_memory_widget = MetricWidget("GPU Mem", "MB")
        grid.addWidget(self._gpu_memory_widget, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()

        self.setWidget(container)

        # Apply dock styling
        self.setStyleSheet(
            """
            QDockWidget {
                color: #E5E5E7;
                font-weight: bold;
            }
            QDockWidget::title {
                background: #1A1A2E;
                padding: 8px;
                border-bottom: 1px solid #363650;
            }
        """
        )

        container.setStyleSheet("background: #16161E;")

    def _start_timer(self) -> None:
        """Start the update timer."""
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_metrics)
        self._timer.start(500)  # Update every 500ms

    def _update_metrics(self) -> None:
        """Update all metrics."""
        self._update_memory()
        self._update_fps_display()

    def _update_memory(self) -> None:
        """Update memory usage display."""
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            self._memory_widget.set_value(memory_mb, warning_threshold=1500.0)
        except ImportError:
            pass
        except Exception:
            pass

    def _update_fps_display(self) -> None:
        """Update FPS display from history."""
        if self._fps_history:
            avg_fps = sum(self._fps_history) / len(self._fps_history)
            self._fps_widget.set_value(avg_fps, warning_threshold=30.0)

    def update_fps(self, fps: float) -> None:
        """Update FPS value.

        Call this once per frame from the render loop.
        """
        self._fps_history.append(fps)

    def update_frame_time(self, frame_time_ms: float) -> None:
        """Update frame time in milliseconds."""
        self._frame_time_widget.set_value(frame_time_ms, warning_threshold=33.3)

    def update_tile_count(self, count: int) -> None:
        """Update visible tile count."""
        self._tiles_widget.set_value(float(count))

    def update_draw_calls(self, count: int) -> None:
        """Update draw call count."""
        self._draw_calls_widget.set_value(float(count))

    def update_gpu_memory(self, memory_mb: float) -> None:
        """Update GPU memory usage."""
        self._gpu_memory_widget.set_value(memory_mb)

    def frame_tick(self) -> None:
        """Call this at the end of each frame to calculate FPS.

        Automatically calculates FPS based on time between calls.
        """
        now = time.perf_counter()
        dt = now - self._last_frame_time
        self._last_frame_time = now

        if dt > 0:
            fps = 1.0 / dt
            frame_time_ms = dt * 1000
            self.update_fps(fps)
            self.update_frame_time(frame_time_ms)
