#!/usr/bin/env python3

import datetime
import os
from random import randint
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
        num_relays = self.settings.get('relays', 0)
        # assert num_relays <= len(self.globals.relays)
        path = self.settings['image']
        fps = self.settings['fps']
        path = os.path.expanduser(path)
        repeat = self.settings.get('repeat', 1)
        if 'variations' in self.settings:
            path = path.format(randint(1, self.settings['variations']))
        print('Opening', path)
        image = Image.open(path)
        data = image.getdata()
        width = min(image.width - num_relays, self.home.max)

        try:
            for y in range(image.height):
                for x, relay in zip(range(num_relays), self.home.relays):
                    color = data[image.width * y + x]
                    assert color[0] == color[1] == color[2]
                    assert color[0] in (0, 255)
        except AssertionError:
            raise ValueError(f'Relay data at Row {y}, Col {x} is not black or white.')

        previous_y = None
        y = 0
        width = image.width
        height = image.height

        countdown = self.settings.get('countdown', 10)
        if countdown:
            for i in range(countdown):
                print(countdown-i)
                time.sleep(1)
            print('go!')

        epoch = time.time()
        while not repeat or (y < height * repeat):
            im_y = y % height
            for x, relay in zip(range(num_relays), self.home.relays):
                color = data[width * im_y + x]
                relay.set(bool(color[0]))
            for x in range(num_relays, width):
                color = data[width * im_y + x]
                self.home[x-num_relays] = color[0], color[1], color[2]
            self.home.show()
            while True:
                previous_y = y
                y = int((time.time() - epoch) * fps)
                if y != previous_y:
                    break
        print('image complete')
