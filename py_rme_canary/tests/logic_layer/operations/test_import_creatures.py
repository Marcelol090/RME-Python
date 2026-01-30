"""Tests for creature import functionality."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from py_rme_canary.core.assets.creatures_loader import CreatureDatabase
from py_rme_canary.logic_layer.operations.import_creatures import (
    ImportResult,
    find_creature_xml_files,
    generate_import_report,
    import_creatures_from_directory,
)


@pytest.fixture
def temp_creature_dir(tmp_path: Path) -> Path:
    """Create temporary directory structure with creature XMLs."""
    # Create nested structure
    monsters_dir = tmp_path / "data" / "monster" / "bosses"
    npcs_dir = tmp_path / "data" / "npc" / "town"

    monsters_dir.mkdir(parents=True)
    npcs_dir.mkdir(parents=True)

    # Create monsters.xml
    monsters_xml = dedent(
        """
        <?xml version="1.0" encoding="UTF-8"?>
        <monsters>
            <monster name="Dragon" looktype="39"/>
            <monster name="Demon" looktype="35"/>
        </monsters>
    """
    ).strip()

    (monsters_dir / "monsters.xml").write_text(monsters_xml, encoding="utf-8")

    # Create npcs.xml
    npcs_xml = dedent(
        """
        <?xml version="1.0" encoding="UTF-8"?>
        <npcs>
            <npc name="Sam" looktype="128"/>
            <npc name="Tom" looktype="129"/>
        </npcs>
    """
    ).strip()

    (npcs_dir / "npcs.xml").write_text(npcs_xml, encoding="utf-8")

    return tmp_path


def test_find_creature_xml_files(temp_creature_dir: Path) -> None:
    """Test recursive XML file discovery."""
    monster_files, npc_files = find_creature_xml_files(temp_creature_dir)

    assert len(monster_files) == 1
    assert len(npc_files) == 1
    assert monster_files[0].name == "monsters.xml"
    assert npc_files[0].name == "npcs.xml"


def test_find_in_nonexistent_directory() -> None:
    """Test handling of nonexistent directory."""
    monster_files, npc_files = find_creature_xml_files(Path("/nonexistent/path"))

    assert len(monster_files) == 0
    assert len(npc_files) == 0


def test_import_creatures_from_directory(temp_creature_dir: Path) -> None:
    """Test importing creatures from directory tree."""
    database = CreatureDatabase()

    result = import_creatures_from_directory(temp_creature_dir, database)

    assert result.monsters_loaded == 2
    assert result.npcs_loaded == 2
    assert len(result.files_processed) == 2
    assert len(result.errors) == 0

    # Verify creatures are in database
    assert "Dragon" in database
    assert "Demon" in database
    assert "Sam" in database
    assert "Tom" in database


def test_import_with_errors(tmp_path: Path) -> None:
    """Test handling of malformed XML files."""
    # Create invalid XML
    bad_xml = tmp_path / "monsters.xml"
    bad_xml.write_text("<<INVALID XML>>", encoding="utf-8")

    database = CreatureDatabase()
    result = import_creatures_from_directory(tmp_path, database)

    assert result.monsters_loaded == 0
    assert len(result.errors) > 0


def test_import_into_existing_database(temp_creature_dir: Path) -> None:
    """Test importing into database with existing creatures."""
    from py_rme_canary.core.assets.creatures_loader import CreatureDefinition
    from py_rme_canary.core.data.creature import Outfit

    database = CreatureDatabase()

    # Add existing creature
    existing = CreatureDefinition("Existing", "monster", Outfit(looktype=1))
    database.add(existing)

    result = import_creatures_from_directory(temp_creature_dir, database)

    # Should add new creatures without affecting existing
    assert result.monsters_loaded == 2
    assert result.npcs_loaded == 2
    assert "Existing" in database
    assert "Dragon" in database


def test_generate_import_report() -> None:
    """Test import report generation."""
    result = ImportResult(
        monsters_loaded=10,
        npcs_loaded=5,
        files_processed=["monsters.xml", "npcs.xml"],
        errors=["error1.xml: Parse error"],
    )

    report = generate_import_report(result)

    assert "Monsters loaded: 10" in report
    assert "NPCs loaded: 5" in report
    assert "Files processed: 2" in report
    assert "Errors: 1" in report
    assert "error1.xml: Parse error" in report


def test_import_result_immutability() -> None:
    """Test that ImportResult is immutable."""
    result = ImportResult(
        monsters_loaded=1,
        npcs_loaded=1,
        files_processed=["test.xml"],
        errors=[],
    )

    with pytest.raises(AttributeError):
        result.monsters_loaded = 999  # type: ignore[misc]


def test_multiple_xml_files_same_directory(tmp_path: Path) -> None:
    """Test handling multiple creature files in same directory."""
    # Create first monsters.xml
    (tmp_path / "monsters.xml").write_text(
        dedent(
            """
            <?xml version="1.0" encoding="UTF-8"?>
            <monsters>
                <monster name="Rat" looktype="21"/>
            </monsters>
        """
        ).strip(),
        encoding="utf-8",
    )

    # Create subdirectory with another monsters.xml
    subdir = tmp_path / "bosses"
    subdir.mkdir()
    (subdir / "monsters.xml").write_text(
        dedent(
            """
            <?xml version="1.0" encoding="UTF-8"?>
            <monsters>
                <monster name="Dragon" looktype="39"/>
            </monsters>
        """
        ).strip(),
        encoding="utf-8",
    )

    database = CreatureDatabase()
    result = import_creatures_from_directory(tmp_path, database)

    # Should load from both files
    assert result.monsters_loaded == 2
    assert "Rat" in database
    assert "Dragon" in database
