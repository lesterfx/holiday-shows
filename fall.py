#!/usr/bin/env python3

from __future__ import division, print_function
import random
import time

from physics import System, Particle, Modulo, Wind, Gravity, Random_Speed, Random_Intensity, Collide, Turbulence
from pixels import Home, Color, Pixel

class Fall (Home):
    leaf_colors = []
    leaf_colors.append(Color(.85**3, .2**3, .2**3))
    leaf_colors.append(Color(.85**3, .85**3, .0**3))
    leaf_colors.append(Color(.7**3, .3**3, .1**3))
    leaf_colors.append(Color(.55**3, .7**3, .3**3))

    def main(self):
        while self.keep_running():
            for _ in range(0):
                self.crawl()
                time.sleep(1)
            for _ in range(1):
                self.leaf_piles()

    def leaf_piles(self):
        self.min = 0
        self.max = len(self)-1
        self.system = System(self)
        self._make_pile_effects()
        self.old_particles = []
        def do_update_wind():
            self.wind.speed = random.uniform(-50, 50)
            self.turbulence.regenerate()
        update_wind = self.run_every(1, do_update_wind)
        make_leaf = self.run_every(2, self._make_leaf)
        while self._make_leaf():
            while self.system.update_and_draw(show=False):
                make_leaf()
                update_wind()
                for leaf in self.old_particles:
                    if leaf.deleted:
                        self[leaf.position] = leaf.color
                self.show()
                time.sleep(0.01)

    def on_collide(self, particle, effect, edge):
        particle.delete()
        self.old_particles.append(particle)
        particle.color.luma = 1
        effect.grow(edge, 2)
        particle.position = edge

    def _make_leaf(self):
        color = self.leaf_color(luma=0, mode='max')
        mass = random.uniform(.8, 1.25)
        particle = Particle(mass=mass, speed=0, color=color, position=0, strip=self)
        for _ in range(len(self)*3):  # should programmatically find empty space rather than throw darts
            particle.position = random.randint(self.min, self.max)
            if any((particle, 0) in pile for pile in self.piles):
                continue
            else:
                break
        else:
            return False
        self.system.particles.add(particle)
        return True

    def _make_pile_effects(self):
        self.wind = Wind(speed=20, strength=0.6)
        self.turbulence = Turbulence(speed=(-200, 200), strength=0.2, length=len(self))
        self.piles = []
        for x in self.config['range'] + self.config['corners']:  # range top end puts it 1 too far
            self.piles.append(Collide(center=x, radius=0, on_collide=self.on_collide))
        self.fade_in = Random_Intensity((1, 1), (0, 1))

        self.system.effects.append(self.wind)
        self.system.effects.append(self.turbulence)
        for pile in self.piles:
            self.system.effects.append(pile)
        self.system.effects.append(self.fade_in)

    def crawl(self):
        self.every = 10
        self.rounded = ((len(self) + self.every - 1) // self.every) * self.every
        self.system = System(self)
        self._make_crawl_effects()
        self._make_crawl_particles()
        def update_wind():
            self.wind.speed = random.uniform(-30, 30)
        update_wind = self.run_every(5, update_wind)
        while self.system.update_and_draw():
            update_wind()

    def _make_crawl_effects(self):
        self.modulo = Modulo(-self.every, self.rounded)
        self.wind = Wind(speed=20, strength=0.3)

        self.system.effects.append(self.modulo)
        self.system.effects.append(self.wind)

    def leaf_color_centered(self, *args, **kwargs):
        tot = 0
        out_color = Color(0, 0, 0, *args, **kwargs)
        for color in self.leaf_colors:
            weight = random.random()
            tot += weight
            out_color += (color * weight)
        out_color /= tot
        return out_color

    def leaf_color(self, *args, **kwargs):
        weight1 = random.random()
        color1 = self.leaf_colors[0] * weight1 + self.leaf_colors[1] * (1-weight1)
        color2 = self.leaf_colors[2] * weight1 + self.leaf_colors[3] * (1-weight1)
        weight2 = random.random()
        color = Color(0, 0, 0, *args, **kwargs) + color1 * weight2 + color2 * (1-weight2)
        return color

    def _make_crawl_particles(self):
        for i in range(-self.every, self.rounded):
            if not i % self.every:
                mass = random.uniform(.8, 1.2)
                particle = Particle(mass=mass, speed=0, position=i, color=self.leaf_color(), strip=self)
                self.system.particles.add(particle)

if __name__ == '__main__':
    Fall(1)
