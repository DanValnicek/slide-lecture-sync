import logging
from datetime import datetime

import cv2
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from src.Argparser import CustomArgParser
from src.HomographyProcessor import HomographyProcessor
from src.Presentation import Presentation
from src.SlideMatcher import SlideMatcher
from src.VideoInfo import VideoInfo

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    homo_checker = HomographyProcessor()
    print(CustomArgParser.get_args().pdf)
    presentation = Presentation(CustomArgParser.get_args().pdf)

    # for i, slide in enumerate(presentation.slides):
    #     cv2.imwrite(f"./data/imgs/{i}-slide.png", cv2.cvtColor(numpy.array(slide.image), cv2.COLOR_RGB2BGR))
    w, h = presentation.slides[0].image.size
    logger.debug("heigh: " + str(h) + "width: " + str(w))
    print(CustomArgParser.get_args().video)
    video = cv2.VideoCapture(CustomArgParser.get_args().video, apiPreference=cv2.CAP_FFMPEG)
    # homo_checker.find_homography_in_video(video, presentation)
    video_duration = video.get(cv2.CAP_PROP_FRAME_COUNT) // video.get(cv2.CAP_PROP_FPS) * 1000
    slide_matcher = SlideMatcher(presentation)
    slide_matcher.create_training_keypoint_set()
    pos = 0
    matching_plots = []
    videoStats = VideoInfo(CustomArgParser.get_args().pdf, CustomArgParser.get_args().video)

    optimization_mask = None
    while pos < video_duration:
        start_time = datetime.now()
        pos += 1000
        video.set(cv2.CAP_PROP_POS_MSEC, pos)
        got_img, frame = video.read()
        if not got_img:
            continue
        frame = cv2.resize(frame, None, fx=720 / frame.shape[0], fy=720 / frame.shape[0])
        hist, slide_id, _, mask = slide_matcher.matched_slide(frame, mask=optimization_mask)
        optimization_mask = mask
        videoStats.add_mapping_continuous(slide_id, pos)
        print(videoStats.toJSON())
        print(pos, " ", datetime.now() - start_time)
    video.release()
