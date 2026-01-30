from __future__ import annotations

import struct
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

NODE_START = 0xFE
NODE_END = 0xFF
ESCAPE_CHAR = 0xFD

MAGIC_OTBI = b"OTBI"
MAGIC_WILDCARD = b"\x00\x00\x00\x00"  # Alternative magic used by RME

# Legacy reference: source/items.h
ROOT_ATTR_VERSION = 0x01

ITEM_GROUP_DEPRECATED = 13

ITEM_ATTR_FIRST = 0x10
ITEM_ATTR_SERVERID = ITEM_ATTR_FIRST
ITEM_ATTR_CLIENTID = ITEM_ATTR_FIRST + 1


class ItemsOTBError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ItemsOTBHeader:
    major: int
    minor: int
    build: int
    csd: str

    @property
    def client_version(self) -> int:
        """Extract Tibia client version from CSD string or major.minor.

        The CSD string typically contains the client version in format "OTB X.Y.Z-AA.BB"
        where AA.BB is the Tibia client version (e.g., "OTB 3.65.62-13.10" → 1310).

        For very old versions (like 7.4) that don't have version in CSD,
        uses legacy OTB version mapping.

        Examples:
            "OTB 3.65.62-13.10" → 1310
            "OTB 3.12.7-8.40" → 840 (8.4 stored as 840)
            "OTB 3.20.20-8.60" → 860 (8.6)
            "OTB 1.1.1 (1-byte aligned)" → 740 (legacy 7.4, special case)
        """
        import re

        # Legacy OTB version → Tibia client version mapping
        # Used for very old OTB versions without client version in CSD
        LEGACY_OTB_MAPPING = {
            101: 740,  # OTB 1.1 → Tibia 7.4
            102: 750,  # OTB 1.2 → Tibia 7.5
        }

        # Try to extract version from CSD string (format: "OTB X.Y.Z-AA.BB")
        match = re.search(r"-(\d+)\.(\d+)", self.csd)
        if match:
            major_client = int(match.group(1))
            minor_client = int(match.group(2))
            return major_client * 100 + minor_client

        # Fallback: use legacy OTB version mapping for very old versions
        otb_version = int(self.major * 100 + self.minor)
        return LEGACY_OTB_MAPPING.get(otb_version, otb_version)


@dataclass(frozen=True, slots=True)
class ItemsOTB:
    header: ItemsOTBHeader
    client_to_server: dict[int, int]
    server_to_client: dict[int, int]

    @classmethod
    def load(cls, path: str | Path) -> ItemsOTB:
        p = Path(path)
        with p.open("rb") as f:
            magic = f.read(4)
            if magic not in (MAGIC_OTBI, MAGIC_WILDCARD):
                raise ItemsOTBError(
                    f"Invalid items.otb magic: {magic!r} (expected {MAGIC_OTBI!r} or {MAGIC_WILDCARD!r})"
                )

            op = _read_u8(f)
            if op != NODE_START:
                raise ItemsOTBError(f"Invalid nodefile op 0x{op:02X} (expected NODE_START)")

            root_payload, root_delim = _read_node_payload_until_delim(f)
            if not root_payload:
                raise ItemsOTBError("Empty root node")

            header = _parse_root_header(root_payload)

            client_to_server: dict[int, int] = {}
            server_to_client: dict[int, int] = {}

            if root_delim == NODE_START:
                # Children begin immediately.
                _consume_siblings_until_end(
                    f,
                    lambda payload: _parse_item_node(
                        payload, client_to_server=client_to_server, server_to_client=server_to_client
                    ),
                )
            elif root_delim != NODE_END:
                raise ItemsOTBError(f"Invalid root delimiter 0x{root_delim:02X}")

            return cls(header=header, client_to_server=client_to_server, server_to_client=server_to_client)

    @classmethod
    def read_header(cls, path: str | Path) -> ItemsOTBHeader:
        """Read just the header without loading all item mappings (fast)."""
        p = Path(path)
        with p.open("rb") as f:
            magic = f.read(4)
            if magic not in (MAGIC_OTBI, MAGIC_WILDCARD):
                raise ItemsOTBError(
                    f"Invalid items.otb magic: {magic!r} (expected {MAGIC_OTBI!r} or {MAGIC_WILDCARD!r})"
                )

            op = _read_u8(f)
            if op != NODE_START:
                raise ItemsOTBError(f"Invalid nodefile op 0x{op:02X} (expected NODE_START)")

            root_payload, _root_delim = _read_node_payload_until_delim(f)
            if not root_payload:
                raise ItemsOTBError("Empty root node")

            return _parse_root_header(root_payload)


def _read_exact(stream: BinaryIO, n: int) -> bytes:
    data = stream.read(n)
    if data is None or len(data) != n:
        raise ItemsOTBError(f"Unexpected EOF (wanted {n} bytes, got {len(data) if data is not None else 0})")
    return data


def _read_u8(stream: BinaryIO) -> int:
    return _read_exact(stream, 1)[0]


def _read_node_payload_until_delim(stream: BinaryIO) -> tuple[bytes, int]:
    out = bytearray()
    while True:
        b = _read_u8(stream)
        if b in (NODE_START, NODE_END):
            return bytes(out), b
        if b == ESCAPE_CHAR:
            out.append(_read_u8(stream))
            continue
        out.append(b)


def _consume_siblings_until_end(stream: BinaryIO, parse_child: Callable[[bytes], None]) -> None:
    while True:
        payload, delim = _read_node_payload_until_delim(stream)
        parse_child(payload)

        if delim == NODE_START:
            _consume_siblings_until_end(stream, parse_child)
        elif delim != NODE_END:
            raise ItemsOTBError(f"Invalid node delimiter 0x{delim:02X}")

        op = _read_u8(stream)
        if op == NODE_START:
            continue
        if op == NODE_END:
            return
        raise ItemsOTBError(f"Invalid stream op 0x{op:02X} while advancing siblings")


def _parse_root_header(root_payload: bytes) -> ItemsOTBHeader:
    # Mirrors ItemDatabase::loadFromOtb root parsing in source/items.cpp
    # root payload layout in legacy:
    # - 1 byte: type info (skipped)
    # - 4 bytes: unused (skipped)
    # - u8 attr (must be ROOT_ATTR_VERSION)
    # - u16 datalen (must be 4+4+4+128)
    # - u32 major, u32 minor, u32 build
    # - 128 bytes raw string (CSD)
    if len(root_payload) < 1 + 4 + 1 + 2:
        raise ItemsOTBError("items.otb: Root node too small")

    off = 0
    off += 1  # type info
    off += 4  # unused

    attr = root_payload[off]
    off += 1
    if attr != ROOT_ATTR_VERSION:
        raise ItemsOTBError("items.otb: Expected ROOT_ATTR_VERSION as first root attribute")

    datalen = struct.unpack_from("<H", root_payload, off)[0]
    off += 2

    expected = 4 + 4 + 4 + 1 * 128
    if int(datalen) != int(expected):
        raise ItemsOTBError("items.otb: Size of version header is invalid")

    if off + expected > len(root_payload):
        raise ItemsOTBError("items.otb: Truncated version header")

    major, minor, build = struct.unpack_from("<III", root_payload, off)
    off += 12

    csd_raw = root_payload[off : off + 128]
    csd = csd_raw.split(b"\x00", 1)[0].decode("latin-1", errors="replace")

    return ItemsOTBHeader(major=int(major), minor=int(minor), build=int(build), csd=str(csd))


def _parse_item_node(payload: bytes, *, client_to_server: dict[int, int], server_to_client: dict[int, int]) -> None:
    # Child payload includes the node's type info as the first byte.
    # In legacy, itemNode->getU8(group) reads this.
    if not payload:
        return

    group = int(payload[0])
    if group == ITEM_GROUP_DEPRECATED:
        return

    if len(payload) < 1 + 4:
        return

    off = 1
    off += 4  # flags (u32) ignored

    sid: int | None = None
    cid: int | None = None

    # Attributes: repeated [u8 attr][u16 datalen][datalen bytes]
    while off < len(payload):
        attr = int(payload[off])
        off += 1
        if off + 2 > len(payload):
            break
        datalen = int(struct.unpack_from("<H", payload, off)[0])
        off += 2
        if off + datalen > len(payload):
            break

        data = payload[off : off + datalen]
        off += datalen

        if attr == ITEM_ATTR_SERVERID and datalen == 2:
            sid = int(struct.unpack_from("<H", data, 0)[0])
        elif attr == ITEM_ATTR_CLIENTID and datalen == 2:
            cid = int(struct.unpack_from("<H", data, 0)[0])

        # We only need server/client id mapping.

    if sid is None or cid is None:
        return

    # Prefer first occurrence; ignore duplicates.
    if int(sid) not in server_to_client:
        server_to_client[int(sid)] = int(cid)
    if int(cid) not in client_to_server:
        client_to_server[int(cid)] = int(sid)
