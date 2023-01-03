#! /usr/bin/env python3

import socket
import time

from RPi import GPIO
GPIO.setmode(GPIO.BCM)

from . import my_ip

class RelayServer():
    def __init__(self):
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        HOST, PORT = my_ip.MY_IP, 2700
        print(f'Serving on {HOST}:{PORT}')
        self.socket.bind((HOST, PORT))
        self.counter = 0
        self.setup_relays()
        try:
            print('server is running')
            self.listen_forever()
        except KeyboardInterrupt:
            pass
        finally:
            GPIO.cleanup()
            print('server closed')
    
    def setup_relays(self):
        self.relay_pins = [
            4, 17, 27, 22, 14, 15, 18, 23,
            6, 13, 19, 26, 12, 16, 20, 21
        ]
        self.relay_values = [False] * len(self.relay_pins)
        GPIO.setup(self.relay_pins, GPIO.OUT)

    def listen_forever(self):
        while True:
            message, address = self.socket.recvfrom(3)
            response = self.handle(message)
            if response:
                self.socket.sendto(response, address)
            time.sleep(0.01)

    def handle(self, message: bytes) -> bytes:
        if message[0] == 0xAA:
            # handshake
            print('handshake')
            return 0xBB.to_bytes(1, 'big') + message[1:3]

        elif message[0] == 0xCC:
            # counter query
            response = 0xCC.to_bytes(1, 'big') + (self.counter % 65536).to_bytes(2, 'big')
            print(f'have received {self.counter} frames')
            self.counter = 0
            return response

        elif message[0] == 0xDD:
            # set relays
            relay_values = int.from_bytes(message[1:3], "big")
            for i in range(16):
                self.relay_values[i] = bool(relay_values & 2**i)
            self.show_relays()
            self.counter += 1

        else:
            print(f'unhandled message {message}')

        return b''

    def show_relays(self):
        relays_on = []
        relays_off = []
        for index, value in enumerate(self.relay_values):
            pin = self.relay_pins[index]
            if pin is None: continue
            if value:
                relays_on.append(pin)
            else:
                relays_off.append(pin)
        if relays_on:
            GPIO.output(relays_on, 1)
        if relays_off:
            GPIO.output(relays_off, 0)

if __name__ == '__main__':
    RelayServer()
