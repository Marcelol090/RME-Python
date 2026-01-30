"""Tests for OpenGL rendering functionality.

Following TDD strict mode - test first, implement after.
"""

from __future__ import annotations

import pytest

from py_rme_canary.vis_layer.renderer.render_model import (
    Color,
    DrawCommand,
    DrawCommandType,
    LayerType,
    Rect,
    RenderFrame,
)


class TestOpenGLRendering:
    """Test OpenGL rendering capabilities."""

    def test_render_frame_supports_layers(self):
        """Test that render frame organizes commands by layer."""
        frame = RenderFrame()

        # Add commands for different layers
        frame.add_command(
            DrawCommand(
                command_type=DrawCommandType.FILL_RECT,
                layer=LayerType.GROUND,
                rect=Rect(0, 0, 32, 32),
                color=Color(100, 100, 100),
            )
        )
        frame.add_command(
            DrawCommand(
                command_type=DrawCommandType.FILL_RECT,
                layer=LayerType.ITEMS,
                rect=Rect(0, 0, 32, 32),
                color=Color(200, 200, 200),
            )
        )

        # Get commands by layer
        by_layer = frame.get_commands_by_layer()

        assert LayerType.GROUND in by_layer
        assert LayerType.ITEMS in by_layer
        assert len(by_layer[LayerType.GROUND]) == 1
        assert len(by_layer[LayerType.ITEMS]) == 1

    def test_render_frame_layer_ordering(self):
        """Test that layers are ordered correctly (bottom to top)."""
        frame = RenderFrame()

        # Add in reverse order
        for layer in [LayerType.OVERLAY, LayerType.GROUND, LayerType.ITEMS]:
            frame.add_command(DrawCommand(command_type=DrawCommandType.FILL_RECT, layer=layer, rect=Rect(0, 0, 32, 32)))

        by_layer = frame.get_commands_by_layer()
        layers = list(by_layer.keys())

        # Should be sorted by layer value (GROUND=0, ITEMS=2, OVERLAY=30)
        assert layers == [LayerType.GROUND, LayerType.ITEMS, LayerType.OVERLAY]

    def test_draw_command_sprite(self):
        """Test draw command with sprite ID."""
        cmd = DrawCommand(
            command_type=DrawCommandType.DRAW_SPRITE, layer=LayerType.ITEMS, rect=Rect(100, 100, 32, 32), sprite_id=1234
        )

        assert cmd.sprite_id == 1234
        assert cmd.command_type == DrawCommandType.DRAW_SPRITE

    def test_draw_command_text(self):
        """Test draw command with text."""
        cmd = DrawCommand(
            command_type=DrawCommandType.DRAW_TEXT,
            layer=LayerType.OVERLAY,
            rect=Rect(100, 100, 200, 50),
            text="Test Label",
            color=Color(255, 255, 255),
        )

        assert cmd.text == "Test Label"
        assert cmd.command_type == DrawCommandType.DRAW_TEXT

    def test_color_from_hex(self):
        """Test color creation from hex string."""
        # RGB hex
        color1 = Color.from_hex("#FF00AA")
        assert color1.r == 255
        assert color1.g == 0
        assert color1.b == 170
        assert color1.a == 255  # default alpha

        # RGBA hex
        color2 = Color.from_hex("#FF00AA80")
        assert color2.a == 128

    def test_color_from_hex_invalid(self):
        """Test color from hex raises on invalid input."""
        with pytest.raises(ValueError, match="Invalid hex color"):
            Color.from_hex("#ZZZZZZ")

    def test_render_frame_clear(self):
        """Test clearing render frame."""
        frame = RenderFrame()
        frame.add_command(
            DrawCommand(command_type=DrawCommandType.FILL_RECT, layer=LayerType.GROUND, rect=Rect(0, 0, 32, 32))
        )

        assert len(frame.commands) == 1

        frame.clear()

        assert len(frame.commands) == 0


class TestGridRendering:
    """Test grid rendering functionality."""

    def test_grid_command_creation(self):
        """Test creating grid overlay commands."""
        frame = RenderFrame()

        # Grid should be on GRID layer
        grid_cmd = DrawCommand(
            command_type=DrawCommandType.DRAW_LINE,
            layer=LayerType.GRID,
            rect=Rect(0, 0, 100, 0),  # horizontal line
            color=Color(58, 58, 58),
            line_width=1,
            dashed=False,
        )

        frame.add_command(grid_cmd)
        by_layer = frame.get_commands_by_layer()

        assert LayerType.GRID in by_layer
        assert by_layer[LayerType.GRID][0].command_type == DrawCommandType.DRAW_LINE


class TestSelectionRendering:
    """Test selection overlay rendering."""

    def test_selection_highlight(self):
        """Test selection highlight rendering."""
        frame = RenderFrame()

        # Selection should be on SELECTION layer (high priority)
        sel_cmd = DrawCommand(
            command_type=DrawCommandType.DRAW_RECT,
            layer=LayerType.SELECTION,
            rect=Rect(100, 100, 32, 32),
            color=Color(230, 230, 230, 128),  # semi-transparent
            line_width=2,
        )

        frame.add_command(sel_cmd)

        assert frame.commands[0].layer == LayerType.SELECTION
        assert frame.commands[0].color.a == 128  # transparent


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
