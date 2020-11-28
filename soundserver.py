#!/usr/bin/env python3

import socket

from pygame import mixer

SOUND_FILE = '/Users/michael/Documents/xmas1.mp3'

mixer.init()
sound = mixer.Sound(SOUND_FILE)


# create an INET, STREAMing socket
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# bind the socket to a public host, and a well-known port
serversocket.bind(('192.168.1.222', 4323))
# become a server socket
serversocket.listen(5)

last_address = None
try:
    while True:
        print('waiting for signal')
        (clientsocket, address) = serversocket.accept()
        print('received connection from', address)
        if last_address and address != last_address:
            print('rejecting connection from different address:', address)
        elif not last_address:
            last_address = address
        clientsocket.recv(2048)
        sound.play()
        print('music has started')
finally:
    serversocket.close()
