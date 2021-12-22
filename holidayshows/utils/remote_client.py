from enum import IntEnum
import json
import time
import socket
import struct

from . import my_ip, players

ALLOW_ERRORS = False

class Remote_Client:
    def __init__(self, name, config):
        self.name = name
        config = config
        print('configuring client for', name)
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
            response = self.send(function='synchronize', arguments={'master_time': client_time})
            server_time = response['response']
            self.time_offset = server_time - client_time
            if abs(self.time_offset) > .03:
                print()
                print()
                print()
                print(f'{self.name}: time offset:', self.time_offset)
                print()
                print()
                print()
        else:
            self.time_offset = 0

    def connect(self):
        if self.ip:
            print(f'connecting to {self.name}:{self.port}')
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.socket.connect((self.ip, self.port))
            except (ConnectionRefusedError, socket.gaierror, OSError) as e:
                print(f'error connecting to {self.ip}: {e}')
                if not ALLOW_ERRORS:
                    raise
            else:
                print(f'connected to {self.name}')
                self.connected = True
        else:
            print(f'server runs locally')

    def disconnect(self):
        if self.connected:
            self.send(function='disconnect', arguments=None, expected_response=-1)
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
            self.send(function='play', arguments={'index': index, 'epoch': epoch}, expected_response=-1)
            self.disconnect()
    
    def get_response(self):
        if not self.local:
            return self.socket.recv(1024)

    def send(self, function, arguments, expected_response=None, fallback_response=None, must_be_connected=True):
        if not self.connected:
            if must_be_connected:
                self.connect()
            else:
                return {'response': expected_response or fallback_response}
        data = json.dumps({'function': function, 'arguments': arguments}).encode()
        print(f'server ({self.name}) sending {len(data)} bytes ({str(data)[:24]}...)')
        data = struct.pack('Q', len(data)) + data
        if self.connected:
            self.socket.sendall(data)
            time.sleep(0.1)
            if expected_response == -1:
                return
            response = self.socket.recv(1024)
            print('raw_response:', response)
            response = json.loads(response.decode())
            if expected_response is not None and response != expected_response:
                raise ValueError(f'music server ({self.name}) expected {expected_response} got {response}')
            return response

    def load_data(self, kind, data):
        if self.local:
            raise NotImplementedError('cannot add player locally at this time')
        else:
            self.send(function='load_data', arguments={'kind': int(kind), 'data': data})

    def add_player(self, kind, player_globals):
        if self.local:
            self.players.add(kind, player_globals)
        else:
            self.send(function='add_player', arguments={'kind':int(kind), 'player_globals': player_globals})
