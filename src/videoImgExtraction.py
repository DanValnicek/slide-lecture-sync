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

# TODO: split code into argparser, homography finder, image matcher
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
    pos = 1700000
    matching_plots = []
    videoStats = VideoInfo(CustomArgParser.get_args().pdf, CustomArgParser.get_args().video)

    while pos < video_duration:
        start_time = datetime.now()
        pos += 1000
        # pos = pos + video_duration / 30
        # if pos > video_duration:
        #     break
        video.set(cv2.CAP_PROP_POS_MSEC, pos)
        got_img, frame = video.read()
        if not got_img:
            continue
        # frame = cv2.resize(frame, None, fx=720 / frame.shape[0], fy=720 / frame.shape[0])
        hist, slide_id, _ = slide_matcher.matched_slide(frame)
        videoStats.add_mapping_continuous(slide_id, pos)
        # sorted_hist = {key: hist[key] for key in sorted(hist)}
        print(videoStats.toJSON())
        # print(sorted_hist)
        # if hist:
        #     matching_plots.append(
        #         (frame, presentation.slides[max(hist, key=hist.get)].image, sorted_hist))
        print(pos, " ", datetime.now() - start_time)
    video.release()

    # cols = 3
    # fig, axes = plt.subplots(len(matching_plots), cols, figsize=(10, 5 * len(matching_plots)))
    # axes = axes.ravel()  # Flatten axes for easier iteration
    #
    # # axes[0].imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
    # for i, img in enumerate(matching_plots):
    #     axes[i * cols].imshow(cv2.cvtColor(img[0], cv2.COLOR_BGR2RGB))
    #     # axes[i * 2].set_title(f"slide: {img[3]}\nat: {img[2]}\nmatch_cnt: {img[4]}\nmatched_slides_cnt: {img[5]}")
    #     axes[i * cols + 1].imshow(img[1])
    #     axes[i * cols + 2].bar(img[2].keys(), img[2].values(), align='center',
    #                            tick_label=[str(key) for key in img[2].keys()])
    #     axes[i * cols + 2].set_xlabel('Slide number')
    #     axes[i * cols + 2].set_ylabel('match valuation')
    #     axes[i * cols].axis('off')  # Turn off axis labels for clarity
    #     axes[i * cols + 1].axis('off')  # Turn off axis labels for clarity
    #
    # plt.tight_layout()
    # with PdfPages('data/imgs/matched_slides.pdf') as pdf:
    #     pdf.savefig(fig)
    # plt.close()
