#!/usr/bin/env python3

import datetime
import socket

from pygame import mixer

SOUND_FILE = '/Users/michael/Documents/xmas1.mp3'

mixer.init()
sound = mixer.Sound(SOUND_FILE)


# create an INET, STREAMing socket
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind the socket to a public host, and a well-known port
serversocket.bind(('192.168.1.222', 4321))
# become a server socket
serversocket.listen(5)

last_ip = None
try:
    while True:
        print('waiting for signal')
        clientsocket, (ip, port) = serversocket.accept()
        print('received connection from', ip, 'at', datetime.datetime.now())
        if last_ip and ip != last_ip:
            print('rejecting connection from different ip:', ip)
        elif not last_ip:
            last_ip = ip
        clientsocket.recv(2048)
        sound.play()
        print('music started at', datetime.datetime.now())
finally:
    serversocket.close()
