from __future__ import division

import ui
from random import random

config = {}
config['range'] = [0, 100]

class NeoPixel (object):
    def __init__(self, pin, n, *args, **kwargs):
        self.view = ui.View()
        self.view.background_color = 0
        self.view.present('modal')
        width = self.view.width
        height = self.view.height
        if width >= height:
            self.pixel_size = width // n
            if not self.pixel_size:
                self.pixel_size = width / n
            width = self.pixel_size * n
            self.view.width = width
            self.view.height = 15 + self.pixel_size
            self.orientation = 'landscape'
        else:
            self.pixel_size = height // n
            if not self.pixel_size:
                self.pixel_size = height / n
            height = self.pixel_size * n
            self.view.height = height
            self.view.width = 15 + self.pixel_size
            self.orientation = 'portrait'
        self.pixels = [self.makeLabel(i) for i in range(n)]

    def makeLabel(self, i):
        label = ui.Label()
        label.background_color = 0
        label.width = self.pixel_size
        label.height = self.pixel_size
        if self.orientation == 'landscape':
            label.x = i * self.pixel_size
            label.y = 5
        else:
            label.y = i * self.pixel_size
            label.x = 5
        label.target_color = None
        self.view.add_subview(label)
        return label

    def show(self):
        if not self.view.on_screen:
            raise KeyboardInterrupt
        for pixel in self.pixels:
            if pixel.target_color is not None:
                pixel.background_color = pixel.target_color

    def __setitem__(self, key, value):
        self.pixels[key].target_color = tuple([x / 255 for x in value])
