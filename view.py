import humanize
from functools import partial

from PyQt5.QtWidgets import QMainWindow, QTreeWidget, QTreeWidgetItem, QPushButton, QHeaderView, QHBoxLayout, QWidget, \
    QProgressBar
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
        self.host.setText("59.66.136.21")
        self.username.setText("ssast")
        self.password.setText("ssast")
        self.port.setText("21")
        # self.port.setText("20000")

        remote_header = ['Name', 'Size', 'Type', 'Last Modifed', 'Mode', 'Owner']
        self.remoteFileWidget.setColumnCount(len(remote_header))
        self.remoteFileWidget.setHeaderLabels(remote_header)
        self.remoteFileWidget.header().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, len(remote_header)):
            self.remoteFileWidget.header().setSectionResizeMode(col, QHeaderView.ResizeToContents)

        self.transferWidget = QTreeWidget()
        transfer_header = ['Server/Local File', 'Direction', 'Remote File', 'Size', 'Start Time', 'End Time', 'Status', 'Operation']
        self.transferWidget.setColumnCount(len(transfer_header))
        self.transferWidget.setHeaderLabels(transfer_header)
        self.transferWidget.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.transferWidget.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.transferWidget.header().setSectionResizeMode(2, QHeaderView.Stretch)
        for col in range(3, len(transfer_header) - 1):
            self.transferWidget.header().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.transferWidget.setColumnWidth(len(transfer_header) - 1, 0)

        self.finishedWidget = QTreeWidget()
        finished_header = ['Server/Local File', 'Direction', 'Remote File', 'Size', 'Start Time', 'End Time',
                           'Elapsed time', 'Status']
        self.finishedWidget.setColumnCount(len(finished_header))
        self.finishedWidget.setHeaderLabels(finished_header)
        self.finishedWidget.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.finishedWidget.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.finishedWidget.header().setSectionResizeMode(2, QHeaderView.Stretch)
        for col in range(3, len(finished_header) - 1):
            self.finishedWidget.header().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.finishedWidget.setColumnWidth(len(transfer_header) - 1, 0)

        self.tabWidget.clear()
        self.tabWidget.addTab(self.transferWidget, "Transferring")
        self.tabWidget.addTab(self.finishedWidget, "Finished")

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
                                    # proc.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                                    str(proc.start_time),
                                    '----',
                                    proc.status.value,
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

            # pbar = QProgressBar()
            # pbar.setValue(100 * proc.trans_size / proc.total_size)

            self.transferWidget.addTopLevelItem(item)
            # self.transferWidget.setItemWidget(item, RunningProcessHeader.Progress.value, pbar)
            self.transferWidget.setItemWidget(item, RunningProcessHeader.Btn.value, btnWidget)

    def update_transfer_item(self, proc):
        items = self.transferWidget.findItems(str(proc.start_time), Qt.MatchExactly,
                                              RunningProcessHeader.StartTime.value)
        for item in items:
            # TODO: check correctness
            item.setText(RunningProcessHeader.Size.value, str(proc.trans_size) + "/" + str(proc.total_size))
            item.setText(RunningProcessHeader.Status.value, proc.status.value)

            # pbar = QProgressBar()
            # pbar.setValue(100 * proc.trans_size / proc.total_size)
            # self.transferWidget.setItemWidget(item, RunningProcessHeader.Progress.value, pbar)

    def refresh_finished_widget(self, finished_proc):
        self.finishedWidget.clear()

        for proc in finished_proc:
            if proc.trans_size < proc.total_size:
                size_str = humanize.naturalsize(proc.trans_size) + "/" + humanize.naturalsize(proc.total_size)
            else:
                size_str = humanize.naturalsize(proc.total_size)

            item = QTreeWidgetItem([proc.local_file,
                                    '<<--' if proc.download else '-->>',
                                    proc.remote_file,
                                    size_str,
                                    # proc.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                                    # proc.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                                    str(proc.start_time),
                                    str(proc.end_time),
                                    humanize.naturaldelta(proc.end_time - proc.start_time),
                                    proc.status.value,
                                    ])

            self.finishedWidget.addTopLevelItem(item)
