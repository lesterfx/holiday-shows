#!/usr/bin/env python3

import datetime
import time

from ..utilities import home

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'blank'

    def main(self, end_by):
        while datetime.datetime.now() < end_by:
            self.home *= 0
            self.home.show(force=True)
            time.sleep(1)

if __name__ == '__main__':
    main()
