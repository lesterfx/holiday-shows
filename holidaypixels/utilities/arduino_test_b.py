#!/usr/bin/env python3

from itertools import count
import socket
import sys
import time

class ArduinoTest:
    def __init__(self):
        self.setup()
        self.cycle()

    def cycle(self):
        start = time.time()
        counted = 0
        for i in count():
            counted += 1
            now = time.time()
            if now - start > 1:
                fps = counted / (now - start)
                if fps < 3:
                    raise Exception('FPS is too low: {}'.format(fps))
                print(f'                     {fps:.5f} fps')
                start = now
                counted = 0
            for sock in self.socks:
                # i = 0
                msg = f'all0,{(i % 16):02d}:1\n'
                print('>', msg, end='')
                sock.send(msg.encode())
                received = ''
                while 'OK' not in received:
                    data = sock.recv(1024)
                    print(data)
                    received += data.decode()
                print('<', received, end='')

    def setup(self):
        ips = ['192.168.1.240'] # , '192.168.1.241', '192.168.1.242']
        self.socks = []
        for ip in ips:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print('connecting to', ip)
            sock.connect((ip, 270))
            # sock.setblocking(False)
            self.socks.append(sock)
            # time.sleep(0.03)

ArduinoTest()
