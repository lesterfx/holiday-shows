#!/usr/bin/env python3

import datetime
import importlib
import os
from pprint import pprint
from random import randint, shuffle
import time

from PIL import Image
from pygame import mixer

from ..utilities.home import Color
from . import simple_xmas

class Animation(object):
    def __init__(self, home, globals_, settings):
        mixer.init()
        self.home = home
        self.globals = globals_
        self.settings = settings
        music = self.settings.get('music')
        if music:
            self.sound = mixer.Sound(music)
            self.silence = mixer.Sound('/home/pi/pixels/holidaypixels/utilities/pop.mp3')
        else:
            self.sound = None
            self.silence = None

    def __str__(self):
        return 'Image'
    
    def load_resources(self, element):
        path = element['image']
        self.relays = element['relays']
        for relay in self.relays:
            if relay not in self.home.relays:
                raise ValueError(f'Relay {relay} is not defined in the home.')
        path = os.path.join(os.path.dirname(__file__), '..', path)
        path = os.path.realpath(path)
        if 'variations' in self.settings:
            path = path.format(randint(1, self.settings['variations']))
        print()
        print('Loading image:', path)
        image = Image.open(path)
        self.image = image.getdata()
        self.width = image.width
        self.height = image.height
        self.data = {}
        self.home.local_strip.load_relays(self.validate_relays())
        for key, options in element['strips'].items():
            start = len(self.relays) + options['start']
            end = len(self.relays) + options['end']
            slice = self.slice_image(start, end)
            print('Slice loaded:', key)
            self.home.strips[key].load_image(slice)
            self.data[key] = slice

        music = element['music']
        if music:
            print('Loading music:', music)
            self.sound = mixer.Sound(music)
            self.silence = mixer.Sound('/home/pi/pixels/holidaypixels/utilities/pop.mp3')
        else:
            print('No music')
            self.sound = None
            self.silence = None
        print()

        self.fps = element['fps']


    def main(self, end_by):
        self.repeat = self.settings.get('repeat', 1)

        animation = self.settings['intermediate_animation']
        waiting_module = importlib.import_module('.' + animation, 'holidaypixels.animations')

        if self.settings.get('days'):
            days = set(self.settings['days'])
        else:
            days = None
        if self.settings['minute']:
            waitfor_minute = int(self.settings['minute'])
            waitfor_second = int(self.settings.get('second', 0))
        else:
            now = datetime.datetime.now()
            now += datetime.timedelta(seconds=2)
            waitfor_minute = now.minute
            waitfor_second = now.second

        while True:
            now = datetime.datetime.now().replace(second=0, microsecond=0)
            self.activate_relays(True)
            waiting = waiting_module.Animation(self.home, self.globals, self.settings)
            if days is None or now.strftime('%A') in days:
                until = now.replace(minute=waitfor_minute, hour=now.hour, second=waitfor_second, microsecond=0)
                if until < now:
                    until += datetime.timedelta(hours=1)
                if until > end_by:
                    print('LAST SHOW ENDED', animation, 'until night time:', end_by)
                    waiting.main(end_by)
                    return
                else:
                    print(animation, 'until', until)
                    waiting.main(until - datetime.timedelta(seconds=5))
            else:
                print(animation, 'until night time:', end_by)
                waiting.main(end_by)
                return
            
            self.activate_relays(True)
            if self.settings.get('shuffle'):
                shuffle(self.settings['elements'])
            for element in self.settings['elements']:
                self.load_resources(element)
                self.activate_relays(False)
                try:
                    self.present(end_by, epoch=until.timestamp())
                finally:
                    if self.sound:
                        self.sound.stop()
                time.sleep(10)
            time.sleep(20)

    def activate_relays(self, active=True):
        self.home.set_relays_in_order(active, True)

    def slice_image(self, start, end):
        image_slice = []
        for y in range(self.height):
            row = []
            for x in range(start, end):
                color = self.image[self.width * y + x]
                color_rgb = color[0], color[1], color[2]
                row.append(color_rgb)
            image_slice.append(row)
        return image_slice

    def validate_relays(self):
        relay_data = []
        for y in range(self.height):
            row = []
            for x, name in enumerate(self.relays):
                color = self.image[self.width * y + x]
                if not (color[0] == color[1] == color[2]) or color[0] not in (0, 255):
                    for row in relay_data:
                        print(''.join(['-','X'][c] for c in row))
                    raise ValueError(f'Relay data at Row {y}, Col {x} ({name}) is ({color[0]}, {color[1]}, {color[2]}). Must be black or white.')
                elif color[0] == 0:
                    row.append(False)
                else:
                    row.append(True)
            relay_data.append(row)
        return relay_data

    def present(self, end_by, epoch=None):
        self.home.strip.on = True
        self.home.clear()
        self.home.show()
        self.home.show_relays(True)

        countdown = self.settings.get('countdown', 0)
        if countdown > 3:
            if self.silence:
                self.silence.play()
            for i in range(countdown -2):
                print(countdown-i)
                time.sleep(1)
        if not self.sound:
            early = epoch - time.time()
            if early > 0:
                print('early by', early, 'seconds. sleeping')
                time.sleep(early)
            else:
                print('not early. late by', early, 'seconds')
        else:
            epoch = time.time() + 2 + self.globals.audio_delay
            for key in self.data:
                self.home.strips[key].play(self.repeat, end_by, epoch)
            while time.time() < epoch - self.globals.audio_delay:
                time.sleep(0.001)
            self.sound.play()
            time.sleep(self.globals.audio_delay)

        self.show_loop(self.data['_image'], self.data['_relays'], self.repeat, end_by, epoch)

    def show_loop(self, image_slice, relays, repeat, end_by, epoch):
        height = len(image_slice)
        abs_y = 0
        while (repeat and (abs_y < height * repeat)) or (not repeat and datetime.datetime.now() < end_by):
            y = abs_y % height

            # for x, name in enumerate(self.relays):
            #     color = self.image[width * im_y + x]
            #     self.home.relays[name].set(bool(color[0]))

            # for x in range(len(self.relays), width):
            #     color = self.image[width * im_y + x]
            #     color_tup = color[0], color[1], color[2]
            #     self.home[x-len(self.relays)] = color_tup

            if relays:
                relay_row = relays[y]
                for x, name in enumerate(self.relays):
                    self.home.relays[name].set(relay_row[x])
                self.home.show_relays(force=True)

            image_row = image_slice[y]
            for x, color in enumerate(image_row):
                self.home[x] = color

            self.home.show()

            while True:
                previous_y = abs_y
                abs_y = int((time.time() - epoch) * self.fps)
                if abs_y != previous_y:
                    break

        print('image complete')
