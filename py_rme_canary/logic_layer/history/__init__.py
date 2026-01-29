"""Undo/redo history primitives (new module path).

This package is a thin compatibility layer over `logic_layer/transactional_brush.py`.
"""

from .action import PaintAction
from .manager import HistoryManager
from .stroke import TransactionalBrushStroke

__all__ = [
    "HistoryManager",
    "PaintAction",
    "TransactionalBrushStroke",
]
