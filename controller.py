from functools import partial
from enum import Enum

from PyQt5 import QtCore
from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import *

from model import SYSTEM_HEADER
from view import FileHeader

class ClientMode(Enum):
    PORT = 0
    PASV = 1


class ClientCtrl(QtCore.QObject):
    def __init__(self, model, view):
        super(ClientCtrl, self).__init__(view)
        self.model = model
        self.view = view

        self.mode = ClientMode.PORT

        self.local_root_path = QDir.rootPath()
        self.local_cur_path = self.local_root_path
        self.remote_cur_path = '/'

        # local path system
        self.view.localSite.setText(self.local_root_path)
        self.model.localFileModel.setRootPath(self.local_root_path)
        self.view.localFileView.setModel(self.model.localFileModel)

        # signal slots
        self.view.connect.clicked.connect(self.login)
        self.view.exit.clicked.connect(self.exit)
        self.view.remoteSiteBtn.clicked.connect(self.change_remote_site)
        self.view.remoteCreateDir.clicked.connect(self.create_remote_dir)
        self.view.download.clicked.connect(self.download)

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

        response, path = self.model.pwd()
        self.push_responses(response)
        self.remote_cur_path = path
        self.view.remoteSite.setText(self.remote_cur_path)
        self.update_remote_site()

    def exit(self):
        pass

    def update_remote_site(self):
        if self.mode == ClientMode.PORT:
            self.model.port()
        else:
            self.model.pasv()
        response, file_list = self.model.list()
        self.push_responses(response)

        files = self.parse_file_list(file_list)
        self.view.update_remote_size(files)

    def change_remote_site(self):
        self.remote_cur_path = self.view.remoteSite.text()

        response = self.model.cwd(self.remote_cur_path)
        if self.get_status_code(response)[0] == '5':
            return response
        self.update_remote_site()

    def create_remote_dir(self):
        class RemoteDirDialog(QDialog):
            def __init__(self):
                super(RemoteDirDialog, self).__init__()

                self.setWindowTitle("Please Enter Directory Name")
                self.setFixedWidth(400)

                QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

                self.newDirEdit = QLineEdit()

                self.buttonBox = QDialogButtonBox(QBtn)
                self.buttonBox.accepted.connect(self.accept)
                self.buttonBox.rejected.connect(self.reject)

                self.layout = QVBoxLayout()
                self.layout.addWidget(self.newDirEdit)
                self.layout.addWidget(self.buttonBox)
                self.setLayout(self.layout)

        dlg = RemoteDirDialog()
        if not dlg.exec_():
            return

        new_dir_name = dlg.newDirEdit.text()
        response = self.model.mkd(new_dir_name)
        self.push_responses(response)
        self.update_remote_site()

    def download(self):
        item = self.view.remoteFileWidget.currentItem()
        item.text(FileHeader.Name.value)

    # help functions
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

    @staticmethod
    def parse_single_file_list(list):
        lists = list.split()
        mode = lists[0]
        # link = lists[1]
        owner = lists[2]
        # group = lists[3]
        size = lists[4]
        last_modified = ' '.join(lists[5:8])
        filename = lists[8]
        file_type = 'Folder' if mode[0] == 'd' else 'File'
        return filename, size, file_type, last_modified, mode, owner

    @staticmethod
    def get_status_code(msg):
        return msg.split(' ')[1]

    @staticmethod
    def parse_file_list(file_list):
        lists = []
        for list in file_list.splitlines(keepends=False)[1:]:
            lists.append(ClientCtrl.parse_single_file_list(list))
        return lists
