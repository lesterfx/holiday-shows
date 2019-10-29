from __future__ import print_function
import os
import subprocess
import sys

ONE_LINE = True
#ONE_LINE = False
CLEAR = False
#CLEAR = True

gamma = 1/2.2

TOP_PADDING, LED_COUNT = map(int, subprocess.check_output(['stty', 'size']).split())
LED_COUNT -= 2
TOP_PADDING //= 4

config = {'range': [0, LED_COUNT], 'order': 'rgb'}
print('Config overrides:', config)

def colorchar(pixel):
    chr = u'\u2585'
    chr = u'\u2b24'
    r, g, b = pixel
    pixel = r, g, b
    return u'\033[38;2;{0:.0f};{1:.0f};{2:.0f}m{chr}\033[00m'.format(*pixel, chr=chr)

class NeoPixel(object):
    def __init__(self, pin, n, *args, **kwargs):
        self.pixels = [Color(10, 10, 10) for _ in range(n)]
        if CLEAR:
            os.system('cls' if os.name == 'nt' else 'clear')
            print('\n' * TOP_PADDING)

    def show(self):
        out = '\r '
        for pixel in self.pixels:
            if pixel:
                out += colorchar(pixel)
            else:
                out += ' '
        if ONE_LINE:
            print(out, end='', flush=True)
        else:
            print(out)

    def __setitem__(self, key, value):
        self.pixels[key] = value

class Color (object):
    def __new__(self, r, g, b):
        return (r, g, b)
