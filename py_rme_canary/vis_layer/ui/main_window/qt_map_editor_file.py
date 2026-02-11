from __future__ import annotations

import contextlib
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QApplication, QDialog, QFileDialog, QInputDialog, QMessageBox

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
from py_rme_canary.core.io.otmm_saver import save_otmm_atomic
from py_rme_canary.core.io.xml.safe import safe_etree as ElementTree  # noqa: N812
from py_rme_canary.logic_layer.editor_session import EditorSession
from py_rme_canary.logic_layer.map_format_conversion import (
    analyze_map_format_conversion,
    apply_map_format_version,
)

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


logger = logging.getLogger(__name__)


class QtMapEditorFileMixin:
    def _new_map(self: QtMapEditor) -> None:
        """Create new map with template selection."""
        from py_rme_canary.vis_layer.ui.dialogs.new_map_dialog import NewMapDialog

        # Show dialog
        dialog = NewMapDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # Get template and settings from dialog
        template = dialog.get_template()
        map_size = dialog.get_map_size()
        description = dialog.get_description()
        # Note: map_name and author from dialog could be used for future metadata

        # Create new map with template settings
        self.current_path = None
        self.map = GameMap(
            header=MapHeader(
                otbm_version=template.otbm_version,
                width=map_size.width,
                height=map_size.height,
                description=description,
            )
        )
        self.session = EditorSession(self.map, self.brush_mgr, on_tiles_changed=self._on_tiles_changed)
        self.apply_ui_state_to_session()
        self.viewport.origin_x = 0
        self.viewport.origin_y = 0
        try:
            self._apply_preferences_for_new_map()
        except Exception:
            logger.exception("Failed to apply preferences for new map")
        self.canvas.update()

    def _open_otbm(self: QtMapEditor) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Map",
            "",
            "OTBM Maps (*.otbm *.otgz);;JSON Maps (*.json);;OTML Maps (*.otml);;XML Maps (*.xml);;All Map Files (*.otbm *.otgz *.json *.otml *.xml);;All Files (*)",
        )
        if not path:
            return
        logger.info("Opening map: %s", path)
        from py_rme_canary.vis_layer.ui.widgets.modern_progress_dialog import ModernProgressDialog

        progress = ModernProgressDialog(
            title="Opening Map",
            label_text="Detecting map format...",
            minimum=0,
            maximum=6,
            parent=self
        )
        progress.show()

        def advance(step: int, message: str) -> None:
            progress.setLabelText(message)
            progress.setValue(int(step))
            QApplication.processEvents()
            if progress.wasCanceled():
                raise RuntimeError("Map loading canceled by user.")

        try:
            advance(1, "Detecting map format...")
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
                QMessageBox.warning(
                    self, "Unknown map", f"Could not detect a supported map format.\n\nReason: {det.reason}"
                )
                return

            advance(2, "Reading map file and translating IDs...")
            loader = OTBMLoader()
            gm = loader.load_with_detection(path)

            advance(3, "Creating editor session...")
            self.current_path = loader.last_otbm_path or path
            self.map = gm
            self.session = EditorSession(self.map, self.brush_mgr, on_tiles_changed=self._on_tiles_changed)
            self.apply_ui_state_to_session()
            self.viewport.origin_x = 0
            self.viewport.origin_y = 0
            self._set_id_mapper(loader.last_id_mapper)

            advance(4, "Applying map context and assets...")
            md = (gm.load_report or {}).get("metadata") or {}
            self._apply_detected_context(md)
            src = md.get("source") or "unknown"

            advance(5, "Finalizing project metadata...")
            if det.kind == "otbm" and loader.last_config is not None and loader.last_otbm_path is not None:
                self._maybe_write_default_project_json(
                    opened_otbm_path=str(loader.last_otbm_path),
                    cfg=loader.last_config,
                )

            advance(6, "Refreshing viewport and palettes...")
            self._update_status_capabilities(prefix=f"Loaded: {self.current_path} | source={src}")
            with contextlib.suppress(Exception):
                self.palettes.refresh_primary_list()
            self.canvas.update()

            # Build and show post-load summary
            try:
                report = gm.load_report or {}
                warnings = report.get("warnings") or []
                dyn = report.get("dynamic_id_conversions") or {}
                unknown_count = report.get("unknown_ids_count") or 0

                header = gm.header
                summary_lines = [
                    f"Map: {Path(self.current_path).name}",
                    f"OTBM version: {header.otbm_version}",
                    f"Dimensions: {header.width} × {header.height}",
                    f"Tiles loaded: {len(gm.tiles):,}",
                    f"Towns: {len(gm.towns)}  |  Waypoints: {len(gm.waypoints)}",
                    f"Source: {src}",
                ]

                if header.description:
                    desc_preview = header.description[:120]
                    if len(header.description) > 120:
                        desc_preview += "…"
                    summary_lines.append(f"Description: {desc_preview}")

                if dyn:
                    summary_lines.append(f"Dynamic ID conversions: {sum(dyn.values()) if isinstance(dyn, dict) else dyn}")
                if unknown_count:
                    summary_lines.append(f"Unknown IDs skipped: {unknown_count}")
                if warnings:
                    summary_lines.append(f"\nWarnings ({len(warnings)}):")
                    for w in warnings[:8]:
                        w_str = str(getattr(w, "message", w))
                        summary_lines.append(f"  • {w_str[:120]}")
                    if len(warnings) > 8:
                        summary_lines.append(f"  … and {len(warnings) - 8} more")
                else:
                    summary_lines.append("\nNo warnings.")

                summary_text = "\n".join(summary_lines)
                QMessageBox.information(self, "Map Loaded", summary_text)

                logger.info(
                    "Load report: warnings=%s unknown_ids=%s dynamic_conversions=%s",
                    len(warnings),
                    unknown_count,
                    dyn,
                )
            except Exception:
                logger.exception("Failed to show load report")

        except Exception as e:
            QMessageBox.critical(self, "Open failed", str(e))
            logger.exception("Open map failed")
        finally:
            progress.close()

    def _save_as(self: QtMapEditor) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save OTBM As", "", "OTBM Maps (*.otbm);;Compressed OTBM (*.otgz);;All Files (*)"
        )
        if not path:
            return
        if not path.lower().endswith(".otbm"):
            path += ".otbm"
        self.current_path = path
        self._save()

    def _save(self: QtMapEditor) -> None:
        if not self.current_path:
            self._save_as()
            return
        try:
            if getattr(self, "id_mapper", None) is not None:
                save_game_map_bundle_atomic(self.current_path, self.map, id_mapper=self.id_mapper)
            else:
                save_game_map_bundle_atomic(self.current_path, self.map)
        except Exception as e:
            QMessageBox.critical(self, "Save failed", str(e))
            logger.exception("Save failed")

    def _import_monsters_npcs(self: QtMapEditor) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Monsters/NPC...", "", "Lua Files (*.lua);;All Files (*)")
        if not path:
            return
        try:
            result = import_lua_creatures_from_file(path)
        except Exception as exc:
            QMessageBox.critical(self, "Import Monsters/NPC...", str(exc))
            return
        self._show_creature_import_result(result, "Import Monsters/NPC...")

    def _import_monster_folder(self: QtMapEditor) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Import Monster Folder...")
        if not folder:
            return
        try:
            result = import_lua_creatures_from_folder(Path(folder))
        except Exception as exc:
            QMessageBox.critical(self, "Import Monster Folder...", str(exc))
            return
        self._show_creature_import_result(result, "Import Monster Folder...")

    def _show_creature_import_result(self: QtMapEditor, result: LuaCreatureImportResult, title: str) -> None:
        if result.files_scanned <= 0:
            QMessageBox.information(self, title, "No Lua files found.")
            return
        if result.total_imported <= 0:
            QMessageBox.information(self, title, "No valid monsters or NPCs found.")
            return

        clear_creature_name_cache()
        with contextlib.suppress(Exception):
            self.palettes.refresh_primary_list()

        lines = [
            f"Files scanned: {int(result.files_scanned)}",
            f"Monsters: +{int(result.monsters_added)} / updated {int(result.monsters_updated)}",
            f"NPCs: +{int(result.npcs_added)} / updated {int(result.npcs_updated)}",
        ]
        QMessageBox.information(self, title, "\n".join(lines))

    def _import_map(self: QtMapEditor) -> None:
        from py_rme_canary.vis_layer.ui.main_window.import_map_dialog import ImportMapDialog

        dialog = ImportMapDialog(self, current_map=self.map)
        if dialog.exec():
            self.canvas.update()

    def _convert_map_format(self: QtMapEditor) -> None:
        if self.map is None:
            return
        current_version = int(self.map.header.otbm_version)
        options: list[tuple[str, int]] = [
            ("ServerID (OTBM 1)", 0),
            ("ServerID (OTBM 2)", 1),
            ("ServerID (OTBM 3)", 2),
            ("ServerID (OTBM 4)", 3),
            ("ClientID (OTBM 5)", 4),
            ("ClientID (OTBM 6)", 5),
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

    def _open_preferences(self: QtMapEditor) -> None:
        from py_rme_canary.vis_layer.ui.main_window.preferences_dialog import PreferencesDialog

        dialog = PreferencesDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        with contextlib.suppress(Exception):
            self._update_status_capabilities(prefix="Preferences updated")
        self.status.showMessage("Preferences updated")

    def _reload_data_files(self: QtMapEditor) -> None:
        try:
            clear_creature_name_cache()

            profile = getattr(self, "asset_profile", None)
            if profile is not None:
                self._apply_asset_profile(profile)

            with contextlib.suppress(Exception):
                self.palettes.refresh_primary_list()

            self.canvas.update()
            self._update_status_capabilities(prefix="Data files reloaded")
        except Exception as exc:
            logger.exception("Failed to reload data files")
            QMessageBox.critical(self, "Reload Data Files", str(exc))

    def _export_otmm(self: QtMapEditor) -> None:
        if self.map is None:
            QMessageBox.information(self, "Export OTMM", "No map loaded.")
            return

        out_path, _ = QFileDialog.getSaveFileName(self, "Export OTMM", "", "OTMM (*.otmm);;All Files (*)")
        if not out_path:
            return
        if not out_path.lower().endswith(".otmm"):
            out_path += ".otmm"

        try:
            save_otmm_atomic(out_path, self.map)
        except Exception as exc:
            logger.exception("OTMM map export failed")
            QMessageBox.critical(self, "Export OTMM", str(exc))
            return

        QMessageBox.information(self, "Export OTMM", f"Map exported successfully:\n{out_path}")

    def _collect_tilesets_by_type(self: QtMapEditor) -> dict[str, list[object]]:
        grouped: dict[str, list[object]] = defaultdict(list)
        brushes = getattr(getattr(self, "brush_mgr", None), "_brushes", None)
        if not isinstance(brushes, dict):
            return {}

        for brush in brushes.values():
            brush_type = str(getattr(brush, "brush_type", "misc") or "misc").strip().lower()
            grouped[brush_type].append(brush)

        for brush_list in grouped.values():
            brush_list.sort(key=lambda b: int(getattr(b, "server_id", 0)))
        return dict(sorted(grouped.items(), key=lambda kv: kv[0]))

    def _build_tilesets_payload(
        self: QtMapEditor, *, selected_tilesets: list[str], include_items: bool
    ) -> dict[str, object]:
        grouped = self._collect_tilesets_by_type()
        tilesets_payload: list[dict[str, object]] = []

        for raw_name in selected_tilesets:
            name = str(raw_name).strip().lower()
            brushes = grouped.get(name, [])
            brush_payload: list[dict[str, object]] = []

            for brush in brushes:
                row: dict[str, object] = {
                    "id": int(getattr(brush, "server_id", 0)),
                    "name": str(getattr(brush, "name", "")),
                    "type": str(getattr(brush, "brush_type", "")),
                }
                if include_items:
                    family_ids = sorted(int(v) for v in getattr(brush, "family_ids", ()) or ())
                    borders_raw = getattr(brush, "borders", {}) or {}
                    borders = {str(side): int(item_id) for side, item_id in dict(borders_raw).items()}
                    transitions_raw = getattr(brush, "transition_borders", {}) or {}
                    transitions: dict[str, dict[str, int]] = {}
                    for target_id, transition_borders in dict(transitions_raw).items():
                        transitions[str(int(target_id))] = {
                            str(side): int(item_id) for side, item_id in dict(transition_borders).items()
                        }
                    row["family_ids"] = family_ids
                    row["borders"] = borders
                    row["transition_borders"] = transitions
                    row["randomize_ids"] = [int(v) for v in getattr(brush, "randomize_ids", ()) or ()]
                brush_payload.append(row)

            tilesets_payload.append(
                {
                    "name": str(raw_name),
                    "count": int(len(brush_payload)),
                    "brushes": brush_payload,
                }
            )

        return {
            "format_version": 1,
            "generated_by": "py_rme_canary",
            "tilesets": tilesets_payload,
        }

    def _write_tilesets_xml(self: QtMapEditor, payload: dict[str, object], output_path: Path) -> None:
        root = ElementTree.Element(
            "tilesets",
            {
                "format_version": str(payload.get("format_version", 1)),
                "generated_by": str(payload.get("generated_by", "py_rme_canary")),
            },
        )

        tilesets_raw = payload.get("tilesets", [])
        if isinstance(tilesets_raw, list):
            for tileset in tilesets_raw:
                if not isinstance(tileset, dict):
                    continue
                ts_node = ElementTree.SubElement(
                    root,
                    "tileset",
                    {
                        "name": str(tileset.get("name", "")),
                        "count": str(int(tileset.get("count", 0) or 0)),
                    },
                )
                brushes_raw = tileset.get("brushes", [])
                if not isinstance(brushes_raw, list):
                    continue
                for brush in brushes_raw:
                    if not isinstance(brush, dict):
                        continue
                    b_node = ElementTree.SubElement(
                        ts_node,
                        "brush",
                        {
                            "id": str(int(brush.get("id", 0) or 0)),
                            "name": str(brush.get("name", "")),
                            "type": str(brush.get("type", "")),
                        },
                    )
                    family_ids = brush.get("family_ids", [])
                    if isinstance(family_ids, list):
                        for family_id in family_ids:
                            ElementTree.SubElement(b_node, "family_id", {"value": str(int(family_id))})

                    borders = brush.get("borders", {})
                    if isinstance(borders, dict):
                        for side, item_id in sorted(borders.items(), key=lambda kv: str(kv[0])):
                            ElementTree.SubElement(
                                b_node,
                                "border",
                                {
                                    "side": str(side),
                                    "item_id": str(int(item_id)),
                                },
                            )

                    transitions = brush.get("transition_borders", {})
                    if isinstance(transitions, dict):
                        for to_id, transition_borders in sorted(transitions.items(), key=lambda kv: str(kv[0])):
                            t_node = ElementTree.SubElement(b_node, "transition", {"to_id": str(to_id)})
                            if isinstance(transition_borders, dict):
                                for side, item_id in sorted(transition_borders.items(), key=lambda kv: str(kv[0])):
                                    ElementTree.SubElement(
                                        t_node,
                                        "border",
                                        {
                                            "side": str(side),
                                            "item_id": str(int(item_id)),
                                        },
                                    )

                    randomize_ids = brush.get("randomize_ids", [])
                    if isinstance(randomize_ids, list):
                        for randomize_id in randomize_ids:
                            ElementTree.SubElement(b_node, "randomize_id", {"value": str(int(randomize_id))})

        tree = ElementTree.ElementTree(root)
        with contextlib.suppress(Exception):
            ElementTree.indent(tree, space="  ")
        tree.write(output_path, encoding="utf-8", xml_declaration=True)

    def _export_tilesets(self: QtMapEditor) -> None:
        from py_rme_canary.vis_layer.ui.dialogs.export_tilesets_dialog import ExportFormat, ExportTilesetsDialog

        grouped = self._collect_tilesets_by_type()
        if not grouped:
            QMessageBox.information(self, "Export Tilesets", "No tilesets available to export.")
            return

        dialog = ExportTilesetsDialog(tilesets=list(grouped.keys()), default_path=Path.cwd(), parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        selected = dialog.get_selected_tilesets()
        if not selected:
            QMessageBox.information(self, "Export Tilesets", "No tilesets selected.")
            return

        output_path = dialog.get_export_path()
        options = dialog.get_options()
        include_items = bool(options.get("include_items", True))
        pretty_print = bool(options.get("pretty_print", True))
        payload = self._build_tilesets_payload(selected_tilesets=selected, include_items=include_items)

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            export_format = dialog.get_export_format()
            if export_format == ExportFormat.JSON:
                with output_path.open("w", encoding="utf-8") as fp:
                    if pretty_print:
                        json.dump(payload, fp, ensure_ascii=False, indent=2)
                    else:
                        json.dump(payload, fp, ensure_ascii=False, separators=(",", ":"))
            else:
                self._write_tilesets_xml(payload, output_path)
        except Exception as exc:
            logger.exception("Tileset export failed")
            QMessageBox.critical(self, "Export Tilesets", str(exc))
            return

        QMessageBox.information(self, "Export Tilesets", f"Tilesets exported successfully:\n{output_path}")

    def _discover_extensions(self: QtMapEditor) -> list[object]:
        from py_rme_canary.vis_layer.ui.dialogs.extensions_dialog import MaterialExtension

        ext_dir = Path.home() / ".py_rme_canary" / "extensions"
        if not ext_dir.exists():
            return []

        out: list[object] = []
        for path in sorted(ext_dir.iterdir(), key=lambda p: p.name.casefold()):
            if path.name.startswith("."):
                continue

            if path.is_file() and path.suffix.lower() == ".json":
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    out.append(
                        MaterialExtension(
                            name=str(data.get("name") or path.stem),
                            author=str(data.get("author") or ""),
                            description=str(data.get("description") or ""),
                            version_string=str(data.get("version") or ""),
                            url=str(data.get("url") or ""),
                            author_url=str(data.get("author_url") or ""),
                            file_path=str(path),
                        )
                    )
                    continue
                except Exception:
                    logger.exception("Failed to parse extension metadata: %s", path)

            out.append(
                MaterialExtension(
                    name=str(path.stem if path.is_file() else path.name),
                    author="",
                    description=f"Detected local extension entry: {path.name}",
                    version_string="",
                    file_path=str(path),
                )
            )
        return out

    def _open_extensions_dialog(self: QtMapEditor) -> None:
        from py_rme_canary.vis_layer.ui.dialogs.extensions_dialog import ExtensionsDialog

        dialog = ExtensionsDialog(parent=self, extensions=self._discover_extensions())
        dialog.exec()

    def _goto_website(self: QtMapEditor) -> None:
        target_url = "https://github.com/Marcelol090/RME-Python"
        if not QDesktopServices.openUrl(QUrl(target_url)):
            QMessageBox.warning(self, "Goto Website", f"Could not open browser for:\n{target_url}")

    # ------------------------------------------------------------------
    # C++ parity stubs (File menu)
    # ------------------------------------------------------------------

    def _generate_map(self: QtMapEditor) -> None:
        """Open map template generation flow (C++ GENERATE_MAP action parity baseline)."""
        # Legacy action opens a generation flow. In Python, reuse the modern template-driven
        # new-map pipeline instead of keeping a dead-end stub.
        self._new_map()
        with contextlib.suppress(Exception):
            self.status.showMessage("Generate Map: template flow opened")

    def _close_map(self: QtMapEditor) -> None:
        """Close the currently open map without exiting (C++ CLOSE action)."""
        if getattr(self, "_dirty", False):
            reply = QMessageBox.question(
                self,
                "Close Map",
                "The current map has unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )
            if reply == QMessageBox.StandardButton.Cancel:
                return
            if reply == QMessageBox.StandardButton.Save:
                self._save()

        # Reset to empty map
        self.map = GameMap(header=MapHeader(width=256, height=256))
        self.session = EditorSession(self.map)
        self._current_file_path = None
        self._dirty = False
        self.setWindowTitle("Canary Map Editor")
        self.status.showMessage("Map closed.")
        with contextlib.suppress(Exception):
            self.canvas.update()
        with contextlib.suppress(Exception):
            self._update_action_enabled_states()

    def _export_minimap(self: QtMapEditor) -> None:
        """Export the minimap to an image file (C++ EXPORT_MINIMAP action)."""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Minimap",
            "",
            "PNG Image (*.png);;BMP Image (*.bmp);;All Files (*.*)",
        )
        if not path:
            return

        try:
            from PyQt6.QtGui import QColor, QImage

            header = self.map.header
            w = int(header.width)
            h = int(header.height)
            z = int(self.viewport.z)

            img = QImage(w, h, QImage.Format.Format_RGB32)
            img.fill(QColor(0, 0, 0))

            for y in range(h):
                for x in range(w):
                    tile = self.map.get_tile(x, y, z)
                    if tile is None:
                        continue
                    color = self.map_drawer._get_tile_color(tile) if hasattr(self, "map_drawer") else (100, 100, 100, 255)
                    r, g, b = int(color[0]), int(color[1]), int(color[2])
                    img.setPixelColor(x, y, QColor(r, g, b))

            if img.save(str(path)):
                self.status.showMessage(f"Minimap exported: {path}")
            else:
                QMessageBox.critical(self, "Export Minimap", f"Failed to save image to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Minimap", str(exc))
