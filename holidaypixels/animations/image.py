#!/usr/bin/env python3

import datetime
import os
from random import randint
import socket
import time

from PIL import Image

from ..utilities.home import Color

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'Image'

    def main(self, end_by):
        self.num_relays = self.settings.get('relays', 0)
        path = self.settings['image']
        self.fps = self.settings['fps']
        path = os.path.expanduser(path)
        self.repeat = self.settings.get('repeat', 1)
        if 'variations' in self.settings:
            path = path.format(randint(1, self.settings['variations']))
        print('Opening', path)
        image = Image.open(path)
        self.data = image.getdata()
        self.width = image.width
        self.height = image.height

        self.validate_relays()

        self.activate_relays()
        now = datetime.datetime.now()
        while now <= end_by:
            while now.minute != 0:
                print('minute is', now.minute)
                self.home.clear()
                self.home.show()
                time.sleep(1)
                now = datetime.datetime.now()
            self.present(end_by)
            time.sleep(30)
            self.activate_relays()
            now = datetime.datetime.now()

    def activate_relays(self):
        for relay in self.home.relays:
            relay.set(True)

    def validate_relays(self):
        try:
            for y in range(self.height):
                for x, relay in zip(range(self.num_relays), self.home.relays):
                    color = self.data[self.width * y + x]
                    assert color[0] == color[1] == color[2]
                    assert color[0] in (0, 255)
        except AssertionError:
            raise ValueError(f'Relay data at Row {y}, Col {x} is not black or white.')

    def present(self, end_by):
        previous_y = None
        y = 0
        width = self.width
        height = self.height

        countdown = self.settings.get('countdown', 0)
        if countdown:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("192.168.1.222", 4321))
            for i in range(countdown):
                print(countdown-i)
                time.sleep(1)
            print('go!')
            s.send(b'hello')
            s.close()

        epoch = time.time()
        while (self.repeat and (y < height * self.repeat)) or (not self.repeat and datetime.datetime.now() < end_by):
            im_y = y % height
            for x, relay in zip(range(self.num_relays), self.home.relays):
                color = self.data[width * im_y + x]
                relay.set(bool(color[0]))
            for x in range(self.num_relays, width):
                color = self.data[width * im_y + x]
                color_tup = color[0], color[1], color[2]
                self.home[x-self.num_relays] = color_tup
            self.home.show()
            while True:
                previous_y = y
                y = int((time.time() - epoch) * self.fps)
                if y != previous_y:
                    break
        print('image complete')
