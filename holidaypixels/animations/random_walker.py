#!/usr/bin/env python3

from __future__ import division
import random
import time

from ..utilities import physics
from ..utilities.home import Home, Color, Pixel

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'Random Walker'

    def main(self, end_by):
        self.system = physics.System(self.home)
        self.system.effects.append(physics.Random_Speed(-self.settings['speed_effect_max'], self.settings['speed_effect_max']))
        self.system.effects.append(physics.Random_Intensity(self.settings['intensity_effect_range'], (0, 1)))

        pos = random.randrange(*self.globals.ranges[0])
        speed = random.uniform(-self.settings['spawn_speed_max'], self.settings['spawn_speed_max'])
        color = Color(random.random())
        self.system.particles.add(physics.Particle(speed=speed, position=pos, color=color, strip=self.home))

        while self.system.update_and_draw():
            pass