#!/usr/bin/env python3

import datetime
import random

from ..utilities import physics
from ..utilities.home import Home, Color, Pixel

class Animation(object):
    leaf_colors = []
    leaf_colors.append(Color(.85**3, .2**3, .1**3))
    leaf_colors.append(Color(.85**3, .85**3, .0**3))
    leaf_colors.append(Color(.7**3, .3**3, .0**3))
    leaf_colors.append(Color(.35**3, .5**3, .1**3))

    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'Fall'

    def main(self, end_by):
        self.leaf_piles()

    def leaf_piles(self):
        self.min = self.globals.ranges[0][0]
        self.max = self.globals.ranges[0][1]
        self.system = physics.System(self.home)
        self._make_pile_effects()
        self.old_particles = []
        def do_update_wind():
            self.wind.speed = random.uniform(-50, 50)
            self.turbulence.regenerate()
        update_wind = self.home.run_every(1, do_update_wind)
        make_leaf = self.home.run_every(self.settings['emit_seconds'], self._make_leaf)
        print('Making leaves')
        while self._make_leaf():
            while self.system.update_and_draw(show=False, clear=False):
                make_leaf()
                update_wind()
                for leaf in self.old_particles:
                    self.home[leaf.position] = leaf.color
                self.home.show()
                self.home *= self.settings['fade']

        print('Blowing away')
        for pile in self.piles:
            self.system.effects.remove(pile)

        for x in self.globals.ranges[-1]:
            self.system.effects.append(physics.Collide(center=x, radius=0, on_collide=self.leave))

        random.shuffle(self.old_particles)
        def do_unlock_leaf():
            if not self.old_particles:
                return False
            self.old_particles.pop().deleted = False
            return True
        unlock_leaf = self.home.run_every(.1, do_unlock_leaf)
        while do_unlock_leaf():
            while self.system.update_and_draw(show=False):
                unlock_leaf()
                update_wind()
                for leaf in self.old_particles:
                    self.home[leaf.position] = leaf.color
                self.home.show()

    def leave(self, particle, effect, edge):
        particle.delete()

    def land(self, particle, effect, edge):
        particle.delete()
        self.old_particles.append(particle)
        particle.color.luma = 1
        effect.grow(edge, self.settings['pile_density'])
        particle.position = edge

    def _find_spawn_point(self):
        ranges = []
        prev_max = self.piles[0].max
        for pile in self.piles[1:-1]:
            this_range = range(prev_max, pile.min)
            if this_range:
                ranges.append(this_range)
            prev_max = pile.max
        this_range = range(prev_max, self.piles[-1].min)
        if this_range:
            ranges.append(this_range)
        if ranges:
            return random.choice(random.choices(ranges, weights=map(len, ranges))[0])

    def _make_leaf(self):
        color = self.leaf_color(luma=0, mode='max')
        mass = random.uniform(.8, 1.25)
        particle = physics.Particle(mass=mass, speed=0, color=color, position=0, strip=self.home)
        particle.position = self._find_spawn_point()
        if particle.position is not None:
            self.system.particles.add(particle)
            return True

    def leaf_color(self, *args, **kwargs):
        color1, color2 = random.sample(self.leaf_colors, 2)
        weight = random.random()
        color = Color(0, 0, 0, *args, **kwargs)
        color += (color1 * weight + color2 * (1-weight))
        return color

    def _make_pile_effects(self):
        self.wind = physics.Wind(speed=20, strength=0.6)
        self.turbulence = physics.Turbulence(speed=(-200, 200), strength=0.2, length=len(self.home), size=len(self.home))
        self.piles = []
        for x in list(self.globals.ranges[0]) + self.globals.corners:  # range top end puts it 1 too far
            self.piles.append(physics.Collide(center=x, radius=0, on_collide=self.land))
        self.piles.sort()
        self.fade_in = physics.Random_Intensity((1, 1), (0, 1))

        self.system.effects.append(self.wind)
        self.system.effects.append(self.turbulence)
        for pile in self.piles:
            self.system.effects.append(pile)
        self.system.effects.append(self.fade_in)

    def respawn(self, particle):
        particle.position = random.uniform(0, len(self.home))
