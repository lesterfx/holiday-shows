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
                print(f'            {fps:.5f} fps')
                start = now
                counted = 0
            for sock in self.socks:
                # i = 0
                if i % 2 == 0:
                    msg = 'all0\n'
                else:
                    msg = 'all1\n'
                # msg = f'{(i % 16):02d}:0,{((i+1) % 16):02d}:1\n'
                while not self.ready_to_receive(sock):
                    print('waiting')
                    time.sleep(0.01)
                print('>', msg, end='')
                sock.send(msg.encode())

    def ready_to_receive(self, sock):
        try:
            data = sock.recv(1024)
        except BlockingIOError:
            return False
        print('<', data.decode(), end='')
        return True

    def wait_for_ready(self, sock):
        while not self.ready_to_receive(sock):
            time.sleep(0.001)

    def setup(self):
        ips = ['192.168.3.241']#, '192.168.3.240', '192.168.3.242']
        ips = ['192.168.1.17']
        self.socks = []
        for ip in ips:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print('connecting to', ip)
            sock.connect((ip, 270))
            # sock.setblocking(False)
            self.socks.append(sock)
            sock.send(b'all0\n')
            # time.sleep(0.03)

ArduinoTest()
