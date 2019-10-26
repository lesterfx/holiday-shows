#!/usr/bin/env python

from __future__ import division, print_function
import random
import time

from physics import System, Particle, Modulo, Wind, Gravity, Random_Speed, Random_Intensity, Collide, Turbulence
from pixels import Home, Color, Pixel

class Fall (Home):
    leaf_colors = []
    leaf_colors.append(Color((217/255)**2.2, ( 55/255)**2.2, ( 55/255)**2.2))
    leaf_colors.append(Color((217/255)**2.2, (212/255)**2.2, ( 39/255)**2.2))
    leaf_colors.append(Color((181/255)**2.2, (174/255)**2.2, (139/255)**2.2))
    leaf_colors.append(Color((142/255)**2.2, (179/255)**2.2, ( 77/255)**2.2))

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
        while True:
            self._make_leaf()
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
        particle.color.r = 0
        particle.color.g = .1
        particle.color.b = 0
        effect.grow(edge, True)
        particle.position = edge
        particle.color.mode = 'add'
        #print()

    def _make_leaf(self):
        speed = 0 # random.uniform(-30, 30)
        color = self.leaf_color(luma=0, mode='max')
        position = random.randint(self.min, self.max)
        mass = random.uniform(.8, 1.25)
        particle = Particle(mass=mass, speed=speed, color=color, position=position, strip=self)
        self.system.particles.add(particle)

    def _make_pile_effects(self):
        self.wind = Wind(speed=20, strength=0.6)
        self.turbulence = Turbulence(speed=(-200, 200), strength=0.2, length=len(self))
        self.pile_left = Collide(center=self.min, radius=0, on_collide=self.on_collide)
        self.pile_center = Collide(center=len(self)/2, radius=0, on_collide=self.on_collide)
        self.pile_right = Collide(center=self.max, radius=0, on_collide=self.on_collide)
        self.fade_in = Random_Intensity((1, 1), (0, 1))

        self.system.effects.append(self.wind)
        self.system.effects.append(self.turbulence)
        self.system.effects.append(self.pile_left)
        self.system.effects.append(self.pile_center)
        self.system.effects.append(self.pile_right)
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

    def leaf_color(self, *args, **kwargs):
        tot = 0
        out_color = Color(0, 0, 0, *args, **kwargs)
        for color in self.leaf_colors:
            weight = random.random()
            tot += weight
            out_color += (color * weight)
        out_color /= tot
        #print(out_color)
        return out_color

    def _make_crawl_particles(self):
        for i in range(-self.every, self.rounded):
            if not i % self.every:
                mass = random.uniform(.8, 1.2)
                particle = Particle(mass=mass, speed=0, position=i, color=self.leaf_color(), strip=self)
                self.system.particles.add(particle)

if __name__ == '__main__':
    try:
        Fall(1).main()
    except KeyboardInterrupt:
        print('\n')
