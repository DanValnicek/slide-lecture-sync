import logging
from datetime import timedelta

import cv2
import numpy
import numpy as np

from src.Presentation import Presentation


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

    def process(self, matches: numpy.ndarray, kp1, kp2):
        good = []
        for m, n in matches:
            if m.distance < 0.8 * n.distance:
                good.append(m)
        if len(good) > self.current_frame_homog_correspondences and len(good) > 200:
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            # if not self.check_array_shape(matches[:, :2]):
            #     return
            # if self.current_frame_homog_correspondences > matches.shape[0]:
            #     return
            # homog, _ = cv2.findHomography(matches[:, 2:], matches[:, :2], cv2.RANSAC, 5.0)
            homog, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            mask = mask.ravel().tolist()
            if cv2.determinant(homog[:2, :2]) < 0:
                return None, None
            self.current_frame_best_homography = homog
            # self.current_frame_homog_correspondences = matches.shape[0]
            self.current_frame_homog_correspondences = len(good)
            return mask, good
        return None, None

    def homog_transform(self, width, height, frame):
        if frame is None or width is None or height is None:
            return
        pts = numpy.float32([[0, 0], [0, height - 1], [width - 1, height - 1], [width - 1, 0]]).reshape(-1, 1, 2)
        dst = cv2.perspectiveTransform(pts, self.get_homography_matrix())
        perspective_mat = cv2.getPerspectiveTransform(numpy.float32(dst), pts)
        perspective_mat = np.linalg.inv(perspective_mat)
        return cv2.warpPerspective(frame, perspective_mat, (width, height))

    def find_homography_in_video(self, video: cv2.VideoCapture, presentation: Presentation):
        w, h = presentation.slides[0].get_size()
        logging.getLogger(__name__).debug("heigh: " + str(h) + "width: " + str(w))
        # g = GeoFormer(w, 0.8, no_match_upscale=False, device='cuda')
        matcher = cv2.SIFT.create()
        bfm = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
        video_duration = video.get(cv2.CAP_PROP_FRAME_COUNT) // video.get(cv2.CAP_PROP_FPS) * 1000
        logging.getLogger(__name__).debug("video_duration: " + str(video_duration))
        pos = 0.0
        while video.isOpened():
            newFrame, frame = video.read()
            logging.getLogger(__name__).debug("video current second: " + str(video.get(cv2.CAP_PROP_POS_MSEC) / 1000))
            if newFrame:
                best_homog = self.get_homography_matrix()
                print("")
                for img in presentation.slides:
                    good_homog = self.get_homography_matrix()
                    kp2, desc2 = matcher.detectAndCompute(numpy.array(img), None)
                    # matches, kpts1, kpts2, scores = g.match_pairs(frame, numpy.array(img), is_draw=False)
                    kp1, desc1 = matcher.detectAndCompute(frame, None)
                    matches = bfm.knnMatch(desc1, desc2, k=2)
                    mask, goodMatches = self.process(matches, kp1, kp2)
                    print('\r', len(matches), " slide n:", img.get_page_number(), end='')
                    if type(self.get_homography_matrix()) is type(np.array) and self.get_homography_matrix().shape == (
                    3, 3) and not numpy.array_equal(good_homog,
                                                    self.get_homography_matrix()):
                        dst = cv2.perspectiveTransform(
                            numpy.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2),
                            self.get_homography_matrix())
                        tmpImg2 = cv2.polylines(np.array(img), [np.int32(dst)], True, 255, 3, cv2.LINE_AA)
                        tmpImg = cv2.drawMatches(frame, kp1, tmpImg2, kp2, goodMatches, None,
                                                 matchColor=(0, 255, 0), matchesMask=mask, singlePointColor=None,
                                                 flags=2)
                        cv2.imwrite(f"data/img{pos}.png", tmpImg)
                        # print('\r', matches.shape, " slide n:", img.get_page_number(), end='')
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
