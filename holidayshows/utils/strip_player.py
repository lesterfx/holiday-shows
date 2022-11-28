from collections import defaultdict
from datetime import datetime
from random import uniform
import time

from ..utils import strip, image_slicer

class Strip_Player():
    def __init__(self, config):
        self.strip = strip.Strip(config)
        self.image_data = {}
        self.relay_data = defaultdict(lambda: None)
        self.relays = {}

    def load_data(self, arguments):
        index = arguments['index']
        if 'relay_data' in arguments:
            self.load_relays(index, arguments['relay_data'], arguments['relay_order'], arguments['home'])
        elif 'relay_slice' in arguments:
            self.slice_relays(index, arguments['relay_slice'], arguments['relay_order'], arguments['home'])
        elif 'procedural_relays' in arguments:
            self.load_relays(index, arguments['procedural_relays'], arguments['relay_order'], arguments['home'])

        elif 'image_data' in arguments:
            self.load_image(index, arguments['image_data'])
        elif 'slice_data' in arguments:
            self.slice_image(index, arguments['slice_data'])

        else:
            raise ValueError(f'unexpected arguments {list(arguments)}')

    def load_image(self, index, image_data):
        self.image_data[index] = image_data

    def slice_image(self, index, slice_data):
        path, start, end, wrap = slice_data
        print('slicing image', path, 'from', start, 'to', end, 'wrap', wrap)
        sliced = image_slicer.ImageSlicer().slice_image(path, start, end, wrap)
        self.image_data[index] = sliced

    def slice_relays(self, index, slice_data, relay_order, home):
        path, start, end = slice_data
        sliced = image_slicer.ImageSlicer().slice_image(path, start, end, False, True)
        self.load_relays(index, sliced, relay_order, home)

    def load_relays(self, index, relay_data, relay_order, home):
        self.relay_data[index] = relay_data
        self.relays[index] = relay_order
        self.home = home  # this is a hack, but relays are a hack right now anyway

    def play(self, arguments):
        index = arguments['index']
        repeat = arguments['repeat']
        end_by = arguments['end_by']
        epoch = arguments['epoch']
        fps = arguments['fps']

        image_data = self.image_data[index]
        relay_data = self.relay_data[index]
        if relay_data is not None:
            relays = self.relays[index]
            if 'mode' in relay_data and relay_data['mode'] == 'random':
                # sure is ugly copying this logic twice...
                relay_toggle_time = {name: uniform(0, 1.5)*(fps * relay_data['timing'] * (1-relay_data['duty_cycle'])) for name in relays}

        height = len(image_data)
        print('\n')
        if repeat:
            print(f'playing {index} at {fps} fps {repeat} times, starting at {datetime.fromtimestamp(epoch)} and ending at {datetime.fromtimestamp(epoch + height * fps)}')
        else:
            print(f'playing {index} at {fps} fps on loop until {datetime.fromtimestamp(end_by)}')
        print('\n')

        FADE_IN_SECONDS = 30
        FADE_OUT_SECONDS = 60
        abs_y = 0
        now = time.time()
        while epoch and epoch > now:
            time.sleep(0.001)
            yield 'waiting for start time'
            now = time.time()
        self.strip.blacks.scale()
        try:
            while (repeat and (abs_y < height * repeat)) or (not repeat and now < end_by):
                y = abs_y % height

                fade_in = (now - epoch) / FADE_IN_SECONDS
                fade_out = (end_by - now) / FADE_OUT_SECONDS
                fade = min(fade_in, fade_out, 1)
                if repeat == 0:
                    self.strip.blacks.scale(fade)

                if relay_data is not None:
                    if 'mode' in relay_data:
                        if relay_data['mode'] == 'cycle':
                            for i, name in enumerate(relays):
                                if i / len(relays) > fade:
                                    on = False
                                else:
                                    on = (abs_y // (fps * relay_data[1])) % len(relays) != i
                                self.home.relays[name].set(on)
                                if on:
                                    print(name.upper(), end=' ')
                                else:
                                    print(name.lower(), end=' ')
                            print()
                        elif relay_data['mode'] == 'random':
                            for name in relays:
                                if abs_y > relay_toggle_time[name]:
                                    if self.home.relays[name].value:
                                        if abs_y + relay_data['timing'] < end_by:
                                            relay_toggle_time[name] = abs_y + uniform(0.5, 1.5) * (fps * relay_data['timing'] * (1-relay_data['duty_cycle']))
                                        else:
                                            print(name, 'staying off')
                                            relay_toggle_time[name] = end_by
                                        self.home.relays[name].set(False)
                                    else:
                                        relay_toggle_time[name] = abs_y + uniform(0.5, 1.5) * (fps * relay_data['timing'] * relay_data['duty_cycle'])
                                        self.home.relays[name].set(True)
                        else:
                            raise NotImplementedError()
                    else:
                        relay_row = relay_data[y]
                        for x, name in enumerate(relays):
                            self.home.relays[name].set(relay_row[x])
                    self.home.show_relays()

                image_row = image_data[y]
                for x, color in enumerate(image_row):
                    self.strip[x] = color.tolist()

                self.strip.show()

                while True:
                    yield f'play in progress: {y / height:.0%}'
                    now = time.time()
                    previous_y = abs_y
                    abs_y = int((now - epoch) * fps)
                    if abs_y != previous_y:
                        break
        finally:
            self.cleanup()

    def cleanup(self):
        self.strip.blacks.scale()

        print('image complete')
        # self.strip.print_fps_histogram()
        self.strip.clear(True)

    def stop(self):
        self.strip.clear(True)
