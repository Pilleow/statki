import socket


class Client:
    def __init__(self) -> None:
        self.MAX_MSG_LEN = 1024
        self.FORMAT = 'utf-8'
        self.DISCONNECT_CODE = '102582957192'
        self.connected_addr = None
        self.await_messages = True

    def connect(self, host: str, port: int) -> None:
        self.connected_addr = (host, port)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(self.connected_addr)

    def send(self, msg):
        message = msg.encode(self.FORMAT)
        self.client.send(message)

    def disconnect(self):
        self.client.send(self.DISCONNECT_CODE.encode(self.FORMAT))
        self.await_messages = False

    def get_new_msg(self):
        return self.client.recv(self.MAX_MSG_LEN).decode(self.FORMAT)
