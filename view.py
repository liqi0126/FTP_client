from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem
from PyQt5.uic import loadUi


class ClientUI(QMainWindow):
    def __init__(self):
        super(ClientUI, self).__init__()
        loadUi("client.ui", self)
        self.setWindowTitle("Simple Client")

        # quick DEBUG
        self.host.setText("209.51.188.20")
        self.username.setText("anonymous")
        self.password.setText("anonymous@")
        self.port.setText("21")

        self.remoteFileWidget.setColumnCount(6)
        self.remoteFileWidget.setHeaderLabels(['Name', 'Size', 'Type', 'Last Modifed', 'Mode', 'Owner'])

    def update_remote_size(self, files):
        self.remoteFileWidget.clear()

        for file in files:
            self.remoteFileWidget.addTopLevelItem(QTreeWidgetItem(file))