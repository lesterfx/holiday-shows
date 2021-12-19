import json
import time
import socket
import struct

from . import my_ip


class Music_Client:
    def __init__(self, config):
        self.config = config
        self.ip = config['ip']
        if self.ip == my_ip.MY_IP:
            self.ip = None
        if self.ip is not None:
            assert self.ip
            self.ip = config['ip']
            self.port = config['port']

        self.connected = False
        self.connect()
        self.synchronize()
        time.sleep(1)

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
            print(f'{self.name}: connecting to {self.ip}:{self.port}')
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.socket.connect((self.ip, self.port))
            except (ConnectionRefusedError, socket.gaierror, OSError) as e:
                print(f'{self.name} ({self.ip}) connection error: {e}')
            else:
                print(f'{self.name} ({self.ip}) connected')
                self.connected = True
        else:
            print(f'{self.name}: this strip runs locally')

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
        if self.ip:
            self.send(b'play:' + struct.pack('id', index, epoch), expected_response=-1)
            self.disconnect()
        else:
            raise NotImplementedError('cannot play locally at this time')
    
    def get_response(self):
        if self.ip:
            return self.socket.recv(1024)

    def send(self, data, expected_response=None, fallback_response=None, must_be_connected=True):
        if not self.connected:
            if must_be_connected:
                self.connect()
            else:
                return expected_response or fallback_response
        print(f'{self.name} ({self.ip}) sending {len(data)} bytes ({str(data)[:24]}...)')
        data = struct.pack('Q', len(data)) + data
        if self.connected:
            self.socket.sendall(data)
            time.sleep(0.1)
            if expected_response == -1:
                return
            response = self.socket.recv(1024)
            if expected_response is not None and response != expected_response:
                raise ValueError(f'{self.name} ({self.ip}) expected {expected_response} got {response}')
            return response

