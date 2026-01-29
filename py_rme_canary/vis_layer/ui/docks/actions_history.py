from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QListWidget


class ActionsHistoryDock:
    def __init__(self, editor) -> None:
        self._editor = editor
        self.dock: Optional[QDockWidget] = None
        self.list: Optional[QListWidget] = None

    def build(self, *, title: str = "Actions History") -> QDockWidget:
        dock = QDockWidget(title, self._editor)
        dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
            | Qt.DockWidgetArea.BottomDockWidgetArea
        )

        lw = QListWidget(dock)
        lw.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        dock.setWidget(lw)

        self.dock = dock
        self.list = lw
        self.refresh()
        return dock

    def _format_action(self, action) -> str:
        try:
            desc = getattr(action, "describe", None)
            if callable(desc):
                d = str(desc())
                if d:
                    return d
        except Exception:
            pass

        try:
            bid = int(getattr(action, "brush_id", 0))
        except Exception:
            bid = 0
        try:
            n = len(getattr(action, "tiles_after", {}) or {})
        except Exception:
            n = 0

        if bid == 0:
            return f"Action (tiles={n})"
        return f"Brush {bid} (tiles={n})"

    def refresh(self) -> None:
        if self.list is None:
            return

        try:
            hist = self._editor.session.history
            undo = list(getattr(hist, "undo_stack", []) or [])
            redo_len = len(getattr(hist, "redo_stack", []) or [])
        except Exception:
            undo = []
            redo_len = 0

        self.list.blockSignals(True)
        self.list.clear()

        if redo_len:
            self.list.addItem(f"Redo available: {redo_len}")
            self.list.addItem("—")

        # Most recent first.
        for action in reversed(undo):
            self.list.addItem(self._format_action(action))

        if not undo and not redo_len:
            self.list.addItem("(empty)")

        self.list.blockSignals(False)

        # Keep dock title informative but stable.
        if self.dock is not None:
            self.dock.setWindowTitle("Actions History")
