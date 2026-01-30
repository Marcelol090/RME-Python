from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QElapsedTimer, QPoint, QRect, Qt, QTimer
from PyQt6.QtGui import QColor, QPainter, QPen, QPolygon
from PyQt6.QtWidgets import QMessageBox, QWidget

from py_rme_canary.logic_layer.lasso_selection import get_lasso_tool
from py_rme_canary.logic_layer.mirroring import union_with_mirrored
from py_rme_canary.logic_layer.session.selection import SelectionApplyMode
from py_rme_canary.vis_layer.renderer.qpainter_backend import QPainterRenderBackend

from ..helpers import iter_brush_border_offsets, iter_brush_offsets, qcolor_from_id

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class MapCanvasWidget(QWidget):
    HARD_REFRESH_RATE_MS = 16
    ANIMATION_INTERVAL_MS = 100

    def __init__(self, parent: QWidget | None, editor: QtMapEditor) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)

        self._editor = editor
        self._mouse_down = False
        self._panning = False
        self._pan_anchor: tuple[QPoint, int, int] | None = None
        self._is_rendering = False
        self._render_pending = False
        self._pending_zoom_step = 0
        self._refresh_watch = QElapsedTimer()
        self._refresh_watch.start()
        self._animation_timer = QTimer(self)
        self._animation_timer.setInterval(self.ANIMATION_INTERVAL_MS)
        self._animation_timer.timeout.connect(self._on_animation_tick)
        self._sync_animation_timer()

        # Selection drag-to-move (legacy-like)
        self._selection_dragging = False
        self._selection_drag_start: tuple[int, int, int] | None = None

        # Selection box apply mode (captured on press)
        self._selection_box_mode: SelectionApplyMode | None = None
        self._lasso_active = False
        self._lasso_apply_mode: SelectionApplyMode | None = None

        # Hover tracking for tooltips (synced into MapDrawer)
        self._hover_tile: tuple[int, int, int] | None = None
        self._hover_stack: list[int] = []

    def sizeHint(self):  # noqa: N802 (Qt style)
        return super().sizeHint()

    # ---------- helpers ----------

    def update(self, *args: object, **kwargs: object) -> None:
        self.request_render()

    def request_render(self) -> None:
        self._sync_animation_timer()
        if self._is_rendering:
            self._render_pending = True
            return
        if self._refresh_watch.isValid() and self._refresh_watch.elapsed() > self.HARD_REFRESH_RATE_MS:
            self._refresh_watch.restart()
            self.repaint()
        QWidget.update(self)

    def _sync_animation_timer(self) -> None:
        enabled = bool(getattr(self._editor, "show_preview", False))
        if enabled and not self._animation_timer.isActive():
            self._animation_timer.start()
        elif not enabled and self._animation_timer.isActive():
            self._animation_timer.stop()

    def _on_animation_tick(self) -> None:
        if not bool(getattr(self._editor, "show_preview", False)):
            return
        if hasattr(self._editor, "advance_animation_clock"):
            self._editor.advance_animation_clock(self.ANIMATION_INTERVAL_MS)
        tile_px = int(getattr(self._editor.viewport, "tile_px", 32))
        zoom = 32.0 / float(tile_px) if tile_px > 0 else 1.0
        if zoom <= 2.0:
            self.request_render()

    def _apply_pending_inputs(self) -> None:
        if self._pending_zoom_step == 0:
            return
        vp = self._editor.viewport
        new_tile_px = int(max(6, min(64, int(vp.tile_px) + int(self._pending_zoom_step))))
        vp.tile_px = new_tile_px
        self._pending_zoom_step = 0

    def _tile_at(self, px: int, py: int) -> tuple[int, int]:
        vp = self._editor.viewport
        tx = vp.origin_x + (int(px) // vp.tile_px)
        ty = vp.origin_y + (int(py) // vp.tile_px)
        return int(tx), int(ty)

    def _visible_bounds(self) -> tuple[int, int, int, int]:
        vp = self._editor.viewport
        cols = max(1, self.width() // vp.tile_px)
        rows = max(1, self.height() // vp.tile_px)
        x0 = vp.origin_x
        y0 = vp.origin_y
        x1 = min(self._editor.map.header.width, x0 + cols + 1)
        y1 = min(self._editor.map.header.height, y0 + rows + 1)
        return x0, y0, x1, y1

    def _server_ids_for_tile_stack(self, x: int, y: int, z: int) -> list[int]:
        t = self._editor.map.get_tile(int(x), int(y), int(z))
        if t is None:
            return []
        out: list[int] = []
        if t.ground is not None:
            out.append(int(t.ground.id))
        if t.items:
            out.extend(int(it.id) for it in t.items)
        return out

    def _server_id_for_tile(self, x: int, y: int, z: int) -> int | None:
        t = self._editor.map.get_tile(int(x), int(y), int(z))
        if t is None:
            return None
        if t.items:
            return int(t.items[-1].id)
        if t.ground is not None:
            return int(t.ground.id)
        return None

    def _open_context_menu_at(self, pos: QPoint) -> None:
        editor = self._editor
        x, y = self._tile_at(int(pos.x()), int(pos.y()))
        z = int(editor.viewport.z)
        try:
            tile = editor.map.get_tile(int(x), int(y), int(z))
        except Exception:
            tile = None
        if tile is None:
            return

        item = tile.items[-1] if getattr(tile, "items", None) else None
        if item is None:
            item = getattr(tile, "ground", None)
        if item is None:
            return

        try:
            from py_rme_canary.vis_layer.ui.menus.context_menus import ItemContextMenu

            menu = ItemContextMenu(self)

            def _set_find() -> None:
                editor._set_quick_replace_source(int(item.id))

            def _set_replace() -> None:
                editor._set_quick_replace_target(int(item.id))

            def _find_all() -> None:
                editor._find_item_by_id(int(item.id))

            def _replace_all() -> None:
                editor._set_quick_replace_source(int(item.id))
                editor._open_replace_items_dialog()

            menu.set_callbacks(
                {
                    "set_find": _set_find,
                    "set_replace": _set_replace,
                    "find_all": _find_all,
                    "replace_all": _replace_all,
                }
            )
            menu.show_for_item(item, tile)
        except Exception:
            return

    def _paint_footprint_at(self, px: int, py: int, *, alt: bool = False) -> None:
        editor = self._editor
        x, y = self._tile_at(px, py)
        z = editor.viewport.z
        if not (0 <= x < editor.map.header.width and 0 <= y < editor.map.header.height):
            return

        def _dedupe_positions(positions: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
            seen: set[tuple[int, int, int]] = set()
            out: list[tuple[int, int, int]] = []
            for px, py, pz in positions:
                key = (int(px), int(py), int(pz))
                if key in seen:
                    continue
                seen.add(key)
                out.append(key)
            return out

        def _union_with_mirror(positions: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
            if not getattr(editor, "mirror_enabled", False) or not editor.has_mirror_axis():
                return _dedupe_positions(positions)
            axis = str(getattr(editor, "mirror_axis", "x")).lower()
            v = int(editor.get_mirror_axis_value())
            return union_with_mirrored(
                positions,
                axis=axis,
                axis_value=int(v),
                width=int(editor.map.header.width),
                height=int(editor.map.header.height),
            )

        # Mark legacy `tilestoborder` ring.
        border_positions: list[tuple[int, int, int]] = []
        for dx, dy in iter_brush_border_offsets(editor.brush_size, editor.brush_shape):
            tx = int(x + dx)
            ty = int(y + dy)
            if 0 <= tx < editor.map.header.width and 0 <= ty < editor.map.header.height:
                border_positions.append((tx, ty, int(z)))

        for tx, ty, _tz in _union_with_mirror(border_positions):
            editor.session.mark_autoborder_position(x=int(tx), y=int(ty), z=int(z))

        draw_positions: list[tuple[int, int, int]] = []
        for dx, dy in iter_brush_offsets(editor.brush_size, editor.brush_shape):
            tx = int(x + dx)
            ty = int(y + dy)
            if 0 <= tx < editor.map.header.width and 0 <= ty < editor.map.header.height:
                draw_positions.append((tx, ty, int(z)))

        for tx, ty, _tz in _union_with_mirror(draw_positions):
            editor.session.mouse_move(x=int(tx), y=int(ty), z=int(z), alt=bool(alt))

    def _draw_with_map_drawer(self, painter: QPainter) -> bool:
        editor = self._editor
        drawer = getattr(editor, "map_drawer", None)
        if drawer is None or not hasattr(editor, "drawing_options_coordinator"):
            return False

        # Sync current UI toggles into DrawingOptions.
        editor.drawing_options_coordinator.sync_from_editor()

        drawer.game_map = editor.map
        drawer.viewport.origin_x = int(editor.viewport.origin_x)
        drawer.viewport.origin_y = int(editor.viewport.origin_y)
        drawer.viewport.z = int(editor.viewport.z)
        drawer.viewport.tile_px = int(editor.viewport.tile_px)
        drawer.viewport.width_px = int(self.width())
        drawer.viewport.height_px = int(self.height())
        self._sync_hover_to_drawer(drawer)
        try:
            drawer.set_live_cursors(editor.session.get_live_cursor_overlays())
        except Exception:
            pass

        backend = QPainterRenderBackend(
            painter,
            target_rect=self.rect(),
            sprite_lookup=lambda sid, size: editor._sprite_pixmap_for_server_id(int(sid), tile_px=int(size)),
            indicator_lookup=editor.indicators.icon,
        )
        drawer.draw(backend)
        return True

    # ---------- Qt events ----------

    def paintEvent(self, _event):  # noqa: N802
        self._is_rendering = True
        self._apply_pending_inputs()
        editor = self._editor
        vp = editor.viewport

        p = QPainter(self)

        x0, y0, x1, y1 = self._visible_bounds()
        s = vp.tile_px
        z = vp.z

        use_map_drawer = self._draw_with_map_drawer(p)
        if not use_map_drawer:
            p.fillRect(self.rect(), QColor(30, 30, 30))

            grid_pen = QPen(QColor(58, 58, 58))
            if getattr(editor, "show_grid", True):
                p.setPen(grid_pen)

            for y in range(y0, y1):
                py0 = (y - y0) * s
                for x in range(x0, x1):
                    px0 = (x - x0) * s
                    rect = QRect(px0, py0, s, s)

                    t = self._editor.map.get_tile(int(x), int(y), int(z))
                    if t is None or (
                        getattr(editor, "only_show_modified", False) and not bool(getattr(t, "modified", False))
                    ):
                        stack = []
                    else:
                        stack = []
                        if t.ground is not None:
                            stack.append(int(t.ground.id))
                        if t.items:
                            stack.extend(int(it.id) for it in t.items)
                    if not stack:
                        p.fillRect(rect, QColor(43, 43, 43))
                    else:
                        p.fillRect(rect, qcolor_from_id(int(stack[-1])))

                    # Legacy-style "Show as minimap": only draw the top-color grid, skip sprites.
                    if not getattr(editor, "show_as_minimap", False):
                        max_draw = 32
                        for sid in stack[:max_draw]:
                            pm = editor._sprite_pixmap_for_server_id(int(sid), tile_px=s)
                            if pm is not None and not pm.isNull():
                                p.drawPixmap(px0, py0, pm)

                    if getattr(editor, "show_grid", True):
                        p.drawRect(rect)

                    # --- Indicators overlay (legacy-inspired) ---
                    if (
                        getattr(editor, "show_wall_hooks", False)
                        or getattr(editor, "show_pickupables", False)
                        or getattr(editor, "show_moveables", False)
                        or getattr(editor, "show_avoidables", False)
                    ):
                        editor.indicators.ensure_loaded()
                        props = editor.indicators.item_props

                        any_hook = False
                        any_pick = False
                        any_move = False
                        any_avoid = False
                        for sid in stack:
                            it = props.get(int(sid))
                            if it is None:
                                continue
                            if editor.show_wall_hooks and it.hook:
                                any_hook = True
                            if editor.show_pickupables and it.pickupable:
                                any_pick = True
                            if editor.show_moveables and it.moveable:
                                any_move = True
                            if editor.show_avoidables and it.avoidable:
                                any_avoid = True

                        icon_size = max(8, min(12, s // 2))
                        cx = px0 + 2
                        cy = py0 + 2
                        if any_hook:
                            pm = editor.indicators.icon("hooks", icon_size)
                            if pm is not None:
                                p.drawPixmap(cx, cy, pm)
                                cx += icon_size + 1
                        if any_pick:
                            pm = editor.indicators.icon("pickupables", icon_size)
                            if pm is not None:
                                p.drawPixmap(cx, cy, pm)
                                cx += icon_size + 1
                        if any_move:
                            pm = editor.indicators.icon("moveables", icon_size)
                            if pm is not None:
                                p.drawPixmap(cx, cy, pm)
                                cx += icon_size + 1
                        if any_avoid:
                            p.setPen(QPen(QColor(255, 60, 60)))
                            p.drawText(
                                QRect(px0 + 2, py0 + 2, s - 4, s - 4),
                                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
                                "A",
                            )
                            if getattr(editor, "show_grid", True):
                                p.setPen(grid_pen)
        elif (
            getattr(editor, "show_wall_hooks", False)
            or getattr(editor, "show_pickupables", False)
            or getattr(editor, "show_moveables", False)
            or getattr(editor, "show_avoidables", False)
        ):
            editor.indicators.ensure_loaded()
            props = editor.indicators.item_props
            for y in range(y0, y1):
                py0 = (y - y0) * s
                for x in range(x0, x1):
                    px0 = (x - x0) * s
                    t = self._editor.map.get_tile(int(x), int(y), int(z))
                    if t is None or (
                        getattr(editor, "only_show_modified", False) and not bool(getattr(t, "modified", False))
                    ):
                        continue
                    stack: list[int] = []
                    if t.ground is not None:
                        stack.append(int(t.ground.id))
                    if t.items:
                        stack.extend(int(it.id) for it in t.items)
                    if not stack:
                        continue

                    any_hook = False
                    any_pick = False
                    any_move = False
                    any_avoid = False
                    for sid in stack:
                        it = props.get(int(sid))
                        if it is None:
                            continue
                        if editor.show_wall_hooks and it.hook:
                            any_hook = True
                        if editor.show_pickupables and it.pickupable:
                            any_pick = True
                        if editor.show_moveables and it.moveable:
                            any_move = True
                        if editor.show_avoidables and it.avoidable:
                            any_avoid = True

                    icon_size = max(8, min(12, s // 2))
                    cx = px0 + 2
                    cy = py0 + 2
                    if any_hook:
                        pm = editor.indicators.icon("hooks", icon_size)
                        if pm is not None:
                            p.drawPixmap(cx, cy, pm)
                            cx += icon_size + 1
                    if any_pick:
                        pm = editor.indicators.icon("pickupables", icon_size)
                        if pm is not None:
                            p.drawPixmap(cx, cy, pm)
                            cx += icon_size + 1
                    if any_move:
                        pm = editor.indicators.icon("moveables", icon_size)
                        if pm is not None:
                            p.drawPixmap(cx, cy, pm)
                            cx += icon_size + 1
                    if any_avoid:
                        p.setPen(QPen(QColor(255, 60, 60)))
                        p.drawText(
                            QRect(px0 + 2, py0 + 2, s - 4, s - 4),
                            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
                            "A",
                        )

        # --- Selection overlay (legacy-inspired) ---
        sel_pen = QPen(QColor(230, 230, 230))
        sel_pen.setWidth(2)
        p.setPen(sel_pen)

        selected = editor.session.get_selection_tiles()
        for sx, sy, sz in selected:
            if int(sz) != int(z):
                continue
            if not (x0 <= int(sx) < x1 and y0 <= int(sy) < y1):
                continue
            px0 = (int(sx) - x0) * s
            py0 = (int(sy) - y0) * s
            p.drawRect(QRect(px0, py0, s, s))

        box = editor.session.get_selection_box()
        if box is not None:
            (ax, ay, az), (bx, by, _bz) = box
            if int(az) == int(z):
                rx0, rx1 = (int(ax), int(bx)) if ax <= bx else (int(bx), int(ax))
                ry0, ry1 = (int(ay), int(by)) if ay <= by else (int(by), int(ay))
                px0 = (rx0 - x0) * s
                py0 = (ry0 - y0) * s
                pw = (rx1 - rx0 + 1) * s
                ph = (ry1 - ry0 + 1) * s
                dash_pen = QPen(QColor(200, 200, 200))
                dash_pen.setStyle(Qt.PenStyle.DashLine)
                dash_pen.setWidth(2)
                p.setPen(dash_pen)
                p.drawRect(QRect(px0, py0, pw, ph))

        if self._lasso_active:
            tool = get_lasso_tool()
            if len(tool.points) >= 2:
                lasso_pen = QPen(QColor(255, 200, 0))
                lasso_pen.setStyle(Qt.PenStyle.DashLine)
                lasso_pen.setWidth(2)
                p.setPen(lasso_pen)
                pts = QPolygon()
                for lx, ly in tool.points:
                    px = (int(lx) - x0) * s + (s // 2)
                    py = (int(ly) - y0) * s + (s // 2)
                    pts.append(QPoint(int(px), int(py)))
                if pts:
                    p.drawPolyline(pts)

        p.end()
        self._is_rendering = False
        if self._render_pending:
            self._render_pending = False
            QTimer.singleShot(0, self.request_render)

    def mousePressEvent(self, event):  # noqa: N802
        editor = self._editor

        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = True
            self._pan_anchor = (event.position().toPoint(), editor.viewport.origin_x, editor.viewport.origin_y)
            event.accept()
            return

        if event.button() == Qt.MouseButton.RightButton:
            self._open_context_menu_at(event.position().toPoint())
            event.accept()
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        editor.apply_ui_state_to_session()

        # Paste (legacy-like Ctrl+V then click to paste)
        if getattr(editor, "paste_armed", False):
            editor.paste_armed = False
            x, y = self._tile_at(int(event.position().x()), int(event.position().y()))
            z = editor.viewport.z
            if not (0 <= x < editor.map.header.width and 0 <= y < editor.map.header.height):
                return
            try:
                editor.session.paste_buffer(x=x, y=y, z=z)
            except Exception as e:
                QMessageBox.critical(self, "Paste", str(e))
                return

            if getattr(editor, "selection_mode", False):
                self._mouse_down = True
                self._selection_dragging = True
                self._selection_drag_start = (int(x), int(y), int(z))

            self.update()
            editor._update_action_enabled_states()
            return

        # Selection mode (legacy-like Shift box selection)
        if getattr(editor, "selection_mode", False):
            self._mouse_down = True
            x, y = self._tile_at(int(event.position().x()), int(event.position().y()))
            z = editor.viewport.z
            if not (0 <= x < editor.map.header.width and 0 <= y < editor.map.header.height):
                self._mouse_down = False
                return

            mods = event.modifiers()
            shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
            ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
            alt = bool(mods & Qt.KeyboardModifier.AltModifier)

            if bool(getattr(editor, "lasso_enabled", False)) and shift:
                mode: SelectionApplyMode
                if ctrl and alt:
                    mode = SelectionApplyMode.TOGGLE
                elif alt:
                    mode = SelectionApplyMode.SUBTRACT
                elif ctrl:
                    mode = SelectionApplyMode.ADD
                else:
                    mode = SelectionApplyMode.REPLACE

                tool = get_lasso_tool()
                tool.start(int(x), int(y), int(z))
                self._lasso_active = True
                self._lasso_apply_mode = mode
                self.request_render()
                return

            selected = editor.session.get_selection_tiles()
            if (not shift) and (not ctrl) and ((int(x), int(y), int(z)) in selected):
                self._selection_dragging = True
                self._selection_drag_start = (int(x), int(y), int(z))
                self.update()
                return

            if shift:
                # Legacy-ish selection modes:
                # - Shift: replace selection with box
                # - Shift+Ctrl: add box
                # - Shift+Alt: subtract box
                # - Shift+Ctrl+Alt: toggle box
                if ctrl and alt:
                    self._selection_box_mode = SelectionApplyMode.TOGGLE
                elif alt:
                    self._selection_box_mode = SelectionApplyMode.SUBTRACT
                elif ctrl:
                    self._selection_box_mode = SelectionApplyMode.ADD
                else:
                    self._selection_box_mode = SelectionApplyMode.REPLACE
                    editor.session.clear_selection()
                editor.session.begin_box_selection(x=x, y=y, z=z)
            elif ctrl:
                editor.session.toggle_select_tile(x=x, y=y, z=z)
            elif alt:
                # Subtract single tile
                selected = editor.session.get_selection_tiles()
                if (int(x), int(y), int(z)) in selected:
                    editor.session.toggle_select_tile(x=x, y=y, z=z)
            else:
                editor.session.set_single_selection(x=x, y=y, z=z)
            self.update()
            editor._update_action_enabled_states()
            return

        # One-shot fill (legacy Ctrl+D): fill ground and do not start a stroke.
        if editor.fill_armed:
            editor.fill_armed = False
            x, y = self._tile_at(int(event.position().x()), int(event.position().y()))
            z = editor.viewport.z
            try:
                editor.session.fill_ground(x=x, y=y, z=z)
            except Exception as e:
                QMessageBox.critical(self, "Fill", str(e))
            self.update()
            editor._update_action_enabled_states()
            return

        self._mouse_down = True

        x, y = self._tile_at(int(event.position().x()), int(event.position().y()))
        z = editor.viewport.z
        if not (0 <= x < editor.map.header.width and 0 <= y < editor.map.header.height):
            self._mouse_down = False
            return

        try:
            alt = bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
            editor.session.mouse_down(x=x, y=y, z=z, alt=alt)
            self._paint_footprint_at(int(event.position().x()), int(event.position().y()), alt=alt)
        except Exception as e:
            QMessageBox.critical(self, "Paint", str(e))
            self._mouse_down = False

    def mouseMoveEvent(self, event):  # noqa: N802
        editor = self._editor

        if self._panning and self._pan_anchor is not None:
            anchor_pt, ox, oy = self._pan_anchor
            cur = event.position().toPoint()
            dx_px = int(cur.x() - anchor_pt.x())
            dy_px = int(cur.y() - anchor_pt.y())
            dx_tiles = -dx_px // editor.viewport.tile_px
            dy_tiles = -dy_px // editor.viewport.tile_px
            editor.viewport.origin_x = max(0, int(ox + dx_tiles))
            editor.viewport.origin_y = max(0, int(oy + dy_tiles))
            self.request_render()
            editor.update_status_from_mouse(int(event.position().x()), int(event.position().y()))
            return

        if self._lasso_active:
            x, y = self._tile_at(int(event.position().x()), int(event.position().y()))
            tool = get_lasso_tool()
            if tool.add_point(int(x), int(y)):
                self.request_render()
            editor.update_status_from_mouse(int(event.position().x()), int(event.position().y()))
            self._set_hover_from_pos(int(event.position().x()), int(event.position().y()))
            return

        if getattr(editor, "selection_mode", False) and self._mouse_down:
            if self._selection_dragging and self._selection_drag_start is not None:
                editor.update_status_from_mouse(int(event.position().x()), int(event.position().y()))
                self._set_hover_from_pos(int(event.position().x()), int(event.position().y()))
                return
            box = editor.session.get_selection_box()
            if box is not None:
                x, y = self._tile_at(int(event.position().x()), int(event.position().y()))
                z = editor.viewport.z
                editor.session.update_box_selection(x=x, y=y, z=z)
                self.request_render()
            editor.update_status_from_mouse(int(event.position().x()), int(event.position().y()))
            self._set_hover_from_pos(int(event.position().x()), int(event.position().y()))
            return

        if self._mouse_down:
            alt = bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
            self._paint_footprint_at(int(event.position().x()), int(event.position().y()), alt=alt)

        editor.update_status_from_mouse(int(event.position().x()), int(event.position().y()))
        self._set_hover_from_pos(int(event.position().x()), int(event.position().y()))

    def mouseReleaseEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.MiddleButton:
            self._panning = False
            self._pan_anchor = None
            event.accept()
            return

        if event.button() != Qt.MouseButton.LeftButton:
            return

        if not self._mouse_down:
            return

        self._mouse_down = False

        editor = self._editor
        if self._lasso_active:
            tool = get_lasso_tool()
            tiles = tool.finish()
            self._lasso_active = False
            editor.session.apply_lasso_selection(
                tiles=tiles,
                mode=self._lasso_apply_mode,
                visible_floors=editor._visible_floors_for_selection(),
            )
            self._lasso_apply_mode = None
            self.request_render()
            editor._update_action_enabled_states()
            return

        if getattr(editor, "selection_mode", False):
            mods = event.modifiers()
            ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)

            if self._selection_dragging and self._selection_drag_start is not None:
                x, y = self._tile_at(int(event.position().x()), int(event.position().y()))
                z = editor.viewport.z
                sx, sy, sz = self._selection_drag_start
                move_x = int(sx - x)
                move_y = int(sy - y)
                move_z = int(sz - z)
                editor.session.move_selection(move_x=move_x, move_y=move_y, move_z=move_z)
                self._selection_dragging = False
                self._selection_drag_start = None
                self.request_render()
                editor._update_action_enabled_states()
                return

            if editor.session.get_selection_box() is not None:
                editor.session.finish_box_selection(
                    toggle_if_single=bool(ctrl),
                    mode=self._selection_box_mode,
                    visible_floors=editor._visible_floors_for_selection(),
                )
            editor.session.cancel_box_selection()
            self._selection_box_mode = None
            self._selection_dragging = False
            self._selection_drag_start = None
            self.request_render()
            editor._update_action_enabled_states()
            return

        editor.session.mouse_up()

    def cancel_interaction(self) -> None:
        self._mouse_down = False
        self._panning = False
        self._pan_anchor = None
        self._selection_dragging = False
        self._selection_drag_start = None
        self._hover_tile = None
        self._hover_stack = []
        self.cancel_lasso()
        self.request_render()

    def cancel_lasso(self) -> None:
        self._lasso_active = False
        self._lasso_apply_mode = None
        try:
            get_lasso_tool().cancel()
        except Exception:
            pass

    def _set_hover_from_pos(self, px: int, py: int) -> None:
        """Capture hover tile for MapDrawer tooltips."""
        editor = self._editor
        x, y = self._tile_at(int(px), int(py))
        z = int(editor.viewport.z)
        if not (0 <= x < editor.map.header.width and 0 <= y < editor.map.header.height):
            self._hover_tile = None
            self._hover_stack = []
            return
        stack = self._server_ids_for_tile_stack(int(x), int(y), z)
        self._hover_tile = (int(x), int(y), z)
        self._hover_stack = stack

    def _sync_hover_to_drawer(self, drawer) -> None:
        """Push current hover tile/stack into MapDrawer before drawing."""
        try:
            pos = self.mapFromGlobal(self.cursor().pos())
            self._set_hover_from_pos(int(pos.x()), int(pos.y()))
        except Exception:
            pass
        if self._hover_tile is None:
            return
        hx, hy, hz = self._hover_tile
        drawer.set_hover_tile(hx, hy, hz, list(self._hover_stack))

    def wheelEvent(self, event):  # noqa: N802
        delta = event.angleDelta().y()
        if delta == 0:
            return
        step = 2 if delta > 0 else -2
        self._pending_zoom_step += int(step)
        self.request_render()
