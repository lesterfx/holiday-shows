import datetime
import time

from ..utilities.home import Color

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'Relay Tester'

    def main(self, end_by=None):
        self.home.strip.on = False
        while datetime.datetime.now() < end_by:
            for relay in self.home.relays:
                print(relay.pin_number)
                for _ in range(10):
                    relay.set(True)
                    time.sleep(.8)
                    relay.set(False)
                    time.sleep(.2)
