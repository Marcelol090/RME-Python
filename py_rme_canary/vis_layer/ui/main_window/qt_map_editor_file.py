from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.io.map_detection import detect_map_file
from py_rme_canary.core.io.otbm_loader import OTBMLoader
from py_rme_canary.core.io.otbm_saver import save_game_map_bundle_atomic
from py_rme_canary.logic_layer.editor_session import EditorSession

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorFileMixin:
    def _new_map(self: "QtMapEditor") -> None:
        if (
            QMessageBox.question(self, "New map", "Discard current map and create a new blank map?")
            != QMessageBox.StandardButton.Yes
        ):
            return
        self.current_path = None
        self.map = GameMap(header=MapHeader(otbm_version=2, width=256, height=256))
        self.session = EditorSession(self.map, self.brush_mgr, on_tiles_changed=self._on_tiles_changed)
        self.apply_ui_state_to_session()
        self.viewport.origin_x = 0
        self.viewport.origin_y = 0
        self.canvas.update()

    def _open_otbm(self: "QtMapEditor") -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Map", "", "Maps (*.otbm *.json *.otml *.xml);;All Files (*)"
        )
        if not path:
            return

        det = detect_map_file(path)
        if det.kind == "canary_json":
            QMessageBox.information(
                self,
                "Detected Canary",
                f"Detected Canary JSON map (reason: {det.reason}).\n\n"
                "This editor currently loads OTBM maps. Use a project wrapper JSON to point to an .otbm, "
                "or export/convert the map to OTBM.",
            )
            return
        if det.kind == "otml_xml":
            QMessageBox.information(
                self,
                "Detected OTML/XML",
                f"Detected OTML/XML map (engine={det.engine}, reason: {det.reason}).\n\n"
                "This editor currently loads OTBM maps only.",
            )
            return
        if det.kind not in ("otbm", "project_json"):
            QMessageBox.warning(self, "Unknown map", f"Could not detect a supported map format.\n\nReason: {det.reason}")
            return

        try:
            loader = OTBMLoader()
            gm = loader.load_with_detection(path)
        except Exception as e:
            QMessageBox.critical(self, "Open failed", str(e))
            return

        self.current_path = loader.last_otbm_path or path
        self.map = gm
        self.session = EditorSession(self.map, self.brush_mgr, on_tiles_changed=self._on_tiles_changed)
        self.apply_ui_state_to_session()
        self.viewport.origin_x = 0
        self.viewport.origin_y = 0
        self.id_mapper = loader.last_id_mapper

        md = (gm.load_report or {}).get("metadata") or {}
        self._apply_detected_context(md)
        src = md.get("source") or "unknown"

        # C) Auto-generate wrapper when opening a bare .otbm
        if det.kind == "otbm" and loader.last_config is not None and loader.last_otbm_path is not None:
            self._maybe_write_default_project_json(opened_otbm_path=str(loader.last_otbm_path), cfg=loader.last_config)

        self._update_status_capabilities(prefix=f"Loaded: {self.current_path} | source={src}")
        self.canvas.update()

    def _save_as(self: "QtMapEditor") -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save OTBM As", "", "OTBM (*.otbm);;All Files (*)")
        if not path:
            return
        if not path.lower().endswith(".otbm"):
            path += ".otbm"
        self.current_path = path
        self._save()

    def _save(self: "QtMapEditor") -> None:
        if not self.current_path:
            self._save_as()
            return
        try:
            save_game_map_bundle_atomic(self.current_path, self.map)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))
