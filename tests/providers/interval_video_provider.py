import json
from argparse import ArgumentError
from pathlib import Path
from typing import Any

import cv2

from src.VideoInfo import PresentationSlideIntervals
from . import DataProvider
from ..test_data.IDM_slides import slides_with_timestamps


class IntervalVideoProvider(DataProvider):
    def __init__(self, json_path, video_path, presentation_path):
        self.video = None
        self._presentation_path = presentation_path
        self.video_path = video_path
        with json_path.open("r", encoding="utf-8") as f:
            self.intervals = PresentationSlideIntervals.from_JSON(f)

    def __del__(self):
        if self.video is not None:
            self.video.release()

    @property
    def presentation_path(self) -> Path:
        return self._presentation_path

    def test_cases(self):
        video = cv2.VideoCapture(self.video_path.as_posix(), apiPreference=cv2.CAP_FFMPEG)
        duration = int(video.get(cv2.CAP_PROP_FRAME_COUNT) // video.get(cv2.CAP_PROP_FPS))
        video.release()
        return [i for i in range(0, duration * 1000, 1000)]

    def get_test_input(self, test_identifier: Any):
        if self.video is None:
            self.video = cv2.VideoCapture(self.video_path.as_posix())
        self.video.set(cv2.CAP_PROP_POS_MSEC, test_identifier)
        success, frame = self.video.read()
        if success:
            return self.intervals.get_slide_from_position(test_identifier), frame
        raise ArgumentError('Invalid identifier!')
