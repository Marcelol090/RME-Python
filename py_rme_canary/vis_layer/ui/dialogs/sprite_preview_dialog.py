"""Sprite Preview Dialog.

Dialog for previewing individual sprites with animation playback,
zoom controls, and detailed sprite information.

Provides a focused view of a single sprite with:
- Animation playback (play/pause/frame-by-frame)
- Zoom controls (1x, 2x, 4x, 8x)
- Sprite metadata display
- Layer/frame navigation
- Background color toggle (checkered/solid)

Reference:
    - C++ IngamePreviewWindow: ingame_preview/ingame_preview_window.cpp
    - Sprite System: rendering/sprites/
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING

from PyQt6.QtCore import (
    QRect,
    Qt,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QColor,
    QPainter,
    QPixmap,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _c() -> dict:
    return get_theme_manager().tokens["color"]


def _r() -> dict:
    return get_theme_manager().tokens.get("radius", {})


class ZoomLevel(IntEnum):
    """Available zoom levels."""

    X1 = 1
    X2 = 2
    X4 = 4
    X8 = 8


@dataclass(slots=True)
class SpriteData:
    """Data for a sprite being previewed.

    Attributes:
        sprite_id: Unique identifier.
        frames: List of pixmaps for each animation frame.
        width: Base sprite width.
        height: Base sprite height.
        layers: Number of layers.
        animation_speed: Milliseconds per frame.
        pattern_x: Number of pattern variations in X.
        pattern_y: Number of pattern variations in Y.
        pattern_z: Number of pattern variations in Z.
    """

    sprite_id: int
    frames: list[QPixmap] = field(default_factory=list)
    width: int = 32
    height: int = 32
    layers: int = 1
    animation_speed: int = 100
    pattern_x: int = 1
    pattern_y: int = 1
    pattern_z: int = 1


class SpriteCanvas(QFrame):
    """Canvas widget for rendering sprite preview.

    Features:
    - Zoom support (1x-8x)
    - Checkered or solid background
    - Animation playback
    - Frame indicator overlay
    """

    frame_changed = pyqtSignal(int)  # Emitted when frame changes

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sprite: SpriteData | None = None
        self._current_frame = 0
        self._zoom = ZoomLevel.X2
        self._playing = False
        self._show_checkered = True
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._next_frame)

        c = _c()
        self.setMinimumSize(128, 128)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        self.setStyleSheet(f"background: {c['surface']['primary']};")

    def set_sprite(self, sprite: SpriteData | None) -> None:
        """Set the sprite to preview."""
        self._sprite = sprite
        self._current_frame = 0

        if sprite and sprite.frames:
            if self._playing:
                self._animation_timer.start(sprite.animation_speed)

        self.update()

    @property
    def current_frame(self) -> int:
        return self._current_frame

    @current_frame.setter
    def current_frame(self, value: int) -> None:
        if self._sprite and self._sprite.frames:
            self._current_frame = value % len(self._sprite.frames)
            self.frame_changed.emit(self._current_frame)
            self.update()

    @property
    def zoom(self) -> ZoomLevel:
        return self._zoom

    @zoom.setter
    def zoom(self, value: ZoomLevel) -> None:
        self._zoom = value
        self.update()

    @property
    def playing(self) -> bool:
        return self._playing

    @playing.setter
    def playing(self, value: bool) -> None:
        self._playing = value
        if value and self._sprite and self._sprite.frames:
            self._animation_timer.start(self._sprite.animation_speed)
        else:
            self._animation_timer.stop()

    @property
    def show_checkered(self) -> bool:
        return self._show_checkered

    @show_checkered.setter
    def show_checkered(self, value: bool) -> None:
        self._show_checkered = value
        self.update()

    def _next_frame(self) -> None:
        """Advance to the next animation frame."""
        if self._sprite and self._sprite.frames:
            self.current_frame = (self._current_frame + 1) % len(self._sprite.frames)

    def prev_frame(self) -> None:
        """Go to previous frame."""
        if self._sprite and self._sprite.frames:
            self.current_frame = (self._current_frame - 1) % len(self._sprite.frames)

    def next_frame_manual(self) -> None:
        """Manually advance one frame."""
        self._next_frame()

    def paintEvent(self, event) -> None:
        c = _c()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        rect = self.rect()

        # Draw background
        if self._show_checkered:
            self._draw_checkered_bg(painter, rect)
        else:
            painter.fillRect(rect, QColor(c["surface"]["secondary"]))

        # Draw sprite
        if self._sprite and self._sprite.frames and self._current_frame < len(self._sprite.frames):
            pixmap = self._sprite.frames[self._current_frame]
            if pixmap and not pixmap.isNull():
                # Calculate scaled size
                scaled_w = pixmap.width() * int(self._zoom)
                scaled_h = pixmap.height() * int(self._zoom)

                # Center in canvas
                x = (rect.width() - scaled_w) // 2
                y = (rect.height() - scaled_h) // 2

                # Draw scaled
                scaled = pixmap.scaled(
                    scaled_w,
                    scaled_h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.FastTransformation
                    if self._zoom > ZoomLevel.X2
                    else Qt.TransformationMode.SmoothTransformation,
                )
                painter.drawPixmap(x, y, scaled)
        else:
            # No sprite
            painter.setPen(QColor(c["text"]["secondary"]))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "No sprite loaded")

        # Draw frame indicator
        if self._sprite and len(self._sprite.frames) > 1:
            painter.setPen(QColor(c["brand"]["secondary"]))
            info = f"Frame {self._current_frame + 1}/{len(self._sprite.frames)}"
            painter.drawText(
                rect.adjusted(4, 4, -4, -4), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, info
            )

    def _draw_checkered_bg(self, painter: QPainter, rect: QRect) -> None:
        """Draw a checkered transparency background."""
        c = _c()
        tile_size = 8
        colors = [QColor(c["surface"]["secondary"]), QColor(c["surface"]["primary"])]

        for y in range(0, rect.height(), tile_size):
            for x in range(0, rect.width(), tile_size):
                idx = ((x // tile_size) + (y // tile_size)) % 2
                painter.fillRect(x, y, tile_size, tile_size, colors[idx])

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zoom."""
        delta = event.angleDelta().y()
        zooms = list(ZoomLevel)
        current_idx = zooms.index(self._zoom)

        if delta > 0 and current_idx < len(zooms) - 1:
            self.zoom = zooms[current_idx + 1]
        elif delta < 0 and current_idx > 0:
            self.zoom = zooms[current_idx - 1]

        event.accept()


class SpriteInfoPanel(QFrame):
    """Panel displaying sprite metadata."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._sprite: SpriteData | None = None

    def _setup_ui(self) -> None:
        c = _c()
        r = _r()
        rad_sm = r.get("sm", 4)

        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMinimumWidth(200)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Info group
        info_group = QGroupBox("Sprite Info")
        info_group.setStyleSheet(
            f"""
            QGroupBox {{
                color: {c['text']['primary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """
        )
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(6)

        labels = ["ID:", "Size:", "Layers:", "Frames:", "Patterns:"]
        self._values: list[QLabel] = []

        for i, text in enumerate(labels):
            label = QLabel(text)
            label.setStyleSheet(f"color: {c['text']['secondary']};")
            info_layout.addWidget(label, i, 0)

            value = QLabel("—")
            value.setStyleSheet(f"color: {c['text']['primary']}; font-weight: bold;")
            info_layout.addWidget(value, i, 1)
            self._values.append(value)

        layout.addWidget(info_group)
        layout.addStretch()

    def set_sprite(self, sprite: SpriteData | None) -> None:
        """Update panel with sprite info."""
        self._sprite = sprite

        if sprite is None:
            for val in self._values:
                val.setText("—")
            return

        self._values[0].setText(str(sprite.sprite_id))
        self._values[1].setText(f"{sprite.width} x {sprite.height}")
        self._values[2].setText(str(sprite.layers))
        self._values[3].setText(str(len(sprite.frames)))
        self._values[4].setText(f"{sprite.pattern_x}x{sprite.pattern_y}x{sprite.pattern_z}")


class SpritePreviewDialog(QDialog):
    """Dialog for previewing individual sprites.

    Provides detailed sprite preview with:
    - Animation playback controls
    - Zoom controls
    - Sprite metadata
    - Background toggle

    Example:
        >>> dialog = SpritePreviewDialog(parent)
        >>> dialog.set_sprite(sprite_data)
        >>> dialog.exec()
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Sprite Preview")
        self.setMinimumSize(600, 450)
        self.setModal(False)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        c = _c()
        r = _r()
        rad_sm = r.get("sm", 4)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("Sprite Preview")
        header.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {c['text']['primary']};")
        layout.addWidget(header)

        # Main content
        content_layout = QHBoxLayout()

        # Canvas with controls
        canvas_container = QVBoxLayout()

        # Canvas
        self.canvas = SpriteCanvas()
        self.canvas.frame_changed.connect(self._on_frame_changed)
        canvas_container.addWidget(self.canvas, 1)

        # Animation controls
        anim_layout = QHBoxLayout()

        # Play/Pause
        self.play_btn = QPushButton("Play")
        self.play_btn.setFixedSize(48, 32)
        self.play_btn.clicked.connect(self._toggle_play)
        self.play_btn.setStyleSheet(self._button_style())
        anim_layout.addWidget(self.play_btn)

        # Prev frame
        prev_btn = QPushButton("Prev")
        prev_btn.setFixedSize(48, 32)
        prev_btn.clicked.connect(self.canvas.prev_frame)
        prev_btn.setStyleSheet(self._button_style())
        anim_layout.addWidget(prev_btn)

        # Next frame
        next_btn = QPushButton("Next")
        next_btn.setFixedSize(48, 32)
        next_btn.clicked.connect(self.canvas.next_frame_manual)
        next_btn.setStyleSheet(self._button_style())
        anim_layout.addWidget(next_btn)

        anim_layout.addStretch()

        # Frame slider
        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.setMaximum(0)
        self.frame_slider.valueChanged.connect(self._on_slider_changed)
        self.frame_slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                background: {c['surface']['secondary']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {c['brand']['secondary']};
                width: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
        """
        )
        anim_layout.addWidget(self.frame_slider, 1)

        canvas_container.addLayout(anim_layout)

        # Zoom and options
        opts_layout = QHBoxLayout()

        # Zoom selector
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet(f"color: {c['text']['primary']};")
        opts_layout.addWidget(zoom_label)

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["1x", "2x", "4x", "8x"])
        self.zoom_combo.setCurrentIndex(1)  # 2x default
        self.zoom_combo.currentIndexChanged.connect(self._on_zoom_changed)
        self.zoom_combo.setStyleSheet(
            f"""
            QComboBox {{
                background: {c['surface']['secondary']};
                color: {c['text']['primary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
                padding: 4px 8px;
            }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
        """
        )
        opts_layout.addWidget(self.zoom_combo)

        opts_layout.addStretch()

        # Checkered background toggle
        self.checkered_check = QCheckBox("Checkered BG")
        self.checkered_check.setChecked(True)
        self.checkered_check.stateChanged.connect(self._on_checkered_changed)
        self.checkered_check.setStyleSheet(f"color: {c['text']['primary']};")
        opts_layout.addWidget(self.checkered_check)

        canvas_container.addLayout(opts_layout)

        content_layout.addLayout(canvas_container, 1)

        # Info panel
        self.info_panel = SpriteInfoPanel()
        content_layout.addWidget(self.info_panel)

        layout.addLayout(content_layout, 1)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {c['brand']['secondary']};
                color: white;
                border: none;
                border-radius: {rad_sm}px;
                padding: 8px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background: {c['brand']['active']}; }}
        """
        )
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _button_style(self) -> str:
        c = _c()
        r = _r()
        rad_sm = r.get("sm", 4)
        return f"""
            QPushButton {{
                background: {c['surface']['secondary']};
                color: {c['text']['primary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
                font-size: 12px;
            }}
            QPushButton:hover {{ background: {c['surface']['tertiary']}; }}
            QPushButton:pressed {{ background: {c['brand']['secondary']}; }}
        """

    def _apply_style(self) -> None:
        """Apply dark theme styling."""
        c = _c()
        r = _r()
        rad_sm = r.get("sm", 4)

        self.setStyleSheet(
            f"""
            QDialog {{ background: {c['surface']['primary']}; }}
            QGroupBox {{
                color: {c['text']['primary']};
                border: 1px solid {c['border']['default']};
                border-radius: {rad_sm}px;
            }}
        """
        )

    def _toggle_play(self) -> None:
        """Toggle animation playback."""
        playing = not self.canvas.playing
        self.canvas.playing = playing
        self.play_btn.setText("Pause" if playing else "Play")

    def _on_frame_changed(self, frame: int) -> None:
        """Handle frame change from canvas."""
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(frame)
        self.frame_slider.blockSignals(False)

    def _on_slider_changed(self, value: int) -> None:
        """Handle slider value change."""
        self.canvas.current_frame = value

    def _on_zoom_changed(self, index: int) -> None:
        """Handle zoom combo change."""
        zooms = [ZoomLevel.X1, ZoomLevel.X2, ZoomLevel.X4, ZoomLevel.X8]
        self.canvas.zoom = zooms[index]

    def _on_checkered_changed(self, state: int) -> None:
        """Handle checkered background toggle."""
        self.canvas.show_checkered = state == Qt.CheckState.Checked.value

    def set_sprite(self, sprite: SpriteData | None) -> None:
        """Set the sprite to preview.

        Args:
            sprite: SpriteData object or None.
        """
        self.canvas.set_sprite(sprite)
        self.info_panel.set_sprite(sprite)

        # Update frame slider
        if sprite and sprite.frames:
            self.frame_slider.setMaximum(len(sprite.frames) - 1)
            self.frame_slider.setValue(0)
        else:
            self.frame_slider.setMaximum(0)

    def set_sprite_from_pixmap(self, sprite_id: int, pixmap: QPixmap | None) -> None:
        """Convenience method to set a sprite from a single pixmap.

        Args:
            sprite_id: Sprite identifier.
            pixmap: Single frame pixmap.
        """
        if pixmap is None or pixmap.isNull():
            self.set_sprite(None)
            return

        sprite = SpriteData(
            sprite_id=sprite_id,
            frames=[pixmap],
            width=pixmap.width(),
            height=pixmap.height(),
        )
        self.set_sprite(sprite)


def show_sprite_preview(
    parent: QWidget | None = None,
    sprite: SpriteData | None = None,
) -> SpritePreviewDialog:
    """Factory function to create and show the dialog.

    Args:
        parent: Parent widget.
        sprite: Optional sprite data to preview.

    Returns:
        The dialog instance.
    """
    dialog = SpritePreviewDialog(parent)
    if sprite:
        dialog.set_sprite(sprite)
    dialog.show()
    return dialog


__all__ = [
    "SpriteData",
    "SpriteCanvas",
    "SpriteInfoPanel",
    "SpritePreviewDialog",
    "ZoomLevel",
    "show_sprite_preview",
]
