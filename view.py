from enum import Enum
from functools import partial

from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem, QPushButton, QHeaderView, QHBoxLayout, QWidget
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt

from config import *


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
        self.port.setText("20000")

        remote_header = ['Name', 'Size', 'Type', 'Last Modifed', 'Mode', 'Owner']
        self.remoteFileWidget.setColumnCount(len(remote_header))
        self.remoteFileWidget.setHeaderLabels(remote_header)
        self.remoteFileWidget.header().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, len(remote_header)):
            self.remoteFileWidget.header().setSectionResizeMode(col, QHeaderView.ResizeToContents)

        transfer_header = ['Server/Local File', 'Direction', 'Remote File', 'Size', 'Start Time', 'End Time', 'Status', 'Operation']
        self.transferWidget.setColumnCount(len(transfer_header))
        self.transferWidget.setHeaderLabels(transfer_header)
        self.transferWidget.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.transferWidget.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.transferWidget.header().setSectionResizeMode(2, QHeaderView.Stretch)
        for col in range(3, len(transfer_header)):
            self.transferWidget.header().setSectionResizeMode(col, QHeaderView.ResizeToContents)

    def refresh_remote_widget(self, files):
        self.remoteFileWidget.clear()
        for file in files:
            self.remoteFileWidget.addTopLevelItem(QTreeWidgetItem(file))

    def refresh_transfer_widget(self, running_proc, pause_resume_callback, cancel_callback):
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

            btnWidget = QWidget()
            layout = QHBoxLayout()

            prBtn = QPushButton("pause/resume")
            cancelBtn = QPushButton("cancel")
            layout.addWidget(prBtn)
            layout.addWidget(cancelBtn)
            prBtn.clicked.connect(partial(pause_resume_callback, proc))
            cancelBtn.clicked.connect(partial(cancel_callback, proc))

            btnWidget.setLayout(layout)

            self.transferWidget.addTopLevelItem(item)
            self.transferWidget.setItemWidget(item, ProcessHeader.Btn.value, btnWidget)

    def update_transfer_item(self, proc):
        items = self.transferWidget.findItems(str(proc.start_time), Qt.MatchExactly, ProcessHeader.StartTime.value)
        if len(items) > 0:
            item = items[0]
            item.setText(ProcessHeader.Size.value, str(proc.trans_size) + "/" + str(proc.total_size))
            item.setText(ProcessHeader.Status.value, proc.status.value)

