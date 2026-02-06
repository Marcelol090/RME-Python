"""Animation utilities for modern UI effects.

Provides reusable animation helpers for smooth transitions,
hover effects, and feedback animations.
"""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QRect,
    QSequentialAnimationGroup,
    QSize,
    QTimer,
)
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget


class AnimationFactory:
    """Factory for creating common animations."""

    @staticmethod
    def fade_in(
        widget: QWidget,
        duration: int = 200,
        start_opacity: float = 0.0,
        end_opacity: float = 1.0,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
    ) -> QPropertyAnimation:
        """Create a fade-in animation for a widget.

        Args:
            widget: Widget to animate
            duration: Animation duration in ms
            start_opacity: Starting opacity (0.0-1.0)
            end_opacity: Ending opacity (0.0-1.0)
            easing: Easing curve type

        Returns:
            Configured QPropertyAnimation
        """
        # Ensure widget has opacity effect
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(effect)

        effect.setOpacity(start_opacity)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(start_opacity)
        anim.setEndValue(end_opacity)
        anim.setEasingCurve(easing)

        return anim

    @staticmethod
    def fade_out(
        widget: QWidget,
        duration: int = 200,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
    ) -> QPropertyAnimation:
        """Create a fade-out animation for a widget."""
        return AnimationFactory.fade_in(widget, duration, start_opacity=1.0, end_opacity=0.0, easing=easing)

    @staticmethod
    def slide_in(
        widget: QWidget,
        direction: str = "up",
        distance: int = 20,
        duration: int = 200,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
    ) -> QPropertyAnimation:
        """Create a slide-in animation.

        Args:
            widget: Widget to animate
            direction: Direction to slide from ("up", "down", "left", "right")
            distance: Distance in pixels to slide
            duration: Animation duration in ms
            easing: Easing curve type

        Returns:
            Configured QPropertyAnimation
        """
        current_pos = widget.pos()

        # Calculate start position based on direction
        offsets = {
            "up": QPoint(0, distance),
            "down": QPoint(0, -distance),
            "left": QPoint(distance, 0),
            "right": QPoint(-distance, 0),
        }
        offset = offsets.get(direction, QPoint(0, distance))
        start_pos = current_pos + offset

        widget.move(start_pos)

        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(start_pos)
        anim.setEndValue(current_pos)
        anim.setEasingCurve(easing)

        return anim

    @staticmethod
    def scale_bounce(
        widget: QWidget,
        duration: int = 300,
        scale_factor: float = 1.1,
    ) -> QPropertyAnimation:
        """Create a bounce scale animation (for button press feedback).

        Note: Qt doesn't support transform:scale directly, so this
        animates the widget's size.
        """
        original_size = widget.size()
        scaled_size = QSize(int(original_size.width() * scale_factor), int(original_size.height() * scale_factor))

        anim = QPropertyAnimation(widget, b"size")
        anim.setDuration(duration)
        anim.setKeyValueAt(0, original_size)
        anim.setKeyValueAt(0.5, scaled_size)
        anim.setKeyValueAt(1, original_size)
        anim.setEasingCurve(QEasingCurve.Type.OutBounce)

        return anim

    @staticmethod
    def pulse_glow(
        widget: QWidget,
        color: QColor | None = None,  # Purple
        duration: int = 1000,
        min_alpha: int = 100,
        max_alpha: int = 200,
    ) -> QPropertyAnimation:
        """Create a pulsing glow effect animation.

        Requires widget to have a QGraphicsDropShadowEffect.
        """
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect

        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsDropShadowEffect):
            effect = QGraphicsDropShadowEffect()
            effect.setBlurRadius(20)
            effect.setOffset(0, 0)
            widget.setGraphicsEffect(effect)

        # Animate blur radius for pulse effect
        anim = QPropertyAnimation(effect, b"blurRadius")
        anim.setDuration(duration)
        anim.setStartValue(10)
        anim.setEndValue(25)
        anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        anim.setLoopCount(-1)  # Infinite loop

        if color is None:
            color = QColor(139, 92, 246)

        # Set color
        color.setAlpha(max_alpha)
        effect.setColor(color)

        return anim


class AnimationGroup:
    """Helper for creating animation groups."""

    @staticmethod
    def parallel(*animations: QPropertyAnimation) -> QParallelAnimationGroup:
        """Run multiple animations in parallel."""
        group = QParallelAnimationGroup()
        for anim in animations:
            group.addAnimation(anim)
        return group

    @staticmethod
    def sequential(*animations: QPropertyAnimation) -> QSequentialAnimationGroup:
        """Run multiple animations in sequence."""
        group = QSequentialAnimationGroup()
        for anim in animations:
            group.addAnimation(anim)
        return group


class TransitionManager:
    """Manages smooth transitions between widget states."""

    def __init__(self) -> None:
        self._active_animations: dict[int, QAbstractAnimation] = {}

    def transition(
        self,
        widget: QWidget,
        property_name: str,
        end_value: object,
        duration: int = 200,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
    ) -> QPropertyAnimation:
        """Smoothly transition a widget property.

        Cancels any existing animation on the same property.

        Args:
            widget: Widget to animate
            property_name: Property to animate (e.g., "pos", "size")
            end_value: Target value
            duration: Animation duration
            easing: Easing curve

        Returns:
            The animation (already started)
        """
        key = id(widget) + hash(property_name)

        # Stop any existing animation
        if key in self._active_animations:
            self._active_animations[key].stop()

        # Get current value
        current = widget.property(property_name)

        anim = QPropertyAnimation(widget, property_name.encode())
        anim.setDuration(duration)
        anim.setStartValue(current)
        anim.setEndValue(end_value)
        anim.setEasingCurve(easing)

        # Track and start
        self._active_animations[key] = anim
        anim.finished.connect(lambda: self._active_animations.pop(key, None))
        anim.start()

        return anim


class FeedbackAnimation:
    """Visual feedback animations for user actions."""

    @staticmethod
    def success_ripple(
        parent: QWidget,
        center: QPoint,
        color: QColor | None = None,  # Green
        duration: int = 400,
    ) -> tuple[QWidget, QAbstractAnimation]:
        """Create an expanding ripple effect for success feedback.

        Args:
            parent: Parent widget to create ripple in
            center: Center point of ripple
            color: Ripple color
            duration: Animation duration

        Returns:
            Tuple of (ripple widget, animation)
        """
        if color is None:
            color = QColor(16, 185, 129)

        # Create ripple widget
        ripple = QWidget(parent)
        ripple.setStyleSheet(
            f"""
            background: transparent;
            border: 3px solid rgba({color.red()}, {color.green()}, {color.blue()}, 200);
            border-radius: 50px;
        """
        )

        start_size = 20
        end_size = 100

        start_rect = QRect(center.x() - start_size // 2, center.y() - start_size // 2, start_size, start_size)
        end_rect = QRect(center.x() - end_size // 2, center.y() - end_size // 2, end_size, end_size)

        ripple.setGeometry(start_rect)
        ripple.show()

        # Geometry animation
        geom_anim = QPropertyAnimation(ripple, b"geometry")
        geom_anim.setDuration(duration)
        geom_anim.setStartValue(start_rect)
        geom_anim.setEndValue(end_rect)
        geom_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Fade out
        effect = QGraphicsOpacityEffect(ripple)
        ripple.setGraphicsEffect(effect)

        fade_anim = QPropertyAnimation(effect, b"opacity")
        fade_anim.setDuration(duration)
        fade_anim.setStartValue(1.0)
        fade_anim.setEndValue(0.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Run parallel
        group = QParallelAnimationGroup()
        group.addAnimation(geom_anim)
        group.addAnimation(fade_anim)

        # Cleanup on finish
        group.finished.connect(ripple.deleteLater)
        group.start()

        return ripple, group

    @staticmethod
    def error_shake(
        widget: QWidget,
        distance: int = 10,
        duration: int = 500,
    ) -> QPropertyAnimation:
        """Shake widget horizontally to indicate error.

        Args:
            widget: Widget to shake
            distance: Shake distance in pixels
            duration: Total animation duration

        Returns:
            The animation (already started)
        """
        original_pos = widget.pos()

        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)

        # Keyframes for shake
        anim.setKeyValueAt(0, original_pos)
        anim.setKeyValueAt(0.1, original_pos + QPoint(distance, 0))
        anim.setKeyValueAt(0.2, original_pos + QPoint(-distance, 0))
        anim.setKeyValueAt(0.3, original_pos + QPoint(distance, 0))
        anim.setKeyValueAt(0.4, original_pos + QPoint(-distance, 0))
        anim.setKeyValueAt(0.5, original_pos + QPoint(distance // 2, 0))
        anim.setKeyValueAt(0.6, original_pos + QPoint(-distance // 2, 0))
        anim.setKeyValueAt(0.7, original_pos)
        anim.setKeyValueAt(1, original_pos)

        anim.setEasingCurve(QEasingCurve.Type.Linear)
        anim.start()

        return anim


def delayed_call(delay_ms: int, callback: Callable[[], None]) -> QTimer:
    """Schedule a callback after a delay.

    Args:
        delay_ms: Delay in milliseconds
        callback: Function to call

    Returns:
        The timer (for cancellation if needed)
    """
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(callback)
    timer.start(delay_ms)
    return timer
