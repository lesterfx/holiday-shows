#!/usr/bin/env python3

from __future__ import division
import random
import time

from ..utilities import physics
from ..utilities.home import Home, Color, Pixel

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.settings = settings

    def __str__(self):
        return 'Black Hole'

    def main(self, end_by):
        self.every = 12
        self.rounded_up = self.home.round_up(12)

        self.system = physics.System(self.home)
        self._make_particles()
        self._make_effects()

        start_time = time.time() + self.settings['delay_seconds']
        while self.system.update_and_draw():
            now = time.time() - start_time
            if now > 0:
                self.gravity.strength = max(0, time.time() - start_time) * self.settings['intensity_multiplier']
                self.wind.strength = 1

    def flash(self, pixel):
        self.home[pixel.position] = pixel.color * 3

    def _make_effects(self):
        self.modulo = physics.Modulo(-self.every, self.rounded_up)
        self.wind = physics.Wind(speed=0, strength=0)
        self.gravity = physics.Gravity(self.settings['center'], 0)

        self.system.effects.append(self.modulo)
        self.system.effects.append(self.wind)
        self.system.effects.append(self.gravity)

    def _make_particles(self):
        speed = self.settings['crawl_speed']
        for x in range(-self.every, self.rounded_up):
            if not x % self.every:
                particle = physics.Particle(speed=speed, position=x, color=Color(1, .1, 0), strip=self.home, on_delete=self.flash)
                self.system.particles.add(particle)
            elif not x % 3:
                particle = physics.Particle(speed=speed, position=x, color=Color(.03, 0, .04), strip=self.home)
                self.system.particles.add(particle)
