#!/usr/bin/env python3

import argparse
import datetime
from collections import namedtuple
import importlib
import json
from operator import itemgetter
import os
import sys
import time
import traceback

from holidayshows.utils import calendar_entry, home, remote_server, relay_server, sun

class Holiday_Pixels(object):
    def __init__(self):
        self.sun = sun.Sun()
        self.load_args()
        if self.args.remote:
            self.run_pixel_server()
        elif self.args.relays:
            self.run_relay_server()
        else:
            config = self.load_config()
            self.process_config(config)
            self.init_home()
            try:
                if self.args.demo:
                    self.demo(self.args.demo)
                else:
                    self.main()
            except KeyboardInterrupt:
                pass
            finally:
                print('cleaning up')
                self.home.cleanup()

    def run_pixel_server(self):
        remote_server.run_remote()

    def run_relay_server(self):
        relay_server.RelayServer()

    def init_home(self):
        self.home = home.Home(self.globals)
            
    def main(self):
        for event_start, event in self.iter():
            print()
            event_end = datetime.datetime.combine(event_start.date(), self.schedule['end_time'])
            print(f'{event_start} starts {event}')
            self.run(event_start, 'blank')
            self.run(event_end, *event.animation)

    def demo(self, *animation):
        if self.args.until:
            hour, minute = map(int, self.args.until.split(':'))
            until = datetime.datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        else:
            if not self.args.minutes and not self.args.seconds:
                self.args.minutes = 10
            until = datetime.datetime.now() + datetime.timedelta(minutes=self.args.minutes, seconds=self.args.seconds)
        self.run(until, *animation)

    def run(self, until, *animation_names):
        animations = []
        with self.home as home:
            for animation in animation_names:
                settings = self.animations.get(animation, {})
                animation = settings.get('module', animation)
                module = importlib.import_module('.' + animation, 'holidayshows.animations')
                settings.update(self.settings_overrides)
                animation = module.Animation(home, self.globals, settings)
                animations.append(animation)
            while datetime.datetime.now() < until:
                for animation in animations:
                    print(f'{until} ends {animation}')
                    home.report_dropped_frames()
                    animation.main(until)
                    print()

    def get_start_time(self, date):
        if self.schedule['start_time']:
            return datetime.datetime.combine(date, self.schedule['start_time'])
        else:
            return datetime.datetime.combine(date, self.get_sunset(date)) + self.schedule['sunset_offset']

    def get_sunset(self, date):
        utc_date = self.utc_time_from_local_time(date)
        sunset = self.sun.getSunsetTime(self.schedule['location'], utc_date=utc_date)
        print('sunset:', sunset)
        hour = sunset['hr']
        minute = sunset['min']
        hour, minute = divmod(sunset['decimal'], 1)
        minute *= 3600
        minute, second = divmod(minute, 60)
        time = datetime.time(hour=int(hour), minute=int(minute), second=int(second))
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
        if self.args.norelays:
            globals_['relays'] = []
        # relay_order = globals_['relay_order']
        strips = self.process_strips(globals_['strips'])
        relay_remotes = self.process_relay_remotes(globals_['relay_remotes'])
        remotes = self.process_remotes(globals_['remotes'])
        music_server = globals_['music_server']
        self.globals = {
            'relay_remotes': relay_remotes,
            # 'relay_order': relay_order,
            'strips': strips,
            'relay_purposes': globals_['relay_purposes'],
            'remotes': remotes,
            'music_server': music_server
        }

    def process_remotes(self, remotes):
        ret = {}
        for name, config in remotes.items():
            ret[name] = {'host': config['host'], 'port': config['port']}
        return ret

    def process_relay_remotes(self, remotes):
        return {name: {'name': name, 'invert': remote.get('invert', False), 'host': remote['host'], 'relays': remote['relays']} for name, remote in remotes.items()}

    def process_strips(self, strips):
        processed_strips = []
        for name, strip in strips.items():
            processed_strips.append({
                'name': name,
                'pin': strip['pin'],
                'pixel_order': strip['pixel_order'],
                'frequency': strip['frequency'],
                'dma': strip['dma'],
                'invert': strip['invert'],
                'pin_channel': strip['pin_channel'],
                'brightness': strip['brightness'],
                'length': strip['length'],
                'black': strip.get('black', [])
            })
        return processed_strips

    def process_strip(self, strip):
        pin = int(strip['pin'])
        pixel_order = strip['pixel_order'].lower()
        brightness = max(0, min(int(strip['brightness']), 255))
        frequency = int(strip['frequency'])
        dma = int(strip['dma'])
        invert = bool(strip['invert'])
        pin_channel = int(strip['pin_channel'])
        relay = strip['relay']
        return {
            'pin': pin,
            'pixel_order': pixel_order,
            'brightness': brightness,
            'frequency': frequency,
            'dma': dma,
            'invert': invert,
            'pin_channel': pin_channel,
            'relay': relay
        }

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
            if sign == '-':
                sunset_offset = -sunset_offset
            elif sign != '+':
                raise ValueError("First digit of sunset_offset must be + or -")
        else:
            hour, minute = map(int, start_time.split(':'))
            start_time = datetime.time(hour, minute)
            sunset_offset = None
        end_time = schedule['end_time']
        hour, minute = map(int, end_time.split(':'))
        end_time = datetime.time(hour, minute)
        self.schedule = {
            'location': location,
            'start_time': start_time,
            'sunset_offset': sunset_offset,
            'end_time': end_time
        }

    def process_calendar(self, calendar):
        self.calendar = set()
        for entry in calendar:
            entry = calendar_entry.CalendarEntry(entry)
            self.calendar.add(entry)

    def process_animations(self, animations):
        if self.args.settings:
            self.settings_overrides = json.loads(self.args.settings)
        else:
            self.settings_overrides = {}
        self.animations = animations

    def load_args(self):
        parser = argparse.ArgumentParser(description='Holiday Lights')
        parser.add_argument('--reset', const=True, choices=['force'], nargs='?', default=False, help='Create a sample config file if one does not exist')
        parser.add_argument('--config', default=self.config_path, help='Path to config file')
        parser.add_argument('--demo', help='Run named animation immediately')
        parser.add_argument('--until', default='', help='When to stop demo')
        parser.add_argument('--minutes', default=0, type=int, help='How many minutes to run demo')
        parser.add_argument('--seconds', default=0, type=int, help='How many seconds to run demo')
        parser.add_argument('--norelays', action='store_true', help="Don't turn on relays")
        parser.add_argument('--settings', help="JSON style settings dictionary of temporary overrides")
        parser.add_argument('--remote', action='store_true', help="Run a remote pixel server. All other options are ignored.")
        parser.add_argument('--relays', action='store_true', help="Run a relay box server. All other options are ignored.")
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
                config = json.load(config_file)
                # self.merge_config(config, json.load(config_file))
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
