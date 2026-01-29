"""Tests for creature database loader."""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from py_rme_canary.core.assets.creatures_loader import (
    CreatureDatabase,
    CreatureDefinition,
    load_all_creatures,
    load_creatures_xml,
)
from py_rme_canary.core.data.creature import Outfit


@pytest.fixture
def tmp_monsters_xml(tmp_path: Path) -> Path:
    """Create temporary monsters.xml file."""
    xml_content = dedent(
        """
        <?xml version="1.0" encoding="UTF-8"?>
        <monsters>
            <monster name="Dragon" looktype="39"/>
            <monster name="Achad" looktype="146" lookhead="95" lookbody="93"
                     looklegs="38" lookfeet="59" lookaddons="3"/>
            <monster name="A Shielded Astral Glyph" lookitem="24226"/>
            <monster name="Rat" looktype="21" lookhead="20" lookbody="30" looklegs="40" lookfeet="50"/>
        </monsters>
    """
    ).strip()

    xml_file = tmp_path / "monsters.xml"
    xml_file.write_text(xml_content, encoding="utf-8")
    return xml_file


@pytest.fixture
def tmp_npcs_xml(tmp_path: Path) -> Path:
    """Create temporary npcs.xml file."""
    xml_content = dedent(
        """
        <?xml version="1.0" encoding="UTF-8"?>
        <npcs>
            <npc name="Sam" looktype="128" lookhead="20" lookbody="30" looklegs="40" lookfeet="50"/>
            <npc name="Norma" looktype="140" lookhead="0" lookbody="0" looklegs="0" lookfeet="0"/>
        </npcs>
    """
    ).strip()

    xml_file = tmp_path / "npcs.xml"
    xml_file.write_text(xml_content, encoding="utf-8")
    return xml_file


@pytest.fixture
def tmp_legacy_xml(tmp_path: Path) -> Path:
    """Create temporary legacy RME creatures.xml file."""
    xml_content = dedent(
        """
        <?xml version="1.0" encoding="UTF-8"?>
        <creatures>
            <creature name="Dragon" type="monster" looktype="39"/>
            <creature name="Sam" type="npc" looktype="128" lookhead="20"/>
        </creatures>
    """
    ).strip()

    xml_file = tmp_path / "creatures.xml"
    xml_file.write_text(xml_content, encoding="utf-8")
    return xml_file


def test_creature_database_add_and_get() -> None:
    """Test adding and retrieving creatures."""
    db = CreatureDatabase()

    outfit = Outfit(looktype=39)
    creature = CreatureDefinition(name="Dragon", creature_type="monster", outfit=outfit)

    db.add(creature)

    assert len(db) == 1
    assert "Dragon" in db
    assert "dragon" in db  # Case-insensitive
    assert db.get("Dragon") == creature
    assert db.get("DRAGON") == creature


def test_creature_database_get_monsters_and_npcs() -> None:
    """Test filtering by creature type."""
    db = CreatureDatabase()

    db.add(CreatureDefinition("Dragon", "monster", Outfit(looktype=39)))
    db.add(CreatureDefinition("Rat", "monster", Outfit(looktype=21)))
    db.add(CreatureDefinition("Sam", "npc", Outfit(looktype=128)))

    monsters = db.get_monsters()
    npcs = db.get_npcs()

    assert len(monsters) == 2
    assert len(npcs) == 1
    assert all(c.creature_type == "monster" for c in monsters)
    assert all(c.creature_type == "npc" for c in npcs)


def test_load_monsters_xml(tmp_monsters_xml: Path) -> None:
    """Test loading TFS/Canary monsters.xml."""
    db = load_creatures_xml(tmp_monsters_xml, "monster")

    assert len(db) == 4
    assert "Dragon" in db
    assert "Achad" in db

    # Check looktype
    dragon = db.get("Dragon")
    assert dragon is not None
    assert dragon.outfit.looktype == 39
    assert dragon.outfit.has_looktype
    assert not dragon.outfit.has_lookitem

    # Check lookitem
    glyph = db.get("A Shielded Astral Glyph")
    assert glyph is not None
    assert glyph.outfit.lookitem == 24226
    assert not glyph.outfit.has_looktype
    assert glyph.outfit.has_lookitem

    # Check colors and addons
    achad = db.get("Achad")
    assert achad is not None
    assert achad.outfit.looktype == 146
    assert achad.outfit.lookhead == 95
    assert achad.outfit.lookbody == 93
    assert achad.outfit.looklegs == 38
    assert achad.outfit.lookfeet == 59
    assert achad.outfit.lookaddons == 3


def test_load_npcs_xml(tmp_npcs_xml: Path) -> None:
    """Test loading TFS/Canary npcs.xml."""
    db = load_creatures_xml(tmp_npcs_xml, "npc")

    assert len(db) == 2
    assert "Sam" in db
    assert "Norma" in db

    sam = db.get("Sam")
    assert sam is not None
    assert sam.creature_type == "npc"
    assert sam.outfit.looktype == 128
    assert sam.outfit.lookhead == 20


def test_load_legacy_xml(tmp_legacy_xml: Path) -> None:
    """Test loading legacy RME creatures.xml format."""
    db = load_creatures_xml(tmp_legacy_xml, "monster")

    assert len(db) == 2
    assert "Dragon" in db
    assert "Sam" in db

    dragon = db.get("Dragon")
    assert dragon is not None
    assert dragon.creature_type == "monster"

    sam = db.get("Sam")
    assert sam is not None
    assert sam.creature_type == "npc"


def test_load_all_creatures(tmp_monsters_xml: Path, tmp_npcs_xml: Path) -> None:
    """Test loading both monsters and NPCs."""
    db = load_all_creatures(tmp_monsters_xml, tmp_npcs_xml)

    assert len(db) == 6  # 4 monsters + 2 NPCs

    monsters = db.get_monsters()
    npcs = db.get_npcs()

    assert len(monsters) == 4
    assert len(npcs) == 2


def test_load_missing_file() -> None:
    """Test handling of missing XML file."""
    with pytest.raises(FileNotFoundError):
        load_creatures_xml(Path("/nonexistent/file.xml"))


def test_load_all_creatures_missing_files() -> None:
    """Test load_all_creatures with missing files (should not raise)."""
    db = load_all_creatures(
        Path("/nonexistent/monsters.xml"),
        Path("/nonexistent/npcs.xml"),
    )

    # Should return empty database without errors
    assert len(db) == 0


def test_outfit_properties() -> None:
    """Test Outfit dataclass properties."""
    # Outfit with looktype
    outfit1 = Outfit(looktype=39, lookhead=10, lookbody=20)
    assert outfit1.has_looktype
    assert not outfit1.has_lookitem
    assert outfit1.looktype == 39

    # Outfit with lookitem
    outfit2 = Outfit(lookitem=12345)
    assert not outfit2.has_looktype
    assert outfit2.has_lookitem
    assert outfit2.lookitem == 12345

    # Empty outfit
    outfit3 = Outfit()
    assert not outfit3.has_looktype
    assert not outfit3.has_lookitem
