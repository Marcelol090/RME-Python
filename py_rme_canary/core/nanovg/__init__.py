"""NanoVG integration module for vector graphics overlay.

This module provides a NanoVG-like API for rendering
vector graphics overlays on the OpenGL map canvas.
"""

from __future__ import annotations

from .nanovg_opengl_adapter import NanoVGContext, NanoVGPaint

__all__ = ["NanoVGContext", "NanoVGPaint"]
