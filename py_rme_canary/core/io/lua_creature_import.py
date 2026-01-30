from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast
from xml.etree.ElementTree import Element

from py_rme_canary.core.io.creatures_xml import default_monsters_path, default_npcs_path
from py_rme_canary.core.io.xml.safe import SubElement
from py_rme_canary.core.io.xml.safe import safe_etree as ET


@dataclass(slots=True)
class CreatureOutfit:
    look_type: int = 0
    look_head: int = 0
    look_body: int = 0
    look_legs: int = 0
    look_feet: int = 0
    look_addons: int = 0
    look_mount: int = 0

    def is_empty(self) -> bool:
        return not any(
            (
                self.look_type,
                self.look_head,
                self.look_body,
                self.look_legs,
                self.look_feet,
                self.look_addons,
                self.look_mount,
            )
        )


@dataclass(slots=True)
class CreatureDefinition:
    name: str
    kind: Literal["monster", "npc"]
    outfit: CreatureOutfit
    source_path: Path | None = None


@dataclass(slots=True)
class LuaCreatureImportResult:
    files_scanned: int = 0
    monsters_added: int = 0
    monsters_updated: int = 0
    npcs_added: int = 0
    npcs_updated: int = 0

    @property
    def total_imported(self) -> int:
        return self.monsters_added + self.monsters_updated + self.npcs_added + self.npcs_updated


_CREATE_RE = re.compile(
    r"Game\.create(?P<kind>Monster|Npc)Type\s*\(\s*(?P<quote>['\"])(?P<name>.*?)\2\s*\)",
    re.IGNORECASE | re.DOTALL,
)

_OUTFIT_FIELDS = {
    "looktype": "look_type",
    "lookhead": "look_head",
    "lookbody": "look_body",
    "looklegs": "look_legs",
    "lookfeet": "look_feet",
    "lookaddons": "look_addons",
    "lookmount": "look_mount",
    "looktypeex": "look_type_ex",
}

_FIELD_RE = re.compile(r"(\w+)\s*=\s*([+-]?(?:0x[0-9a-fA-F]+|\d+))")


def _strip_lua_comments(text: str) -> str:
    text = re.sub(r"--\[\[.*?\]\]", "", text, flags=re.DOTALL)
    text = re.sub(r"--.*?$", "", text, flags=re.MULTILINE)
    return text


def _find_outfit_block(text: str, kind: str) -> str | None:
    kind = (kind or "").strip().lower()
    var = "monster" if kind == "monster" else "npc"
    patterns = [
        rf"{var}\.outfit\s*=\s*{{(.*?)}}",
        r"outfit\s*=\s*{(.*?)}",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.DOTALL)
        if match:
            return match.group(1)
    return None


def _parse_outfit_block(block: str) -> CreatureOutfit:
    values: dict[str, int] = {}
    for key, raw in _FIELD_RE.findall(block or ""):
        key_lower = str(key or "").strip().lower()
        if not key_lower:
            continue
        try:
            num = int(str(raw), 0)
        except ValueError:
            continue
        values[key_lower] = num

    outfit = CreatureOutfit()
    look_type_ex = 0
    for raw_key, value in values.items():
        mapped = _OUTFIT_FIELDS.get(raw_key)
        if mapped is None:
            continue
        if mapped == "look_type_ex":
            look_type_ex = int(value)
            continue
        setattr(outfit, mapped, int(value))

    if outfit.look_type == 0 and look_type_ex:
        outfit.look_type = int(look_type_ex)
    return outfit


def parse_lua_creatures_text(text: str, *, source_path: Path | None = None) -> list[CreatureDefinition]:
    cleaned = _strip_lua_comments(text or "")
    results: list[CreatureDefinition] = []
    for match in _CREATE_RE.finditer(cleaned):
        kind = str(match.group("kind") or "").strip().lower()
        name = str(match.group("name") or "").strip()
        if not name or kind not in ("monster", "npc"):
            continue
        outfit_block = _find_outfit_block(cleaned, kind)
        if not outfit_block:
            continue
        outfit = _parse_outfit_block(outfit_block)
        if outfit.is_empty():
            continue
        results.append(
            CreatureDefinition(
                name=name,
                kind=cast(Literal["monster", "npc"], kind),
                outfit=outfit,
                source_path=source_path,
            )
        )
    return results


def parse_lua_creatures_file(path: str | Path) -> list[CreatureDefinition]:
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []
    return parse_lua_creatures_text(text, source_path=file_path)


def parse_lua_creatures_folder(path: str | Path, *, recursive: bool = True) -> tuple[list[CreatureDefinition], int]:
    base = Path(path)
    if not base.exists() or not base.is_dir():
        return [], 0
    files = sorted(base.rglob("*.lua") if recursive else base.glob("*.lua"))
    definitions: list[CreatureDefinition] = []
    for file_path in files:
        definitions.extend(parse_lua_creatures_file(file_path))
    return definitions, len(files)


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _load_or_create_root(path: Path, root_tag: str) -> Element:
    if not path.exists():
        return ET.Element(root_tag)
    try:
        root = ET.parse(path).getroot()
    except Exception as exc:
        raise ValueError(f"Failed to parse {path}") from exc
    if (root.tag or "").strip().lower() != root_tag.lower():
        raise ValueError(f"Invalid root tag in {path}: expected <{root_tag}>")
    return root


def _indent(elem: Element, level: int = 0) -> None:
    indent = "\n" + level * "\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = indent + "\t"
        for child in elem:
            _indent(child, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = indent


def _apply_outfit(elem: Element, outfit: CreatureOutfit) -> None:
    elem.set("lookType", str(int(outfit.look_type)))
    elem.set("lookHead", str(int(outfit.look_head)))
    elem.set("lookBody", str(int(outfit.look_body)))
    elem.set("lookLegs", str(int(outfit.look_legs)))
    elem.set("lookFeet", str(int(outfit.look_feet)))
    elem.set("lookAddons", str(int(outfit.look_addons)))
    elem.set("lookMount", str(int(outfit.look_mount)))


def _merge_definitions_into_xml(
    path: Path,
    root_tag: str,
    child_tag: str,
    definitions: Iterable[CreatureDefinition],
) -> tuple[int, int]:
    items = list(definitions)
    if not items:
        return 0, 0
    root = _load_or_create_root(path, root_tag)
    existing: dict[str, Element] = {}
    for child in list(root):
        if (child.tag or "").strip().lower() != child_tag:
            continue
        name = str(child.attrib.get("name", "") or "").strip()
        if not name:
            continue
        existing[name.lower()] = child

    added = 0
    updated = 0
    for creature in items:
        key = creature.name.lower()
        if key in existing:
            elem = existing[key]
            updated += 1
        else:
            elem = SubElement(root, child_tag)
            existing[key] = elem
            added += 1
        elem.set("name", creature.name)
        _apply_outfit(elem, creature.outfit)

    _indent(root)
    _ensure_parent_dir(path)
    xml_text = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    path.write_bytes(xml_text)
    return added, updated


def import_lua_creatures_from_file(
    path: str | Path,
    *,
    monsters_path: str | Path | None = None,
    npcs_path: str | Path | None = None,
) -> LuaCreatureImportResult:
    definitions = parse_lua_creatures_file(path)
    return _import_definitions(
        definitions,
        files_scanned=1 if definitions or Path(path).exists() else 0,
        monsters_path=monsters_path,
        npcs_path=npcs_path,
    )


def import_lua_creatures_from_folder(
    path: str | Path,
    *,
    recursive: bool = True,
    monsters_path: str | Path | None = None,
    npcs_path: str | Path | None = None,
) -> LuaCreatureImportResult:
    definitions, file_count = parse_lua_creatures_folder(path, recursive=recursive)
    return _import_definitions(
        definitions,
        files_scanned=file_count,
        monsters_path=monsters_path,
        npcs_path=npcs_path,
    )


def _import_definitions(
    definitions: Iterable[CreatureDefinition],
    *,
    files_scanned: int,
    monsters_path: str | Path | None,
    npcs_path: str | Path | None,
) -> LuaCreatureImportResult:
    result = LuaCreatureImportResult(files_scanned=int(files_scanned))
    defs = list(definitions)
    if not defs:
        return result

    monsters = [d for d in defs if d.kind == "monster"]
    npcs = [d for d in defs if d.kind == "npc"]

    if monsters:
        path = default_monsters_path() if monsters_path is None else Path(monsters_path)
        added, updated = _merge_definitions_into_xml(path, "monsters", "monster", monsters)
        result.monsters_added = int(added)
        result.monsters_updated = int(updated)

    if npcs:
        path = default_npcs_path() if npcs_path is None else Path(npcs_path)
        added, updated = _merge_definitions_into_xml(path, "npcs", "npc", npcs)
        result.npcs_added = int(added)
        result.npcs_updated = int(updated)

    return result
