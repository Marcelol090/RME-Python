from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class SimpleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Initial", self)
        self.button = QPushButton("Click Me", self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.button)

        self.button.clicked.connect(self.on_click)

    def on_click(self):
        self.label.setText("Clicked")


def test_button_click(qtbot):
    """
    Verify that clicking the button changes the label text.
    """
    widget = SimpleWidget()
    qtbot.addWidget(widget)

    # Assert initial state
    assert widget.label.text() == "Initial"

    # Interact
    qtbot.mouseClick(widget.button, Qt.MouseButton.LeftButton)

    # Assert final state
    assert widget.label.text() == "Clicked"
