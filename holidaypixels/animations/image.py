#!/usr/bin/env python3

import datetime
import os
import random
import time

from PIL import Image
from pygame import mixer

class Animation(object):
    def __init__(self, home, globals_, settings):
        mixer.init()
        self.home = home
        self.globals = globals_
        self.settings = settings
        self.silence = mixer.Sound('/home/pi/pixels/holidaypixels/utilities/pop.mp3')

    def __str__(self):
        return 'Image'
    
    def get_resource(self, element):
        index = self.element_indices[element['image']]
        return self.resources_loaded[index]
    
    def load_resources(self):
        self.element_indices = {}
        self.resources_loaded = {}
        self.resources_without_sound = []

        for index, element in enumerate(self.settings['elements']):
            self.element_indices[element['image']] = index

            resource = {}
            resource['index'] = index
            resource['fps'] = element['fps']
            resource['relays'] = element['relays']

            path = element['image']
            for relay in resource['relays']:
                if relay not in self.home.relays:
                    raise ValueError(f'Relay {relay} is not defined in the home.')
            path = os.path.join(os.path.dirname(__file__), '..', path)
            path = os.path.realpath(path)
            if 'variations' in self.settings:
                path = path.format(random.randint(1, self.settings['variations']))
            print()
            print('Loading image:', path)
            image = Image.open(path)
            image_data = image.getdata()
            resource['width'] = image.width
            resource['height'] = image.height

            resource['data'] = {}
            print('Image loaded')
            if 'relays' in element['slices']:
                options = element['slices']['relays']
                try:
                    start = options['start']
                    end = options['end']
                except TypeError:
                    if options == 'cycle':
                        relay_data = 'cycle'
                else:
                    relay_data = self.slice_image(image_data, resource, start, end, True)
            self.home.local_strip.load_relays(index, relay_data)
            print('Relays loaded')
            for key, options in element['slices'].items():
                if key == 'relays':
                    continue
                print(key, "processing")
                start = options['start']
                end = options['end']
                slice = self.slice_image(image_data, resource, start, end)
                resource['data'][key] = slice
                self.home.strips[key].load_image(index, slice)     # copy to other strip controller
                print(key, 'loaded')

            music = element.get('music')
            if music:
                print('Loading music:', music)
                resource['sound'] = mixer.Sound(music)
                self.resources_loaded[index] = resource
            else:
                print('No music')
                self.resources_without_sound = resource

    def main(self, end_by):
        self.repeat = self.settings.get('repeat', 1)

        self.load_resources()

        if self.settings.get('days'):
            days = set(self.settings['days'])
        else:
            days = None
        if self.settings['minute'] is not None:
            waitfor_minute = int(self.settings['minute'])
            waitfor_second = int(self.settings.get('second', 0))
        else:
            now = datetime.datetime.now()
            now += datetime.timedelta(seconds=2)
            waitfor_minute = now.minute
            waitfor_second = now.second

        while True:
            now = datetime.datetime.now().replace(second=0, microsecond=0)
            self.activate_relays(True)
            
            silent_resource = random.choice(self.resources_without_sound)
            if days is None or now.strftime('%A') in days:
                until = now.replace(minute=waitfor_minute, hour=now.hour, second=waitfor_second, microsecond=0)
                if until < now:
                    until += datetime.timedelta(hours=1)
                if until > end_by:
                    print('LAST SHOW ENDED. silent animation until night time:', end_by)
                    self.present(silent_resource, end_by)
                    return
                else:
                    print('silent animation until', until)
                    self.present(silent_resource, until-datetime.timedelta(seconds=5))
            else:
                print('silent animation until night time:', end_by)
                self.present(silent_resource, end_by)
                return
            
            self.activate_relays(True)
            if self.settings.get('shuffle'):
                random.shuffle(self.settings['elements'])
            for element in self.settings['elements']:
                resource = self.get_resource(element)
                self.activate_relays(False)
                try:
                    self.present(resource, end_by, epoch=until.timestamp())
                finally:
                    if resource['sound']:
                        resource['sound'].stop()
                time.sleep(10)
            time.sleep(10)

    def activate_relays(self, active=True):
        self.home.set_relays_in_order(active, True)

    def slice_image(self, image, resource, start, end, is_relays=False):
        print('slicing image from', start, 'to', end)
        print('image dimensions', resource['width'], 'x', resource['height'])
        image_slice = []
        if is_relays and end == 'auto':
            end = len(resource['relays'])
        for y in range(resource['height']):
            row = []
            for x in range(start, end):
                if x < resource['width']:
                    color = image[resource['width'] * y + x]
                    color_rgb = color[0], color[1], color[2]
                else:
                    color_rgb = (0, 0, 0)
                if is_relays:
                    if not (color[0] == color[1] == color[2]) or color[0] not in (0, 255):
                        raise ValueError(f'Relay data at Row {y}, Col {x} is ({color[0]}, {color[1]}, {color[2]}). Must be black or white.')
                    row.append(bool(color_rgb[0]))
                else:
                    row.append(color_rgb)
            image_slice.append(row)
        return image_slice

    def present(self, resource, end_by, epoch=None):
        end_by_float = end_by.timestamp()
        self.home.strip.on = True
        self.home.clear()
        self.home.show()
        self.home.show_relays(True)

        countdown = self.settings.get('countdown', 0)
        if countdown > 3:
            self.silence.play()
            for i in range(countdown -2):
                print(countdown-i)
                time.sleep(1)
        if not resource['sound']:
            early = epoch - time.time()
            if early > 0:
                print('early by', early, 'seconds. sleeping')
                time.sleep(early)
            else:
                print('not early. late by', early, 'seconds')
        else:
            self.home.local_strip.player.relays = resource['relays']
            epoch = time.time() + 2 + self.globals.audio_delay
            for key in resource['data']:
                strip = self.home.strips[key]
                if strip.ip:
                    print('sending play command')
                    strip.play(resource['index'], self.repeat, end_by_float, epoch, resource['fps'])
                    print('sent!')
            while time.time() < epoch - self.globals.audio_delay:
                time.sleep(0.001)
            resource['sound'].play()
            time.sleep(self.globals.audio_delay)

        print("PLAYING LOCALLY??????")
        self.home.local_strip.play(resource['index'], self.repeat, end_by_float, epoch, resource['fps'])

        for key in resource['data']:
            strip = self.home.strips[key]
            if strip.ip:
                print(strip.get_response())
        # self.show_loop(self.data['_image'], self.data['_relays'], self.repeat, end_by_float, epoch)

    def show_loop(self, image_slice, relays, repeat, end_by_float, epoch):
        height = len(image_slice)
        abs_y = 0
        while (repeat and (abs_y < height * repeat)) or (not repeat and time.time() < end_by_float):
            y = abs_y % height

            # for x, name in enumerate(self.relays):
            #     color = self.image[width * im_y + x]
            #     self.home.relays[name].set(bool(color[0]))

            # for x in range(len(self.relays), width):
            #     color = self.image[width * im_y + x]
            #     color_tup = color[0], color[1], color[2]
            #     self.home[x-len(self.relays)] = color_tup

            if relays:
                relay_row = relays[y]
                for x, name in enumerate(self.relays):
                    self.home.relays[name].set(relay_row[x])
                self.home.show_relays(force=True)

            image_row = image_slice[y]
            for x, color in enumerate(image_row):
                self.home[x] = color

            self.home.show()

            while True:
                previous_y = abs_y
                abs_y = int((time.time() - epoch) * self.fps)
                if abs_y != previous_y:
                    break

        print('image complete')
