from __future__ import annotations

import contextlib
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


def _refresh_action_states(editor: QtMapEditor) -> None:
    if hasattr(editor, "_update_action_enabled_states"):
        with contextlib.suppress(Exception):
            editor._update_action_enabled_states()


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
                _refresh_action_states(editor)
            else:
                QMessageBox.critical(editor, "Connection Failed", f"Could not connect to {host}:{port}")
                _refresh_action_states(editor)
        except Exception as e:
            QMessageBox.critical(editor, "Error", str(e))
            _refresh_action_states(editor)


def disconnect_live(editor: QtMapEditor) -> None:
    editor.session.disconnect_live()
    QMessageBox.information(editor, "Disconnected", "Disconnected from Live Server")
    if hasattr(editor, "dock_live_log"):
        editor.dock_live_log.set_input_enabled(False)
    _refresh_action_states(editor)


def open_host_dialog(editor: QtMapEditor) -> None:
    dlg = HostDialog(editor)
    if dlg.exec():
        name, host, port, password = dlg.get_values()
        try:
            success = editor.session.start_live_server(host=host, port=port, name=name, password=password)
            if success:
                QMessageBox.information(editor, "Live Server", f"Hosting on {host}:{port}")
                _refresh_action_states(editor)
            else:
                QMessageBox.critical(editor, "Live Server", "Failed to start live server")
                _refresh_action_states(editor)
        except Exception as e:
            QMessageBox.critical(editor, "Error", str(e))
            _refresh_action_states(editor)


def stop_host(editor: QtMapEditor) -> None:
    editor.session.stop_live_server()
    QMessageBox.information(editor, "Live Server", "Live server stopped")
    _refresh_action_states(editor)


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


def manage_ban_list(editor: QtMapEditor) -> None:
    banned_hosts = list(editor.session.list_live_banned_hosts())
    if not banned_hosts:
        QMessageBox.information(editor, "Ban List", "Ban list is empty or server is not running")
        return

    host, ok = QInputDialog.getItem(editor, "Ban List", "Banned host:", banned_hosts, 0, False)
    if not ok:
        return
    host = str(host).strip()
    if not host:
        return

    confirm = QMessageBox.question(
        editor,
        "Ban List",
        f"Unban host '{host}'?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if confirm != QMessageBox.StandardButton.Yes:
        return

    if editor.session.unban_live_host(host):
        QMessageBox.information(editor, "Ban List", f"Host '{host}' removed from ban list")
    else:
        QMessageBox.warning(editor, "Ban List", f"Could not unban '{host}'")
