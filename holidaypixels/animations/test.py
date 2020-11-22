#!/usr/bin/env python3

import datetime
import random
import time

from ..utilities import physics
from ..utilities.home import Home, Color, Pixel

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'Test'

    def main(self, end_by):
        colors = [
            Color(0, 0, 0),
            Color(0, 0, 0),
            Color(0, 0, 1),
            Color(0, 0, 0),
            Color(0, 0, 0),
            Color(0, 1, 0),
            Color(0, 0, 0),
            Color(0, 0, 0),
            Color(1, 0, 0),
            Color(0, 0, 0),
            Color(0, 0, 0),
            Color(1, 1, 0),
            Color(0, 0, 0),
            Color(0, 0, 0),
            Color(1, 0, 1),
            Color(0, 0, 0),
            Color(0, 0, 0),
            Color(0, 1, 1),
        ]
        for t in range(1000):
            for x in range(450, 750):
                self.home[x] = colors[(x + t) % len(colors)]
            self.home.show()
            print('test')
            time.sleep(1)

        max_ = self.globals.ranges[-1][1]
        for x in range(0, max_, 5):
            self.home[x] = Color(0, 0, 1)
        for x in range(0, max_, 10):
            self.home[x] = Color(0, 1, 0)
        for x in range(0, max_, 50):
            self.home[x] = Color(1, 0, 0)
        for range_ in self.globals.ranges:
            self.home[range_[0]] = Color(1, 1, 1)
            self.home[range_[1]-1] = Color(1, 1, 1)
        while datetime.datetime.now() < end_by:
            self.home.show()
            time.sleep(1)
