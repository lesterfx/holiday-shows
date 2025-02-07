from collections import defaultdict
import os
import time

from pygame import mixer

class Music_Player():
    def __init__(self, config):
        mixer.init()
        self.delay = 0
        self.config = config
        self.songs = defaultdict(lambda: None)

    def load_data(self, arguments):
        index = arguments['index']
        music = arguments['music']
        if music is None:
            self.songs[index] = None
            return
        music = os.path.expanduser(music)
        if not os.path.exists(music):
            message = f'music file does not exist: {music}'
            raise OSError(message)
        self.songs[index] = mixer.Sound(music)

    def play(self, arguments):
        index = arguments['index']
        repeat = arguments['repeat']
        end_by = arguments['end_by']
        epoch = arguments['epoch']
        fps = arguments['fps']

        song = self.songs[index]
        if song:
            while time.time() < epoch + self.delay:
                time.sleep(0.001)
                yield 'waiting for start time'
            song.play()
            yield 'song playing'
        else:
            yield 'no song to play'

    def stop(self):
        mixer.stop()
