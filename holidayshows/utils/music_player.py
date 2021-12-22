import os
import time

from pygame import mixer

class Music_Player():
    def __init__(self):
        mixer.init()
        self.delay = 0
        self.songs = {}  # a list, but populated out of order

    def load(self, index, path):
        if path is None:
            self.songs[index] = None
            return
        if not os.path.exists(path):
            raise OSError(f'song does not exist: {path}')
        self.songs[index] = mixer.Sound(path)

    def play(self, index, at):
        while time.time() < at + self.delay:
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
