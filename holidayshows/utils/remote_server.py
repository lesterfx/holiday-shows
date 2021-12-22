import json
import socket
import struct
import time

from . import my_ip, players

class Remote_Server:
    def __init__(self, HOST, PORT):
        print(f'Serving on {HOST}:{PORT}')
        self.delay = 0
        self.time_offset = 0
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((HOST, PORT))
        self.players = players.Players()
        try:
            while True:
                self.listen()
        except KeyboardInterrupt:
            pass
        finally:
            self.sock.close()
            for player in self.players.values():
                player.stop()
            print('Remote Server closed')

    def listen(self):
        self.sock.listen(1)
        print('Players:', list(self.players))
        print('waiting for connection')
        conn, addr = self.sock.accept()
        print('accepted connection from', addr)
        while 1:
            print(f'Waiting for message from {addr}')
            message = b''
            while len(message) < 8:
                message += conn.recv(8 - len(message))
            message_length = struct.unpack('Q', message)[0]
            message = b''
            while len(message) < message_length:
                message += conn.recv(message_length - len(message))
            if message == b'disconnect':
                print('disconnecting')
                break
            response = self.handle(message)
            if response:
                conn.sendall(response)
            else:
                break
        conn.close()
        print('connection closed')

    def handle(self, data):
        options = {
            b'synchronize': self.synchronize,
            b'play': self.play,
            b'add_player': self.add_player
        }
        for key in options:
            if data.startswith(key + b':'):
                handler = options[key]
                response = handler(data[len(key)+1:])
                print(f'successfully handled {key}. replying with:', response)
                if key == b'play':
                    return
                return response
        else:
            raise NotImplementedError(data)

    def synchronize(self, data):
        master_time = struct.unpack('d', data)[0]
        my_time = time.time()
        self.time_offset = my_time - master_time
        return struct.pack('d', my_time)

    def play(self, data):
        index, epoch = struct.unpack('id', data)
        print('\n'*4)
        print('received play request:', index, epoch)
        print('\n'*4)
        self.play_all(index, epoch + self.time_offset)

    def add_player(self, data):
        kind = struct.unpack('b', data[:1])[0]
        player_kind = players.PLAYER_KINDS(kind)
        player_globals = json.loads(data[1:])

        self.players.add(player_kind, player_globals)


def run_remote():
    print('Running Remote')
    HOST, PORT = my_ip.MY_IP, 2700
    Remote_Server(HOST, PORT)
