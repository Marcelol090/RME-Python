from __future__ import annotations

from pathlib import Path

from py_rme_canary.core.io.lua_creature_import import (
    import_lua_creatures_from_folder,
    parse_lua_creatures_text,
)
from py_rme_canary.core.io.xml.safe import Element
from py_rme_canary.core.io.xml.safe import safe_etree as ET


def test_parse_monster_outfit() -> None:
    text = """
local mType = Game.createMonsterType("Rat")
local monster = {}
monster.outfit = { lookType = 21, lookHead = 95, lookBody = 58, lookLegs = 76, lookFeet = 114, lookAddons = 1, lookMount = 0 }
mType:register(monster)
"""
    definitions = parse_lua_creatures_text(text)
    assert len(definitions) == 1
    creature = definitions[0]
    assert creature.kind == "monster"
    assert creature.name == "Rat"
    assert creature.outfit.look_type == 21
    assert creature.outfit.look_head == 95
    assert creature.outfit.look_body == 58
    assert creature.outfit.look_legs == 76
    assert creature.outfit.look_feet == 114
    assert creature.outfit.look_addons == 1
    assert creature.outfit.look_mount == 0


def test_parse_npc_outfit() -> None:
    text = """
local npcType = Game.createNpcType("Tom")
local npc = {}
npc.outfit = { lookType = 130, lookHead = 0, lookBody = 0, lookLegs = 0, lookFeet = 0, lookAddons = 0, lookMount = 0 }
npcType:register(npc)
"""
    definitions = parse_lua_creatures_text(text)
    assert len(definitions) == 1
    creature = definitions[0]
    assert creature.kind == "npc"
    assert creature.name == "Tom"
    assert creature.outfit.look_type == 130


def test_import_folder_merges_monsters_and_npcs(tmp_path: Path) -> None:
    monsters_path = tmp_path / "monsters.xml"
    npcs_path = tmp_path / "npcs.xml"

    root = Element("monsters")
    existing = ET.SubElement(root, "monster")
    existing.set("name", "Rat")
    existing.set("lookType", "1")
    monsters_path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))

    npcs_path.write_bytes(ET.tostring(Element("npcs"), encoding="utf-8", xml_declaration=True))

    folder = tmp_path / "lua"
    folder.mkdir()

    (folder / "rat.lua").write_text(
        """
local mType = Game.createMonsterType("Rat")
local monster = {}
monster.outfit = { lookType = 2, lookHead = 1, lookBody = 2, lookLegs = 3, lookFeet = 4, lookAddons = 5, lookMount = 6 }
mType:register(monster)
""",
        encoding="utf-8",
    )
    (folder / "cat.lua").write_text(
        """
local mType = Game.createMonsterType("Cat")
local monster = {}
monster.outfit = { lookType = 3, lookHead = 10, lookBody = 11, lookLegs = 12, lookFeet = 13, lookAddons = 14, lookMount = 15 }
mType:register(monster)
""",
        encoding="utf-8",
    )
    (folder / "tom.lua").write_text(
        """
local npcType = Game.createNpcType("Tom")
local npc = {}
npc.outfit = { lookType = 130, lookHead = 0, lookBody = 0, lookLegs = 0, lookFeet = 0, lookAddons = 0, lookMount = 0 }
npcType:register(npc)
""",
        encoding="utf-8",
    )

    result = import_lua_creatures_from_folder(
        folder,
        monsters_path=monsters_path,
        npcs_path=npcs_path,
    )

    assert result.files_scanned == 3
    assert result.monsters_added == 1
    assert result.monsters_updated == 1
    assert result.npcs_added == 1

    parsed = ET.parse(monsters_path).getroot()
    assert parsed.tag == "monsters"
    monsters = {m.get("name"): m for m in parsed.findall("monster")}
    assert set(monsters.keys()) == {"Rat", "Cat"}
    assert monsters["Rat"].get("lookType") == "2"
    assert monsters["Cat"].get("lookType") == "3"

    parsed_npcs = ET.parse(npcs_path).getroot()
    npcs = {n.get("name"): n for n in parsed_npcs.findall("npc")}
    assert set(npcs.keys()) == {"Tom"}
    assert npcs["Tom"].get("lookType") == "130"
