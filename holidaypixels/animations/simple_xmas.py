import datetime
import time

from ..utilities.home import Color

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings
        self.timer = 0

    def __str__(self):
        return 'Simple Xmas'

    def main(self, end_by):
        while datetime.datetime.now() < end_by:
            self.set_pixels()
            self.set_relays()
            self.timer += 1

    def set_relays(self):
        offset = self.timer // 30
        num_relays = len(self.home.relays_in_order)
        for i, relay in enumerate(self.home.relays_in_order):
            if offset % num_relays == i:
                relay.set(False)
            else:
                relay.set(True)
        self.home.show_relays(True)

    def set_pixels(self):
        offset = self.timer // 2
        self.home.clear()
        for x in range(self.globals.max):
            if self.home.blacked_out(x):
                continue
            pos = (x + offset) % 30
            if pos == 0:
                self.home[x] = 255, 0, 0
            elif pos == 15:
                self.home[x] = 0, 255, 0
        self.home.show()
