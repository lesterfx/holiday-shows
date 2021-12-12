#!/usr/bin/env python3

from __future__ import print_function, division

from collections import defaultdict
import datetime
import json
from pprint import pprint
import socket
import struct
import time

from rpi_ws281x import Adafruit_NeoPixel

from . import relay_client

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

class Strip_Cache_Player():
    def __init__(self, config):
        self.strip = StripWrapper(config)
        self.image_data = defaultdict(lambda: None)
        self.relay_data = defaultdict(lambda: None)
        
    def load_image(self, index, image_data):
        self.image_data[index] = image_data

    def load_relays(self, index, relay_data):
        self.relay_data[index] = relay_data

    def play(self, index, repeat, end_by, epoch, fps):
        height = len(self.image_data[index])
        if repeat:
            print(f'playing at {fps} fps {repeat} times, starting at {datetime.datetime.fromtimestamp(epoch)} and ending at {datetime.datetime.fromtimestamp(epoch + height * fps)}')
        else:
            print(f'playing at {fps} fps on loop until {datetime.datetime.fromtimestamp(end_by)}, at {fps} fps')
        abs_y = 0
        if epoch and epoch > time.time():
            time.sleep(epoch - time.time())
        while (repeat and (abs_y < height * repeat)) or (not repeat and time.time() < end_by):
            y = abs_y % height

            if self.relay_data[index]:
                if self.relay_data[index] == 'cycle':
                    for x, name in enumerate(self.relays):
                        self.home.relays[name].set((abs_y//fps) % len(self.relays) != x)
                else:
                    relay_row = self.relay_data[index][y]
                    for x, name in enumerate(self.relays):
                        self.home.relays[name].set(relay_row[x])
                self.home.show_relays()

            image_row = self.image_data[index][y]
            for x, color in enumerate(image_row):
                self.strip[x] = color

            self.strip.show()

            while True:
                previous_y = abs_y
                abs_y = int((time.time() - epoch) * fps)
                if abs_y != previous_y:
                    break

        print('image complete')
        self.strip.clear(True)

    def stop(self):
        self.strip.clear(True)

class Strip_Remote_Server():
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
                conn.sendall(b'ok')
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
        pprint(strip_data)
        self.player = Strip_Cache_Player(strip_data)
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

class Strip_Remote_Client():
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
            self.player = Strip_Cache_Player(self.config)

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
            self.send(b'disconnect', expected_response=b'ok')
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
            for row in image_data:
                for pixel in row:
                    assert all(type(x) == int for x in pixel)
                    pattern += 'BBB'
                    data += pixel
            packed = struct.pack(pattern, *data)
            print('sending image to remote')
            self.send(b'load_image:' + packed, expected_response=b'ok')
            print('sent!')
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
                print('no response expected')
                return
            response = self.socket.recv(1024)
            if expected_response is not None and response != expected_response:
                raise ValueError(f'{self.name} ({self.ip}) expected {expected_response} got {response}')
            return response

class Relay_Remote(dict):
    def __init__(self, name, config, client):
        self.client = client
        self.name = name
        ip = config.ip
        port = config.port
        for i, relay_name in enumerate(config.relays):
            if relay_name is None: continue
            relay = Relay(self, relay_name, i)
            self[relay_name] = relay
        if not self: return
        self.client_index = client.append(ip, port)
        self.all(0)

    def __hash__(self):
        return hash(self.name)

    def show(self):
        if not self: return ''
        for relay in self.values():
            self.client.set_relay(self.client_index, relay.index, relay.value)
        return self.client.send_state(self.client_index)
    
    def all(self, value):
        for relay in self.values():
            relay.value = value
        self.show()

class Relay(object):
    def __init__(self, remote, name, index):
        self.remote = remote
        self.name = name
        self.index = index
        self.value = 0

    def set(self, value):
        self.value = int(bool(value))

    def show(self):
        self.remote.show()

class StripWrapper(object):
    def __init__(self, strip_prefs):
        length = strip_prefs.length
        pin = strip_prefs.pin
        frequency = strip_prefs.frequency
        dma = strip_prefs.dma
        invert = strip_prefs.invert
        brightness = strip_prefs.brightness
        pin_channel = strip_prefs.pin_channel
        self.black = []
        for black in strip_prefs.black:
            self.black.append(range(black[0], black[1]))

        self.real_strip = Adafruit_NeoPixel(length, pin, frequency, dma, invert, brightness, pin_channel)
        self.real_strip.begin()

        pixel_order = strip_prefs.pixel_order.lower()

        self.shift = [1<<((2-pixel_order.index(x))*8) for x in 'rgb']
        self.delay = self.calculate_delay(length)
        print('minimum time between frames:', self.delay)
        print('maximum fps:', 1/self.delay)
        self.next_available = 0

        self.fps_timer = time.time()
        self.fps_count = 0
        self.relay = None

    @property
    def on(self):
        return self.relay and self.relay.value

    def calculate_delay(self, pixels):
        # about 1ms per 100 bytes
        # 100 bytes == 33 pixels
        # 1ms per 33 pixels
        return 0.001 * pixels/33 * 1.3
        # 1.3 multiplier just in case

    def map(self, r, g, b):
        return (
            r * self.shift[0] +
            g * self.shift[1] + 
            b * self.shift[2]
        )

    def __setitem__(self, x, rgb):
        for black in self.black:
            if x in black:
                return
        if rgb:
            value = self.map(*rgb)
        else:
            value = 0
        self.real_strip.setPixelColor(x, value)

    def clear(self, show=False):
        for x in range(self.real_strip.numPixels()):
            self.real_strip.setPixelColor(x, 0)
        if show:
            self.show()

    def show(self):
        need_to_wait = self.next_available - time.time()
        if need_to_wait > 0:
            time.sleep(need_to_wait)
        self.real_strip.show()
        self.next_available = time.time() + self.delay
        self.print_fps()

    def print_fps(self):
        now = time.time()
        if now - self.fps_timer >= 1:
            print(f'\r{self.fps_count} fps (on: {self.on})')
            self.fps_count = 0
            self.fps_timer = now
        self.fps_count += 1


class Home(object):
    def __init__(self, globals_):
        self.globals = globals_
        self.init_relays()
        self.init_strips()
        self.clear()
        self.show()

    def init_strips(self):
        print('Initializing Strips')
        self.strips = {}
        for strip_config in self.globals.strips:
            strip = Strip_Remote_Client(strip_config)
            self.strips[strip.name] = strip
            if strip.ip is None:
                self.local_strip = strip
                self.local_strip.player.home = self
                # shortcut for "old code" that doesn't use severs
                self.strip = self.strips[strip_config.name].player.strip
                self.strip.relay = self.relays.get('strips')

    def init_relays(self):
        self.relay_client = relay_client.RelayClient()

        self.relays = {}
        self.remotes = {}
        for name, config in self.globals.relay_remotes.items():
            remote = Relay_Remote(name, config, self.relay_client)
            self.remotes[name] = remote
            self.relays.update(remote)
        self.relay_client.handshake_all()
        self.relay_groups = {}
        for name in [
            'off_when_blank',
            'off_for_shows',
            'animate_between_shows',
            'on_show_nights'
        ]:
            self.relay_groups[name] = []
            for relay_name in self.globals.relay_purposes.get(name, []):
                self.relay_groups[name].append(self.relays[relay_name])
    
    def show_relays(self):
        for remote in self.remotes.values():
            labels = remote.show()
            print(remote.name, labels, end=' ')
        print()

    def __enter__(self):
        self.show_relays()
        return self

    def cleanup(self):
        self.clear()
        self.show()
        for strip in self.strips:
            self.strips[strip].disconnect()
        self.clear_relays()

    def __exit__(self, *args, **kwargs):
        self.cleanup()
        print('Complete')
    
    @staticmethod
    def run_for(seconds, function, *args, **kwargs):
        end = time.time() + seconds
        while time.time() < end:
            function(*args, **kwargs)

    def clear(self, show=False):
        self.strip.clear(show)
    
    def clear_relays(self):
        for remote in self.remotes.values():
            remote.all(False)

    def show(self):
        self.strip.show()

    def __setitem__(self, key, value):
        key = int(key)
        if key not in self: return
        self.strip[key] = value or 0

    def __del__(self):
        try:
            self.clear(True)
        except:
            pass

def run_remote(StripRemotePrefs):
    print('Running Remote')
    HOST, PORT = MY_IP, 2700
    Strip_Remote_Server(HOST, PORT, StripRemotePrefs)
