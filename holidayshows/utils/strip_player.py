from collections import defaultdict
from datetime import datetime
import time

from ..utils import strip

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
        elif 'image_data' in arguments:
            self.load_image(index, arguments['image_data'])
        else:
            raise ValueError(f'unexpected arguments {list(arguments)}')

    def load_image(self, index, image_data):
        self.image_data[index] = image_data

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

        height = len(self.image_data[index])
        print('\n')
        if repeat:
            print(f'playing at {fps} fps {repeat} times, starting at {datetime.fromtimestamp(epoch)} and ending at {datetime.fromtimestamp(epoch + height * fps)}')
        else:
            print(f'playing at {fps} fps on loop until {datetime.fromtimestamp(end_by)}, at {fps} fps')
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
        while (repeat and (abs_y < height * repeat)) or (not repeat and now < end_by):
            y = abs_y % height

            fade_in = (now - epoch) / FADE_IN_SECONDS
            fade_out = (end_by - now) / FADE_OUT_SECONDS
            fade = min(fade_in, fade_out, 1)
            if repeat == 0:
                self.strip.blacks.scale(fade)

            if self.relay_data[index]:
                if self.relay_data[index] == 'cycle':
                    for i, name in enumerate(self.relays[index]):
                        if i / len(self.relays) > fade:
                            on = False
                            print(f'{name}', end=' ')
                        else:
                            on = (abs_y//fps) % len(self.relays) != i
                        self.home.relays[name].set(on)
                    print()
                else:
                    relay_row = self.relay_data[index][y]
                    for x, name in enumerate(self.relays[index]):
                        self.home.relays[name].set(relay_row[x])
                self.home.show_relays()

            image_row = self.image_data[index][y]
            for x, color in enumerate(image_row):
                self.strip[x] = color

            self.strip.show()

            while True:
                yield f'play in progress: {y / height:.0%}'
                now = time.time()
                previous_y = abs_y
                abs_y = int((now - epoch) * fps)
                if abs_y != previous_y:
                    break

        self.strip.blacks.scale()

        print('image complete')
        self.strip.clear(True)

    def stop(self):
        self.strip.clear(True)
