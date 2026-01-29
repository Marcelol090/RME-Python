"""Export map statistics to various formats.

Exports map statistics (already calculated by map_statistics.py) to:
- XML format
- CSV format
- JSON format
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

if TYPE_CHECKING:
    from py_rme_canary.logic_layer.map_statistics import MapStatistics


def export_to_xml(stats: MapStatistics, output_path: Path) -> None:
    """Export statistics to XML format.

    Args:
        stats: MapStatistics object to export
        output_path: Destination XML file path

    Example:
        >>> from pathlib import Path
        >>> export_to_xml(stats, Path("map_stats.xml"))
    """
    root = ET.Element("map_statistics")

    # Basic counts
    basic = ET.SubElement(root, "basic")
    ET.SubElement(basic, "total_tiles").text = str(stats.total_tiles)
    ET.SubElement(basic, "total_items").text = str(stats.total_items)
    ET.SubElement(basic, "unique_items").text = str(stats.unique_items)

    # Creatures
    creatures = ET.SubElement(root, "creatures")
    ET.SubElement(creatures, "total_monsters").text = str(stats.total_monsters)
    ET.SubElement(creatures, "unique_monsters").text = str(stats.unique_monsters)
    ET.SubElement(creatures, "total_npcs").text = str(stats.total_npcs)
    ET.SubElement(creatures, "unique_npcs").text = str(stats.unique_npcs)
    ET.SubElement(creatures, "total_spawns").text = str(stats.total_spawns)

    # Map features
    features = ET.SubElement(root, "features")
    ET.SubElement(features, "total_houses").text = str(stats.total_houses)
    ET.SubElement(features, "waypoint_count").text = str(stats.waypoint_count)
    ET.SubElement(features, "teleport_count").text = str(stats.teleport_count)
    ET.SubElement(features, "container_count").text = str(stats.container_count)
    ET.SubElement(features, "depot_count").text = str(stats.depot_count)
    ET.SubElement(features, "door_count").text = str(stats.door_count)

    # Special item counts
    special = ET.SubElement(root, "special_items")
    ET.SubElement(special, "items_with_action_id").text = str(
        stats.items_with_action_id,
    )
    ET.SubElement(special, "items_with_unique_id").text = str(
        stats.items_with_unique_id,
    )

    # Tiles per floor
    floors = ET.SubElement(root, "floors")
    for floor_idx, count in enumerate(stats.tiles_per_floor):
        floor_elem = ET.SubElement(floors, "floor")
        floor_elem.set("level", str(floor_idx))
        floor_elem.text = str(count)

    # Write to file with pretty formatting
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(output_path, encoding="utf-8", xml_declaration=True)



def export_to_csv(stats: MapStatistics, output_path: Path) -> None:
    """Export statistics to CSV format.

    Args:
        stats: MapStatistics object to export
        output_path: Destination CSV file path

    Example:
        >>> from pathlib import Path
        >>> export_to_csv(stats, Path("map_stats.csv"))
    """
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(["Category", "Metric", "Value"])

        # Basic statistics
        writer.writerow(["Basic", "Total Tiles", stats.total_tiles])
        writer.writerow(["Basic", "Total Items", stats.total_items])
        writer.writerow(["Basic", "Unique Items", stats.unique_items])

        # Creatures
        writer.writerow(["Creatures", "Total Monsters", stats.total_monsters])
        writer.writerow(["Creatures", "Unique Monsters", stats.unique_monsters])
        writer.writerow(["Creatures", "Total NPCs", stats.total_npcs])
        writer.writerow(["Creatures", "Unique NPCs", stats.unique_npcs])
        writer.writerow(["Creatures", "Total Spawns", stats.total_spawns])

        # Map features
        writer.writerow(["Features", "Total Houses", stats.total_houses])
        writer.writerow(["Features", "Waypoint Count", stats.waypoint_count])
        writer.writerow(["Features", "Teleport Count", stats.teleport_count])
        writer.writerow(["Features", "Container Count", stats.container_count])
        writer.writerow(["Features", "Depot Count", stats.depot_count])
        writer.writerow(["Features", "Door Count", stats.door_count])

        # Special items
        writer.writerow(
            ["Special Items", "Items with Action ID", stats.items_with_action_id],
        )
        writer.writerow(
            ["Special Items", "Items with Unique ID", stats.items_with_unique_id],
        )

        # Blank line before floors
        writer.writerow([])
        writer.writerow(["Floors", "Floor Level", "Tile Count"])

        # Tiles per floor
        for floor_idx, count in enumerate(stats.tiles_per_floor):
            writer.writerow(["Floors", floor_idx, count])


def export_to_json(stats: MapStatistics, output_path: Path) -> None:
    """Export statistics to JSON format.

    Args:
        stats: MapStatistics object to export
        output_path: Destination JSON file path

    Example:
        >>> from pathlib import Path
        >>> export_to_json(stats, Path("map_stats.json"))
    """
    # Convert dataclass to dict
    stats_dict = asdict(stats)

    with output_path.open("w", encoding="utf-8") as jsonfile:
        json.dump(stats_dict, jsonfile, indent=2, ensure_ascii=False)


def export_statistics(
    stats: MapStatistics,
    output_path: Path,
    *,
    format_type: str = "xml",
) -> None:
    """Export map statistics to file in specified format.

    Args:
        stats: MapStatistics object to export
        output_path: Destination file path
        format_type: Export format ("xml", "csv", or "json")

    Raises:
        ValueError: If format_type is not supported

    Example:
        >>> from pathlib import Path
        >>> export_statistics(stats, Path("output.xml"), format_type="xml")
    """
    format_type = format_type.lower()

    if format_type == "xml":
        export_to_xml(stats, output_path)
    elif format_type == "csv":
        export_to_csv(stats, output_path)
    elif format_type == "json":
        export_to_json(stats, output_path)
    else:
        msg = f"Unsupported format: {format_type}. Use 'xml', 'csv', or 'json'"
        raise ValueError(msg)
