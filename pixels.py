#!/usr/bin/env python2

import datetime
import getpass
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
        self.luma = 1

    def __len__(self):
        return LED_COUNT

    @property
    def color(self):
        if hasattr(library, 'gamma'):
            gamma = library.gamma
        else:
            gamma = 1/2.2

        def mapper(x):
            return max(0, min(255, ((x*self.luma) ** gamma) * 255))

        return library.Color(*map(mapper, self.tuple))

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
            self.r * other,
            self.g * other,
            self.b * other
        )

    def __idiv__(self, other):
        self *= 1 / other
        return self

    def __div__(self, other):
        return self * (1 / other)

    __floordiv__ = __div__
    __truediv__ = __div__

    def __iadd__(self, other):
        self.r += other.r
        self.g += other.g
        self.b += other.b
        return self

    def __add__(self, other):
        return Color(
            self.r + other.r,
            self.g + other.g,
            self.b + other.b
        )

    def __repr__(self):
        color = self.tuple
        return ','.join(map('{:.04f}'.format, color))


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

class Home(object):
    def __init__(self, minutes=0):
        self.cache = [0] * len(self)
        self.previous = [0] * len(self)
        self.strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
        self.strip.begin()
        self.stop_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)

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

    @property
    def round_up(self):
        return ((len(self) + self.every - 1) // self.every) * self.every

    def keep_running(self):
        return datetime.datetime.now() < self.stop_time

    def clear(self, show=False):
        for i in range(LED_COUNT):
            self[i] = None
        if show:
            self.show()

    def show(self):
        if self.previous != self.cache:
            for i, color in enumerate(self.cache):
                self.strip.setPixelColor(i, color)
            self.strip.show()
            self.previous = self.cache
            self.cache = [0] * len(self)

    def __setitem__(self, key, value):
        key = int(key)
        if key in self:
            if value:
                self.cache[key] = value.color
            else:
                self.cache[key] = 0

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
