from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget, QLabel, QSpinBox, QVBoxLayout, QWidget

from py_rme_canary.vis_layer.ui.docks.minimap import MinimapWidget

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


def build_docks(editor: QtMapEditor) -> None:
    # Modern Palette Dock
    from py_rme_canary.vis_layer.ui.docks.modern_palette_dock import ModernPaletteDock

    editor.dock_palette = ModernPaletteDock(editor, editor)
    editor.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, editor.dock_palette)

    # Backwards compatibility aliases expected by legacy mixins/actions.
    editor.dock_brushes = editor.dock_palette
    editor.palettes = editor.dock_palette
    editor.brush_filter = editor.dock_palette.brush_filter
    editor.brush_list = editor.dock_palette.brush_list

    # Minimap dock
    editor.dock_minimap = QDockWidget("Minimap", editor)
    editor.dock_minimap.setAllowedAreas(
        Qt.DockWidgetArea.LeftDockWidgetArea
        | Qt.DockWidgetArea.RightDockWidgetArea
        | Qt.DockWidgetArea.BottomDockWidgetArea
    )
    editor.minimap_widget = MinimapWidget(editor.dock_minimap, editor=editor)
    editor.dock_minimap.setWidget(editor.minimap_widget)
    editor.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, editor.dock_minimap)
    editor.dock_minimap.hide()
    editor.dock_minimap.visibilityChanged.connect(lambda v: editor._sync_dock_action(editor.act_window_minimap, v))
    editor.act_window_minimap.setChecked(False)

    # Actions history dock
    editor.dock_actions_history = editor.actions_history.build(title="Actions History")
    editor.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, editor.dock_actions_history)
    editor.dock_actions_history.hide()
    editor.dock_actions_history.visibilityChanged.connect(
        lambda v: editor._sync_dock_action(editor.act_window_actions_history, v)
    )
    editor.act_window_actions_history.setChecked(False)

    # Live Log dock
    from py_rme_canary.vis_layer.ui.docks.live_log_panel import LiveLogPanel

    editor.dock_live_log = LiveLogPanel(editor)
    editor.dock_live_log.message_sent.connect(lambda msg: editor.session.send_live_chat(msg))
    editor.dock_live_log.set_input_enabled(False)
    editor.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, editor.dock_live_log)
    editor.dock_live_log.hide()
    editor.dock_live_log.visibilityChanged.connect(lambda v: editor._sync_dock_action(editor.act_window_live_log, v))
    editor.act_window_live_log.setChecked(False)

    # Friends dock
    from py_rme_canary.vis_layer.ui.docks.friends_sidebar import FriendsDock

    friends_widget = FriendsDock(editor)
    editor.friends_sidebar = friends_widget.sidebar
    editor.dock_friends = QDockWidget("Friends", editor)
    editor.dock_friends.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
    editor.dock_friends.setWidget(friends_widget)
    editor.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, editor.dock_friends)
    editor.dock_friends.hide()
    editor.dock_friends.visibilityChanged.connect(lambda v: editor._sync_dock_action(editor.act_window_friends, v))
    editor.act_window_friends.setChecked(False)

    # Modern Assets & Sprite Preview dock
    from py_rme_canary.vis_layer.ui.docks.assets_dock import ModernAssetsDock

    asset_dock = ModernAssetsDock(editor, editor)
    editor.dock_sprite_preview = asset_dock
    asset_dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

    editor.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, asset_dock)

    # Bind widgets for legacy compatibility (QtMapEditorAssetsMixin expects these)
    editor.sprite_id_spin = asset_dock.sprite_id_spin
    editor.sprite_preview = asset_dock.preview_lbl

    asset_dock.visibilityChanged.connect(lambda v: editor._sync_dock_action(editor.act_show_preview, v))
    asset_dock.setVisible(bool(getattr(editor, "show_preview", True)))
