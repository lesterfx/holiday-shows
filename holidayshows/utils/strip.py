import time

try:
    from rpi_ws281x import Adafruit_NeoPixel
except ImportError:
    def Adafruit_NeoPixel(*args, **kwargs):
        raise ImportError('rpi_ws281x not installed')
    print('rpi_ws281x not installed')

class Blacks:
    def __init__(self, blacks_prefs):
        self.ranges = []
        self.original_ranges = []
        for black in blacks_prefs:
            self.ranges.append(range(black[0], black[1]))
            self.original_ranges.append(range(black[0], black[1]))
        self.ranges.sort(key=lambda x:x.start)
        previous_stop = None
        self.longest_span = 0
        for black_range in self.ranges:
            if previous_stop:
                self.longest_span = max(self.longest_span, black_range.start - previous_stop)
            previous_stop = black_range.stop
        print('longest span:', self.longest_span)

    def scale(self, x=0):
        '''
        expand the blacks such that at 0 it's all black, and at 1 it's all default
        '''
        x = max(min(1-x, 1), 0)
        delta = int(self.longest_span / 2 * x)
        # print(' scale is', x, 'with delta', delta)
        for i, old_range in enumerate(self.original_ranges):
            self.ranges[i] = range(old_range.start-delta, old_range.stop+delta)

    def __contains__(self, x):
        for black_range in self.ranges:
            if x in black_range:
                return True
        return False

class Strip:
    def __init__(self, strip_prefs):
        length = strip_prefs['length']
        pin = strip_prefs['pin']
        frequency = strip_prefs['frequency']
        dma = strip_prefs['dma']
        invert = strip_prefs['invert']
        brightness = strip_prefs['brightness']
        pin_channel = strip_prefs['pin_channel']
        self.blacks = Blacks(strip_prefs['black'])

        self.real_strip = Adafruit_NeoPixel(length, pin, frequency, dma, invert, brightness, pin_channel)
        self.real_strip.begin()

        pixel_order = strip_prefs['pixel_order'].lower()

        self.shift = [1<<((2-pixel_order.index(x))*8) for x in 'rgb']
        self.delay = self.calculate_delay(length, frequency)
        print('time between frames:', self.delay)
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
        if x in self.blacks: 
            rgb = 0
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
        # self.print_fps()

    def print_fps(self):
        now = time.time()
        if now - self.fps_timer >= 1:
            print(f'\r{self.fps_count} fps (on: {self.on})')
            self.fps_count = 0
            self.fps_timer = now
        self.fps_count += 1


