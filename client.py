import sys

from PyQt5.QtWidgets import QApplication
from view import ClientUI
from model import ClientModel
from controller import ClientCtrl


def main():
    client = QApplication(sys.argv)
    # Show the client's UI
    client_view = ClientUI()
    client_view.show()
    # Create instances of the model and the controller
    client_model = ClientModel()
    ClientCtrl(model=client_model, view=client_view)
    # Execute client's main loop
    sys.exit(client.exec_())


if __name__ == '__main__':
    main()