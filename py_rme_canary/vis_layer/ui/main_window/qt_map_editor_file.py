from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QInputDialog

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.io.creatures_xml import clear_creature_name_cache
from py_rme_canary.core.io.lua_creature_import import (
    LuaCreatureImportResult,
    import_lua_creatures_from_file,
    import_lua_creatures_from_folder,
)
from py_rme_canary.core.io.map_detection import detect_map_file
from py_rme_canary.core.io.otbm_loader import OTBMLoader
from py_rme_canary.core.io.otbm_saver import save_game_map_bundle_atomic
from py_rme_canary.logic_layer.map_format_conversion import (
    analyze_map_format_conversion,
    apply_map_format_version,
)
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
            save_game_map_bundle_atomic(self.current_path, self.map, id_mapper=self.id_mapper)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))

    def _import_monsters_npcs(self: "QtMapEditor") -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Monsters/NPC...", "", "Lua Files (*.lua);;All Files (*)")
        if not path:
            return
        try:
            result = import_lua_creatures_from_file(path)
        except Exception as exc:
            QMessageBox.critical(self, "Import Monsters/NPC...", str(exc))
            return
        self._show_creature_import_result(result, "Import Monsters/NPC...")

    def _import_monster_folder(self: "QtMapEditor") -> None:
        folder = QFileDialog.getExistingDirectory(self, "Import Monster Folder...")
        if not folder:
            return
        try:
            result = import_lua_creatures_from_folder(Path(folder))
        except Exception as exc:
            QMessageBox.critical(self, "Import Monster Folder...", str(exc))
            return
        self._show_creature_import_result(result, "Import Monster Folder...")

    def _show_creature_import_result(self: "QtMapEditor", result: LuaCreatureImportResult, title: str) -> None:
        if result.files_scanned <= 0:
            QMessageBox.information(self, title, "No Lua files found.")
            return
        if result.total_imported <= 0:
            QMessageBox.information(self, title, "No valid monsters or NPCs found.")
            return

        clear_creature_name_cache()
        try:
            self.palettes.refresh_primary_list()
        except Exception:
            pass

        lines = [
            f"Files scanned: {int(result.files_scanned)}",
            f"Monsters: +{int(result.monsters_added)} / updated {int(result.monsters_updated)}",
            f"NPCs: +{int(result.npcs_added)} / updated {int(result.npcs_updated)}",
        ]
        QMessageBox.information(self, title, "\n".join(lines))

    def _import_map(self: "QtMapEditor") -> None:
        from py_rme_canary.vis_layer.ui.main_window.import_map_dialog import ImportMapDialog

        dialog = ImportMapDialog(self, current_map=self.map)
        if dialog.exec():
            self.canvas.update()

    def _convert_map_format(self: "QtMapEditor") -> None:
        if self.map is None:
            return
        current_version = int(self.map.header.otbm_version)
        options: list[tuple[str, int]] = [
            ("ServerID (OTBM 2)", 2),
            ("ClientID (OTBM 5)", 5),
            ("ClientID (OTBM 6)", 6),
        ]
        labels = [opt[0] for opt in options]
        default_index = 0
        for idx, (_label, version) in enumerate(options):
            if int(version) == int(current_version):
                default_index = idx
                break

        choice, ok = QInputDialog.getItem(
            self,
            "Convert Map Format",
            "Target format:",
            labels,
            int(default_index),
            False,
        )
        if not ok or not choice:
            return
        target_version = options[int(labels.index(choice))][1]
        if int(target_version) == int(current_version):
            QMessageBox.information(self, "Convert Map Format", "Map already uses the selected format.")
            return

        report = analyze_map_format_conversion(
            self.map,
            target_version=int(target_version),
            id_mapper=self.id_mapper,
        )

        if not report.ok:
            missing_preview = ""
            if report.id_mapper_missing:
                missing_preview = "IdMapper not loaded. Load assets/items first."
            elif report.missing_mappings:
                preview = ", ".join(str(i) for i in report.missing_mappings[:12])
                suffix = "..." if len(report.missing_mappings) > 12 else ""
                missing_preview = f"Missing mappings for {len(report.missing_mappings)} item ids: {preview}{suffix}"

            placeholder_info = ""
            if report.placeholder_items > 0:
                placeholder_info = f"\nUnknown/placeholder items: {int(report.placeholder_items)}"

            msg = (
                f"Conversion to OTBM {int(target_version)} has unresolved mappings."
                f"\n{missing_preview}{placeholder_info}"
                "\n\nSaving in ClientID format will fail until mappings are fixed."
                "\n\nConvert anyway?"
            )
            if QMessageBox.question(self, "Convert Map Format", msg) != QMessageBox.StandardButton.Yes:
                return

        apply_map_format_version(self.map, target_version=int(target_version))
        self._update_status_capabilities(prefix=f"Map format converted to OTBM {int(target_version)}")
        self.canvas.update()
