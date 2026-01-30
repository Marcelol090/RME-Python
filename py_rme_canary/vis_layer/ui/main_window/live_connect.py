from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class ConnectDialog(QDialog):
    def __init__(self, parent=None, host="127.0.0.1", port=7171):
        super().__init__(parent)
        self.setWindowTitle("Connect to Live Server")
        self.host = host
        self.port = port

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit("")
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Host:"))
        self.host_edit = QLineEdit(self.host)
        layout.addWidget(self.host_edit)

        layout.addWidget(QLabel("Port:"))
        self.port_edit = QLineEdit(str(self.port))
        layout.addWidget(self.port_edit)

        layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit("")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_values(self) -> tuple[str, str, int, str]:
        return self.name_edit.text(), self.host_edit.text(), int(self.port_edit.text()), self.password_edit.text()


class HostDialog(QDialog):
    def __init__(self, parent=None, host="127.0.0.1", port=7171):
        super().__init__(parent)
        self.setWindowTitle("Host Live Server")
        self.host = host
        self.port = port

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Server Name:"))
        self.name_edit = QLineEdit("Live Server")
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Host:"))
        self.host_edit = QLineEdit(self.host)
        layout.addWidget(self.host_edit)

        layout.addWidget(QLabel("Port:"))
        self.port_edit = QLineEdit(str(self.port))
        layout.addWidget(self.port_edit)

        layout.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit("")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_values(self) -> tuple[str, str, int, str]:
        return (
            self.name_edit.text(),
            self.host_edit.text(),
            int(self.port_edit.text()),
            self.password_edit.text(),
        )


def open_connect_dialog(editor: QtMapEditor) -> None:
    dlg = ConnectDialog(editor)
    if dlg.exec():
        name, host, port, password = dlg.get_values()
        try:
            success = editor.session.connect_live(host, port, name=name, password=password)
            if success:
                QMessageBox.information(editor, "Connected", f"Successfully connected to {host}:{port}")
                if hasattr(editor, "dock_live_log"):
                    editor.dock_live_log.set_input_enabled(True)
            else:
                QMessageBox.critical(editor, "Connection Failed", f"Could not connect to {host}:{port}")
        except Exception as e:
            QMessageBox.critical(editor, "Error", str(e))


def disconnect_live(editor: QtMapEditor) -> None:
    editor.session.disconnect_live()
    QMessageBox.information(editor, "Disconnected", "Disconnected from Live Server")
    if hasattr(editor, "dock_live_log"):
        editor.dock_live_log.set_input_enabled(False)


def open_host_dialog(editor: QtMapEditor) -> None:
    dlg = HostDialog(editor)
    if dlg.exec():
        name, host, port, password = dlg.get_values()
        try:
            success = editor.session.start_live_server(host=host, port=port, name=name, password=password)
            if success:
                QMessageBox.information(editor, "Live Server", f"Hosting on {host}:{port}")
            else:
                QMessageBox.critical(editor, "Live Server", "Failed to start live server")
        except Exception as e:
            QMessageBox.critical(editor, "Error", str(e))


def stop_host(editor: QtMapEditor) -> None:
    editor.session.stop_live_server()
    QMessageBox.information(editor, "Live Server", "Live server stopped")


def kick_client(editor: QtMapEditor) -> None:
    client_id, ok = QInputDialog.getInt(editor, "Kick Client", "Client ID:", 1, 1, 2**31 - 1, 1)
    if not ok:
        return
    reason, ok = QInputDialog.getText(editor, "Kick Client", "Reason:", text="Disconnected by host")
    if not ok:
        return
    if not editor.session.kick_live_client(int(client_id), reason=str(reason)):
        QMessageBox.information(editor, "Kick Client", "Client not found or server not running")


def ban_client(editor: QtMapEditor) -> None:
    client_id, ok = QInputDialog.getInt(editor, "Ban Client", "Client ID:", 1, 1, 2**31 - 1, 1)
    if not ok:
        return
    reason, ok = QInputDialog.getText(editor, "Ban Client", "Reason:", text="Banned by host")
    if not ok:
        return
    if not editor.session.ban_live_client(int(client_id), reason=str(reason)):
        QMessageBox.information(editor, "Ban Client", "Client not found or server not running")
