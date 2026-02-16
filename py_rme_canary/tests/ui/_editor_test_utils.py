from __future__ import annotations

import contextlib

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication


def stabilize_editor_for_headless_tests(editor) -> None:
    """
    Disable always-on timers that can keep pytest-qt teardown busy forever
    in offscreen/minimal environments.
    """

    with contextlib.suppress(Exception):
        editor.show_preview = False

    for timer_name in ("_live_timer", "_ui_backend_contract_timer", "_friends_timer"):
        timer = getattr(editor, timer_name, None)
        if timer is not None:
            with contextlib.suppress(Exception):
                timer.stop()

    canvas = getattr(editor, "canvas", None)
    if canvas is not None:
        with contextlib.suppress(Exception):
            animation_timer = getattr(canvas, "_animation_timer", None)
            if animation_timer is not None:
                animation_timer.stop()
        with contextlib.suppress(Exception):
            canvas._sync_animation_timer()

    with contextlib.suppress(Exception):
        for timer in editor.findChildren(QTimer):
            timer.stop()


def show_editor_window(qtbot, editor, wait_ms: int = 50) -> None:
    """Headless-safe show helper for editor windows."""

    editor.show()
    app = QApplication.instance()
    if app is not None:
        app.processEvents()
    qtbot.wait(int(wait_ms))
