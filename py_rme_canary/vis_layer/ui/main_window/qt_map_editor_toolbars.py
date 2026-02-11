from __future__ import annotations

from typing import TYPE_CHECKING, cast

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QButtonGroup, QCheckBox, QLabel, QPushButton, QSpinBox, QToolBar

from py_rme_canary.vis_layer.ui.main_window.build_menus import build_menus_and_toolbars
from py_rme_canary.vis_layer.ui.resources.icon_pack import load_icon
from py_rme_canary.vis_layer.ui.widgets.brush_toolbar import BrushToolbar, ToolSelector

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorToolbarsMixin:
    def _build_menus_and_toolbars(self) -> None:
        editor = cast("QtMapEditor", self)
        # Menus live in ui/main_window/build_menus.py
        build_menus_and_toolbars(editor)

        # ---- Toolbars (legacy set) ----
        editor.tb_standard = QToolBar("Standard", editor)
        editor.tb_standard.setMovable(False)
        editor.addToolBar(editor.tb_standard)
        editor.tb_standard.addAction(editor.act_new)
        editor.tb_standard.addAction(editor.act_open)
        editor.tb_standard.addAction(editor.act_save)
        editor.tb_standard.addAction(editor.act_save_as)
        editor.tb_standard.addSeparator()
        editor.tb_standard.addAction(editor.act_undo)
        editor.tb_standard.addAction(editor.act_redo)
        editor.tb_standard.addSeparator()
        editor.tb_standard.addAction(editor.act_cut)
        editor.tb_standard.addAction(editor.act_copy)
        editor.tb_standard.addAction(editor.act_paste)
        editor.tb_standard.addSeparator()
        editor.tb_standard.addAction(editor.act_zoom_in)
        editor.tb_standard.addAction(editor.act_zoom_out)
        editor.tb_standard.addAction(editor.act_zoom_normal)

        # ---- Modern Toolbars ----

        # 1. Tools (Left Sidebar typically)
        editor.tb_tools = QToolBar("Tools", editor)
        editor.tb_tools.setMovable(False)
        editor.addToolBar(Qt.ToolBarArea.LeftToolBarArea, editor.tb_tools)

        editor.tool_selector = ToolSelector(editor)
        editor.tool_selector.tool_changed.connect(lambda t: self._on_modern_tool_changed(editor, t))
        editor.tb_tools.addWidget(editor.tool_selector)

        # 2. Brush Settings (Quick Access)
        editor.tb_brush_quick = QToolBar("Brush Settings", editor)
        editor.tb_brush_quick.setMovable(False)
        editor.addToolBar(Qt.ToolBarArea.TopToolBarArea, editor.tb_brush_quick)

        editor.brush_toolbar = BrushToolbar(editor)
        editor.brush_toolbar.size_changed.connect(lambda s: editor._set_brush_size(s))
        editor.brush_toolbar.shape_changed.connect(lambda s: editor._set_brush_shape(s))
        editor.brush_toolbar.automagic_changed.connect(lambda b: editor.act_automagic.setChecked(b))

        # Sync automagic action back to toolbar
        editor.act_automagic.toggled.connect(lambda b: editor.brush_toolbar.set_automagic(b))

        editor.tb_brush_quick.addWidget(editor.brush_toolbar)

        # 3. Brush ID (Legacy support / Quick Entry)
        editor.tb_brushes = QToolBar("Brush ID", editor)
        editor.tb_brushes.setMovable(False)
        editor.addToolBar(editor.tb_brushes)

        editor.brush_id_entry = QSpinBox(editor)
        editor.brush_id_entry.setRange(0, 1000000)
        editor.brush_id_entry.setValue(4405)
        editor.brush_id_entry.setPrefix("ID: ")
        editor.brush_id_entry.valueChanged.connect(
            lambda _v: editor._set_selected_brush_id(editor.brush_id_entry.value())
        )
        editor.tb_brushes.addWidget(editor.brush_id_entry)

        editor.brush_label = QLabel("", editor)
        editor.brush_label.setStyleSheet("color: #a1a1aa; font-style: italic; margin-left: 8px;")
        editor.tb_brushes.addWidget(editor.brush_label)
        editor.tb_brushes.addSeparator()
        editor.tb_brushes.addAction(editor.act_toggle_mirror)

        # Dummy references for legacy mixin compatibility (QtMapEditorBrushesMixin)
        # These are no longer displayed but maintained to prevent AttributeErrors in legacy code
        editor.size_spin = QSpinBox(editor)
        editor.shape_square = QCheckBox(editor)
        editor.shape_circle = QCheckBox(editor)
        editor.automagic_cb = QCheckBox(editor)
        editor.variation_spin = QSpinBox(editor)
        editor.thickness_cb = QCheckBox(editor)
        editor.thickness_spin = QSpinBox(editor)

        m_toolbars = getattr(editor, "_menu_toolbars", None)

        editor.tb_position = QToolBar("Position", editor)
        editor.tb_position.setMovable(False)
        editor.addToolBar(editor.tb_position)
        editor.tb_position.addAction(editor.act_goto_previous_position)
        editor.tb_position.addSeparator()
        editor.cursor_pos_label = QLabel("Cursor: -,-,-", editor)
        editor.tb_position.addWidget(editor.cursor_pos_label)
        editor.tb_position.addSeparator()
        editor.tb_position.addWidget(QLabel("Go X:"))
        editor.goto_x_spin = QSpinBox(editor)
        editor.goto_x_spin.setRange(0, max(0, int(editor.map.header.width) - 1))
        editor.tb_position.addWidget(editor.goto_x_spin)
        editor.tb_position.addWidget(QLabel("Y:"))
        editor.goto_y_spin = QSpinBox(editor)
        editor.goto_y_spin.setRange(0, max(0, int(editor.map.header.height) - 1))
        editor.tb_position.addWidget(editor.goto_y_spin)
        editor.tb_position.addWidget(QLabel("Z:"))
        editor.z_spin = QSpinBox(editor)
        editor.z_spin.setRange(0, 15)
        editor.z_spin.setValue(editor.viewport.z)
        editor.z_spin.valueChanged.connect(lambda _v: editor._set_z(editor.z_spin.value()))
        editor.tb_position.addWidget(editor.z_spin)
        go_btn = QPushButton("Go", editor)
        go_btn.setIcon(load_icon("action_go_to"))
        go_btn.clicked.connect(editor._goto_position_from_fields)
        editor.tb_position.addWidget(go_btn)

        # UX: Enter on GoTo fields triggers the Go action.
        try:
            le = editor.goto_x_spin.lineEdit()
            if le is not None:
                le.returnPressed.connect(editor._goto_position_from_fields)
            le = editor.goto_y_spin.lineEdit()
            if le is not None:
                le.returnPressed.connect(editor._goto_position_from_fields)
            le = editor.z_spin.lineEdit()
            if le is not None:
                le.returnPressed.connect(editor._goto_position_from_fields)
        except Exception:
            pass

        editor.tb_indicators = QToolBar("Indicators", editor)
        editor.tb_indicators.setMovable(False)
        editor.addToolBar(editor.tb_indicators)

        editor.act_tb_hooks = QAction(load_icon("indicator_hooks"), "Wall Hooks", editor)
        editor.act_tb_hooks.setCheckable(True)
        editor.act_tb_pickupables = QAction(load_icon("indicator_pickupables"), "Pickupables", editor)
        editor.act_tb_pickupables.setCheckable(True)
        editor.act_tb_moveables = QAction(load_icon("indicator_moveables"), "Moveables", editor)
        editor.act_tb_moveables.setCheckable(True)
        editor.act_tb_avoidables = QAction(load_icon("indicator_avoidables"), "Avoidables", editor)
        editor.act_tb_avoidables.setCheckable(True)

        def _sync_toggle(source: QAction, target: QAction) -> None:
            def _apply(checked: bool) -> None:
                target.blockSignals(True)
                target.setChecked(bool(checked))
                target.blockSignals(False)

            source.toggled.connect(_apply)

        _sync_toggle(editor.act_tb_hooks, editor.act_show_wall_hooks)
        _sync_toggle(editor.act_show_wall_hooks, editor.act_tb_hooks)
        _sync_toggle(editor.act_tb_pickupables, editor.act_show_pickupables)
        _sync_toggle(editor.act_show_pickupables, editor.act_tb_pickupables)
        _sync_toggle(editor.act_tb_moveables, editor.act_show_moveables)
        _sync_toggle(editor.act_show_moveables, editor.act_tb_moveables)
        _sync_toggle(editor.act_tb_avoidables, editor.act_show_avoidables)
        _sync_toggle(editor.act_show_avoidables, editor.act_tb_avoidables)

        editor.act_tb_hooks.setChecked(bool(editor.act_show_wall_hooks.isChecked()))
        editor.act_tb_pickupables.setChecked(bool(editor.act_show_pickupables.isChecked()))
        editor.act_tb_moveables.setChecked(bool(editor.act_show_moveables.isChecked()))
        editor.act_tb_avoidables.setChecked(bool(editor.act_show_avoidables.isChecked()))

        editor.tb_indicators.addAction(editor.act_tb_hooks)
        editor.tb_indicators.addAction(editor.act_tb_pickupables)
        editor.tb_indicators.addAction(editor.act_tb_moveables)
        editor.tb_indicators.addAction(editor.act_tb_avoidables)

        # View -> Toolbars toggles
        editor.act_view_toolbar_brushes = QAction("Brush ID", editor)
        editor.act_view_toolbar_brushes.setCheckable(True)
        editor.act_view_toolbar_brushes.setChecked(True)
        editor.act_view_toolbar_position = QAction("Position", editor)
        editor.act_view_toolbar_position.setCheckable(True)
        editor.act_view_toolbar_position.setChecked(True)

        editor.act_view_toolbar_standard = QAction("Standard", editor)
        editor.act_view_toolbar_standard.setCheckable(True)
        editor.act_view_toolbar_standard.setChecked(True)

        editor.act_view_toolbar_indicators = QAction("Indicators", editor)
        editor.act_view_toolbar_indicators.setCheckable(True)
        editor.act_view_toolbar_indicators.setChecked(True)

        editor.act_view_toolbar_tools = QAction("Tools", editor)
        editor.act_view_toolbar_tools.setCheckable(True)
        editor.act_view_toolbar_tools.setChecked(True)

        editor.act_view_toolbar_brush_settings = QAction("Brush Settings", editor)
        editor.act_view_toolbar_brush_settings.setCheckable(True)
        editor.act_view_toolbar_brush_settings.setChecked(True)

        def _bind_toolbar_visibility(action: QAction, toolbar: QToolBar) -> None:
            action.toggled.connect(lambda visible: toolbar.setVisible(bool(visible)))

            def _update_action(visible: bool) -> None:
                action.blockSignals(True)
                action.setChecked(bool(visible))
                action.blockSignals(False)

            toolbar.visibilityChanged.connect(_update_action)
            action.setChecked(bool(toolbar.isVisible()))

        if m_toolbars is not None:
            m_toolbars.addAction(editor.act_view_toolbar_tools)
            m_toolbars.addAction(editor.act_view_toolbar_brush_settings)
            m_toolbars.addAction(editor.act_view_toolbar_standard)
            m_toolbars.addAction(editor.act_view_toolbar_position)
            m_toolbars.addAction(editor.act_view_toolbar_brushes)
            m_toolbars.addAction(editor.act_view_toolbar_indicators)

        _bind_toolbar_visibility(editor.act_view_toolbar_brushes, editor.tb_brushes)
        _bind_toolbar_visibility(editor.act_view_toolbar_position, editor.tb_position)
        _bind_toolbar_visibility(editor.act_view_toolbar_standard, editor.tb_standard)
        _bind_toolbar_visibility(editor.act_view_toolbar_indicators, editor.tb_indicators)
        _bind_toolbar_visibility(editor.act_view_toolbar_tools, editor.tb_tools)
        _bind_toolbar_visibility(editor.act_view_toolbar_brush_settings, editor.tb_brush_quick)

        # Keep mirror UI in sync with initial state
        editor._sync_mirror_actions()

        # Keep indicator UI in sync
        editor._sync_indicator_actions()

        # Keep selection UI in sync
        editor.act_selection_mode.setChecked(bool(editor.selection_mode))

    def _on_modern_tool_changed(self, editor: QtMapEditor, tool_id: str) -> None:
        """Handle modern tool selector changes."""
        if tool_id == "pointer":
            # Select/Move logic
            editor.act_selection_mode.setChecked(False) # Usually pointer is just navigation/single select
            editor.fill_armed = False
            editor.paste_armed = False
        elif tool_id == "pencil":
            # Standard draw
            editor.act_selection_mode.setChecked(False)
            editor.fill_armed = False
            editor.paste_armed = False
        elif tool_id == "select":
            # Selection mode (Box)
            editor.act_selection_mode.setChecked(True)
            editor.fill_armed = False
            editor.paste_armed = False
        elif tool_id == "fill":
            editor.act_fill.trigger()
        elif tool_id == "eraser":
            # Switch to eraser brush (usually ID 0 or specific)
            # For now, we can just ensure not in selection mode.
            # In RME, eraser is often a specific brush ID (0) or a mode.
            # Assuming brush 0 is eraser for now or just selecting it in logic.
            editor.act_selection_mode.setChecked(False)
            # If we have an eraser brush logic:
            # editor._set_selected_brush_id(0)
            pass
        elif tool_id == "picker":
            # Eyedropper
            editor.act_jump_to_brush.trigger()
