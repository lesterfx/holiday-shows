import os
import subprocess
import sys

ONE_LINE = True
ONE_LINE = False
CLEAR = False
#CLEAR = True

gamma = 1/2.2

_, LED_COUNT = map(int, subprocess.check_output(['stty', 'size']).split())
LED_COUNT -= 2

def colorchar(pixel):
    #chr = u'\u2585'
    #chr = u'\u2b24'
    chr = '.'
    if any(pixel):
        return u'\033[38;2;{0:.0f};{1:.0f};{2:.0f}m{chr}\033[00m'.format(*pixel, chr=chr)
    else:
        return ' '

class ConsolePixel(object):
    def __init__(self, n):
        self.pixels = [Color(10, 10, 10) for _ in range(n)]
        if CLEAR:
            os.system('cls' if os.name == 'nt' else 'clear')
            print('\n' * TOP_PADDING)

    def show(self):
        if ONE_LINE:
            out = '\r '
        else:
            out = ''
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
