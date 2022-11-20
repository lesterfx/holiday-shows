import os

from PIL import Image
import numpy as np

class ImageSlicer:
    _instance = None
    images: dict
    def __new__(cls):
        if not cls._instance:
            self = cls._instance = object.__new__(cls)
            self.images = {}
        return cls._instance

    def slice_image(self, path, start, end, wrap=False, bw=False):
        if path not in self.images:
            self.images[path] = self.load_image(path)
        return self._slice_image(self.images[path], start, end, wrap, bw)

    def load_image(self, path):
        path = os.path.join(os.path.dirname(__file__), '..', path)
        path = os.path.realpath(path)
        image = Image.open(path)
        image_data = np.asarray(image, dtype=np.uint8)
        return image_data

    def _slice_image(self, image, start, end, wrap=False, bw=False):
        image_slice = image[:, start:end]
        if bw:
            image_slice = self.booleanize(image_slice)
        needed_width = end - start
        if needed_width > image_slice.shape[1]:
            pad = ((0, 0), (0, needed_width - image_slice.shape[1]), (0, 0))
            if wrap:
                mode = 'wrap'
                kwargs = {}
            else:
                mode = 'constant'
                kwargs = {'constant_values': 0}
            image_slice = np.pad(image_slice, pad, mode=mode, **kwargs)
        # ret = image_slice.tolist()
        ret = image_slice
        return ret

    @staticmethod
    def booleanize(image_slice):
        if ((image_slice[:,:,0] == image_slice[:,:,1]).all() and  # red == green
            (image_slice[:,:,0] == image_slice[:,:,2]).all() and  # red == blue
            not (set(np.unique(image_slice)) - {0, 255})):        # nothing but black and white
            return image_slice[:,:,0] > 127
        raise ValueError('Relay pixels must be black or white')
