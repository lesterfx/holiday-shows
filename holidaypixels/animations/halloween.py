#!/usr/bin/env python3

from __future__ import division
import random
import time

from ..utilities import physics
from ..utilities.home import Home, Color, Pixel

class Halloween (Home):
    def main(self):
        for _ in range(1):
            self.blackhole()
            time.sleep(1)
        for _ in range(3):
            self.random_walker()
            time.sleep(1)
        for _ in range(3):
            self.blinky_eyes()
            time.sleep(1)

    def __str__(self):
        return 'Halloween'

    def random_walker(self):
        self.system = physics.System(self)
        self.system.effects.append(physics.Random_Speed(-3000, 3000))
        self.system.effects.append(physics.Random_Intensity((-.01, .007), (0, 1)))

        pos = random.randrange(len(self))
        speed = random.uniform(-30, 30)
        color = Color(random.random())
        self.system.particles.add(physics.Particle(speed=speed, position=pos, color=color, strip=self))

        while self.system.update_and_draw():
            pass

    def blackhole(self):
        self.every = 12

        self.system = physics.System(self)
        self._make_blackhole_particles()
        self._make_blackhole_effects()

        start_time = time.time()+20
        while self.system.update_and_draw():
            now = time.time() - start_time
            if False: #now > 0:
                self.gravity.strength = max(0, time.time() - start_time)*50000
                self.wind.strength = 1
            time.sleep(.03)

    def flash(self, pixel):
        self[pixel.position] = pixel.color * 3

    def _make_blackhole_effects(self):
        self.modulo = physics.Modulo(-self.every, self.round_up)
        self.wind = physics.Wind(speed=0, strength=0)
        self.gravity = physics.Gravity(len(self)/2, 0)

        self.system.effects.append(self.modulo)
        self.system.effects.append(self.wind)
        self.system.effects.append(self.gravity)

    def _make_blackhole_particles(self):
        speed = 5
        speed = 1
        for x in range(-self.every, self.round_up):
            if not x % self.every:
                particle = physics.Particle(speed=speed, position=x, color=Color(1, .1, 0), strip=self, on_delete=self.flash)
                self.system.particles.add(particle)
            elif not x % 3:
                particle = physics.Particle(speed=speed, position=x, color=Color(.007, 0, .01), strip=self)
                self.system.particles.add(particle)

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
            #print(color)
            self[center+distance] = color * (i/20)
            self[center-distance] = color * (i/20)
            self.show()
            time.sleep(0.001)
        time.sleep(random.uniform(1, 3))
        self.clear(True)
        time.sleep(random.uniform(.1, .4))

if __name__ == '__main__':
    Halloween(1)
