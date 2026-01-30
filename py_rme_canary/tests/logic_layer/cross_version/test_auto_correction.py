"""Tests for auto-correction system."""

from __future__ import annotations

import pytest

from py_rme_canary.logic_layer.cross_version.auto_correction import (
    CorrectionResult,
    ItemIdAutoCorrector,
)
from py_rme_canary.logic_layer.cross_version.sprite_hash import SpriteHashMatcher


@pytest.fixture
def sprite_matcher() -> SpriteHashMatcher:
    """Create a configured sprite matcher with test data."""
    matcher = SpriteHashMatcher()

    # Create test pixel data
    # Same sprite data for IDs 100 and 200 (cross-version scenario)
    same_pixels = b"\x12\x34\x56\x78" * 64  # 256 bytes = 64 pixels
    unique_pixels = b"\xff\x00\xaa\xbb" * 64  # Different sprite

    matcher.add_sprite(sprite_id=100, pixel_data=same_pixels, width=8, height=8)
    matcher.add_sprite(sprite_id=200, pixel_data=same_pixels, width=8, height=8)  # Same sprite
    matcher.add_sprite(sprite_id=300, pixel_data=unique_pixels, width=8, height=8)

    return matcher


@pytest.fixture
def corrector(sprite_matcher: SpriteHashMatcher) -> ItemIdAutoCorrector:
    """Create auto-corrector with test matcher."""
    return ItemIdAutoCorrector(sprite_matcher)


def test_no_correction_needed_unique_sprite(corrector: ItemIdAutoCorrector) -> None:
    """Test that unique sprites don't get corrected."""
    result = corrector.correct_item_id(300)

    assert result is None


def test_no_correction_for_missing_sprite(corrector: ItemIdAutoCorrector) -> None:
    """Test handling of IDs with no sprite data."""
    result = corrector.correct_item_id(999)

    assert result is None


def test_correct_to_lower_id(corrector: ItemIdAutoCorrector) -> None:
    """Test that correction prefers lower IDs."""
    # ID 200 has same sprite as ID 100, should correct to 100
    result = corrector.correct_item_id(200)

    assert result is not None
    assert result.original_id == 200
    assert result.corrected_id == 100
    assert result.confidence == 1.0
    assert result.method == "sprite_hash"


def test_correction_respects_min_confidence(
    sprite_matcher: SpriteHashMatcher,
) -> None:
    """Test that low confidence corrections are rejected."""
    corrector = ItemIdAutoCorrector(sprite_matcher)

    # Request impossibly high confidence
    result = corrector.correct_item_id(200, min_confidence=1.5)

    assert result is None


def test_batch_correction(corrector: ItemIdAutoCorrector) -> None:
    """Test batch correction of multiple IDs."""
    items = [100, 200, 300, 999]

    corrections = corrector.correct_items_batch(items)

    # Only ID 200 should be corrected (to 100)
    assert len(corrections) == 1
    assert 200 in corrections
    assert corrections[200].corrected_id == 100


def test_correction_history(corrector: ItemIdAutoCorrector) -> None:
    """Test that corrections are tracked in history."""
    corrector.correct_item_id(200)
    corrector.correct_item_id(300)  # No correction
    corrector.correct_item_id(200)  # Duplicate

    history = corrector.get_correction_history()

    # Should have 2 entries (300 didn't need correction)
    assert len(history) == 2
    assert all(isinstance(r, CorrectionResult) for r in history)


def test_clear_history(corrector: ItemIdAutoCorrector) -> None:
    """Test clearing correction history."""
    corrector.correct_item_id(200)
    assert len(corrector.get_correction_history()) == 1

    corrector.clear_history()
    assert len(corrector.get_correction_history()) == 0


def test_generate_report_empty(corrector: ItemIdAutoCorrector) -> None:
    """Test report generation with no corrections."""
    report = corrector.generate_correction_report()

    assert "No corrections" in report


def test_generate_report_with_corrections(corrector: ItemIdAutoCorrector) -> None:
    """Test report generation with corrections."""
    corrector.correct_item_id(200)

    report = corrector.generate_correction_report()

    assert "Auto-Correction Report" in report
    assert "200 → 100" in report
    assert "100.0%" in report
    assert "sprite_hash" in report
    assert "Total corrections: 1" in report


def test_correction_result_immutability() -> None:
    """Test that CorrectionResult is immutable."""
    result = CorrectionResult(
        original_id=200,
        corrected_id=100,
        confidence=1.0,
        method="sprite_hash",
    )

    with pytest.raises(AttributeError):
        result.original_id = 999  # type: ignore[misc]


def test_no_self_correction(corrector: ItemIdAutoCorrector) -> None:
    """Test that IDs don't get corrected to themselves."""
    # ID 100 has same sprite as 200, but shouldn't correct to itself
    result = corrector.correct_item_id(100)

    # Should suggest ID 200 since it's the alternative
    # But wait - we prefer LOWER IDs, so 100 is already the lowest
    # Therefore no correction needed
    assert result is None
