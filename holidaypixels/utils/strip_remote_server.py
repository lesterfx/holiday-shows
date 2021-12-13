import json
import socket
import struct
import time

from . import strip_cache_player, my_ip

class Strip_Remote_Server:
    def __init__(self, HOST, PORT, StripRemotePrefs):
        self.StripRemotePrefs = StripRemotePrefs
        print(f'Serving on {HOST}:{PORT}')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((HOST, PORT))
        try:
            while True:
                self.listen()
        except KeyboardInterrupt:
            pass
        finally:
            self.sock.close()
            if hasattr(self, 'player'):
                self.player.stop()
            print('Strip Remote Server closed.')

    def listen(self):
        self.sock.listen(1)
        print('waiting for connection')
        conn, addr = self.sock.accept()
        print('accepted connection from', addr)
        while 1:
            print(f'Waiting for message (connected to {addr})')
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

    def handle(self, data):
        options = {
            b'init_strip': self.init_strip,
            b'synchronize': self.synchronize,
            b'load_image': self.load_image,
            b'play': self.play
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

    def init_strip(self, data):
        strip_data = self.StripRemotePrefs(*json.loads(data))
        self.player = strip_cache_player.Strip_Cache_Player(strip_data)
        return b'ok'
    
    def synchronize(self, data):
        master_time = struct.unpack('d', data)[0]
        my_time = time.time()
        self.time_offset = my_time - master_time
        return struct.pack('d', my_time)

    def load_image(self, data):
        index, width, height = struct.unpack('iii', data[:12])
        data = data[12:]
        flat_pixel_data = struct.unpack('BBB'*width*height, data)
        image_data = []
        for y in range(height):
            row = []
            rowstart = y * width * 3
            for x in range(width):
                pixelstart = rowstart + x*3
                pixel = flat_pixel_data[pixelstart:pixelstart+3]
                row.append(pixel)
            image_data.append(row)
        self.player.load_image(index, image_data)
        return b'ok'

    def play(self, data):
        index, repeat, end_by, epoch, fps = struct.unpack('ibddb', data)
        end_by += self.time_offset
        epoch += self.time_offset
        self.player.play(index, repeat, end_by, epoch, fps)
        return b'ok'

def run_remote(StripRemotePrefs):
    print('Running Remote')
    HOST, PORT = my_ip.MY_IP, 2700
    Strip_Remote_Server(HOST, PORT, StripRemotePrefs)
