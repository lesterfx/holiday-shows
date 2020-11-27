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
        max_ = self.globals.max
        # digits = len(bin(max_)) - 1
        # for x in range(0, max_, digits):
        #     num = bin(x)[2:]
        #     for i, val in enumerate(num):
        #         if val == '1':
        #             self.home[x+i] = Color(1, 0, 0)
        #         elif val == '0':
        #             self.home[x+i] = Color(0, 1, 0)

        for corner in self.globals.corners:
            self.home[corner] = Color(0, 0, 1)
        for black in self.globals.black:
            for x in range(black[0], black[-1]):
                self.home[x] = Color(1, 1, 1)

        while datetime.datetime.now() < end_by:
            self.home.show()
            time.sleep(1)
