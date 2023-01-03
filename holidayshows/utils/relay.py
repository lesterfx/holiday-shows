#! /usr/bin/env python3

import math
import socket
import time

class RelayClientException(Exception):
    pass

class RelayRemote(dict):
    _socket: socket.socket

    @classmethod
    def simple(cls, host):
        config = {}
        config['host'] = host
        config['relays'] = list(range(16))
        return RelayRemote(host, config)

    def __init__(self, name, config):
        self.name = name
        self.ip = config['host']
        self.invert = bool(config.get('invert', False))
        print(f'{self.name}: invert: {self.invert}')
        self.port = 2700
        for i, relay_name in enumerate(config['relays']):
            if relay_name is None: continue
            relay = Relay(self, relay_name, i)
            if relay_name in self:
                raise KeyError(f'A relay already exists with name `{relay_name}`')
            self[relay_name] = relay
        if not self:
            print(f'relay remote {name} is unused')
            return
        self.counter = 0
        self.handshake()
        self.get_frames()  # to zero it out on the server side
        self.all(0)

    def handshake(self):
        if not hasattr(RelayRemote, '_socket'):
            RelayRemote._socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

        message = 0xAA0000.to_bytes(3, 'big')
        self._socket.sendto(message, (self.ip, self.port))
        self._socket.settimeout(1)
        try:
            message, (returnIP, returnPort) = self._socket.recvfrom(3)
        except socket.timeout:
            raise RelayClientException(f'Timeout on handshake with {self.ip}:{self.port}') from None
        if int.from_bytes(message[:1], 'big') != 0xBB:
            raise RelayClientException(f'Invalid handshake message: {message}')
        message_value = int.from_bytes(message[1:3], 'big')
        print(f'{returnIP} replied with {message_value} to handshake request to {self.name}')
        self.ip = returnIP

    def get_frames(self):
        self._socket.sendto(bytes.fromhex('CC0000'), (self.ip, self.port))

        self._socket.settimeout(1)
        msg, (returnIP, returnPort) = self._socket.recvfrom(3)
        if returnIP != self.ip:
            raise RelayClientException(f'Got frame response from {returnIP}, expected {self.ip}')
        if msg[0] != 0xCC:
            raise RelayClientException(f'Invalid response from get_frames: {msg}')
        sent_count = self.counter
        self.counter = 0
        return int.from_bytes(msg[1:3], "big"), sent_count

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def show(self):
        if not self: return ''

        state = 0xDD0000
        for relay in self.values():
            if relay.value != self.invert:
                state |= (1 << relay.index)
            else:
                state &= ~(1 << relay.index)

        self._socket.sendto(state.to_bytes(3, byteorder='big'), (self.ip, self.port))
        self.counter += 1
        binary = bin(state)
        return binary[-16:].replace("0", ".").replace("1", "|")

    def all(self, value):
        for relay in self.values():
            relay.value = value
        self.show()

class Relay(object):
    def __init__(self, remote, name, index):
        self.remote = remote
        self.name = name
        self.index = index
        self.value = False
        self._timings = {False: -time.time(), True: 0.0}

    def set(self, value):
        value = bool(value)
        if value != self.value:
            now = time.time()
            self._timings[self.value] += now
            self._timings[value] -= now
            self.value = value

    @property
    def time_on(self):
        now = time.time()
        self._timings[self.value] += now
        time_on = self._timings[True]
        time_off = self._timings[False]
        self._timings[self.value] = -time.time()
        self._timings[not self.value] = 0.0
        if time_on + time_off:
            return time_on / (time_on+time_off)
        else:
            return math.nan

if __name__ == '__main__':
    boxes = []
    message = 'Add box host name: '
    while True:
        ip_ = input(message)
        message = 'Add box host name: (Return if done) '
        if ip_:
            boxes.append(RelayRemote.simple(ip_))
        else:
            break
    if len(boxes):
        delay = 1
        dropped = False
        while True:
            print(f'Testing with delay of {delay} seconds')
            for on in True, False:
                for box in boxes:
                    for relay in range(16):
                        box[relay].set(on)
                        print(f'{box}: {box.show()}')
                        time.sleep(delay)
            for box in boxes:
                try:
                    delivered, sent = box.get_frames()
                except:
                    print('Dropped getting frame count')
                    dropped = True
                    break
                print('{} of {} frames delivered successfully'.format(delivered, sent))
                if sent != delivered: dropped = True
            if not dropped:
                delay /= 2
                time.sleep(delay*2)
            else:
                break
        print(f'Frames dropped at delay of {delay} seconds')
        print('Test complete')
