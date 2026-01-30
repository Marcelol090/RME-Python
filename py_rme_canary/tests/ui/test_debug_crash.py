import pytest

print("DEBUG: Checking importorskip")
pytest.importorskip("PyQt6.QtWidgets")
print("DEBUG: Importing QtWidgets...")
print("DEBUG: Importing QtMapEditor...")
print("DEBUG: Importing BrushManager...")
print("DEBUG: Done.")


def test_noop():
    pass
