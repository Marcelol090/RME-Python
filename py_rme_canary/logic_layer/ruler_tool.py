"""Ruler/Distance Measure Tool.

This module provides tools for measuring distances and areas on the map.
Essential for map designers planning spawn areas, house sizes, and pathfinding.

Reference:
    - Common feature in map editors (Tiled, RPG Maker)
    - User request for planning tools

Features:
    - RulerTool: Measures straight-line distance
    - PathMeasure: Measures along a path (polyline)
    - AreaMeasure: Measures rectangular or polygonal areas
    - Unit conversion (tiles, SQM, walking time)

Layer: logic_layer (no PyQt6 dependencies)
"""

from __future__ import annotations

import logging
import math
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from enum import Enum, auto

logger = logging.getLogger(__name__)


class MeasureUnit(Enum):
    """Units for distance/area measurements."""

    TILES = auto()  # Raw tile count
    SQM = auto()  # Square meters (1 tile = 1 SQM in Tibia)
    PIXELS = auto()  # Pixel distance (tile = 32px)
    WALK_TIME = auto()  # Walking time in seconds (diagonal = 1.4x)


class DistanceType(Enum):
    """Type of distance calculation."""

    EUCLIDEAN = auto()  # Straight line (sqrt)
    MANHATTAN = auto()  # City block (abs sum)
    CHEBYSHEV = auto()  # Diagonal allowed (max of abs)
    WALKING = auto()  # Actual walking (diagonal costs more)


# Position type alias
Position = tuple[int, int, int]  # (x, y, z)
Position2D = tuple[int, int]  # (x, y)


@dataclass(slots=True, frozen=True)
class MeasurePoint:
    """A point in a measurement.

    Attributes:
        x: X coordinate.
        y: Y coordinate.
        z: Z coordinate (floor level).
        label: Optional label for the point.
    """

    x: int
    y: int
    z: int
    label: str = ""

    @classmethod
    def from_tuple(cls, pos: Position, label: str = "") -> MeasurePoint:
        return cls(pos[0], pos[1], pos[2], label)

    def to_tuple(self) -> Position:
        return (self.x, self.y, self.z)

    def __str__(self) -> str:
        if self.label:
            return f"{self.label}: ({self.x}, {self.y}, {self.z})"
        return f"({self.x}, {self.y}, {self.z})"


@dataclass
class DistanceResult:
    """Result of a distance measurement.

    Attributes:
        start: Starting point.
        end: End point.
        euclidean: Straight-line distance in tiles.
        manhattan: Manhattan distance.
        chebyshev: Chebyshev distance.
        walking: Walking distance (diagonal = sqrt(2)).
        walking_time_sec: Estimated walking time in seconds.
        delta_x: X difference.
        delta_y: Y difference.
        delta_z: Z difference.
        angle_deg: Angle in degrees (0 = East, 90 = North).
    """

    start: MeasurePoint
    end: MeasurePoint
    euclidean: float = 0.0
    manhattan: int = 0
    chebyshev: int = 0
    walking: float = 0.0
    walking_time_sec: float = 0.0
    delta_x: int = 0
    delta_y: int = 0
    delta_z: int = 0
    angle_deg: float = 0.0

    def format(self, unit: MeasureUnit = MeasureUnit.TILES) -> str:
        """Format the distance for display."""
        if unit == MeasureUnit.TILES:
            return f"{self.euclidean:.1f} tiles"
        elif unit == MeasureUnit.SQM:
            return f"{self.euclidean:.1f} SQM"
        elif unit == MeasureUnit.PIXELS:
            return f"{self.euclidean * 32:.0f} px"
        elif unit == MeasureUnit.WALK_TIME:
            return f"{self.walking_time_sec:.1f}s walk"
        return f"{self.euclidean:.1f}"


@dataclass
class AreaResult:
    """Result of an area measurement.

    Attributes:
        points: List of corner points.
        area_tiles: Area in tiles.
        perimeter: Perimeter in tiles.
        bounding_box: (min_x, min_y, max_x, max_y).
        width: Width in tiles.
        height: Height in tiles.
        center: Center point.
    """

    points: list[MeasurePoint] = field(default_factory=list)
    area_tiles: float = 0.0
    perimeter: float = 0.0
    bounding_box: tuple[int, int, int, int] | None = None
    width: int = 0
    height: int = 0
    center: MeasurePoint | None = None
    error: str = ""

    def format(self, unit: MeasureUnit = MeasureUnit.SQM) -> str:
        """Format the area for display."""
        if unit == MeasureUnit.TILES or unit == MeasureUnit.SQM:
            return f"{self.area_tiles:.0f} SQM ({self.width}x{self.height})"
        return f"{self.area_tiles:.0f} tiles"


@dataclass
class PathResult:
    """Result of a path/polyline measurement.

    Attributes:
        points: Points along the path.
        total_distance: Total path length.
        segment_distances: Distance of each segment.
        walking_time_sec: Total walking time.
    """

    points: list[MeasurePoint] = field(default_factory=list)
    total_distance: float = 0.0
    segment_distances: list[float] = field(default_factory=list)
    walking_time_sec: float = 0.0

    @property
    def segment_count(self) -> int:
        return max(0, len(self.points) - 1)


class RulerTool:
    """Tool for measuring distances on the map.

    Example:
        ruler = RulerTool()

        # Measure distance between two points
        result = ruler.measure(
            start=(100, 100, 7),
            end=(110, 105, 7)
        )
        print(f"Distance: {result.euclidean:.1f} tiles")
        print(f"Walking time: {result.walking_time_sec:.1f}s")

        # Measure a path
        path_result = ruler.measure_path([
            (100, 100, 7),
            (110, 100, 7),
            (110, 110, 7)
        ])
        print(f"Total path: {path_result.total_distance:.1f} tiles")
    """

    # Walking speed in tiles per second (approximate for Tibia)
    WALK_SPEED_TILES_PER_SEC = 4.5
    DIAGONAL_COST = math.sqrt(2)  # ~1.414

    def __init__(self) -> None:
        """Initialize the ruler tool."""
        self._points: list[MeasurePoint] = []
        self._is_measuring = False

    def measure(
        self,
        start: Position | MeasurePoint,
        end: Position | MeasurePoint,
        distance_type: DistanceType = DistanceType.EUCLIDEAN,
    ) -> DistanceResult:
        """Measure distance between two points.

        Args:
            start: Starting position.
            end: Ending position.
            distance_type: Type of distance calculation.

        Returns:
            DistanceResult with all metrics.
        """
        # Convert to MeasurePoint if needed
        if isinstance(start, tuple):
            start = MeasurePoint.from_tuple(start)
        if isinstance(end, tuple):
            end = MeasurePoint.from_tuple(end)

        # Calculate deltas
        dx = end.x - start.x
        dy = end.y - start.y
        dz = end.z - start.z

        abs_dx = abs(dx)
        abs_dy = abs(dy)

        # Calculate all distance types
        euclidean = math.sqrt(dx * dx + dy * dy)
        manhattan = abs_dx + abs_dy
        chebyshev = max(abs_dx, abs_dy)

        # Walking distance (diagonal movements cost more)
        diag_steps = min(abs_dx, abs_dy)
        straight_steps = abs(abs_dx - abs_dy)
        walking = diag_steps * self.DIAGONAL_COST + straight_steps

        # Estimate walking time
        walking_time = walking / self.WALK_SPEED_TILES_PER_SEC

        # Calculate angle (0 = East, 90 = North)
        angle = 0.0
        if dx != 0 or dy != 0:
            angle = math.degrees(math.atan2(-dy, dx))  # Negative Y because Y increases downward

        return DistanceResult(
            start=start,
            end=end,
            euclidean=euclidean,
            manhattan=manhattan,
            chebyshev=chebyshev,
            walking=walking,
            walking_time_sec=walking_time,
            delta_x=dx,
            delta_y=dy,
            delta_z=dz,
            angle_deg=angle,
        )

    def measure_path(
        self,
        points: Sequence[Position | MeasurePoint],
    ) -> PathResult:
        """Measure the total distance along a path.

        Args:
            points: List of points forming the path.

        Returns:
            PathResult with total and segment distances.
        """
        if len(points) < 2:
            return PathResult(points=[p if isinstance(p, MeasurePoint) else MeasurePoint.from_tuple(p) for p in points])

        measure_points: list[MeasurePoint] = []
        segment_distances: list[float] = []
        total_distance = 0.0
        total_walk_time = 0.0

        for i, p in enumerate(points):
            mp = p if isinstance(p, MeasurePoint) else MeasurePoint.from_tuple(p)
            measure_points.append(mp)

            if i > 0:
                result = self.measure(measure_points[i - 1], mp)
                segment_distances.append(result.walking)
                total_distance += result.walking
                total_walk_time += result.walking_time_sec

        return PathResult(
            points=measure_points,
            total_distance=total_distance,
            segment_distances=segment_distances,
            walking_time_sec=total_walk_time,
        )

    def measure_area_rect(
        self,
        corner1: Position | MeasurePoint,
        corner2: Position | MeasurePoint,
    ) -> AreaResult:
        """Measure a rectangular area.

        Args:
            corner1: First corner.
            corner2: Opposite corner.

        Returns:
            AreaResult with dimensions and area.
        """
        if isinstance(corner1, tuple):
            corner1 = MeasurePoint.from_tuple(corner1)
        if isinstance(corner2, tuple):
            corner2 = MeasurePoint.from_tuple(corner2)

        min_x = min(corner1.x, corner2.x)
        max_x = max(corner1.x, corner2.x)
        min_y = min(corner1.y, corner2.y)
        max_y = max(corner1.y, corner2.y)

        width = max_x - min_x + 1
        height = max_y - min_y + 1
        area = width * height
        perimeter = 2 * (width + height)

        center_x = (min_x + max_x) // 2
        center_y = (min_y + max_y) // 2
        center = MeasurePoint(center_x, center_y, corner1.z)

        return AreaResult(
            points=[corner1, corner2],
            area_tiles=area,
            perimeter=perimeter,
            bounding_box=(min_x, min_y, max_x, max_y),
            width=width,
            height=height,
            center=center,
        )

    def measure_area_polygon(
        self,
        points: Sequence[Position | MeasurePoint],
    ) -> AreaResult:
        """Measure area of a polygon using Shoelace formula.

        Args:
            points: Vertices of the polygon (closed automatically).

        Returns:
            AreaResult with area and perimeter.
        """
        if len(points) < 3:
            return AreaResult(error="Need at least 3 points for polygon")

        measure_points: list[MeasurePoint] = [
            p if isinstance(p, MeasurePoint) else MeasurePoint.from_tuple(p) for p in points
        ]

        # Shoelace formula for area
        n = len(measure_points)
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += measure_points[i].x * measure_points[j].y
            area -= measure_points[j].x * measure_points[i].y
        area = abs(area) / 2.0

        # Calculate perimeter
        perimeter = 0.0
        for i in range(n):
            j = (i + 1) % n
            dx = measure_points[j].x - measure_points[i].x
            dy = measure_points[j].y - measure_points[i].y
            perimeter += math.sqrt(dx * dx + dy * dy)

        # Bounding box
        xs = [p.x for p in measure_points]
        ys = [p.y for p in measure_points]
        bbox = (min(xs), min(ys), max(xs), max(ys))

        # Center (centroid)
        center_x = sum(xs) // n
        center_y = sum(ys) // n
        center = MeasurePoint(center_x, center_y, measure_points[0].z)

        return AreaResult(
            points=measure_points,
            area_tiles=area,
            perimeter=perimeter,
            bounding_box=bbox,
            width=bbox[2] - bbox[0] + 1,
            height=bbox[3] - bbox[1] + 1,
            center=center,
        )

    def radius_to_area(self, radius: int) -> float:
        """Convert radius to circular area.

        Args:
            radius: Radius in tiles.

        Returns:
            Approximate circular area in tiles.
        """
        return math.pi * radius * radius

    def spawn_radius_tiles(self, radius: int) -> Iterator[Position2D]:
        """Generate all tile positions within a spawn radius.

        Useful for visualizing spawn areas.

        Args:
            radius: Spawn radius in tiles.

        Yields:
            (x, y) offsets from center within radius.
        """
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    yield (dx, dy)

    # Interactive measurement state
    def start_measurement(self) -> None:
        """Start a new measurement session."""
        self._points.clear()
        self._is_measuring = True

    def add_point(self, pos: Position) -> None:
        """Add a point to the current measurement."""
        if self._is_measuring:
            self._points.append(MeasurePoint.from_tuple(pos))

    def get_current_result(self) -> DistanceResult | PathResult | None:
        """Get result of current measurement."""
        if len(self._points) == 2:
            return self.measure(self._points[0], self._points[1])
        elif len(self._points) > 2:
            return self.measure_path(self._points)
        return None

    def end_measurement(self) -> DistanceResult | PathResult | None:
        """End measurement and return final result."""
        self._is_measuring = False
        return self.get_current_result()

    def clear(self) -> None:
        """Clear current measurement."""
        self._points.clear()
        self._is_measuring = False

    @property
    def is_measuring(self) -> bool:
        return self._is_measuring

    @property
    def points(self) -> list[MeasurePoint]:
        return self._points.copy()


def create_ruler_tool() -> RulerTool:
    """Factory function to create a RulerTool.

    Returns:
        New RulerTool instance.
    """
    return RulerTool()
