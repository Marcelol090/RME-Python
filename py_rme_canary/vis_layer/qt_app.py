from __future__ import annotations

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
    return int(app.exec())


if __name__ == "__main__":
    raise SystemExit(main())
