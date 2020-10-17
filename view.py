from PyQt5.QtWidgets import QMainWindow
from PyQt5.uic import loadUi


class ClientUI(QMainWindow):
    def __init__(self):
        super(ClientUI, self).__init__()
        loadUi("client.ui", self)
        self.setWindowTitle("Simple Client")