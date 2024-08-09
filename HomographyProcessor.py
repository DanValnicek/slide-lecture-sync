import cv2
import numpy


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
