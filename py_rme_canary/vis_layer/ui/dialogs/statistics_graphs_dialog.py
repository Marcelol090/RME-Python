"""Statistics Graphs Dialog.

Provides visual representation of map statistics using charts.
Complements the text-based MapStatisticsDialog with graphical insights.

Reference:
    - project_tasks.json: TOOL-002 (Statistics Graphs)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

if TYPE_CHECKING:
    from core.data.gamemap import GameMap

logger = logging.getLogger(__name__)


# Try to import matplotlib - it's optional
try:
    import matplotlib

    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    FigureCanvas = None
    Figure = None


class ChartWidget(QWidget):
    """Widget that displays a matplotlib chart."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._figure: Figure | None = None
        self._canvas: FigureCanvas | None = None

        if not HAS_MATPLOTLIB:
            layout = QVBoxLayout(self)
            label = QLabel("Matplotlib not installed.\npip install matplotlib")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #EF4444; font-size: 14px;")
            layout.addWidget(label)
            return

        self._figure = Figure(figsize=(8, 6), dpi=100)
        self._figure.set_facecolor("#1E1E2E")
        self._canvas = FigureCanvas(self._figure)
        self._canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._canvas)

    @property
    def figure(self) -> Figure | None:
        return self._figure

    def refresh(self) -> None:
        """Redraw the canvas."""
        if self._canvas:
            self._canvas.draw()


class ItemDistributionChart(ChartWidget):
    """Pie chart showing distribution of items by category."""

    def __init__(self, game_map: GameMap, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._game_map = game_map
        if HAS_MATPLOTLIB:
            self._draw_chart()

    def _draw_chart(self) -> None:
        if not self._figure:
            return

        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor("#1E1E2E")

        # Collect statistics
        categories = {
            "Ground": 0,
            "Items": 0,
            "Creatures": 0,
            "Spawns": 0,
            "Houses": 0,
            "Other": 0,
        }

        try:
            for tile in self._game_map.iter_tiles():
                if tile.ground:
                    categories["Ground"] += 1
                categories["Items"] += len(tile.items) if hasattr(tile, "items") else 0
                if hasattr(tile, "creature") and tile.creature:
                    categories["Creatures"] += 1
                if hasattr(tile, "spawn") and tile.spawn:
                    categories["Spawns"] += 1
                if hasattr(tile, "house_id") and tile.house_id:
                    categories["Houses"] += 1
        except Exception as e:
            logger.warning("Failed to collect statistics: %s", e)

        # Filter out zero values
        labels = []
        sizes = []
        colors = ["#22C55E", "#8B5CF6", "#EF4444", "#F59E0B", "#3B82F6", "#6B7280"]
        filtered_colors = []

        for i, (label, size) in enumerate(categories.items()):
            if size > 0:
                labels.append(f"{label}\n({size:,})")
                sizes.append(size)
                filtered_colors.append(colors[i % len(colors)])

        if sizes:
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                colors=filtered_colors,
                autopct="%1.1f%%",
                startangle=90,
                textprops={"color": "#E5E5E7", "fontsize": 10},
            )
            for autotext in autotexts:
                autotext.set_color("#E5E5E7")
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes, color="#9CA3AF", fontsize=14)

        ax.set_title("Item Distribution by Category", color="#E5E5E7", fontsize=14, pad=20)
        self.refresh()


class FloorDistributionChart(ChartWidget):
    """Bar chart showing tile count per floor."""

    def __init__(self, game_map: GameMap, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._game_map = game_map
        if HAS_MATPLOTLIB:
            self._draw_chart()

    def _draw_chart(self) -> None:
        if not self._figure:
            return

        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor("#1E1E2E")

        # Count tiles per floor
        floor_counts: dict[int, int] = {}
        try:
            for tile in self._game_map.iter_tiles():
                z = tile.z if hasattr(tile, "z") else 7
                floor_counts[z] = floor_counts.get(z, 0) + 1
        except Exception as e:
            logger.warning("Failed to collect floor statistics: %s", e)

        if floor_counts:
            floors = sorted(floor_counts.keys())
            counts = [floor_counts[z] for z in floors]

            # Create gradient colors based on floor level
            colors = []
            for z in floors:
                if z < 7:  # Underground
                    colors.append("#6B7280")
                elif z == 7:  # Ground level
                    colors.append("#22C55E")
                else:  # Above ground
                    colors.append("#3B82F6")

            bars = ax.bar([str(z) for z in floors], counts, color=colors)

            # Add value labels on bars
            for bar, count in zip(bars, counts, strict=False):
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    height,
                    f"{count:,}",
                    ha="center",
                    va="bottom",
                    color="#E5E5E7",
                    fontsize=9,
                )
        else:
            ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes, color="#9CA3AF", fontsize=14)

        ax.set_xlabel("Floor (Z)", color="#E5E5E7")
        ax.set_ylabel("Tile Count", color="#E5E5E7")
        ax.set_title("Tiles per Floor", color="#E5E5E7", fontsize=14, pad=20)
        ax.tick_params(colors="#9CA3AF")
        ax.spines["bottom"].set_color("#363650")
        ax.spines["top"].set_color("#363650")
        ax.spines["left"].set_color("#363650")
        ax.spines["right"].set_color("#363650")

        self._figure.tight_layout()
        self.refresh()


class DensityHeatmapChart(ChartWidget):
    """Heatmap showing tile density across the map."""

    GRID_SIZE = 20  # Divide map into 20x20 grid

    def __init__(self, game_map: GameMap, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._game_map = game_map
        if HAS_MATPLOTLIB:
            self._draw_chart()

    def _draw_chart(self) -> None:
        if not self._figure:
            return

        try:
            import numpy as np
        except Exception:
            self._figure.clear()
            ax = self._figure.add_subplot(111)
            ax.set_facecolor("#1E1E2E")
            ax.text(
                0.5,
                0.5,
                "NumPy not installed",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color="#EF4444",
                fontsize=14,
            )
            self.refresh()
            return

        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor("#1E1E2E")

        # Get map bounds
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        try:
            for tile in self._game_map.iter_tiles():
                x = tile.x if hasattr(tile, "x") else 0
                y = tile.y if hasattr(tile, "y") else 0
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        except Exception:
            min_x = min_y = 0
            max_x = max_y = 100

        if min_x == float("inf"):
            min_x = min_y = 0
            max_x = max_y = 100

        # Create density grid
        width = max(1, max_x - min_x + 1)
        height = max(1, max_y - min_y + 1)

        cell_w = max(1, width // self.GRID_SIZE)
        cell_h = max(1, height // self.GRID_SIZE)

        grid = np.zeros((self.GRID_SIZE, self.GRID_SIZE))

        try:
            for tile in self._game_map.iter_tiles():
                x = tile.x if hasattr(tile, "x") else 0
                y = tile.y if hasattr(tile, "y") else 0
                gx = min(self.GRID_SIZE - 1, (x - min_x) // cell_w)
                gy = min(self.GRID_SIZE - 1, (y - min_y) // cell_h)
                grid[gy, gx] += 1
        except Exception as e:
            logger.warning("Failed to build density grid: %s", e)

        # Draw heatmap
        im = ax.imshow(
            grid,
            cmap="viridis",
            aspect="auto",
            origin="upper",
        )

        # Colorbar
        cbar = self._figure.colorbar(im, ax=ax)
        cbar.ax.yaxis.set_tick_params(color="#E5E5E7")
        cbar.outline.set_edgecolor("#363650")
        for label in cbar.ax.get_yticklabels():
            label.set_color("#E5E5E7")

        ax.set_title("Tile Density Heatmap", color="#E5E5E7", fontsize=14, pad=20)
        ax.set_xlabel("X Region", color="#E5E5E7")
        ax.set_ylabel("Y Region", color="#E5E5E7")
        ax.tick_params(colors="#9CA3AF")

        self._figure.tight_layout()
        self.refresh()


class StatisticsGraphsDialog(ModernDialog):
    """Dialog displaying map statistics as interactive charts.

    Provides visual insights into:
    - Item distribution by category
    - Tile count per floor level
    - Map density heatmap

    Usage:
        dialog = StatisticsGraphsDialog(parent, game_map=editor.map)
        dialog.exec()
    """

    def __init__(self, parent: QWidget | None, *, game_map: GameMap) -> None:
        self._game_map = game_map
        super().__init__(parent, title="Map Statistics - Graphs")
        self.resize(800, 600)
        self._setup_content()

    def _setup_content(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget for different charts
        self._tabs = QTabWidget()

        # Distribution chart
        self._dist_chart = ItemDistributionChart(self._game_map)
        self._tabs.addTab(self._dist_chart, "Item Distribution")

        # Floor chart
        self._floor_chart = FloorDistributionChart(self._game_map)
        self._tabs.addTab(self._floor_chart, "Floors")

        # Density heatmap
        self._density_chart = DensityHeatmapChart(self._game_map)
        self._tabs.addTab(self._density_chart, "Density Heatmap")

        layout.addWidget(self._tabs)

        # Set content layout
        self.set_content_layout(layout)

        # Buttons in footer
        self.add_button("Refresh", callback=self._refresh_all)
        self.add_spacer_to_footer()
        self.add_button("Close", callback=self.accept)

    def _refresh_all(self) -> None:
        """Refresh all charts."""
        # Recreate charts with fresh data
        current_index = self._tabs.currentIndex()

        # Remove old widgets
        while self._tabs.count() > 0:
            widget = self._tabs.widget(0)
            self._tabs.removeTab(0)
            widget.deleteLater()

        # Create new charts
        self._dist_chart = ItemDistributionChart(self._game_map)
        self._tabs.addTab(self._dist_chart, "Item Distribution")

        self._floor_chart = FloorDistributionChart(self._game_map)
        self._tabs.addTab(self._floor_chart, "Floors")

        self._density_chart = DensityHeatmapChart(self._game_map)
        self._tabs.addTab(self._density_chart, "Density Heatmap")

        # Restore tab selection
        if 0 <= current_index < self._tabs.count():
            self._tabs.setCurrentIndex(current_index)
