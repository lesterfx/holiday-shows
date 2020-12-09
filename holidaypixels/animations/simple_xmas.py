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

    def main(self, end_by=None):
        if end_by:
            for relay in self.home.relays:
                relay.set(True)
        while True:
            self.set_pixels()
            self.set_relays()
            time.sleep(0.1)
            self.timer += 1
            if end_by is None:
                return
            elif datetime.datetime.now() >= end_by:
                break
    
    def set_relays(self):
        offset = self.timer // 10
        num_relays = len(self.home.relays)
        for i, relay in enumerate(self.home.relays):
            if offset % num_relays == i:
                relay.set(False)
            else:
                relay.set(True)

    def set_pixels(self):
        offset = self.timer // 3
        self.home.clear()
        for x in range(self.globals.max):
            if self.home.blacked_out(x):
                continue
            pos = (x + offset) % 10
            if pos == 0:
                self.home[x] = 255, 0, 0
            elif pos == 5:
                self.home[x] = 0, 255, 0
        self.home.show()
