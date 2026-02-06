"""Core rendering components.

This module provides foundational rendering infrastructure matching
the remeres-map-editor-redux architecture.

Components:
    - TextureArray: GL_TEXTURE_2D_ARRAY for sprite batching
    - ModernSpriteBatcher: High-performance sprite batching
    - AtlasManager: Manages sprite atlas allocation (future)
"""

from __future__ import annotations

from .modern_batcher import ModernSpriteBatcher
from .texture_array import TextureArray

__all__ = ["TextureArray", "ModernSpriteBatcher"]
