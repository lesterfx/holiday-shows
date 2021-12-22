#!/usr/bin/env python3

import datetime
import os
import random
import time

from PIL import Image
# from pygame import mixer really

from ..utils import progress_bar, players

class Animation(object):
    def __init__(self, home, globals_, settings):
        # mixer.init()
        self.home = home
        self.globals = globals_
        self.settings = settings
        prep_path = os.path.join(os.path.dirname(__file__), '..', 'utils', 'prepare_speakers.mp3')
        prep_path = os.path.realpath(prep_path)
        # self.prepare_speakers = mixer.Sound(prep_path)

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
            print('Loading image:', path, end='... ')
            image = Image.open(path)
            image_data = image.getdata()
            print('done')
            resource['width'] = image.width
            resource['height'] = image.height

            resource['data'] = {}
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
            self.home.local_client.load_data(players.PLAYER_KINDS.STRIP, {'index': index, 'relay_data': relay_data})
            print('Relays loaded')
            for key, options in element['slices'].items():
                if key == 'relays':
                    continue
                print(key, "processing")
                start = options['start']
                end = options['end']
                wrap = options.get('wrap', False)
                slice = self.slice_image(image_data, resource, start, end, wrap)
                resource['data'][key] = slice
                self.home.remote_clients[key].load_data(players.PLAYER_KINDS.STRIP, {'index': index, 'image_data': slice})
                print(key, 'loaded')

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
        print('slicing image from', start, 'to', end)
        print('image dimensions', resource['width'], 'x', resource['height'])
        image_slice = []
        if is_relays and end == 'auto':
            end = len(resource['relays'])
        with progress_bar.ProgressBar(resource['height']) as progress:
            for y in range(resource['height']):
                progress.update(y)
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
        self.home.clear()
        self.home.show()
        self.home.show_relays()

        repeat = self.repeat
        if resource.get('loop'):
            repeat = 0
        countdown = self.settings.get('countdown', 0)
        if countdown > 3:
            self.prepare_speakers.play()
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
            self.home.local_strip.player.relays = resource['relays']
            epoch = time.time() + 2
            players = []
            for remote in self.home.remote_clients.values():
                players.append(remote.play(resource['index'], repeat, end_by_float, epoch, resource['fps']))
            while True:
                for player in players:
                    any_still_playing = False
                    try:
                        next(player)
                        any_still_playing = True
                    except StopIteration:
                        pass
                if not any_still_playing:
                    break
        #     for key in resource['data']:
        #         strip = self.home.strips[key]
        #         if strip.ip:
        #             print('sending play command')
        #             strip.play(resource['index'], repeat, end_by_float, epoch, resource['fps'])
        #             print('sent!')
        #     print('\n'*4)
        #     print('telling music to play index', resource['index'], 'at', epoch)
        #     self.home.music_client.play(resource['index'], epoch)
        #     print('\n'*4)
        #     now = time.time()
        #     if now < epoch:
        #         time.sleep(epoch - now)
        #     if resource.get('sound'):
        #         # resource['sound'].play()
        #         pass

        # self.home.local_strip.play(resource['index'], repeat, end_by_float, epoch, resource['fps'])

        print('image complete')
