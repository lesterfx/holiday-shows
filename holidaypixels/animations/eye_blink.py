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
        return 'Eye Blink'

    def main(self, end_by):
        color1 = Color(1, 1, .8)
        color2 = Color(1, .1, 0)
        fade = random.random()
        color = color1 * fade + color2 * (1-fade)
        distance = random.randrange(*self.settings['distance_range'])
        center = random.randrange(self.globals.ranges[0][0] + distance, self.globals.ranges[0][1]-distance)
        for _ in range(random.randrange(*self.settings['blinks_range'])):
            self._show_eyes_once(center, distance, color)

    def _show_eyes_once(self, center, distance, color):
        fade_in_frames = self.settings['fade_in_frames']
        print('open')
        for i in range(fade_in_frames):
            self.home[center+distance] = color * (i/fade_in_frames)
            self.home[center-distance] = color * (i/fade_in_frames)
            self.home.show()
        self.home.sleep(random.uniform(*self.settings['open_time_range']))
        self.home.clear(True)
        print('close')
        self.home.sleep(random.uniform(*self.settings['closed_time_range']))