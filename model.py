import os
import re
import socket
from enum import Enum

from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import QObject

BUF_SIZE = 8192
BACKLOG = 5

CRLF = '\r\n'
SERVER_HEADER = 'server: '
SYSTEM_HEADER = 'system: '


class ClientStatus(Enum):
    DISCONNECT = 0
    CONNECT = 1
    USER = 2
    PASS = 3
    PORT = 4
    PASV = 5


class ClientModel(QObject):
    def __init__(self):
        super(ClientModel, self).__init__()

        self.command_socket = None
        self.command_recevier = None

        self.status = ClientStatus.DISCONNECT

        self.file_socket = None
        self.file_ip = None
        self.file_port = None

        self.offset = 0

        # local file system
        self.localFileModel = QFileSystemModel(self)

    # help functions to communicate with server
    def push_command(self, command, argu):
        msg = command
        if argu is not None and len(argu) > 0:
            msg += " " + argu
        msg += CRLF
        self.command_socket.sendall(msg.encode())

    def getline(self):
        line = self.command_recevier.readline(BUF_SIZE + 1)
        if not line:
            raise EOFError
        if line[-2:] == CRLF:
            line = line[:-2]
        elif line[-1:] in CRLF:
            line = line[:-1]
        return line

    def recv_response(self):
        line = self.getline()
        if line[3:4] == '-':
            code = line[:3]
            while 1:
                nextline = self.getline()
                line = line + ('\n' + nextline)
                if nextline[:3] == code and \
                        nextline[3:4] != '-':
                    break
        return line

    def send_command(self, command, argu=None):
        self.push_command(command, argu)
        return SERVER_HEADER + self.recv_response()

    # standard command of FTP
    def connect(self, ip, port):
        if not self.is_valid_ipv4_by_ip_and_port(ip, port):
            return SYSTEM_HEADER + "5 invalid ip address."

        self.command_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.command_socket = socket.create_connection((ip, int(port)))
        except ConnectionRefusedError:
            return SYSTEM_HEADER + "5 fail to connect target computer."
        self.command_recevier = self.command_socket.makefile('r')

        response = self.recv_response()
        return SERVER_HEADER + response

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
        response = self.send_command("PWD")
        path = re.search(r"\".*\"", response).group()[1:-1]
        return response, path

    def cwd(self, dir_name):
        return self.send_command("CWD", dir_name)

    def syst(self):
        return self.send_command("SYST")

    def rest(self, offset):
        self.offset = offset
        return self.send_command("REST", offset)

    def quit(self):
        response = self.send_command("QUIT")
        self.status = ClientStatus.DISCONNECT
        self.command_socket.close()
        return response

    def port(self):
        self.file_socket = None
        for res in socket.getaddrinfo(None, 0, self.command_socket.family, socket.SOCK_STREAM, 0, socket.AI_PASSIVE):
            af, socktype, proto, canonname, sa = res
            try:
                self.file_socket = socket.socket(af, socktype, proto)
                self.file_socket.bind(sa)
            except OSError as _:
                if self.file_socket:
                    self.file_socket.close()
                self.file_socket = None
                continue
            break

        if self.file_socket is None:
            return SERVER_HEADER + "fail to bind socket."

        self.file_socket.listen(1)
        port = self.file_socket.getsockname()[1]  # Get proper port
        ip = self.command_socket.getsockname()[0]  # Get proper ip

        addr = self.ip_and_port_to_addr(ip, port)
        response = self.send_command("PORT", addr)
        self.status = ClientStatus.PORT
        return response

    def pasv(self):
        response = self.send_command("PASV")
        if self.get_status_code(response)[0] == '5':
            return response
        addr = re.search(r"\d{1,3},\d{1,3},\d{1,3},\d{1,3},\d{1,3},\d{1,3}", response).group()
        if not self.is_valid_ipv4_by_addr(addr):
            return SYSTEM_HEADER + "5 invalid ip address."
        ip, port = self.addr_to_ip_and_port(addr)
        self.file_ip = ip
        self.file_port = port
        self.status = ClientStatus.PASV
        return response

    def build_transfer_sock(self, msg):
        self.command_socket.send(msg.encode())
        if self.status == ClientStatus.PORT:
            sock, _ = self.file_socket.accept()
            self.file_socket.close()
            self.file_socket = None
        elif self.status == ClientStatus.PASV:
            sock = socket.create_connection((self.file_ip, self.file_port))
        else:
            raise RuntimeError
        response = SERVER_HEADER + self.recv_response()
        return sock, response

    def retr(self, filename):
        if self.status != ClientStatus.PASV and self.status != ClientStatus.PORT:
            return SYSTEM_HEADER + "5 RETR require PORT/PASV mode."

        msg = "RETR " + filename + CRLF
        sock, response = self.build_transfer_sock(msg)

        if response[0] != 5:
            file_path = os.path.join(self.cur_path, filename)
            self.recv_data(sock, file_path, self.offset)
            sock.close()
            response += SERVER_HEADER + self.recv_response()
        self.offset = 0
        self.status = ClientStatus.PASS
        return response

    def list(self):
        if self.status != ClientStatus.PASV and self.status != ClientStatus.PORT:
            return SYSTEM_HEADER + "5 LIST require PORT/PASV mode.", ""

        list_str = b''

        msg = "LIST" + CRLF
        sock, response = self.build_transfer_sock(msg)

        if response[0] != '5':
            buf = sock.recv(BUF_SIZE)
            while buf:
                list_str += buf
                buf = sock.recv(BUF_SIZE)
            sock.close()
            response += SERVER_HEADER + self.recv_response()

        return response, list_str.decode()

    def stor(self, filename):
        if self.status != ClientStatus.PASV and self.status != ClientStatus.PORT:
            return SYSTEM_HEADER + "5 STOR require PORT/PASV mode."

        file_path = os.path.join(self.cur_path, filename)

        if not os.path.isfile(file_path):
            return SYSTEM_HEADER + "5 not such file."

        msg = "STOR " + filename + CRLF
        sock, response = self.build_transfer_sock(msg)

        if response[0] != '5':
            self.send_data(sock, file_path, self.offset)
            sock.close()
            response += SERVER_HEADER + self.recv_response()

        self.offset = 0
        self.status = ClientStatus.PASS
        return response

    @staticmethod
    def get_status_code(response):
        return response.split(' ')[1]

    # help functions
    @staticmethod
    def is_valid_ipv4_by_addr(addr):
        addr_num = addr.split(',')
        if len(addr_num) != 6:
            return False

        for num in addr_num:
            try:
                num = int(num)
            except:
                return False
            if num < 0 or num > 255:
                return False
        return True

    @staticmethod
    def is_valid_ipv4_by_ip_and_port(ip, port):
        addr = ClientModel.ip_and_port_to_addr(ip, port)
        return ClientModel.is_valid_ipv4_by_addr(addr)

    @staticmethod
    def addr_to_ip_and_port(addr):
        addr = addr.split(',')
        if len(addr) < 6:
            return SYSTEM_HEADER + "5 invalid ip address."
        ip = '.'.join(addr[:4])
        port = int(addr[-2]) * 256 + int(addr[-1])
        return ip, port

    @staticmethod
    def ip_and_port_to_addr(ip, port):
        addr = ip.split('.')
        port = int(port)
        addr.append(str(port // 256))
        addr.append(str(port % 256))
        return ','.join(addr)

    @staticmethod
    def recv_data(sock, file_path, offset):
        if offset > 0:
            fp = open(file_path, "r+b")
            fp.seek(offset-1, 0)
        else:
            fp = open(file_path, "wb")

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
            sock.sendall(buf)
            buf = fp.read(BUF_SIZE)


def test_login(ftp, client):
    fr1 = ftp.connect("209.51.188.20", 21)
    # fr1 = ftp.connect("127.0.0.1", 20000)
    fr2 = ftp.sendcmd("USER anonymous")
    fr3 = ftp.sendcmd("PASS anonymous@")

    cr1 = client.connect("209.51.188.20", 21)
    # cr1 = client.connect("127.0.0.1", 20000)
    cr2 = client.send_command("USER anonymous")
    cr3 = client.send_command("PASS anonymous@")

    assert fr1 == cr1[8:]
    assert fr2 == cr2[8:]
    assert fr3 == cr3[8:]


def test_file_retr(ftp, client, filename):
    import filecmp
    ftp.retrbinary(f"RETR {filename}", open("ftp_retr", 'wb').write)

    client.send_command("TYPE I")
    client.port()
    client.retr(filename)

    assert filecmp.cmp("ftp_retr", filename)
    os.remove(filename)

    client.send_command("TYPE I")
    client.pasv()
    client.retr(filename)
    assert filecmp.cmp("ftp_retr", filename)
    os.remove(filename)

    os.remove("ftp_retr")


def test_file_stor(ftp, client, filename):
    import filecmp

    client.send_command("TYPE I")
    client.port()
    client.stor(filename)

    ftp.retrbinary(f"RETR {filename}", open("ftp_retr", 'wb').write)
    assert filecmp.cmp("ftp_retr", filename)

    ftp.delete(filename)
    os.remove("ftp_retr")

    client.send_command("TYPE I")
    client.pasv()
    client.stor(filename)

    ftp.retrbinary(f"RETR {filename}", open("ftp_retr", 'wb').write)
    assert filecmp.cmp("ftp_retr", filename)

    ftp.delete(filename)
    os.remove("ftp_retr")


def test_list_dir(ftp, client):
    def set_ftp_list(list):
        global ftp_list
        ftp_list = list.decode()

    ftp.retrbinary("LIST", set_ftp_list)

    client.pasv()
    _, list = client.list()

    assert ftp_list == list


if __name__ == '__main__':
    from ftplib import FTP
    ftp = FTP()

    client = ClientModel()

    test_login(ftp, client)
    # test_file_retr(ftp, client, "temp.c")
    # test_file_stor(ftp, client, "README.md")
    # test_list_dir(ftp, client)

    # ftp.retrbinary("LIST", print)

    pwd = client.pwd()
    print(pwd)
    print()