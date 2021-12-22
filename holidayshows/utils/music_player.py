import os
import time

from pygame import mixer

class Music_Player():
    def __init__(self, config):
        mixer.init()
        self.delay = 0
        self.config = config
        self.songs = {}  # a list, but populated out of order

    def load_data(self, arguments):
        index = arguments['index']
        music = arguments['music']
        if music is None:
            self.songs[index] = None
            return
        music = os.path.expanduser(music)
        if not os.path.exists(music):
            raise OSError(f'music file does not exist: {music}')
        self.songs[index] = mixer.Sound(music)

    def play(self, arguments):
        index = arguments['index']
        repeat = arguments['repeat']
        end_by = arguments['end_by']
        epoch = arguments['epoch']
        fps = arguments['fps']
        while time.time() < epoch + self.delay:
            time.sleep(0.001)
            yield
        song = self.songs[index]
        if song:
            song.play()
            print('song playing')
        else:
            print('no song to play')

    def stop(self):
        mixer.stop()
