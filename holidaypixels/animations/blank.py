#!/usr/bin/env python3

import datetime
import time

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'blank'

    def main(self, end_by):
        while datetime.datetime.now() < end_by:
            self.home.strip.on = False
            self.home.clear()
            self.home.show()
            self.home.show_relays()
            time.sleep(1)
