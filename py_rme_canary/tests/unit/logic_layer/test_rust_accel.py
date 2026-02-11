from __future__ import annotations

import sys
import zlib
from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import py_rme_canary.logic_layer.rust_accel as rust_accel
from py_rme_canary.logic_layer.rust_accel import (
    assemble_png_idat,
    fnv1a_64,
    render_minimap_buffer,
    spawn_entry_names_at_cursor,
    sprite_hash,
)


@dataclass(slots=True)
class _Center:
    x: int
    y: int
    z: int


@dataclass(slots=True)
class _Entry:
    name: str
    dx: int
    dy: int


@dataclass(slots=True)
class _MonsterArea:
    center: _Center
    radius: int
    monsters: tuple[_Entry, ...]


@pytest.fixture(autouse=True)
def _reset_backend_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rust_accel, "_BACKEND_CACHE", None)
    monkeypatch.setattr(rust_accel, "_BACKEND_CACHE_READY", False)


# ---------------------------------------------------------------------------
# spawn_entry_names_at_cursor (existing tests, unchanged)
# ---------------------------------------------------------------------------


def test_spawn_entry_names_at_cursor_python_fallback() -> None:
    areas = [
        _MonsterArea(
            center=_Center(x=20, y=30, z=7),
            radius=3,
            monsters=(
                _Entry(name="Dragon", dx=0, dy=0),
                _Entry(name="Demon", dx=1, dy=0),
            ),
        )
    ]

    names = spawn_entry_names_at_cursor(areas, entries_attr="monsters", x=20, y=30, z=7)
    assert names == ["Dragon"]


def test_spawn_entry_names_at_cursor_uses_backend_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    backend_calls: list[tuple[object, int, int, int]] = []

    def _backend_fn(payload: object, x: int, y: int, z: int) -> list[str]:
        backend_calls.append((payload, x, y, z))
        return ["BackendResult"]

    monkeypatch.setitem(
        sys.modules,
        "py_rme_canary_rust",
        SimpleNamespace(spawn_entry_names_at_cursor=_backend_fn),
    )

    areas = [
        _MonsterArea(
            center=_Center(x=10, y=10, z=7),
            radius=2,
            monsters=(_Entry(name="A", dx=0, dy=0),),
        )
    ]

    names = spawn_entry_names_at_cursor(areas, entries_attr="monsters", x=10, y=10, z=7)
    assert names == ["BackendResult"]
    assert len(backend_calls) == 1
    _, bx, by, bz = backend_calls[0]
    assert (bx, by, bz) == (10, 10, 7)


def test_spawn_entry_names_at_cursor_falls_back_when_backend_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    def _backend_fn(payload: object, x: int, y: int, z: int) -> list[str]:
        raise RuntimeError("backend failure")

    monkeypatch.setitem(
        sys.modules,
        "py_rme_canary_rust",
        SimpleNamespace(spawn_entry_names_at_cursor=_backend_fn),
    )

    areas = [
        _MonsterArea(
            center=_Center(x=15, y=15, z=7),
            radius=2,
            monsters=(_Entry(name="FallbackMonster", dx=0, dy=0),),
        )
    ]

    names = spawn_entry_names_at_cursor(areas, entries_attr="monsters", x=15, y=15, z=7)
    assert names == ["FallbackMonster"]


# ---------------------------------------------------------------------------
# fnv1a_64 — FNV-1a 64-bit hash (Python fallback)
# ---------------------------------------------------------------------------


class TestFnv1a64:
    """Tests for the FNV-1a 64-bit hash function."""

    def test_empty_data_returns_offset_basis(self) -> None:
        assert fnv1a_64(b"") == 0xCBF29CE484222325

    def test_known_hash_foo(self) -> None:
        # Known FNV-1a 64 hash for "foo"
        assert fnv1a_64(b"foo") == 0xDCB27518FED9D577

    def test_different_inputs_produce_different_hashes(self) -> None:
        h1 = fnv1a_64(b"hello")
        h2 = fnv1a_64(b"world")
        assert h1 != h2

    def test_same_input_produces_same_hash(self) -> None:
        data = b"deterministic"
        assert fnv1a_64(data) == fnv1a_64(data)

    def test_single_byte(self) -> None:
        h = fnv1a_64(b"\x00")
        assert isinstance(h, int)
        assert h != 0xCBF29CE484222325  # Different from empty

    def test_large_data(self) -> None:
        data = bytes(range(256)) * 100  # 25,600 bytes
        h = fnv1a_64(data)
        assert isinstance(h, int)
        assert 0 <= h < 2**64

    def test_uses_backend_when_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[bytes] = []

        def _backend_hash(data: bytes) -> int:
            calls.append(data)
            return 42

        monkeypatch.setitem(
            sys.modules,
            "py_rme_canary_rust",
            SimpleNamespace(
                spawn_entry_names_at_cursor=lambda *a: [],
                fnv1a_64_hash=_backend_hash,
            ),
        )
        result = fnv1a_64(b"test")
        assert result == 42
        assert calls == [b"test"]


# ---------------------------------------------------------------------------
# sprite_hash — including dimensions
# ---------------------------------------------------------------------------


class TestSpriteHash:
    """Tests for sprite_hash (dimensions + pixel data)."""

    def test_returns_int(self) -> None:
        pixel_data = b"\xff" * (2 * 2 * 4)  # 2x2 RGBA
        h = sprite_hash(pixel_data, 2, 2)
        assert isinstance(h, int)

    def test_different_dimensions_different_hash(self) -> None:
        # Same pixel bytes but different dimensions → different hash
        data = b"\x00" * 16
        h1 = sprite_hash(data, 2, 2)
        h2 = sprite_hash(data, 4, 1)
        assert h1 != h2

    def test_consistent(self) -> None:
        data = b"\xAB" * (3 * 3 * 4)
        assert sprite_hash(data, 3, 3) == sprite_hash(data, 3, 3)


# ---------------------------------------------------------------------------
# render_minimap_buffer — pixel buffer generation
# ---------------------------------------------------------------------------


class TestRenderMinimapBuffer:
    """Tests for the minimap pixel buffer renderer."""

    def test_all_transparent_returns_background(self) -> None:
        colors: list[tuple[int, int, int, int]] = [(0, 0, 0, 0)] * 4  # 2x2 grid
        buf = render_minimap_buffer(colors, 2, 2, 1, 128, 64, 32)
        assert isinstance(buf, (bytes, bytearray))
        assert len(buf) == 2 * 2 * 3
        # All pixels should be background
        for i in range(0, len(buf), 3):
            assert buf[i] == 128
            assert buf[i + 1] == 64
            assert buf[i + 2] == 32

    def test_single_tile_colored(self) -> None:
        colors: list[tuple[int, int, int, int]] = [(255, 0, 0, 255)]  # 1x1
        buf = render_minimap_buffer(colors, 1, 1, 1, 0, 0, 0)
        assert buf[0] == 255
        assert buf[1] == 0
        assert buf[2] == 0

    def test_tile_size_scaling(self) -> None:
        # 1 tile at tile_size=2 → 2x2 pixels all same color
        colors: list[tuple[int, int, int, int]] = [(10, 20, 30, 255)]
        buf = render_minimap_buffer(colors, 1, 1, 2, 0, 0, 0)
        assert len(buf) == 2 * 2 * 3  # 4 pixels
        for i in range(0, len(buf), 3):
            assert (buf[i], buf[i + 1], buf[i + 2]) == (10, 20, 30)

    def test_mixed_tiles(self) -> None:
        # 2x1 grid: red tile, transparent tile
        colors: list[tuple[int, int, int, int]] = [
            (255, 0, 0, 255),
            (0, 0, 0, 0),  # transparent
        ]
        buf = render_minimap_buffer(colors, 2, 1, 1, 50, 50, 50)
        assert len(buf) == 2 * 1 * 3
        assert (buf[0], buf[1], buf[2]) == (255, 0, 0)     # red tile
        assert (buf[3], buf[4], buf[5]) == (50, 50, 50)     # background

    def test_empty_grid(self) -> None:
        buf = render_minimap_buffer([], 0, 0, 1, 0, 0, 0)
        assert len(buf) == 0

    def test_uses_backend_when_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[object] = []

        def _backend_fn(*args: object) -> bytes:
            calls.append(args)
            return b"\xFF\x00\x00"

        monkeypatch.setitem(
            sys.modules,
            "py_rme_canary_rust",
            SimpleNamespace(
                spawn_entry_names_at_cursor=lambda *a: [],
                render_minimap_buffer=_backend_fn,
            ),
        )
        result = render_minimap_buffer([(255, 0, 0, 255)], 1, 1, 1, 0, 0, 0)
        assert result == b"\xFF\x00\x00"
        assert len(calls) == 1


# ---------------------------------------------------------------------------
# assemble_png_idat — PNG row assembly + compression
# ---------------------------------------------------------------------------


class TestAssemblePngIdat:
    """Tests for PNG IDAT assembly."""

    def test_basic_1x1_image(self) -> None:
        # 1x1 RGB image: single red pixel
        image_data = bytearray([255, 0, 0])
        compressed = assemble_png_idat(image_data, 1, 1)
        assert isinstance(compressed, bytes)
        # Decompress and verify
        raw = zlib.decompress(compressed)
        # Should be: filter_byte(0) + R, G, B
        assert raw == b"\x00\xff\x00\x00"

    def test_2x2_image(self) -> None:
        # 2x2 RGB: red, green, blue, white
        image_data = bytearray([
            255, 0, 0,  0, 255, 0,    # row 0
            0, 0, 255,  255, 255, 255  # row 1
        ])
        compressed = assemble_png_idat(image_data, 2, 2)
        raw = zlib.decompress(compressed)
        # row 0: filter(0) + 6 bytes, row 1: filter(0) + 6 bytes
        assert len(raw) == 2 * (1 + 6)
        assert raw[0] == 0  # filter byte row 0
        assert raw[7] == 0  # filter byte row 1

    def test_roundtrip_data_integrity(self) -> None:
        width, height = 4, 3
        image_data = bytearray(range(width * height * 3))
        compressed = assemble_png_idat(image_data, width, height)
        raw = zlib.decompress(compressed)

        # Reconstruct image from raw (strip filter bytes)
        row_bytes = width * 3
        reconstructed = bytearray()
        for y in range(height):
            offset = y * (row_bytes + 1)
            assert raw[offset] == 0  # filter byte
            reconstructed.extend(raw[offset + 1: offset + 1 + row_bytes])
        assert reconstructed == image_data

    def test_uses_backend_when_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[object] = []

        def _backend_fn(data: bytes, w: int, h: int) -> bytes:
            calls.append((data, w, h))
            return b"COMPRESSED"

        monkeypatch.setitem(
            sys.modules,
            "py_rme_canary_rust",
            SimpleNamespace(
                spawn_entry_names_at_cursor=lambda *a: [],
                assemble_png_idat=_backend_fn,
            ),
        )
        result = assemble_png_idat(bytearray([255, 0, 0]), 1, 1)
        assert result == b"COMPRESSED"
        assert len(calls) == 1
