#!/usr/bin/env python3

import random
import time

import pixels
import physics

class Flag(pixels.Home):
    def main(self):
        self.flag_colors = [pixels.Color(1,0,0), pixels.Color(1,1,1)]
        self.dir = -20
        self.last_color = 1
        self.center = int(len(self) * .7)
        bluestart = int(len(self) * .55)
        blueend = int(len(self) * .85)
        for x in range(bluestart, blueend):
            self[x] = pixels.Color(0, 0, 1)
        for x in range(bluestart):
            self[x] = pixels.Color(1, 0, 0)
        for x in range(blueend, len(self)):
            self[x] = pixels.Color(1, 0, 0)
        self.system = physics.System(self)
        self.system.effects.append(physics.Collide(0))
        self.system.effects.append(physics.Collide(len(self)))
        emitter = physics.Emitter(.5, self.emit, True)
        while self.system.update_and_draw(remove_deleted=True, clear=False, show=True):
            emitter.emit()
            last = 0
            for particle in sorted(self.system.particles):
                pos = particle.position
                last_color = particle.flag_color
                for x in range(int(last), int(pos)):
                    self[x] = self.flag_colors[last_color]
                last = pos
            for x in range(int(last), len(self)):
                self[x] = self.flag_colors[1-last_color]
            for x in range(bluestart, blueend):
                self[x] = pixels.Color(0, 0, 1)

    def emit(self):
        position = self.center
        speed = self.dir / 2
        self.dir = -self.dir
        if self.dir < 0:
            self.last_color = 1-self.last_color
        color = pixels.Color(1, 1, 1)
        particle = physics.Particle(strip=self, position=position, speed=speed, color=color)
        particle.flag_color = self.last_color
        self.system.particles.add(particle)

class Flag(pixels.Home):
    def main(self):
        red = pixels.Color(1,0,0)
        white = pixels.Color(1,1,1)
        blue = pixels.Color(0,0,1)
        center = int(len(self) * .7)
        bluestart = int(len(self) * .55)
        blueend = int(len(self) * .85)
        blues = range(bluestart, blueend)
        every = 10
        offset = 0
        while True:
            self *= .9
            #self.clear()
            #self -= pixels.Color(.03, .03, .03)
            offset = (offset + 1) % every
            end = max(center, len(self)-center)
            for i in range(offset-every, end, every//2):
                if i < 0: continue
                for sign in (-1, 1):
                    x = center + i*sign
                    if bool((i-offset - every//2) % every) != (sign < 0):
                        if x in blues:
                            color = blue
                        else:
                            color = red
                    else:
                            color = white
                    self[x] = color
            self.show()
            time.sleep(0.1)
if __name__ == '__main__':
    Flag()
