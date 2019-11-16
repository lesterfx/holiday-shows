#!/usr/bin/env python3

from __future__ import print_function

import argparse
import datetime
from collections import namedtuple
import importlib
from itertools import count
import json
import math
from operator import itemgetter, methodcaller
import os
import sys
import time
import traceback

import board
import neopixel

from holidaypixels.utilities import sun, home

GlobalPrefs = namedtuple('GlobalPrefs', ['corners', 'pin', 'pixel_order', 'ranges', 'brightness', 'relay'])
SchedulePrefs = namedtuple('SchedulePrefs', ['location', 'start_time', 'sunset_offset', 'end_time', 'dusk_brightness', 'dusk_duration'])

class CalendarEntry(object):
    def __init__(self, entry):
        today = datetime.date.today()

        self.start = datetime.datetime.strptime(entry['start'], '%B %d').date().replace(year=today.year)
        self.end = datetime.datetime.strptime(entry['end'], '%B %d').date().replace(year=today.year)

        self.days = frozenset(datetime.datetime.strptime(day, '%A').weekday() for day in entry.get('days', []))
        self.animation = frozenset(entry['animation'])
        
        self.name = entry['name']

    def __repr__(self):
        return self.name

    def iter(self):
        today = datetime.date.today()
        if self.end < self.start:
            # crosses december 31, so end next year instead of this year
            extrayear = 1
        else:
            extrayear = 0
        for year in count(today.year):
            start = self.start.replace(year=year)
            end = self.end.replace(year=year+extrayear)
            day = start
            if day < today:
                day = today
            while day <= end:
                if self.days:
                    if day.weekday() in self.days:
                        yield day
                else:
                    yield day
                day += datetime.timedelta(1)

class Holiday_Pixels(object):
    def __init__(self):
        self.sun = sun.Sun()
        self.load_args()
        config = self.load_config()
        self.process_config(config)
        if self.args.demo:
            self.demo(self.args.demo)
        else:
            self.main()

    def main(self):
        for event_start, event in self.iter():
            print()
            print(f'Next event: {event}')
            event_end = datetime.datetime.combine(event_start.date(), self.schedule.end_time)
            print(f'Starts at {event_start}')
            self.sleep_until(event_start)
            print(f'Running {event} until {event_end}')
            self.run(event_end, *event.animation)

    def demo(self, *animation):
        self.run(datetime.datetime.now() + datetime.timedelta(minutes=self.args.minutes), *animation)

    def run(self, until, *animation_names):
        animations = []
        try:
            console = (self.args.display == 'console')
            strip = home.Home(self.globals, console=console)
        except RuntimeError as err:
            print(err)
            print('To preview in console, run with flag "--display console"')
            return
        with strip as h:
            for animation in animation_names:
                module = importlib.import_module('.' + animation, 'holidaypixels.animations')
                settings = self.animations.get(animation, {})
                animation = module.Animation(h, self.globals, settings)
                animations.append(animation)
            while datetime.datetime.now() < until:
                for animation in animations:
                    print(f'Running {animation}')
                    try:
                        animation.main(until)
                    except KeyboardInterrupt:
                        raise
                    except:
                        print(traceback.format_exc())
                        print('Continuing in 10 seconds...')
                        time.sleep(10)

    def sleep_until(self, event):
        while True:
            now = datetime.datetime.now()
            if now > event:
                return
            duration = event - now
            sleep = duration.total_seconds() * .75
            print(f'Sleeping for {sleep:.0f} seconds')
            time.sleep(sleep)

    def get_start_time(self, date):
        if self.schedule.start_time:
            return datetime.datetime.combine(date, self.schedule.start_time)
        else:
            return datetime.datetime.combine(date, self.get_sunset(date)) + self.schedule.sunset_offset

    def get_sunset(self, date):
        utc_date = self.utc_time_from_local_time(date)
        sunset = self.sun.getSunsetTime(self.schedule.location, utc_date=utc_date)
        hour = sunset['hr']
        minute = sunset['min']
        hour, minute = divmod(sunset['decimal'], 1)
        minute *= 60
        time = datetime.time(hour=int(hour), minute=int(minute))
        sunset_utc = datetime.datetime.combine(utc_date, time)
        sunset_local = self.local_time_from_utc_time(sunset_utc)
        return sunset_local.time()
        
    def local_time_from_utc_time(self, utc_time):
        return utc_time + self.local_utc_offset(utc_time)

    def utc_time_from_local_time(self, local_time):
        return local_time - self.local_utc_offset(local_time)

    def local_utc_offset(self, epoch_time):
        epoch = time.mktime(epoch_time.timetuple())
        offset = datetime.datetime.fromtimestamp(epoch) - datetime.datetime.utcfromtimestamp(epoch)
        return offset

    def iter(self):
        cals = [[None, entry.iter(), entry] for entry in self.calendar]
        for cal in cals:
            cal[0] = next(cal[1])
        date = None
        while True:
            cals.sort(key=itemgetter(0))
            event = cals[0]
            event_date, date_generator, entry = event
            event_start = self.get_start_time(event_date)
            yield event_start, entry
            event[0] = next(date_generator)

    def process_config(self, config):
        self.process_globals(config['globals'])
        self.process_schedule(config['schedule'])
        self.process_calendar(config['calendar'])
        self.process_animations(config['animations'])

    def process_globals(self, globals_):
        corners = [int(corner) for corner in globals_['corners']]
        pin = getattr(board, 'D{}'.format(int(globals_['pin'])))
        pixel_order = getattr(neopixel, globals_['pixel_order'])
        ranges = [(int(min_range), int(max_range)) for min_range, max_range in globals_['ranges']]
        brightness = max(0, min(int(globals_['brightness']), 255))
        relay = getattr(board, 'D{}'.format(int(globals_['relay'])))
        self.globals = GlobalPrefs(corners, pin, pixel_order, ranges, brightness, relay)

    def process_schedule(self, schedule):
        lat, lon = schedule['location']
        location = {'latitude': float(lat), 'longitude': float(lon)}
        start_time = schedule['start_time']
        if start_time == 'sunset':
            start_time = None
            offset = schedule['sunset_offset']
            sign = offset[0]
            hours, minutes = map(int, offset[1:].split(':'))
            sunset_offset = datetime.timedelta(hours=hours, minutes=minutes)
            if sign == '+':
                pass
            elif sign == '-':
                sunset_offset = -sunset_offset
            else:
                raise ValueError("First digit of sunset_offset must be + or -")
        else:
            hour, minute = map(int, start_time.split(':'))
            start_time = datetime.time(hour, minute)
            sunset_offset = None
        end_time = schedule['end_time']
        hour, minute = map(int, end_time.split(':'))
        end_time = datetime.time(hour, minute)
        dusk_brightness = max(0, min(int(schedule['dusk_brightness']), 255))
        dusk_duration = schedule['dusk_duration']
        hours, minutes = map(int, dusk_duration.split(':'))
        dusk_duration = datetime.timedelta(hours=hours, minutes=minutes)
        self.schedule = SchedulePrefs(location, start_time, sunset_offset, end_time, dusk_brightness, dusk_duration)

    def process_calendar(self, calendar):
        self.calendar = set()
        for entry in calendar:
            entry = CalendarEntry(entry)
            self.calendar.add(entry)

    def process_animations(self, animations):
        self.animations = animations

    def load_args(self):
        parser = argparse.ArgumentParser(description='Holiday Lights')
        parser.add_argument('--reset', const=True, choices=['force'], nargs='?', default=False, help='Create a sample config file if one does not exist')
        parser.add_argument('--config', default=self.config_path, help='Path to config file')
        parser.add_argument('--demo', help='Run named animation immediately')
        parser.add_argument('--minutes', default=1, type=int, help='How many minutes to run demo')
        parser.add_argument('--display', choices=['gpio', 'console'], default='gpio', help='Where to render the animation')
        self.args = parser.parse_args()
        print(self.args)

    def load_config(self):
        config = json.load(open(self.default_config_path))
        config_path = self.args.config
        print('Config file path:')
        print(config_path)
        if self.args.reset == 'force' or not os.path.exists(config_path):
            if self.args.reset:
                print('Saving default config file.')
                with open(config_path, 'w') as config_file:
                    json.dump(config, config_file, indent=4)
            else:
                print('File not found.')
                print('To auto-populate run with argument "--reset"')
                raise Exit
        else:
            if self.args.reset:
                print('Reset argument passed, but config file already exists. Use "--reset force" to make a new config')
                raise Exit
            print('Loading config')
            with open(config_path) as config_file:
                self.merge_config(config, json.load(config_file))
        return config

    @property
    def config_path(self):
        return os.path.join(os.path.expanduser('~'), '.holiday-pixels-config.json')

    @property
    def default_config_path(self):
        return os.path.join(os.path.dirname(__file__), 'default_config.json')

    def merge_config(self, config, override):
        def merge_dict(base, update):
            base_keys = set(base.keys())
            update_keys = set(update.keys())
            invalid_keys = update_keys - base_keys
            if invalid_keys:
                msg = 'Unexpected key(s) {}'.format(' '.join(invalid_keys))
                raise KeyError(msg)
            for key in update_keys:
                if isinstance(base[key], dict):
                    merge_dict(base[key], update[key])
                else:
                    base[key] = update[key]

class Exit (Exception):
    pass

def main():
    try:
        Holiday_Pixels()
    except Exit:
        sys.exit()

if __name__ == '__main__':
    main()
