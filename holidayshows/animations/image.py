#!/usr/bin/env python3

import datetime
import os
import random
import time

from PIL import Image
import numpy as np

from ..utils import progress_bar, players

class Animation(object):
    def __init__(self, home, globals_, settings):
        # mixer.init()
        self.home = home
        self.globals = globals_
        self.settings = settings

    def __str__(self):
        return 'Image'
    
    def load_resources(self):
        self.resources_loaded = []
        self.resources_without_sound = []

        for index, element in enumerate(self.settings['songs']):
            resource = {}
            resource['index'] = index  # in case it gets shuffled later, this is the original
            resource['fps'] = element['fps']
            resource['relays'] = element['relays']
            resource['loop'] = element.get('loop', False)

            path = element['image']
            for relay in resource['relays']:
                if relay not in self.home.relays:
                    raise ValueError(f'Relay {relay} is not defined in the home.')
            path = os.path.join(os.path.dirname(__file__), '..', path)
            path = os.path.realpath(path)
            if 'variations' in self.settings:
                path = path.format(random.randint(1, self.settings['variations']))
            print()
            print(os.path.basename(path), end=' ')
            image = Image.open(path)
            # image_data = image.getdata()
            print('loaded')
            resource['width'] = image.width
            resource['height'] = image.height

            resource['data'] = {}
            print('image is', image.width, 'x', image.height, 'pixels')
            image_data = np.asarray(image, dtype=np.uint8)
            if 'relays' in element['slices']:
                options = element['slices']['relays']
                try:
                    start = options['start']
                    end = options['end']
                except TypeError:
                    if options == 'cycle':
                        relay_data = 'cycle'
                else:
                    relay_data = self.slice_image(image_data, resource, start, end, False, True)
            self.home.local_client.load_data(players.PLAYER_KINDS.STRIP, {'index': index, 'relay_data': relay_data, 'relay_order': resource['relays'], 'home': self.home})
            for key, options in element['slices'].items():
                if key == 'relays':
                    continue
                start = options['start']
                end = options['end']
                wrap = options.get('wrap', False)
                slice = self.slice_image(image_data, resource, start, end, wrap)
                resource['data'][key] = slice
                self.home.remote_clients[key].load_data(players.PLAYER_KINDS.STRIP, {'index': index, 'image_data': slice})

            music = element.get('music')
            if music:
                self.home.music_client.load_data(players.PLAYER_KINDS.MUSIC, {'index': index, 'music': music})
                resource['sound'] = True
                self.resources_loaded.append(resource)
            else:
                print('No music')
                self.resources_without_sound.append(resource)

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

            silent_resource = random.choice(self.resources_without_sound)
            if days is None or now.strftime('%A') in days:
                until = now.replace(minute=waitfor_minute, hour=now.hour, second=waitfor_second, microsecond=0)
                if until < now:
                    until += datetime.timedelta(hours=1)
                if until > end_by:
                    print('LAST SHOW ENDED. silent animation until night time:', end_by)
                    self.activate_relays(show_starting=False, any_show_tonight=False)
                    self.present(silent_resource, end_by)
                    return
                else:
                    print('silent animation until', until)
                    self.activate_relays(show_starting=False, any_show_tonight=True)
                    self.present(silent_resource, until-datetime.timedelta(seconds=5))
            else:
                print('silent animation until night time:', end_by)
                self.activate_relays(show_starting=False, any_show_tonight=False)
                self.present(silent_resource, end_by)
                return
            
            self.activate_relays(show_starting=True, any_show_tonight=True)  # before a music show
            if self.settings.get('shuffle'):
                random.shuffle(self.resources_loaded)
            for resource in self.resources_loaded:
                try:
                    self.present(resource, end_by, epoch=until.timestamp())
                finally:
                    if 'sound' in resource:
                        # resource['sound'].stop()
                        pass
                time.sleep(3)
            time.sleep(10)

    def activate_relays(self, show_starting, any_show_tonight):
        relay_group_values = {
            'off_when_blank': True,
            'off_for_shows': not show_starting,
            'animate_between_shows': show_starting,
            'on_show_nights': any_show_tonight,
        }
        for group, value in relay_group_values.items():
            for relay in self.home.relay_groups[group]:
                # print('Setting', relay, 'in relay group', group, 'to', value)
                relay.set(value)

    def slice_image(self, image, resource, start, end, wrap=False, is_relays=False):
        with progress_bar.ProgressBar(4) as progress:
            if end == 'auto':
                end = len(resource['relays'])
            print('slicing from', start, 'to', end)
            image_slice = image[:, start:end]
            progress(1)
            if is_relays:
                image_slice = self.booleanize(image_slice)
            progress(2)
            needed_width = end - start
            if needed_width > image_slice.shape[1]:
                print('need', needed_width, 'but only have', image_slice.shape[1])
                need_size = (image_slice.shape[0], needed_width, 3)
                if wrap:
                    image_slice = np.resize(image_slice, need_size)
                else:
                    image_slice = image_slice.resize(need_size)
            progress(3)
            image_slice = image[:, start:end]
            progress(4)
        return image_slice.tolist()

    @staticmethod
    def booleanize(image_slice):
        if ((image_slice[:,:,0] == image_slice[:,:,1]).all() and 
            (image_slice[:,:,0] == image_slice[:,:,2]).all() and
            not (set(np.unique(image_slice)) - {0, 255})):
            return image_slice[:,:,0] > 127
        raise ValueError('Relay pixels must be black or white')


    def slice_image_old(self, image, resource, start, end, wrap=False, is_relays=False):
        image_slice = []
        if is_relays and end == 'auto':
            end = len(resource['relays'])
        with progress_bar.ProgressBar(resource['height']) as progress:
            for y in range(resource['height']):
                progress(y)
                row = []
                for x in range(start, end):
                    if x < resource['width'] or wrap:
                        color = image[resource['width'] * y + (x % resource['width'])]
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
        self.home.show_relays()

        repeat = self.repeat
        if resource.get('loop'):
            repeat = 0
        countdown = self.settings.get('countdown', 0)
        if countdown > 3:
            for i in range(countdown -2):
                print(countdown-i)
                time.sleep(1)
        if not resource.get('sound') and epoch is not None:
            early = epoch - time.time()
            if early > 0:
                print('early by', early, 'seconds. sleeping')
                time.sleep(early)
            else:
                print('not early. late by', early, 'seconds')
        else:
            epoch = time.time() + 2
            players = []
            for remote in self.home.remote_clients.values():
                players.append(remote.play(resource['index'], repeat, end_by_float, epoch, resource['fps']))
            while True:
                still_going = False
                for player in players:
                    try:
                        print('\r', next(player).ljust(50), end='')
                        still_going = True
                    except StopIteration:
                        pass
                if not still_going:
                    break

        print('image complete')
