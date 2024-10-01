import logging
from datetime import timedelta

import cv2
import numpy

from src.Presentation import Presentation
from src.geoformer.inference import GeoFormer


# good homography
# > 10 correspondences
# small reprojection error
# not singular or close to it (determinant > 0)

class HomographyProcessor:
    current_frame_best_homography: numpy.matrix
    current_frame_homog_correspondences: int

    def __init__(self):
        self.current_frame_best_homography = []
        self.current_frame_homog_correspondences = 0

    def get_homography_matrix(self):
        return self.current_frame_best_homography

    @staticmethod
    def check_array_shape(arr):
        # Check if the array is valid list of matches
        if not isinstance(arr, numpy.ndarray):
            return False
        n, cols = arr.shape
        if n >= 4 and (cols == 2 or cols == 6):
            return True
        return False

    def process(self, matches: numpy.ndarray):
        if not self.check_array_shape(matches[:, :2]):
            return
        if self.current_frame_homog_correspondences > matches.shape[0]:
            return
        homog, _ = cv2.findHomography(matches[:, 2:], matches[:, :2], cv2.RANSAC, 5.0)
        if cv2.determinant(homog[:2, :2]) < 0:
            return
        self.current_frame_best_homography = homog
        self.current_frame_homog_correspondences = matches.shape[0]

    def homog_transform(self, width, height, frame):
        if frame is None or width is None or height is None:
            return
        pts = numpy.float32([[0, 0], [0, height - 1], [width - 1, height - 1], [width - 1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, self.get_homography_matrix())
        perspective_mat = cv2.getPerspectiveTransform(numpy.float32(dst), pts)
        return cv2.warpPerspective(frame, perspective_mat, (width, height))

    def find_homography_in_video(self, video: cv2.VideoCapture, presentation: Presentation):
        w, h = presentation.slides[0].get_size()
        logging.getLogger(__name__).debug("heigh: " + str(h) + "width: " + str(w))
        g = GeoFormer(w, 0.8, no_match_upscale=False, device='cuda')
        video_duration = video.get(cv2.CAP_PROP_FRAME_COUNT) // video.get(cv2.CAP_PROP_FPS) * 1000
        logging.getLogger(__name__).debug("video_duration: " + str(video_duration))
        pos = 0.0
        while video.isOpened():
            newFrame, frame = video.read()
            logging.getLogger(__name__).debug("video current second: " + str(video.get(cv2.CAP_PROP_POS_MSEC) / 1000))
            if newFrame:
                best_homog = self.get_homography_matrix()
                for img in presentation.slides:
                    matches, kpts1, kpts2, scores = g.match_pairs(frame, numpy.array(img), is_draw=False)
                    self.process(matches)
                    print('\r', matches.shape, " slide n:", img.get_page_number(), end='')
                print("")
                logging.getLogger(__name__).debug(logging.getLogger(__name__).getEffectiveLevel())
            if (not numpy.array_equal(best_homog, self.get_homography_matrix()) and
                    logging.getLogger(__name__).getEffectiveLevel() >= logging.DEBUG):
                cv2.imwrite(f"data/imgs/best_at_{timedelta(milliseconds=pos)}.png", frame)
                cv2.imwrite(f"data/imgs/best_at_{timedelta(milliseconds=pos)}_transformed.png",
                            self.homog_transform(w, h, frame))
                logging.getLogger(__name__).debug(str(self.get_homography_matrix()))
                logging.getLogger(__name__).debug(
                    "best correspondences: " + str(self.current_frame_homog_correspondences))
                logging.getLogger(__name__).debug(str(pos))
            pos = pos + video_duration / 20
            if pos > video_duration:
                break
            video.set(cv2.CAP_PROP_POS_MSEC, pos)
