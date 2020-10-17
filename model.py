from socket import *
from enum import Enum

import os
import re

BUF_SIZE = 8096
BACKLOG = 5


class ClientStatus(Enum):
    DISCONNECT = 0
    CONNECT = 1
    USER = 2
    PASS = 3
    PORT = 4
    PASV = 5


class ClientModel(object):
    def __init__(self):
        self.command_socket = None

        self.status = ClientStatus.DISCONNECT

        self.file_socket = None
        self.file_ip = None
        self.file_port = None

        self.cur_path = os.path.dirname(os.path.abspath(__file__))

        self.offset = 0

    # standard command of FTP
    def connect(self, host, port):
        self.command_socket = socket(AF_INET, SOCK_STREAM)
        self.command_socket.connect((host, int(port)))
        response = str(self.command_socket.recv(BUF_SIZE))
        return "server " + response

    def send_command(self, command, argu=None):
        msg = command
        if argu is not None and len(argu) > 0:
            msg += " " + argu
        msg += "\r\n"
        self.command_socket.send(msg.encode())
        return "server " + self.command_socket.recv(BUF_SIZE).decode()

    def user(self, username):
        self.status = ClientStatus.USER
        return self.send_command("USER", username)

    def password(self, password):
        self.status = ClientStatus.PASS
        return self.send_command("PASS", password)

    def type(self):
        return self.send_command("TYPE")

    def mkd(self, dir_name):
        return self.send_command("MKD", dir_name)

    def rnfr(self, old_name):
        return self.send_command("RNFR", old_name)

    def rnto(self, new_name):
        return self.send_command("RNTO", new_name)

    def rmd(self, dir_name):
        return self.send_command("RMD", dir_name)

    def pwd(self):
        return self.send_command("PWD")

    def cwd(self):
        return self.send_command("CWD")

    def syst(self):
        return self.send_command("SYST")

    def rest(self, offset):
        return self.send_command("REST", offset)

    def quit(self):
        response = self.send_command("QUIT")
        self.status = ClientStatus.DISCONNECT
        self.command_socket.close()
        return response

    def port(self, ip, port):
        port = int(port)
        addr = self.ip_and_port_to_addr(ip, port)
        self.file_socket = socket(AF_INET, SOCK_STREAM)
        self.file_socket.bind((ip, port))
        self.file_socket.listen(BACKLOG)
        response = self.send_command("PORT", addr)
        self.status = ClientStatus.PORT
        return response

    def pasv(self):
        response = self.send_command("PASV")
        addr = re.search(r"\d{1,3},\d{1,3},\d{1,3},\d{1,3},\d{1,3}", response).group()
        ip, port = self.addr_to_ip_and_port(addr)
        self.file_ip = ip
        self.file_port = port
        # self.file_socket = socket(AF_INET, SOCK_STREAM)
        self.status = ClientStatus.PASV
        return response

    def retr_port(self, filename):
        responses = []

        msg = "RETR " + filename + "\r\n"
        self.command_socket.send(msg.encode())
        socket, _ = self.file_socket.accept()
        response = "server " + str(self.command_socket.recv(BUF_SIZE))
        responses.append(response)

        if response[0] != '5':
            file_path = os.path.join(self.cur_path, filename)
            self.recv_data(socket, file_path, self.offset)
            response = "server " + str(self.command_socket.recv(BUF_SIZE))
            responses.append(response)

        socket.close()
        self.file_socket.close()
        self.file_socket = None
        return responses

    def retr_pasv(self, filename):
        responses = []

        msg = "RETR " + filename + "\r\n"
        self.command_socket.send(msg.encode())
        self.file_socket.connect((self.file_ip, self.file_port))
        response = "server " + str(self.command_socket.recv(BUF_SIZE))
        responses.append(response)

        if response[0] != '5':
            file_path = os.path.join(self.cur_path, filename)
            self.recv_data(self.file_socket, file_path, self.offset)
            response = "server " + str(self.command_socket.recv(BUF_SIZE))
            responses.append(response)

        self.file_socket.close()
        self.file_socket = None
        return responses

    def retr(self, filename):
        if self.status == ClientStatus.PORT:
            response = self.retr_port(filename)
        elif self.status == ClientStatus.PASV:
            response = self.retr_pasv(filename)
        else:
            return "system 0 RETR require PORT/PASV mode"
        self.offset = 0
        self.status = ClientStatus.PASS
        return response

    def list_port(self):
        list_str = b''
        responses = []

        msg = "LIST\r\n"
        self.command_socket.send(msg.encode())
        socket, _ = self.file_socket.accept()
        response = "server " + str(self.command_socket.recv(BUF_SIZE).decode())
        responses.append(response)

        if response[0] != '5':
            buf = socket.recv(BUF_SIZE)
            while buf:
                list_str += buf
                buf = socket.recv(BUF_SIZE)
            response = "server " + str(self.command_socket.recv(BUF_SIZE))
            responses.append(response)

        socket.close()
        self.file_socket.close()
        self.file_socket = None
        return responses, list_str.decode()

    def list_pasv(self):
        list_str = b''
        responses = []

        msg = "LIST\r\n"
        self.command_socket.send(msg.encode())
        self.file_socket.connect((self.file_ip, self.file_port))
        response = "server " + str(self.command_socket.recv(BUF_SIZE))
        responses.append(response)

        if response[0] != '5':
            buf = self.file_socket.recv(BUF_SIZE)
            while buf:
                list_str += buf
                buf = self.file_socket.recv(BUF_SIZE)
            response = "server " + str(self.command_socket.recv(BUF_SIZE))
            responses.append(response)

        self.file_socket.close()
        self.file_socket = None
        return responses, list_str.decode()

    def list(self):
        if self.status == ClientStatus.PORT:
            response, list_str = self.list_port()
        elif self.status == ClientStatus.PASV:
            response, list_str = self.list_pasv()
        else:
            return "system 0 LIST require PORT/PASV mode", ""
        self.status = ClientStatus.PASS
        return response, list_str

    def stor_port(self, filename):
        file_path = os.path.join(self.cur_path, filename)

        if not os.path.isfile(file_path):
            return "system 0 not such file"

        responses = []

        msg = "STOR " + filename + "\r\n"
        self.command_socket.send(msg.encode())
        socket, _ = self.file_socket.accept()
        response = "server " + str(self.command_socket.recv(BUF_SIZE))
        responses.append(response)

        if response[0] != '5':
            self.send_data(socket, file_path, self.offset)
            response = "server " + str(self.command_socket.recv(BUF_SIZE))
            responses.append(response)

        socket.close()
        self.file_socket.close()
        self.file_socket = None
        return responses

    def stor_pasv(self, filename):
        file_path = os.path.join(self.cur_path, filename)

        if not os.path.isfile(file_path):
            return "system 0 not such file"

        responses = []
        msg = "STOR " + filename + "\r\n"
        self.command_socket.send(msg.encode())
        self.file_socket.connect((self.file_ip, self.file_port))
        response = "server " + str(self.command_socket.recv(BUF_SIZE))
        responses.append(response)

        if response[0] != '5':
            self.send_data(socket, file_path, self.offset)
            response = "server " + str(self.command_socket.recv(BUF_SIZE))
            responses.append(response)

        self.file_socket.close()
        self.file_socket = None
        return responses

    def stor(self, filename):
        if self.status == ClientStatus.PORT:
            response = self.stor_port(filename)
        elif self.status == ClientStatus.PASV:
            response = self.stor_pasv(filename)
        else:
            return "system 0 STOR require PORT/PASV mode"
        self.offset = 0
        self.status = ClientStatus.PASS
        return response

    # help functions
    @staticmethod
    def addr_to_ip_and_port(addr):
        addr = addr.split(',')
        if len(addr) < 6:
            return "system 0 invalid addr\r\n"
        ip = '.'.join(addr[:4])
        port = int(addr[-2]) * 256 + int(addr[-1])
        return ip, port

    @staticmethod
    def ip_and_port_to_addr(ip, port):
        addr = ip.split('.')
        addr.append(str(port / 256))
        addr.append(str(port % 256))
        return ','.join(addr)

    @staticmethod
    def recv_data(sock, file_path, offset):
        fp = open(file_path, "wb")
        if offset > 0:
            fp.seek(offset-1, 0)

        buf = sock.recv(BUF_SIZE)
        while buf:
            fp.write(buf)
            buf = sock.recv(BUF_SIZE)

    @staticmethod
    def send_data(sock, file_path, offset):
        fp = open(file_path, "rb")

        if offset > 0:
            fp.seek(offset-1, 0)

        buf = fp.read(BUF_SIZE)
        while buf:
            sock.send(buf)
            fp.read(BUF_SIZE)
