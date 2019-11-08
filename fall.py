#!/usr/bin/env python3

import random
import time

import physics
from pixels import Home, Color, Pixel

class Fall (Home):
    leaf_colors = []
    leaf_colors.append(Color(.85**3, .2**3, .2**3))
    leaf_colors.append(Color(.85**3, .85**3, .0**3))
    leaf_colors.append(Color(.7**3, .3**3, .1**3))
    leaf_colors.append(Color(.35**3, .7**3, .2**3))

    def main(self):
        for _ in range(0):
            self.crawl()
            time.sleep(1)
        for _ in range(1):
            self.leaf_piles()

    def leaf_piles(self):
        self.min = 0
        self.max = len(self)-1
        self.system = physics.System(self)
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
                    self[leaf.position] = leaf.color
                self.show()
                time.sleep(0.01)

        print('Done making leaves. Blowing away.')
        for pile in self.piles:
            self.system.effects.remove(pile)

        for x in self.config['range']:
            self.piles.append(physics.Collide(center=x, radius=0, on_collide=self.leave))

        random.shuffle(self.old_particles)
        def do_unlock_leaf():
            if not self.old_particles:
                return False
            self.old_particles.pop().deleted = False
            return True
        unlock_leaf = self.run_every(1, do_unlock_leaf)
        while do_unlock_leaf():
            while self.system.update_and_draw(show=False):
                unlock_leaf()
                update_wind()
                for leaf in self.old_particles:
                    self[leaf.position] = leaf.color
                self.show()
                time.sleep(0.01)

    def leave(self, particle, effect, edge):
        print('particle collided')
        particle.delete()

    def land(self, particle, effect, edge):
        particle.delete()
        self.old_particles.append(particle)
        particle.color.luma = 1
        effect.grow(edge, 3)
        particle.position = edge

    def _make_leaf(self):
        color = self.leaf_color(luma=0, mode='max')
        mass = random.uniform(.8, 1.25)
        particle = physics.Particle(mass=mass, speed=0, color=color, position=0, strip=self)
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

    def leaf_color(self, *args, **kwargs):
        color1, color2 = random.sample(self.leaf_colors, 2)
        weight = random.random()
        color = Color(0, 0, 0, *args, **kwargs)
        color += (color1 * weight + color2 * (1-weight))
        return color

    def _make_pile_effects(self):
        self.wind = physics.Wind(speed=20, strength=0.6)
        self.turbulence = physics.Turbulence(speed=(-200, 200), strength=0.2, length=len(self), size=len(self))
        self.piles = []
        for x in self.config['range'] + self.config['corners']:  # range top end puts it 1 too far
            self.piles.append(physics.Collide(center=x, radius=0, on_collide=self.land))
        self.fade_in = physics.Random_Intensity((1, 1), (0, 1))

        self.system.effects.append(self.wind)
        self.system.effects.append(self.turbulence)
        for pile in self.piles:
            self.system.effects.append(pile)
        self.system.effects.append(self.fade_in)

    def crawl(self):
        self.every = 10
        self.rounded = ((len(self) + self.every - 1) // self.every) * self.every
        self.system = physics.System(self)
        self._make_crawl_particles()
        self._make_crawl_effects()
        def update_wind():
            pass
            self.wind.speed = random.uniform(-60, 60)
            self.turbulence.regenerate()
        update_wind = self.run_every(5, update_wind)
        while self.system.update_and_draw():
            update_wind()

    def respawn(self, particle):
        particle.position = random.uniform(0, len(self))

    def _make_crawl_effects(self):
        self.modulo = physics.Modulo(0, len(self))
        #self.modulo = physics.Modulo(-self.every, self.rounded)
        self.wind = physics.Wind(speed=0, strength=0.3)
        self.turbulence = physics.Turbulence(speed=(-200, 200), strength=0.2, length=len(self), size=10)
        self.repel = physics.Repel(strength=30, radius=5, particles=self.system.particles)#, loop=len(self))
        self.speed_limit = physics.SpeedLimit(30)
        gravity_strength = -2000
        self.gravity1 = physics.Gravity(0, gravity_strength, on_collide=self.respawn)
        self.gravity2 = physics.Gravity(len(self)-1, gravity_strength, on_collide=self.respawn)
        self.system.effects.append(self.modulo)
        #self.system.effects.append(self.wind)
        self.system.effects.append(self.turbulence)
        self.system.effects.append(self.gravity1)
        self.system.effects.append(self.gravity2)
        self.system.effects.append(self.repel)
        self.system.effects.append(self.speed_limit)

    def _make_crawl_particles(self):
        #for i in range(-self.every, self.rounded, self.every):
        #for i in range(60,63):
        for i in range(0, len(self), 20):
            mass = random.uniform(.8, 1.2)
            speed = 0
            particle = physics.Particle(mass=mass, speed=speed, position=i, color=self.leaf_color(mode='max'), strip=self)
            self.system.particles.add(particle)

if __name__ == '__main__':
    Fall(1)
