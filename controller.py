from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileSystemModel, QTableWidgetItem

from PyQt5.QtCore import QAbstractTableModel


class ResponseModel(QAbstractTableModel):
    def __init__(self, *args, **kwargs):
        super(ResponseModel, self).__init__(*args, **kwargs)


class ClientCtrl(QtCore.QObject):
    def __init__(self, model, view):
        super(ClientCtrl, self).__init__(view)
        self.model = model
        self.view = view

        self.view.responses.setColumnCount(3)
        self.view.responses.setHorizontalHeaderLabels(['source', 'message', 'code'])
        self.view.responses.setColumnWidth(0, 80)
        self.view.responses.setColumnWidth(2, 80)

        self.connect_signals()

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
        response = response.split(' ')
        source = response[0]
        code = response[1]
        message = ' '.join(response[2:])

        self.view.responses.setRowCount(self.responses.rowCount() + 1)
        sourceItem = QTableWidgetItem(source)
        self.view.responses.setItem(self.view.responses.rowCount()-1, 0, sourceItem)
        messageItem = QTableWidgetItem(message)
        self.view.responses.setItem(self.view.responses.rowCount()-1, 1, messageItem)
        codeItem = QTableWidgetItem(code)
        self.view.responses.setItem(self.view.responses.rowCount()-1, 2, codeItem)

    def push_responses(self, responses):
        if isinstance(responses, list):
            for response in responses:
                self.add_response(response)
        else:
            self.add_response(responses)

    def login(self):
        host = self.view.host.text()
        port = self.view.port.text()
        username = self.view.username.text()
        password = self.view.password.text()

        response = self.model.connect(host, port)
        self.push_responses(response)

        if response[0] == '5':
            return

        response = self.model.user(username)
        self.push_responses(response)

        if response[0] == '5':
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
