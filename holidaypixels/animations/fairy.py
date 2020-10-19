#!/usr/bin/env python3

from __future__ import division
import random
import time

from ..utilities import physics
from ..utilities.home import Home, Color, Pixel

class Animation(Home):
    def main(self):
        self.system = physics.System(self)
        self.system.effects.append(physics.Random_Speed(-3000, 3000))
        self.system.effects.append(physics.Random_Intensity((-.01, .007), (0, 1)))

        pos = random.randrange(len(self))
        speed = random.uniform(-30, 30)
        color = Color(random.random())
        self.system.particles.add(physics.Particle(speed=speed, position=pos, color=color, strip=self))

        while self.system.update_and_draw():
            pass
    
    def __str__(self):
        return 'fairy'
