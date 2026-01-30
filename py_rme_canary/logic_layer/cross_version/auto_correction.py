"""Auto-correction of item IDs using sprite hash matching.

Automatically finds and corrects wrong ServerIDs when sprites exist but
are mapped to incorrect IDs (e.g., after version migrations or corrupted maps).

Uses FNV-1a sprite hash matching to identify the correct ID.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.logic_layer.cross_version.sprite_hash import SpriteHashMatcher


@dataclass(frozen=True, slots=True)
class CorrectionResult:
    """Result of auto-correction operation.

    Attributes:
        original_id: The incorrect/wrong ID that was found
        corrected_id: The correct ID determined by sprite matching
        confidence: Confidence score (0.0-1.0), 1.0 = exact match
        method: Correction method used ("sprite_hash", "manual", etc.)
    """

    original_id: int
    corrected_id: int
    confidence: float
    method: str


class ItemIdAutoCorrector:
    """Auto-corrects item IDs using sprite hash matching.

    When an item ID doesn't match the expected sprite, this corrector
    can find the correct ID by comparing sprite hashes.

    Features:
    - Exact sprite hash matching
    - Confidence scoring
    - Batch correction support
    - Correction history tracking

    Example:
        >>> corrector = ItemIdAutoCorrector(sprite_matcher)
        >>> result = corrector.correct_item_id(12345)
        >>> if result and result.confidence > 0.9:
        ...     print(f"Corrected {result.original_id} → {result.corrected_id}")
    """

    def __init__(self, sprite_matcher: SpriteHashMatcher) -> None:
        """Initialize auto-corrector.

        Args:
            sprite_matcher: Configured sprite hash matcher with loaded sprites
        """
        self._matcher = sprite_matcher
        self._correction_history: list[CorrectionResult] = []

    def correct_item_id(
        self,
        item_id: int,
        *,
        min_confidence: float = 0.95,
    ) -> CorrectionResult | None:
        """Attempt to correct a single item ID.

        Args:
            item_id: The item ID to check/correct
            min_confidence: Minimum confidence required (0.0-1.0)

        Returns:
            CorrectionResult if correction found with sufficient confidence,
            None if no correction needed or confidence too low
        """
        # Get sprite hash for this item ID
        sprite_hash = self._matcher.get_hash(item_id)
        if sprite_hash is None:
            # No sprite data for this ID - cannot correct
            return None

        # Find all IDs with matching hash
        matching_ids = self._matcher.find_by_hash(sprite_hash)
        if not matching_ids:
            # No matches found
            return None

        if item_id in matching_ids and len(matching_ids) == 1:
            # Current ID is the only match - already correct
            return None

        # Find best alternative ID (prefer lower IDs for stability)
        alternative_ids = [mid for mid in matching_ids if mid != item_id]
        if not alternative_ids:
            return None

        corrected_id = min(alternative_ids)  # Prefer lowest ID

        # Don't "correct" if current ID is already the lowest
        if item_id < corrected_id:
            return None

        # Calculate confidence (exact hash match = 1.0)
        confidence = 1.0

        if confidence < min_confidence:
            return None

        result = CorrectionResult(
            original_id=item_id,
            corrected_id=corrected_id,
            confidence=confidence,
            method="sprite_hash",
        )

        self._correction_history.append(result)
        return result

    def correct_items_batch(
        self,
        item_ids: list[int],
        *,
        min_confidence: float = 0.95,
    ) -> dict[int, CorrectionResult]:
        """Correct multiple item IDs in batch.

        Args:
            item_ids: List of item IDs to check
            min_confidence: Minimum confidence required

        Returns:
            Dictionary mapping original_id → CorrectionResult for items
            that were corrected. Items that don't need correction or
            have low confidence are omitted.
        """
        corrections: dict[int, CorrectionResult] = {}

        for item_id in item_ids:
            result = self.correct_item_id(item_id, min_confidence=min_confidence)
            if result:
                corrections[item_id] = result

        return corrections

    def get_correction_history(self) -> list[CorrectionResult]:
        """Get history of all corrections made."""
        return list(self._correction_history)

    def clear_history(self) -> None:
        """Clear correction history."""
        self._correction_history.clear()

    def generate_correction_report(self) -> str:
        """Generate human-readable correction report.

        Returns:
            Formatted report string showing all corrections
        """
        if not self._correction_history:
            return "No corrections have been made."

        lines = ["Auto-Correction Report", "=" * 50, ""]

        for idx, result in enumerate(self._correction_history, 1):
            lines.append(f"{idx}. ID {result.original_id} → {result.corrected_id}")
            lines.append(f"   Confidence: {result.confidence:.1%}")
            lines.append(f"   Method: {result.method}")
            lines.append("")

        lines.append(f"Total corrections: {len(self._correction_history)}")

        return "\n".join(lines)
