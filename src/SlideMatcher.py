from bisect import bisect
from collections import defaultdict
from typing import Any, Sequence

import cv2
import numpy as np
from cv2 import Mat

from src import Presentation


class SlideMatcher:
    video: cv2.VideoCapture
    presentation: Presentation
    # list of keypoint/descriptor indexes of the last
    last_slide_kp_idx: list
    descriptors: Mat | np.ndarray[Any, np.dtype] | np.ndarray
    keypoints: Sequence[cv2.KeyPoint]

    def __init__(self, video: cv2.VideoCapture, presentation: Presentation):
        self.video = video
        self.presentation = presentation

    # def matchPresentationToVideo(self):

    def matched_slide(self, frame) -> (int, int):
        matcher = cv2.SIFT.create()
        kp, desc = matcher.detectAndCompute(frame, None)
        bfm = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
        matches = bfm.knnMatch(desc, self.descriptors, k=2)
        instance_cnt = defaultdict(list)

        for m, n in matches:
            if m.distance < 0.7 * n.distance:
                index = bisect(self.last_slide_kp_idx, m.trainIdx)
                instance_cnt[index].append(m)
        for slide_matches in sorted(instance_cnt.items(), key=lambda x: len(x[1]), reverse=True):
            kps_lower_idx = self.last_slide_kp_idx[slide_matches[0] - 1] if slide_matches[0] != 0 else 0
            kps_upper_idx = self.last_slide_kp_idx[slide_matches[0]] - 1
            kp1 = self.keypoints[kps_lower_idx:kps_upper_idx]
            src_pts = np.float32([kp1[m.trainIdx].pt for m in slide_matches[1]]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp[m.queryIdx].pt for m in slide_matches[1]]).reshape(-1, 1, 2)
            homog, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            mask = mask.ravel().tolist()
            transformed_pts = cv2.perspectiveTransform(dst_pts, homog)




    def eval_keypoints_by_distance(self):



    def create_training_keypoint_set(self):
        matcher = cv2.SIFT.create()
        self.descriptors = None
        for slide in self.presentation.slides:
            kp, desc = matcher.detectAndCompute(np.array(slide.image), None)
            if self.descriptors is None:
                self.keypoints = kp
                self.descriptors = desc
            else:
                self.keypoints = np.vstack((self.keypoints, kp))
                self.descriptors = np.concatenate((self.descriptors, desc), axis=0)
            self.last_slide_kp_idx.append(len(self.descriptors))
