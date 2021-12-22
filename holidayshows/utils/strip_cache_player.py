from collections import defaultdict
from datetime import datetime
import time

from ..utils import strip

class Strip_Cache_Player():
    def __init__(self, config):
        self.strip = strip.Strip(config)
        self.image_data = {}
        self.relay_data = {}
        
    def load_data(self, arguments):
        index = arguments['index']
        if 'relay_data' in arguments:
            self.load_relays(index, arguments['relay_data'], arguments['relay_order'])
        elif 'image_data' in arguments:
            self.load_image(index, arguments['image_data'])
        else:
            raise ValueError(f'unexpected arguments {list(arguments)}')

    def load_image(self, index, image_data):
        self.image_data[index] = image_data

    def load_relays(self, index, relay_data, relay_order):
        self.relay_data[index] = relay_data
        self.relays = relay_order

    def play(self, arguments):
        index = arguments['index']
        repeat = arguments['repeat']
        end_by = arguments['end_by']
        epoch = arguments['epoch']
        fps = arguments['fps']

        height = len(self.image_data[index])
        if repeat:
            print(f'playing at {fps} fps {repeat} times, starting at {datetime.fromtimestamp(epoch)} and ending at {datetime.fromtimestamp(epoch + height * fps)}')
        else:
            print(f'playing at {fps} fps on loop until {datetime.fromtimestamp(end_by)}, at {fps} fps')
        abs_y = 0
        if epoch and epoch > time.time():
            time.sleep(epoch - time.time())
        while (repeat and (abs_y < height * repeat)) or (not repeat and time.time() < end_by):
            y = abs_y % height

            if self.relay_data[index]:
                if self.relay_data[index] == 'cycle':
                    for x, name in enumerate(self.relays):
                        self.home.relays[name].set((abs_y//fps) % len(self.relays) != x)
                else:
                    relay_row = self.relay_data[index][y]
                    for x, name in enumerate(self.relays):
                        self.home.relays[name].set(relay_row[x])
                self.home.show_relays()

            # TODO: grow after epoch, shrink as we approach end_by

            image_row = self.image_data[index][y]
            for x, color in enumerate(image_row):
                self.strip[x] = color

            self.strip.show()

            while True:
                yield
                previous_y = abs_y
                abs_y = int((time.time() - epoch) * fps)
                if abs_y != previous_y:
                    break

        print('image complete')
        self.strip.clear(True)

    def stop(self):
        self.strip.clear(True)
