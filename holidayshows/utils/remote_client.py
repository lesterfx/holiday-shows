from enum import IntEnum
import json
import time
import socket
import struct

from . import my_ip, players

ALLOW_ERRORS = False

class Remote_Client:
    def __init__(self, config):
        config = config
        print('configuring client for remote:', config)
        self.ip = config['ip']
        self.port = config['port']
        self.local = False
        if self.ip == my_ip.MY_IP:
            self.ip = None
            self.local = True
            self.players = players.Players()

        self.connected = False
        self.connect()
        self.synchronize()

    def __del__(self):
        self.disconnect()
    
    def synchronize(self):
        '''
        sends time to remote and gets time back. offset is stored on remote, but printed here too
        '''
        if self.ip:
            client_time = time.time()
            packed = struct.pack('d', client_time)
            response = self.send(b'synchronize:' + packed, fallback_response=packed)
            server_time = struct.unpack('d', response)[0]
            self.time_offset = server_time - client_time
            if abs(self.time_offset) > .03:
                print()
                print()
                print()
                print(f'{self.ip}: time offset:', self.time_offset)
                print()
                print()
                print()
        else:
            self.time_offset = 0

    def connect(self):
        if self.ip:
            print(f'connecting to {self.ip}:{self.port}')
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.socket.connect((self.ip, self.port))
            except (ConnectionRefusedError, socket.gaierror, OSError) as e:
                print(f'error connecting to {self.ip}: {e}')
                if not ALLOW_ERRORS:
                    raise
            else:
                print(f'connected to {self.ip}')
                self.connected = True
        else:
            print(f'server runs locally')

    def disconnect(self):
        if self.connected:
            self.send(b'disconnect', expected_response=-1)
            self.socket.close()
            self.connected = False

    def play(self, index, epoch):
        '''
        plays the indexed song, starting at epoch, which should be in the future
        time offset will be applied to epoch and end_by on remote
        '''
        if self.local:
            raise NotImplementedError('cannot play locally at this time')
        else:
            self.send(b'play:' + struct.pack('id', index, epoch), expected_response=-1)
            self.disconnect()
    
    def get_response(self):
        if not self.local:
            return self.socket.recv(1024)

    def send(self, data, expected_response=None, fallback_response=None, must_be_connected=True):
        if not self.connected:
            if must_be_connected:
                self.connect()
            else:
                return expected_response or fallback_response
        print(f'server ({self.ip}) sending {len(data)} bytes ({str(data)[:24]}...)')
        data = struct.pack('Q', len(data)) + data
        if self.connected:
            self.socket.sendall(data)
            time.sleep(0.1)
            if expected_response == -1:
                return
            response = self.socket.recv(1024)
            if expected_response is not None and response != expected_response:
                raise ValueError(f'music server ({self.ip}) expected {expected_response} got {response}')
            return response

    def load_data(self, kind, data_bytes):
        if self.local:
            raise NotImplementedError('cannot add player locally at this time')
        else:
            self.send(b'load_data:' + struct.pack('b', int(kind)) + data_bytes)

    def add_player(self, kind, player_globals):
        if self.local:
            self.players.add(kind, player_globals)
        else:
            self.send(b'add_player:' + struct.pack('b', int(kind)) + json.dumps(player_globals).encode())
