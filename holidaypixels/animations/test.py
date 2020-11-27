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
        max_ = self.globals.ranges[-1][1]
        for x in range(0, max_, 5):
            self.home[x] = Color(0, 0, 0.5)
        for x in range(0, max_, 10):
            self.home[x] = Color(0, 0.5, 0)
        for x in range(0, max_, 50):
            self.home[x] = Color(0.5, 0, 0)
        for corner in self.globals.corners:
            self.home[corner] = Color(1, 1, 1)
        while datetime.datetime.now() < end_by:
            self.home.show()
            time.sleep(1)
