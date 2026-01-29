"""Modern rich tooltips with animations.

Provides beautiful, informative tooltips with:
- Smooth fade-in animation
- Icon + title + description layout
- Keyboard shortcut display
- Consistent styling
"""
from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class RichTooltip(QWidget):
    """Modern rich tooltip with icon, title, description, and shortcut.

    Usage:
        tooltip = RichTooltip(
            title="Terrain Brush",
            description="Paint ground tiles with auto-bordering",
            shortcut="B",
            icon="🎨"
        )
        tooltip.show_at(QPoint(100, 100))
    """

    def __init__(
        self,
        title: str,
        description: str = "",
        shortcut: str = "",
        icon: str = "",
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)

        self._title = title
        self._description = description
        self._shortcut = shortcut
        self._icon = icon

        self._setup_ui()
        self._setup_style()
        self._setup_animation()

    def _setup_ui(self) -> None:
        """Initialize UI layout."""
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Main container
        container = QWidget(self)
        container.setObjectName("tooltipContainer")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header row (icon + title + shortcut)
        header = QHBoxLayout()
        header.setSpacing(8)

        # Icon
        if self._icon:
            icon_label = QLabel(self._icon)
            icon_label.setStyleSheet("font-size: 16px;")
            header.addWidget(icon_label)

        # Title
        title_label = QLabel(self._title)
        title_label.setObjectName("tooltipTitle")
        header.addWidget(title_label)

        header.addStretch()

        # Shortcut badge
        if self._shortcut:
            shortcut_label = QLabel(self._shortcut)
            shortcut_label.setObjectName("tooltipShortcut")
            header.addWidget(shortcut_label)

        layout.addLayout(header)

        # Description
        if self._description:
            desc_label = QLabel(self._description)
            desc_label.setObjectName("tooltipDescription")
            desc_label.setWordWrap(True)
            desc_label.setMaximumWidth(250)
            layout.addWidget(desc_label)

    def _setup_style(self) -> None:
        """Apply modern styling."""
        self.setStyleSheet("""
            #tooltipContainer {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2A2A3E, stop:1 #1E1E2E);
                border: 1px solid #363650;
                border-radius: 10px;
            }

            #tooltipTitle {
                color: #E5E5E7;
                font-size: 13px;
                font-weight: 600;
            }

            #tooltipDescription {
                color: #A1A1AA;
                font-size: 11px;
            }

            #tooltipShortcut {
                background: #363650;
                color: #A1A1AA;
                font-size: 10px;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                padding: 3px 6px;
                border-radius: 4px;
            }
        """)

    def _setup_animation(self) -> None:
        """Setup fade-in animation."""
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(150)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_at(self, pos: QPoint, delay_ms: int = 0) -> None:
        """Show tooltip at position with optional delay.

        Args:
            pos: Screen position to show tooltip
            delay_ms: Delay before showing (0 = immediate)
        """
        def _show() -> None:
            # Adjust position to avoid screen edges
            self.adjustSize()
            self.move(pos)
            self.show()

            # Fade in
            self._fade_anim.stop()
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.start()

        if delay_ms > 0:
            QTimer.singleShot(delay_ms, _show)
        else:
            _show()

    def hide_animated(self) -> None:
        """Hide tooltip with fade-out animation."""
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self._opacity_effect.opacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self.hide)
        self._fade_anim.start()


class TooltipManager:
    """Manages tooltip display for widgets.

    Usage:
        manager = TooltipManager()
        manager.register(
            widget=my_button,
            title="Save Map",
            description="Save the current map to disk",
            shortcut="Ctrl+S",
            icon="💾"
        )
    """

    _instance: TooltipManager | None = None

    def __init__(self) -> None:
        self._current_tooltip: RichTooltip | None = None
        self._hover_timer: QTimer | None = None
        self._delay_ms = 500  # Default hover delay

    @classmethod
    def instance(cls) -> TooltipManager:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(
        self,
        widget: QWidget,
        title: str,
        description: str = "",
        shortcut: str = "",
        icon: str = "",
        delay_ms: int | None = None
    ) -> None:
        """Register a widget for rich tooltips.

        Args:
            widget: Widget to add tooltip to
            title: Tooltip title
            description: Detailed description
            shortcut: Keyboard shortcut text
            icon: Emoji or text icon
            delay_ms: Custom delay (or use default)
        """
        delay = delay_ms if delay_ms is not None else self._delay_ms

        # Store tooltip data on widget
        widget.setProperty("_tooltip_title", title)
        widget.setProperty("_tooltip_desc", description)
        widget.setProperty("_tooltip_shortcut", shortcut)
        widget.setProperty("_tooltip_icon", icon)
        widget.setProperty("_tooltip_delay", delay)

        # Disable default tooltip
        widget.setToolTip("")

        # Install event filter (this is a simplified approach)
        # In production, would need proper event filter installation

    def show_tooltip(
        self,
        pos: QPoint,
        title: str,
        description: str = "",
        shortcut: str = "",
        icon: str = "",
    ) -> None:
        """Show a tooltip at the specified position."""
        self.hide_tooltip()

        self._current_tooltip = RichTooltip(
            title=title,
            description=description,
            shortcut=shortcut,
            icon=icon
        )
        self._current_tooltip.show_at(pos)

    def hide_tooltip(self) -> None:
        """Hide current tooltip."""
        if self._current_tooltip:
            self._current_tooltip.hide_animated()
            self._current_tooltip = None


class StatusToast(QWidget):
    """Toast notification for status messages.

    Shows temporary notifications that auto-dismiss.
    """

    def __init__(
        self,
        message: str,
        variant: str = "info",  # info, success, warning, error
        duration_ms: int = 3000,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._message = message
        self._variant = variant
        self._duration = duration_ms

        self._setup_ui()
        self._setup_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Icon based on variant
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌"
        }
        icon = icons.get(self._variant, "ℹ️")

        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)

        message_label = QLabel(self._message)
        message_label.setStyleSheet("""
            color: #E5E5E7;
            font-size: 13px;
            font-weight: 500;
        """)
        layout.addWidget(message_label)

    def _setup_style(self) -> None:
        """Apply styling based on variant."""
        colors = {
            "info": "#3B82F6",
            "success": "#10B981",
            "warning": "#F59E0B",
            "error": "#EF4444"
        }
        accent = colors.get(self._variant, "#3B82F6")

        self.setStyleSheet(f"""
            StatusToast {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2A2A3E, stop:1 #1E1E2E);
                border: 1px solid {accent};
                border-left: 4px solid {accent};
                border-radius: 8px;
            }}
        """)

    def show_toast(self, screen_pos: QPoint | None = None) -> None:
        """Show the toast notification."""
        self.adjustSize()

        if screen_pos:
            self.move(screen_pos)

        # Opacity effect
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        # Fade in
        fade_in = QPropertyAnimation(effect, b"opacity")
        fade_in.setDuration(200)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.show()
        fade_in.start()

        # Auto dismiss
        QTimer.singleShot(self._duration, self._dismiss)

    def _dismiss(self) -> None:
        """Dismiss with fade-out."""
        effect = self.graphicsEffect()
        if not effect:
            self.hide()
            return

        fade_out = QPropertyAnimation(effect, b"opacity")
        fade_out.setDuration(200)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.finished.connect(self.deleteLater)
        fade_out.start()
