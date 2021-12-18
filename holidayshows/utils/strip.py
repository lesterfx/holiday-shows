import time

from rpi_ws281x import Adafruit_NeoPixel

class Strip(object):
    def __init__(self, strip_prefs):
        length = strip_prefs.length
        pin = strip_prefs.pin
        frequency = strip_prefs.frequency
        dma = strip_prefs.dma
        invert = strip_prefs.invert
        brightness = strip_prefs.brightness
        pin_channel = strip_prefs.pin_channel
        self.black = []
        for black in strip_prefs.black:
            self.black.append(range(black[0], black[1]))

        self.real_strip = Adafruit_NeoPixel(length, pin, frequency, dma, invert, brightness, pin_channel)
        self.real_strip.begin()

        pixel_order = strip_prefs.pixel_order.lower()

        self.shift = [1<<((2-pixel_order.index(x))*8) for x in 'rgb']
        self.delay = self.calculate_delay(length, frequency)
        print('minimum time between frames:', self.delay)
        print('maximum fps:', 1/self.delay)
        self.next_available = 0

        self.fps_timer = time.time()
        self.fps_count = 0
        self.relay = None

    @property
    def on(self):
        return self.relay and self.relay.value

    def calculate_delay(self, pixels, frequency):
        # each pixel uses 24 bits
        # multiply by pixels to get bits per frame
        # divide by frequency to get seconds per frame
        # times 1.2 and plus .005 for safety
        return pixels * 24 / frequency * 1.3 + .005

    def map(self, r, g, b):
        return (
            r * self.shift[0] +
            g * self.shift[1] + 
            b * self.shift[2]
        )

    def __setitem__(self, x, rgb):
        for black in self.black:
            if x in black:
                return
        if rgb:
            value = self.map(*rgb)
        else:
            value = 0
        self.real_strip.setPixelColor(x, value)

    def clear(self, show=False):
        for x in range(self.real_strip.numPixels()):
            self.real_strip.setPixelColor(x, 0)
        if show:
            self.show()

    def show(self):
        need_to_wait = self.next_available - time.time()
        if need_to_wait > 0:
            time.sleep(need_to_wait)
        self.real_strip.show()
        self.next_available = time.time() + self.delay
        self.print_fps()

    def print_fps(self):
        now = time.time()
        if now - self.fps_timer >= 1:
            print(f'\r{self.fps_count} fps (on: {self.on})')
            self.fps_count = 0
            self.fps_timer = now
        self.fps_count += 1


