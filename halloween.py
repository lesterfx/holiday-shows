#!/usr/bin/env python

from __future__ import division
import datetime
from itertools import count
from math import copysign
import random
import time

from pixels import Home, Color, Pixel

def sign(number):
    return copysign(1, number)

def roundup(number, interval):
    return ((number + interval - 1) // interval) * interval

class Halloween(Home):
    purple = Color(.1, 0, .4)
    orange = Color(1, .4, 0)

    def main(self):
        while self.keep_running():
            self.chase()
            self.blackhole()
            time.sleep(2)
            self.ghost()
            self.ghost()
            self.blinky_eyes()
            ##time.sleep(random.uniform(0, 10))

    def blackhole(self):
        every = 10
        pixels = []
        rounded = roundup(len(self), every)
        for i in range(rounded):
            if not i % every:
                pixels.append(Pixel(i, self.orange, self))
            elif not i % 2:
                pixels.append(Pixel(i, self.purple, self))
        center = random.randrange(0, len(self))
        def move():
            for pixel in pixels:
                pixel.position += 1
                if pixel.position > rounded:
                    pixel.position -= rounded
        update = self.run_every(.1, move)
        for radius in count():
            center_color = Color(.5)
            self.clear()
            anything_to_do = False
            for pixel in pixels:
                delta = pixel.position - center
                if not delta:
                    pixel.delete()
                    continue
                if abs(delta) < radius:
                    add = copysign((abs(delta) - radius) / 30, -delta)
                    if abs(add) > abs(delta):
                        pixel.position = center
                        center_color = pixel.color * 3
                    else:
                        pixel.position += add
                anything_to_do = True
                pixel.draw()
            update()
            self[center] = center_color
            time.sleep(.02)
            self.show()
            if not anything_to_do: break
        self.clear(True)

    def chase(self):
        every = 10
        offset = 0
        for offset in range(30):
            self.clear()
            for i in range(len(self)):
                if not (i-offset) % every:
                    self[i] = self.orange
                elif not (i-offset) % 2:
                    self[i] = self.purple
            self.show()
            time.sleep(.1)

    def chase(self):
        every = 10
        offset = [0]
        def move():
            offset[0] += 1
        update = self.run_every(.1, move)
        def loop():
            update()
            self.clear()
            for i in range(len(self)):
                if not (i-offset[0]) % every:
                    self[i] = self.orange
                elif not (i-offset[0]) % 2:
                    self[i] = self.purple
            self.show()
        self.run_for(3, loop)

    def ghost(self):
        position = random.randrange(len(self))
        speed = random.uniform(-3, 3)
        intensity = random.uniform(0, 1)
        intensity_speed = random.uniform(-.05, .05)
        for i in range(2000):
            position += speed
            speed = speed + random.uniform(-1, 1)
            intensity += intensity_speed
            intensity_speed = intensity_speed + random.uniform(-10, 10)
            self.clear()
            if intensity <= 0: break
            if position not in self: break
            self[position] = Color(intensity)
            self.show()
            time.sleep(.01)
        self.clear(True)

    def blinky_eyes(self):
        color1 = Color(1, 1, .8)
        color2 = Color(1, .1, 0)
        fade = random.random()
        color = color1 * fade + color2 * (1-fade)
        distance = random.randrange(2, 6)
        center = random.randrange(distance, len(self)-distance)
        for _ in range(random.randrange(1, 5)):
            self._show_eyes_once(center, distance, color)

    def _show_eyes_once(self, center, distance, color):
        for i in range(20):
            self[center+distance] = color * (i/20)
            self[center-distance] = color * (i/20)
            self.show()
            time.sleep(0.001)
        time.sleep(random.uniform(1, 3))
        self.clear(True)
        time.sleep(random.uniform(.1, .4))

if __name__ == '__main__':
    try:
        Halloween(1).main()
    except KeyboardInterrupt:
        pass
