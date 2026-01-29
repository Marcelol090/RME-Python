"""Low-level streaming utilities for OTBM node file format.

Handles escape sequences and provides an abstraction for reading
payloads from OTBM's node-based binary format.
"""

from __future__ import annotations

from typing import BinaryIO

from py_rme_canary.core.constants import ESCAPE_CHAR, NODE_END, NODE_START
from py_rme_canary.core.exceptions import OTBMParseError


def read_exact(stream: BinaryIO, n: int) -> bytes:
    """Read exactly n bytes from stream or raise OTBMParseError."""
    data = stream.read(n)
    if data is None or len(data) != n:
        raise OTBMParseError(f"Unexpected EOF (wanted {n} bytes, got {len(data) if data is not None else 0})")
    return data


def read_u8(stream: BinaryIO) -> int:
    """Read a single unsigned byte from stream."""
    return read_exact(stream, 1)[0]


class EscapedPayloadReader:
    """Streams bytes inside a NodeFile node payload, honoring escape semantics.

    OTBM uses a node-based format where special bytes (NODE_START, NODE_END,
    ESCAPE_CHAR) within payload data must be escaped with ESCAPE_CHAR.

    This reader transparently handles unescaping while reading payload bytes.
    """

    __slots__ = ("_ended", "_stream", "delimiter")

    def __init__(self, stream: BinaryIO) -> None:
        self._stream = stream
        self._ended = False
        self.delimiter: int | None = None

    def read_escaped_bytes(self, n: int) -> bytes:
        """Read exactly n unescaped bytes from the payload."""
        out = bytearray()
        while len(out) < n:
            b = read_u8(self._stream)
            if b == ESCAPE_CHAR:
                out.append(read_u8(self._stream))
                continue
            if b in (NODE_START, NODE_END):
                raise OTBMParseError(
                    f"Unexpected delimiter 0x{b:02X} inside payload (needed {n} bytes, got {len(out)})"
                )
            out.append(b)
        return bytes(out)

    def read_escaped_u8(self) -> int | None:
        """Read a single unescaped byte, or None if delimiter reached."""
        if self._ended:
            return None

        b = read_u8(self._stream)
        if b == ESCAPE_CHAR:
            return read_u8(self._stream)
        if b in (NODE_START, NODE_END):
            self._ended = True
            self.delimiter = b
            return None
        return b

    def drain_to_delimiter(self) -> int:
        """Skip remaining payload bytes until a delimiter is reached."""
        while True:
            b = read_u8(self._stream)
            if b == ESCAPE_CHAR:
                read_u8(self._stream)
                continue
            if b in (NODE_START, NODE_END):
                self._ended = True
                self.delimiter = b
                return b


def begin_node(stream: BinaryIO) -> tuple[int, EscapedPayloadReader]:
    """Begin reading a new node, returning (node_type, payload_reader)."""
    node_type = read_u8(stream)
    return node_type, EscapedPayloadReader(stream)


def consume_siblings_until_end(stream: BinaryIO) -> None:
    """Skip all sibling nodes until NODE_END is reached.

    Used to skip unknown or unsupported node subtrees.
    """
    while True:
        _node_type, payload = begin_node(stream)
        delim = payload.drain_to_delimiter()
        if delim == NODE_START:
            consume_siblings_until_end(stream)

        op = read_u8(stream)
        if op == NODE_START:
            continue
        if op == NODE_END:
            return
        raise OTBMParseError(f"Invalid stream op 0x{op:02X} while skipping")


def read_string(payload: EscapedPayloadReader) -> str:
    """Read a length-prefixed string from payload."""
    import struct

    slen = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
    raw = payload.read_escaped_bytes(int(slen))
    return raw.decode("utf-8", errors="replace")


def read_string_bytes(payload: EscapedPayloadReader) -> bytes:
    """Read a length-prefixed string as raw bytes from payload."""
    import struct

    slen = struct.unpack("<H", payload.read_escaped_bytes(2))[0]
    return payload.read_escaped_bytes(int(slen))
