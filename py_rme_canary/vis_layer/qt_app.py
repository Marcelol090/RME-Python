from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer, qInstallMessageHandler
from PyQt6.QtWidgets import QApplication, QMessageBox

from py_rme_canary.core.runtime import assert_64bit_runtime
from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor
from py_rme_canary.vis_layer.ui.theme.integration import apply_modern_theme


def _resolve_log_path() -> Path:
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
    log_dir = Path(base) / "py_rme_canary" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "app.log"


def _setup_logging() -> None:
    log_path = _resolve_log_path()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8")],
    )
    logging.getLogger("app").info("Logging initialized: %s", log_path)

    def _qt_message_handler(mode, context, message) -> None:  # type: ignore[no-redef]
        logger = logging.getLogger("qt")
        logger.info("%s | %s", mode, message)

    qInstallMessageHandler(_qt_message_handler)

    def _excepthook(exc_type, exc, tb) -> None:
        logging.getLogger("exceptions").exception("Unhandled exception", exc_info=(exc_type, exc, tb))
        sys.__excepthook__(exc_type, exc, tb)

    sys.excepthook = _excepthook


def main() -> int:
    _setup_logging()
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
    apply_modern_theme(app)
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
