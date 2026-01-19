"""Compatibility wrapper for the editor session.

The architecture proposal moves the implementation to `logic_layer/session/`.
This module keeps the legacy import path stable:

    from py_rme_canary.logic_layer.editor_session import EditorSession
"""

from __future__ import annotations

from py_rme_canary.logic_layer.session.editor import EditorSession

__all__ = ["EditorSession"]
