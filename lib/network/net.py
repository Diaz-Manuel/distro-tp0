import socket
from lib.serde import Message
from lib.utils import uint32_from_be, int_to_be

class MINTSocket:
    '''
    Wrapper for TCPSocket.
    Handles short-read, short-write issues and delegates de/serialization
    of messages to be sent to (or received from) the peer.
    Mint Is Not TCP.
    '''
    def __init__(self, from_socket=None):
        if from_socket:
            self.socket = from_socket
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def bind(self, *args, **kwargs):
        return self.socket.bind(*args, **kwargs)

    def listen(self, *args, **kwargs):
        return self.socket.listen(*args, **kwargs)

    def accept(self, *args, **kwargs):
        new_soc, addr = self.socket.accept(*args, **kwargs)
        return MINTSocket(new_soc), addr

    def connect(self, *args, **kwargs):
        return self.socket.connect(*args, **kwargs)

    def getpeername(self, *args, **kwargs):
        return self.socket.getpeername(*args, **kwargs)

    def recv_sized(self, size):
        """Wrapper for Socket.recv, loops until all bytes have been read
        to avoid handling short-reads everywhere.
        """
        # not very performant to do a syscall for <size> bytes
        # should read as much as possible into a buffer instead
        buffer = []
        while len(buffer) < size:
            read_bytes = self.socket.recv(size - len(buffer))
            if not read_bytes:
                # closed socket
                raise EOFError
            buffer.extend(read_bytes)
        return bytes(buffer)

    def recv(self):
        """
        """
        # max msg size supported is uint_32 max
        buffer = self.recv_sized(4)
        size = uint32_from_be(buffer)
        buffer = self.recv_sized(size)
        return Message.deserialize(buffer)

    def send(self, payload):
        byte_list = payload.serialize()
        size_bytes = int_to_be(len(byte_list))
        return self.socket.sendall(size_bytes + byte_list)


    def close(self):
        return self.socket.close()
