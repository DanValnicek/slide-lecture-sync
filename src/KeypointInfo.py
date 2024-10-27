from src.Presentation import ImageDecorator


class KeypointInfo(ImageDecorator):
    def __init__(self, img, keypoints):
        super().__init__(img)
        self.keypoints = keypoints

    def get_keypoints(self):
        return self.keypoints
