import os
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

class FileType(Enum):
    File = 'File'
    Folder = 'Folder'


class ClientCtrl(QtCore.QObject):
    def __init__(self, model, view):
        super(ClientCtrl, self).__init__(view)
        self.model = model
        self.view = view

        self.mode = ClientMode.PORT

        self.local_cur_path = QDir.rootPath()
        self.remote_cur_path = '/'

        # local path system
        self.view.localSite.setText(self.local_cur_path)
        self.model.localFileModel.setRootPath(self.local_cur_path)
        self.view.localFileView.setModel(self.model.localFileModel)

        # signal slots
        self.view.connect.clicked.connect(self.login)
        self.view.exit.clicked.connect(self.exit)

        self.view.localFileView.selectionModel().selectionChanged.connect(self.sync_local_path)
        self.view.localSiteBtn.clicked.connect(self.change_local_site)

        self.view.remoteFileWidget.selectionModel().selectionChanged.connect(self.sync_remote_path)
        self.view.remoteRename.clicked.connect(self.remote_rename)
        self.view.remoteDelete.clicked.connect(self.remote_delete)
        self.view.remoteSiteBtn.clicked.connect(self.change_remote_site)
        self.view.remoteCreateDir.clicked.connect(self.create_remote_dir)

        self.view.upload.clicked.connect(self.upload)
        self.view.download.clicked.connect(self.download)

    def login(self):
        host = self.view.host.text()
        port = self.view.port.text()
        username = self.view.username.text()
        password = self.view.password.text()

        if not host:
            self.push_response(SYSTEM_HEADER + "5 please enter host to connect!")
            return

        if not port:
            self.push_response(SYSTEM_HEADER + "5 please enter port to connect!")
            return

        response = self.model.connect(host, port)
        self.push_response(response)

        if self.get_status_code(response)[0] == '5':
            return

        if not username:
            self.push_response(SYSTEM_HEADER + "5 please enter username to login!")
            return

        response = self.model.user(username)
        self.push_response(response)

        if self.get_status_code(response)[0] == '5':
            return

        if not password:
            self.push_response(SYSTEM_HEADER + "5 please enter password to login!")
            return

        response = self.model.password(password)
        self.push_response(response)

        response, path = self.model.pwd()
        self.push_response(response)
        self.remote_cur_path = path
        self.view.remoteSite.setText(self.remote_cur_path)
        self.update_remote_site()

    def exit(self):
        pass

    def sync_local_path(self):
        selected_path = self.model.localFileModel.filePath(self.view.localFileView.selectedIndexes()[0])
        self.view.localSite.setText(selected_path)

    def sync_remote_path(self):
        item = self.view.remoteFileWidget.currentItem()
        filename = item.text(FileHeader.Name.value)
        selected_path = os.path.join(self.remote_cur_path, filename)
        self.view.remoteSite.setText(selected_path)

    def change_local_site(self):
        new_path = self.view.localSite.text()
        if not os.path.isdir(new_path):
            self.push_response("system: 5 invalid path.")
            return

        self.local_cur_path = new_path
        self.view.localFileView.setRootIndex(self.model.localFileModel.setRootPath(self.local_cur_path))

    def upload(self):
        filepath = self.model.localFileModel.filePath(self.view.localFileView.selectedIndexes()[0])

        self.push_response(self.model.type('I'))
        if self.mode == ClientMode.PORT:
            self.push_response(self.model.port())
        else:
            self.push_response(self.model.pasv())

        fp = open(os.path.join(filepath), 'rb')
        self.push_response(self.model.stor(filepath.split('/')[-1], fp.read))
        self.update_remote_site()

    def update_remote_site(self):
        if self.mode == ClientMode.PORT:
            self.push_response(self.model.port())
        else:
            self.push_response(self.model.pasv())
        response, file_list = self.model.list()
        self.push_response(response)

        files = self.parse_file_list(file_list)
        self.view.update_remote_size(files)

    def change_remote_site(self):
        self.remote_cur_path = self.view.remoteSite.text()

        response = self.model.cwd(self.remote_cur_path)
        self.push_response(response)
        if self.get_status_code(response)[0] == '5':
            return
        self.update_remote_site()

    def create_remote_dir(self):
        class RemoteDirDialog(QDialog):
            def __init__(self):
                super(RemoteDirDialog, self).__init__()

                self.setWindowTitle("Please Enter Directory Name")
                self.setFixedWidth(400)

                QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

                self.lineEdit = QLineEdit()

                self.buttonBox = QDialogButtonBox(QBtn)
                self.buttonBox.accepted.connect(self.accept)
                self.buttonBox.rejected.connect(self.reject)

                self.layout = QVBoxLayout()
                self.layout.addWidget(self.lineEdit)
                self.layout.addWidget(self.buttonBox)
                self.setLayout(self.layout)

        dlg = RemoteDirDialog()
        if not dlg.exec_():
            return

        new_dir_name = dlg.lineEdit.text()
        response = self.model.mkd(new_dir_name)
        self.push_response(response)
        self.update_remote_site()

    def download(self):
        item = self.view.remoteFileWidget.currentItem()
        filename = item.text(FileHeader.Name.value)

        self.model.type('I')
        if self.mode == ClientMode.PORT:
            self.model.port()
        else:
            self.model.pasv()

        fp = open(os.path.join(self.local_cur_path, filename), 'wb')
        self.push_response(self.model.retr(filename, fp.write))

    def remote_delete(self):
        item = self.view.remoteFileWidget.currentItem()
        name = item.text(FileHeader.Name.value)
        if item.text(FileHeader.Type.value) == FileType.Folder.value:
            response = self.model.rmd(name)
        else:
            response = self.model.dele(name)
        self.push_response(response)
        self.update_remote_site()

    def remote_rename(self):
        class RemoteReNameDialog(QDialog):
            def __init__(self, old_name):
                super(RemoteReNameDialog, self).__init__()

                self.setWindowTitle("Please Enter New Name")
                self.setFixedWidth(400)

                QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

                self.lineEdit = QLineEdit()
                self.lineEdit.setText(old_name)

                self.buttonBox = QDialogButtonBox(QBtn)
                self.buttonBox.accepted.connect(self.accept)
                self.buttonBox.rejected.connect(self.reject)

                self.layout = QVBoxLayout()
                self.layout.addWidget(self.lineEdit)
                self.layout.addWidget(self.buttonBox)
                self.setLayout(self.layout)

        item = self.view.remoteFileWidget.currentItem()
        old_name = item.text(FileHeader.Name.value)

        dlg = RemoteReNameDialog(old_name)
        if not dlg.exec_():
            return

        new_name = dlg.lineEdit.text()

        self.push_response(self.model.rnfr(old_name))
        self.push_response(self.model.rnto(new_name))
        self.update_remote_site()

    # help functions
    def push_response(self, response):
        if not response.endswith('\n'):
            response += '\n'
        self.view.responses.insertPlainText(response)

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
        file_type = FileType.Folder.value if mode[0] == 'd' else FileType.File.value
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
