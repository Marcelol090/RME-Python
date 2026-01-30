"""UI test configuration."""

from __future__ import annotations


def _pyqt6_available() -> bool:
    try:
        from PyQt6.QtCore import Qt  # noqa: F401
        from PyQt6.QtWidgets import QApplication  # noqa: F401
    except Exception:
        return False
    return True


def pytest_ignore_collect(collection_path, config):
    if _pyqt6_available():
        return False
    path_str = str(collection_path).replace("\\", "/")
    if path_str.endswith("test_ui_placeholder.py"):
        return False
    if "/tests/ui/" in path_str:
        return True
    return False
