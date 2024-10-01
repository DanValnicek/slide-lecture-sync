import logging

import cv2
import numpy

from src.Argparser import CustomArgParser
from src.HomographyProcessor import HomographyProcessor
from src.Presentation import Presentation

logger = logging.getLogger(__name__)

# TODO: split code into argparser, homography finder, image matcher
if __name__ == '__main__':
    homo_checker = HomographyProcessor()
    print(CustomArgParser.get_args().pdf)
    presentation = Presentation(CustomArgParser.get_args().pdf)
    for i, slide in enumerate(presentation.slides):
        cv2.imwrite(f"./data/imgs/{i}-slide.png", cv2.cvtColor(numpy.array(slide.image), cv2.COLOR_RGB2BGR))
    w, h = presentation.slides[0].image.size
    logger.debug("heigh: " + str(h) + "width: " + str(w))
    video = cv2.VideoCapture(CustomArgParser.get_args().video, apiPreference=cv2.CAP_FFMPEG)
    homo_checker.find_homography_in_video(video, presentation)
    video_duration = video.get(cv2.CAP_PROP_FRAME_COUNT) // video.get(cv2.CAP_PROP_FPS) * 1000
    pos = 0
    for v in range(30):
        pos = pos + video_duration / 30
        if pos > video_duration:
            break
        video.set(cv2.CAP_PROP_POS_MSEC, pos)
        got_img, frame = video.read()
        if not got_img:
            continue
        newFrame = homo_checker.homog_transform(w, h, frame)
        cv2.imwrite(f"./data/imgs/{v}.png", newFrame)
        cv2.imwrite(f"./data/imgs/{v}-orig.png", frame)
    video.release()
