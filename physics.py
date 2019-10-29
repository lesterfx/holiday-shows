#!/usr/bin/env python

from __future__ import division, print_function
import math
import random
import time

from pixels import Home, Color, Pixel

class Particle (Pixel):
    def __init__(self, mass=1, speed=0, on_delete=None, *args, **kwargs):
        super(Particle, self).__init__(*args, **kwargs)
        self.mass = mass
        self.speed = speed
        self.on_delete = on_delete

    def __iadd__(self, effect):
        self.effects.add(effect)
        return self

    def update(self, tdelta):
        if not self.deleted:
            self.position += (self.speed * tdelta)

class Effect (object):
    pass

class Wind(Effect):
    def __init__(self, speed, strength):
        self.speed = speed
        self.strength = strength

    def apply(self, particle, tdelta):
        self._apply_wind(particle, tdelta, self.speed)

    def _apply_wind(self, particle, tdelta, windspeed):
        particle.speed = (particle.speed - windspeed) * (1 - self.strength * (1/particle.mass) * tdelta) + windspeed

class Turbulence(Wind):
    def __init__(self, speed=(-10,10), strength=.6, length=150):
        self.min, self.max = speed
        self.strength = strength
        self.length = length
        self.loglength = int(math.ceil(math.log(self.length, 2)))
        self.regenerate()

    def regenerate(self):
        self.noise = [0] * self.length
        for logby in range(self.loglength):
            power = 2 ** (logby - self.loglength + 1)
            by = 2**logby
            nextval = random.uniform(0, .5) * power
            for x in range(0, self.length, by):
                prevval = nextval
                nextval = random.uniform(0, .5) * power
                for subx in range(by):
                    if x + subx < self.length:
                        tween = prevval * (1 - subx/by) + nextval * (subx/by)
                        self.noise[x + subx] += tween

    def apply(self, particle, tdelta):
        position = int(particle.position)
        position = min(self.length-1, (max(0, position)))
        sample = self.noise[position]  # should we interpolate sub-pixel?
        speed = self.min * (1-sample) + self.max * (sample)
        self._apply_wind(particle, tdelta, speed)

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
        add = self.strength / math.copysign(distance*distance, distance)
        add *= tdelta
        if abs(add) > abs(distance):
            add = math.copysign(distance, add)
        particle.speed += add
        next_position = particle.position + particle.speed * tdelta
        bounds = [particle.position, next_position]
        bounds.sort()
        if bounds[0] <= self.center <= bounds[1]:
            particle.position = self.center
            particle.delete()

class Collide(Effect):
    def __init__(self, center, radius, on_collide=None):
        self.min = center - radius
        self.max = center + radius
        self.on_collide = on_collide

    def grow(self, edge, plus=0):
        self.min = min(self.min, edge-plus)
        self.max = max(self.max, edge+plus)

    def apply(self, particle, tdelta):
        if (particle, tdelta) in self:
            if self.on_collide:
                if particle.position > (self.min + self.max)/2:
                    edge = self.max
                else:
                    edge = self.min
                self.on_collide(particle, self, edge)

    def __contains__(self, other_tdelta):
        other, tdelta = other_tdelta
        next_position = other.position + other.speed * tdelta
        particle_min, particle_max = sorted((other.position, next_position))
        return (particle_min <= self.max) and (particle_max >= self.min)

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
        particle.color.luma += random.uniform(*self.add)*tdelta
        particle.color.luma = min(particle.color.luma, self.limits[1])
        if particle.color.luma < self.limits[0]:
            particle.delete()

class System (object):
    def __init__(self, strip):
        self.particles = set()
        self.effects = []
        self.last_update = time.time()
        self.strip = strip

    def update_and_draw(self, clear=True, show=True):
        if clear:
            self.strip.clear()
        self.update()
        anything_drawn = self.draw()
        if show:
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
