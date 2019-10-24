from __future__ import print_function
import os
import subprocess
import sys

ONE_LINE = True
#ONE_LINE = False

gamma = 1/2.2

TOP_PADDING, LED_COUNT = map(int, subprocess.check_output(['stty', 'size']).split())
LED_COUNT -= 2
TOP_PADDING //= 2
print ('Strip size:', LED_COUNT)
print ('Top padding:', TOP_PADDING)

def colorchar(pixel):
    #print(pixel)
    chr = u'\u2585'
    return u'\033[38;2;{0:.0f};{1:.0f};{2:.0f}m{chr}\033[00m'.format(*pixel, chr=chr)

class Adafruit_NeoPixel(object):
    def __init__(self, LED_COUNT, *args):
        self.pixels = [Color(10, 10, 10) for _ in range(LED_COUNT)]

    def show(self):
        out = ' '
        for pixel in self.pixels:
            if pixel:
                out += colorchar(pixel)
            else:
                out += ' '
        if ONE_LINE:
            print(out, end='\r')
        else:
            print(out)
        sys.stdout.flush()

    def setPixelColor(self, key, value):
        self.pixels[key] = value

    def begin(self):
        os.system('clear')
        print('\n' * TOP_PADDING)
        self.show()

class Color (object):
    def __new__(self, r, g, b):
        return (r, g, b)
