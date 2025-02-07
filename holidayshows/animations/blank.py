#!/usr/bin/env python3

import datetime
import time

class Animation(object):
    relay_group_values = {
        'off_when_blank': False,
        'off_for_shows': False,
        'animate': False,
        'on_show_nights': False,
    }
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'blank'

    def main(self, end_by):
        i = 0
        while datetime.datetime.now() < end_by:
            for group, value in self.relay_group_values.items():
                for relay in self.home.relay_groups[group]:
                    relay.set(value)
            self.home.show_relays()

            time.sleep(1)
            i += 1
            if not (i % 100):
                self.home.report_dropped_frames()
