
import os
import pytest
print("DEBUG: Checking importorskip")
pytest.importorskip("PyQt6.QtWidgets")
print("DEBUG: Importing QtWidgets...")
from PyQt6.QtWidgets import QDialog, QFileDialog
print("DEBUG: Importing QtMapEditor...")
from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor
print("DEBUG: Importing BrushManager...")
from py_rme_canary.logic_layer.brush_definitions import BrushManager
print("DEBUG: Done.")

def test_noop():
    pass
