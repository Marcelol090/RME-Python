"""Tests for Minimap Export/Import functionality."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestMinimapGeneration:
    """Test minimap image generation from GameMap."""

    def test_create_minimap_renderer(self):
        """Test creating minimap renderer."""
        from py_rme_canary.tools.minimap_export import MinimapRenderer

        renderer = MinimapRenderer()

        assert renderer is not None

    def test_render_empty_map(self):
        """Test rendering empty map to minimap."""
        from py_rme_canary.core.data.gamemap import GameMap, MapHeader
        from py_rme_canary.tools.minimap_export import MinimapRenderer

        renderer = MinimapRenderer()
        game_map = GameMap(header=MapHeader(otbm_version=2, width=256, height=256, description="Test map"))

        # Render size matches bounds of tiles, not header dimensions
        image = renderer.render(game_map, floor=7, bounds=(0, 0, 256, 256))

        assert image is not None

    def test_export_minimap_bmp(self, tmp_path: Path):
        """Test exporting minimap as BMP."""
        from py_rme_canary.core.data.gamemap import GameMap, MapHeader
        from py_rme_canary.tools.minimap_export import MinimapRenderer

        renderer = MinimapRenderer()
        game_map = GameMap(header=MapHeader(otbm_version=2, width=32, height=32, description="Test map"))

        output_path = tmp_path / "minimap.bmp"
        renderer.export_bmp(game_map, floor=7, output_path=output_path)

        assert output_path.exists()
        assert output_path.stat().st_size > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
