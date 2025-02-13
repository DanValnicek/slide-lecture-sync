from argparse import ArgumentError
from pathlib import Path
from typing import Any

import cv2

from . import DataProvider
from ..data.IDM_slides import slides_with_timestamps


class IDMVideoProvider(DataProvider):
    def __init__(self):
        self.video = None

    def __del__(self):
        if self.video is not None:
            self.video.release()

    @property
    def presentation_path(self) -> Path:
        return Path(__file__).parent.parent / Path("data/grafy1.pdf")

    def test_cases(self):
        return slides_with_timestamps

    def get_test_input(self, test_identifier: Any):
        if self.video is None:
            self.video = cv2.VideoCapture(
                Path(__file__).parents[2] / Path("data/videos/IDM_2023-11-07_1080p.mp4"))
        self.video.set(cv2.CAP_PROP_POS_MSEC, test_identifier['time'] / 1000)
        success, frame = self.video.read()
        if success:
        # subtract 1 to align with 0 based counting
            return test_identifier['label'] - 1, frame
        raise ArgumentError('Invalid identifier!')
