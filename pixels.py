#!/usr/bin/env python3

from __future__ import print_function, division

import copy
import datetime
import json
import getpass
import os
import time
import traceback

user = getpass.getuser()
if user == 'root':
    import board
    import neopixel
    GAMMA = 1
elif user == 'mobile':
    import uipixel as neopixel
    GAMMA = .3
else:
    import consolepixel as neopixel
    GAMMA = .3
    SCALE = 255

class Color (object):
    def __init__(self, r, g=None, b=None, luma=1, mode='over'):
        if g is None: g = r
        if b is None: b = r
        self.r = r
        self.g = g
        self.b = b
        self.luma = luma
        self.mode = mode

    @property
    def color(self):
        return tuple(map(self.channelmap, self.tuple))

    def channelmap(self, x):
        clamped = min(1, max(0, x))
        scaled = int(clamped ** GAMMA * 255)
        return scaled

    @property
    def tuple(self):
        return (
            self.r*self.luma,
            self.g*self.luma,
            self.b*self.luma
        )

    def __imul__(self, other):
        self.r *= other
        self.g *= other
        self.b *= other
        return self

    def __mul__(self, other):
        return Color(
            r=self.r * other,
            g=self.g * other,
            b=self.b * other,
            luma=self.luma,
            mode=self.mode
        )

    def __idiv__(self, other):
        self *= 1 / other
        return self

    def __div__(self, other):
        return self * (1 / other)

    __floordiv__ = __div__
    __truediv__ = __div__

    def __iadd__(self, other):
        self.r += other.r*other.luma
        self.g += other.g*other.luma
        self.b += other.b*other.luma
        return self

    def __add__(self, other):
        return Color(
            r=self.r + other.r*other.luma,
            g=self.g + other.g*other.luma,
            b=self.b + other.b*other.luma,
            mode=self.mode,
            luma=self.luma
        )

    def __isub__(self, other):
        self.r -= other.r*other.luma
        self.g -= other.g*other.luma
        self.b -= other.b*other.luma
        return self

    def __or__(self, other):
        return Color(
            r=max(self.r, other.r*other.luma),
            g=max(self.g, other.g*other.luma),
            b=max(self.b, other.b*other.luma),
            mode=self.mode,
            luma=self.luma
        )

    def __eq__(self, other):
        return self.tuple == other.tuple

    def __repr__(self):
        color = self.tuple
        return f'{color[0]:.04f},{color[1]:.04f},{color[2]:.04f} ({self.luma:.04f})'


class Pixel(object):
    def __init__(self, position, color, strip):
        self.strip = strip
        self.position = position
        self.color = color
        self.deleted = False

    def draw(self):
        if not self.deleted and 0 <= self.position < len(self.strip):
            self.strip[self.position] = self.color
            return 1
        else:
            return 0

    def delete(self):
        if self.on_delete:
            self.on_delete(self)
        self.deleted = True

    def __lt__(self, other):
        return self.position < other.position

class Home(object):
    def __init__(self, minutes=0):
        print('Loading')
        self.load_config()
        pin = self.config['pin']
        pixel_order = self.config['pixel_order']
        if neopixel.__name__ == 'neopixel':
            pin = getattr(board, f'D{pin}')
            pixel_order = getattr(neopixel, pixel_order)
        num = self.config['range'][-1]
        print('Initializing Strip')
        self.strip = neopixel.NeoPixel(pin=pin, n=num, brightness=1, auto_write=False, pixel_order=pixel_order)
        self.cache = [None] * len(self)
        self.previous = None
        self.clear()
        stop_time = time.time() + minutes * 60
        print('Running', self.__class__.__name__)
        self.show()
        try:
            while True:
                self.main()
                if time.time() >= stop_time: break
        except KeyboardInterrupt:
            pass
        except:
            raise
        finally:
            self.clear()
            self.show()
            print('\n')
            print('Exiting')
            del self.strip

    def load_config(self):
        config_file = os.path.join(os.path.expanduser('~'), '.holiday-pixels', 'config.json')
        if not os.path.exists(config_file):
            print(f'Config file does not exist. Creating a sample in {config_file}')
            neopixel.CLEAR = False
            neopixel.ONE_LINE = True
            self.save_sample_config(config_file)

        print('Loading config', config_file)
        with open(config_file) as p:
            self.config = json.load(p)

        if hasattr(neopixel, 'config'):
            self.config.update(neopixel.config)

    def save_sample_config(self, config_file):
        config_dir = os.path.dirname(config_file)
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        config = {}
        config['pin'] = 18
        config['corners'] = [130, 190]
        config['pixel_order'] = 'GRB'
        config['range'] = 0, 440
        with open(config_file, 'w') as p:
            json.dump(config, p, indent=4, sort_keys=True)

    @staticmethod
    def run_every(seconds, function):
        last_run = [time.time()]
        def maybe_run(*args, **kwargs):
            now = time.time()
            if now - last_run[0] >= seconds:
                last_run[0] = now
                return function(*args, **kwargs)
        return maybe_run

    @staticmethod
    def run_for(seconds, function, *args, **kwargs):
        end = time.time() + seconds
        while time.time() < end:
            function(*args, **kwargs)

    @property
    def round_up(self):
        return ((len(self) + self.every - 1) // self.every) * self.every

    def clear(self, show=False):
        for i in range(len(self)):
            self[i] = None
        if show:
            self.show()

    def show(self):
        if self.previous != self.cache:
            start = time.time()
            for i, pixel in enumerate(self.cache):
                try:
                    color = pixel.color
                    self.strip[i] = color
                except:
                    raise
            last = time.time()
            delta = last-start
            #print(f'{delta:<.9f}', end=' ')
            self.strip.show()
            #print(time.time() - last)
            self.previous = self.cache
            self.cache = copy.deepcopy(self.previous)

    def __str__(self):
        return ' '.join(map(str, self.cache))

    def __setitem__(self, key, value):
        key = int(key)
        if key in self:
            if value:
                if value.mode == 'over':
                    self.cache[key] = value
                elif value.mode == 'add':
                    self.cache[key] += value
                elif value.mode == 'max':
                    self.cache[key] |= value
            else:
                self.cache[key] = Color(0, 0, 0)

    def __contains__(self, key):
        key = int(key)
        return 0 <= key < len(self)

    def __len__(self):
        return self.config['range'][-1]

    def __del__(self):
        try:
            self.clear(True)
        except:
            pass

    def __imul__(self, other):
        for pixel in self.cache:
            pixel *= other
        return self

    def __isub__(self, other):
        for pixel in self.cache:
            pixel -= other
        return self

if __name__ == '__main__':
        class Test(Home):
            def main(self):
                for i in range(len(self)):
                    self[i] = Color(1, 1, 1)
                    # start = time.time()
                    self.show()
                    # print(time.time() - start)
                    # time.sleep(1)
        Test()
