"""Header parsing utilities for OTBM format.

Handles parsing of OTBM root node and map metadata.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import BinaryIO

from py_rme_canary.core.constants import (
    MAGIC_OTBM,
    MAGIC_WILDCARD,
    NODE_START,
    OTBM_ATTR_DESCRIPTION,
    OTBM_ATTR_EXT_HOUSE_FILE,
    OTBM_ATTR_EXT_SPAWN_MONSTER_FILE,
    OTBM_ATTR_EXT_SPAWN_NPC_FILE,
    OTBM_ATTR_EXT_ZONE_FILE,
    OTBM_ROOTV1,
)
from py_rme_canary.core.data.gamemap import MapHeader
from py_rme_canary.core.exceptions import OTBMParseError

from .streaming import (
    EscapedPayloadReader,
    begin_node,
    read_exact,
    read_string,
    read_u8,
)


@dataclass(frozen=True, slots=True)
class RootHeader:
    """Parsed root node header data."""

    otbm_version: int
    width: int
    height: int


def read_root_header(stream: BinaryIO, *, allow_unsupported_versions: bool = False) -> RootHeader:
    """Read and validate OTBM file header and root node."""

    # Read magic bytes
    magic = read_exact(stream, 4)
    if magic not in (MAGIC_OTBM, MAGIC_WILDCARD):
        raise OTBMParseError(f"Invalid OTBM magic: {magic!r}")

    # Expect NODE_START
    op = read_u8(stream)
    if op != NODE_START:
        raise OTBMParseError(f"Expected NODE_START, got 0x{op:02X}")

    # Begin root node
    root_type, root_payload = begin_node(stream)
    if root_type != OTBM_ROOTV1:
        raise OTBMParseError(f"Expected OTBM_ROOTV1 (0x01), got 0x{root_type:02X}")

    # Read version
    version_bytes = root_payload.read_escaped_bytes(4)
    otbm_version = struct.unpack("<I", version_bytes)[0]

    if not allow_unsupported_versions and otbm_version not in (1, 2):
        raise OTBMParseError(f"Unsupported OTBM version: {otbm_version}")

    # Read dimensions
    dim_bytes = root_payload.read_escaped_bytes(4)
    width, height = struct.unpack("<HH", dim_bytes)

    # Drain the remaining root payload to position the stream at either:
    # - the first child node type (if delimiter is NODE_START), or
    # - the end of the root node (if delimiter is NODE_END).
    delim = root_payload.drain_to_delimiter()
    if delim != NODE_START:
        raise OTBMParseError("Root node has no children")

    return RootHeader(
        otbm_version=int(otbm_version),
        width=int(width),
        height=int(height),
    )


def parse_map_data_attributes(payload: EscapedPayloadReader) -> dict[str, str]:
    """Parse MAP_DATA node attributes."""
    attrs: dict[str, str] = {
        "description": "",
        "spawnmonsterfile": "",
        "spawnnpcfile": "",
        "housefile": "",
        "zonefile": "",
    }

    while True:
        attr_byte = payload.read_escaped_u8()
        if attr_byte is None:
            break

        attr = int(attr_byte)

        if attr == OTBM_ATTR_DESCRIPTION:
            attrs["description"] = read_string(payload)
        elif attr == OTBM_ATTR_EXT_SPAWN_MONSTER_FILE:
            attrs["spawnmonsterfile"] = read_string(payload)
        elif attr == OTBM_ATTR_EXT_HOUSE_FILE:
            attrs["housefile"] = read_string(payload)
        elif attr == OTBM_ATTR_EXT_SPAWN_NPC_FILE:
            attrs["spawnnpcfile"] = read_string(payload)
        elif attr == OTBM_ATTR_EXT_ZONE_FILE:
            attrs["zonefile"] = read_string(payload)
        else:
            # Unknown attribute - skip
            pass

    return attrs


def create_map_header(
    root: RootHeader,
    attrs: dict[str, str],
) -> MapHeader:
    """Create MapHeader from parsed root and attributes."""
    return MapHeader(
        otbm_version=int(root.otbm_version),
        width=int(root.width),
        height=int(root.height),
        description=str(attrs.get("description", "")),
        spawnmonsterfile=str(attrs.get("spawnmonsterfile", "")),
        spawnnpcfile=str(attrs.get("spawnnpcfile", "")),
        housefile=str(attrs.get("housefile", "")),
        zonefile=str(attrs.get("zonefile", "")),
    )
