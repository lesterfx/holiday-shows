#!/usr/bin/env python3

import datetime
import random
import time

from ..utilities import home

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'Flag'

    def main(self, end_by):
        red = home.Color(1,0,0)
        white = home.Color(1,1,.6)
        blue = home.Color(0,0,1)
        center = self.settings['center']
        blues = range(*self.settings['blue_range'])
        every = self.settings['every']
        fade = self.settings['fade']
        offset = 0
        while datetime.datetime.now() < end_by:
            self.home *= fade
            offset = (offset + 1) % every
            end = max(center-self.globals.ranges[0][0], self.globals.ranges[0][1]-center)
            for i in range(offset-every, end+1, every//2):
                if i < 0: continue
                for sign in (-1, 1):
                    x = center + i*sign
                    if bool((i-offset - every//2) % every) != (sign < 0):
                        if x in blues:
                            color = blue
                        else:
                            color = red
                    else:
                            color = white
                    self.home[x] = color
            self.home.show()

if __name__ == '__main__':
    main()
