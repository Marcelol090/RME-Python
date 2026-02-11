"""Modern Status Bar for the map editor.

Displays:
- Current position (X, Y, Z)
- Zoom level
- Selection info
- Map info
- Current tool/brush
- Memory usage
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QStatusBar,
    QWidget,
)

if TYPE_CHECKING:
    pass


class StatusBarSection(QFrame):
    """A section of the status bar with icon and text."""

    def __init__(self, icon: str = "", text: str = "", tooltip: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(4)

        if icon:
            self.icon_label = QLabel(icon)
            self.icon_label.setStyleSheet("font-size: 12px;")
            layout.addWidget(self.icon_label)
        else:
            self.icon_label = None

        self.text_label = QLabel(text)
        self.text_label.setStyleSheet("color: #A1A1AA; font-size: 11px;")
        layout.addWidget(self.text_label)

        if tooltip:
            self.setToolTip(tooltip)

        self.setStyleSheet(
            """
            StatusBarSection {
                background: transparent;
                border-left: 1px solid #363650;
                padding-left: 8px;
            }
        """
        )

    def set_text(self, text: str) -> None:
        """Update the text."""
        self.text_label.setText(text)

    def set_icon(self, icon: str) -> None:
        """Update the icon."""
        if self.icon_label:
            self.icon_label.setText(icon)


class PositionIndicator(StatusBarSection):
    """Shows current position (X, Y, Z)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(icon="Pos", text="0, 0, 7", tooltip="Current position (X, Y, Z)", parent=parent)

        self._x = 0
        self._y = 0
        self._z = 7

    def set_position(self, x: int, y: int, z: int) -> None:
        """Update position display."""
        self._x = x
        self._y = y
        self._z = z
        self.set_text(f"{x}, {y}, {z}")


class ZoomIndicator(StatusBarSection):
    """Shows current zoom level."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(icon="Zoom", text="100%", tooltip="Zoom level", parent=parent)

        self._zoom = 1.0

    def set_zoom(self, zoom: float) -> None:
        """Update zoom display."""
        self._zoom = zoom
        self.set_text(f"{int(zoom * 100)}%")


class SelectionIndicator(StatusBarSection):
    """Shows selection info."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(icon="SEL", text="No selection", tooltip="Selection info", parent=parent)

    def set_selection(self, count: int, width: int = 0, height: int = 0) -> None:
        """Update selection display."""
        if count == 0:
            self.set_text("No selection")
        elif width > 0 and height > 0:
            self.set_text(f"{count} tiles ({width}×{height})")
        else:
            self.set_text(f"{count} tile{'s' if count != 1 else ''}")


class BrushIndicator(StatusBarSection):
    """Shows current brush/tool."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(icon="BR", text="No brush", tooltip="Current brush", parent=parent)

    def set_brush(self, name: str, size: int = 1) -> None:
        """Update brush display."""
        if name:
            text = name
            if size > 1:
                text += f" ({size}×{size})"
            self.set_text(text)
        else:
            self.set_text("No brush")


class SelectionModeIndicator(StatusBarSection):
    """Shows current selection mode.

    Modes:
        - "normal": Standard selection
        - "additive": Add to selection (Shift)
        - "subtractive": Remove from selection (Ctrl)
        - "intersection": Intersect with selection (Shift+Ctrl)
    """

    # Mode configurations
    MODES = {
        "normal": ("N", "Normal", "#A1A1AA"),
        "additive": ("+", "Add", "#22C55E"),
        "subtractive": ("-", "Subtract", "#EF4444"),
        "intersection": ("INT", "Intersect", "#8B5CF6"),
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(icon="N", text="Normal", tooltip="Selection mode", parent=parent)
        self._mode = "normal"

    def set_mode(self, mode: str) -> None:
        """Update selection mode display.

        Args:
            mode: One of "normal", "additive", "subtractive", "intersection"
        """
        if mode not in self.MODES:
            mode = "normal"

        self._mode = mode
        icon, text, color = self.MODES[mode]

        self.set_icon(icon)
        self.set_text(text)
        self.text_label.setStyleSheet(f"color: {color}; font-size: 11px;")

    @property
    def mode(self) -> str:
        """Get current mode."""
        return self._mode


class MapInfoIndicator(StatusBarSection):
    """Shows map dimensions and tile count."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(icon="Map", text="No map", tooltip="Map info", parent=parent)

    def set_map_info(self, width: int, height: int, tile_count: int = 0) -> None:
        """Update map info display."""
        if width > 0 and height > 0:
            text = f"{width}×{height}"
            if tile_count > 0:
                text += f" ({tile_count:,} tiles)"
            self.set_text(text)
        else:
            self.set_text("No map")


class MemoryIndicator(StatusBarSection):
    """Shows memory usage."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(icon="MEM", text="0 MB", tooltip="Memory usage", parent=parent)

        # Update timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_memory)
        self._timer.start(5000)  # Update every 5 seconds

        self._update_memory()

    def _update_memory(self) -> None:
        """Update memory display."""
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            self.set_text(f"{memory_mb:.0f} MB")
        except ImportError:
            self.set_text("N/A")
        except Exception:
            pass


class LiveConnectionIndicator(StatusBarSection):
    """Displays live collaboration connection status.

    Shows a colored dot and text indicating the current state:
    - Disconnected (red)
    - Connecting / Reconnecting (yellow)
    - Connected (green, with user count)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(icon="LIVE", text="Offline", tooltip="Live Collaboration Status", parent=parent)
        self._user_count: int = 0

    def set_disconnected(self) -> None:
        """Show disconnected state."""
        self.set_icon("LIVE")
        self.set_text("Offline")
        self.setToolTip("Live Collaboration: Disconnected")
        self._update_color("#EF4444")
        self._user_count = 0

    def set_connecting(self) -> None:
        """Show connecting state."""
        self.set_icon("LIVE")
        self.set_text("Connecting...")
        self.setToolTip("Live Collaboration: Connecting")
        self._update_color("#EAB308")

    def set_reconnecting(self, attempt: int = 0) -> None:
        """Show reconnecting state."""
        self.set_icon("LIVE")
        text = "Reconnecting..."
        if attempt > 0:
            text = f"Reconnecting ({attempt})..."
        self.set_text(text)
        self.setToolTip(f"Live Collaboration: Reconnecting (attempt {attempt})")
        self._update_color("#EAB308")

    def set_connected(self, user_count: int = 0, *, is_host: bool = False) -> None:
        """Show connected state."""
        self.set_icon("LIVE")
        self._user_count = int(user_count)
        role = "Hosting" if is_host else "Connected"
        if user_count > 0:
            self.set_text(f"{role} ({user_count})")
        else:
            self.set_text(role)
        self.setToolTip(f"Live Collaboration: {role}")
        self._update_color("#22C55E")

    def update_user_count(self, count: int) -> None:
        """Update the displayed user count."""
        self._user_count = int(count)
        current = self.text_label.text()
        if "Connected" in current or "Hosting" in current:
            role = "Hosting" if "Hosting" in current else "Connected"
            if count > 0:
                self.set_text(f"{role} ({count})")
            else:
                self.set_text(role)

    def _update_color(self, hex_color: str) -> None:
        """Update the icon label color."""
        if self.icon_label:
            self.icon_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {hex_color};")


class ModernStatusBar(QStatusBar):
    """Modern status bar for the map editor.

    Usage:
        status_bar = ModernStatusBar()
        window.setStatusBar(status_bar)

        # Update sections
        status_bar.position.set_position(100, 200, 7)
        status_bar.zoom.set_zoom(1.5)
        status_bar.brush.set_brush("Grass", 3)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        # Left section - position and selection
        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        self.position = PositionIndicator()
        left_layout.addWidget(self.position)

        self.selection = SelectionIndicator()
        left_layout.addWidget(self.selection)

        self.selection_mode = SelectionModeIndicator()
        left_layout.addWidget(self.selection_mode)

        self.addWidget(left_container)

        # Center - message area (built-in)

        # Right section - brush, map, zoom, memory
        self.brush = BrushIndicator()
        self.addPermanentWidget(self.brush)

        self.map_info = MapInfoIndicator()
        self.addPermanentWidget(self.map_info)

        self.zoom = ZoomIndicator()
        self.addPermanentWidget(self.zoom)

        self.live_status = LiveConnectionIndicator()
        self.addPermanentWidget(self.live_status)

        self.memory = MemoryIndicator()
        self.addPermanentWidget(self.memory)

    def _apply_style(self) -> None:
        """Apply modern styling."""
        self.setStyleSheet(
            """
            QStatusBar {
                background: #1A1A2E;
                border-top: 1px solid #363650;
                color: #A1A1AA;
                min-height: 26px;
            }

            QStatusBar::item {
                border: none;
            }
        """
        )

    def show_message(self, message: str, timeout: int = 3000) -> None:
        """Show a temporary message."""
        self.showMessage(message, timeout)

    def show_permanent_message(self, message: str) -> None:
        """Show a permanent message (until cleared)."""
        self.showMessage(message, 0)

    def clear_message(self) -> None:
        """Clear the message."""
        self.clearMessage()
