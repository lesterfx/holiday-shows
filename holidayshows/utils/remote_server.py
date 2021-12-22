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
            response = self.handle(message)
            if response:
                conn.sendall(response)
            else:
                break
        conn.close()
        print('connection closed')

    def handle(self, data):
        data = json.loads(data)
        handlers = {
            'synchronize': self.synchronize,
            'play': self.play,
            'add_player': self.add_player,
            'disconnect': None
        }
        return handlers[data['function']](data['arguments'])

    def synchronize(self, arguments):
        master_time = arguments['master_time']
        my_time = time.time()
        self.time_offset = my_time - master_time
        return {'response': my_time}

    def play(self, arguments):
        index = arguments['index']
        epoch = arguments['epoch']
        print('\n'*4)
        print('received play request:', index, epoch)
        print('\n'*4)
        self.play_all(index, epoch + self.time_offset)

    def add_player(self, arguments):
        kind = arguments['kind']
        player_kind = players.PLAYER_KINDS(kind)
        player_globals = arguments['player_globals']

        self.players.add(player_kind, player_globals)

    def load_data(self, arguments):
        kind = arguments['kind']
        player_kind = players.PLAYER_KINDS(kind)
        data = arguments['data']
        self.players.load_data(player_kind, data)

def run_remote():
    print('Running Remote')
    HOST, PORT = my_ip.MY_IP, 2700
    Remote_Server(HOST, PORT)
