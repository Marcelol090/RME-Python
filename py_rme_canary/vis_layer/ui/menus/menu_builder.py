"""Context Menu Builder."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtGui import QAction, QCursor
from PyQt6.QtWidgets import QMenu, QWidget

from py_rme_canary.vis_layer.ui.theme import get_theme_manager


class ContextMenuBuilder:
    """Builder for creating context menus.

    Usage:
        menu = (ContextMenuBuilder(parent)
            .add_action("Copy", on_copy, "Ctrl+C")
            .add_separator()
            .add_submenu("Selection")
                .add_action("Select All", on_select_all)
                .end_submenu()
            .build())
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        self._parent = parent
        self._menu = QMenu(parent)
        self._current_menu = self._menu
        self._menu_stack: list[QMenu] = []

        # Apply styling from theme tokens
        tm = get_theme_manager()
        c = tm.tokens["color"]
        s = tm.tokens["spacing"]
        r = tm.tokens["radius"]

        self._menu.setStyleSheet(
            f"""
            QMenu {{
                background: {c["surface"]["elevated"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["md"]}px;
                padding: {s["xs"]}px;
                color: {c["text"]["primary"]};
            }}

            QMenu::item {{
                padding: {s["sm"]}px {s["lg"]}px {s["sm"]}px {s["lg"]}px;
                border-radius: {r["sm"]}px;
                margin: 2px;
            }}

            QMenu::item:selected {{
                background: {c["brand"]["primary"]};
                color: {c["surface"]["primary"]};
            }}

            QMenu::item:disabled {{
                color: {c["text"]["disabled"]};
            }}

            QMenu::separator {{
                background: {c["border"]["default"]};
                height: 1px;
                margin: {s["xs"]}px {s["sm"]}px;
            }}

            QMenu::icon {{
                margin-left: {s["sm"]}px;
            }}
        """
        )

    def add_action(
        self,
        text: str,
        callback: Callable[[], None] | None = None,
        shortcut: str | None = None,
        icon: str | None = None,
        enabled: bool = True,
        checkable: bool = False,
        checked: bool = False,
    ) -> ContextMenuBuilder:
        """Add an action to the menu."""
        display = f"{icon} {text}" if icon else text
        action = QAction(display, self._current_menu)

        if callback:
            action.triggered.connect(callback)
        if shortcut:
            action.setShortcut(shortcut)

        action.setEnabled(enabled)
        action.setCheckable(checkable)
        action.setChecked(checked)

        self._current_menu.addAction(action)
        return self

    def add_separator(self) -> ContextMenuBuilder:
        """Add a separator line."""
        self._current_menu.addSeparator()
        return self

    def add_submenu(self, title: str, icon: str | None = None) -> ContextMenuBuilder:
        """Start a submenu."""
        display = f"{icon} {title}" if icon else title
        submenu = self._current_menu.addMenu(display)
        submenu.setStyleSheet(self._menu.styleSheet())

        self._menu_stack.append(self._current_menu)
        self._current_menu = submenu
        return self

    def end_submenu(self) -> ContextMenuBuilder:
        """End current submenu."""
        if self._menu_stack:
            self._current_menu = self._menu_stack.pop()
        return self

    def build(self) -> QMenu:
        """Build and return the menu."""
        return self._menu

    def exec_at_cursor(self) -> QAction | None:
        """Execute menu at cursor position."""
        return self._menu.exec(QCursor.pos())
