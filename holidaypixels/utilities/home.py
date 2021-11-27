#!/usr/bin/env python3

from __future__ import print_function, division

import logging
import socket
import socketserver
import struct
import time

import board
import digitalio
from rpi_ws281x import Adafruit_NeoPixel, Color as WS_Color

from . import consolepixel, imagepixel, relay_client

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

GAMMA = 1

class Color (object):
    def __init__(self, r, g=None, b=None, luma=1, mode='over'):
        if g is None: g = r
        if b is None: b = r
        self.r = r
        self.g = g
        self.b = b
        self.luma = luma
        self.mode = mode

    @property
    def color(self):
        return tuple(map(self.channelmap, self.tuple))

    def channelmap(self, x):
        clamped = min(1, max(0, x))
        scaled = int(clamped ** GAMMA * 255)
        return scaled

    @property
    def tuple(self):
        return (
            self.r*self.luma,
            self.g*self.luma,
            self.b*self.luma
        )

    def __imul__(self, other):
        self.r *= other
        self.g *= other
        self.b *= other
        return self

    def __mul__(self, other):
        return Color(
            r=self.r * other,
            g=self.g * other,
            b=self.b * other,
            luma=self.luma,
            mode=self.mode
        )

    def __idiv__(self, other):
        self *= 1 / other
        return self

    def __div__(self, other):
        return self * (1 / other)

    __floordiv__ = __div__
    __truediv__ = __div__

    def __iadd__(self, other):
        self.r += other.r*other.luma
        self.g += other.g*other.luma
        self.b += other.b*other.luma
        return self

    def __add__(self, other):
        return Color(
            r=self.r + other.r*other.luma,
            g=self.g + other.g*other.luma,
            b=self.b + other.b*other.luma,
            mode=self.mode,
            luma=self.luma
        )

    def __isub__(self, other):
        self.r -= other.r*other.luma
        self.g -= other.g*other.luma
        self.b -= other.b*other.luma
        return self

    def __or__(self, other):
        if isinstance(other, Color):
            other = (
                other.r * other.luma,
                other.g * other.luma,
                other.b * other.luma
            )
        return Color(
            r=max(self.r, other[0]),
            g=max(self.g, other[1]),
            b=max(self.b, other[2]),
            mode=self.mode,
            luma=self.luma
        )
    
    def __ror__(self, other):
        if isinstance(other, int):
            return self
        return self | other

    def __eq__(self, other):
        return self.tuple == other.tuple

    def __repr__(self):
        color = self.tuple
        return f'{color[0]:.04f},{color[1]:.04f},{color[2]:.04f} ({self.luma:.04f})'

    def copy(self):
        return Color(*self.tuple)

class Pixel(object):
    def __init__(self, position, color, strip):
        self.strip = strip
        self.position = position
        self.color = color
        self.deleted = False

    def draw(self):
        if not self.deleted and 0 <= self.position < len(self.strip):
            self.strip[self.position] = self.color
            return 1
        else:
            return 0

    def delete(self):
        if self.on_delete:
            self.on_delete(self)
        self.deleted = True

    def __lt__(self, other):
        return self.position < other.position

class Strip_Cache_Player():
    def __init__(self, config):
        self.strip = StripWrapper(config)
        self.cache = []
    
    def load(self, data):
        self.cache = data
        
    def play(self, end_by, epoch, repeat):
        pass

class Strip_Remote_Server(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024)
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)

        if data.startswith(b'sync:'):
            self.sync(data[5:])
        else:
            raise NotImplementedError(data)
    
    def sync(self, data):
        client_time = struct.unpack('d', data)[0]
        server_time = time.time()
        self.time_offset = server_time - client_time
        self.request.sendall(struct.pack('d', server_time))

class Strip_Remote_Client():
    def __init__(self, config):
        self.name = config.name
        self.ip = config.ip
        if self.ip is None:
            self.player = Strip_Cache_Player(config)
        else:
            assert self.ip
            self.ip = config.ip
            self.port = config.port

    def connect(self):
        if self.ip:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.socket.connect((self.ip, self.port))
            except (ConnectionRefusedError, socket.gaierror, OSError) as e:
                print(f'{self.name} ({self.ip}) connection error: {e}')
                return
            else:
                print(f'{self.name} ({self.ip}) connected')
                client_time = time.time()
                self.socket.send(b'sync:' + struct.pack('d', client_time))
                server_time = struct.unpack('d', self.socket.recv(1024))[0]
                print(f'{self.ip}: server_time - client_time:', server_time - client_time)
                self.socket.setblocking(False)
                self.connected = True

    def load(self, data):
        pass

    def play(self, end_by, epoch, repeat):
        pass

    def send(self, data):
        if self.connected:
            self.socket.sendall(data)




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
        if not len(self): return
        self.client_index = client.append(ip, port)
        # self._ok_to_send = True
        # self.sock = self.connect()
        # self.deficit = 0
        self.all(0)

    def __hash__(self):
        return hash(self.name)

    # def connect(self):
    #     if len(self):
    #         print(f'{self.name} {len(self)} relays: {", ".join(self.keys())}')
    #         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         try:
    #             self.conn = sock.connect((self.ip, self.port))
    #         except (ConnectionRefusedError, socket.gaierror, OSError) as e:
    #             print(f'{self.name} ({self.ip}) connection error: {e}')
    #             return
    #         else:
    #             print(f'{self.name} ({self.ip}) connected')
    #         sock.setblocking(False)
    #         return sock
    #     else:
    #         print(f'{self.name} has no relays')

    def send(self, *msgs, force=False):
        if not hasattr(self, 'client_index'): return
        for relay in self.values():
            self.client.set_relay(self.client_index, relay.index, relay.value)
        self.client.send_state(self.client_index)
        return
        if not self.sock: return
        if msgs:
            msg = b' '.join(msgs) + b'\n'
            msg_str = msg.decode().strip()
            if self.ok_to_send or force:
                self.deficit += 1
                self.sock.send(msg)
                print(f'{self.name} ({self.ip}) > {msg_str}')
                self.ok_to_send = False
                return True
            else:
                print(f'{self.name} ({self.ip}) > {msg_str} (not ready)')
                return False

    # @property
    # def ok_to_send(self):
    #     if not self._ok_to_send:
    #         try:
    #             resp = self.sock.recv(1024)
    #         except BlockingIOError:
    #             self._ok_to_send = False
    #         else:
    #             self.deficit -= resp.count(b'\n')
    #             print(f'                           deficit: {self.deficit}')
    #             # if self.deficit <= 0:
    #             #     self._ok_to_send = True  # maybe? untested
    #             self._ok_to_send = True
    #     return self._ok_to_send
    
    # @ok_to_send.setter
    # def ok_to_send(self, value):
    #     self.response = b''
    #     self._ok_to_send = value

    def show(self, wait_if_busy=False, force=False):
        msgs = []
        for relay in self.values():
            # if relay.changed:
                msgs.append(relay.msg)
        # if wait_if_busy:
        #     while not self.ok_to_send:
        #         time.sleep(0.001)
        self.send(*msgs, force=force)
            # for relay in self.values():
                # if relay.changed:
                    # relay.changed = False
    
    def all(self, value):
        for relay in self.values():
            relay.value = value
        self.send(b'all1' if value else b'all0')
            # for relay in self.values():
                # relay.changed = False

class Relay(object):
    def __init__(self, remote, name, index):
        self.remote = remote
        self.name = name
        self.index = index
        self.value = 0
        self.changed = False

    def set(self, value):
        value = int(bool(value))
        if self.value != value:
            self.value = value
            self.changed = True
    
    @property
    def msg(self):
        return (f'{self.index:02d}:{self.value}').encode()
    
    def show(self, wait_if_busy=False):
        logger.debug(f'inefficient relay showing: {self.name} {self.value}')
        self.remote.show(wait_if_busy)

class StripWrapper(object):
    def __init__(self, strip_prefs):
        length = strip_prefs.length
        pin = strip_prefs.pin
        frequency = strip_prefs.frequency
        dma = strip_prefs.dma
        invert = strip_prefs.invert
        brightness = strip_prefs.brightness
        pin_channel = strip_prefs.pin_channel

        self.real_strip = Adafruit_NeoPixel(length, pin, frequency, dma, invert, brightness, pin_channel)
        self.real_strip.begin()

        pixel_order = strip_prefs.pixel_order.lower()

        self.cached = [(0, 0, 0)] * length
        self.shift = [1<<((2-pixel_order.index(x))*8) for x in 'rgb']
        print('rgb shift:', self.shift)
        self.delay = self.calculate_delay(length)
        print('minimum time between frames:', self.delay)
        self.next_available = 0

    @property
    def on(self):
        # return self.relay.value
        print('Deprecated strip relay getter called!')
        return True

    @on.setter
    def on(self, value):
        print('Deprecated strip relay setter called!')
        # self.relay.set(value)
        # self.relay.show(True)  # TODO: potentially inefficient

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
        # self.cached[x] = rgb
        if rgb:
            value = self.map(*rgb)
        else:
            value = 0
        self.real_strip.setPixelColor(x, value)

    # def __getitem__(self, x):
    #     return self.cached[x]

    def show(self):
        need_to_wait = self.next_available - time.time()
        if need_to_wait > 0:
            # print('need to wait', need_to_wait)
            time.sleep(need_to_wait)
        self.real_strip.show()
        self.next_available = time.time() + self.delay

class Home(object):
    def __init__(self, globals_):
        self.globals = globals_
        self.max = self.globals.ranges[-1][-1]
        self.init_relays()
        self.init_strip()
        # self.cache = [None] * len(self)
        # self.previous = None
        self.clear()
        self.fps_count = 0
        self.fps_timer = time.time()
        self.show()

    def init_strip(self):
        print('Initializing Strip')
        self.strips = {}
        for strip in self.globals.strips:
            self.strips[strip.name] = Strip_Remote_Client(strip)
            if strip.ip is None:
                # shortcut for "old code" that doesn't use severs
                self.strip = self.strips[strip.name].player.strip

    def init_relays(self):
        self.relay_client = relay_client.RelayClient()

        self.relays = {}
        self.remotes = {}
        for name, config in self.globals.relay_remotes.items():
            remote = Relay_Remote(name, config, self.relay_client)
            self.remotes[name] = remote
            self.relays.update(remote)
        self.relay_client.handshake_all()
        self.relays_in_order = []
        self.remotes_used_in_order = set()
        for name in self.globals.relay_order:
            self.relays_in_order.append(self.relays[name])
            self.remotes_used_in_order.add(self.relays[name].remote)
    
    def set_relays_in_order(self, value, wait_if_busy=False):
        for relay in self.relays_in_order:
            relay.set(value)
        self.show_relays(wait_if_busy)
    
    def show_relays(self, wait_if_busy=False, force=False):
        for remote in self.remotes.values():
            remote.show(wait_if_busy, force)

    def __enter__(self):
        self.strip.on = True
        return self

    def __exit__(self, *args, **kwargs):
        print('Complete')
        self.clear()
        self.clear_relays()
        self.show()
        self.strip.on = False

    def sleep(self, seconds):
        if hasattr(self, 'fps'):
            frames = int(seconds * self.fps)
            print(f'sleep for {frames} frames')
            for _ in range(frames):
                self.strip.show()
        else:
            time.sleep(seconds)

    def run_every(self, seconds, function):
        def func(*args, **kwargs):
            now = time.time()
            func.run_tries += 1
            run = False
            if hasattr(self, 'fps'):
                if func.run_tries == self.fps * func.seconds:
                    run = True
                    func.run_tries = 0
            else:
                if now - func.last_run >= func.seconds:
                    run = True
                    func.last_run = now
            if run:
                return function(*args, **kwargs)
        func.last_run = time.time()
        func.run_tries = 0
        func.seconds = seconds

        return func
    
    def blacked_out(self, x):
        for blackout in self.globals.black:
            if x in range(blackout[0], blackout[-1]+1):
                return True
        return False

    @staticmethod
    def run_for(seconds, function, *args, **kwargs):
        end = time.time() + seconds
        while time.time() < end:
            function(*args, **kwargs)

    def round_up(self, every):
        return ((len(self) + every - 1) // every) * every

    def clear(self, show=False):
        for i in range(len(self)):
            self[i] = None
        if show:
            self.show()
    
    def clear_relays(self):
        for remote in self.remotes.values():
            remote.all(False)

    def print_fps(self):
        now = time.time()
        if now - self.fps_timer >= 1:
            print(f'\r{self.fps_count} fps (on: {self.strip.on})')
            self.fps_count = 0
            self.fps_timer = now
        self.fps_count += 1

    def show(self, force=True):
        self.print_fps()
        self.strip.show()

    def __setitem__(self, key, value):
        key = int(key)
        if key not in self: return
        if isinstance(value, Color):
            if value.mode == 'over':
                self.strip[key] = value.color
            elif value.mode == 'add':
                raise NotImplementedError
                self.strip[key] += value
            elif value.mode == 'max':
                self.strip[key] = (self.strip[key] | value).color
        else:
            self.strip[key] = value or 0

    def __contains__(self, key):
        key = int(key)
        for range_ in self.globals.ranges:
            if range_[0] <= key <= range_[1]:
                return True
        return False

    def __len__(self):
        return self.max+1

    def __del__(self):
        try:
            self.clear(True)
        except:
            pass

    def __imul__(self, other):
        for i, pixel in enumerate(self.strip):
            if pixel:
                self.strip[i] = (Color(*pixel) * other).color
                # pixel *= other
        return self

    def __isub__(self, other):
        for pixel in self.strip:
            pixel -= other
        return self
