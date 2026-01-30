from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


def apply_dark_theme(app: QApplication):
    """
    Applies a dark theme to the QApplication using the Fusion style and a custom palette.
    """
    app.setStyle("Fusion")

    dark_palette = QPalette()

    # Base colors
    color_dark = QColor(45, 45, 45)
    color_mid = QColor(40, 40, 40)
    color_light = QColor(60, 60, 60)
    color_text = QColor(208, 208, 208)
    color_bright_text = QColor(255, 255, 255)
    color_disabled_text = QColor(127, 127, 127)
    color_highlight = QColor(42, 130, 218)
    color_highlight_text = QColor(255, 255, 255)
    color_link = QColor(42, 130, 218)

    # Window
    dark_palette.setColor(QPalette.ColorRole.Window, color_dark)
    dark_palette.setColor(QPalette.ColorRole.WindowText, color_text)

    # Base (text widgets, lists, etc)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, color_dark)

    # Tooltips
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, color_bright_text)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, color_bright_text)

    # Text
    dark_palette.setColor(QPalette.ColorRole.Text, color_text)
    dark_palette.setColor(QPalette.ColorRole.Button, color_dark)
    dark_palette.setColor(QPalette.ColorRole.ButtonText, color_text)
    dark_palette.setColor(QPalette.ColorRole.BrightText, color_bright_text)

    # Highlight
    dark_palette.setColor(QPalette.ColorRole.Highlight, color_highlight)
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, color_highlight_text)

    # Links
    dark_palette.setColor(QPalette.ColorRole.Link, color_link)
    dark_palette.setColor(QPalette.ColorRole.LinkVisited, color_highlight)  # Use highlight for visited

    # Disabled
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, color_disabled_text)
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, color_disabled_text)
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, color_disabled_text)
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(80, 80, 80))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.HighlightedText, color_disabled_text)

    app.setPalette(dark_palette)

    # Additional stylesheet for specific controls if needed
    app.setStyleSheet("""
        QToolTip {
            color: #ffffff;
            background-color: #2a82da;
            border: 1px solid white;
        }
    """)
