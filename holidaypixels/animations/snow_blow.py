#!/usr/bin/env python3

import datetime
import random

from ..utilities import physics
from ..utilities.home import Home, Color, Pixel

class Animation(object):
    snow_colors = []
    snow_colors.append(Color(.1**3, .1**3, 1**3))
    snow_colors.append(Color(1**3, 1**3, 1**3))
    snow_colors.append(Color(.3**3, 0**3, 1**3))

    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'Snow Blow'

    def main(self, end_by):
        self.end_by = end_by
        self.system = physics.System(self.home)
        self._make_effects()
        def do_update_wind():
            speed = random.uniform(*self.settings['wind_range']) * random.choice([-1, 1])
            self.wind.speed = speed
            #self.turbulence.regenerate()
        update_wind = self.home.run_every(4, do_update_wind)
        self.sleep = .5
        self.make_snow = self.home.run_every(0, self._make_snow)
        while datetime.datetime.now() < self.end_by:
            self.make_snow()
            while self.system.update_and_draw(show=True, remove_deleted=True, clear=False):
                self.make_snow()
                update_wind()
                self.home.show()
                self.home *= self.settings['fade']

    def leave(self, particle, effect, edge):
        particle.delete()

    def lifecycle(self, particle, absolute_age, uniform_age):
        particle.color.luma = 1 - abs(1 - uniform_age * 2)

    def _make_snow(self):
        if datetime.datetime.now() >= self.end_by:
            return
        extra = random.uniform(0, 1)
        self.sleep = self.sleep * .9 + extra * .1
        self.sleep = min(1, max(0, self.sleep))
        self.make_snow.seconds = self.sleep ** 8 * 30
        color = self.snow_color(luma=0, mode='max')
        mass = random.uniform(.8, 1.25)
        life = random.uniform(*self.settings['life_range'])
        speed = random.uniform(0, self.wind.speed)
        particle = physics.Particle(mass=mass, speed=speed, life=life, lifecycle=self.lifecycle, color=color, position=0, strip=self.home)
        particle.position = self._find_spawn_point()
        if particle.position is not None:
            self.system.particles.add(particle)
            return True

    def _find_spawn_point(self):
        return random.randrange(*self.globals.ranges[0])

    def snow_color(self, *args, **kwargs):
        color1, color2 = random.sample(self.snow_colors, 2)
        weight = random.random()
        color = Color(0, 0, 0, *args, **kwargs)
        color += (color1 * weight + color2 * (1-weight))
        return color

    def _make_effects(self):
        self.wind = physics.Wind(speed=20, strength=0.6)
        #self.turbulence = physics.Turbulence(speed=(-200, 200), strength=0.2, length=len(self.home), size=len(self.home))
        self.piles = []
        for x in self.globals.ranges[0]:  # range top end puts it 1 too far
            self.piles.append(physics.Collide(center=x, radius=0, on_collide=self.leave))

        self.system.effects.append(self.wind)
        #self.system.effects.append(self.turbulence)
        for pile in self.piles:
            self.system.effects.append(pile)

    def respawn(self, particle):
        particle.position = random.uniform(0, len(self.home))
