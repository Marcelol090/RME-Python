"""
Friends System Dock Widget.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDockWidget

from py_rme_canary.vis_layer.ui.friends.sidebar import FriendsSidebar
from py_rme_canary.logic_layer.friends_client import FriendsClient

class FriendsDock(QDockWidget):
    def __init__(self, client: FriendsClient, parent=None):
        super().__init__("Friends", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

        self.sidebar = FriendsSidebar(client, self)
        self.setWidget(self.sidebar)

        # Default styling
        self.setStyleSheet("""
            QDockWidget::title {
                background: #202225;
                color: #FFF;
                padding: 5px;
            }
        """)
