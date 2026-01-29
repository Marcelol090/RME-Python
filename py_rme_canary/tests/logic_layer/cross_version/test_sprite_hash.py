"""Tests for sprite hash matching (FNV-1a algorithm)."""
from __future__ import annotations

from py_rme_canary.logic_layer.cross_version.sprite_hash import (
    SpriteHashMatcher,
    calculate_sprite_hash,
    fnv1a_64,
)


def test_fnv1a_64_empty():
    """Test FNV-1a hash of empty bytes."""
    result = fnv1a_64(b"")
    assert result == 0xCBF29CE484222325  # FNV-1a 64-bit offset basis


def test_fnv1a_64_known_values():
    """Test FNV-1a hash with known values."""
    # Test vectors from FNV specification
    assert fnv1a_64(b"a") == 0xAF63DC4C8601EC8C
    assert fnv1a_64(b"foo") == 0xDCB27518FED9D577
    assert fnv1a_64(b"foobar") == 0x85944171F73967E8


def test_calculate_sprite_hash_basic():
    """Test sprite hash calculation from pixel data."""
    # 2x2 white sprite
    pixel_data = b"\xff\xff\xff\xff" * 4  # 4 pixels RGBA
    width, height = 2, 2

    hash_value = calculate_sprite_hash(pixel_data, width, height)

    assert isinstance(hash_value, int)
    assert hash_value > 0


def test_calculate_sprite_hash_different_sprites():
    """Test that different sprites produce different hashes."""
    # White sprite
    white = b"\xff\xff\xff\xff" * 4
    # Black sprite
    black = b"\x00\x00\x00\xff" * 4

    hash_white = calculate_sprite_hash(white, 2, 2)
    hash_black = calculate_sprite_hash(black, 2, 2)

    assert hash_white != hash_black


def test_calculate_sprite_hash_same_sprites():
    """Test that identical sprites produce same hash."""
    data = b"\x12\x34\x56\x78" * 16  # 4x4 sprite

    hash1 = calculate_sprite_hash(data, 4, 4)
    hash2 = calculate_sprite_hash(data, 4, 4)

    assert hash1 == hash2


def test_sprite_hash_matcher_add_and_lookup():
    """Test adding sprites and looking up by hash."""
    matcher = SpriteHashMatcher()

    # Add sprite with ID 100
    sprite_data = b"\xaa\xbb\xcc\xdd" * 4
    sprite_id = 100

    matcher.add_sprite(sprite_id, sprite_data, 2, 2)

    # Calculate hash and lookup
    hash_value = calculate_sprite_hash(sprite_data, 2, 2)
    result = matcher.find_by_hash(hash_value)

    assert result == [sprite_id]


def test_sprite_hash_matcher_multiple_matches():
    """Test that hash collisions are handled correctly."""
    matcher = SpriteHashMatcher()

    sprite_data = b"\xff" * 16

    # Same sprite, different IDs (e.g., different client versions)
    matcher.add_sprite(100, sprite_data, 2, 2)
    matcher.add_sprite(200, sprite_data, 2, 2)

    hash_value = calculate_sprite_hash(sprite_data, 2, 2)
    results = matcher.find_by_hash(hash_value)

    assert set(results) == {100, 200}


def test_sprite_hash_matcher_no_match():
    """Test lookup when no matching hash exists."""
    matcher = SpriteHashMatcher()

    # Add one sprite
    matcher.add_sprite(100, b"\xff" * 16, 2, 2)

    # Look for different sprite
    different_sprite = b"\x00" * 16
    hash_value = calculate_sprite_hash(different_sprite, 2, 2)
    result = matcher.find_by_hash(hash_value)

    assert result == []


def test_sprite_hash_matcher_get_hash():
    """Test retrieving hash for a sprite ID."""
    matcher = SpriteHashMatcher()

    sprite_data = b"\xaa\xbb\xcc\xdd" * 4
    sprite_id = 150

    matcher.add_sprite(sprite_id, sprite_data, 2, 2)

    expected_hash = calculate_sprite_hash(sprite_data, 2, 2)
    actual_hash = matcher.get_hash(sprite_id)

    assert actual_hash == expected_hash


def test_sprite_hash_matcher_clear():
    """Test clearing all hashes."""
    matcher = SpriteHashMatcher()

    matcher.add_sprite(100, b"\xff" * 16, 2, 2)
    matcher.add_sprite(200, b"\x00" * 16, 2, 2)

    assert len(matcher._hash_to_ids) > 0

    matcher.clear()

    assert len(matcher._hash_to_ids) == 0
    assert len(matcher._id_to_hash) == 0
