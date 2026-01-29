from __future__ import annotations

from py_rme_canary.logic_layer.session.selection_modes import SelectionDepthMode


def toggle_selection_mode(editor) -> None:
    editor._toggle_selection_mode()


def set_selection_depth(editor, mode: SelectionDepthMode | str) -> None:
    editor._set_selection_depth_mode(mode)
