import os
import socket

from pygame import mixer

import socket
import struct
import time

from . import my_ip


class Music_Server:
    def __init__(self, HOST, PORT):
        print(f'Serving on {HOST}:{PORT}')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((HOST, PORT))

        self.load_music()

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
            b'synchronize': self.synchronize,
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
        while time.time() < epoch:
            time.sleep(0.01)
        song = self.songs[index]
        if song:
            song.play()
        
    def load_music(self):
        songs = [
            None,
            '/Users/michael/Documents/development/xmas/music/sugarplum.mp3',
            '/Users/michael/Documents/development/xmas/music/sarajevo.mp3'
        ]
        mixer.init()
        self.songs = []
        for song in songs:
            if song is None:
                self.songs.append(None)
                continue
            if not os.path.exists(song):
                raise OSError(f'song does not exist: {song}')
            self.songs.append(mixer.Sound(song))

def run_remote():
    print('Running Remote')
    HOST, PORT = my_ip.MY_IP, 2700
    Music_Server(HOST, PORT)
