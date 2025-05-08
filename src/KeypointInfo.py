import numpy as np

from src.Slides import ImageDecorator


class KeypointInfo(ImageDecorator):
    keypoints: np.ndarray
    descriptors: np.ndarray
    def __init__(self, img, keypoints, descriptors):
        super().__init__(img)
        self.keypoints = keypoints
        self.descriptors = descriptors

    def get_keypoints(self):
        return self.keypoints
