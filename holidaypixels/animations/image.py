#!/usr/bin/env python3

import datetime
import os
from PIL import Image
import time

from ..utilities.home import Home, Color, Pixel

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'Image'

    def main(self, end_by):
        path = self.settings['path']
        fps = self.settings['fps']
        path = os.path.expanduser(path)
        image = Image.open(path)
        data = image.getdata()
        epoch = time.time()
        y = 0
        while y < image.height:
            width = min(image.width, self.home.max)
            for x in range(width):
                color = data[image.width * y + x]
                self.home.strip[x] = color[0], color[1], color[2]
            self.home.strip.show()
            self.home.print_fps()
            y = int((time.time() - epoch) * fps)
