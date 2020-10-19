from enum import Enum
from functools import partial

from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem, QPushButton
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt

from controller import TransferStatus, ProcessStatus


class ClientUI(QMainWindow):
    def __init__(self):
        super(ClientUI, self).__init__()
        loadUi("client.ui", self)
        self.setWindowTitle("Simple Client")

        # quick DEBUG
        # self.host.setText("209.51.188.20")
        self.host.setText("127.0.0.1")
        self.username.setText("anonymous")
        self.password.setText("anonymous@")
        # self.port.setText("21")
        self.port.setText("20002")
        self.localSite.setText("/Users/liqi17thu/Desktop")

        remote_header = ['Name', 'Size', 'Type', 'Last Modifed', 'Mode', 'Owner']
        self.remoteFileWidget.setColumnCount(len(remote_header))
        self.remoteFileWidget.setHeaderLabels(remote_header)

        transfer_header = ['Server/Local File', 'Direction', 'Remote File', 'Size', 'Start Time', 'End Time', 'Status', '', '']
        self.transferWidget.setColumnCount(len(transfer_header))
        self.transferWidget.setHeaderLabels(transfer_header)

    def refresh_remote_widget(self, files):
        self.remoteFileWidget.clear()
        for file in files:
            self.remoteFileWidget.addTopLevelItem(QTreeWidgetItem(file))

    def refresh_transfer_widget(self, running_proc, pause_callback, resume_callback):
        self.transferWidget.clear()

        for proc_name in running_proc:
            proc = running_proc[proc_name]
            item = QTreeWidgetItem([proc.local_file,
                     '<<--' if proc.download else '-->>',
                     proc.remote_file,
                     str(proc.trans_size) + "/" + str(proc.total_size),
                     str(proc.start_time),
                     '----',
                     proc.status.value
                     ])

            pauseBtn = QPushButton("pause")
            resumeBtn = QPushButton("resume")

            pauseBtn.clicked.connect(partial(pause_callback, proc))
            resumeBtn.clicked.connect(partial(resume_callback, proc))

            self.transferWidget.addTopLevelItem(item)
            self.transferWidget.setItemWidget(item, ProcessStatus.pauseBtn.value, pauseBtn)
            self.transferWidget.setItemWidget(item, ProcessStatus.resumeBtn.value, resumeBtn)

    def update_transfer_item(self, proc):
        items = self.transferWidget.findItems(str(proc.start_time), Qt.MatchExactly, ProcessStatus.StartTime.value)
        if len(items) > 0:
            item = items[0]
            item.setText(ProcessStatus.Size.value, str(proc.trans_size) + "/" + str(proc.total_size))
            item.setText(ProcessStatus.Status.value, proc.status.value)

