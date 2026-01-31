
import pytest
from PyQt6.QtCore import QObject, QTimer
from unittest.mock import MagicMock
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_assets import QtMapEditorAssetsMixin, SpriteHashWorker

class MockEditor(QObject, QtMapEditorAssetsMixin):
    def __init__(self):
        super().__init__()
        self.sprite_assets = None
        self.id_mapper = None
        self.sprite_matcher = None
        self.status = MagicMock()
        self.status.showMessage = MagicMock()

@pytest.fixture
def mock_sprite_assets():
    assets = MagicMock()
    assets.sprite_count = 100
    # valid sprite: w=32, h=32, bgra=bytes
    assets.get_sprite_rgba.return_value = (32, 32, b'\xff' * (32*32*4))
    return assets

def test_sprite_hash_worker(mock_sprite_assets, qtbot):
    worker = SpriteHashWorker(mock_sprite_assets)

    with qtbot.waitSignal(worker.finished, timeout=1000) as blocker:
        worker.run()

    matcher = blocker.args[0]
    assert matcher is not None

def test_build_sprite_hash_database_async(mock_sprite_assets, qtbot):
    editor = MockEditor()
    editor.sprite_assets = mock_sprite_assets
    editor.id_mapper = MagicMock()

    # Trigger the async build
    editor._build_sprite_hash_database()

    assert editor._hash_thread is not None
    assert editor._hash_thread.isRunning()

    # Wait for completion
    # We wait until sprite_matcher is set
    qtbot.waitUntil(lambda: editor.sprite_matcher is not None, timeout=2000)

    assert editor.sprite_matcher is not None

    # Verify status message
    # It might have been called multiple times: "Building..." then "Ready"
    calls = [c[0][0] for c in editor.status.showMessage.call_args_list]
    assert "Building sprite hash database..." in calls
    assert "Sprite hash database ready" in calls

    # Verify cleanup
    # Thread might take a moment to be deleted, but reference should be cleared
    qtbot.waitUntil(lambda: editor._hash_thread is None, timeout=1000)
    assert editor._hash_thread is None
