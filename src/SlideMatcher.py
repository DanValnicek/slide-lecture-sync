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

    # def matched_slide(self, frame, frame_time=0) -> (int, int):
    #     matcher = cv2.SIFT.create()
    #     kp, desc = matcher.detectAndCompute(frame, None)
    #     bfm = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
    #     matches = bfm.knnMatch(desc, self.descriptors, k=2)
    #     instance_cnt = defaultdict(list)
    #
    #     for m, n in matches:
    #         if m.distance < 0.7 * n.distance:
    #             index = bisect(self.last_slide_kp_idx, m.trainIdx)
    #             instance_cnt[index].append(m)
    #     match_histogram = dict()
    #     for slide_matches in sorted(instance_cnt.items(), key=lambda x: len(x[1]), reverse=True):
    #         kps_lower_idx = self.last_slide_kp_idx[slide_matches[0] - 1] if slide_matches[0] != 0 else 0
    #         kps_upper_idx = self.last_slide_kp_idx[slide_matches[0]]
    #         kp1 = self.keypoints[kps_lower_idx:kps_upper_idx]
    #         if len(slide_matches[1]) < 4:
    #             continue
    #         src_pts = np.float32([self.keypoints[m.trainIdx].pt for m in slide_matches[1]]).reshape(-1, 1, 2)
    #         dst_pts = np.float32([kp[m.queryIdx].pt for m in slide_matches[1]]).reshape(-1, 1, 2)
    #         homog, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
    #         mask = mask.ravel().tolist()
    #         # print(homog)
    #         # print(dst_pts)
    #         if homog is None:
    #             continue
    #         transformed_pts = cv2.perspectiveTransform(dst_pts, homog)
    #         eval_sum = 0.0
    #         for i in range(len(transformed_pts)):
    #             eval_sum += self.eval_keypoints_by_distance(src_pts[i], transformed_pts[i])
    #         # match_histogram[slide_matches[0]] = eval_sum
    #         slide_desc_cnt = (self.last_slide_kp_idx[slide_matches[0]] -
    #                           (self.last_slide_kp_idx[slide_matches[0] - 1] if slide_matches[0] != 0 else 0))
    #         match_histogram[slide_matches[0]] = eval_sum / slide_desc_cnt
    #         keypoints1 = [kp[m.queryIdx].pt for m in slide_matches[1]]
    #         keypoints2 = [self.keypoints[m.trainIdx].pt for m in slide_matches[1]]
    #         cv2.imwrite(f"./data/imgs/{slide_matches[0]}w{frame_time}.png",
    #                     cv2.drawMatches(frame, keypoints2, self.presentation.slides[slide_matches[0]].image, keypoints1,
    #                     ,
    #                     None,
    #                     2,
    #                     (0, 255, 0), mask, cv2.DrawMatchesFlags_DEFAULT))
    #         return match_histogram

    def matched_slide(self, frame) -> (int, int):
        matcher = cv2.SIFT.create()

        kp, desc = matcher.detectAndCompute(frame, None)
        bfm = cv2.FlannBasedMatcher({"algorithm": 1, "trees": 5}, {"checks": 50})
        matches = bfm.knnMatch(desc, self.descriptors, k=2)
        instance_cnt = defaultdict(list)

        for m, n in matches:
            # if m.distance < 0.7 * n.distance:
            index = bisect(self.last_slide_kp_idx, m.trainIdx)
            instance_cnt[index].append(m)

        match_histogram = dict()
        best_slide = None
        max_eval_sum = -1
        best_keypoints1 = []
        best_keypoints2 = []

        for slide_idx, slide_matches in sorted(instance_cnt.items(), key=lambda x: len(x[1]), reverse=True):
            kps_lower_idx = self.last_slide_kp_idx[slide_idx - 1] if slide_idx != 0 else 0
            kps_upper_idx = self.last_slide_kp_idx[slide_idx]
            if len(slide_matches) < 4:
                continue

            src_pts = np.float32([self.keypoints[m.trainIdx].pt for m in slide_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp[m.queryIdx].pt for m in slide_matches]).reshape(-1, 1, 2)

            homog, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
            if homog is None:
                continue

            transformed_pts = cv2.perspectiveTransform(dst_pts, homog)
            eval_sum = 0.0
            for i in range(len(transformed_pts)):
                eval_sum += self.eval_keypoints_by_distance(src_pts[i], transformed_pts[i])

            slide_desc_cnt = (self.last_slide_kp_idx[slide_idx] -
                              (self.last_slide_kp_idx[slide_idx - 1] if slide_idx != 0 else 0))
            match_score = eval_sum / slide_desc_cnt
            match_histogram[slide_idx] = match_score

            if match_score > max_eval_sum:
                max_eval_sum = match_score
                best_slide = slide_idx
                best_keypoints1 = [kp[m.queryIdx].pt for m in slide_matches]
                best_keypoints2 = [self.keypoints[m.trainIdx].pt for m in slide_matches]
        result_img = None
        if best_slide is not None:
            result_img = cv2.drawMatches(
                frame,
                [cv2.KeyPoint(pt[0], pt[1], 1) for pt in best_keypoints1],
                np.array(self.presentation.slides[best_slide].image)[:, :, ::-1],
                [cv2.KeyPoint(pt[0], pt[1], 1) for pt in best_keypoints2],
                [cv2.DMatch(i, i, 0) for i in range(len(best_keypoints1))],
                None,
                flags=cv2.DrawMatchesFlags_DEFAULT
            )
            # cv2.imwrite(f"./data/imgs/{best_slide}_w{frame_time}.png", result_img)
        if match_histogram == {}:
            return match_histogram, None, None
        return match_histogram, max(match_histogram, key=match_histogram.get), result_img

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
