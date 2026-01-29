import pytest

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.vis_layer.renderer.render_model import RenderFrame

# Mock loading if necessary, or use minimal logic
# Since we don't have large maps committed, we bench synthetic creation or small loads


@pytest.mark.benchmark
def test_map_creation_time(benchmark):
    """Benchmark creating a new GameMap."""

    def create_custom_map():
        return GameMap(header=MapHeader(otbm_version=2, width=2048, height=2048))

    _ = benchmark(create_custom_map)
    # Target: < 100ms for init
    assert benchmark.stats["mean"] < 0.100


@pytest.mark.benchmark
def test_render_frame_time(benchmark):
    """Single frame render command generation should be <16ms (60 FPS)."""
    # Import RenderFrame and DrawCommand for proper testing
    from py_rme_canary.vis_layer.renderer.render_model import Color, DrawCommand, DrawCommandType, LayerType, Rect

    def render_loop():
        frame = RenderFrame()
        # Simulate adding commands with proper DrawCommand objects
        for i in range(100):
            cmd = DrawCommand(
                command_type=DrawCommandType.FILL_RECT,
                layer=LayerType.GROUND,
                rect=Rect(i, i, 32, 32),
                color=Color(255, 255, 255),
                sprite_id=None,
                text=None,
            )
            frame.add_command(cmd)

    _ = benchmark(render_loop)
    assert benchmark.stats["mean"] < 0.016
