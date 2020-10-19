from enum import Enum

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


class ProcessHeader(Enum):
    Local = 0
    Direction = 1
    Remote = 2
    Size = 3
    StartTime = 4
    EndTime = 5
    Status = 6
    Btn = 7


class FileHeader(Enum):
    Name = 0
    Size = 1
    Type = 2
    LastMod = 3
    Mode = 4
    Owner = 5


class ClientMode(Enum):
    PORT = 0
    PASV = 1


class FileType(Enum):
    File = 'File'
    Folder = 'Folder'


class TransferStatus(Enum):
    Running = 'Running'
    Paused = 'Paused'
    Finished = 'Finished'
    Canceled = 'Canceled'
    Failed = 'Failed'
