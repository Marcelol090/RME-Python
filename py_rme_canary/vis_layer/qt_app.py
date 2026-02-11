from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from PyQt6.QtCore import QTimer, qInstallMessageHandler
from PyQt6.QtWidgets import QApplication, QMessageBox

from py_rme_canary.core.runtime import assert_64bit_runtime
from py_rme_canary.core.version import get_build_info
from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor
from py_rme_canary.vis_layer.ui.splash import StartupSplash
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
    build = get_build_info()
    logging.getLogger("app").info("Starting %s", build.display_name)

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

    # Show splash screen during startup
    splash = StartupSplash()
    splash.show()
    app.processEvents()

    splash.set_phase("Initializing editor...")
    win = QtMapEditor()

    splash.set_phase("Preparing workspace...")
    win.show()
    splash.finish_with_delay(win, delay_ms=500)

    # Background update check (non-blocking)
    def _schedule_update_check() -> None:
        if "PYTEST_CURRENT_TEST" in os.environ:
            return
        try:
            from py_rme_canary.core.updates.update_checker import UpdateChecker

            checker = UpdateChecker()
            future = checker.check_async()

            def _on_update_result() -> None:
                try:
                    result = future.result(timeout=0)
                except Exception:
                    return
                if result.available:
                    QMessageBox.information(
                        win,
                        "Update Available",
                        f"A new version ({result.latest_version}) is available.\n"
                        f"You are running {result.current_version}.\n\n"
                        f"Visit the release page to download the update.",
                    )
                checker.shutdown()

            # Poll the future after a short delay
            QTimer.singleShot(12000, _on_update_result)
        except Exception:
            pass

    QTimer.singleShot(3000, _schedule_update_check)

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
