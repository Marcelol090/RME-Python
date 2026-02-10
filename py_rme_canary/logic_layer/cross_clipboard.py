"""Cross-Instance Clipboard Handler.

This module provides clipboard interoperability between different
PyRME instances and supports ID translation between client versions.

Reference:
    - project_tasks.json: FEAT-002 (Cross-Version Copy/Paste)
    - GAP_ANALYSIS.md: Cross-Version Copy/Paste

Architecture:
    - CrossClipboard: Handles system clipboard read/write
    - VersionTranslator: Translates item/creature IDs between versions
    - ClipboardFormat: Defines the serialization format

Layer: logic_layer (no PyQt6 imports)
"""

from __future__ import annotations

import base64
import json
import logging
import struct
import zlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Magic header for PyRME clipboard data
CLIPBOARD_MAGIC = b"PYRME\x01"
CLIPBOARD_VERSION = 2

# MIME type for clipboard
CLIPBOARD_MIME_TYPE = "application/x-pyrme-clipboard"


@dataclass
class ClipboardHeader:
    """Header for serialized clipboard data.

    Attributes:
        magic: Magic bytes (PYRME + version).
        format_version: Serialization format version.
        source_client_version: Client version of source data.
        tile_count: Number of tiles in payload.
        compressed: Whether payload is zlib compressed.
        checksum: CRC32 of decompressed payload.
    """

    magic: bytes = CLIPBOARD_MAGIC
    format_version: int = CLIPBOARD_VERSION
    source_client_version: str = ""
    tile_count: int = 0
    compressed: bool = True
    checksum: int = 0

    def pack(self) -> bytes:
        """Serialize header to bytes."""
        version_bytes = self.source_client_version.encode("utf-8")[:32]
        version_bytes = version_bytes.ljust(32, b"\0")

        return struct.pack(
            "<6sB32sI?I",
            self.magic,
            self.format_version,
            version_bytes,
            self.tile_count,
            self.compressed,
            self.checksum,
        )

    @classmethod
    def unpack(cls, data: bytes) -> ClipboardHeader | None:
        """Deserialize header from bytes."""
        if len(data) < 48:
            return None

        try:
            magic, fmt_ver, version_bytes, tile_count, compressed, checksum = struct.unpack("<6sB32sI?I", data[:48])

            if magic[:5] != b"PYRME":
                return None

            version_str = version_bytes.rstrip(b"\0").decode("utf-8", errors="ignore")

            return cls(
                magic=magic,
                format_version=fmt_ver,
                source_client_version=version_str,
                tile_count=tile_count,
                compressed=compressed,
                checksum=checksum,
            )
        except Exception:
            return None


@dataclass
class TranslationMapping:
    """Item/creature ID translation between versions.

    Attributes:
        from_version: Source client version.
        to_version: Target client version.
        item_map: Dict mapping source_id -> target_id.
        creature_map: Dict mapping source_name -> target_name.
    """

    from_version: str = ""
    to_version: str = ""
    item_map: dict[int, int] = field(default_factory=dict)
    creature_map: dict[str, str] = field(default_factory=dict)

    def translate_item(self, item_id: int) -> int:
        """Translate an item ID, returning unchanged if no mapping."""
        return self.item_map.get(item_id, item_id)

    def translate_creature(self, name: str) -> str:
        """Translate a creature name, returning unchanged if no mapping."""
        return self.creature_map.get(name, name)


class VersionTranslator:
    """Translates IDs between different client versions.

    This class loads translation tables and performs ID mapping
    when pasting data from a different client version.

    Usage:
        translator = VersionTranslator()
        translator.load_mappings("path/to/translations.json")

        new_id = translator.translate_item(
            item_id=2160,
            from_version="10.98",
            to_version="12.90"
        )
    """

    def __init__(self) -> None:
        # Mappings: (from_ver, to_ver) -> TranslationMapping
        self._mappings: dict[tuple[str, str], TranslationMapping] = {}

        # Cache for reverse lookups
        self._reverse_cache: dict[tuple[str, str], TranslationMapping] = {}

    def load_mappings(self, path: str) -> bool:
        """Load translation mappings from JSON file.

        Expected format:
        {
            "10.98->12.90": {
                "items": {"2160": 2161, ...},
                "creatures": {"Demon": "Greater Demon", ...}
            }
        }

        Args:
            path: Path to JSON file.

        Returns:
            True if loaded successfully.
        """
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            for key, mapping_data in data.items():
                if "->" not in key:
                    continue

                from_ver, to_ver = key.split("->", 1)

                item_map = {int(k): int(v) for k, v in mapping_data.get("items", {}).items()}
                creature_map = dict(mapping_data.get("creatures", {}))

                mapping = TranslationMapping(
                    from_version=from_ver.strip(),
                    to_version=to_ver.strip(),
                    item_map=item_map,
                    creature_map=creature_map,
                )

                self._mappings[(mapping.from_version, mapping.to_version)] = mapping

            logger.info("Loaded %d version translation mappings", len(self._mappings))
            return True

        except Exception as e:
            logger.warning("Failed to load version mappings: %s", e)
            return False

    def add_mapping(self, mapping: TranslationMapping) -> None:
        """Add a translation mapping programmatically."""
        self._mappings[(mapping.from_version, mapping.to_version)] = mapping

    def get_mapping(self, from_version: str, to_version: str) -> TranslationMapping | None:
        """Get translation mapping between versions.

        Args:
            from_version: Source client version.
            to_version: Target client version.

        Returns:
            TranslationMapping or None if not found.
        """
        # Direct mapping
        key = (from_version, to_version)
        if key in self._mappings:
            return self._mappings[key]

        # Try reverse mapping (swap keys/values)
        reverse_key = (to_version, from_version)
        if reverse_key in self._reverse_cache:
            return self._reverse_cache[reverse_key]

        if reverse_key in self._mappings:
            original = self._mappings[reverse_key]
            reversed_map = TranslationMapping(
                from_version=from_version,
                to_version=to_version,
                item_map={v: k for k, v in original.item_map.items()},
                creature_map={v: k for k, v in original.creature_map.items()},
            )
            self._reverse_cache[key] = reversed_map
            return reversed_map

        return None

    def translate_item(self, item_id: int, from_version: str, to_version: str) -> int:
        """Translate a single item ID.

        Args:
            item_id: Source item ID.
            from_version: Source client version.
            to_version: Target client version.

        Returns:
            Translated ID or original if no mapping.
        """
        if from_version == to_version:
            return item_id

        mapping = self.get_mapping(from_version, to_version)
        if mapping:
            return mapping.translate_item(item_id)
        return item_id

    def translate_creature(self, name: str, from_version: str, to_version: str) -> str:
        """Translate a creature name.

        Args:
            name: Source creature name.
            from_version: Source client version.
            to_version: Target client version.

        Returns:
            Translated name or original if no mapping.
        """
        if from_version == to_version:
            return name

        mapping = self.get_mapping(from_version, to_version)
        if mapping:
            return mapping.translate_creature(name)
        return name


class CrossClipboard:
    """Handles cross-instance clipboard operations.

    This class provides reading/writing clipboard data to the system
    clipboard in a format that can be shared between PyRME instances.

    Usage:
        cross = CrossClipboard()
        cross.set_translator(VersionTranslator())

        # Copy to system clipboard
        cross.write_tiles(tiles, source_version="12.90")

        # Paste from system clipboard
        tiles = cross.read_tiles(target_version="12.90")
    """

    def __init__(self) -> None:
        self._translator: VersionTranslator | None = None

        # Stats
        self._writes: int = 0
        self._reads: int = 0
        self._translations: int = 0

    def set_translator(self, translator: VersionTranslator) -> None:
        """Set the version translator for ID mapping."""
        self._translator = translator

    def write_tiles(
        self,
        tiles: list[dict[str, Any]],
        source_version: str = "",
        *,
        compress: bool = True,
    ) -> bytes:
        """Serialize tiles to clipboard format.

        Args:
            tiles: List of tile data dicts.
            source_version: Client version of the data.
            compress: Whether to compress payload.

        Returns:
            Serialized bytes for clipboard.
        """
        # Serialize tiles to JSON
        payload = json.dumps(tiles, separators=(",", ":")).encode("utf-8")

        # Calculate checksum before compression
        checksum = zlib.crc32(payload) & 0xFFFFFFFF

        # Compress if requested
        if compress:
            payload = zlib.compress(payload, level=6)

        # Build header
        header = ClipboardHeader(
            source_client_version=source_version,
            tile_count=len(tiles),
            compressed=compress,
            checksum=checksum,
        )

        self._writes += 1

        return header.pack() + payload

    def read_tiles(
        self,
        data: bytes,
        target_version: str = "",
    ) -> tuple[list[dict[str, Any]], str]:
        """Deserialize tiles from clipboard format.

        Args:
            data: Raw clipboard bytes.
            target_version: Client version to translate to.

        Returns:
            Tuple of (tiles, source_version).

        Raises:
            ValueError: If data is invalid.
        """
        # Parse header
        header = ClipboardHeader.unpack(data)
        if header is None:
            raise ValueError("Invalid clipboard header")

        # Extract payload
        payload = data[48:]

        # Decompress if needed
        if header.compressed:
            payload = zlib.decompress(payload)

        # Verify checksum
        actual_checksum = zlib.crc32(payload) & 0xFFFFFFFF
        if actual_checksum != header.checksum:
            logger.warning("Clipboard checksum mismatch: expected %08x, got %08x", header.checksum, actual_checksum)

        # Parse JSON
        tiles: list[dict[str, Any]] = json.loads(payload)

        # Translate if needed
        if target_version and header.source_client_version != target_version:
            tiles = self._translate_tiles(
                tiles,
                header.source_client_version,
                target_version,
            )

        self._reads += 1

        return tiles, header.source_client_version

    def _translate_tiles(
        self,
        tiles: list[dict[str, Any]],
        from_version: str,
        to_version: str,
    ) -> list[dict[str, Any]]:
        """Translate all IDs in tile data.

        Args:
            tiles: List of tile dicts.
            from_version: Source version.
            to_version: Target version.

        Returns:
            Translated tile list.
        """
        if self._translator is None:
            logger.debug("No translator set, skipping ID translation")
            return tiles

        translated: list[dict[str, Any]] = []

        for tile in tiles:
            new_tile = dict(tile)

            # Translate ground
            if "ground_id" in new_tile and new_tile["ground_id"]:
                new_tile["ground_id"] = self._translator.translate_item(new_tile["ground_id"], from_version, to_version)
                self._translations += 1

            # Translate items
            if "items" in new_tile and isinstance(new_tile["items"], list):
                new_items = []
                for item in new_tile["items"]:
                    new_item = dict(item)
                    if "id" in new_item:
                        new_item["id"] = self._translator.translate_item(new_item["id"], from_version, to_version)
                        self._translations += 1
                    new_items.append(new_item)
                new_tile["items"] = new_items

            # Translate monsters
            if "monsters" in new_tile and isinstance(new_tile["monsters"], list):
                new_monsters = []
                for monster in new_tile["monsters"]:
                    new_monster = dict(monster)
                    if "name" in new_monster:
                        new_monster["name"] = self._translator.translate_creature(
                            new_monster["name"], from_version, to_version
                        )
                        self._translations += 1
                    new_monsters.append(new_monster)
                new_tile["monsters"] = new_monsters

            # Translate NPC
            if "npc" in new_tile and new_tile["npc"]:
                npc = dict(new_tile["npc"])
                if "name" in npc:
                    npc["name"] = self._translator.translate_creature(npc["name"], from_version, to_version)
                    self._translations += 1
                new_tile["npc"] = npc

            # Translate spawn_monster entries
            if "spawn_monster" in new_tile and new_tile["spawn_monster"]:
                spawn = dict(new_tile["spawn_monster"])
                if "monsters" in spawn:
                    for entry in spawn.get("monsters", []):
                        if "name" in entry:
                            entry["name"] = self._translator.translate_creature(entry["name"], from_version, to_version)
                            self._translations += 1
                new_tile["spawn_monster"] = spawn

            # Translate spawn_npc entries
            if "spawn_npc" in new_tile and new_tile["spawn_npc"]:
                spawn = dict(new_tile["spawn_npc"])
                if "npcs" in spawn:
                    for entry in spawn.get("npcs", []):
                        if "name" in entry:
                            entry["name"] = self._translator.translate_creature(entry["name"], from_version, to_version)
                            self._translations += 1
                new_tile["spawn_npc"] = spawn

            translated.append(new_tile)

        logger.debug("Translated %d tiles from %s to %s", len(translated), from_version, to_version)
        return translated

    def to_base64(self, data: bytes) -> str:
        """Encode binary data for text clipboard.

        Args:
            data: Binary clipboard data.

        Returns:
            Base64-encoded string with prefix.
        """
        encoded = base64.b64encode(data).decode("ascii")
        return f"PYRME:{encoded}"

    def from_base64(self, text: str) -> bytes:
        """Decode binary data from text clipboard.

        Args:
            text: Base64-encoded string.

        Returns:
            Binary clipboard data.

        Raises:
            ValueError: If text is not valid PYRME clipboard data.
        """
        if not text.startswith("PYRME:"):
            raise ValueError("Not a PYRME clipboard string")

        encoded = text[6:]  # Skip "PYRME:"
        return base64.b64decode(encoded)

    def get_stats(self) -> dict[str, int]:
        """Get clipboard operation statistics."""
        return {
            "writes": self._writes,
            "reads": self._reads,
            "translations": self._translations,
        }


# Global instances
_translator: VersionTranslator | None = None
_clipboard: CrossClipboard | None = None


def get_version_translator() -> VersionTranslator:
    """Get the global version translator instance."""
    global _translator
    if _translator is None:
        _translator = VersionTranslator()
    return _translator


def get_cross_clipboard() -> CrossClipboard:
    """Get the global cross clipboard instance."""
    global _clipboard
    if _clipboard is None:
        _clipboard = CrossClipboard()
        _clipboard.set_translator(get_version_translator())
    return _clipboard
