#!/usr/bin/env python3

import datetime
import os
import random
import time

from PIL import Image
import numpy as np

from ..utils import progress_bar, players, image_slicer

class Animation(object):
    def __init__(self, home, globals_, settings):
        self.home = home
        self.globals = globals_
        self.settings = settings
        self.slicer = image_slicer.ImageSlicer()

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

            for relay in resource['relays']:
                if relay not in self.home.relays:
                    raise ValueError(f'Relay {relay} is not defined in the home.')
            path = element['image']
            if 'variations' in self.settings:
                path = path.format(random.randint(1, self.settings['variations']))

            resource['data'] = {}

            for key, options in element['slices'].items():
                if key == 'relays':
                    continue
                self.loading_times['remote metadata'] -= time.time()
                start = options['start']
                end = options['end']
                wrap = options.get('wrap', False)
                self.loading_times['remote metadata'] += time.time()
                # slice = self.slice_image(image_data, start, end, wrap)
                # self.slicer.slice_image(path, start, end, wrap)
                # resource['data'][key] = slice
                self.loading_times['remote transfer'] -= time.time()
                self.home.remote_clients[key].load_data(players.PLAYER_KINDS.STRIP, {'index': index, 'slice_data': [path, start, end, wrap]})
                # self.home.remote_clients[key].load_data(players.PLAYER_KINDS.STRIP, {'index': index, 'image_data': slice})
                self.loading_times['remote transfer'] += time.time()

            if 'relays' in element['slices']:
                options = element['slices']['relays']
                if procedural := self.parse_procedural_relays(options):
                    self.home.local_client.load_data(players.PLAYER_KINDS.STRIP, {'index': index, 'procedural_relays': procedural, 'relay_order': resource['relays'], 'home': self.home})
                else:
                    start = options['start']
                    end = options['end']
                    if end == 'auto':
                        end = len(resource['relays'])
                    self.home.local_client.load_data(players.PLAYER_KINDS.STRIP, {'index': index, 'relay_slice': [path, start, end], 'relay_order': resource['relays'], 'home': self.home})

            self.loading_times['music'] -= time.time()
            music = element.get('music')
            if music:
                self.home.music_client.load_data(players.PLAYER_KINDS.MUSIC, {'index': index, 'music': music})
                resource['sound'] = True
                self.resources_loaded.append(resource)
            else:
                self.resources_without_sound.append(resource)
            self.loading_times['music'] += time.time()

    @staticmethod
    def parse_procedural_relays(options):
        if 'mode' in options:
            if options['mode'] == 'cycle':
                default = {'mode': 'cycle', 'timing': 1}
            elif options['mode'] == 'random':
                default = {'mode': 'random', 'timing': 10, 'duty_cycle': 0.5}
            else:
                raise NotImplementedError(f'mode `{options["mode"]}` not implemented')
            for key in options:
                if key in default:
                    default[key] = options[key]
                else:
                    raise KeyError(f'extra key `{key}` found in relay options')
            return default

    def main(self, end_by):
        self.repeat = self.settings.get('repeat', 1)

        start = time.time()
        from collections import defaultdict
        self.loading_times = defaultdict(float)
        self.load_resources()
        print(time.time() - start, 'seconds to load resources')
        loading_times = list(self.loading_times.items())
        loading_times.sort(key=lambda x:x[1])
        for key, value in loading_times:
            print(f'{key:<20s} took {value:.04f} seonds')
        # time.sleep(30)

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
                self.present(resource, end_by, epoch=until.timestamp())
                time.sleep(3)
            time.sleep(10)

    def activate_relays(self, show_starting, any_show_tonight):
        relay_group_values = {
            'off_when_blank': True,
            'off_for_shows': not show_starting,
            'animate': show_starting,
            'on_show_nights': any_show_tonight,
        }
        print(relay_group_values)
        for group, value in relay_group_values.items():
            for relay in self.home.relay_groups[group]:
                relay.set(value)

    @staticmethod
    def booleanize(image_slice):
        if ((image_slice[:,:,0] == image_slice[:,:,1]).all() and  # red == green
            (image_slice[:,:,0] == image_slice[:,:,2]).all() and  # red == blue
            not (set(np.unique(image_slice)) - {0, 255})):        # nothing but black and white
            return image_slice[:,:,0] > 127
        raise ValueError('Relay pixels must be black or white')

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
                        message = next(player)
                        # print('\r', str(message).ljust(50), end='')
                        still_going = True
                    except StopIteration:
                        pass
                if not still_going:
                    break

        print('image complete')
