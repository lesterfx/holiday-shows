from __future__ import division

import ui
from random import random

LED_COUNT = 106

class Color(object):
    def __new__(self, r, g, b):
        return r/255, g/255, b/255

class Adafruit_NeoPixel (object):
    def __init__(self, LED_COUNT, *args):
        self.view = ui.View()
        self.view.background_color = 0
        self.view.present('sheet')
        width = self.view.width
        height = self.view.height
        if width >= height:
            self.pixel_size = width // LED_COUNT
            if not self.pixel_size:
                self.pixel_size = width / LED_COUNT
            width = self.pixel_size * LED_COUNT
            self.view.width = width
            self.view.height = 15 + self.pixel_size
            self.orientation = 'landscape'
        else:
            self.pixel_size = height // LED_COUNT
            if not self.pixel_size:
                self.pixel_size = height / LED_COUNT
            height = self.pixel_size * LED_COUNT
            self.view.height = height
            self.view.width = 15 + self.pixel_size
            self.orientation = 'portrait'
        self.pixels = [self.makeLabel(i) for i in range(LED_COUNT)]
        

    def makeLabel(self, i):
        label = ui.Label()
        label.background_color = 1
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

    def setPixelColor(self, key, value):
        self.pixels[key].target_color = value

    def begin(self):
        pass
        #self.view.present('sheet')

if __name__ == '__main__':
    Adafruit_NeoPixel(LED_COUNT).begin()
