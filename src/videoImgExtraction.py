# author Dan Valníček
# This file can serve as an entry point for CLI based slide
import logging
from datetime import datetime
from pathlib import Path

import cv2
from PySide6.QtCore import Signal, QThread

from src.Argparser import CustomArgParser
from src.Slides import Slides
from src.SlideMatcher import SlideMatcher
from src.SlideIntervals import SlideIntervals

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.debug(CustomArgParser.get_args().pdf)
    presentation = Slides(CustomArgParser.get_args().pdf)

    w, h = presentation.get_slide(0).image.size
    logger.debug("height: " + str(h) + "width: " + str(w))
    logger.debug(CustomArgParser.get_args().video)
    video = cv2.VideoCapture(CustomArgParser.get_args().video, apiPreference=cv2.CAP_FFMPEG)
    video_duration = video.get(cv2.CAP_PROP_FRAME_COUNT) // video.get(cv2.CAP_PROP_FPS) * 1000
    slide_matcher = SlideMatcher(presentation)
    slide_matcher.create_training_keypoint_set()
    pos = 0
    matching_plots = []
    slide_intervals = SlideIntervals()
    while pos < video_duration:
        start_time = datetime.now()
        pos += 1000
        video.set(cv2.CAP_PROP_POS_MSEC, pos)
        got_img, frame = video.read()
        if not got_img:
            continue
        hist, slide_id, dbg = slide_matcher.matched_slide(frame, [])
        slide_intervals.add_point_to_slides(slide_id, pos)
        logger.debug(slide_intervals.to_JSON())
    video.release()
    slide_intervals.compile_pdf_w_timestamps(presentation.get_pdf_file_path(), presentation.get_pdf_file_path().stem + "_w_timings.pdf" )


class SlideIntervalFinder(QThread):
    """Class for slide annotation that is Qt friendly running asynchronously."""
    progres_updated = Signal(int)

    def __init__(self, video_path: Path, presentation_path: Path, out_pdf_path: Path):
        """Input data for later calculation."""
        super().__init__()
        self.presentation = Slides(presentation_path)
        w, h = self.presentation.get_slide(0).image.size
        logger.debug("height: " + str(h) + "width: " + str(w))
        self.video = cv2.VideoCapture(video_path, apiPreference=cv2.CAP_FFMPEG)
        self.video_duration = self.video.get(cv2.CAP_PROP_FRAME_COUNT) // self.video.get(cv2.CAP_PROP_FPS) * 1000
        self.slide_matcher = SlideMatcher(self.presentation)
        self.out_pdf_path = out_pdf_path

    def get_frame_cnt(self):
        return self.video_duration // 1000

    def run(self) -> SlideIntervals:
        """Run the slide-matching and store the results in a pdf as specified previously."""
        self.slide_matcher.create_training_keypoint_set()
        pos = 0
        slide_intervals = SlideIntervals()
        while pos < self.video_duration:
            if self.isInterruptionRequested():
                break
            pos += 1000
            self.video.set(cv2.CAP_PROP_POS_MSEC, pos)
            got_img, frame = self.video.read()
            if not got_img:
                continue
            hist, slide_id, _ = self.slide_matcher.matched_slide(frame)
            slide_intervals.add_point_to_slides(slide_id, pos)
            logger.debug(slide_intervals.to_JSON())
            self.progres_updated.emit(pos // 1000)
        self.video.release()
        slide_intervals.compile_pdf_w_timestamps(self.presentation.get_pdf_file_path(), self.out_pdf_path)
