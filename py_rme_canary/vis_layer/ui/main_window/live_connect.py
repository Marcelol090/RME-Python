from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QMessageBox

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class ConnectDialog(QDialog):
    def __init__(self, parent=None, host="127.0.0.1", port=7171):
        super().__init__(parent)
        self.setWindowTitle("Connect to Live Server")
        self.host = host
        self.port = port

        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Host:"))
        self.host_edit = QLineEdit(self.host)
        layout.addWidget(self.host_edit)

        layout.addWidget(QLabel("Port:"))
        self.port_edit = QLineEdit(str(self.port))
        layout.addWidget(self.port_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_values(self) -> tuple[str, int]:
        return self.host_edit.text(), int(self.port_edit.text())


def open_connect_dialog(editor: "QtMapEditor") -> None:
    dlg = ConnectDialog(editor)
    if dlg.exec():
        host, port = dlg.get_values()
        try:
            success = editor.session.connect_live(host, port)
            if success:
                QMessageBox.information(editor, "Connected", f"Successfully connected to {host}:{port}")
            else:
                QMessageBox.critical(editor, "Connection Failed", f"Could not connect to {host}:{port}")
        except Exception as e:
            QMessageBox.critical(editor, "Error", str(e))

def disconnect_live(editor: "QtMapEditor") -> None:
    editor.session.disconnect_live()
    QMessageBox.information(editor, "Disconnected", "Disconnected from Live Server")
