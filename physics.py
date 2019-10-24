#!/usr/bin/env python

from __future__ import division
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
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def apply(self, particle, tdelta):
        particle.position = ((particle.position - self.min) % (self.max - self.min)) + self.min

class Random_Speed (Effect):
    def __init__(self, min, max):
        self.min = min
        self.max = max

    def apply(self, particle, tdelta):
        particle.speed += random.uniform(self.min, self.max) * tdelta

class Random_Intensity (Effect):
    def __init__(self, add, limits):
        self.add = add
        self.limits = limits

    def apply(self, particle, tdelta):
        #print particle.color
        particle.color.luma += random.uniform(*self.add)
        #particle.color.luma = min(particle.color.luma, self.limits[1])
        #print particle.color
        if particle.color.luma < self.limits[0]:
            particle.delete()

class System (object):
    def __init__(self, strip):
        self.particles = set()
        self.effects = set()
        self.last_update = time.time()
        self.strip = strip

    def update_and_draw(self):
        self.strip.clear()
        self.update()
        anything_drawn = self.draw()
        self.strip.show()
        return anything_drawn

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
