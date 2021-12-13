import json
import time
import socket
import struct

from . import strip_cache_player, progress_bar

def my_ip():
    # https://stackoverflow.com/a/28950776/3130539
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip
MY_IP = my_ip()


class Strip_Remote_Client:
    def __init__(self, config):
        self.config = config
        self.name = config.name
        self.ip = config.ip
        if self.ip == MY_IP:
            self.ip = None
        if self.ip is not None:
            assert self.ip
            self.ip = config.ip
            self.port = config.port
            self.strip_config = config

        self.connected = False
        self.connect()
        self.synchronize()
        time.sleep(1)
        self.init_strip()

    def __del__(self):
        self.disconnect()
    
    def load_relays(self, index, relay_data):
        '''
        stores all relays' animations for the indexed song
        this doesn't make sense for remotes, since they're all sent over the same network anyway
        '''
        if self.ip:
            raise ValueError('Cannot play back relays on remote client')
        self.player.load_relays(index, relay_data)

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

    def init_strip(self):
        '''
        sends the strip config to the remote
        TODO should we use struct pack here?
        '''
        if self.ip:
            self.send(b'init_strip:' + json.dumps(self.config).encode(), expected_response=b'ok')
        else:
            self.player = strip_cache_player.Strip_Cache_Player(self.config)

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

    def load_image(self, index, image_data):
        '''
        sends the full pixel animation for the indexed song to the remote
        '''
        if self.ip:
            width = len(image_data[0])
            height = len(image_data)
            print(f'{self.name}: loading image {index} ({width}x{height})')
            data = [index, width, height]
            pattern = 'iii'
            with progress_bar.ProgressBar(len(image_data)) as bar:
                for i, row in enumerate(image_data):
                    bar.update(i)
                    for pixel in row:
                        assert all(type(x) == int for x in pixel)
                        pattern += 'BBB'
                        data += pixel
            packed = struct.pack(pattern, *data)
            self.send(b'load_image:' + packed, expected_response=b'ok')
        else:
            self.player.load_image(index, image_data)

    def play(self, index, repeat, end_by, epoch, fps):
        '''
        plays the indexed song, starting at epoch, which should be in the future
        time offset will be applied to epoch and end_by on remote
        '''
        if self.ip:
            self.send(b'play:' + struct.pack('ibddb', index, repeat, end_by, epoch, fps), expected_response=-1)
            self.disconnect()
        else:
            self.player.play(index, repeat, end_by, epoch, fps)
    
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

