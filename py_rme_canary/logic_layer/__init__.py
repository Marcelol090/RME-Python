"""Logic layer: editing rules (brushes, auto-border, mirroring).

This package contains modular components organized into sub-packages:
- session/: Editor session management (selection, clipboard, gestures, move)
- borders/: Auto-border processing (neighbor masks, alignment, processor)
"""

# Re-export main classes for backward compatibility
from .borders import AutoBorderProcessor
from .drawing_options import DrawingOptions, TransparencyMode
from .session import EditorSession

__all__ = [
    "AutoBorderProcessor",
    "DrawingOptions",
    "EditorSession",
    "TransparencyMode",
]
