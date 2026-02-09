from __future__ import annotations

import re
from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)


def _normalize_action_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("&", "").strip())


@dataclass(slots=True)
class CommandEntry:
    action: QAction
    label: str
    path: str
    shortcut: str


class CommandPaletteDialog(QDialog):
    def __init__(self, parent=None, *, entries: list[CommandEntry] | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.setModal(True)
        self.resize(640, 420)

        self._all_entries: list[CommandEntry] = list(entries or [])
        self._filtered_entries: list[CommandEntry] = list(self._all_entries)
        self.last_executed: str = ""

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("Search Commands")
        title.setObjectName("commandPaletteTitle")
        title.setStyleSheet("font-size: 14px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        self._search = QLineEdit(self)
        self._search.setPlaceholderText("Type a command (Ctrl+K)")
        self._search.textChanged.connect(self._apply_filter)
        self._search.returnPressed.connect(self._trigger_selected)
        layout.addWidget(self._search)

        self._list = QListWidget(self)
        self._list.itemActivated.connect(lambda _item: self._trigger_selected())
        self._list.itemDoubleClicked.connect(lambda _item: self._trigger_selected())
        layout.addWidget(self._list, 1)

        self._hint = QLabel("Enter to run • Esc to close")
        self._hint.setStyleSheet("color: #9ca3af; font-size: 11px;")
        layout.addWidget(self._hint)

        self._refresh_list()
        self._search.setFocus()
        self._search.selectAll()

    @staticmethod
    def collect_from_editor(editor) -> list[CommandEntry]:
        seen: set[int] = set()
        entries: list[CommandEntry] = []

        def add_action(action: QAction, path: str) -> None:
            if action.isSeparator():
                return
            text = _normalize_action_text(action.text())
            if not text:
                return
            if not action.isEnabled():
                return
            ident = id(action)
            if ident in seen:
                return
            seen.add(ident)
            shortcut = action.shortcut().toString()
            entries.append(
                CommandEntry(
                    action=action,
                    label=text,
                    path=str(path),
                    shortcut=str(shortcut),
                )
            )

        def walk_menu(menu, menu_path: list[str]) -> None:
            for action in menu.actions():
                sub = action.menu()
                if sub is not None:
                    name = _normalize_action_text(action.text())
                    next_path = [*menu_path, name] if name else list(menu_path)
                    walk_menu(sub, next_path)
                    continue
                add_action(action, " > ".join(p for p in menu_path if p))

        menubar = editor.menuBar()
        for top_action in menubar.actions():
            submenu = top_action.menu()
            if submenu is None:
                continue
            top_name = _normalize_action_text(top_action.text())
            walk_menu(submenu, [top_name] if top_name else [])

        for action in editor.actions():
            add_action(action, "Global")

        entries.sort(key=lambda entry: (entry.path, entry.label))
        return entries

    @classmethod
    def from_editor(cls, editor) -> CommandPaletteDialog:
        return cls(editor, entries=cls.collect_from_editor(editor))

    def _apply_filter(self, query: str) -> None:
        terms = [token for token in str(query).lower().split() if token]
        if not terms:
            self._filtered_entries = list(self._all_entries)
            self._refresh_list()
            return

        out: list[CommandEntry] = []
        for entry in self._all_entries:
            haystack = f"{entry.label} {entry.path} {entry.shortcut}".lower()
            if all(term in haystack for term in terms):
                out.append(entry)
        self._filtered_entries = out
        self._refresh_list()

    def _refresh_list(self) -> None:
        self._list.clear()
        for index, entry in enumerate(self._filtered_entries):
            shortcut = f" [{entry.shortcut}]" if entry.shortcut else ""
            path = f"  {entry.path}" if entry.path else ""
            item = QListWidgetItem(f"{entry.label}{shortcut}")
            item.setToolTip(path.strip())
            item.setData(Qt.ItemDataRole.UserRole, int(index))
            self._list.addItem(item)
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _trigger_selected(self) -> None:
        item = self._list.currentItem()
        if item is None:
            return
        index = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(index, int):
            return
        if index < 0 or index >= len(self._filtered_entries):
            return
        entry = self._filtered_entries[index]
        self.last_executed = entry.label
        entry.action.trigger()
        self.accept()
