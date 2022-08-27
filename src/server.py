import socket
import threading


class Server:
    def __init__(self, port: int = 5050, max_msg_len: int = 1024, format: str = 'utf_8', disconnect_code: str = '102582957192'):
        self.PORT = port
        self.MAX_MSG_LEN = max_msg_len
        self.FORMAT = format
        self.DISCONNECT_CODE = disconnect_code

        self.users_connected = {}
        self.SERVER = socket.gethostbyname(socket.gethostname())
        self.ADDR = (self.SERVER, self.PORT)

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.ADDR)

    def handle_client(self, conn, addr):
        key = f"{addr[0]}x{addr[1]}"
        self.users_connected[key] = conn
        print(f"[CONNECTION] Client {addr} connected.")
        connected = True
        while connected:
            msg = conn.recv(self.MAX_MSG_LEN).decode(self.FORMAT)
            print(f"[{addr}] MSG: {msg}")
            if not msg:
                continue
            if msg == self.DISCONNECT_CODE:
                break
            for k in self.users_connected:
                if k == key:
                    continue
                self.users_connected[k].send(msg.encode(self.FORMAT))

        del self.users_connected[key]
        conn.send("[SERVER] Disconnected.".encode(self.FORMAT))
        conn.close()
        print(f"[CONNECTION] Client {addr} disconnected.")

    def start(self):
        self.server.listen()
        print(f"[SERVER] Server is listening on {self.SERVER}.")
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    s = Server()
    s.start()
