import datetime
import time

from ..utilities.home import Color

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'Simple Xmas'

    def main(self, end_by=None):
        while True:
            offset = int(time.time() % 10)
            for x in range(self.globals.max):
                pos = (x + offset) % 10
                self.home.clear()
                if pos == 0:
                    self.home[x] = 255, 0, 0
                elif pos == 5:
                    self.home[x] = 255, 255, 255
            self.home.show()
            if end_by is None:
                return
            elif datetime.datetime.now() >= end_by:
                break
