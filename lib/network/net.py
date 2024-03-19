import socket
from lib.network import serde
from lib.network.utils import uint32_from_le, int_to_le

class OTPSocket:
    '''
    Wrapper for TCPSocket.
    Handles short-read, short-write issues and delegates de/serialization
    for the transmission of simple key-value pairs through the network.
    keys must be strings and values must be strings or ints.
    '''
    def __init__(self, underlying_socket=None):
        if underlying_socket:
            self.socket = underlying_socket
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def bind(self, *args, **kwargs):
        return self.socket.bind(*args, **kwargs)

    def listen(self, *args, **kwargs):
        return self.socket.listen(*args, **kwargs)

    def accept(self, *args, **kwargs):
        new_soc, addr = self.socket.accept(*args, **kwargs)
        return OTPSocket(new_soc), addr

    def connect(self, *args, **kwargs):
        return self.socket.connect(*args, **kwargs)

    def getpeername(self, *args, **kwargs):
        return self.socket.getpeername(*args, **kwargs)

    def recv_sized(self, size):
        buffer = []
        while len(buffer) < size:
            read_bytes = self.socket.recv(size - len(buffer))
            if not read_bytes:
                # closed socket
                raise EOFError
            buffer.extend(read_bytes)
        return buffer

    def recv(self):
        # max msg size supported is uint_32 max
        buffer = self.recv_sized(4)
        size = uint32_from_le(buffer)
        buffer = self.recv_sized(size)
        return serde.deserialize(buffer)

    def send(self, obj):
        byte_list = serde.serialize(obj)
        size_bytes = int_to_le(len(byte_list))
        return self.socket.sendall(size_bytes + byte_list)


    def close(self):
        return self.socket.close()
