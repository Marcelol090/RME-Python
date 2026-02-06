"""
Reusable widgets for the Friends System UI.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QPixmap, QBrush, QPen
from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QFrame, QStyleOption
)

class CircularAvatar(QLabel):
    def __init__(self, size=40, parent=None):
        super().__init__(parent)
        self.size_px = size
        self.setFixedSize(size, size)
        self._pixmap = None

        # Default placeholder style
        self.setStyleSheet(f"background-color: #7289DA; border-radius: {size//2}px;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("?")

    def set_image(self, url_or_path):
        # In a real implementation, we would download the image asynchronously.
        # For this mock, we just use a colored placeholder with initials if provided
        # or load if it's a local path.
        if not url_or_path or url_or_path.startswith("http"):
            # Placeholder for remote images
            self.setText(url_or_path[0] if url_or_path else "?")
            return

        pixmap = QPixmap(url_or_path)
        if not pixmap.isNull():
            self.set_pixmap(pixmap)

    def set_pixmap(self, pixmap):
        # Scale and mask to circle
        scaled = pixmap.scaled(
            self.size_px, self.size_px,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        # Create circular mask
        result = QPixmap(self.size_px, self.size_px)
        result.fill(Qt.GlobalColor.transparent)

        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw circle clip
        path = QPainter.Path() # type: ignore
        # Actually simplest way is CompositionMode
        painter.setBrush(Qt.GlobalColor.black)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.size_px, self.size_px)

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.drawPixmap(0, 0, scaled)
        painter.end()

        self.setPixmap(result)
        self.setText("") # Clear placeholder text

class StatusIndicator(QWidget):
    def __init__(self, status='offline', parent=None):
        super().__init__(parent)
        self._status = status
        self.setFixedSize(12, 12)

    def set_status(self, status):
        self._status = status
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Discord-like colors
        colors = {
            'online': QColor(67, 181, 129),   # Green
            'idle': QColor(250, 166, 26),     # Yellow
            'dnd': QColor(240, 71, 71),       # Red
            'offline': QColor(116, 127, 141)  # Gray
        }

        color = colors.get(self._status, colors['offline'])

        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 10, 10) # Slightly smaller than widget size

class FriendItemWidget(QWidget):
    def __init__(self, friend_data, parent=None):
        super().__init__(parent)
        self.friend_data = friend_data
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Top Row: Avatar + Name + Status
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)

        self.avatar = CircularAvatar(size=32)
        self.avatar.set_image(self.friend_data.get('avatar_url'))

        name_container = QVBoxLayout()
        name_container.setSpacing(0)

        self.name_label = QLabel(self.friend_data.get('username', 'Unknown'))
        self.name_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #FFF;")

        name_container.addWidget(self.name_label)

        self.status_indicator = StatusIndicator(self.friend_data.get('status', 'offline'))

        top_row.addWidget(self.avatar)
        top_row.addLayout(name_container)
        top_row.addStretch()
        top_row.addWidget(self.status_indicator)

        layout.addLayout(top_row)

        # Activity Row
        current_map = self.friend_data.get('current_map')
        if current_map:
            activity_layout = QHBoxLayout()
            activity_layout.setContentsMargins(40, 0, 0, 0) # Indent under name

            icon = QLabel("📍")
            icon.setStyleSheet("font-size: 10px;")

            text = QLabel(f"Editing: {current_map}")
            text.setStyleSheet("color: #AAA; font-size: 10px;")

            activity_layout.addWidget(icon)
            activity_layout.addWidget(text)
            activity_layout.addStretch()

            if self.friend_data.get('privacy_mode') in ['public', 'friends_only']:
                view_btn = QPushButton("View")
                view_btn.setFixedSize(40, 18)
                view_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4F545C;
                        border: none;
                        border-radius: 3px;
                        color: white;
                        font-size: 9px;
                    }
                    QPushButton:hover { background-color: #686D73; }
                """)
                activity_layout.addWidget(view_btn)

            layout.addLayout(activity_layout)

        self.setLayout(layout)

        # Hover effect
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setStyleSheet("""
            FriendItemWidget {
                background-color: transparent;
                border-radius: 4px;
            }
            FriendItemWidget:hover {
                background-color: #36393F;
            }
        """)

    def update_data(self, new_data):
        self.friend_data.update(new_data)
        # Refresh UI
        self.status_indicator.set_status(self.friend_data.get('status', 'offline'))
        # Re-setup if structural changes (like map activity appearing/disappearing)
        # For simplicity, we might just recreate the widget in the parent list,
        # or implement granular updates here.

class FriendRequestWidget(QWidget):
    accepted = pyqtSignal(int)
    rejected = pyqtSignal(int)

    def __init__(self, request_data, parent=None):
        super().__init__(parent)
        self.request_data = request_data
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        avatar = CircularAvatar(24)
        avatar.set_image(self.request_data.get('requester_avatar'))

        name = QLabel(self.request_data.get('requester_name', 'Unknown'))
        name.setStyleSheet("color: #FFF; font-weight: bold;")

        accept_btn = QPushButton("✓")
        accept_btn.setFixedSize(24, 24)
        accept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        accept_btn.setStyleSheet("""
            QPushButton { background-color: #43B581; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #3CA374; }
        """)
        accept_btn.clicked.connect(lambda: self.accepted.emit(self.request_data['id']))

        reject_btn = QPushButton("✗")
        reject_btn.setFixedSize(24, 24)
        reject_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reject_btn.setStyleSheet("""
            QPushButton { background-color: #F04747; color: white; border-radius: 12px; border: none; }
            QPushButton:hover { background-color: #D84040; }
        """)
        reject_btn.clicked.connect(lambda: self.rejected.emit(self.request_data['id']))

        layout.addWidget(avatar)
        layout.addWidget(name)
        layout.addStretch()
        layout.addWidget(accept_btn)
        layout.addWidget(reject_btn)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #2F3136; border-radius: 4px;")
