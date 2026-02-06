"""Tests for statistics export."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from py_rme_canary.core.io.xml.safe import safe_etree as ET

from py_rme_canary.logic_layer.map_statistics import MapStatistics
from py_rme_canary.logic_layer.operations.export_statistics import (
    export_statistics,
    export_to_csv,
    export_to_json,
    export_to_xml,
)


@pytest.fixture
def sample_stats() -> MapStatistics:
    """Create sample statistics for testing."""
    return MapStatistics(
        total_tiles=1000,
        total_items=5000,
        unique_items=150,
        total_monsters=50,
        unique_monsters=10,
        total_npcs=10,
        unique_npcs=5,
        total_spawns=25,
        total_houses=5,
        items_with_action_id=100,
        items_with_unique_id=50,
        teleport_count=20,
        container_count=80,
        depot_count=5,
        door_count=40,
        waypoint_count=8,
        tiles_per_floor=(100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 5, 3, 2, 1, 0, 0),
    )


def test_export_to_xml(sample_stats: MapStatistics, tmp_path: Path) -> None:
    """Test XML export."""
    output_file = tmp_path / "stats.xml"

    export_to_xml(sample_stats, output_file)

    assert output_file.exists()

    # Parse and verify
    tree = ET.parse(output_file)
    root = tree.getroot()

    assert root.tag == "map_statistics"

    # Check basic stats
    basic = root.find("basic")
    assert basic is not None
    assert basic.find("total_tiles").text == "1000"  # type: ignore[union-attr]
    assert basic.find("total_items").text == "5000"  # type: ignore[union-attr]
    assert basic.find("unique_items").text == "150"  # type: ignore[union-attr]

    # Check creatures
    creatures = root.find("creatures")
    assert creatures is not None
    assert creatures.find("total_monsters").text == "50"  # type: ignore[union-attr]
    assert creatures.find("unique_monsters").text == "10"  # type: ignore[union-attr]


def test_export_to_csv(sample_stats: MapStatistics, tmp_path: Path) -> None:
    """Test CSV export."""
    output_file = tmp_path / "stats.csv"

    export_to_csv(sample_stats, output_file)

    assert output_file.exists()

    # Read and verify
    with output_file.open(encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)

    # Check header
    assert rows[0] == ["Category", "Metric", "Value"]

    # Check some values
    assert ["Basic", "Total Tiles", "1000"] in rows
    assert ["Creatures", "Total Monsters", "50"] in rows


def test_export_to_json(sample_stats: MapStatistics, tmp_path: Path) -> None:
    """Test JSON export."""
    output_file = tmp_path / "stats.json"

    export_to_json(sample_stats, output_file)

    assert output_file.exists()

    # Read and verify
    with output_file.open(encoding="utf-8") as jsonfile:
        data = json.load(jsonfile)

    assert data["total_tiles"] == 1000
    assert data["total_monsters"] == 50
    assert data["unique_items"] == 150
    assert len(data["tiles_per_floor"]) == 16


def test_export_statistics_xml(sample_stats: MapStatistics, tmp_path: Path) -> None:
    """Test export_statistics wrapper with XML format."""
    output_file = tmp_path / "output.xml"

    export_statistics(sample_stats, output_file, format_type="xml")

    assert output_file.exists()


def test_export_statistics_csv(sample_stats: MapStatistics, tmp_path: Path) -> None:
    """Test export_statistics wrapper with CSV format."""
    output_file = tmp_path / "output.csv"

    export_statistics(sample_stats, output_file, format_type="csv")

    assert output_file.exists()


def test_export_statistics_json(sample_stats: MapStatistics, tmp_path: Path) -> None:
    """Test export_statistics wrapper with JSON format."""
    output_file = tmp_path / "output.json"

    export_statistics(sample_stats, output_file, format_type="json")

    assert output_file.exists()


def test_export_statistics_invalid_format(
    sample_stats: MapStatistics,
    tmp_path: Path,
) -> None:
    """Test error handling for invalid format."""
    output_file = tmp_path / "output.txt"

    with pytest.raises(ValueError, match="Unsupported format"):
        export_statistics(sample_stats, output_file, format_type="txt")


def test_export_statistics_case_insensitive(
    sample_stats: MapStatistics,
    tmp_path: Path,
) -> None:
    """Test that format type is case-insensitive."""
    output_file = tmp_path / "output.xml"

    export_statistics(sample_stats, output_file, format_type="XML")

    assert output_file.exists()


def test_xml_item_frequency_sorting(
    sample_stats: MapStatistics,
    tmp_path: Path,
) -> None:
    """Test that floors are included in XML."""
    output_file = tmp_path / "stats.xml"

    export_to_xml(sample_stats, output_file)

    tree = ET.parse(output_file)
    root = tree.getroot()

    floors = root.find("floors")
    assert floors is not None

    floor_items = floors.findall("floor")
    # Should have 16 floors
    assert len(floor_items) == 16
    # First floor should have level 0
    assert floor_items[0].get("level") == "0"


def test_csv_includes_all_categories(
    sample_stats: MapStatistics,
    tmp_path: Path,
) -> None:
    """Test that CSV includes all statistic categories."""
    output_file = tmp_path / "stats.csv"

    export_to_csv(sample_stats, output_file)

    with output_file.open(encoding="utf-8") as csvfile:
        content = csvfile.read()

    assert "Basic" in content
    assert "Creatures" in content
    assert "Features" in content
    assert "Special Items" in content
    assert "Floors" in content


def test_json_structure(sample_stats: MapStatistics, tmp_path: Path) -> None:
    """Test JSON output structure."""
    output_file = tmp_path / "stats.json"

    export_to_json(sample_stats, output_file)

    with output_file.open(encoding="utf-8") as jsonfile:
        data = json.load(jsonfile)

    # Check all expected fields
    expected_fields = [
        "total_tiles",
        "total_items",
        "unique_items",
        "total_monsters",
        "unique_monsters",
        "total_npcs",
        "unique_npcs",
        "total_spawns",
        "total_houses",
        "items_with_action_id",
        "items_with_unique_id",
        "teleport_count",
        "container_count",
        "depot_count",
        "door_count",
        "waypoint_count",
        "tiles_per_floor",
    ]

    for field in expected_fields:
        assert field in data


def test_export_with_empty_item_frequency(tmp_path: Path) -> None:
    """Test export with minimal data."""
    stats = MapStatistics(
        total_tiles=100,
        total_items=0,
        unique_items=0,
        total_monsters=0,
        unique_monsters=0,
        total_npcs=0,
        unique_npcs=0,
        total_spawns=0,
        total_houses=0,
        items_with_action_id=0,
        items_with_unique_id=0,
        teleport_count=0,
        container_count=0,
        depot_count=0,
        door_count=0,
        waypoint_count=0,
        tiles_per_floor=(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    )

    output_file = tmp_path / "empty_stats.json"
    export_to_json(stats, output_file)

    assert output_file.exists()
