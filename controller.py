from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileSystemModel, QTableWidgetItem

from PyQt5.QtCore import QAbstractTableModel

from model import SYSTEM_HEADER


class ResponseModel(QAbstractTableModel):
    def __init__(self, *args, **kwargs):
        super(ResponseModel, self).__init__(*args, **kwargs)


class ClientCtrl(QtCore.QObject):
    def __init__(self, model, view):
        super(ClientCtrl, self).__init__(view)
        self.model = model
        self.view = view

        # DEBUG
        self.view.host.setText("209.51.188.20")
        self.view.username.setText("anonymous")
        self.view.password.setText("anonymous@")
        self.view.port.setText("21")

        self.connect_signals()

    @staticmethod
    def get_status_code(msg):
        return msg.split(' ')[1]

    def connect_signals(self):
        # login and exit
        self.view.connect.clicked.connect(self.login)
        self.view.exit.clicked.connect(self.exit)

        # local
        self.view.localSiteGo.clicked.connect(self.change_local_site)
        self.view.localCreateDir.clicked.connect(self.create_local_dir)
        self.view.localCreateFile.clicked.connect(self.create_local_file)
        self.view.localRename.clicked.connect(self.local_rename)
        self.view.localDelete.clicked.connect(self.local_delete)

        # remote
        self.view.remoteSiteGo.clicked.connect(self.change_remote_site)
        self.view.remoteCreateDir.clicked.connect(self.create_remote_dir)
        self.view.remoteCreateFile.clicked.connect(self.create_remote_file)
        self.view.remoteRename.clicked.connect(self.remote_rename)
        self.view.remoteDelete.clicked.connect(self.remote_delete)

        # upload and download
        self.view.upload.clicked.connect(self.upload)
        self.view.download.clicked.connect(self.download)

    def push_response(self, response):
        if not response.endswith('\n'):
            response += '\n'
        self.view.responses.insertPlainText(response)

    def push_responses(self, responses):
        if isinstance(responses, list):
            for response in responses:
                self.push_response(response)
        else:
            self.push_response(responses)

    def login(self):
        host = self.view.host.text()
        port = self.view.port.text()
        username = self.view.username.text()
        password = self.view.password.text()

        if not host:
            self.push_responses(SYSTEM_HEADER + "5 please enter host to connect!")
            return

        if not port:
            self.push_responses(SYSTEM_HEADER + "5 please enter port to connect!")
            return

        response = self.model.connect(host, port)
        self.push_responses(response)

        if self.get_status_code(response)[0] == '5':
            return

        if not username:
            self.push_responses(SYSTEM_HEADER + "5 please enter username to login!")
            return

        response = self.model.user(username)
        self.push_responses(response)

        if self.get_status_code(response)[0] == '5':
            return

        if not password:
            self.push_responses(SYSTEM_HEADER + "5 please enter password to login!")
            return

        response = self.model.password(password)
        self.push_responses(response)

    def exit(self):
        print('exit called')

    def change_local_site(self):
        pass

    def create_local_dir(self):
        pass

    def create_local_file(self):
        pass

    def upload(self):
        pass

    def local_rename(self):
        pass

    def local_delete(self):
        pass

    def delete_local_file(self):
        pass

    def delete_local_dir(self):
        pass

    def change_remote_site(self):
        pass

    def create_remote_dir(self):
        pass

    def create_remote_file(self):
        pass

    def download(self):
        pass

    def remote_rename(self):
        pass

    def remote_delete(self):
        pass

    def delete_remote_file(self):
        pass

    def delete_remote_dir(self):
        pass
