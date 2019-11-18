import os
import subprocess
import sys
import time

from PIL import Image

class ImagePixel(object):
    def __init__(self, n, outfile):
        self.pixels = [Color(10, 10, 10) for _ in range(n)]
        self.data = []
        self.rows = 0
        self.outfile = outfile

    def show(self):
        row = []
        for pixel in self.pixels:
            if pixel:
                row.append(pixel)
            else:
                row.append((0, 0, 0))
        self.data += row
        self.rows += 1
        print(self.rows)

    def __setitem__(self, key, value):
        self.pixels[key] = value

    def __del__(self):
        print('Save Image!')
        size = (len(self.pixels), self.rows)
        print(size)
        image = Image.new('RGB', size)
        image.putdata(self.data)
        image.save(self.outfile)
        print('Saved')

class Color (object):
    def __new__(self, r, g, b):
        return (r, g, b)
