#!/usr/bin/env python3

import datetime
import os
from random import randint
# import socket
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
        self.silence = mixer.Sound('/home/pi/pixels/holidaypixels/utilities/pop.mp3')
        self.sound = mixer.Sound(self.settings['music'])

    def __str__(self):
        return 'Image'

    def main(self, end_by):
        self.num_relays = self.settings.get('relays', 0)
        path = self.settings['image']
        self.fps = self.settings['fps']
        path = os.path.expanduser(path)
        self.repeat = self.settings.get('repeat', 1)
        if 'variations' in self.settings:
            path = path.format(randint(1, self.settings['variations']))
        print('Opening', path)
        image = Image.open(path)
        self.data = image.getdata()
        self.width = image.width
        self.height = image.height

        self.validate_relays()

        self.activate_relays()
        waitfor_minute = int(self.settings['minute'])
        days = set(self.settings['days'])
        while True:
            now = datetime.datetime.now()
            self.activate_relays(True)
            waiting = simple_xmas.Animation(self.home, self.globals, self.settings)
            if now.strftime('%A') in days:
                until = now.replace(minute=waitfor_minute, hour=now.hour, second=0, microsecond=0)
                if until < now:
                    until += datetime.timedelta(hours=1)
                print('simple xmas until', until)
                waiting.main(until)
            else:
                print('simple xmas until night time:', end_by)
                waiting.main(end_by)
                return
            self.activate_relays(False)
            try:
                self.present(end_by)
            finally:
                self.sound.stop()
            time.sleep(30)

    def activate_relays(self, active=True):
        for relay in self.home.relays:
            relay.set(active)

    def validate_relays(self):
        try:
            for y in range(self.height):
                for x, relay in zip(range(self.num_relays), self.home.relays):
                    color = self.data[self.width * y + x]
                    assert color[0] == color[1] == color[2]
                    assert color[0] in (0, 255)
        except AssertionError:
            raise ValueError(f'Relay data at Row {y}, Col {x} is not black or white.')

    def present(self, end_by):
        previous_y = None
        y = 0
        width = self.width
        height = self.height

        countdown = self.settings.get('countdown', 0)
        if countdown:
            self.home.clear()
            self.home.show()
            # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # s.connect(("192.168.1.222", 4321))
            self.silence.play()
            for i in range(countdown):
                print(countdown-i)
                time.sleep(1)
            # print('go!')
            # s.send(b'hello')
            self.sound.play()
            time.sleep(self.globals.audio_delay)
            # s.close()

        epoch = time.time()
        while (self.repeat and (y < height * self.repeat)) or (not self.repeat and datetime.datetime.now() < end_by):
            im_y = y % height
            for x, relay in zip(range(self.num_relays), self.home.relays):
                color = self.data[width * im_y + x]
                relay.set(bool(color[0]))
            for x in range(self.num_relays, width):
                color = self.data[width * im_y + x]
                color_tup = color[0], color[1], color[2]
                self.home[x-self.num_relays] = color_tup
            self.home.show()
            while True:
                previous_y = y
                y = int((time.time() - epoch) * self.fps)
                if y != previous_y:
                    break
        print('image complete')
