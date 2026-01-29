"""Cross-version compatibility layer for copy/paste between different client versions.

This module enables seamless copying of map areas between RME instances running
different Tibia client versions (e.g., 7.4, 10.x, 13.x). Features include:

- Sprite hash matching (FNV-1a) to find equivalent sprites across versions
- Automatic ID translation during paste operations
- Auto-correction of wrong IDs using sprite matching
- Support for multiple simultaneous RME instances
- Inter-instance data transfer via shared memory or IPC

See features.md for complete cross-version workflow documentation.
"""

from __future__ import annotations

from py_rme_canary.logic_layer.cross_version.auto_correction import (
    CorrectionResult,
    ItemIdAutoCorrector,
)
from py_rme_canary.logic_layer.cross_version.clipboard import (
    ClipboardData,
    CrossVersionClipboard,
    TranslationResult,
)
from py_rme_canary.logic_layer.cross_version.sprite_hash import (
    SpriteHashMatcher,
    calculate_sprite_hash,
    fnv1a_64,
)

__all__ = [
    # Sprite hashing
    "fnv1a_64",
    "calculate_sprite_hash",
    "SpriteHashMatcher",
    # Clipboard
    "CrossVersionClipboard",
    "ClipboardData",
    "TranslationResult",
    # Auto-correction
    "ItemIdAutoCorrector",
    "CorrectionResult",
]
