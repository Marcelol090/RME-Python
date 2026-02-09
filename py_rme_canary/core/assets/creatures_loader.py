"""Creature database loader from TFS/Canary XML format.

Loads creature definitions from monsters.xml and npcs.xml files used by
TFS (The Forgotten Server) and Canary game servers. These files define
creature names, visual appearance (looktype/lookitem), and outfit colors.

XML Format Examples:
    <monster name="Dragon" looktype="39"/>
    <monster name="Achad" looktype="146" lookhead="95" lookbody="93" looklegs="38" lookfeet="59" lookaddons="3"/>
    <monster name="A Shielded Astral Glyph" lookitem="24226"/>
    <npc name="Sam" looktype="128" lookhead="20" lookbody="30" looklegs="40" lookfeet="50"/>

This module provides:
- CreatureDatabase: Registry of all creatures with lookup by name
- load_creatures_xml(): Parse TFS/Canary XML files
- Fallback support for legacy RME creatures.xml format
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from defusedxml import ElementTree as ET

if TYPE_CHECKING:
    pass

from py_rme_canary.core.data.creature import Outfit


@dataclass
class CreatureDefinition:
    """Creature metadata from XML.

    Stores creature name, type (monster/npc), and visual appearance.
    Used to create Creature instances with correct outfit data.
    """

    name: str
    creature_type: str  # "monster" or "npc"
    outfit: Outfit

    def __hash__(self) -> int:
        """Make hashable for set/dict usage."""
        return hash(self.name.lower())


@dataclass
class CreatureDatabase:
    """Registry of all loaded creatures.

    Provides fast lookup by name (case-insensitive) and iteration.
    Supports both TFS/Canary and legacy RME XML formats.
    """

    creatures: dict[str, CreatureDefinition] = field(default_factory=dict)

    def add(self, creature: CreatureDefinition) -> None:
        """Register a creature (overwrites if exists)."""
        self.creatures[creature.name.lower()] = creature

    def get(self, name: str) -> CreatureDefinition | None:
        """Look up creature by name (case-insensitive)."""
        return self.creatures.get(name.lower())

    def get_monsters(self) -> list[CreatureDefinition]:
        """Get all monsters."""
        return [c for c in self.creatures.values() if c.creature_type == "monster"]

    def get_npcs(self) -> list[CreatureDefinition]:
        """Get all NPCs."""
        return [c for c in self.creatures.values() if c.creature_type == "npc"]

    def get_all(self) -> list[CreatureDefinition]:
        """Get all creatures (both monsters and NPCs)."""
        return list(self.creatures.values())

    def __len__(self) -> int:
        """Get total creature count."""
        return len(self.creatures)

    def __contains__(self, name: str) -> bool:
        """Check if creature exists (case-insensitive)."""
        return name.lower() in self.creatures


def _parse_int(value: str | None, default: int = 0) -> int:
    """Safely parse integer from XML attribute."""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def load_creatures_xml(
    xml_path: Path,
    creature_type: str = "monster",
) -> CreatureDatabase:
    """Load creatures from TFS/Canary XML file.

    Args:
        xml_path: Path to monsters.xml or npcs.xml
        creature_type: "monster" or "npc"

    Returns:
        CreatureDatabase with all parsed creatures

    Raises:
        FileNotFoundError: If XML file doesn't exist
        ET.ParseError: If XML is malformed

    Examples:
        >>> db = load_creatures_xml(Path("data/monsters.xml"))
        >>> dragon = db.get("Dragon")
        >>> dragon.outfit.looktype
        39
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"Creatures XML not found: {xml_path}")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    if root is None:
        return CreatureDatabase()

    database = CreatureDatabase()

    # TFS/Canary format: <monsters> or <npcs> root element
    if root.tag in ("monsters", "npcs"):
        for elem in root.findall("monster") + root.findall("npc"):
            name = elem.get("name")
            if not name:
                continue

            # Parse outfit (looktype or lookitem)
            looktype = _parse_int(elem.get("looktype"))
            lookitem = _parse_int(elem.get("lookitem"))

            # Parse colors (0-132 range)
            lookhead = _parse_int(elem.get("lookhead"), 0)
            lookbody = _parse_int(elem.get("lookbody"), 0)
            looklegs = _parse_int(elem.get("looklegs"), 0)
            lookfeet = _parse_int(elem.get("lookfeet"), 0)
            lookaddons = _parse_int(elem.get("lookaddons"), 0)

            outfit = Outfit(
                looktype=looktype if looktype > 0 else None,
                lookitem=lookitem if lookitem > 0 else None,
                lookhead=lookhead,
                lookbody=lookbody,
                looklegs=looklegs,
                lookfeet=lookfeet,
                lookaddons=lookaddons,
            )

            # Determine type from element tag or parameter
            ctype = elem.tag if elem.tag in ("monster", "npc") else creature_type

            creature = CreatureDefinition(
                name=name,
                creature_type=ctype,
                outfit=outfit,
            )
            database.add(creature)

    # Legacy RME format: <creatures> root with type attribute
    elif root.tag == "creatures":
        for elem in root.findall("creature"):
            name = elem.get("name")
            ctype = elem.get("type", creature_type)
            if not name:
                continue

            looktype = _parse_int(elem.get("looktype"))
            lookitem = _parse_int(elem.get("lookitem"))
            lookhead = _parse_int(elem.get("lookhead"), 0)
            lookbody = _parse_int(elem.get("lookbody"), 0)
            looklegs = _parse_int(elem.get("looklegs"), 0)
            lookfeet = _parse_int(elem.get("lookfeet"), 0)
            lookaddons = _parse_int(elem.get("lookaddons"), 0)

            outfit = Outfit(
                looktype=looktype if looktype > 0 else None,
                lookitem=lookitem if lookitem > 0 else None,
                lookhead=lookhead,
                lookbody=lookbody,
                looklegs=looklegs,
                lookfeet=lookfeet,
                lookaddons=lookaddons,
            )

            creature = CreatureDefinition(
                name=name,
                creature_type=ctype,
                outfit=outfit,
            )
            database.add(creature)

    return database


def load_all_creatures(
    monsters_xml: Path | None = None,
    npcs_xml: Path | None = None,
) -> CreatureDatabase:
    """Load both monsters and NPCs from separate XML files.

    Args:
        monsters_xml: Path to monsters.xml (TFS/Canary format)
        npcs_xml: Path to npcs.xml (TFS/Canary format)

    Returns:
        Combined CreatureDatabase with all creatures

    Examples:
        >>> db = load_all_creatures(
        ...     Path("data/monsters.xml"),
        ...     Path("data/npcs.xml"),
        ... )
        >>> len(db)
        500
    """
    database = CreatureDatabase()

    if monsters_xml and monsters_xml.exists():
        try:
            monster_db = load_creatures_xml(monsters_xml, "monster")
            for creature in monster_db.creatures.values():
                database.add(creature)
        except Exception:
            # Silently ignore errors, continue with NPCs
            pass

    if npcs_xml and npcs_xml.exists():
        try:
            npc_db = load_creatures_xml(npcs_xml, "npc")
            for creature in npc_db.creatures.values():
                database.add(creature)
        except Exception:
            # Silently ignore errors
            pass

    return database
