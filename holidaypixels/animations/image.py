#!/usr/bin/env python3

import datetime
import importlib
import os
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
        path = os.path.join(os.path.dirname(__file__), '..', path)
        path = os.path.realpath(path)
        if 'variations' in self.settings:
            path = path.format(randint(1, self.settings['variations']))
        print()
        print('Loading image:', path)
        print()
        image = Image.open(path)
        self.image = image.getdata()
        self.width = image.width
        self.height = image.height
        self.validate_relays()

        music = element['music']
        if music:
            print('Loading music:', music)
            self.sound = mixer.Sound(music)
            self.silence = mixer.Sound('/home/pi/pixels/holidaypixels/utilities/pop.mp3')
        else:
            print('No music')
            self.sound = None
            self.silence = None

        self.fps = element['fps']


    def main(self, end_by):
        self.num_relays = self.settings.get('relays', 0)
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

    def validate_relays(self):
        for y in range(self.height):
            for x in range(self.num_relays):
                color = self.image[self.width * y + x]
                if not (color[0] == color[1] == color[2]) or color[0] not in (0, 255):
                    raise ValueError(f'Relay data at Row {y}, Col {x} is not black or white.')

    def present(self, end_by, epoch=None):
        previous_y = None
        y = 0
        width = self.width
        height = self.height

        self.home.strip.on = True
        self.home.clear()
        self.home.show()
        self.home.show_relays(True)

        countdown = self.settings.get('countdown', 0)
        if countdown:
            if self.silence:
                self.silence.play()
            for i in range(countdown):
                print(countdown-i)
                time.sleep(1)
        if self.sound:
            self.sound.play()
            time.sleep(self.globals.audio_delay)
            epoch = time.time()
        else:
            early = epoch - time.time()
            if early > 0:
                print('early by', early, 'seconds. sleeping')
                time.sleep(early)
            else:
                print('not early. late by', early, 'seconds')

        while (self.repeat and (y < height * self.repeat)) or (not self.repeat and datetime.datetime.now() < end_by):
            im_y = y % height

            for x, relay in zip(range(self.num_relays), self.home.relays_in_order):
                color = self.image[width * im_y + x]
                relay.set(bool(color[0]))

            for x in range(self.num_relays, width):
                color = self.image[width * im_y + x]
                color_tup = color[0], color[1], color[2]
                self.home[x-self.num_relays] = color_tup
            self.home.show_relays(force=False)
            self.home.show()

            while True:
                previous_y = y
                y = int((time.time() - epoch) * self.fps)
                if y != previous_y:
                    break
        print('image complete')
