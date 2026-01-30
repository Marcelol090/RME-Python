"""Tests for cross-version clipboard with ID translation."""

from __future__ import annotations

import pytest

from py_rme_canary.core.data import Item, Tile
from py_rme_canary.core.data.creature import Monster
from py_rme_canary.logic_layer.cross_version.clipboard import (
    CrossVersionClipboard,
)
from py_rme_canary.logic_layer.cross_version.sprite_hash import SpriteHashMatcher


@pytest.fixture
def sprite_matcher() -> SpriteHashMatcher:
    """Create sprite matcher with test data."""
    matcher = SpriteHashMatcher()

    # Same visual sprite in different versions
    white_sprite = b"\xff\xff\xff\xff" * 4  # 2x2 white
    matcher.add_sprite(100, white_sprite, 2, 2)  # Version 7.4
    matcher.add_sprite(200, white_sprite, 2, 2)  # Version 13.x

    # Different sprites
    black_sprite = b"\x00\x00\x00\xff" * 4
    matcher.add_sprite(101, black_sprite, 2, 2)  # Version 7.4
    matcher.add_sprite(201, black_sprite, 2, 2)  # Version 13.x

    return matcher


@pytest.fixture
def clipboard() -> CrossVersionClipboard:
    """Create empty cross-version clipboard."""
    return CrossVersionClipboard()


def test_clipboard_copy_single_tile(clipboard: CrossVersionClipboard) -> None:
    """Test copying a single tile to clipboard."""
    tile = Tile(x=100, y=100, z=7, ground=Item(id=100))

    tiles = [tile]
    result = clipboard.copy(tiles, source_version="7.4")

    assert result.success
    assert result.tile_count == 1
    assert clipboard.has_data()


def test_clipboard_paste_without_translation(clipboard: CrossVersionClipboard) -> None:
    """Test pasting without sprite matching (same version)."""
    # Copy
    tile = Tile(x=100, y=100, z=7, ground=Item(id=100))
    clipboard.copy([tile], source_version="13.x")

    # Paste
    pasted = clipboard.paste(target_version="13.x")

    assert len(pasted) == 1
    assert pasted[0].ground is not None
    assert pasted[0].ground.id == 100  # Same ID


def test_clipboard_paste_with_translation(
    clipboard: CrossVersionClipboard,
    sprite_matcher: SpriteHashMatcher,
) -> None:
    """Test pasting with ID translation across versions."""
    # Copy from 7.4
    tile = Tile(x=100, y=100, z=7, ground=Item(id=100))
    clipboard.copy([tile], source_version="7.4")

    # Paste to 13.x with translation
    pasted = clipboard.paste(target_version="13.x", sprite_matcher=sprite_matcher)

    assert len(pasted) == 1
    assert pasted[0].ground is not None
    # Should translate to ID 200 (matching sprite in v13.x)
    assert pasted[0].ground.id == 200


def test_clipboard_paste_no_match_keeps_original(
    clipboard: CrossVersionClipboard,
    sprite_matcher: SpriteHashMatcher,
) -> None:
    """Test that items without sprite match keep original ID."""
    # Copy item with ID that doesn't exist in matcher
    tile = Tile(x=100, y=100, z=7, ground=Item(id=999))
    clipboard.copy([tile], source_version="7.4")

    # Paste with matcher
    pasted = clipboard.paste(target_version="13.x", sprite_matcher=sprite_matcher)

    assert len(pasted) == 1
    assert pasted[0].ground is not None
    assert pasted[0].ground.id == 999  # Keeps original


def test_clipboard_translate_multiple_items(
    clipboard: CrossVersionClipboard,
    sprite_matcher: SpriteHashMatcher,
) -> None:
    """Test translating tile with multiple items."""
    tile = Tile(
        x=100,
        y=100,
        z=7,
        ground=Item(id=100),
        items=[Item(id=101), Item(id=999)],  # 999 has no match
    )

    clipboard.copy([tile], source_version="7.4")
    pasted = clipboard.paste(target_version="13.x", sprite_matcher=sprite_matcher)

    assert len(pasted) == 1
    t = pasted[0]
    assert t.ground is not None
    assert t.ground.id == 200  # Translated
    assert len(t.items) == 2
    assert t.items[0].id == 201  # Translated
    assert t.items[1].id == 999  # Kept original


def test_clipboard_translate_creature(
    clipboard: CrossVersionClipboard,
    sprite_matcher: SpriteHashMatcher,
) -> None:
    """Test that creatures are preserved during paste (no translation yet)."""
    tile = Tile(x=100, y=100, z=7)
    creature = Monster(name="Dragon", direction=2)

    # Create tile with monster
    tile_with_monster = Tile(
        x=tile.x,
        y=tile.y,
        z=tile.z,
        ground=tile.ground,
        items=tile.items,
        monsters=[creature],
    )

    clipboard.copy([tile_with_monster], source_version="7.4")
    pasted = clipboard.paste(target_version="13.x", sprite_matcher=sprite_matcher)

    assert len(pasted) == 1
    assert len(pasted[0].monsters) == 1
    # Creature should be preserved
    assert pasted[0].monsters[0].name == "Dragon"


def test_clipboard_clear(clipboard: CrossVersionClipboard) -> None:
    """Test clearing clipboard data."""
    tile = Tile(x=100, y=100, z=7)
    clipboard.copy([tile], source_version="7.4")

    assert clipboard.has_data()

    clipboard.clear()

    assert not clipboard.has_data()


def test_clipboard_get_stats(clipboard: CrossVersionClipboard) -> None:
    """Test getting clipboard statistics."""
    tiles = [
        Tile(x=100, y=100, z=7, ground=Item(id=100)),
        Tile(x=101, y=100, z=7, ground=Item(id=100)),
        Tile(x=102, y=100, z=7, ground=Item(id=100)),
    ]

    clipboard.copy(tiles, source_version="13.x")
    stats = clipboard.get_stats()

    assert stats["tile_count"] == 3
    assert stats["source_version"] == "13.x"
    assert stats["has_data"] is True
