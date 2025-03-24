import logging
from datetime import datetime
import cv2
from src.Argparser import CustomArgParser
from src.Presentation import Presentation
from src.SlideMatcher import SlideMatcher
from src.VideoInfo import PresentationSlideIntervals

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    print(CustomArgParser.get_args().pdf)
    presentation = Presentation(CustomArgParser.get_args().pdf)

    w, h = presentation.get_slide(0).image.size
    logger.debug("height: " + str(h) + "width: " + str(w))
    print(CustomArgParser.get_args().video)
    video = cv2.VideoCapture(CustomArgParser.get_args().video, apiPreference=cv2.CAP_FFMPEG)
    # homo_checker.find_homography_in_video(video, presentation)
    video_duration = video.get(cv2.CAP_PROP_FRAME_COUNT) // video.get(cv2.CAP_PROP_FPS) * 1000
    slide_matcher = SlideMatcher(presentation)
    slide_matcher.create_training_keypoint_set()
    pos = 0
    matching_plots = []
    slide_intervals = PresentationSlideIntervals()
    optimization_mask = None
    while pos < video_duration:
        start_time = datetime.now()
        pos += 1000
        video.set(cv2.CAP_PROP_POS_MSEC, pos)
        got_img, frame = video.read()
        if not got_img:
            continue
        hist, slide_id, _, mask = slide_matcher.matched_slide(frame, mask=optimization_mask)
        slide_intervals.add_point_to_slides(slide_id, pos)
        print(slide_intervals.to_json_human_readable())
    video.release()
    slide_intervals.compile_pdf_w_timestamps(presentation.get_pdf_file_path(),"pdf_w_timings.pdf")
