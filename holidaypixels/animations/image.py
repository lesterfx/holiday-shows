#!/usr/bin/env python3

import datetime
import os
from PIL import Image
import time

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'Image'

    def main(self, end_by):
        num_relays = self.settings.get('relays', 0)
        assert num_relays <= len(self.globals.relays)
        path = self.settings['image']
        fps = self.settings['fps']
        path = os.path.expanduser(path)
        image = Image.open(path)
        data = image.getdata()
        width = min(image.width - num_relays, self.home.max)

        try:
            for y in range(image.height):
                for x, relay in enumerate(self.home.relays):
                    color = data[image.width * y + x]
                    assert color[0] == color[1] == color[2]
                    assert color[0] in (0, 255)
        except AssertionError:
            raise ValueError(f'Relay data at Row {y}, Col {x} is not black or white.')

        for i in range(5):
            print(5-i)
            time.sleep(1)
        print('go!')

        y = 0
        epoch = time.time()
        while y < image.height:
            for x, relay in enumerate(self.home.relays):
                color = data[image.width * y + x]
                assert color[0] == color[1] == color[2]
                assert color[0] in (0, 255)
                relay.set(color[0] > 0)
            for x in range(num_relays, width - num_relays):
                color = data[image.width * y + x]
                self.home.strip[x] = color[0], color[1], color[2]
            self.home.strip.show()
            self.home.print_fps()
            y = int((time.time() - epoch) * fps)
        print('image complete')
