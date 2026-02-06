"""
Brush Management System - Intelligent, Version-Aware Brush Definition Loading
Automatically detects Tibia version (ServerID vs ClientID) and loads appropriate brushes
"""

import contextlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from py_rme_canary.core.io.xml.safe import safe_etree as ET


class BrushType(Enum):
    """All supported brush types based on RME architecture"""

    GROUND = "ground"
    WALL = "wall"
    CARPET = "carpet"
    DOODAD = "doodad"
    DOOR = "door"
    HOUSE = "house"
    SPAWN = "spawn"
    CREATURE = "creature"
    WAYPOINT = "waypoint"
    FLAG = "flag"
    ERASER = "eraser"
    RAW = "raw"
    BORDER = "border"
    BORDER_TOOL = "border_tool"


class TibiaVersion(Enum):
    """Tibia version timeline with format detection"""

    V740 = ("740", "traditional", True, 0)
    V800 = ("800", "traditional", True, 0)
    V840 = ("840", "traditional", True, 1)
    V860 = ("860", "traditional", True, 1)
    V910 = ("910", "traditional", True, 2)
    V920 = ("920", "traditional", True, 2)
    V946 = ("946", "traditional", True, 2)
    V960 = ("960", "traditional", True, 2)
    V986 = ("986", "traditional", True, 3)
    V1010 = ("1010", "traditional", True, 3)
    V1098 = ("1098", "traditional", True, 4)
    V1271 = ("1271", "canary", False, 5)
    V1310 = ("1310", "canary", False, 5)
    V1320 = ("1320", "canary", False, 5)
    V1330 = ("1330", "canary", False, 6)

    def __init__(self, version_str: str, format_type: str, uses_server_id: bool, otbm_version: int) -> None:
        self.version_str = version_str
        self.format_type = format_type  # "traditional" or "canary"
        self.uses_server_id = uses_server_id
        self.otbm_version = otbm_version


@dataclass
class BrushItem:
    """Individual item in a brush (with chance for randomization)"""

    item_id: int
    chance: int = 100

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BrushBorder:
    """Border configuration for a brush"""

    position: str  # "CENTER", "NORTH", "EAST", "SOUTH", "WEST", etc.
    item_id: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BrushDefinition:
    """Complete brush definition with version-aware IDs"""

    name: str
    brush_type: BrushType
    items: list[BrushItem] = field(default_factory=list)
    borders: dict[str, int] = field(default_factory=dict)

    # Version-specific IDs
    server_id: int | None = None  # Traditional format (OTBM 0-4)
    client_id: int | None = None  # Canary format (OTBM 5+)

    # Additional metadata
    draggable: bool = False
    on_blocking: bool = False
    thickness: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "name": self.name,
            "type": self.brush_type.value,
            "items": [item.to_dict() for item in self.items],
            "borders": self.borders,
            "server_id": self.server_id,
            "client_id": self.client_id,
            "draggable": self.draggable,
            "on_blocking": self.on_blocking,
            "thickness": self.thickness,
        }

    def get_id_for_version(self, tibia_version: TibiaVersion) -> int | None:
        """Get appropriate ID for given Tibia version"""
        if tibia_version.uses_server_id:
            return self.server_id
        else:
            return self.client_id if self.client_id else self.server_id


class BrushXMLParser:
    """Parse RME brush XML definitions"""

    def __init__(self, rme_brushs_path: str):
        self.brushs_path = Path(rme_brushs_path)
        self.brushes: list[BrushDefinition] = []

    def parse_all(self) -> list[BrushDefinition]:
        """Parse all brush XML files from RME directory"""
        all_brushes: list[BrushDefinition] = []

        if not self.brushs_path.exists():
            print(f"Warning: Brushs path not found: {self.brushs_path}")
            return all_brushes

        # Map XML file names to brush types
        file_to_type = {
            "grounds.xml": BrushType.GROUND,
            "walls.xml": BrushType.WALL,
            "brushes.xml": BrushType.DOODAD,
            "grass.xml": BrushType.GROUND,
            "flowers.xml": BrushType.DOODAD,
            "plants.xml": BrushType.DOODAD,
            "trees.xml": BrushType.DOODAD,
            "stones.xml": BrushType.DOODAD,
            "animals.xml": BrushType.DOODAD,
            "decorations.xml": BrushType.DOODAD,
            "constructions.xml": BrushType.DOODAD,
            "holes.xml": BrushType.GROUND,
            "fields.xml": BrushType.GROUND,
            "doodads.xml": BrushType.DOODAD,
            "statues.xml": BrushType.DOODAD,
            "natural_products.xml": BrushType.DOODAD,
            "tiny_borders.xml": BrushType.BORDER,
        }

        for xml_file, brush_type in file_to_type.items():
            xml_path = self.brushs_path / xml_file
            if xml_path.exists():
                try:
                    brushes = self._parse_xml_file(xml_path, brush_type)
                    all_brushes.extend(brushes)
                    print(f"  [OK] Loaded {len(brushes)} brushes from {xml_file}")
                except Exception as e:
                    print(f"  [ERR] Error parsing {xml_file}: {e}")

        self.brushes = all_brushes
        return all_brushes

    def _parse_xml_file(self, xml_path: Path, brush_type: BrushType) -> list[BrushDefinition]:
        """Parse a single brush XML file"""
        brushes: list[BrushDefinition] = []

        try:
            # Try to parse with error handling for malformed XML
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError:
            # Handle malformed XML by reading and trying to fix
            return brushes

        for brush_elem in root.findall("brush"):
            try:
                brush = self._parse_brush_element(brush_elem, brush_type)
                if brush:
                    brushes.append(brush)
            except Exception as e:
                print(f"    Warning: Could not parse brush element: {e}")

        return brushes

    def _parse_brush_element(self, elem: ET.Element, brush_type: BrushType) -> BrushDefinition | None:
        """Parse a single brush XML element"""
        name = elem.get("name")
        if not name:
            return None

        # Parse IDs - prefer lookid (ClientID) but also accept server_lookid (ServerID)
        client_id: int | None = None
        server_id: int | None = None

        lookid = elem.get("lookid")
        if lookid:
            with contextlib.suppress(ValueError):
                client_id = int(lookid)

        server_lookid = elem.get("server_lookid")
        if server_lookid:
            with contextlib.suppress(ValueError):
                server_id = int(server_lookid)

        # If only one ID is present, use it for both (version compatibility)
        if client_id and not server_id:
            server_id = client_id
        elif server_id and not client_id:
            client_id = server_id

        # Parse items
        items = []
        for item_elem in elem.findall("item"):
            try:
                item_id = int(item_elem.get("id", "0"))
                chance = int(item_elem.get("chance", "100"))
                items.append(BrushItem(item_id=item_id, chance=chance))
            except (ValueError, TypeError):
                pass

        # Parse borders (if any)
        borders = {}
        for border_elem in elem.findall("border"):
            try:
                pos = border_elem.get("name", "").upper()
                bid = int(border_elem.get("id", "0"))
                if pos and bid > 0:
                    borders[pos] = bid
            except (ValueError, TypeError):
                pass

        # Create brush definition
        brush = BrushDefinition(
            name=name,
            brush_type=brush_type,
            items=items,
            borders=borders,
            server_id=server_id,
            client_id=client_id,
            draggable=elem.get("draggable", "false").lower() == "true",
            on_blocking=elem.get("on_blocking", "false").lower() == "true",
            thickness=elem.get("thickness"),
        )

        return brush


class BrushJsonGenerator:
    """Generate intelligent, version-aware brush.json from RME sources"""

    def __init__(self, rme_brushs_path: str, output_path: str | None = None):
        self.rme_brushs_path = rme_brushs_path
        self.output_path = output_path
        self.parser = BrushXMLParser(rme_brushs_path)

    def generate(self) -> dict[str, Any]:
        """Generate complete brush.json"""
        print("Generating intelligent brush.json...")

        # Parse all brushes from RME XMLs
        print("Step 1: Parsing RME brush XMLs...")
        brushes = self.parser.parse_all()
        print(f"  Total brushes loaded: {len(brushes)}\n")

        # Build metadata
        metadata = {
            "version": "3.0",
            "description": "Version-aware brush definitions with intelligent ServerID/ClientID detection",
            "supported_versions": [v.version_str for v in TibiaVersion],
            "generation_mode": "intelligent",
            "auto_detect": True,
            "generated_at": datetime.now().isoformat(),
            "total_brushes": len(brushes),
            "rme_source": self.rme_brushs_path,
        }

        # Build version mappings
        version_mappings = {}
        for tibia_version in TibiaVersion:
            version_mappings[tibia_version.version_str] = {
                "format": tibia_version.format_type,
                "uses_server_id": tibia_version.uses_server_id,
                "otbm_version": tibia_version.otbm_version,
                "timeline": self._get_timeline_for_version(tibia_version),
            }

        # Build brush list
        brush_list = []
        for brush in brushes:
            brush_dict = brush.to_dict()
            brush_list.append(brush_dict)

        # Compile final JSON
        result = {"metadata": metadata, "version_mappings": version_mappings, "brushes": brush_list}

        return result

    def _get_timeline_for_version(self, version: TibiaVersion) -> str:
        """Get timeline description for version"""
        timelines = {
            "740": "2003 - Original OTB 1.1",
            "800": "2004 - OTB 2.7",
            "840": "2004 - OTB 3.12",
            "860": "2004 - OTB 3.20",
            "910": "2004 - OTB 3.28",
            "920": "2004 - OTB 3.31",
            "946": "2004 - OTB 3.35",
            "960": "2004 - OTB 3.39",
            "986": "2004 - OTB 3.43",
            "1010": "2004 - OTB 3.50",
            "1098": "2004 - OTB 3.59",
            "1271": "2007 - OTB 3.65 (Canary Era)",
            "1310": "2007 - OTB 3.65 (Canary)",
            "1320": "2007 - OTB 3.65 (Canary)",
            "1330": "2008 - OTB 3.65 (Canary)",
        }
        return timelines.get(version.version_str, "Unknown")

    def save(self, output_path: str | None = None) -> str:
        """Save generated brush.json to file"""
        path = output_path or self.output_path
        if not path:
            raise ValueError("Output path must be specified")

        json_data = self.generate()

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVED] Brush.json saved to: {path}")
        print(f"  File size: {os.path.getsize(path)} bytes")

        return path


def create_intelligent_brushes(
    rme_path: str | None = None, output_path: str | None = None, save_to_file: bool = True
) -> dict[str, Any]:
    """
    Main entry point: Create intelligent brush system

    Args:
        rme_path: Path to RME brushs directory
        output_path: Output path for brush.json
        save_to_file: Whether to save to file

    Returns:
        Generated brush dictionary
    """
    # Use defaults if not provided
    if not rme_path:
        rme_path = "Remeres-map-editor-linux-4.0.0/data/materials/brushs"

    if not output_path:
        output_path = "py_rme_canary/data/brushes.json"

    # Generate
    generator = BrushJsonGenerator(rme_path, output_path)
    result = generator.generate()

    # Save if requested
    if save_to_file:
        generator.save(output_path)

    return result


if __name__ == "__main__":
    # Generate and save intelligent brushes
    create_intelligent_brushes()
