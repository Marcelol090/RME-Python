"""Import creatures and NPCs from TFS/Canary XML files.

Scans directories recursively for monsters.xml and npcs.xml files,
loads creature definitions, and makes them available for placement.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.core.assets.creatures_loader import CreatureDatabase


@dataclass(frozen=True, slots=True)
class ImportResult:
    """Result of creature import operation.

    Attributes:
        monsters_loaded: Number of monster definitions imported
        npcs_loaded: Number of NPC definitions imported
        files_processed: List of XML files that were processed
        errors: List of error messages for failed files
    """

    monsters_loaded: int
    npcs_loaded: int
    files_processed: list[str]
    errors: list[str]


def find_creature_xml_files(root_path: Path) -> tuple[list[Path], list[Path]]:
    """Recursively find all monsters.xml and npcs.xml files.

    Args:
        root_path: Root directory to search

    Returns:
        Tuple of (monster_files, npc_files) containing paths to XML files
    """
    monster_files: list[Path] = []
    npc_files: list[Path] = []

    if not root_path.exists() or not root_path.is_dir():
        return monster_files, npc_files

    # Search recursively
    for xml_file in root_path.rglob("*.xml"):
        filename = xml_file.name.lower()
        if filename == "monsters.xml":
            monster_files.append(xml_file)
        elif filename == "npcs.xml":
            npc_files.append(xml_file)

    return monster_files, npc_files


def import_creatures_from_directory(
    root_path: Path,
    database: CreatureDatabase,
) -> ImportResult:
    """Import all creatures from a directory tree.

    Recursively scans for monsters.xml and npcs.xml files and loads
    all creature definitions into the provided database.

    Args:
        root_path: Root directory to scan
        database: CreatureDatabase to populate with loaded creatures

    Returns:
        ImportResult with statistics and any errors encountered

    Example:
        >>> from pathlib import Path
        >>> from py_rme_canary.core.assets.creatures_loader import CreatureDatabase
        >>> db = CreatureDatabase()
        >>> result = import_creatures_from_directory(Path("data"), db)
        >>> print(f"Loaded {result.monsters_loaded} monsters, {result.npcs_loaded} NPCs")
    """
    from py_rme_canary.core.assets.creatures_loader import load_creatures_xml

    monster_files, npc_files = find_creature_xml_files(root_path)

    files_processed: list[str] = []
    errors: list[str] = []
    initial_monster_count = len(database.get_monsters())
    initial_npc_count = len(database.get_npcs())

    # Load monsters
    for monster_file in monster_files:
        try:
            temp_db = load_creatures_xml(monster_file, "monster")
            # Merge into main database
            for creature in temp_db.get_all():
                database.add(creature)
            files_processed.append(str(monster_file))
        except Exception as e:
            errors.append(f"{monster_file}: {e!s}")

    # Load NPCs
    for npc_file in npc_files:
        try:
            temp_db = load_creatures_xml(npc_file, "npc")
            # Merge into main database
            for creature in temp_db.get_all():
                database.add(creature)
            files_processed.append(str(npc_file))
        except Exception as e:
            errors.append(f"{npc_file}: {e!s}")

    # Calculate how many were added
    final_monster_count = len(database.get_monsters())
    final_npc_count = len(database.get_npcs())

    monsters_loaded = final_monster_count - initial_monster_count
    npcs_loaded = final_npc_count - initial_npc_count

    return ImportResult(
        monsters_loaded=monsters_loaded,
        npcs_loaded=npcs_loaded,
        files_processed=files_processed,
        errors=errors,
    )


def generate_import_report(result: ImportResult) -> str:
    """Generate human-readable import report.

    Args:
        result: ImportResult from import operation

    Returns:
        Formatted report string
    """
    lines = [
        "Creature Import Report",
        "=" * 50,
        "",
        f"Monsters loaded: {result.monsters_loaded}",
        f"NPCs loaded: {result.npcs_loaded}",
        f"Files processed: {len(result.files_processed)}",
        "",
    ]

    if result.errors:
        lines.append(f"Errors: {len(result.errors)}")
        lines.append("")
        lines.append("Error Details:")
        for error in result.errors:
            lines.append(f"  - {error}")
        lines.append("")

    lines.append("Successfully loaded creature definitions from:")
    for filepath in result.files_processed:
        lines.append(f"  - {filepath}")

    return "\n".join(lines)
