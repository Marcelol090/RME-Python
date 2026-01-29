from __future__ import annotations

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox

from py_rme_canary.core.runtime import assert_64bit_runtime

from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor
from py_rme_canary.vis_layer.ui.themes import apply_dark_theme


def main() -> int:
    try:
        assert_64bit_runtime()
    except Exception as e:
        # Best-effort: show a GUI dialog if Qt can be initialized.
        try:
            app = QApplication([])
            QMessageBox.critical(None, "Startup Error", str(e))
            return 1
        except Exception:
            raise

    app = QApplication([])
    apply_dark_theme(app)
    win = QtMapEditor()
    win.show()

    def maybe_show_welcome() -> None:
        import os

        if "PYTEST_CURRENT_TEST" in os.environ:
            return

        try:
            from py_rme_canary.vis_layer.ui.dialogs.welcome_dialog import WelcomeDialog
            from py_rme_canary.vis_layer.ui.utils.recent_files import RecentFilesManager
        except Exception:
            return

        recent = RecentFilesManager.instance().get_recent_files()
        dialog = WelcomeDialog(recent_files=recent, parent=win)
        if hasattr(win, "act_new"):
            dialog.new_map_requested.connect(lambda: win.act_new.trigger())
        if hasattr(win, "act_open"):
            dialog.open_map_requested.connect(lambda: win.act_open.trigger())
        if hasattr(win, "do_open_file"):
            dialog.recent_file_selected.connect(win.do_open_file)
        dialog.open()

    QTimer.singleShot(0, maybe_show_welcome)
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
