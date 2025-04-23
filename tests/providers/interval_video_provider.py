from argparse import ArgumentError
from pathlib import Path
from typing import Any

import cv2

from src.VideoInfo import PresentationSlideIntervals
from . import DataProvider


class IntervalVideoProvider(DataProvider):
    def __init__(self, json_path, video_path, presentation_path):
        self.video = None
        self._presentation_path = presentation_path
        self.video_path = video_path
        self.test_cnt = 0
        with json_path.open("r", encoding="utf-8") as f:
            self.intervals = PresentationSlideIntervals.from_JSON(f)

    def __del__(self):
        if self.video is not None:
            self.video.release()

    def get_test_suite_name(self):
        return self._presentation_path.stem + "_intervals"

    @property
    def presentation_path(self) -> Path:
        return self._presentation_path

    def get_test_cnt(self):
        return self.test_cnt

    def test_cases(self):
        video = cv2.VideoCapture(self.video_path.as_posix(), apiPreference=cv2.CAP_FFMPEG)
        duration = int(video.get(cv2.CAP_PROP_FRAME_COUNT) // video.get(cv2.CAP_PROP_FPS))
        video.release()
        cases = [i for i in range(0, duration * 1000, 1000)]
        self.test_cnt = len(cases)
        return cases

    def get_test_input(self, test_identifier: Any):
        if self.video is None:
            self.video = cv2.VideoCapture(self.video_path.as_posix())
        self.video.set(cv2.CAP_PROP_POS_MSEC, test_identifier)
        success, frame = self.video.read()
        if success:
            return self.intervals.get_slide_from_position(test_identifier), frame
        raise ArgumentError('Invalid identifier!')
