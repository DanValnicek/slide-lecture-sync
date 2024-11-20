import logging
from bisect import bisect
from datetime import timedelta

import cv2
import numpy
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from src.Argparser import CustomArgParser
from src.HomographyProcessor import HomographyProcessor
from src.Presentation import Presentation

logger = logging.getLogger(__name__)


# TODO: split code into argparser, homography finder, image matcher
if __name__ == '__main__':
    homo_checker = HomographyProcessor()
    print(CustomArgParser.get_args().pdf)
    presentation = Presentation(CustomArgParser.get_args().pdf)
    desc, idxs = create_training_keypoint_set(presentation)

    # for i, slide in enumerate(presentation.slides):
    #     cv2.imwrite(f"./data/imgs/{i}-slide.png", cv2.cvtColor(numpy.array(slide.image), cv2.COLOR_RGB2BGR))
    w, h = presentation.slides[0].image.size
    logger.debug("heigh: " + str(h) + "width: " + str(w))
    video = cv2.VideoCapture(CustomArgParser.get_args().video, apiPreference=cv2.CAP_FFMPEG)
    # homo_checker.find_homography_in_video(video, presentation)
    video_duration = video.get(cv2.CAP_PROP_FRAME_COUNT) // video.get(cv2.CAP_PROP_FPS) * 1000
    pos = 0
    matching_plots = []
    for v in range(30):
        pos = pos + video_duration / 30
        if pos > video_duration:
            break
        video.set(cv2.CAP_PROP_POS_MSEC, pos)
        got_img, frame = video.read()
        if not got_img:
            continue
        slide_n, match_cnt, matched_slide_cnt = matched_slide(desc, idxs, presentation, frame)
        print("slide: ", slide_n, " at:", timedelta(milliseconds=pos), " match_cnt: ", match_cnt,
              " matched_slides_cnt: ", matched_slide_cnt)
        matching_plots.append(
            (frame, presentation.slides[slide_n].image, timedelta(milliseconds=pos), slide_n, match_cnt,
             matched_slide_cnt))
        # newFrame = homo_checker.homog_transform(w, h, frame)
        # cv2.imwrite(f"./data/imgs/{v}.png", newFrame)
        # cv2.imwrite(f"./data/imgs/{v}-orig.png", frame)
    video.release()

    fig, axes = plt.subplots(len(matching_plots), 2, figsize=(10, 5 * len(matching_plots)))
    axes = axes.ravel()  # Flatten axes for easier iteration

    # axes[0].imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
    for i, img in enumerate(matching_plots):
        axes[i * 2].imshow(cv2.cvtColor(img[0], cv2.COLOR_BGR2RGB))
        axes[i * 2].set_title(f"slide: {img[3]}\nat: {img[2]}\nmatch_cnt: {img[4]}\nmatched_slides_cnt: {img[5]}")
        axes[i * 2 + 1].imshow(img[1])
        axes[i * 2].axis('off')  # Turn off axis labels for clarity
        axes[i * 2 + 1].axis('off')  # Turn off axis labels for clarity

    plt.tight_layout()
    with PdfPages('data/imgs/matched_slides.pdf') as pdf:
        pdf.savefig(fig)
    plt.close()
