from __future__ import annotations

from py_rme_canary.logic_layer.cross_clipboard import CrossClipboard, TranslationMapping, VersionTranslator


def test_cross_clipboard_translates_npc_and_spawn_npc_names() -> None:
    translator = VersionTranslator()
    translator.add_mapping(
        TranslationMapping(
            from_version="13.x",
            to_version="7.4",
            item_map={100: 200, 101: 201},
            creature_map={"Dragon": "Dragon Lord", "Sam": "Samuel"},
        )
    )

    clipboard = CrossClipboard()
    clipboard.set_translator(translator)

    source_tiles = [
        {
            "ground_id": 100,
            "items": [{"id": 101, "name": "sword"}],
            "monsters": [{"name": "Dragon"}],
            "npc": {"name": "Sam"},
            "spawn_monster": {"monsters": [{"name": "Dragon"}]},
            "spawn_npc": {"npcs": [{"name": "Sam"}]},
        }
    ]

    payload = clipboard.write_tiles(source_tiles, source_version="13.x")
    translated, source_version = clipboard.read_tiles(payload, target_version="7.4")

    assert source_version == "13.x"
    assert translated[0]["ground_id"] == 200
    assert translated[0]["items"][0]["id"] == 201
    assert translated[0]["monsters"][0]["name"] == "Dragon Lord"
    assert translated[0]["npc"]["name"] == "Samuel"
    assert translated[0]["spawn_monster"]["monsters"][0]["name"] == "Dragon Lord"
    assert translated[0]["spawn_npc"]["npcs"][0]["name"] == "Samuel"


def test_cross_clipboard_keeps_npc_names_without_mapping() -> None:
    translator = VersionTranslator()
    translator.add_mapping(
        TranslationMapping(
            from_version="13.x",
            to_version="7.4",
            item_map={},
            creature_map={},
        )
    )

    clipboard = CrossClipboard()
    clipboard.set_translator(translator)

    source_tiles = [{"npc": {"name": "Unknown NPC"}, "spawn_npc": {"npcs": [{"name": "Unknown NPC"}]}}]
    payload = clipboard.write_tiles(source_tiles, source_version="13.x")
    translated, _ = clipboard.read_tiles(payload, target_version="7.4")

    assert translated[0]["npc"]["name"] == "Unknown NPC"
    assert translated[0]["spawn_npc"]["npcs"][0]["name"] == "Unknown NPC"
