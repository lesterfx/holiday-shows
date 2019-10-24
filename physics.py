#!/usr/bin/env python

from __future__ import division
import datetime
from itertools import count
from math import copysign
import random
import time

from pixels import Home, Color, Pixel

class Particle (Pixel):
    def __init__(self, speed=0, *args):
        super(Particle, self).__init__(*args)
        self.effects = set()
        self.speed = speed

    def __iadd__(self, effect):
        self.effects.add(effect)
        return self

    def update(self, tdelta):
        self.position += (self.speed * tdelta)

class Effect (object):
    pass

class Wind(Effect):
    def __init__(self, speed, strength):
        self.speed = speed
        self.strength = strength

    def apply(self, particle, tdelta):
        particle.speed = (particle.speed - self.speed) * (1-self.strength*tdelta) + self.speed

class Gravity (Effect):
    def __init__(self, center, strength):
        self.center = center
        self.strength = strength

    def apply(self, particle, tdelta):
        if not self.strength: return
        distance = self.center - particle.position
        if not distance:
            particle.delete()
            return
        add = self.strength / copysign(distance*distance, distance)
        add *= tdelta
        if abs(add) > abs(distance):
            add = copysign(distance, add)
        particle.speed += add
        next_position = particle.position + particle.speed*tdelta
        bounds = [particle.position, next_position]
        bounds.sort()
        if bounds[0] <= self.center <= bounds[1]:
            particle.position = self.center
            particle.delete()

class Modulo (Effect):
    def __init__(self, maximum):
        self.maximum = maximum

    def apply(self, particle, tdelta):
        particle.position = particle.position % self.maximum

class Random_Speed (Effect):
    def __init__(self, min, max):
        self.min = min
        self.max = max
        
    def apply(self, particle, tdelta):
        particle.speed += random.uniform(self.min, self.max)*tdelta

class Random_Intensity (Effect):
    def __init__(self, add, limits):
        self.add = add
        self.limits = limit
        
    def apply(self, particle, tdelta):
        print particle.color
        particle.color.luma += random.uniform(*self.add)
        print particle.color
        if self.limits[0] <= particle.color.luma <= self.limits[1]:
            particle.delete()
        #raise StopIteration

class System (object):
    def __init__(self):
        self.particles = set()
        self.effects = set()
        self.last_update = time.time()

    def update_and_draw(self):
        self.update()
        return self.draw()

    def update(self):
        now = time.time()
        tdelta = (now - self.last_update)
        for particle in self.particles:
            if particle.deleted: continue
            for effect in self.effects:
                effect.apply(particle, tdelta)
            particle.update(tdelta)
        self.last_update = now

    def draw(self):
        ret = 0
        for particle in self.particles:
            ret += particle.draw()
        return ret

class Physics (Home):
    def main(self):
        self.every = 10
        self.rounded = ((len(self) + self.every - 1) // self.every) * self.every

        self.system = System()
        self.make_particles()
        self.make_effects()

        start_time = time.time()+20
        while self.keep_running():
            self.clear()
            now = time.time() - start_time
            if now > 0:
                self.gravity.strength = max(0, time.time() - start_time)*50000
                self.wind.strength = 1
            self.system.update_and_draw()
            #print next(iter(self.system.particles)).speed
            self.show()
            time.sleep(.03)

    def flash(self, pixel):
        self[pixel.position] = pixel.color * 3

    def make_effects(self):
        self.modulo = Modulo(self.rounded)
        self.wind = Wind(speed=0, strength=0)
        self.gravity = Gravity(len(self)/2, 0)

        self.system.effects.add(self.modulo)
        self.system.effects.add(self.wind)
        self.system.effects.add(self.gravity)

    def make_particles(self):
        for i in range(self.rounded):
            if not i % self.every:
                particle = Particle(20, i, Color(1, .4, 0), self)
                particle.on_delete = self.flash
                self.system.particles.add(particle)
            elif not i % 2:
                particle = Particle(20, i, Color(.1, 0, .4), self)
                self.system.particles.add(particle)

if __name__ == '__main__':
    Physics(1).main()
