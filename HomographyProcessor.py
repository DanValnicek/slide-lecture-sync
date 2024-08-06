import cv2
import numpy
from scipy.linalg import logm


# good homography
# > 10 correspondences
# small reprojection error
# not singular or close to it (determinant > 0)

class HomographyProcessor:
    sum_of_frame_homographies: numpy.matrix
    n_of_summed_homographies: int
    current_frame_best_homography: numpy.matrix
    current_frame_homog_correspondences: int

    def __init__(self):
        self.sum_of_frame_homographies = numpy.matrix('0 0 0; 0 0 0; 0 0 0')
        self.n_of_summed_homographies = 0
        self.current_frame_best_homography = []
        self.current_frame_homog_correspondences = 0

    def get_homography_matrix(self):
        return self.current_frame_best_homography
        # if self.n_of_summed_homographies == 0:
        #     return self.sum_of_frame_homographies
        # return self.sum_of_frame_homographies / self.n_of_summed_homographies

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
        if self.current_frame_homog_correspondences > matches.shape[0] < 200:
            return
        homog, _ = cv2.findHomography(matches[:, 2:], matches[:, :2], cv2.RANSAC, 5.0)
        if cv2.determinant(homog[:2, :2]) < 0:
            return
        self.current_frame_best_homography = homog
        self.current_frame_homog_correspondences = matches.shape[0]

    def add_current_frame_and_start_new(self):
        return
        if self.current_frame_homog_correspondences == 0:
            return
        self.sum_of_frame_homographies +=  self.current_frame_best_homography
        self.n_of_summed_homographies = self.n_of_summed_homographies + 1
        self.current_frame_best_homography = []
        self.current_frame_homog_correspondences = 0
