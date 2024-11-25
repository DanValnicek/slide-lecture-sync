from bisect import bisect
from collections import defaultdict
from typing import Sequence

import cv2
import numpy as np

from src import Presentation


class SlideMatcher:
    video: cv2.VideoCapture
    presentation: Presentation
    # list of keypoint/descriptor indexes of the last
    last_slide_kp_idx: list
    descriptors: np.ndarray
    keypoints: Sequence[cv2.KeyPoint]

    def __init__(self, presentation: Presentation):
        self.presentation = presentation
        self.last_slide_kp_idx = []

    # def matchPresentationToVideo(self):
    @staticmethod
    def eval_keypoints_by_distance(src_keypoint1: cv2.KeyPoint, dst_keypoint2: cv2.KeyPoint) -> float:
        """https://www.desmos.com/calculator/9ag3brj92d"""
        distance = np.linalg.norm(src_keypoint1 - dst_keypoint2)
        if distance > 7.0:
            return 0.0
        return np.exp(-(distance ** 2) / (2 * 3 ** 2))

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
        match_histogram = dict()
        for slide_matches in sorted(instance_cnt.items(), key=lambda x: len(x[1]), reverse=True):
            kps_lower_idx = self.last_slide_kp_idx[slide_matches[0] - 1] if slide_matches[0] != 0 else 0
            kps_upper_idx = self.last_slide_kp_idx[slide_matches[0]]
            kp1 = self.keypoints[kps_lower_idx:kps_upper_idx]
            if len(slide_matches[1]) < 4:
                continue
            src_pts = np.float32([self.keypoints[m.trainIdx].pt for m in slide_matches[1]]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp[m.queryIdx].pt for m in slide_matches[1]]).reshape(-1, 1, 2)
            homog, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
            mask = mask.ravel().tolist()
            # print(homog)
            # print(dst_pts)
            if homog is None:
                continue
            transformed_pts = cv2.perspectiveTransform(dst_pts, homog)
            eval_sum = 0.0
            for i in range(len(transformed_pts)):
                eval_sum += self.eval_keypoints_by_distance(src_pts[i], transformed_pts[i])
            # match_histogram[slide_matches[0]] = eval_sum
            slide_desc_cnt = (self.last_slide_kp_idx[slide_matches[0]] -
                              (self.last_slide_kp_idx[slide_matches[0] - 1] if slide_matches[0] != 0 else 0))
            match_histogram[slide_matches[0]] = eval_sum / slide_desc_cnt
        return match_histogram

    def create_training_keypoint_set(self):
        matcher = cv2.SIFT.create()
        self.descriptors = None
        for slide in self.presentation.slides:
            kp, desc = matcher.detectAndCompute(np.array(slide.image), None)
            if self.descriptors is None:
                self.keypoints = kp
                self.descriptors = desc
            else:
                self.keypoints = np.concatenate((self.keypoints, kp), axis=0)
                self.descriptors = np.concatenate((self.descriptors, desc), axis=0)
            self.last_slide_kp_idx.append(len(self.descriptors))
