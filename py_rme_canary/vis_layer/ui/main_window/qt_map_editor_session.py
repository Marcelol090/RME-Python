from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any, cast

from PyQt6.QtWidgets import QInputDialog, QMessageBox

if TYPE_CHECKING:
    from .editor import QtMapEditor


class QtMapEditorSessionMixin:
    def _as_editor(self) -> QtMapEditor:
        return cast("QtMapEditor", self)

    def __getattr__(self, name: str) -> Any:  # pragma: no cover
        raise AttributeError(name)

    # ---------- editor/model actions ----------

    def apply_ui_state_to_session(self) -> None:
        self.session.set_automagic(bool(self.automagic_cb.isChecked()))
        self.session.set_merge_move(bool(self.act_merge_move.isChecked()))
        self.session.set_borderize_drag(bool(self.act_borderize_drag.isChecked()), threshold=6000)
        self.session.set_merge_paste(bool(self.act_merge_paste.isChecked()))
        self.session.set_borderize_paste(bool(self.act_borderize_paste.isChecked()), threshold=10000)

    def _toggle_automagic(self, enabled: bool) -> None:
        # Keep legacy hotkey action and toolbar checkbox in sync.
        try:
            self.automagic_cb.blockSignals(True)
            self.automagic_cb.setChecked(bool(enabled))
            self.automagic_cb.blockSignals(False)
        except Exception:
            pass
        self.apply_ui_state_to_session()
        self.status.showMessage(f"Automagic {'enabled' if enabled else 'disabled'}")

    def _toggle_symmetry_vertical(self, enabled: bool) -> None:
        """Toggle vertical symmetry mode."""
        from py_rme_canary.logic_layer.symmetry_manager import get_symmetry_manager

        manager = get_symmetry_manager()
        manager.vertical_enabled = bool(enabled)

        # Initialize center if not set
        if manager.center_x == 0 and hasattr(self, "session"):
            try:
                w = getattr(self.session, "map_width", 2048) or 2048
                manager.center_x = w // 2
            except Exception:
                manager.center_x = 1024

        self.status.showMessage(f"Symmetry Vertical {'enabled' if enabled else 'disabled'}")
        self._update_symmetry_overlay()

    def _toggle_symmetry_horizontal(self, enabled: bool) -> None:
        """Toggle horizontal symmetry mode."""
        from py_rme_canary.logic_layer.symmetry_manager import get_symmetry_manager

        manager = get_symmetry_manager()
        manager.horizontal_enabled = bool(enabled)

        # Initialize center if not set
        if manager.center_y == 0 and hasattr(self, "session"):
            try:
                h = getattr(self.session, "map_height", 2048) or 2048
                manager.center_y = h // 2
            except Exception:
                manager.center_y = 1024

        self.status.showMessage(f"Symmetry Horizontal {'enabled' if enabled else 'disabled'}")
        self._update_symmetry_overlay()

    def _update_symmetry_overlay(self) -> None:
        """Update symmetry overlay widget if present."""
        if hasattr(self, "symmetry_overlay"):
            with contextlib.suppress(Exception):
                self.symmetry_overlay.update()

    def _borderize_selection(self, _checked: bool = False) -> None:
        if not self.session.has_selection():
            self.status.showMessage("Borderize selection: nothing selected")
            return

        try:
            action = self.session.borderize_selection()
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Borderize Selection", str(e))
            return

        if action is None:
            self.status.showMessage("Borderize selection: no changes")
        else:
            self.canvas.update()
            self.status.showMessage("Borderize selection: done")
        self._update_action_enabled_states()

    def _open_border_builder(self) -> None:
        from py_rme_canary.vis_layer.ui.dialogs.border_builder_dialog import BorderBuilderDialog

        brush_manager = getattr(self.session, "brush_manager", None)
        if brush_manager is None:
            brush_manager = getattr(self, "brush_manager", None)

        dialog = BorderBuilderDialog(brush_manager, parent=self._as_editor())
        dialog.exec()
        with contextlib.suppress(Exception):
            self.canvas.update()

    def _export_png(self) -> None:
        """Open PNG export dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.png_export_dialog import PNGExportDialog

        dialog = PNGExportDialog(parent=self._as_editor(), session=self.session)
        dialog.exec()

    def _toggle_dark_mode(self, enabled: bool) -> None:
        """Toggle dark mode theme."""
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            if enabled:
                from py_rme_canary.vis_layer.ui.theme.integration import apply_modern_theme

                apply_modern_theme(app)
            else:
                app.setStyleSheet("")

        self.status.showMessage(f"Dark Mode {'enabled' if enabled else 'disabled'}")

    def _replace_items(self) -> None:
        """Open Replace Items dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.replace_items_dialog import ReplaceItemsDialog

        dialog = ReplaceItemsDialog(parent=self._as_editor(), session=self.session)
        dialog.exec()

    def _check_uid(self) -> None:
        """Open UID Report dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.uid_report_dialog import UIDReportDialog

        dialog = UIDReportDialog(parent=self._as_editor(), session=self.session)
        dialog.show()  # Non-modal for navigation while dialog is open

    def _clear_modified_state(self) -> None:
        ret = QMessageBox.question(
            self._as_editor(),
            "Clear Modified State",
            "This will have the same effect as closing the map and opening it again. Do you want to proceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret != QMessageBox.StandardButton.Yes:
            return

        cleared = int(self.session.clear_modified_state())
        self.status.showMessage(f"Clear modified state: {cleared} tiles")
        self.canvas.update()

    def _clear_invalid_tiles(self, *, selection_only: bool) -> None:
        if bool(selection_only) and not self.session.has_selection():
            self.status.showMessage("Clear invalid tiles: nothing selected")
            return

        if not bool(selection_only):
            ret = QMessageBox.question(
                self._as_editor(),
                "Clear Invalid Tiles (Map)",
                "This will remove placeholder/unknown items (id=0 / unknown replacements) from the entire map. Do you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ret != QMessageBox.StandardButton.Yes:
                return

        try:
            removed, action = self.session.clear_invalid_tiles(selection_only=bool(selection_only))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Clear Invalid Tiles", str(e))
            return

        if action is None:
            self.status.showMessage("Clear invalid tiles: no changes")
        else:
            scope = "selection" if bool(selection_only) else "map"
            self.status.showMessage(f"Clear invalid tiles ({scope}): removed {int(removed)} items")
            self.canvas.update()
        self._update_action_enabled_states()

    def _map_remove_item_global(self) -> None:
        from py_rme_canary.vis_layer.ui.main_window.dialogs import FindItemDialog

        dialog = FindItemDialog(self._as_editor(), title="Remove Item From Map")
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        server_id = int(dialog.result_value().server_id)
        if server_id <= 0:
            self.status.showMessage("Remove item: invalid serverId")
            return

        try:
            removed, action = self.session.remove_items(server_id=int(server_id), selection_only=False)
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Remove Item", str(e))
            return

        if action is None:
            self.status.showMessage("Remove item: no changes")
        else:
            self.status.showMessage(f"Remove item: {int(removed)} item(s) deleted")
            self.canvas.update()
        self._update_action_enabled_states()

    def _map_remove_corpses(self) -> None:
        ret = QMessageBox.question(
            self._as_editor(),
            "Remove Corpses",
            "Do you want to remove all corpses from the map?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret != QMessageBox.StandardButton.Yes:
            return

        try:
            removed, action = self.session.remove_corpses()
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Remove Corpses", str(e))
            return

        if action is None:
            self.status.showMessage("Remove corpses: no changes")
        else:
            self.status.showMessage(f"Remove corpses: {int(removed)} item(s) deleted")
            self.canvas.update()
        self._update_action_enabled_states()

    def _map_remove_unreachable(self) -> None:
        ret = QMessageBox.question(
            self._as_editor(),
            "Remove Unreachable Tiles",
            "Do you want to remove all unreachable items from the map?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret != QMessageBox.StandardButton.Yes:
            return

        try:
            removed, action = self.session.remove_unreachable_tiles()
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Remove Unreachable Tiles", str(e))
            return

        if action is None:
            self.status.showMessage("Remove unreachable: no changes")
        else:
            self.status.showMessage(f"Remove unreachable: {int(removed)} tile(s) deleted")
            self.canvas.update()
        self._update_action_enabled_states()

    def _map_clear_invalid_house_tiles(self) -> None:
        ret = QMessageBox.question(
            self._as_editor(),
            "Clear Invalid House Tiles",
            "Are you sure you want to remove all house tiles that do not belong to a house?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ret != QMessageBox.StandardButton.Yes:
            return

        try:
            result, action = self.session.clear_invalid_house_tiles()
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Clear Invalid House Tiles", str(e))
            return

        if action is None:
            self.status.showMessage("Clear invalid house tiles: no changes")
        else:
            self.status.showMessage(
                "Clear invalid house tiles: "
                f"removed {int(result.houses_removed)} house definition(s), "
                f"cleared {int(result.tile_refs_cleared)} tile ref(s)"
            )
            self.canvas.update()
        self._update_action_enabled_states()

    def _randomize(self, *, selection_only: bool) -> None:
        if bool(selection_only) and not self.session.has_selection():
            self.status.showMessage("Randomize: nothing selected")
            return

        if not bool(selection_only):
            ret = QMessageBox.question(
                self._as_editor(),
                "Randomize (Map)",
                "This will randomize ground tiles across the entire map for brushes that define randomize_ids. Do you want to proceed?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if ret != QMessageBox.StandardButton.Yes:
                return

        try:
            if bool(selection_only):
                changed, action = self.session.randomize_selection()
            else:
                changed, action = self.session.randomize_map()
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Randomize", str(e))
            return

        if action is None:
            self.status.showMessage("Randomize: no changes")
        else:
            scope = "selection" if bool(selection_only) else "map"
            self.status.showMessage(f"Randomize ({scope}): changed {int(changed)} tiles")
            self.canvas.update()
        self._update_action_enabled_states()

    # ---------- tools: waypoints / houses ----------

    def _town_add_edit(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        tid, ok = QInputDialog.getInt(self._as_editor(), "Add/Edit Town", "Town ID:", 1, 1, 2**31 - 1, 1)
        if not ok:
            return
        tid = int(tid)

        before = (getattr(self.session.game_map, "towns", None) or {}).get(tid)
        default_name = str(before.name) if before is not None else ""
        name, ok = QInputDialog.getText(self._as_editor(), "Add/Edit Town", "Town name:", text=default_name)
        if not ok:
            return
        name = str(name).strip()
        if not name:
            self.status.showMessage("Add/edit town: canceled")
            return

        if before is None:
            tx, ty, tz = int(x), int(y), int(z)
        else:
            pos = getattr(before, "temple_position", None)
            if pos is None:
                tx, ty, tz = int(x), int(y), int(z)
            else:
                tx, ty, tz = int(pos.x), int(pos.y), int(pos.z)

        try:
            action = self.session.upsert_town(
                town_id=int(tid),
                name=name,
                temple_x=int(tx),
                temple_y=int(ty),
                temple_z=int(tz),
            )
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Add/Edit Town", str(e))
            return

        if action is None:
            self.status.showMessage("Add/edit town: no changes")
        else:
            self.status.showMessage(f"Town saved: {int(tid)} ({name})")
            self.canvas.update()
        self._update_action_enabled_states()

    def _town_set_temple_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        towns = getattr(self.session.game_map, "towns", None) or {}
        if not towns:
            self.status.showMessage("Set town temple: no towns")
            return

        items = [f"{int(t.id)}: {t.name}" for t in sorted(towns.values(), key=lambda t: int(t.id))]
        item, ok = QInputDialog.getItem(self._as_editor(), "Set Town Temple", "Town:", items, 0, False)
        if not ok:
            return
        item = str(item)
        try:
            tid = int(item.split(":", 1)[0].strip())
        except Exception:
            return

        try:
            action = self.session.set_town_temple_position(town_id=int(tid), x=int(x), y=int(y), z=int(z))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Set Town Temple", str(e))
            return

        if action is None:
            self.status.showMessage("Set town temple: no changes")
        else:
            self.status.showMessage(f"Town temple set: {int(tid)} @ {int(x)},{int(y)},{int(z)}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _town_delete(self) -> None:
        towns = getattr(self.session.game_map, "towns", None) or {}
        if not towns:
            self.status.showMessage("Delete town: none")
            return

        items = [f"{int(t.id)}: {t.name}" for t in sorted(towns.values(), key=lambda t: int(t.id))]
        item, ok = QInputDialog.getItem(self._as_editor(), "Delete Town", "Town:", items, 0, False)
        if not ok:
            return
        item = str(item)
        try:
            tid = int(item.split(":", 1)[0].strip())
        except Exception:
            return

        if (
            QMessageBox.question(
                self._as_editor(),
                "Delete Town",
                f"Delete town {int(tid)}?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            action = self.session.delete_town(town_id=int(tid))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Delete Town", str(e))
            return

        if action is None:
            self.status.showMessage("Delete town: no changes")
        else:
            self.status.showMessage(f"Deleted town: {int(tid)}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _zone_add_edit(self) -> None:
        zid, ok = QInputDialog.getInt(self._as_editor(), "Add/Edit Zone", "Zone ID:", 1, 1, 2**31 - 1, 1)
        if not ok:
            return
        zid = int(zid)

        zones = getattr(self.session.game_map, "zones", None) or {}
        before = zones.get(zid)
        default_name = str(before.name) if before is not None else ""
        name, ok = QInputDialog.getText(self._as_editor(), "Add/Edit Zone", "Zone name:", text=default_name)
        if not ok:
            return
        name = str(name).strip()
        if not name:
            self.status.showMessage("Add/edit zone: canceled")
            return

        try:
            action = self.session.upsert_zone(zone_id=int(zid), name=name)
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Add/Edit Zone", str(e))
            return

        if action is None:
            self.status.showMessage("Add/edit zone: no changes")
        else:
            self.status.showMessage(f"Zone saved: {int(zid)} ({name})")
            self.canvas.update()
            with contextlib.suppress(Exception):
                self.palettes.refresh_primary_list()
        self._update_action_enabled_states()

    def _zone_delete_definition(self) -> None:
        zones = getattr(self.session.game_map, "zones", None) or {}
        if not zones:
            self.status.showMessage("Delete zone: none")
            return

        items = [f"{int(z.id)}: {z.name}" for z in sorted(zones.values(), key=lambda z: int(z.id))]
        item, ok = QInputDialog.getItem(self._as_editor(), "Delete Zone", "Zone:", items, 0, False)
        if not ok:
            return
        item = str(item)
        try:
            zid = int(item.split(":", 1)[0].strip())
        except Exception:
            return

        if (
            QMessageBox.question(
                self._as_editor(),
                "Delete Zone",
                f"Delete zone {int(zid)}?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            action = self.session.delete_zone(zone_id=int(zid))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Delete Zone", str(e))
            return

        if action is None:
            self.status.showMessage("Delete zone: no changes")
        else:
            self.status.showMessage(f"Deleted zone: {int(zid)}")
            self.canvas.update()
            with contextlib.suppress(Exception):
                self.palettes.refresh_primary_list()
        self._update_action_enabled_states()

    def _waypoint_set_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        name, ok = QInputDialog.getText(self._as_editor(), "Set Waypoint", "Waypoint name:")
        if not ok:
            return
        name = str(name).strip()
        if not name:
            self.status.showMessage("Set waypoint: canceled")
            return

        try:
            action = self.session.set_waypoint(name=name, x=int(x), y=int(y), z=int(z))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Set Waypoint", str(e))
            return

        if action is None:
            self.status.showMessage("Set waypoint: no changes")
        else:
            self.status.showMessage(f"Set waypoint: {name} @ {int(x)},{int(y)},{int(z)}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _waypoint_delete(self) -> None:
        names = sorted((self.session.game_map.waypoints or {}).keys(), key=lambda s: str(s).casefold())
        if not names:
            self.status.showMessage("Delete waypoint: none")
            return

        name, ok = QInputDialog.getItem(self._as_editor(), "Delete Waypoint", "Waypoint:", names, 0, False)
        if not ok:
            return
        name = str(name).strip()
        if not name:
            return

        try:
            action = self.session.delete_waypoint(name=name)
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Delete Waypoint", str(e))
            return

        if action is None:
            self.status.showMessage("Delete waypoint: no changes")
        else:
            self.status.showMessage(f"Deleted waypoint: {name}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _switch_door_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        try:
            action = self.session.switch_door_at(x=int(x), y=int(y), z=int(z))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Switch Door", str(e))
            return

        if action is None:
            self.status.showMessage("Switch door: none at cursor")
        else:
            self.status.showMessage(f"Switched door @ {int(x)},{int(y)},{int(z)}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _house_set_id_on_selection(self) -> None:
        if not self.session.has_selection():
            self.status.showMessage("Set house id: nothing selected")
            return

        hid, ok = QInputDialog.getInt(self._as_editor(), "Set House ID", "House ID:", 1, 1, 2**31 - 1, 1)
        if not ok:
            return

        try:
            action = self.session.set_house_id_on_selection(house_id=int(hid))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Set House ID", str(e))
            return

        if action is None:
            self.status.showMessage("Set house id: no changes")
        else:
            self.status.showMessage(f"Set house id on selection: {int(hid)}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _house_clear_id_on_selection(self) -> None:
        if not self.session.has_selection():
            self.status.showMessage("Clear house id: nothing selected")
            return

        try:
            action = self.session.set_house_id_on_selection(house_id=None)
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Clear House ID", str(e))
            return

        if action is None:
            self.status.showMessage("Clear house id: no changes")
        else:
            self.status.showMessage("Cleared house id on selection")
            self.canvas.update()
        self._update_action_enabled_states()

    # ---------- tools: houses metadata ----------

    def _house_add_edit(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        hid, ok = QInputDialog.getInt(self._as_editor(), "Add/Edit House", "House ID:", 1, 1, 2**31 - 1, 1)
        if not ok:
            return
        hid = int(hid)

        before = (getattr(self.session.game_map, "houses", None) or {}).get(hid)
        default_name = str(before.name) if before is not None else ""
        name, ok = QInputDialog.getText(self._as_editor(), "Add/Edit House", "House name:", text=default_name)
        if not ok:
            return
        name = str(name).strip()
        if not name:
            self.status.showMessage("Add/edit house: canceled")
            return

        towns = getattr(self.session.game_map, "towns", None) or {}
        if towns:
            items = [f"{int(t.id)}: {t.name}" for t in sorted(towns.values(), key=lambda t: int(t.id))]
            item, ok = QInputDialog.getItem(self._as_editor(), "Add/Edit House", "Town:", items, 0, False)
            if not ok:
                return
            item = str(item)
            try:
                townid = int(item.split(":", 1)[0].strip())
            except Exception:
                return
        else:
            townid, ok = QInputDialog.getInt(self._as_editor(), "Add/Edit House", "Town ID:", 1, 1, 2**31 - 1, 1)
            if not ok:
                return
            townid = int(townid)

        rent_default = int(before.rent) if before is not None else 0
        rent, ok = QInputDialog.getInt(self._as_editor(), "Add/Edit House", "Rent:", rent_default, 0, 2**31 - 1, 1)
        if not ok:
            return

        gh_default = "Yes" if (before is not None and bool(before.guildhall)) else "No"
        gh, ok = QInputDialog.getItem(
            self._as_editor(), "Add/Edit House", "Guildhall:", ["No", "Yes"], 1 if gh_default == "Yes" else 0, False
        )
        if not ok:
            return
        guildhall = str(gh).strip().lower() == "yes"

        # Keep existing entry if any, else default to cursor.
        if before is None or getattr(before, "entry", None) is None:
            entryx, entryy, entryz = int(x), int(y), int(z)
        else:
            e = before.entry
            entryx, entryy, entryz = int(e.x), int(e.y), int(e.z)

        try:
            action = self.session.upsert_house(
                house_id=int(hid),
                name=name,
                townid=int(townid),
                rent=int(rent),
                guildhall=bool(guildhall),
            )
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Add/Edit House", str(e))
            return

        # If newly created and we chose cursor defaults, ensure entry is set.
        if before is None:
            with contextlib.suppress(Exception):
                self.session.set_house_entry(house_id=int(hid), x=int(entryx), y=int(entryy), z=int(entryz))

        if action is None:
            self.status.showMessage("Add/edit house: no changes")
        else:
            self.status.showMessage(f"House saved: {int(hid)} ({name})")
            self.canvas.update()
        self._update_action_enabled_states()

    def _house_set_entry_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        houses = getattr(self.session.game_map, "houses", None) or {}
        if not houses:
            self.status.showMessage("Set house entry: no houses")
            return

        items = [f"{int(h.id)}: {h.name}" for h in sorted(houses.values(), key=lambda h: int(h.id))]
        item, ok = QInputDialog.getItem(self._as_editor(), "Set House Entry", "House:", items, 0, False)
        if not ok:
            return
        item = str(item)
        try:
            hid = int(item.split(":", 1)[0].strip())
        except Exception:
            return

        try:
            action = self.session.set_house_entry(house_id=int(hid), x=int(x), y=int(y), z=int(z))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Set House Entry", str(e))
            return

        if action is None:
            self.status.showMessage("Set house entry: no changes")
        else:
            self.status.showMessage(f"House entry set: {int(hid)} @ {int(x)},{int(y)},{int(z)}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _house_delete_definition(self) -> None:
        houses = getattr(self.session.game_map, "houses", None) or {}
        if not houses:
            self.status.showMessage("Delete house: none")
            return

        items = [f"{int(h.id)}: {h.name}" for h in sorted(houses.values(), key=lambda h: int(h.id))]
        item, ok = QInputDialog.getItem(self._as_editor(), "Delete House", "House:", items, 0, False)
        if not ok:
            return
        item = str(item)
        try:
            hid = int(item.split(":", 1)[0].strip())
        except Exception:
            return

        if (
            QMessageBox.question(
                self._as_editor(),
                "Delete House",
                f"Delete house {int(hid)} definition?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            action = self.session.delete_house(house_id=int(hid))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Delete House", str(e))
            return

        if action is None:
            self.status.showMessage("Delete house: no changes")
        else:
            self.status.showMessage(f"Deleted house: {int(hid)}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _monster_spawn_set_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        radius, ok = QInputDialog.getInt(self._as_editor(), "Set Monster Spawn", "Radius:", 5, 1, 255, 1)
        if not ok:
            return

        try:
            action = self.session.set_monster_spawn_area(x=int(x), y=int(y), z=int(z), radius=int(radius))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Set Monster Spawn", str(e))
            return

        if action is None:
            self.status.showMessage("Set monster spawn: no changes")
        else:
            self.status.showMessage(f"Set monster spawn: {int(x)},{int(y)},{int(z)} r={int(radius)}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _monster_spawn_delete_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        if (
            QMessageBox.question(
                self._as_editor(),
                "Delete Monster Spawn",
                f"Delete monster spawn at {int(x)},{int(y)},{int(z)}?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            action = self.session.delete_monster_spawn_area(x=int(x), y=int(y), z=int(z))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Delete Monster Spawn", str(e))
            return

        if action is None:
            self.status.showMessage("Delete monster spawn: none at cursor")
        else:
            self.status.showMessage(f"Deleted monster spawn: {int(x)},{int(y)},{int(z)}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _npc_spawn_set_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        radius, ok = QInputDialog.getInt(self._as_editor(), "Set NPC Spawn", "Radius:", 5, 1, 255, 1)
        if not ok:
            return

        try:
            action = self.session.set_npc_spawn_area(x=int(x), y=int(y), z=int(z), radius=int(radius))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Set NPC Spawn", str(e))
            return

        if action is None:
            self.status.showMessage("Set NPC spawn: no changes")
        else:
            self.status.showMessage(f"Set NPC spawn: {int(x)},{int(y)},{int(z)} r={int(radius)}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _npc_spawn_delete_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        if (
            QMessageBox.question(
                self._as_editor(),
                "Delete NPC Spawn",
                f"Delete NPC spawn at {int(x)},{int(y)},{int(z)}?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            action = self.session.delete_npc_spawn_area(x=int(x), y=int(y), z=int(z))
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Delete NPC Spawn", str(e))
            return

        if action is None:
            self.status.showMessage("Delete NPC spawn: none at cursor")
        else:
            self.status.showMessage(f"Deleted NPC spawn: {int(x)},{int(y)},{int(z)}")
            self.canvas.update()
        self._update_action_enabled_states()

    def _monster_spawn_add_entry_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        name, ok = QInputDialog.getText(self._as_editor(), "Add Monster", "Monster name:")
        if not ok:
            return
        name = str(name).strip()
        if not name:
            return

        spawntime, ok = QInputDialog.getInt(
            self._as_editor(), "Add Monster", "Spawn time (seconds, 0=default):", 0, 0, 65535, 1
        )
        if not ok:
            return

        weight, ok = QInputDialog.getInt(self._as_editor(), "Add Monster", "Weight (0=omit):", 0, 0, 255, 1)
        if not ok:
            return

        try:
            action = self.session.add_monster_spawn_entry(
                x=int(x),
                y=int(y),
                z=int(z),
                name=name,
                spawntime=int(spawntime),
                weight=None if int(weight) == 0 else int(weight),
            )
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Add Monster", str(e))
            return

        if action is None:
            self.status.showMessage("Add monster: no spawn area covers cursor")
        else:
            self.status.showMessage(f"Added monster: {name} @ {int(x)},{int(y)},{int(z)}")
            self.canvas.update()

    def _monster_spawn_delete_entry_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        # Build choices from entries exactly at this tile.
        names: list[str] = []
        try:
            for area in self.session.game_map.monster_spawns:
                if int(area.center.z) != int(z):
                    continue
                dx = int(int(x) - int(area.center.x))
                dy = int(int(y) - int(area.center.y))
                if max(abs(dx), abs(dy)) > int(area.radius):
                    continue
                for e in area.monsters:
                    if int(e.dx) == dx and int(e.dy) == dy:
                        names.append(str(e.name))
                if names:
                    break
        except Exception:
            names = []

        if not names:
            self.status.showMessage("Delete monster: none at cursor")
            return

        choice, ok = QInputDialog.getItem(self._as_editor(), "Delete Monster", "Monster:", names, 0, False)
        if not ok:
            return
        choice = str(choice).strip()
        if not choice:
            return

        try:
            action = self.session.delete_monster_spawn_entry_at_cursor(x=int(x), y=int(y), z=int(z), name=choice)
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Delete Monster", str(e))
            return

        if action is None:
            self.status.showMessage("Delete monster: no changes")
        else:
            self.status.showMessage(f"Deleted monster: {choice} @ {int(x)},{int(y)},{int(z)}")
            self.canvas.update()

    def _npc_spawn_add_entry_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        name, ok = QInputDialog.getText(self._as_editor(), "Add NPC", "NPC name:")
        if not ok:
            return
        name = str(name).strip()
        if not name:
            return

        spawntime, ok = QInputDialog.getInt(
            self._as_editor(), "Add NPC", "Spawn time (seconds, 0=default):", 0, 0, 65535, 1
        )
        if not ok:
            return

        try:
            action = self.session.add_npc_spawn_entry(
                x=int(x),
                y=int(y),
                z=int(z),
                name=name,
                spawntime=int(spawntime),
            )
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Add NPC", str(e))
            return

        if action is None:
            self.status.showMessage("Add NPC: no spawn area covers cursor")
        else:
            self.status.showMessage(f"Added NPC: {name} @ {int(x)},{int(y)},{int(z)}")
            self.canvas.update()

    def _npc_spawn_delete_entry_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        names: list[str] = []
        try:
            for area in self.session.game_map.npc_spawns:
                if int(area.center.z) != int(z):
                    continue
                dx = int(int(x) - int(area.center.x))
                dy = int(int(y) - int(area.center.y))
                if max(abs(dx), abs(dy)) > int(area.radius):
                    continue
                for e in area.npcs:
                    if int(e.dx) == dx and int(e.dy) == dy:
                        names.append(str(e.name))
                if names:
                    break
        except Exception:
            names = []

        if not names:
            self.status.showMessage("Delete NPC: none at cursor")
            return

        choice, ok = QInputDialog.getItem(self._as_editor(), "Delete NPC", "NPC:", names, 0, False)
        if not ok:
            return
        choice = str(choice).strip()
        if not choice:
            return

        try:
            action = self.session.delete_npc_spawn_entry_at_cursor(x=int(x), y=int(y), z=int(z), name=choice)
        except Exception as e:
            QMessageBox.critical(self._as_editor(), "Delete NPC", str(e))
            return

        if action is None:
            self.status.showMessage("Delete NPC: no changes")
        else:
            self.status.showMessage(f"Deleted NPC: {choice} @ {int(x)},{int(y)},{int(z)}")
            self.canvas.update()

    def _update_action_enabled_states(self) -> None:
        has_sel = bool(self.session.has_selection())
        can_paste = bool(self.session.can_paste())

        self.act_copy.setEnabled(has_sel)
        self.act_cut.setEnabled(has_sel)
        self.act_delete_selection.setEnabled(has_sel)
        self.act_duplicate_selection.setEnabled(has_sel)

        self.act_move_selection_up.setEnabled(has_sel)
        self.act_move_selection_down.setEnabled(has_sel)

        self.act_borderize_selection.setEnabled(has_sel)

        if hasattr(self, "act_clear_invalid_tiles_selection"):
            self.act_clear_invalid_tiles_selection.setEnabled(has_sel)
        if hasattr(self, "act_randomize_selection"):
            self.act_randomize_selection.setEnabled(has_sel)

        if hasattr(self, "act_house_set_id_on_selection"):
            self.act_house_set_id_on_selection.setEnabled(has_sel)
        if hasattr(self, "act_house_clear_id_on_selection"):
            self.act_house_clear_id_on_selection.setEnabled(has_sel)

        if hasattr(self, "act_switch_door_here"):
            self.act_switch_door_here.setEnabled(True)

        self.act_paste.setEnabled(can_paste)

        # Esc should remain meaningful even when no selection.
        self.act_clear_selection.setEnabled(has_sel or bool(self.paste_armed) or bool(self.fill_armed))

    def _on_tiles_changed(self, _changed) -> None:
        self.canvas.update()
        if self.minimap_widget is not None and self.dock_minimap is not None and self.dock_minimap.isVisible():
            self.minimap_widget.update()
        with contextlib.suppress(Exception):
            self.actions_history.refresh()
        self._update_action_enabled_states()

    def _poll_live_events(self) -> None:
        try:
            count = int(self.session.process_live_events())
        except Exception:
            return
        if count > 0:
            self.canvas.update()

    def _handle_live_chat(self, client_id: int, name: str, message: str) -> None:
        if not hasattr(self, "dock_live_log") or self.dock_live_log is None:
            return
        label = str(name or f"#{int(client_id)}")
        self.dock_live_log.add_message(label, str(message))

    def _handle_live_client_list(self, clients: list[dict[str, object]]) -> None:
        if not hasattr(self, "dock_live_log") or self.dock_live_log is None:
            pass
        else:
            self.dock_live_log.update_user_list(clients)
        if hasattr(self, "_friends_sync_live_clients"):
            with contextlib.suppress(Exception):
                self._friends_sync_live_clients(clients)

    def _handle_live_cursor(self, _client_id: int, _x: int, _y: int, _z: int) -> None:
        self.canvas.update()
