#!/usr/bin/env python3

import datetime
import time

class Animation(object):
    relay_group_values = {
        'off_when_blank': False,
        'off_for_shows': False,
        'animate_between_shows': False,
        'on_show_nights': False,
    }
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'blank'

    def main(self, end_by):
        while datetime.datetime.now() < end_by:

            self.home.clear()
            self.home.show()

            for group, value in self.relay_group_values.items():
                for relay in self.home.relay_groups[group]:
                    relay.set(value)
            self.home.show_relays()

            time.sleep(1)
