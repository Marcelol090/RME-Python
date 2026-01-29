"""Sprite hash matching using FNV-1a algorithm for cross-version copy/paste.

This module implements the FNV-1a 64-bit hashing algorithm to create unique
fingerprints of sprite pixel data. This allows matching sprites across different
client versions where sprite IDs may differ but visual content is identical.

References:
    - FNV-1a specification: http://www.isthe.com/chongo/tech/comp/fnv/
    - Cross-version workflow: features.md "Cross-Version Copy/Paste"
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# FNV-1a 64-bit constants
FNV_OFFSET_BASIS_64: int = 0xCBF29CE484222325
FNV_PRIME_64: int = 0x100000001B3


def fnv1a_64(data: bytes) -> int:
    """Calculate FNV-1a 64-bit hash of byte data.

    The FNV-1a (Fowler-Noll-Vo) hash is a fast, non-cryptographic hash function
    with excellent distribution properties. The 'a' variant processes bytes before
    multiplication, which improves avalanche characteristics.

    Algorithm:
        1. Initialize hash to FNV offset basis (0xcbf29ce484222325)
        2. For each byte:
           a. XOR hash with byte value
           b. Multiply hash by FNV prime (0x100000001b3)
        3. Return final hash & 0xFFFFFFFFFFFFFFFF (64-bit mask)

    Args:
        data: Raw bytes to hash (sprite pixel data, metadata, etc.)

    Returns:
        64-bit unsigned integer hash value

    Examples:
        >>> fnv1a_64(b'')
        14695981039346656037
        >>> fnv1a_64(b'foo')
        15902901984413996407
    """
    if not data:
        return FNV_OFFSET_BASIS_64

    hash_value = FNV_OFFSET_BASIS_64

    for byte in data:
        hash_value ^= byte
        hash_value = (hash_value * FNV_PRIME_64) & 0xFFFFFFFFFFFFFFFF

    return hash_value


def calculate_sprite_hash(pixel_data: bytes, width: int, height: int) -> int:
    """Calculate hash of sprite pixel data including dimensions.

    Creates a unique fingerprint by hashing pixel data + dimensions. Including
    dimensions prevents hash collisions between sprites with identical pixels
    but different sizes (e.g., 32x32 vs 64x64 versions).

    Hash input format:
        width (4 bytes LE) + height (4 bytes LE) + pixel_data

    Args:
        pixel_data: Raw RGBA pixel bytes (width * height * 4 bytes)
        width: Sprite width in pixels
        height: Sprite height in pixels

    Returns:
        64-bit hash uniquely identifying this sprite's visual appearance

    Raises:
        ValueError: If pixel_data length doesn't match width * height * 4

    Examples:
        >>> white_2x2 = b'\\xff\\xff\\xff\\xff' * 4  # 4 white pixels
        >>> hash_val = calculate_sprite_hash(white_2x2, 2, 2)
        >>> isinstance(hash_val, int)
        True
    """
    expected_size = width * height * 4  # RGBA = 4 bytes per pixel
    if len(pixel_data) != expected_size:
        msg = (
            f"Pixel data size mismatch: expected {expected_size} bytes "
            f"for {width}x{height} sprite, got {len(pixel_data)} bytes"
        )
        raise ValueError(msg)

    # Prepend dimensions to prevent hash collisions between different sizes
    dimension_bytes = width.to_bytes(4, "little") + height.to_bytes(4, "little")
    hash_input = dimension_bytes + pixel_data

    return fnv1a_64(hash_input)


class SpriteHashMatcher:
    """Bidirectional hash table for matching sprites across client versions.

    This class maintains two mappings:
        1. hash → [sprite_ids]: Find which sprite IDs have this visual appearance
        2. sprite_id → hash: Get the visual fingerprint of a sprite ID

    Use case:
        When copying from Client 13.x to Client 7.4, sprite IDs differ but visuals
        may be identical. Hash matching allows finding equivalent sprites:

        1. Calculate hash of source sprite (e.g., ID 1234 in 13.x)
        2. Look up hash in target client (7.4)
        3. Find matching sprite ID (e.g., ID 5678 in 7.4)
        4. Replace ID during paste operation

    Thread safety: Not thread-safe. Use external synchronization if needed.

    Examples:
        >>> matcher = SpriteHashMatcher()
        >>> sprite_data = b'\\xff' * 16  # 2x2 white sprite
        >>> matcher.add_sprite(100, sprite_data, 2, 2)
        >>> hash_val = calculate_sprite_hash(sprite_data, 2, 2)
        >>> matcher.find_by_hash(hash_val)
        [100]
    """

    def __init__(self) -> None:
        """Initialize empty hash tables."""
        self._hash_to_ids: dict[int, list[int]] = {}
        self._id_to_hash: dict[int, int] = {}

    def add_sprite(self, sprite_id: int, pixel_data: bytes, width: int, height: int) -> None:
        """Register a sprite in the hash table.

        Calculates hash of pixel data and creates bidirectional mapping.
        Multiple sprite IDs can map to the same hash (visual duplicates).

        Args:
            sprite_id: Unique sprite identifier (from .dat file)
            pixel_data: Raw RGBA pixel bytes
            width: Sprite width in pixels
            height: Sprite height in pixels

        Raises:
            ValueError: If pixel_data size doesn't match dimensions
        """
        hash_value = calculate_sprite_hash(pixel_data, width, height)

        # Forward mapping: hash → ids (one-to-many)
        if hash_value not in self._hash_to_ids:
            self._hash_to_ids[hash_value] = []
        if sprite_id not in self._hash_to_ids[hash_value]:
            self._hash_to_ids[hash_value].append(sprite_id)

        # Reverse mapping: id → hash (one-to-one)
        self._id_to_hash[sprite_id] = hash_value

    def find_by_hash(self, hash_value: int) -> list[int]:
        """Find all sprite IDs matching a hash value.

        Returns list of sprite IDs that have identical pixel data (and dimensions).
        Empty list if no matches found.

        Args:
            hash_value: 64-bit sprite hash to search for

        Returns:
            List of sprite IDs with matching visual appearance (may be empty)

        Examples:
            >>> matcher = SpriteHashMatcher()
            >>> matcher.add_sprite(100, b'\\xff' * 16, 2, 2)
            >>> hash_val = calculate_sprite_hash(b'\\xff' * 16, 2, 2)
            >>> matcher.find_by_hash(hash_val)
            [100]
        """
        return self._hash_to_ids.get(hash_value, []).copy()

    def get_hash(self, sprite_id: int) -> int | None:
        """Get hash value for a sprite ID.

        Args:
            sprite_id: Sprite identifier to look up

        Returns:
            64-bit hash value, or None if sprite_id not registered

        Examples:
            >>> matcher = SpriteHashMatcher()
            >>> matcher.add_sprite(100, b'\\xff' * 16, 2, 2)
            >>> hash_val = matcher.get_hash(100)
            >>> hash_val is not None
            True
        """
        return self._id_to_hash.get(sprite_id)

    def clear(self) -> None:
        """Remove all sprites from the hash table.

        Resets to empty state. Useful when switching client versions or
        reloading sprite data.
        """
        self._hash_to_ids.clear()
        self._id_to_hash.clear()
