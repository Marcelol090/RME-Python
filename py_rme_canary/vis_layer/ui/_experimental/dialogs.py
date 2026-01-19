"""
Standard Dialogs for the Map Editor (DEPRECATED - PySide6).

⚠️ WARNING: This file uses PySide6. The main application uses PyQt6.
   Do NOT import this file in production code.

   Canonical implementation: vis_layer/ui/main_window/dialogs/

Original purpose - Implements replacement for:
- source/about_window.cpp
- source/properties_window.cpp (generic)
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QTextEdit, QTabWidget, QWidget, QDialogButtonBox
)
from PySide6.QtCore import Qt, __version__ as qt_version
from PySide6 import __version__ as pyside_version
import sys
import platform

class AboutDialog(QDialog):
    """
    Standard About Dialog showing versioning and credits.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Canary Map Editor")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Header / Logo placeholder
        title = QLabel("Canary Map Editor")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffeb3b;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Version Info
        info_text = (
            f"Version: 0.1.0-alpha\n"
            f"Python: {sys.version.split()[0]}\n"
            f"PySide6: {pyside_version}\n"
            f"Qt: {qt_version}\n"
            f"OS: {platform.system()} {platform.release()}"
        )
        info_lbl = QLabel(info_text)
        info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_lbl)
        
        # Tabs for Credits / License
        tabs = QTabWidget()
        
        # Credits Tab
        credits_tab = QWidget()
        c_layout = QVBoxLayout(credits_tab)
        credits_text = QTextEdit()
        credits_text.setReadOnly(True)
        credits_text.setHtml("""
        <h3>Core Team</h3>
        <ul>
            <li>Marcelo Henrique - Lead Developer</li>
            <li>Antigravity AI - Assistant</li>
        </ul>
        <h3>Special Thanks</h3>
        <p>Remere's Map Editor Team, OTA Team.</p>
        """)
        c_layout.addWidget(credits_text)
        tabs.addTab(credits_tab, "Credits")
        
        # License Tab
        license_tab = QWidget()
        l_layout = QVBoxLayout(license_tab)
        lic_text = QTextEdit()
        lic_text.setReadOnly(True)
        lic_text.setText("MIT License (or GPL if using TFS sources).")
        l_layout.addWidget(lic_text)
        tabs.addTab(license_tab, "License")
        
        layout.addWidget(tabs)
        
        # Close Button
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.accept)
        layout.addWidget(btn_box)

class PropertyDialog(QDialog):
    """
    Generic property editor dialog.
    """
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.layout = QVBoxLayout(self)
        
        # Content placeholder
        self.layout.addWidget(QLabel("Properties generic placeholder"))
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        self.layout.addWidget(btns)
