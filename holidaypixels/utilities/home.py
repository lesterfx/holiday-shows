#!/usr/bin/env python3

from __future__ import print_function, division

import copy
import datetime
import json
import gc
import os
import sys
import time
import traceback

import board
import digitalio
import neopixel

from . import consolepixel, imagepixel

GAMMA = 1


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

    def copy(self):
        return Color(*self.tuple)

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

class Relay(object):
    def __init__(self, pin):
        self.pin = digitalio.DigitalInOut(pin)
        self.pin.direction = digitalio.Direction.OUTPUT

    def set(self, value):
        self.pin.value = value

class Home(object):
    def __init__(self, globals_, display='gpio', outfile=None):
        self.globals = globals_
        self.max = self.globals.ranges[-1][-1]
        self.strip = self.init_strip(display, outfile)
        self.relays = self.init_relays()
        self.cache = [None] * len(self)
        self.previous = None
        self.clear()
        self.fps_count = 0
        self.fps_timer = time.time()
        self.show()

    def init_strip(self, display, outfile):
        print('Initializing Strip')
        if display == 'gpio':
            pin = self.globals.pin
            pixel_order = self.globals.pixel_order
            return neopixel.NeoPixel(pin=pin, n=self.max+1, brightness=1, auto_write=False, pixel_order=pixel_order)
        elif display == 'console':
            self.max = consolepixel.LED_COUNT
            return consolepixel.ConsolePixel(n=self.max+1)
        else:
            assert display == 'image'
            return imagepixel.ImagePixel(n=self.max+1, outfile=outfile)

    def init_relays(self):
        return [Relay(pin) for pin in self.globals.relays]

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        print('Complete')
        self.clear()
        self.clear_relays()
        self.show()

    def sleep(self, seconds):
        if hasattr(self, 'fps'):
            frames = int(seconds * self.fps)
            print(f'sleep for {frames} frames')
            for _ in range(frames):
                self.strip.show()
        else:
            time.sleep(seconds)

    def run_every(self, seconds, function):
        def func(*args, **kwargs):
            now = time.time()
            func.run_tries += 1
            run = False
            if hasattr(self, 'fps'):
                if func.run_tries == self.fps * func.seconds:
                    run = True
                    func.run_tries = 0
            else:
                if now - func.last_run >= func.seconds:
                    run = True
                    func.last_run = now
            if run:
                return function(*args, **kwargs)
        func.last_run = time.time()
        func.run_tries = 0
        func.seconds = seconds

        return func

    @staticmethod
    def run_for(seconds, function, *args, **kwargs):
        end = time.time() + seconds
        while time.time() < end:
            function(*args, **kwargs)

    def round_up(self, every):
        return ((len(self) + every - 1) // every) * every

    def clear(self, show=False):
        for i in range(len(self)):
            self[i] = None
        if show:
            self.show()
    
    def clear_relays(self):
        for relay in self.relays:
            relay.set(False)

    def print_fps(self):
        now = time.time()
        if now - self.fps_timer >= 1:
            print(f'\r{self.fps_count} fps', end='')
            self.fps_count = 0
            self.fps_timer = now
        self.fps_count += 1

    def show(self, force=False):
        self.print_fps()
        if force or self.previous != self.cache:
            for i, pixel in enumerate(self.cache):
                if pixel:
                    try:
                        color = pixel.color
                        self.strip[i] = color
                    except:
                        raise
                else:
                    self.strip[i] = 0
            self.strip.show()
            self.previous = self.cache
            self.cache = [color and color.copy() for color in self.previous]

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
        for range_ in self.globals.ranges:
            if range_[0] <= key <= range_[1]:
                return True
        return False

    def __len__(self):
        return self.max+1

    def __del__(self):
        try:
            self.clear(True)
        except:
            pass

    def __imul__(self, other):
        for pixel in self.cache:
            if pixel:
                pixel *= other
        return self

    def __isub__(self, other):
        for pixel in self.cache:
            pixel -= other
        return self
