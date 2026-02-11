from __future__ import annotations

import contextlib
from collections.abc import Callable
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

    def _confirm(self, title: str, text: str) -> bool:
        return (
            QMessageBox.question(
                self._as_editor(),
                str(title),
                str(text),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        )

    def _run_guarded(self, title: str, operation: Callable[[], Any]) -> tuple[bool, Any]:
        try:
            return True, operation()
        except Exception as exc:
            QMessageBox.critical(self._as_editor(), str(title), str(exc))
            return False, None

    def _apply_action_result(
        self,
        *,
        action: object | None,
        no_changes_message: str,
        changed_message: str,
        refresh_actions: bool = True,
        refresh_palettes: bool = False,
    ) -> None:
        if action is None:
            self.status.showMessage(str(no_changes_message))
        else:
            self.status.showMessage(str(changed_message))
            self.canvas.update()
            if bool(refresh_palettes):
                with contextlib.suppress(Exception):
                    self.palettes.refresh_primary_list()
        if bool(refresh_actions):
            self._update_action_enabled_states()

    @staticmethod
    def _parse_prefixed_int(choice: str) -> int | None:
        with contextlib.suppress(ValueError, TypeError, AttributeError):
            return int(str(choice).split(":", 1)[0].strip())
        return None

    @staticmethod
    def _collect_spawn_entry_names_at_cursor(
        spawn_areas: list[object],
        *,
        entries_attr: str,
        x: int,
        y: int,
        z: int,
    ) -> list[str]:
        from py_rme_canary.logic_layer.rust_accel import spawn_entry_names_at_cursor

        return spawn_entry_names_at_cursor(
            spawn_areas,
            entries_attr=entries_attr,
            x=int(x),
            y=int(y),
            z=int(z),
        )

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

        ok, action = self._run_guarded("Borderize Selection", self.session.borderize_selection)
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Borderize selection: no changes",
            changed_message="Borderize selection: done",
        )

    def _borderize_map(self, _checked: bool = False) -> None:
        """Reborder the entire map (C++ BORDERIZE_MAP action)."""
        reply = QMessageBox.question(
            self._as_editor(),
            "Borderize Map",
            "This will reborder the entire map. This may take a while.\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        ok, action = self._run_guarded("Borderize Map", self.session.borderize_map)
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Borderize map: no changes",
            changed_message="Borderize map: done",
        )

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

    def _replace_items_on_selection(self) -> None:
        """Open Replace Items dialog scoped to selection (C++ REPLACE_ON_SELECTION_ITEMS)."""
        if not self.session.has_selection():
            self.status.showMessage("Replace items on selection: nothing selected")
            return
        from py_rme_canary.vis_layer.ui.dialogs.replace_items_dialog import ReplaceItemsDialog

        dialog = ReplaceItemsDialog(parent=self._as_editor(), session=self.session)
        # Pre-check the "Selection only" checkbox
        if hasattr(dialog, "_selection_only_cb"):
            dialog._selection_only_cb.setChecked(True)
        dialog.exec()

    def _remove_item_on_selection(self) -> None:
        """Remove a specific item from the current selection (C++ REMOVE_ON_SELECTION_ITEM)."""
        if not self.session.has_selection():
            self.status.showMessage("Remove item on selection: nothing selected")
            return
        from py_rme_canary.vis_layer.ui.main_window.dialogs import FindItemDialog

        dialog = FindItemDialog(self._as_editor(), title="Remove Item From Selection")
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        result_value = dialog.result_value()
        if not result_value.resolved:
            self.status.showMessage(result_value.error or "Remove item: unable to resolve item id")
            return

        server_id = int(result_value.server_id)
        if server_id <= 0:
            self.status.showMessage("Remove item: invalid serverId")
            return

        ok, result = self._run_guarded(
            "Remove Item on Selection",
            lambda: self.session.remove_items(server_id=int(server_id), selection_only=True),
        )
        if not ok or result is None:
            return
        removed, action = result

        self._apply_action_result(
            action=action,
            no_changes_message="Remove item on selection: no changes",
            changed_message=f"Remove item on selection: {int(removed)} item(s) deleted",
        )

    def _check_uid(self) -> None:
        """Open UID Report dialog."""
        from py_rme_canary.vis_layer.ui.dialogs.uid_report_dialog import UIDReportDialog

        dialog = UIDReportDialog(parent=self._as_editor(), session=self.session)
        dialog.show()  # Non-modal for navigation while dialog is open

    def _clear_modified_state(self) -> None:
        if not self._confirm(
            "Clear Modified State",
            "This will have the same effect as closing the map and opening it again. Do you want to proceed?",
        ):
            return

        cleared = int(self.session.clear_modified_state())
        self.status.showMessage(f"Clear modified state: {cleared} tiles")
        self.canvas.update()

    def _clear_invalid_tiles(self, *, selection_only: bool) -> None:
        if bool(selection_only) and not self.session.has_selection():
            self.status.showMessage("Clear invalid tiles: nothing selected")
            return

        if not bool(selection_only) and not self._confirm(
            "Clear Invalid Tiles (Map)",
            "This will remove placeholder/unknown items (id=0 / unknown replacements) from the entire map. Do you want to proceed?",
        ):
            return

        ok, result = self._run_guarded(
            "Clear Invalid Tiles",
            lambda: self.session.clear_invalid_tiles(selection_only=bool(selection_only)),
        )
        if not ok or result is None:
            return
        removed, action = result

        scope = "selection" if bool(selection_only) else "map"
        self._apply_action_result(
            action=action,
            no_changes_message="Clear invalid tiles: no changes",
            changed_message=f"Clear invalid tiles ({scope}): removed {int(removed)} items",
        )

    def _map_remove_item_global(self) -> None:
        from py_rme_canary.vis_layer.ui.main_window.dialogs import FindItemDialog

        dialog = FindItemDialog(self._as_editor(), title="Remove Item From Map")
        if dialog.exec() != dialog.DialogCode.Accepted:
            return

        result_value = dialog.result_value()
        if not result_value.resolved:
            self.status.showMessage(result_value.error or "Remove item: unable to resolve item id")
            return

        server_id = int(result_value.server_id)
        if server_id <= 0:
            self.status.showMessage("Remove item: invalid serverId")
            return

        ok, result = self._run_guarded(
            "Remove Item",
            lambda: self.session.remove_items(server_id=int(server_id), selection_only=False),
        )
        if not ok or result is None:
            return
        removed, action = result

        self._apply_action_result(
            action=action,
            no_changes_message="Remove item: no changes",
            changed_message=f"Remove item: {int(removed)} item(s) deleted",
        )

    def _map_remove_corpses(self) -> None:
        if not self._confirm("Remove Corpses", "Do you want to remove all corpses from the map?"):
            return

        ok, result = self._run_guarded("Remove Corpses", self.session.remove_corpses)
        if not ok or result is None:
            return
        removed, action = result

        self._apply_action_result(
            action=action,
            no_changes_message="Remove corpses: no changes",
            changed_message=f"Remove corpses: {int(removed)} item(s) deleted",
        )

    def _map_remove_unreachable(self) -> None:
        if not self._confirm("Remove Unreachable Tiles", "Do you want to remove all unreachable items from the map?"):
            return

        ok, result = self._run_guarded("Remove Unreachable Tiles", self.session.remove_unreachable_tiles)
        if not ok or result is None:
            return
        removed, action = result

        self._apply_action_result(
            action=action,
            no_changes_message="Remove unreachable: no changes",
            changed_message=f"Remove unreachable: {int(removed)} tile(s) deleted",
        )

    def _map_clear_invalid_house_tiles(self) -> None:
        if not self._confirm(
            "Clear Invalid House Tiles",
            "Are you sure you want to remove all house tiles that do not belong to a house?",
        ):
            return

        ok, payload = self._run_guarded("Clear Invalid House Tiles", self.session.clear_invalid_house_tiles)
        if not ok or payload is None:
            return
        result, action = payload

        self._apply_action_result(
            action=action,
            no_changes_message="Clear invalid house tiles: no changes",
            changed_message=(
                "Clear invalid house tiles: "
                f"removed {int(result.houses_removed)} house definition(s), "
                f"cleared {int(result.tile_refs_cleared)} tile ref(s)"
            ),
        )

    def _randomize(self, *, selection_only: bool) -> None:
        if bool(selection_only) and not self.session.has_selection():
            self.status.showMessage("Randomize: nothing selected")
            return

        if not bool(selection_only) and not self._confirm(
            "Randomize (Map)",
            "This will randomize ground tiles across the entire map for brushes that define randomize_ids. Do you want to proceed?",
        ):
            return

        ok, payload = self._run_guarded(
            "Randomize",
            self.session.randomize_selection if bool(selection_only) else self.session.randomize_map,
        )
        if not ok or payload is None:
            return
        changed, action = payload

        scope = "selection" if bool(selection_only) else "map"
        self._apply_action_result(
            action=action,
            no_changes_message="Randomize: no changes",
            changed_message=f"Randomize ({scope}): changed {int(changed)} tiles",
        )

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

        ok, action = self._run_guarded(
            "Add/Edit Town",
            lambda: self.session.upsert_town(
                town_id=int(tid),
                name=name,
                temple_x=int(tx),
                temple_y=int(ty),
                temple_z=int(tz),
            ),
        )
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Add/edit town: no changes",
            changed_message=f"Town saved: {int(tid)} ({name})",
        )

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
        tid = self._parse_prefixed_int(str(item))
        if tid is None:
            return

        ok, action = self._run_guarded(
            "Set Town Temple",
            lambda: self.session.set_town_temple_position(town_id=int(tid), x=int(x), y=int(y), z=int(z)),
        )
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Set town temple: no changes",
            changed_message=f"Town temple set: {int(tid)} @ {int(x)},{int(y)},{int(z)}",
        )

    def _town_delete(self) -> None:
        towns = getattr(self.session.game_map, "towns", None) or {}
        if not towns:
            self.status.showMessage("Delete town: none")
            return

        items = [f"{int(t.id)}: {t.name}" for t in sorted(towns.values(), key=lambda t: int(t.id))]
        item, ok = QInputDialog.getItem(self._as_editor(), "Delete Town", "Town:", items, 0, False)
        if not ok:
            return
        tid = self._parse_prefixed_int(str(item))
        if tid is None:
            return

        if not self._confirm("Delete Town", f"Delete town {int(tid)}?"):
            return

        ok, action = self._run_guarded("Delete Town", lambda: self.session.delete_town(town_id=int(tid)))
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Delete town: no changes",
            changed_message=f"Deleted town: {int(tid)}",
        )

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

        ok, action = self._run_guarded("Add/Edit Zone", lambda: self.session.upsert_zone(zone_id=int(zid), name=name))
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Add/edit zone: no changes",
            changed_message=f"Zone saved: {int(zid)} ({name})",
            refresh_palettes=True,
        )

    def _zone_delete_definition(self) -> None:
        zones = getattr(self.session.game_map, "zones", None) or {}
        if not zones:
            self.status.showMessage("Delete zone: none")
            return

        items = [f"{int(z.id)}: {z.name}" for z in sorted(zones.values(), key=lambda z: int(z.id))]
        item, ok = QInputDialog.getItem(self._as_editor(), "Delete Zone", "Zone:", items, 0, False)
        if not ok:
            return
        zid = self._parse_prefixed_int(str(item))
        if zid is None:
            return

        if not self._confirm("Delete Zone", f"Delete zone {int(zid)}?"):
            return

        ok, action = self._run_guarded("Delete Zone", lambda: self.session.delete_zone(zone_id=int(zid)))
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Delete zone: no changes",
            changed_message=f"Deleted zone: {int(zid)}",
            refresh_palettes=True,
        )

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

        ok, action = self._run_guarded(
            "Set Waypoint",
            lambda: self.session.set_waypoint(name=name, x=int(x), y=int(y), z=int(z)),
        )
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Set waypoint: no changes",
            changed_message=f"Set waypoint: {name} @ {int(x)},{int(y)},{int(z)}",
        )

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

        ok, action = self._run_guarded("Delete Waypoint", lambda: self.session.delete_waypoint(name=name))
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Delete waypoint: no changes",
            changed_message=f"Deleted waypoint: {name}",
        )

    def _switch_door_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        ok, action = self._run_guarded(
            "Switch Door",
            lambda: self.session.switch_door_at(x=int(x), y=int(y), z=int(z)),
        )
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Switch door: none at cursor",
            changed_message=f"Switched door @ {int(x)},{int(y)},{int(z)}",
        )

    def _house_set_id_on_selection(self) -> None:
        if not self.session.has_selection():
            self.status.showMessage("Set house id: nothing selected")
            return

        hid, ok = QInputDialog.getInt(self._as_editor(), "Set House ID", "House ID:", 1, 1, 2**31 - 1, 1)
        if not ok:
            return

        ok, action = self._run_guarded(
            "Set House ID",
            lambda: self.session.set_house_id_on_selection(house_id=int(hid)),
        )
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Set house id: no changes",
            changed_message=f"Set house id on selection: {int(hid)}",
        )

    def _house_clear_id_on_selection(self) -> None:
        if not self.session.has_selection():
            self.status.showMessage("Clear house id: nothing selected")
            return

        ok, action = self._run_guarded("Clear House ID", lambda: self.session.set_house_id_on_selection(house_id=None))
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Clear house id: no changes",
            changed_message="Cleared house id on selection",
        )

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
            parsed_townid = self._parse_prefixed_int(str(item))
            if parsed_townid is None:
                return
            townid = int(parsed_townid)
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

        ok, action = self._run_guarded(
            "Add/Edit House",
            lambda: self.session.upsert_house(
                house_id=int(hid),
                name=name,
                townid=int(townid),
                rent=int(rent),
                guildhall=bool(guildhall),
            ),
        )
        if not ok:
            return

        # If newly created and we chose cursor defaults, ensure entry is set.
        if before is None:
            with contextlib.suppress(Exception):
                self.session.set_house_entry(house_id=int(hid), x=int(entryx), y=int(entryy), z=int(entryz))

        self._apply_action_result(
            action=action,
            no_changes_message="Add/edit house: no changes",
            changed_message=f"House saved: {int(hid)} ({name})",
        )

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
        hid = self._parse_prefixed_int(str(item))
        if hid is None:
            return

        ok, action = self._run_guarded(
            "Set House Entry",
            lambda: self.session.set_house_entry(house_id=int(hid), x=int(x), y=int(y), z=int(z)),
        )
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Set house entry: no changes",
            changed_message=f"House entry set: {int(hid)} @ {int(x)},{int(y)},{int(z)}",
        )

    def _house_delete_definition(self) -> None:
        houses = getattr(self.session.game_map, "houses", None) or {}
        if not houses:
            self.status.showMessage("Delete house: none")
            return

        items = [f"{int(h.id)}: {h.name}" for h in sorted(houses.values(), key=lambda h: int(h.id))]
        item, ok = QInputDialog.getItem(self._as_editor(), "Delete House", "House:", items, 0, False)
        if not ok:
            return
        hid = self._parse_prefixed_int(str(item))
        if hid is None:
            return

        if not self._confirm("Delete House", f"Delete house {int(hid)} definition?"):
            return

        ok, action = self._run_guarded("Delete House", lambda: self.session.delete_house(house_id=int(hid)))
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Delete house: no changes",
            changed_message=f"Deleted house: {int(hid)}",
        )

    def _monster_spawn_set_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        radius, ok = QInputDialog.getInt(self._as_editor(), "Set Monster Spawn", "Radius:", 5, 1, 255, 1)
        if not ok:
            return

        ok, action = self._run_guarded(
            "Set Monster Spawn",
            lambda: self.session.set_monster_spawn_area(x=int(x), y=int(y), z=int(z), radius=int(radius)),
        )
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Set monster spawn: no changes",
            changed_message=f"Set monster spawn: {int(x)},{int(y)},{int(z)} r={int(radius)}",
        )

    def _monster_spawn_delete_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        if not self._confirm("Delete Monster Spawn", f"Delete monster spawn at {int(x)},{int(y)},{int(z)}?"):
            return

        ok, action = self._run_guarded(
            "Delete Monster Spawn",
            lambda: self.session.delete_monster_spawn_area(x=int(x), y=int(y), z=int(z)),
        )
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Delete monster spawn: none at cursor",
            changed_message=f"Deleted monster spawn: {int(x)},{int(y)},{int(z)}",
        )

    def _npc_spawn_set_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        radius, ok = QInputDialog.getInt(self._as_editor(), "Set NPC Spawn", "Radius:", 5, 1, 255, 1)
        if not ok:
            return

        ok, action = self._run_guarded(
            "Set NPC Spawn",
            lambda: self.session.set_npc_spawn_area(x=int(x), y=int(y), z=int(z), radius=int(radius)),
        )
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Set NPC spawn: no changes",
            changed_message=f"Set NPC spawn: {int(x)},{int(y)},{int(z)} r={int(radius)}",
        )

    def _npc_spawn_delete_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        if not self._confirm("Delete NPC Spawn", f"Delete NPC spawn at {int(x)},{int(y)},{int(z)}?"):
            return

        ok, action = self._run_guarded(
            "Delete NPC Spawn",
            lambda: self.session.delete_npc_spawn_area(x=int(x), y=int(y), z=int(z)),
        )
        if not ok:
            return

        self._apply_action_result(
            action=action,
            no_changes_message="Delete NPC spawn: none at cursor",
            changed_message=f"Deleted NPC spawn: {int(x)},{int(y)},{int(z)}",
        )

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

        ok, action = self._run_guarded(
            "Add Monster",
            lambda: self.session.add_monster_spawn_entry(
                x=int(x),
                y=int(y),
                z=int(z),
                name=name,
                spawntime=int(spawntime),
                weight=None if int(weight) == 0 else int(weight),
            ),
        )
        if not ok:
            return

        if action is None:
            self.status.showMessage("Add monster: no spawn area covers cursor")
        else:
            self.status.showMessage(f"Added monster: {name} @ {int(x)},{int(y)},{int(z)}")
            self.canvas.update()

    def _monster_spawn_delete_entry_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        names = self._collect_spawn_entry_names_at_cursor(
            self.session.game_map.monster_spawns,
            entries_attr="monsters",
            x=int(x),
            y=int(y),
            z=int(z),
        )

        if not names:
            self.status.showMessage("Delete monster: none at cursor")
            return

        choice, ok = QInputDialog.getItem(self._as_editor(), "Delete Monster", "Monster:", names, 0, False)
        if not ok:
            return
        choice = str(choice).strip()
        if not choice:
            return

        ok, action = self._run_guarded(
            "Delete Monster",
            lambda: self.session.delete_monster_spawn_entry_at_cursor(x=int(x), y=int(y), z=int(z), name=choice),
        )
        if not ok:
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

        ok, action = self._run_guarded(
            "Add NPC",
            lambda: self.session.add_npc_spawn_entry(
                x=int(x),
                y=int(y),
                z=int(z),
                name=name,
                spawntime=int(spawntime),
            ),
        )
        if not ok:
            return

        if action is None:
            self.status.showMessage("Add NPC: no spawn area covers cursor")
        else:
            self.status.showMessage(f"Added NPC: {name} @ {int(x)},{int(y)},{int(z)}")
            self.canvas.update()

    def _npc_spawn_delete_entry_here(self) -> None:
        x, y = getattr(self, "_last_hover_tile", (0, 0))
        z = int(getattr(self.viewport, "z", 7))

        names = self._collect_spawn_entry_names_at_cursor(
            self.session.game_map.npc_spawns,
            entries_attr="npcs",
            x=int(x),
            y=int(y),
            z=int(z),
        )

        if not names:
            self.status.showMessage("Delete NPC: none at cursor")
            return

        choice, ok = QInputDialog.getItem(self._as_editor(), "Delete NPC", "NPC:", names, 0, False)
        if not ok:
            return
        choice = str(choice).strip()
        if not choice:
            return

        ok, action = self._run_guarded(
            "Delete NPC",
            lambda: self.session.delete_npc_spawn_entry_at_cursor(x=int(x), y=int(y), z=int(z), name=choice),
        )
        if not ok:
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
