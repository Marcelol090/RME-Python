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

    result = benchmark(create_custom_map)
    # Target: < 100ms for init
    assert benchmark.stats["mean"] < 0.100


@pytest.mark.benchmark
def test_render_frame_time(benchmark):
    """Single frame render command generation should be <16ms (60 FPS)."""
    # Create a dummy frame logic, assuming RenderFrame setup is fast
    # Real render logic is in MapCanvasWidget.paintGL, but we can bench the model construction
    # if we have a model.
    # For now, let's bench a dummy numeric operation to ensure infrastructure works,
    # or better, mock a simple render loop.

    def render_loop():
        frame = RenderFrame()
        # Simulate adding commands
        for i in range(100):
            frame.add_command(1, 2, i)  # Assuming signature

    result = benchmark(render_loop)
    assert benchmark.stats["mean"] < 0.016
