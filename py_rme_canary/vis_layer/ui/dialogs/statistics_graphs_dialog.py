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
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

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


def _tokens() -> dict:
    """Return the current color tokens dict."""
    return get_theme_manager().tokens["color"]


# Chart-specific categorical palette (not theme-dependent).
_CHART_PALETTE = ["#22C55E", "#8B5CF6", "#EF4444", "#F59E0B", "#3B82F6", "#6B7280"]


class ChartWidget(QWidget):
    """Widget that displays a matplotlib chart."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._figure: Figure | None = None
        self._canvas: FigureCanvas | None = None
        c = _tokens()

        if not HAS_MATPLOTLIB:
            layout = QVBoxLayout(self)
            label = QLabel("Matplotlib not installed.\npip install matplotlib")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"color: {c['state']['error']}; font-size: 14px;")
            layout.addWidget(label)
            return

        self._figure = Figure(figsize=(8, 6), dpi=100)
        self._figure.set_facecolor(c["surface"]["primary"])
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

        c = _tokens()
        text_primary = c["text"]["primary"]
        text_secondary = c["text"]["tertiary"]

        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor(c["surface"]["primary"])

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
        filtered_colors = []

        for i, (label, size) in enumerate(categories.items()):
            if size > 0:
                labels.append(f"{label}\n({size:,})")
                sizes.append(size)
                filtered_colors.append(_CHART_PALETTE[i % len(_CHART_PALETTE)])

        if sizes:
            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                colors=filtered_colors,
                autopct="%1.1f%%",
                startangle=90,
                textprops={"color": text_primary, "fontsize": 10},
            )
            for autotext in autotexts:
                autotext.set_color(text_primary)
        else:
            ax.text(
                0.5,
                0.5,
                "No data",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color=text_secondary,
                fontsize=14,
            )

        ax.set_title("Item Distribution by Category", color=text_primary, fontsize=14, pad=20)
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

        c = _tokens()
        text_primary = c["text"]["primary"]
        text_secondary = c["text"]["tertiary"]
        border_clr = c["border"]["default"]

        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor(c["surface"]["primary"])

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
                    colors.append(c["text"]["tertiary"])
                elif z == 7:  # Ground level
                    colors.append(c["state"]["success"])
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
                    color=text_primary,
                    fontsize=9,
                )
        else:
            ax.text(
                0.5,
                0.5,
                "No data",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color=text_secondary,
                fontsize=14,
            )

        ax.set_xlabel("Floor (Z)", color=text_primary)
        ax.set_ylabel("Tile Count", color=text_primary)
        ax.set_title("Tiles per Floor", color=text_primary, fontsize=14, pad=20)
        ax.tick_params(colors=text_secondary)
        for spine in ax.spines.values():
            spine.set_color(border_clr)

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

        c = _tokens()
        text_primary = c["text"]["primary"]
        text_secondary = c["text"]["tertiary"]
        border_clr = c["border"]["default"]
        surface = c["surface"]["primary"]

        try:
            import numpy as np
        except Exception:
            self._figure.clear()
            ax = self._figure.add_subplot(111)
            ax.set_facecolor(surface)
            ax.text(
                0.5,
                0.5,
                "NumPy not installed",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color=c["state"]["error"],
                fontsize=14,
            )
            self.refresh()
            return

        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor(surface)

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
        cbar.ax.yaxis.set_tick_params(color=text_primary)
        cbar.outline.set_edgecolor(border_clr)
        for label in cbar.ax.get_yticklabels():
            label.set_color(text_primary)

        ax.set_title("Tile Density Heatmap", color=text_primary, fontsize=14, pad=20)
        ax.set_xlabel("X Region", color=text_primary)
        ax.set_ylabel("Y Region", color=text_primary)
        ax.tick_params(colors=text_secondary)

        self._figure.tight_layout()
        self.refresh()


class StatisticsGraphsDialog(QDialog):
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
        super().__init__(parent)
        self._game_map = game_map

        self.setWindowTitle("Map Statistics - Graphs")
        self.setModal(True)
        self.resize(800, 600)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        c = _tokens()
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Map Statistics Visualization")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {c['text']['primary']};")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

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

        # Buttons
        button_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_all)
        button_layout.addWidget(refresh_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _apply_style(self) -> None:
        """Apply modern dark theme styling."""
        c = _tokens()
        r = get_theme_manager().tokens.get("radius", {})
        rad = r.get("md", 6)

        self.setStyleSheet(
            f"""
            QDialog {{
                background: {c['surface']['primary']};
                color: {c['text']['primary']};
            }}

            QTabWidget::pane {{
                border: 1px solid {c['border']['default']};
                border-radius: {rad}px;
                background: {c['surface']['primary']};
            }}

            QTabBar::tab {{
                background: {c['surface']['secondary']};
                color: {c['text']['tertiary']};
                padding: 8px 16px;
                border: 1px solid {c['border']['default']};
                border-bottom: none;
                border-top-left-radius: {rad}px;
                border-top-right-radius: {rad}px;
            }}

            QTabBar::tab:selected {{
                background: {c['surface']['tertiary']};
                color: {c['text']['primary']};
            }}

            QPushButton {{
                background: {c['surface']['tertiary']};
                border: 1px solid {c['border']['strong']};
                border-radius: {rad}px;
                padding: 8px 16px;
                color: {c['text']['primary']};
            }}

            QPushButton:hover {{
                background: {c['border']['strong']};
            }}
        """
        )

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
