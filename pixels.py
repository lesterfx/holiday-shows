#!/usr/bin/env python2

import datetime
import getpass
import sys
import time

# LED strip configuration:
LED_COUNT      = 450     # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

user = getpass.getuser()
if user == 'root':
    import neopixel as library
elif user == 'mobile':
    import uipixel as library
else: # user == 'pi':
    import consolepixel as library

Adafruit_NeoPixel = library.Adafruit_NeoPixel
try:
    LED_COUNT = library.LED_COUNT
except AttributeError:
    pass

class Color (object):
    def __init__(self, r, g=None, b=None):
        if g is None: g = r
        if b is None: b = r
        self.r = r
        self.g = g
        self.b = b

    def __len__(self):
        return LED_COUNT

    @property
    def color(self):
        if hasattr(library, 'gamma'):
            gamma = library.gamma
        else:
            gamma = 1/2.2

        return library.Color(
            max(0, min(255, (self.r ** gamma) * 255)),
            max(0, min(255, (self.g ** gamma) * 255)),
            max(0, min(255, (self.b ** gamma) * 255))
        )

    def __imul__(self, other):
        self.r *= other
        self.g *= other
        self.b *= other

    def __mul__(self, other):
        return Color(
            self.r * other,
            self.g * other,
            self.b*other
        )

    def __iadd__(self, other):
        self.r += other.r
        self.g += other.g
        self.b += other.b

    def __add__(self, other):
        return Color(
            self.r + other.r,
            self.g + other.g,
            self.b + other.b
        )

class Pixel(object):
    def __init__(self, position, color, strip):
        self.strip = strip
        self.position = position
        self.color = color
        self.deleted = False

    def draw(self):
        if not self.deleted:
            self.strip[self.position] = self.color

    def delete(self):
        if hasattr(self, 'on_delete'):
            self.on_delete(self)
        self.deleted = True

class Home(object):
    def __init__(self, minutes=0):
        self.stop_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()

    @staticmethod
    def run_every(seconds, function):
        last_run = [time.time()]
        def maybe_run(*args, **kwargs):
            now = time.time()
            if now - last_run[0] >= seconds:
                function(*args, **kwargs)
                last_run[0] = now
        return maybe_run

    @staticmethod
    def run_for(seconds, function, *args, **kwargs):
        end = time.time() + seconds
        while time.time() < end:
            function(*args, **kwargs)

    def keep_running(self):
        return datetime.datetime.now() < self.stop_time

    def clear(self, show=False):
        for i in range(LED_COUNT):
            self[i] = Color(0, 0, 0)
        if show:
            self.show()

    def show(self):
        self.strip.show()

    def __setitem__(self, key, value):
        key = int(key)
        if key in self:
            self.strip.setPixelColor(int(key), value.color)

    def __contains__(self, key):
        key = int(key)
        return 0 <= key < len(self)

    def __len__(self):
        return LED_COUNT

    def __del__(self):
        try:
            self.clear(True)
        except:
            pass
