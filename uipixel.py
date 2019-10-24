from __future__ import division

import ui
from random import random

LED_COUNT = 53

class Color(object):
    def __new__(self, r, g, b):
        return r/255, g/255, b/255

class Adafruit_NeoPixel (object):
    def __init__(self, LED_COUNT, *args):
        self.view = ui.View()
        self.view.background_color = 0
        width, height = ui.get_screen_size()
        self.pixel_size = width // LED_COUNT
        if not self.pixel_size:
            self.pixel_size = width / LED_COUNT
        width = self.pixel_size * LED_COUNT
        self.view.width = width
        self.view.height = 15 + self.pixel_size
        self.pixels = [self.makeLabel(i) for i in range(LED_COUNT)]

    def makeLabel(self, i):
        label = ui.Label()
        label.background_color = 0
        label.width = self.pixel_size
        label.height = self.pixel_size
        label.x = i * self.pixel_size
        label.y = 5
        label.target_color = None
        self.view.add_subview(label)
        return label
    
    def show(self):
        if not self.view.on_screen:
            raise KeyboardInterrupt
        for pixel in self.pixels:
            if pixel.target_color is not None:
                pixel.background_color = pixel.target_color

    def setPixelColor(self, key, value):
        self.pixels[key].target_color = value

    def begin(self):
        self.view.present('sheet')

