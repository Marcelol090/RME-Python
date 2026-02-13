"""Activity Bar Widget — Antigravity Style Sidebar."""

from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt, QSize, pyqtSignal, QEvent
from PyQt6.QtGui import QColor, QPainter, QIcon, QAction, QBrush, QPen
from PyQt6.QtWidgets import (
    QToolBar,
    QToolButton,
    QWidget,
    QVBoxLayout,
    QSizePolicy,
    QApplication
)

from py_rme_canary.vis_layer.ui.icons import activity_icons
from py_rme_canary.vis_layer.ui.theme import get_theme_manager


class ActivityButton(QToolButton):
    """Custom styled button for the activity bar."""

    def __init__(self, icon_key: str, tooltip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        icons = activity_icons()
        self.setIcon(icons.get(icon_key, QIcon()))
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setFixedSize(48, 48)
        self.setIconSize(QSize(28, 28))
        self.setAutoRaise(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        tm = get_theme_manager()
        c = tm.tokens["color"]

        # Background on hover/checked
        if self.isChecked() or self.underMouse():
            bg_color = QColor(c["state"]["hover"])
            if self.isChecked():
                bg_color = QColor(c["surface"]["secondary"])  # Slightly lighter for active

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg_color)
            # Draw rounded rect slightly smaller than button
            painter.drawRoundedRect(4, 4, self.width() - 8, self.height() - 8, 8, 8)

        # Active Indicator (Left strip)
        if self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(c["brand"]["primary"]))
            painter.drawRoundedRect(2, 10, 3, self.height() - 20, 1.5, 1.5)

        # Draw Icon (centered)
        icon = self.icon()
        if not icon.isNull():
            mode = QIcon.Mode.Normal
            if self.isChecked():
                mode = QIcon.Mode.Active
            elif not self.isEnabled():
                mode = QIcon.Mode.Disabled

            # Helper to center icon
            rect = self.rect()
            size = self.iconSize()
            x = (rect.width() - size.width()) // 2
            y = (rect.height() - size.height()) // 2

            # State based pixmap
            pixmap = icon.pixmap(size, mode, QIcon.State.On if self.isChecked() else QIcon.State.Off)
            painter.drawPixmap(x, y, pixmap)


class ActivityBar(QToolBar):
    """
    Vertical sidebar for switching between main views/docks.
    """

    activity_changed = pyqtSignal(str, bool)  # Emits (activity_id, is_active)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMovable(False)
        self.setOrientation(Qt.Orientation.Vertical)
        self.setFloatable(False)
        self.setIconSize(QSize(28, 28))
        # Transparent background, spacing handled by widget layout
        self.setStyleSheet("QToolBar { border: none; background: transparent; spacing: 4px; }")

        self._buttons: dict[str, ActivityButton] = {}
        self._callbacks: dict[str, Callable[[bool], None]] = {}

        # Spacer setup
        self._spacer = QWidget()
        self._spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._spacer_action = self.addWidget(self._spacer)

    def add_activity(
        self,
        uid: str,
        icon_key: str,
        tooltip: str,
        callback: Callable[[bool], None] | None = None,
        bottom: bool = False
    ) -> None:
        """
        Add an activity button.

        Args:
            uid: Unique identifier for the activity
            icon_key: Key for `activity_icons` dict
            tooltip: Tooltip text
            callback: Function(checked: bool) called on toggle
            bottom: If True, adds to bottom section (settings, etc.)
        """
        btn = ActivityButton(icon_key, tooltip, self)

        # Connect click handler
        # Note: we use a closure to capture uid
        btn.clicked.connect(lambda checked, u=uid: self._on_clicked(u, checked))

        if bottom:
            # Add after spacer
            self.addWidget(btn)
        else:
            # Add before spacer
            self.insertWidget(self._spacer_action, btn)

        self._buttons[uid] = btn
        if callback:
            self._callbacks[uid] = callback

    def set_active(self, uid: str, active: bool = True) -> None:
        """Programmatically set the active state of an activity."""
        if uid in self._buttons:
            btn = self._buttons[uid]
            if btn.isChecked() != active:
                btn.blockSignals(True)
                btn.setChecked(active)
                btn.blockSignals(False)
                # We trigger callback to ensure UI sync
                if uid in self._callbacks:
                    self._callbacks[uid](active)

    def _on_clicked(self, uid: str, checked: bool) -> None:
        # Toggle behavior:
        # If checking: deactivate others (radio behavior for top group usually)
        # If unchecking: allow it (toggle off)

        if checked:
            for key, btn in self._buttons.items():
                if key != uid and btn.isChecked():
                    # Check if we should enforce exclusivity.
                    # Usually "bottom" actions (settings) might be separate?
                    # For now, treat all as exclusive for clean UI.
                    btn.blockSignals(True)
                    btn.setChecked(False)
                    btn.blockSignals(False)
                    if key in self._callbacks:
                        self._callbacks[key](False)

        # Trigger this button's callback
        if uid in self._callbacks:
            self._callbacks[uid](checked)

        self.activity_changed.emit(uid, checked)
