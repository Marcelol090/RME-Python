from __future__ import annotations

import os
from typing import TYPE_CHECKING, cast

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QCheckBox, QLabel, QPushButton, QSpinBox, QToolBar

from py_rme_canary.vis_layer.ui.main_window.build_menus import build_menus_and_toolbars

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

        editor.tb_brushes = QToolBar("Brushes", editor)
        editor.tb_brushes.setMovable(False)
        editor.addToolBar(editor.tb_brushes)
        editor.tb_brushes.addWidget(QLabel("Brush:"))
        editor.brush_id_entry = QSpinBox(editor)
        editor.brush_id_entry.setRange(0, 1000000)
        editor.brush_id_entry.setValue(4405)
        editor.brush_id_entry.valueChanged.connect(
            lambda _v: editor._set_selected_brush_id(editor.brush_id_entry.value())
        )
        editor.tb_brushes.addWidget(editor.brush_id_entry)
        editor.brush_label = QLabel("", editor)
        editor.tb_brushes.addWidget(editor.brush_label)
        editor.tb_brushes.addSeparator()
        editor.tb_brushes.addAction(editor.act_selection_mode)
        editor.tb_brushes.addAction(editor.act_toggle_mirror)

        editor.tb_sizes = QToolBar("Sizes", editor)
        editor.tb_sizes.setMovable(False)
        editor.addToolBar(editor.tb_sizes)
        editor.tb_sizes.addWidget(QLabel("Size:"))
        editor.size_spin = QSpinBox(editor)
        editor.size_spin.setRange(0, 15)
        editor.size_spin.setValue(0)
        editor.size_spin.valueChanged.connect(lambda _v: editor._set_brush_size(editor.size_spin.value()))

        # Populate Toolbars submenu now that toolbars exist.
        m_toolbars = getattr(editor, "_menu_toolbars", None)
        if m_toolbars is not None:
            try:
                m_toolbars.addAction(editor.tb_standard.toggleViewAction())
                m_toolbars.addAction(editor.tb_brushes.toggleViewAction())
                m_toolbars.addAction(editor.tb_position.toggleViewAction())
                m_toolbars.addAction(editor.tb_sizes.toggleViewAction())
            except Exception:
                pass

        editor.tb_sizes.addWidget(editor.size_spin)

        for idx, radius in enumerate((0, 1, 2, 4, 6, 8, 11), start=1):
            btn = QPushButton(str(idx), editor)
            btn.setFixedWidth(26)
            btn.clicked.connect(lambda _c=False, r=radius: editor._set_brush_size(r))
            editor.tb_sizes.addWidget(btn)

        editor.tb_sizes.addSeparator()
        editor.tb_sizes.addWidget(QLabel("Shape:"))
        editor.shape_square = QPushButton("square", editor)
        editor.shape_circle = QPushButton("circle", editor)
        editor.shape_square.setCheckable(True)
        editor.shape_circle.setCheckable(True)
        editor.shape_square.setChecked(True)
        editor.shape_square.clicked.connect(lambda: editor._set_brush_shape("square"))
        editor.shape_circle.clicked.connect(lambda: editor._set_brush_shape("circle"))
        editor.tb_sizes.addWidget(editor.shape_square)
        editor.tb_sizes.addWidget(editor.shape_circle)

        editor.tb_sizes.addSeparator()
        editor.automagic_cb = QCheckBox("Automagic", editor)
        editor.automagic_cb.setChecked(True)
        editor.automagic_cb.stateChanged.connect(lambda _s: editor.apply_ui_state_to_session())
        editor.tb_sizes.addWidget(editor.automagic_cb)

        # Sync menu action state with checkbox (best-effort).
        try:
            editor.act_automagic.setChecked(bool(editor.automagic_cb.isChecked()))

            def _sync_act_from_cb(_s: int) -> None:
                editor.act_automagic.blockSignals(True)
                editor.act_automagic.setChecked(bool(editor.automagic_cb.isChecked()))
                editor.act_automagic.blockSignals(False)

            editor.automagic_cb.stateChanged.connect(_sync_act_from_cb)
        except Exception:
            pass
        editor.tb_sizes.addSeparator()
        editor.tb_sizes.addAction(editor.act_fill)

        editor.tb_sizes.addSeparator()
        editor.tb_sizes.addWidget(QLabel("Var:"))
        editor.variation_spin = QSpinBox(editor)
        editor.variation_spin.setRange(0, 100)
        editor.variation_spin.setValue(int(getattr(editor, "brush_variation", 0) or 0))
        editor.variation_spin.valueChanged.connect(
            lambda _v: editor._set_brush_variation(editor.variation_spin.value())
        )
        editor.tb_sizes.addWidget(editor.variation_spin)

        editor.tb_sizes.addSeparator()
        editor.thickness_cb = QCheckBox("Thickness", editor)
        editor.thickness_cb.setChecked(bool(getattr(editor, "doodad_thickness_enabled", False)))
        editor.thickness_cb.stateChanged.connect(
            lambda _s: editor._set_doodad_thickness_enabled(bool(editor.thickness_cb.isChecked()))
        )
        editor.tb_sizes.addWidget(editor.thickness_cb)
        editor.tb_sizes.addWidget(QLabel("T:"))
        editor.thickness_spin = QSpinBox(editor)
        editor.thickness_spin.setRange(1, 10)
        editor.thickness_spin.setValue(int(getattr(editor, "doodad_thickness_level", 5) or 5))
        editor.thickness_spin.valueChanged.connect(
            lambda _v: editor._set_doodad_thickness_level(editor.thickness_spin.value())
        )
        editor.tb_sizes.addWidget(editor.thickness_spin)

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
        go_icon = os.path.join("icons", "position_go.png")
        if os.path.exists(go_icon):
            go_btn.setIcon(QIcon(go_icon))
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

        hooks_path = os.path.join("icons", "toolbar_hooks.png")
        pickup_path = os.path.join("icons", "toolbar_pickupables.png")
        move_path = os.path.join("icons", "toolbar_moveables.png")

        editor.act_tb_hooks = QAction(
            QIcon(hooks_path) if os.path.exists(hooks_path) else QIcon(), "Wall Hooks", editor
        )
        editor.act_tb_hooks.setCheckable(True)
        editor.act_tb_pickupables = QAction(
            QIcon(pickup_path) if os.path.exists(pickup_path) else QIcon(), "Pickupables", editor
        )
        editor.act_tb_pickupables.setCheckable(True)
        editor.act_tb_moveables = QAction(
            QIcon(move_path) if os.path.exists(move_path) else QIcon(), "Moveables", editor
        )
        editor.act_tb_moveables.setCheckable(True)
        editor.act_tb_avoidables = QAction("Avoidables", editor)
        editor.act_tb_avoidables.setCheckable(True)

        editor.act_tb_hooks.toggled.connect(editor.act_show_wall_hooks.setChecked)
        editor.act_tb_pickupables.toggled.connect(editor.act_show_pickupables.setChecked)
        editor.act_tb_moveables.toggled.connect(editor.act_show_moveables.setChecked)
        editor.act_tb_avoidables.toggled.connect(editor.act_show_avoidables.setChecked)

        editor.tb_indicators.addAction(editor.act_tb_hooks)
        editor.tb_indicators.addAction(editor.act_tb_pickupables)
        editor.tb_indicators.addAction(editor.act_tb_moveables)
        editor.tb_indicators.addAction(editor.act_tb_avoidables)

        # View -> Toolbars toggles
        editor.act_view_toolbar_brushes = QAction("Brushes", editor)
        editor.act_view_toolbar_brushes.setCheckable(True)
        editor.act_view_toolbar_brushes.setChecked(True)
        editor.act_view_toolbar_position = QAction("Position", editor)
        editor.act_view_toolbar_position.setCheckable(True)
        editor.act_view_toolbar_position.setChecked(True)
        editor.act_view_toolbar_sizes = QAction("Sizes", editor)
        editor.act_view_toolbar_sizes.setCheckable(True)
        editor.act_view_toolbar_sizes.setChecked(True)
        editor.act_view_toolbar_standard = QAction("Standard", editor)
        editor.act_view_toolbar_standard.setCheckable(True)
        editor.act_view_toolbar_standard.setChecked(True)

        editor.act_view_toolbar_indicators = QAction("Indicators", editor)
        editor.act_view_toolbar_indicators.setCheckable(True)
        editor.act_view_toolbar_indicators.setChecked(True)

        if m_toolbars is not None:
            m_toolbars.addAction(editor.act_view_toolbar_brushes)
            m_toolbars.addAction(editor.act_view_toolbar_position)
            m_toolbars.addAction(editor.act_view_toolbar_sizes)
            m_toolbars.addAction(editor.act_view_toolbar_standard)
            m_toolbars.addAction(editor.act_view_toolbar_indicators)

        editor.act_view_toolbar_brushes.toggled.connect(lambda v: editor.tb_brushes.setVisible(bool(v)))
        editor.act_view_toolbar_position.toggled.connect(lambda v: editor.tb_position.setVisible(bool(v)))
        editor.act_view_toolbar_sizes.toggled.connect(lambda v: editor.tb_sizes.setVisible(bool(v)))
        editor.act_view_toolbar_standard.toggled.connect(lambda v: editor.tb_standard.setVisible(bool(v)))
        editor.act_view_toolbar_indicators.toggled.connect(lambda v: editor.tb_indicators.setVisible(bool(v)))

        # Keep mirror UI in sync with initial state
        editor._sync_mirror_actions()

        # Keep indicator UI in sync
        editor._sync_indicator_actions()

        # Keep selection UI in sync
        editor.act_selection_mode.setChecked(bool(editor.selection_mode))
