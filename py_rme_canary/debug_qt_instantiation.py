
from PyQt6.QtWidgets import QApplication
import sys
import os

# Mock BrushManager to avoid loading files if possible, or just let it load
# But let's rely on real files if they exist.
# We need to access QtMapEditor.

try:
    print("Creating QApplication...")
    app = QApplication(sys.argv)
    print("Importing QtMapEditor...")
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor
    print("Instantiating QtMapEditor...")
    w = QtMapEditor()
    print("Instantiated successfully")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
